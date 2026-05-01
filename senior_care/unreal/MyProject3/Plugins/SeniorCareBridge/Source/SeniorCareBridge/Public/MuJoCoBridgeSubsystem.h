// Copyright SeniorCare.
#pragma once

#include "CoreMinimal.h"
#include "EditorSubsystem.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "Containers/Queue.h"
#include "Containers/Ticker.h"
#include "MuJoCoBridgeSubsystem.generated.h"

class FRunnableThread;

/** Per-bone parent-relative rotation pulled from MuJoCo. */
struct FMuJoCoBoneRotation
{
	FString MuJoCoBodyName;
	FQuat ParentRelative = FQuat::Identity;
};

/** Single MuJoCo frame for a single asset. */
struct FMuJoCoAssetFrame
{
	FString AssetName;
	int64 Seq = 0;
	double TimestampSec = 0.0;
	FVector RootPosition = FVector::ZeroVector;     // world units (cm)
	FQuat RootOrientation = FQuat::Identity;

	/** Joint angles (radians). Drives bone rotations about a local axis. */
	TMap<FString, double> Joints;

	/** Per-body world orientations (kept for future drivers that need them). */
	TArray<FMuJoCoBoneRotation> BoneRotations;

	/** Updated every time this frame was overwritten by a newer one. */
	double ReceivedAtSec = 0.0;
};

/**
 * Editor subsystem that runs a background thread subscribing to
 * MuJoCo state frames over ZMQ (tcp://localhost:5556 by default)
 * and exposes the latest frame per asset for drivers to read.
 */
UCLASS()
class SENIORCAREBRIDGE_API UMuJoCoBridgeSubsystem : public UEditorSubsystem
{
	GENERATED_BODY()

public:
	//~ Begin UEditorSubsystem
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	//~ End UEditorSubsystem

	/**
	 * Read the most recent frame for an asset name. Returns false
	 * if no frame has ever been received for that name.
	 */
	bool LatestFrameForAsset(const FString& AssetName, FMuJoCoAssetFrame& OutFrame) const;

	/** Restart the SUB thread on a new endpoint. Call from python/editor. */
	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	void Reconnect(const FString& Endpoint);

	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	FString GetEndpoint() const { return Endpoint; }

	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	int64 GetFramesReceived() const { return FramesReceived.GetValue(); }

	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	int64 GetLastFrameSeq() const { return LastFrameSeq.GetValue(); }

private:
	/** ZMQ SUB worker, friend so it can publish frames. */
	class FBridgeRunnable;
	friend class FBridgeRunnable;

	void StartWorker();
	void StopWorker();

	/** Called from the worker thread. Stores or overwrites the latest frame. */
	void PushFrame(const TSharedRef<FMuJoCoAssetFrame>& Frame);

	UPROPERTY()
	FString Endpoint = TEXT("tcp://localhost:5556");

	mutable FCriticalSection FramesMutex;
	TMap<FString, TSharedRef<FMuJoCoAssetFrame>> LatestFrames;

	TUniquePtr<FBridgeRunnable> Worker;
	TUniquePtr<FRunnableThread> WorkerThread;

	FThreadSafeCounter FramesReceived;
	FThreadSafeCounter64 LastFrameSeq;

	/**
	 * Editor-tick driver: fans the latest frame out to every live
	 * UMuJoCoDrivenSkeletonComponent. We use FTSTicker because
	 * UActorComponent::bTickInEditor doesn't fire reliably for actors
	 * spawned via UEditorActorSubsystem on UE 5.1 -- this bypass
	 * routes through a guaranteed-every-frame hook on the game thread.
	 */
	bool OnEditorTick(float DeltaSeconds);
	FTSTicker::FDelegateHandle TickerHandle;

	/** Counts editor-ticks; used to throttle heartbeat logging. */
	int64 TickCount = 0;
};
