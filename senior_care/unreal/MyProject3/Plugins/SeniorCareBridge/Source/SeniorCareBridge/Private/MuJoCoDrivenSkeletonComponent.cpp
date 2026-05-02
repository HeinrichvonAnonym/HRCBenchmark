// Copyright SeniorCare.

#include "MuJoCoDrivenSkeletonComponent.h"

#include "MuJoCoBridgeSubsystem.h"
#include "MuJoCoSkeletalActor.h"
#include "SeniorCareBridge.h"

#include "Components/PoseableMeshComponent.h"
#include "Editor.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Actor.h"
#include "ReferenceSkeleton.h"

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
	 *
	 * Coordinate system conversion: MuJoCo uses right-handed (Y left),
	 * UE uses left-handed (Y right). This means:
	 *   - X axis rotation: same direction → no sign flip
	 *   - Y axis rotation: opposite direction → NEGATE
	 *   - Z axis rotation: same direction → no sign flip
	 */
	FRotator AxisAngleToRotator(double ValueRad, TCHAR Axis)
	{
		const double Deg = FMath::RadiansToDegrees(ValueRad);
		switch (Axis)
		{
		case TEXT('x'):
		case TEXT('X'): return FRotator(0.0, 0.0, Deg);            // Roll (X unchanged)
		case TEXT('y'):
		case TEXT('Y'): return FRotator(-Deg, 0.0, 0.0);           // Pitch (Y negated for handedness)
		case TEXT('z'):
		case TEXT('Z'):
		default:        return FRotator(0.0, Deg, 0.0);            // Yaw (Z unchanged)
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

void UMuJoCoDrivenSkeletonComponent::CaptureInitialPose(UPoseableMeshComponent* Poseable)
{
	if (!Poseable || bHasCapturedInitialPose)
	{
		return;
	}

	InitialBoneTransforms = Poseable->BoneSpaceTransforms;
	bHasCapturedInitialPose = true;

	// Build cumulative world-space bind rotations by walking the
	// reference skeleton hierarchy. Needed for quaternion ball-joint
	// application (see ApplyLatestFrame).
	InitialBoneWorldRotations.Reset();
	USkinnedAsset* SkinnedAsset = Poseable->GetSkinnedAsset();
	if (SkinnedAsset)
	{
		const FReferenceSkeleton& RefSkel = SkinnedAsset->GetRefSkeleton();
		const int32 NumBones = RefSkel.GetNum();
		InitialBoneWorldRotations.SetNum(NumBones);
		for (int32 i = 0; i < NumBones; ++i)
		{
			const int32 ParentIdx = RefSkel.GetParentIndex(i);
			const FQuat ParentWorld = (ParentIdx >= 0 && ParentIdx < InitialBoneWorldRotations.Num())
				? InitialBoneWorldRotations[ParentIdx]
				: FQuat::Identity;
			const FQuat BoneLocalRest = (i < InitialBoneTransforms.Num())
				? InitialBoneTransforms[i].GetRotation()
				: FQuat::Identity;
			InitialBoneWorldRotations[i] = ParentWorld * BoneLocalRest;
		}
	}

	UE_LOG(LogSeniorCareBridge, Log,
	       TEXT("[Driver:%s] captured initial pose (%d bones, %d world rotations)"),
	       *AssetName, InitialBoneTransforms.Num(), InitialBoneWorldRotations.Num());
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

	// Apply root transform for non-fixed-base assets (e.g. human body).
	// Fixed-base assets (e.g. robot arm) keep their spawned position.
	if (!bFixBase)
	{
		AActor* Owner = GetOwner();
		if (Owner)
		{
			// Compose RootOrientationOffset with the MuJoCo root quaternion.
			// The offset is applied FIRST (brings the FBX bind pose from
			// standing/vertical to the MuJoCo rest pose's horizontal
			// orientation), then the MuJoCo root rotation is applied on
			// top so the character follows physics-driven root motion.
			const FQuat Offset = RootOrientationOffset.Quaternion();
			const FQuat FinalActorQuat = Frame.RootOrientation * Offset;

			Owner->SetActorLocation(Frame.RootPosition);
			Owner->SetActorRotation(FinalActorQuat.Rotator());

			// Diag every ~1s at 120Hz so we can verify the composition
			// and tune RootOrientationOffset live if the sign/axis is off.
			if ((Frame.Seq % 120) == 0)
			{
				const FRotator InE = Frame.RootOrientation.Rotator();
				const FRotator FinalE = FinalActorQuat.Rotator();
				UE_LOG(LogSeniorCareBridge, Log,
				       TEXT("[Driver:%s][ROOT seq=%lld] raw=(P%+.1f,Y%+.1f,R%+.1f) "
				            "offset=(P%+.1f,Y%+.1f,R%+.1f) "
				            "final=(P%+.1f,Y%+.1f,R%+.1f)"),
				       *AssetName, Frame.Seq,
				       InE.Pitch, InE.Yaw, InE.Roll,
				       RootOrientationOffset.Pitch,
				       RootOrientationOffset.Yaw,
				       RootOrientationOffset.Roll,
				       FinalE.Pitch, FinalE.Yaw, FinalE.Roll);
			}
		}
	}

	UPoseableMeshComponent* Poseable = ResolvePoseable();
	if (!Poseable)
	{
		return;
	}

	// Capture bind pose on first frame so we can apply rotations on top of it.
	if (!bHasCapturedInitialPose)
	{
		CaptureInitialPose(Poseable);
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

	// Collect per-bone rotation components. 'w' axis means quaternion
	// mode (full rotation in parent world frame, for ball joints).
	// 'x'/'y'/'z' alone means axis-angle (legacy, for revolute joints).
	struct FBoneRotationAccum
	{
		int32 BoneIdx = INDEX_NONE;
		double RotW = 1.0;
		double RotX = 0.0;
		double RotY = 0.0;
		double RotZ = 0.0;
		bool bHasW = false;
		bool bHasX = false;
		bool bHasY = false;
		bool bHasZ = false;
	};
	TMap<FName, FBoneRotationAccum> BoneAccum;

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

		FBoneRotationAccum& Accum = BoneAccum.FindOrAdd(Entry->BoneName);
		Accum.BoneIdx = BoneIdx;
		switch (Entry->Axis)
		{
		case TEXT('w'):
		case TEXT('W'):
			Accum.RotW = Value; Accum.bHasW = true; break;
		case TEXT('x'):
		case TEXT('X'):
			Accum.RotX = Value; Accum.bHasX = true; break;
		case TEXT('y'):
		case TEXT('Y'):
			Accum.RotY = Value; Accum.bHasY = true; break;
		case TEXT('z'):
		case TEXT('Z'):
		default:
			Accum.RotZ = Value; Accum.bHasZ = true; break;
		}
	}

	const FReferenceSkeleton* RefSkel = nullptr;
	if (USkinnedAsset* SkinnedAsset = Poseable->GetSkinnedAsset())
	{
		RefSkel = &SkinnedAsset->GetRefSkeleton();
	}

	for (const auto& AccumPair : BoneAccum)
	{
		const FBoneRotationAccum& Accum = AccumPair.Value;
		const int32 BoneIdx = Accum.BoneIdx;
		if (BoneIdx < 0 || BoneIdx >= Poseable->BoneSpaceTransforms.Num()
		    || BoneIdx >= InitialBoneTransforms.Num())
		{
			++Missed;
			continue;
		}

		const FQuat InitialRot = InitialBoneTransforms[BoneIdx].GetRotation();
		FQuat FinalRot;

		if (Accum.bHasW)
		{
			// Quaternion mode: (w, x, y, z) already handedness-flipped
			// in Python. Apply with parent-frame formula:
			//   FinalLocal = ParentWorldRest^-1 * Q_ue * ParentWorldRest * BindRot
			const FQuat QuatUe(Accum.RotX, Accum.RotY, Accum.RotZ, Accum.RotW);
			FQuat ParentWorldRest = FQuat::Identity;
			if (RefSkel)
			{
				const int32 ParentIdx = RefSkel->GetParentIndex(BoneIdx);
				if (ParentIdx >= 0 && ParentIdx < InitialBoneWorldRotations.Num())
				{
					ParentWorldRest = InitialBoneWorldRotations[ParentIdx];
				}
			}
			FinalRot = ParentWorldRest.Inverse() * QuatUe * ParentWorldRest * InitialRot;
		}
		else
		{
			// Axis-angle mode (legacy for revolute joints like Franka).
			FQuat CombinedDelta = FQuat::Identity;
			if (Accum.bHasX)
			{
				CombinedDelta = CombinedDelta * AxisAngleToRotator(Accum.RotX, TEXT('x')).Quaternion();
			}
			if (Accum.bHasY)
			{
				CombinedDelta = CombinedDelta * AxisAngleToRotator(Accum.RotY, TEXT('y')).Quaternion();
			}
			if (Accum.bHasZ)
			{
				CombinedDelta = CombinedDelta * AxisAngleToRotator(Accum.RotZ, TEXT('z')).Quaternion();
			}
			FinalRot = InitialRot * CombinedDelta;
		}

		FTransform LocalT = Poseable->BoneSpaceTransforms[BoneIdx];
		LocalT.SetRotation(FinalRot);
		Poseable->BoneSpaceTransforms[BoneIdx] = LocalT;
		if (Applied == 0)
		{
			FirstAppliedDiag = FString::Printf(
				TEXT("first: bone='%s' idx=%d hasWXYZ=(%d,%d,%d,%d)"),
				*AccumPair.Key.ToString(), BoneIdx,
				Accum.bHasW ? 1 : 0, Accum.bHasX ? 1 : 0,
				Accum.bHasY ? 1 : 0, Accum.bHasZ ? 1 : 0);
		}
		++Applied;
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
