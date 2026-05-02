// Copyright SeniorCare.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MuJoCoDrivenSkeletonComponent.generated.h"

class UPoseableMeshComponent;

/**
 * Pulls the latest MuJoCo frame for a named asset from
 * UMuJoCoBridgeSubsystem each tick, and applies it to a sibling
 * UPoseableMeshComponent on the same actor. Ticks in editor so it
 * works under `test_ue.py` without having to enter PIE.
 */
UCLASS(ClassGroup = (SeniorCare), meta = (BlueprintSpawnableComponent))
class SENIORCAREBRIDGE_API UMuJoCoDrivenSkeletonComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMuJoCoDrivenSkeletonComponent();

	//~ Begin UActorComponent interface
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void OnRegister() override;
	virtual void OnUnregister() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
	                           FActorComponentTickFunction* ThisTickFunction) override;
	//~ End UActorComponent interface

	/** Owner actor's logical asset name; used as the routing key. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SeniorCare|Bridge")
	FString AssetName;

	/**
	 * JSON describing how to drive each MuJoCo joint:
	 *
	 *   {
	 *     "joint_to_bone": {
	 *       "panda_joint1": {"bone": "panda_joint1_revolute_bone", "axis": "z"},
	 *       "panda_joint2": {"bone": "panda_joint2_revolute_bone", "axis": "z"}
	 *     }
	 *   }
	 *
	 * Set once by Python after spawn (before any frames arrive).
	 */
	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	void SetBoneNameMappingJson(const FString& Json);

	/** If true, log per-frame diagnostics (very verbose). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SeniorCare|Bridge")
	bool bVerboseLogging = false;

	/** Default rotation axis for joints whose entry doesn't specify one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SeniorCare|Bridge")
	FString DefaultAxis = TEXT("z");

	/**
	 * If true, the actor's root transform will NOT be updated from MuJoCo frames.
	 * Set this for fixed-base assets like robot arms mounted to a table.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SeniorCare|Bridge")
	bool bFixBase = true;

	/** Set fix_base from Python setup script. */
	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	void SetFixBase(bool bInFixBase) { bFixBase = bInFixBase; }

	/**
	 * Rotation applied to the actor root BEFORE the MuJoCo root
	 * orientation, to reconcile the FBX bind pose with the MuJoCo
	 * SMPL-X rest pose.
	 *
	 * SMPL-X rest in MuJoCo: horizontal, face-UP (spine mujoco +Y,
	 * belly mujoco +Z). UE FBX bind (observed): spine bone-local +Z,
	 * belly bone-local -Y.
	 *
	 * Default Pitch=180, Roll=-90:
	 *   - Roll -90 lays the standing FBX spine from +Z down to -Y (UE).
	 *   - Pitch 180 flips the body around its long axis so belly faces
	 *     +Z (face-UP), matching MuJoCo.
	 *
	 * Only used when bFixBase == false. Editor-tunable live; if
	 * left/right or facing direction is still off, try alternatives
	 * such as FRotator(0,180,-90) or FRotator(180,180,-90) without
	 * recompiling.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SeniorCare|Bridge")
	FRotator RootOrientationOffset = FRotator(180.0, 0.0, -90.0);

	/** Set RootOrientationOffset from Python setup script. */
	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	void SetRootOrientationOffset(FRotator InOffset) { RootOrientationOffset = InOffset; }

	/**
	 * Pull the latest frame for AssetName from the bridge subsystem and
	 * apply joint rotations to the sibling PoseableMesh. Public so the
	 * subsystem's editor-tick driver can invoke us when UActorComponent
	 * ticks aren't firing reliably (UE 5.1 editor-spawned actors).
	 */
	void ApplyLatestFrame(float DeltaSeconds);

private:
	struct FJointDriveEntry
	{
		FName BoneName;
		TCHAR Axis = TEXT('z');
	};

	/** Cached pointer to the sibling PoseableMesh on the owning actor. */
	TWeakObjectPtr<UPoseableMeshComponent> CachedPoseable;

	/** joint_name -> drive entry. */
	TMap<FString, FJointDriveEntry> JointDriveMap;

	/** Last applied frame sequence; skip duplicates. */
	int64 LastAppliedSeq = -1;

	/** Logged once if mapping was empty / never set. */
	bool bWarnedEmptyMapping = false;

	/** Initial bone transforms captured from bind pose; used as base for delta rotations. */
	TArray<FTransform> InitialBoneTransforms;

	/**
	 * Cumulative world-space rotation of each bone at bind (rest) pose.
	 * Used by the quaternion ball-joint formula to apply MuJoCo rotations
	 * in the correct parent-world frame.
	 */
	TArray<FQuat> InitialBoneWorldRotations;

	/** True once we've captured the initial bone transforms. */
	bool bHasCapturedInitialPose = false;

	/** Resolve / refresh CachedPoseable if needed; returns nullptr on failure. */
	UPoseableMeshComponent* ResolvePoseable();

	/** Capture the current bone transforms as the initial (bind) pose. */
	void CaptureInitialPose(UPoseableMeshComponent* Poseable);
};
