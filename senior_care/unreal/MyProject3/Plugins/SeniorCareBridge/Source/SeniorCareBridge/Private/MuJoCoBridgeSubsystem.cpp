// Copyright SeniorCare.

#include "MuJoCoBridgeSubsystem.h"

#include "MuJoCoDrivenSkeletonComponent.h"
#include "MuJoCoSkeletalActor.h"
#include "SeniorCareBridge.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#include "Containers/Ticker.h"
#include "EngineUtils.h"
#include "Editor.h"
#include "Engine/World.h"
#include "HAL/PlatformProcess.h"
#include "Misc/ScopeLock.h"
#include "UObject/UObjectIterator.h"

#include <atomic>

THIRD_PARTY_INCLUDES_START
#include "zmq.h"
THIRD_PARTY_INCLUDES_END

// ---------------------------------------------------------------------------
// FBridgeRunnable: background thread that owns the ZMQ context + SUB socket
// and pushes parsed frames back into the subsystem.
// ---------------------------------------------------------------------------
class UMuJoCoBridgeSubsystem::FBridgeRunnable : public FRunnable
{
public:
	FBridgeRunnable(UMuJoCoBridgeSubsystem* InOwner, FString InEndpoint)
		: Owner(InOwner)
		, Endpoint(MoveTemp(InEndpoint))
	{
	}

	virtual ~FBridgeRunnable() override
	{
		FBridgeRunnable::Stop();
	}

	virtual bool Init() override { return true; }

	virtual uint32 Run() override
	{
		void* Context = zmq_ctx_new();
		if (!Context)
		{
			UE_LOG(LogSeniorCareBridge, Error, TEXT("zmq_ctx_new failed"));
			return 1;
		}

		void* Socket = zmq_socket(Context, ZMQ_SUB);
		if (!Socket)
		{
			UE_LOG(LogSeniorCareBridge, Error, TEXT("zmq_socket(SUB) failed"));
			zmq_ctx_term(Context);
			return 2;
		}

		// Subscribe to all messages.
		zmq_setsockopt(Socket, ZMQ_SUBSCRIBE, "", 0);

		// Short receive timeout so the thread can poll bStopRequested.
		const int RecvTimeoutMs = 100;
		zmq_setsockopt(Socket, ZMQ_RCVTIMEO,
		               &RecvTimeoutMs, sizeof(RecvTimeoutMs));

		FTCHARToUTF8 EndpointUtf8(*Endpoint);
		if (zmq_connect(Socket, EndpointUtf8.Get()) != 0)
		{
			UE_LOG(LogSeniorCareBridge, Error,
			       TEXT("zmq_connect('%s') failed: %hs"),
			       *Endpoint, zmq_strerror(zmq_errno()));
			zmq_close(Socket);
			zmq_ctx_term(Context);
			return 3;
		}

		UE_LOG(LogSeniorCareBridge, Log,
		       TEXT("[Bridge] SUB connected to '%s'"), *Endpoint);

		// Reuse one buffer for received messages; grow on demand.
		TArray<uint8> Buffer;
		Buffer.SetNumUninitialized(64 * 1024);

		while (!bStopRequested.load())
		{
			int N = zmq_recv(Socket, Buffer.GetData(), Buffer.Num(), 0);
			if (N < 0)
			{
				int Err = zmq_errno();
				if (Err == EAGAIN || Err == EINTR)
				{
					continue;
				}
				UE_LOG(LogSeniorCareBridge, Warning,
				       TEXT("zmq_recv error: %hs"), zmq_strerror(Err));
				FPlatformProcess::Sleep(0.05f);
				continue;
			}

			// On truncation, ZMQ returns the original message length.
			if (N > Buffer.Num())
			{
				Buffer.SetNumUninitialized(N);
				continue; // next iteration will receive again
			}

			// Convert UTF-8 byte range -> FString without relying on
			// null termination of the recv buffer.
			FUTF8ToTCHAR Conv(reinterpret_cast<const ANSICHAR*>(Buffer.GetData()), N);
			FString Json(Conv.Length(), Conv.Get());

			ParseAndPush(Json);
		}

		zmq_close(Socket);
		zmq_ctx_term(Context);
		UE_LOG(LogSeniorCareBridge, Log, TEXT("[Bridge] SUB worker stopped"));
		return 0;
	}

	virtual void Stop() override
	{
		bStopRequested.store(true);
	}

	virtual void Exit() override {}

private:
	void ParseAndPush(const FString& Json)
	{
		TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
		TSharedPtr<FJsonObject> Root;
		if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
		{
			UE_LOG(LogSeniorCareBridge, Warning,
			       TEXT("[Bridge] failed to parse frame JSON (len=%d)"), Json.Len());
			return;
		}

		const int64 Seq = static_cast<int64>(Root->GetNumberField(TEXT("seq")));

		const TSharedPtr<FJsonObject>* AssetsObj = nullptr;
		if (!Root->TryGetObjectField(TEXT("assets"), AssetsObj) || !AssetsObj || !AssetsObj->IsValid())
		{
			UE_LOG(LogSeniorCareBridge, Warning,
			       TEXT("[Bridge] frame missing 'assets' (seq=%lld)"), Seq);
			return;
		}

		int32 PerFrameAssets = 0;
		for (const auto& Pair : (*AssetsObj)->Values)
		{
			const FString& AssetName = Pair.Key;
			const TSharedPtr<FJsonValue>& AssetVal = Pair.Value;
			if (!AssetVal.IsValid() || AssetVal->Type != EJson::Object)
			{
				continue;
			}
			TSharedPtr<FJsonObject> AssetObj = AssetVal->AsObject();
			if (!AssetObj.IsValid())
			{
				continue;
			}

			TSharedRef<FMuJoCoAssetFrame> Frame = MakeShared<FMuJoCoAssetFrame>();
			Frame->AssetName = AssetName;
			Frame->Seq = Seq;
			Frame->ReceivedAtSec = FPlatformTime::Seconds();

			// root_position [x,y,z] in meters
			const TArray<TSharedPtr<FJsonValue>>* RootPos = nullptr;
			if (AssetObj->TryGetArrayField(TEXT("root_position"), RootPos)
			    && RootPos && RootPos->Num() == 3)
			{
				const double X = (*RootPos)[0]->AsNumber();
				const double Y = (*RootPos)[1]->AsNumber();
				const double Z = (*RootPos)[2]->AsNumber();
				// MuJoCo (m) -> UE (cm). No axis flip; the Python
				// setup script picks placement, this is just a
				// passthrough for the driver.
				Frame->RootPosition = FVector(X * 100.0, Y * 100.0, Z * 100.0);
			}

			// root_orientation [w,x,y,z]
			const TArray<TSharedPtr<FJsonValue>>* RootOri = nullptr;
			if (AssetObj->TryGetArrayField(TEXT("root_orientation"), RootOri)
			    && RootOri && RootOri->Num() == 4)
			{
				const double W = (*RootOri)[0]->AsNumber();
				const double X = (*RootOri)[1]->AsNumber();
				const double Y = (*RootOri)[2]->AsNumber();
				const double Z = (*RootOri)[3]->AsNumber();
				Frame->RootOrientation = FQuat(X, Y, Z, W);
			}

			// joints: { joint_name: value_rad }
			const TSharedPtr<FJsonObject>* JointsObj = nullptr;
			if (AssetObj->TryGetObjectField(TEXT("joints"), JointsObj)
			    && JointsObj && JointsObj->IsValid())
			{
				Frame->Joints.Reserve((*JointsObj)->Values.Num());
				for (const auto& JointPair : (*JointsObj)->Values)
				{
					if (!JointPair.Value.IsValid())
					{
						continue;
					}
					double Value = 0.0;
					if (JointPair.Value->TryGetNumber(Value))
					{
						Frame->Joints.Add(JointPair.Key, Value);
					}
				}
			}

			// bone_transforms: { body_name: { position, orientation } }
			const TSharedPtr<FJsonObject>* BonesObj = nullptr;
			if (AssetObj->TryGetObjectField(TEXT("bone_transforms"), BonesObj)
			    && BonesObj && BonesObj->IsValid())
			{
				Frame->BoneRotations.Reserve((*BonesObj)->Values.Num());
				for (const auto& BonePair : (*BonesObj)->Values)
				{
					const FString& BodyName = BonePair.Key;
					if (!BonePair.Value.IsValid()
					    || BonePair.Value->Type != EJson::Object)
					{
						continue;
					}
					TSharedPtr<FJsonObject> BoneObj = BonePair.Value->AsObject();
					const TArray<TSharedPtr<FJsonValue>>* OriArr = nullptr;
					if (!BoneObj->TryGetArrayField(TEXT("orientation"), OriArr)
					    || !OriArr || OriArr->Num() != 4)
					{
						continue;
					}
					FMuJoCoBoneRotation Rot;
					Rot.MuJoCoBodyName = BodyName;
					const double W = (*OriArr)[0]->AsNumber();
					const double X = (*OriArr)[1]->AsNumber();
					const double Y = (*OriArr)[2]->AsNumber();
					const double Z = (*OriArr)[3]->AsNumber();
					Rot.ParentRelative = FQuat(X, Y, Z, W);
					Frame->BoneRotations.Add(MoveTemp(Rot));
				}
			}

			Owner->PushFrame(Frame);
			++PerFrameAssets;
		}

		Owner->FramesReceived.Increment();
		Owner->LastFrameSeq.Set(Seq);
		UE_LOG(LogSeniorCareBridge, Verbose,
		       TEXT("[Bridge] frame seq=%lld assets=%d"),
		       Seq, PerFrameAssets);
	}

	UMuJoCoBridgeSubsystem* Owner;
	FString Endpoint;
	std::atomic<bool> bStopRequested{false};
};

// ---------------------------------------------------------------------------
// UMuJoCoBridgeSubsystem
// ---------------------------------------------------------------------------

void UMuJoCoBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	UE_LOG(LogSeniorCareBridge, Log,
	       TEXT("UMuJoCoBridgeSubsystem::Initialize -> connecting to '%s'"),
	       *Endpoint);
	StartWorker();

	// Editor-tick driver: fire OnEditorTick every frame on the game
	// thread. We use this to fan the latest frame out to every live
	// UMuJoCoDrivenSkeletonComponent because UActorComponent ticks
	// don't reliably run for actors spawned via UEditorActorSubsystem.
	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &UMuJoCoBridgeSubsystem::OnEditorTick),
		0.0f);
}

void UMuJoCoBridgeSubsystem::Deinitialize()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}
	StopWorker();
	{
		FScopeLock Lock(&FramesMutex);
		LatestFrames.Empty();
	}
	Super::Deinitialize();
}

bool UMuJoCoBridgeSubsystem::OnEditorTick(float DeltaSeconds)
{
	// Walk the actual editor world's actor list rather than going via
	// TObjectIterator: that path on UE 5.1 misses default-subobject
	// driver components on actors that were spawned at editor runtime.
	int32 ActorsScanned = 0;
	int32 DriversApplied = 0;
	int32 NoDriverComp = 0;

	UWorld* World = nullptr;
	if (GEditor)
	{
		World = GEditor->GetEditorWorldContext().World();
	}

	if (World)
	{
		for (TActorIterator<AMuJoCoSkeletalActor> It(World); It; ++It)
		{
			++ActorsScanned;
			AMuJoCoSkeletalActor* Actor = *It;
			if (!IsValid(Actor))
			{
				continue;
			}
			UMuJoCoDrivenSkeletonComponent* Driver = Actor->GetDriver();
			if (!IsValid(Driver))
			{
				++NoDriverComp;
				continue;
			}
			Driver->ApplyLatestFrame(DeltaSeconds);
			++DriversApplied;
		}
	}

	// Heartbeat: roughly every 2 seconds (assuming ~60Hz editor tick),
	// at Log level so it's visible without enabling Verbose.
	++TickCount;
	if ((TickCount % 120) == 0)
	{
		UE_LOG(LogSeniorCareBridge, Log,
		       TEXT("[Bridge] OnEditorTick heartbeat: world=%s actors_scanned=%d "
		            "drivers_applied=%d no_driver=%d frames_received=%d"),
		       World ? *World->GetName() : TEXT("<null>"),
		       ActorsScanned, DriversApplied, NoDriverComp,
		       FramesReceived.GetValue());
	}
	return true; // keep ticking
}

void UMuJoCoBridgeSubsystem::Reconnect(const FString& InEndpoint)
{
	StopWorker();
	Endpoint = InEndpoint;
	StartWorker();
}

void UMuJoCoBridgeSubsystem::StartWorker()
{
	StopWorker(); // idempotent
	Worker = MakeUnique<FBridgeRunnable>(this, Endpoint);
	WorkerThread.Reset(FRunnableThread::Create(
		Worker.Get(), TEXT("SeniorCareBridge_Sub"),
		0, TPri_BelowNormal));
}

void UMuJoCoBridgeSubsystem::StopWorker()
{
	if (Worker.IsValid())
	{
		Worker->Stop();
	}
	if (WorkerThread.IsValid())
	{
		WorkerThread->WaitForCompletion();
		WorkerThread.Reset();
	}
	Worker.Reset();
}

void UMuJoCoBridgeSubsystem::PushFrame(const TSharedRef<FMuJoCoAssetFrame>& Frame)
{
	FScopeLock Lock(&FramesMutex);
	LatestFrames.Add(Frame->AssetName, Frame);
}

bool UMuJoCoBridgeSubsystem::LatestFrameForAsset(const FString& AssetName,
                                                  FMuJoCoAssetFrame& OutFrame) const
{
	FScopeLock Lock(&FramesMutex);
	const TSharedRef<FMuJoCoAssetFrame>* Found = LatestFrames.Find(AssetName);
	if (!Found)
	{
		return false;
	}
	OutFrame = **Found; // shallow copy of POD struct
	return true;
}
