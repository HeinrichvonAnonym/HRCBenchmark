// Copyright SeniorCare.

#include "MuJoCoSkeletalActor.h"
#include "MuJoCoDrivenSkeletonComponent.h"
#include "SeniorCareBridge.h"

#include "Components/SceneComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Engine/SkeletalMesh.h"

AMuJoCoSkeletalActor::AMuJoCoSkeletalActor()
{
	PrimaryActorTick.bCanEverTick = false;

	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	RootComponent = SceneRoot;

	PoseableMesh = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("PoseableMesh"));
	PoseableMesh->SetupAttachment(RootComponent);
	PoseableMesh->SetVisibility(true);
	PoseableMesh->SetHiddenInGame(false);
	PoseableMesh->bCastDynamicShadow = true;

	Driver = CreateDefaultSubobject<UMuJoCoDrivenSkeletonComponent>(TEXT("Driver"));
}

void AMuJoCoSkeletalActor::BeginPlay()
{
	Super::BeginPlay();
	if (Driver && Driver->AssetName.IsEmpty())
	{
		Driver->AssetName = AssetName;
	}
}

void AMuJoCoSkeletalActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
}

void AMuJoCoSkeletalActor::SetSkinnedAsset(USkeletalMesh* Mesh)
{
	if (!PoseableMesh)
	{
		UE_LOG(LogSeniorCareBridge, Warning,
		       TEXT("SetSkinnedAsset called but PoseableMesh is null on '%s'."),
		       *GetName());
		return;
	}

	PoseableMesh->SetSkinnedAssetAndUpdate(Mesh, /*bReinitPose=*/true);

	UE_LOG(LogSeniorCareBridge, Log,
	       TEXT("[%s] PoseableMesh skinned asset set to '%s' (%d bones)"),
	       *GetName(),
	       Mesh ? *Mesh->GetName() : TEXT("<null>"),
	       Mesh ? PoseableMesh->GetNumBones() : 0);
}

void AMuJoCoSkeletalActor::SetAssetName(const FString& InAssetName)
{
	AssetName = InAssetName;
	if (Driver)
	{
		Driver->AssetName = InAssetName;
	}
}

void AMuJoCoSkeletalActor::SetBoneNameMappingJson(const FString& Json)
{
	UE_LOG(LogSeniorCareBridge, Log,
	       TEXT("[%s] SetBoneNameMappingJson called (asset='%s', json_len=%d, "
	            "driver=%s)"),
	       *GetName(), *AssetName, Json.Len(),
	       Driver ? TEXT("ok") : TEXT("NULL"));
	if (Driver)
	{
		Driver->SetBoneNameMappingJson(Json);
	}
	else
	{
		UE_LOG(LogSeniorCareBridge, Warning,
		       TEXT("[%s] SetBoneNameMappingJson dropped: Driver is null"),
		       *GetName());
	}
}
