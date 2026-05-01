// Copyright SeniorCare.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MuJoCoSkeletalActor.generated.h"

class USkeletalMesh;
class UPoseableMeshComponent;
class UMuJoCoDrivenSkeletonComponent;

/**
 * Actor that hosts a UPoseableMeshComponent driven by MuJoCo state.
 *
 * Designed to be spawned from Python (replaces ASkeletalMeshActor +
 * manual UPoseableMeshComponent attach path that was unreliable on
 * UE 5.1's Python bindings). The PoseableMesh is created via
 * CreateDefaultSubobject so it auto-registers with the scene.
 *
 * Python is expected to:
 *   1. Spawn this actor at the desired location.
 *   2. Call SetSkinnedAsset(mesh) to assign the skeletal mesh.
 *   3. Call SetAssetName("franka_emika_panda") so the bridge subsystem
 *      can route incoming MuJoCo frames to this actor.
 *   4. (Optional) Call SetBoneNameMappingJson(...) with a JSON object
 *      mapping MuJoCo body name -> UE bone name.
 */
UCLASS(Blueprintable, BlueprintType)
class SENIORCAREBRIDGE_API AMuJoCoSkeletalActor : public AActor
{
	GENERATED_BODY()

public:
	AMuJoCoSkeletalActor();

	//~ Begin AActor interface
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	//~ End AActor interface

	/** Assign the SkeletalMesh that the PoseableMesh will pose. */
	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	void SetSkinnedAsset(USkeletalMesh* Mesh);

	/** Logical asset name used as the routing key for MuJoCo frames. */
	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	void SetAssetName(const FString& InAssetName);

	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	FString GetAssetName() const { return AssetName; }

	/** Tell the driver how to map MuJoCo body names to UE bone names. */
	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	void SetBoneNameMappingJson(const FString& Json);

	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	UPoseableMeshComponent* GetPoseableMesh() const { return PoseableMesh; }

	UFUNCTION(BlueprintCallable, Category = "SeniorCare|Bridge")
	UMuJoCoDrivenSkeletonComponent* GetDriver() const { return Driver; }

protected:
	/** Asset routing key (e.g. "franka_emika_panda"). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SeniorCare|Bridge")
	FString AssetName;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SeniorCare|Bridge")
	TObjectPtr<USceneComponent> SceneRoot;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SeniorCare|Bridge")
	TObjectPtr<UPoseableMeshComponent> PoseableMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SeniorCare|Bridge")
	TObjectPtr<UMuJoCoDrivenSkeletonComponent> Driver;
};
