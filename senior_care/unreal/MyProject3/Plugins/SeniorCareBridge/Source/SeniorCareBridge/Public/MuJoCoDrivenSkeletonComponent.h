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

	/** Resolve / refresh CachedPoseable if needed; returns nullptr on failure. */
	UPoseableMeshComponent* ResolvePoseable();
};
