// Copyright Epic Games, Inc. All Rights Reserved.
/*===========================================================================
	Generated code exported from UnrealHeaderTool.
	DO NOT modify this manually! Edit the corresponding .h files instead!
===========================================================================*/

#include "UObject/GeneratedCppIncludes.h"
#include "SeniorCareBridge/Public/MuJoCoSkeletalActor.h"
PRAGMA_DISABLE_DEPRECATION_WARNINGS
void EmptyLinkFunctionForGeneratedCodeMuJoCoSkeletalActor() {}
// Cross Module References
	ENGINE_API UClass* Z_Construct_UClass_AActor();
	ENGINE_API UClass* Z_Construct_UClass_UPoseableMeshComponent_NoRegister();
	ENGINE_API UClass* Z_Construct_UClass_USceneComponent_NoRegister();
	ENGINE_API UClass* Z_Construct_UClass_USkeletalMesh_NoRegister();
	SENIORCAREBRIDGE_API UClass* Z_Construct_UClass_AMuJoCoSkeletalActor();
	SENIORCAREBRIDGE_API UClass* Z_Construct_UClass_AMuJoCoSkeletalActor_NoRegister();
	SENIORCAREBRIDGE_API UClass* Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_NoRegister();
	UPackage* Z_Construct_UPackage__Script_SeniorCareBridge();
// End Cross Module References
	DEFINE_FUNCTION(AMuJoCoSkeletalActor::execGetDriver)
	{
		P_FINISH;
		P_NATIVE_BEGIN;
		*(UMuJoCoDrivenSkeletonComponent**)Z_Param__Result=P_THIS->GetDriver();
		P_NATIVE_END;
	}
	DEFINE_FUNCTION(AMuJoCoSkeletalActor::execGetPoseableMesh)
	{
		P_FINISH;
		P_NATIVE_BEGIN;
		*(UPoseableMeshComponent**)Z_Param__Result=P_THIS->GetPoseableMesh();
		P_NATIVE_END;
	}
	DEFINE_FUNCTION(AMuJoCoSkeletalActor::execSetBoneNameMappingJson)
	{
		P_GET_PROPERTY(FStrProperty,Z_Param_Json);
		P_FINISH;
		P_NATIVE_BEGIN;
		P_THIS->SetBoneNameMappingJson(Z_Param_Json);
		P_NATIVE_END;
	}
	DEFINE_FUNCTION(AMuJoCoSkeletalActor::execGetAssetName)
	{
		P_FINISH;
		P_NATIVE_BEGIN;
		*(FString*)Z_Param__Result=P_THIS->GetAssetName();
		P_NATIVE_END;
	}
	DEFINE_FUNCTION(AMuJoCoSkeletalActor::execSetAssetName)
	{
		P_GET_PROPERTY(FStrProperty,Z_Param_InAssetName);
		P_FINISH;
		P_NATIVE_BEGIN;
		P_THIS->SetAssetName(Z_Param_InAssetName);
		P_NATIVE_END;
	}
	DEFINE_FUNCTION(AMuJoCoSkeletalActor::execSetSkinnedAsset)
	{
		P_GET_OBJECT(USkeletalMesh,Z_Param_Mesh);
		P_FINISH;
		P_NATIVE_BEGIN;
		P_THIS->SetSkinnedAsset(Z_Param_Mesh);
		P_NATIVE_END;
	}
	void AMuJoCoSkeletalActor::StaticRegisterNativesAMuJoCoSkeletalActor()
	{
		UClass* Class = AMuJoCoSkeletalActor::StaticClass();
		static const FNameNativePtrPair Funcs[] = {
			{ "GetAssetName", &AMuJoCoSkeletalActor::execGetAssetName },
			{ "GetDriver", &AMuJoCoSkeletalActor::execGetDriver },
			{ "GetPoseableMesh", &AMuJoCoSkeletalActor::execGetPoseableMesh },
			{ "SetAssetName", &AMuJoCoSkeletalActor::execSetAssetName },
			{ "SetBoneNameMappingJson", &AMuJoCoSkeletalActor::execSetBoneNameMappingJson },
			{ "SetSkinnedAsset", &AMuJoCoSkeletalActor::execSetSkinnedAsset },
		};
		FNativeFunctionRegistrar::RegisterFunctions(Class, Funcs, UE_ARRAY_COUNT(Funcs));
	}
	struct Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics
	{
		struct MuJoCoSkeletalActor_eventGetAssetName_Parms
		{
			FString ReturnValue;
		};
		static const UECodeGen_Private::FStrPropertyParams NewProp_ReturnValue;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::NewProp_ReturnValue = { "ReturnValue", nullptr, (EPropertyFlags)0x0010000000000580, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoSkeletalActor_eventGetAssetName_Parms, ReturnValue), METADATA_PARAMS(nullptr, 0) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::NewProp_ReturnValue,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_AMuJoCoSkeletalActor, nullptr, "GetAssetName", nullptr, nullptr, sizeof(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::MuJoCoSkeletalActor_eventGetAssetName_Parms), Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x54020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	struct Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics
	{
		struct MuJoCoSkeletalActor_eventGetDriver_Parms
		{
			UMuJoCoDrivenSkeletonComponent* ReturnValue;
		};
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_ReturnValue_MetaData[];
#endif
		static const UECodeGen_Private::FObjectPropertyParams NewProp_ReturnValue;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::NewProp_ReturnValue_MetaData[] = {
		{ "EditInline", "true" },
	};
#endif
	const UECodeGen_Private::FObjectPropertyParams Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::NewProp_ReturnValue = { "ReturnValue", nullptr, (EPropertyFlags)0x0010000000080588, UECodeGen_Private::EPropertyGenFlags::Object, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoSkeletalActor_eventGetDriver_Parms, ReturnValue), Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_NoRegister, METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::NewProp_ReturnValue_MetaData, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::NewProp_ReturnValue_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::NewProp_ReturnValue,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_AMuJoCoSkeletalActor, nullptr, "GetDriver", nullptr, nullptr, sizeof(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::MuJoCoSkeletalActor_eventGetDriver_Parms), Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x54020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	struct Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics
	{
		struct MuJoCoSkeletalActor_eventGetPoseableMesh_Parms
		{
			UPoseableMeshComponent* ReturnValue;
		};
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_ReturnValue_MetaData[];
#endif
		static const UECodeGen_Private::FObjectPropertyParams NewProp_ReturnValue;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::NewProp_ReturnValue_MetaData[] = {
		{ "EditInline", "true" },
	};
#endif
	const UECodeGen_Private::FObjectPropertyParams Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::NewProp_ReturnValue = { "ReturnValue", nullptr, (EPropertyFlags)0x0010000000080588, UECodeGen_Private::EPropertyGenFlags::Object, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoSkeletalActor_eventGetPoseableMesh_Parms, ReturnValue), Z_Construct_UClass_UPoseableMeshComponent_NoRegister, METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::NewProp_ReturnValue_MetaData, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::NewProp_ReturnValue_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::NewProp_ReturnValue,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_AMuJoCoSkeletalActor, nullptr, "GetPoseableMesh", nullptr, nullptr, sizeof(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::MuJoCoSkeletalActor_eventGetPoseableMesh_Parms), Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x54020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	struct Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics
	{
		struct MuJoCoSkeletalActor_eventSetAssetName_Parms
		{
			FString InAssetName;
		};
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_InAssetName_MetaData[];
#endif
		static const UECodeGen_Private::FStrPropertyParams NewProp_InAssetName;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::NewProp_InAssetName_MetaData[] = {
		{ "NativeConst", "" },
	};
#endif
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::NewProp_InAssetName = { "InAssetName", nullptr, (EPropertyFlags)0x0010000000000080, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoSkeletalActor_eventSetAssetName_Parms, InAssetName), METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::NewProp_InAssetName_MetaData, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::NewProp_InAssetName_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::NewProp_InAssetName,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/** Logical asset name used as the routing key for MuJoCo frames. */" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
		{ "ToolTip", "Logical asset name used as the routing key for MuJoCo frames." },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_AMuJoCoSkeletalActor, nullptr, "SetAssetName", nullptr, nullptr, sizeof(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::MuJoCoSkeletalActor_eventSetAssetName_Parms), Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x04020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	struct Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics
	{
		struct MuJoCoSkeletalActor_eventSetBoneNameMappingJson_Parms
		{
			FString Json;
		};
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_Json_MetaData[];
#endif
		static const UECodeGen_Private::FStrPropertyParams NewProp_Json;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::NewProp_Json_MetaData[] = {
		{ "NativeConst", "" },
	};
#endif
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::NewProp_Json = { "Json", nullptr, (EPropertyFlags)0x0010000000000080, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoSkeletalActor_eventSetBoneNameMappingJson_Parms, Json), METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::NewProp_Json_MetaData, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::NewProp_Json_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::NewProp_Json,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/** Tell the driver how to map MuJoCo body names to UE bone names. */" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
		{ "ToolTip", "Tell the driver how to map MuJoCo body names to UE bone names." },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_AMuJoCoSkeletalActor, nullptr, "SetBoneNameMappingJson", nullptr, nullptr, sizeof(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::MuJoCoSkeletalActor_eventSetBoneNameMappingJson_Parms), Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x04020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	struct Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics
	{
		struct MuJoCoSkeletalActor_eventSetSkinnedAsset_Parms
		{
			USkeletalMesh* Mesh;
		};
		static const UECodeGen_Private::FObjectPropertyParams NewProp_Mesh;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
	const UECodeGen_Private::FObjectPropertyParams Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::NewProp_Mesh = { "Mesh", nullptr, (EPropertyFlags)0x0010000000000080, UECodeGen_Private::EPropertyGenFlags::Object, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoSkeletalActor_eventSetSkinnedAsset_Parms, Mesh), Z_Construct_UClass_USkeletalMesh_NoRegister, METADATA_PARAMS(nullptr, 0) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::NewProp_Mesh,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/** Assign the SkeletalMesh that the PoseableMesh will pose. */" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
		{ "ToolTip", "Assign the SkeletalMesh that the PoseableMesh will pose." },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_AMuJoCoSkeletalActor, nullptr, "SetSkinnedAsset", nullptr, nullptr, sizeof(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::MuJoCoSkeletalActor_eventSetSkinnedAsset_Parms), Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x04020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	IMPLEMENT_CLASS_NO_AUTO_REGISTRATION(AMuJoCoSkeletalActor);
	UClass* Z_Construct_UClass_AMuJoCoSkeletalActor_NoRegister()
	{
		return AMuJoCoSkeletalActor::StaticClass();
	}
	struct Z_Construct_UClass_AMuJoCoSkeletalActor_Statics
	{
		static UObject* (*const DependentSingletons[])();
		static const FClassFunctionLinkInfo FuncInfo[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Class_MetaDataParams[];
#endif
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_AssetName_MetaData[];
#endif
		static const UECodeGen_Private::FStrPropertyParams NewProp_AssetName;
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_SceneRoot_MetaData[];
#endif
		static const UECodeGen_Private::FObjectPtrPropertyParams NewProp_SceneRoot;
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_PoseableMesh_MetaData[];
#endif
		static const UECodeGen_Private::FObjectPtrPropertyParams NewProp_PoseableMesh;
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_Driver_MetaData[];
#endif
		static const UECodeGen_Private::FObjectPtrPropertyParams NewProp_Driver;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
		static const FCppClassTypeInfoStatic StaticCppClassTypeInfo;
		static const UECodeGen_Private::FClassParams ClassParams;
	};
	UObject* (*const Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::DependentSingletons[])() = {
		(UObject* (*)())Z_Construct_UClass_AActor,
		(UObject* (*)())Z_Construct_UPackage__Script_SeniorCareBridge,
	};
	const FClassFunctionLinkInfo Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::FuncInfo[] = {
		{ &Z_Construct_UFunction_AMuJoCoSkeletalActor_GetAssetName, "GetAssetName" }, // 4180073028
		{ &Z_Construct_UFunction_AMuJoCoSkeletalActor_GetDriver, "GetDriver" }, // 1069592501
		{ &Z_Construct_UFunction_AMuJoCoSkeletalActor_GetPoseableMesh, "GetPoseableMesh" }, // 4013194712
		{ &Z_Construct_UFunction_AMuJoCoSkeletalActor_SetAssetName, "SetAssetName" }, // 1297830406
		{ &Z_Construct_UFunction_AMuJoCoSkeletalActor_SetBoneNameMappingJson, "SetBoneNameMappingJson" }, // 598863152
		{ &Z_Construct_UFunction_AMuJoCoSkeletalActor_SetSkinnedAsset, "SetSkinnedAsset" }, // 3153940937
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::Class_MetaDataParams[] = {
		{ "BlueprintType", "true" },
		{ "Comment", "/**\n * Actor that hosts a UPoseableMeshComponent driven by MuJoCo state.\n *\n * Designed to be spawned from Python (replaces ASkeletalMeshActor +\n * manual UPoseableMeshComponent attach path that was unreliable on\n * UE 5.1's Python bindings). The PoseableMesh is created via\n * CreateDefaultSubobject so it auto-registers with the scene.\n *\n * Python is expected to:\n *   1. Spawn this actor at the desired location.\n *   2. Call SetSkinnedAsset(mesh) to assign the skeletal mesh.\n *   3. Call SetAssetName(\"franka_emika_panda\") so the bridge subsystem\n *      can route incoming MuJoCo frames to this actor.\n *   4. (Optional) Call SetBoneNameMappingJson(...) with a JSON object\n *      mapping MuJoCo body name -> UE bone name.\n */" },
		{ "IncludePath", "MuJoCoSkeletalActor.h" },
		{ "IsBlueprintBase", "true" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
		{ "ToolTip", "Actor that hosts a UPoseableMeshComponent driven by MuJoCo state.\n\nDesigned to be spawned from Python (replaces ASkeletalMeshActor +\nmanual UPoseableMeshComponent attach path that was unreliable on\nUE 5.1's Python bindings). The PoseableMesh is created via\nCreateDefaultSubobject so it auto-registers with the scene.\n\nPython is expected to:\n  1. Spawn this actor at the desired location.\n  2. Call SetSkinnedAsset(mesh) to assign the skeletal mesh.\n  3. Call SetAssetName(\"franka_emika_panda\") so the bridge subsystem\n     can route incoming MuJoCo frames to this actor.\n  4. (Optional) Call SetBoneNameMappingJson(...) with a JSON object\n     mapping MuJoCo body name -> UE bone name." },
	};
#endif
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_AssetName_MetaData[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/** Asset routing key (e.g. \"franka_emika_panda\"). */" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
		{ "ToolTip", "Asset routing key (e.g. \"franka_emika_panda\")." },
	};
#endif
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_AssetName = { "AssetName", nullptr, (EPropertyFlags)0x0020080000000005, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(AMuJoCoSkeletalActor, AssetName), METADATA_PARAMS(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_AssetName_MetaData, UE_ARRAY_COUNT(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_AssetName_MetaData)) };
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_SceneRoot_MetaData[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "EditInline", "true" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
	};
#endif
	const UECodeGen_Private::FObjectPtrPropertyParams Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_SceneRoot = { "SceneRoot", nullptr, (EPropertyFlags)0x00240800000a001d, UECodeGen_Private::EPropertyGenFlags::Object | UECodeGen_Private::EPropertyGenFlags::ObjectPtr, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(AMuJoCoSkeletalActor, SceneRoot), Z_Construct_UClass_USceneComponent_NoRegister, METADATA_PARAMS(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_SceneRoot_MetaData, UE_ARRAY_COUNT(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_SceneRoot_MetaData)) };
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_PoseableMesh_MetaData[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "EditInline", "true" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
	};
#endif
	const UECodeGen_Private::FObjectPtrPropertyParams Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_PoseableMesh = { "PoseableMesh", nullptr, (EPropertyFlags)0x00240800000a001d, UECodeGen_Private::EPropertyGenFlags::Object | UECodeGen_Private::EPropertyGenFlags::ObjectPtr, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(AMuJoCoSkeletalActor, PoseableMesh), Z_Construct_UClass_UPoseableMeshComponent_NoRegister, METADATA_PARAMS(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_PoseableMesh_MetaData, UE_ARRAY_COUNT(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_PoseableMesh_MetaData)) };
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_Driver_MetaData[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "EditInline", "true" },
		{ "ModuleRelativePath", "Public/MuJoCoSkeletalActor.h" },
	};
#endif
	const UECodeGen_Private::FObjectPtrPropertyParams Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_Driver = { "Driver", nullptr, (EPropertyFlags)0x00240800000a001d, UECodeGen_Private::EPropertyGenFlags::Object | UECodeGen_Private::EPropertyGenFlags::ObjectPtr, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(AMuJoCoSkeletalActor, Driver), Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_NoRegister, METADATA_PARAMS(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_Driver_MetaData, UE_ARRAY_COUNT(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_Driver_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_AssetName,
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_SceneRoot,
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_PoseableMesh,
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::NewProp_Driver,
	};
	const FCppClassTypeInfoStatic Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::StaticCppClassTypeInfo = {
		TCppClassTypeTraits<AMuJoCoSkeletalActor>::IsAbstract,
	};
	const UECodeGen_Private::FClassParams Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::ClassParams = {
		&AMuJoCoSkeletalActor::StaticClass,
		"Engine",
		&StaticCppClassTypeInfo,
		DependentSingletons,
		FuncInfo,
		Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::PropPointers,
		nullptr,
		UE_ARRAY_COUNT(DependentSingletons),
		UE_ARRAY_COUNT(FuncInfo),
		UE_ARRAY_COUNT(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::PropPointers),
		0,
		0x009000A4u,
		METADATA_PARAMS(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::Class_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::Class_MetaDataParams))
	};
	UClass* Z_Construct_UClass_AMuJoCoSkeletalActor()
	{
		if (!Z_Registration_Info_UClass_AMuJoCoSkeletalActor.OuterSingleton)
		{
			UECodeGen_Private::ConstructUClass(Z_Registration_Info_UClass_AMuJoCoSkeletalActor.OuterSingleton, Z_Construct_UClass_AMuJoCoSkeletalActor_Statics::ClassParams);
		}
		return Z_Registration_Info_UClass_AMuJoCoSkeletalActor.OuterSingleton;
	}
	template<> SENIORCAREBRIDGE_API UClass* StaticClass<AMuJoCoSkeletalActor>()
	{
		return AMuJoCoSkeletalActor::StaticClass();
	}
	DEFINE_VTABLE_PTR_HELPER_CTOR(AMuJoCoSkeletalActor);
	AMuJoCoSkeletalActor::~AMuJoCoSkeletalActor() {}
	struct Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoSkeletalActor_h_Statics
	{
		static const FClassRegisterCompiledInInfo ClassInfo[];
	};
	const FClassRegisterCompiledInInfo Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoSkeletalActor_h_Statics::ClassInfo[] = {
		{ Z_Construct_UClass_AMuJoCoSkeletalActor, AMuJoCoSkeletalActor::StaticClass, TEXT("AMuJoCoSkeletalActor"), &Z_Registration_Info_UClass_AMuJoCoSkeletalActor, CONSTRUCT_RELOAD_VERSION_INFO(FClassReloadVersionInfo, sizeof(AMuJoCoSkeletalActor), 574014952U) },
	};
	static FRegisterCompiledInInfo Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoSkeletalActor_h_4078243630(TEXT("/Script/SeniorCareBridge"),
		Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoSkeletalActor_h_Statics::ClassInfo, UE_ARRAY_COUNT(Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoSkeletalActor_h_Statics::ClassInfo),
		nullptr, 0,
		nullptr, 0);
PRAGMA_ENABLE_DEPRECATION_WARNINGS
