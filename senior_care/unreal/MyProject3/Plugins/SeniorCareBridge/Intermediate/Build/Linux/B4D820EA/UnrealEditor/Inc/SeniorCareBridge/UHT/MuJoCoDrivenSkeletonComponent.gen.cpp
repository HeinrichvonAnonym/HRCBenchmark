// Copyright Epic Games, Inc. All Rights Reserved.
/*===========================================================================
	Generated code exported from UnrealHeaderTool.
	DO NOT modify this manually! Edit the corresponding .h files instead!
===========================================================================*/

#include "UObject/GeneratedCppIncludes.h"
#include "SeniorCareBridge/Public/MuJoCoDrivenSkeletonComponent.h"
PRAGMA_DISABLE_DEPRECATION_WARNINGS
void EmptyLinkFunctionForGeneratedCodeMuJoCoDrivenSkeletonComponent() {}
// Cross Module References
	ENGINE_API UClass* Z_Construct_UClass_UActorComponent();
	SENIORCAREBRIDGE_API UClass* Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent();
	SENIORCAREBRIDGE_API UClass* Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_NoRegister();
	UPackage* Z_Construct_UPackage__Script_SeniorCareBridge();
// End Cross Module References
	DEFINE_FUNCTION(UMuJoCoDrivenSkeletonComponent::execSetBoneNameMappingJson)
	{
		P_GET_PROPERTY(FStrProperty,Z_Param_Json);
		P_FINISH;
		P_NATIVE_BEGIN;
		P_THIS->SetBoneNameMappingJson(Z_Param_Json);
		P_NATIVE_END;
	}
	void UMuJoCoDrivenSkeletonComponent::StaticRegisterNativesUMuJoCoDrivenSkeletonComponent()
	{
		UClass* Class = UMuJoCoDrivenSkeletonComponent::StaticClass();
		static const FNameNativePtrPair Funcs[] = {
			{ "SetBoneNameMappingJson", &UMuJoCoDrivenSkeletonComponent::execSetBoneNameMappingJson },
		};
		FNativeFunctionRegistrar::RegisterFunctions(Class, Funcs, UE_ARRAY_COUNT(Funcs));
	}
	struct Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics
	{
		struct MuJoCoDrivenSkeletonComponent_eventSetBoneNameMappingJson_Parms
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
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::NewProp_Json_MetaData[] = {
		{ "NativeConst", "" },
	};
#endif
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::NewProp_Json = { "Json", nullptr, (EPropertyFlags)0x0010000000000080, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoDrivenSkeletonComponent_eventSetBoneNameMappingJson_Parms, Json), METADATA_PARAMS(Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::NewProp_Json_MetaData, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::NewProp_Json_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::NewProp_Json,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/**\n\x09 * JSON describing how to drive each MuJoCo joint:\n\x09 *\n\x09 *   {\n\x09 *     \"joint_to_bone\": {\n\x09 *       \"panda_joint1\": {\"bone\": \"panda_joint1_revolute_bone\", \"axis\": \"z\"},\n\x09 *       \"panda_joint2\": {\"bone\": \"panda_joint2_revolute_bone\", \"axis\": \"z\"}\n\x09 *     }\n\x09 *   }\n\x09 *\n\x09 * Set once by Python after spawn (before any frames arrive).\n\x09 */" },
		{ "ModuleRelativePath", "Public/MuJoCoDrivenSkeletonComponent.h" },
		{ "ToolTip", "JSON describing how to drive each MuJoCo joint:\n\n  {\n    \"joint_to_bone\": {\n      \"panda_joint1\": {\"bone\": \"panda_joint1_revolute_bone\", \"axis\": \"z\"},\n      \"panda_joint2\": {\"bone\": \"panda_joint2_revolute_bone\", \"axis\": \"z\"}\n    }\n  }\n\nSet once by Python after spawn (before any frames arrive)." },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent, nullptr, "SetBoneNameMappingJson", nullptr, nullptr, sizeof(Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::MuJoCoDrivenSkeletonComponent_eventSetBoneNameMappingJson_Parms), Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x04020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	IMPLEMENT_CLASS_NO_AUTO_REGISTRATION(UMuJoCoDrivenSkeletonComponent);
	UClass* Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_NoRegister()
	{
		return UMuJoCoDrivenSkeletonComponent::StaticClass();
	}
	struct Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics
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
		static const UECodeGen_Private::FMetaDataPairParam NewProp_bVerboseLogging_MetaData[];
#endif
		static void NewProp_bVerboseLogging_SetBit(void* Obj);
		static const UECodeGen_Private::FBoolPropertyParams NewProp_bVerboseLogging;
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_DefaultAxis_MetaData[];
#endif
		static const UECodeGen_Private::FStrPropertyParams NewProp_DefaultAxis;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
		static const FCppClassTypeInfoStatic StaticCppClassTypeInfo;
		static const UECodeGen_Private::FClassParams ClassParams;
	};
	UObject* (*const Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::DependentSingletons[])() = {
		(UObject* (*)())Z_Construct_UClass_UActorComponent,
		(UObject* (*)())Z_Construct_UPackage__Script_SeniorCareBridge,
	};
	const FClassFunctionLinkInfo Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::FuncInfo[] = {
		{ &Z_Construct_UFunction_UMuJoCoDrivenSkeletonComponent_SetBoneNameMappingJson, "SetBoneNameMappingJson" }, // 2419068994
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::Class_MetaDataParams[] = {
		{ "BlueprintSpawnableComponent", "" },
		{ "ClassGroupNames", "SeniorCare" },
		{ "Comment", "/**\n * Pulls the latest MuJoCo frame for a named asset from\n * UMuJoCoBridgeSubsystem each tick, and applies it to a sibling\n * UPoseableMeshComponent on the same actor. Ticks in editor so it\n * works under `test_ue.py` without having to enter PIE.\n */" },
		{ "IncludePath", "MuJoCoDrivenSkeletonComponent.h" },
		{ "ModuleRelativePath", "Public/MuJoCoDrivenSkeletonComponent.h" },
		{ "ToolTip", "Pulls the latest MuJoCo frame for a named asset from\nUMuJoCoBridgeSubsystem each tick, and applies it to a sibling\nUPoseableMeshComponent on the same actor. Ticks in editor so it\nworks under `test_ue.py` without having to enter PIE." },
	};
#endif
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_AssetName_MetaData[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/** Owner actor's logical asset name; used as the routing key. */" },
		{ "ModuleRelativePath", "Public/MuJoCoDrivenSkeletonComponent.h" },
		{ "ToolTip", "Owner actor's logical asset name; used as the routing key." },
	};
#endif
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_AssetName = { "AssetName", nullptr, (EPropertyFlags)0x0010000000000005, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(UMuJoCoDrivenSkeletonComponent, AssetName), METADATA_PARAMS(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_AssetName_MetaData, UE_ARRAY_COUNT(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_AssetName_MetaData)) };
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_bVerboseLogging_MetaData[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/** If true, log per-frame diagnostics (very verbose). */" },
		{ "ModuleRelativePath", "Public/MuJoCoDrivenSkeletonComponent.h" },
		{ "ToolTip", "If true, log per-frame diagnostics (very verbose)." },
	};
#endif
	void Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_bVerboseLogging_SetBit(void* Obj)
	{
		((UMuJoCoDrivenSkeletonComponent*)Obj)->bVerboseLogging = 1;
	}
	const UECodeGen_Private::FBoolPropertyParams Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_bVerboseLogging = { "bVerboseLogging", nullptr, (EPropertyFlags)0x0010000000000005, UECodeGen_Private::EPropertyGenFlags::Bool | UECodeGen_Private::EPropertyGenFlags::NativeBool, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, sizeof(bool), sizeof(UMuJoCoDrivenSkeletonComponent), &Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_bVerboseLogging_SetBit, METADATA_PARAMS(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_bVerboseLogging_MetaData, UE_ARRAY_COUNT(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_bVerboseLogging_MetaData)) };
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_DefaultAxis_MetaData[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/** Default rotation axis for joints whose entry doesn't specify one. */" },
		{ "ModuleRelativePath", "Public/MuJoCoDrivenSkeletonComponent.h" },
		{ "ToolTip", "Default rotation axis for joints whose entry doesn't specify one." },
	};
#endif
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_DefaultAxis = { "DefaultAxis", nullptr, (EPropertyFlags)0x0010000000000005, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(UMuJoCoDrivenSkeletonComponent, DefaultAxis), METADATA_PARAMS(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_DefaultAxis_MetaData, UE_ARRAY_COUNT(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_DefaultAxis_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_AssetName,
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_bVerboseLogging,
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::NewProp_DefaultAxis,
	};
	const FCppClassTypeInfoStatic Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::StaticCppClassTypeInfo = {
		TCppClassTypeTraits<UMuJoCoDrivenSkeletonComponent>::IsAbstract,
	};
	const UECodeGen_Private::FClassParams Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::ClassParams = {
		&UMuJoCoDrivenSkeletonComponent::StaticClass,
		"Engine",
		&StaticCppClassTypeInfo,
		DependentSingletons,
		FuncInfo,
		Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::PropPointers,
		nullptr,
		UE_ARRAY_COUNT(DependentSingletons),
		UE_ARRAY_COUNT(FuncInfo),
		UE_ARRAY_COUNT(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::PropPointers),
		0,
		0x00B000A4u,
		METADATA_PARAMS(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::Class_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::Class_MetaDataParams))
	};
	UClass* Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent()
	{
		if (!Z_Registration_Info_UClass_UMuJoCoDrivenSkeletonComponent.OuterSingleton)
		{
			UECodeGen_Private::ConstructUClass(Z_Registration_Info_UClass_UMuJoCoDrivenSkeletonComponent.OuterSingleton, Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent_Statics::ClassParams);
		}
		return Z_Registration_Info_UClass_UMuJoCoDrivenSkeletonComponent.OuterSingleton;
	}
	template<> SENIORCAREBRIDGE_API UClass* StaticClass<UMuJoCoDrivenSkeletonComponent>()
	{
		return UMuJoCoDrivenSkeletonComponent::StaticClass();
	}
	DEFINE_VTABLE_PTR_HELPER_CTOR(UMuJoCoDrivenSkeletonComponent);
	UMuJoCoDrivenSkeletonComponent::~UMuJoCoDrivenSkeletonComponent() {}
	struct Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoDrivenSkeletonComponent_h_Statics
	{
		static const FClassRegisterCompiledInInfo ClassInfo[];
	};
	const FClassRegisterCompiledInInfo Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoDrivenSkeletonComponent_h_Statics::ClassInfo[] = {
		{ Z_Construct_UClass_UMuJoCoDrivenSkeletonComponent, UMuJoCoDrivenSkeletonComponent::StaticClass, TEXT("UMuJoCoDrivenSkeletonComponent"), &Z_Registration_Info_UClass_UMuJoCoDrivenSkeletonComponent, CONSTRUCT_RELOAD_VERSION_INFO(FClassReloadVersionInfo, sizeof(UMuJoCoDrivenSkeletonComponent), 950683716U) },
	};
	static FRegisterCompiledInInfo Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoDrivenSkeletonComponent_h_668310027(TEXT("/Script/SeniorCareBridge"),
		Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoDrivenSkeletonComponent_h_Statics::ClassInfo, UE_ARRAY_COUNT(Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoDrivenSkeletonComponent_h_Statics::ClassInfo),
		nullptr, 0,
		nullptr, 0);
PRAGMA_ENABLE_DEPRECATION_WARNINGS
