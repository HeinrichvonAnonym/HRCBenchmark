// Copyright SeniorCare.

#include "MuJoCoDrivenSkeletonComponent.h"

#include "MuJoCoBridgeSubsystem.h"
#include "MuJoCoSkeletalActor.h"
#include "SeniorCareBridge.h"

#include "Components/PoseableMeshComponent.h"
#include "Editor.h"
#include "GameFramework/Actor.h"

#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
	UMuJoCoBridgeSubsystem* GetBridgeSubsystem()
	{
		if (GEditor)
		{
			return GEditor->GetEditorSubsystem<UMuJoCoBridgeSubsystem>();
		}
		return nullptr;
	}

	/**
	 * Build a rotation of <Value> radians around the given local axis.
	 * Mirrors the convention used by the original
	 * Python-side _radians_to_unreal_rotator.
	 */
	FRotator AxisAngleToRotator(double ValueRad, TCHAR Axis)
	{
		const double Deg = FMath::RadiansToDegrees(ValueRad);
		switch (Axis)
		{
		case TEXT('x'):
		case TEXT('X'): return FRotator(0.0, 0.0, Deg);            // Roll
		case TEXT('y'):
		case TEXT('Y'): return FRotator(Deg, 0.0, 0.0);            // Pitch
		case TEXT('z'):
		case TEXT('Z'):
		default:        return FRotator(0.0, Deg, 0.0);            // Yaw
		}
	}
}

UMuJoCoDrivenSkeletonComponent::UMuJoCoDrivenSkeletonComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;
	bTickInEditor = true;
	bAutoActivate = true;
}

void UMuJoCoDrivenSkeletonComponent::BeginPlay()
{
	Super::BeginPlay();
}

void UMuJoCoDrivenSkeletonComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
}

void UMuJoCoDrivenSkeletonComponent::OnRegister()
{
	Super::OnRegister();
	ResolvePoseable();
}

void UMuJoCoDrivenSkeletonComponent::OnUnregister()
{
	Super::OnUnregister();
	CachedPoseable.Reset();
}

UPoseableMeshComponent* UMuJoCoDrivenSkeletonComponent::ResolvePoseable()
{
	if (UPoseableMeshComponent* Cached = CachedPoseable.Get())
	{
		return Cached;
	}
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return nullptr;
	}
	if (AMuJoCoSkeletalActor* Mu = Cast<AMuJoCoSkeletalActor>(Owner))
	{
		if (UPoseableMeshComponent* P = Mu->GetPoseableMesh())
		{
			CachedPoseable = P;
			return P;
		}
	}
	UPoseableMeshComponent* P = Owner->FindComponentByClass<UPoseableMeshComponent>();
	CachedPoseable = P;
	return P;
}

void UMuJoCoDrivenSkeletonComponent::SetBoneNameMappingJson(const FString& Json)
{
	JointDriveMap.Reset();

	if (Json.IsEmpty())
	{
		UE_LOG(LogSeniorCareBridge, Log,
		       TEXT("[Driver:%s] cleared joint->bone mapping"), *AssetName);
		return;
	}

	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
	TSharedPtr<FJsonObject> Root;
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		UE_LOG(LogSeniorCareBridge, Warning,
		       TEXT("[Driver:%s] could not parse mapping JSON: '%s'"),
		       *AssetName, *Json);
		return;
	}

	const TSharedPtr<FJsonObject>* JointToBone = nullptr;
	if (!Root->TryGetObjectField(TEXT("joint_to_bone"), JointToBone)
	    || !JointToBone || !JointToBone->IsValid())
	{
		UE_LOG(LogSeniorCareBridge, Warning,
		       TEXT("[Driver:%s] mapping JSON has no 'joint_to_bone' object"),
		       *AssetName);
		return;
	}

	for (const auto& Pair : (*JointToBone)->Values)
	{
		const FString& JointName = Pair.Key;
		if (!Pair.Value.IsValid())
		{
			continue;
		}

		FJointDriveEntry Entry;
		Entry.Axis = DefaultAxis.IsEmpty() ? TEXT('z') : DefaultAxis[0];

		// Allow shorthand: "joint_to_bone": {"j1": "boneA"} (string form)
		if (Pair.Value->Type == EJson::String)
		{
			Entry.BoneName = FName(*Pair.Value->AsString());
		}
		else if (Pair.Value->Type == EJson::Object)
		{
			TSharedPtr<FJsonObject> Obj = Pair.Value->AsObject();
			FString BoneStr, AxisStr;
			if (Obj->TryGetStringField(TEXT("bone"), BoneStr))
			{
				Entry.BoneName = FName(*BoneStr);
			}
			if (Obj->TryGetStringField(TEXT("axis"), AxisStr) && !AxisStr.IsEmpty())
			{
				Entry.Axis = AxisStr[0];
			}
		}
		else
		{
			continue;
		}

		if (Entry.BoneName == NAME_None)
		{
			continue;
		}
		JointDriveMap.Add(JointName, Entry);
	}

	UE_LOG(LogSeniorCareBridge, Log,
	       TEXT("[Driver:%s] joint->bone mapping loaded (%d entries)"),
	       *AssetName, JointDriveMap.Num());
	if (JointDriveMap.Num() == 0)
	{
		const int32 PreviewLen = FMath::Min(Json.Len(), 256);
		UE_LOG(LogSeniorCareBridge, Warning,
		       TEXT("[Driver:%s] mapping parsed to 0 entries. "
		            "joint_to_bone fields=%d. JSON preview: %s"),
		       *AssetName, (*JointToBone)->Values.Num(),
		       *Json.Left(PreviewLen));
	}
	bWarnedEmptyMapping = false;
}

void UMuJoCoDrivenSkeletonComponent::TickComponent(
	float DeltaTime, ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	// Belt-and-suspenders: if UActorComponent ticks happen to be firing
	// (PIE / standalone), use them. The subsystem ticker also calls us;
	// LastAppliedSeq dedupes so this is safe.
	ApplyLatestFrame(DeltaTime);
}

void UMuJoCoDrivenSkeletonComponent::ApplyLatestFrame(float DeltaSeconds)
{
	if (AssetName.IsEmpty())
	{
		return;
	}

	UMuJoCoBridgeSubsystem* Bridge = GetBridgeSubsystem();
	if (!Bridge)
	{
		return;
	}

	FMuJoCoAssetFrame Frame;
	if (!Bridge->LatestFrameForAsset(AssetName, Frame))
	{
		return;
	}

	if (Frame.Seq == LastAppliedSeq)
	{
		return; // nothing new
	}
	LastAppliedSeq = Frame.Seq;

	UPoseableMeshComponent* Poseable = ResolvePoseable();
	if (!Poseable)
	{
		return;
	}

	if (JointDriveMap.Num() == 0)
	{
		if (!bWarnedEmptyMapping)
		{
			UE_LOG(LogSeniorCareBridge, Warning,
			       TEXT("[Driver:%s] received frame seq=%lld but no "
			            "joint->bone mapping was set; nothing will move."),
			       *AssetName, Frame.Seq);
			bWarnedEmptyMapping = true;
		}
		return;
	}

	int32 Applied = 0;
	int32 Missed = 0;
	FString FirstAppliedDiag;
	for (const auto& Pair : Frame.Joints)
	{
		const FString& JointName = Pair.Key;
		const double Value = Pair.Value;

		const FJointDriveEntry* Entry = JointDriveMap.Find(JointName);
		if (!Entry)
		{
			++Missed;
			continue;
		}
		const int32 BoneIdx = Poseable->GetBoneIndex(Entry->BoneName);
		if (BoneIdx == INDEX_NONE)
		{
			UE_LOG(LogSeniorCareBridge, Verbose,
			       TEXT("[Driver:%s] bone '%s' (joint '%s') not on PoseableMesh"),
			       *AssetName, *Entry->BoneName.ToString(), *JointName);
			++Missed;
			continue;
		}
		const FRotator Rot = AxisAngleToRotator(Value, Entry->Axis);

		// Drive the bone in PARENT-LOCAL space by overwriting the
		// BoneSpaceTransforms entry. UPoseableMeshComponent stores
		// per-bone local transforms here; the renderer composes them
		// into a world pose during refresh. ComponentSpace input via
		// SetBoneRotationByName has subtle offset semantics and ends
		// up not visibly moving anything, so we go direct.
		if (BoneIdx >= 0 && BoneIdx < Poseable->BoneSpaceTransforms.Num())
		{
			FTransform LocalT = Poseable->BoneSpaceTransforms[BoneIdx];
			LocalT.SetRotation(Rot.Quaternion());
			Poseable->BoneSpaceTransforms[BoneIdx] = LocalT;
			if (Applied == 0)
			{
				FirstAppliedDiag = FString::Printf(
					TEXT("first: joint='%s' bone='%s' axis=%c value=%.3frad rot=(%.1f,%.1f,%.1f)deg idx=%d"),
					*JointName, *Entry->BoneName.ToString(), Entry->Axis,
					Value, Rot.Pitch, Rot.Yaw, Rot.Roll, BoneIdx);
			}
			++Applied;
		}
		else
		{
			++Missed;
		}
	}

	if (Applied > 0)
	{
		// Force the renderer + child component transforms to refresh.
		// Without this, the BoneSpaceTransforms write doesn't propagate
		// to the visible skeleton on the editor world.
		Poseable->RefreshBoneTransforms();
		Poseable->MarkRenderStateDirty();
	}

	// Log first 2 frames after we get a mapping, then every 60th, so
	// you can verify motion without verbose. Drops to Verbose otherwise.
	const bool bShouldLogLog =
		(Applied > 0)
		&& (LastAppliedSeq <= 2 || (LastAppliedSeq % 60) == 0);
	if (bShouldLogLog)
	{
		UE_LOG(LogSeniorCareBridge, Log,
		       TEXT("[Driver:%s] seq=%lld applied=%d missed=%d (frame.joints=%d) %s"),
		       *AssetName, Frame.Seq, Applied, Missed, Frame.Joints.Num(),
		       *FirstAppliedDiag);
	}
	else
	{
		UE_LOG(LogSeniorCareBridge, Verbose,
		       TEXT("[Driver:%s] seq=%lld applied=%d missed=%d (frame.joints=%d)"),
		       *AssetName, Frame.Seq, Applied, Missed, Frame.Joints.Num());
	}
}
