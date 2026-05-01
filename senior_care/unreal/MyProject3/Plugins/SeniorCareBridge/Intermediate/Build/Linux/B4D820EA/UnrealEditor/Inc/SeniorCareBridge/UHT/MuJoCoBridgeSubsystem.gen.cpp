// Copyright Epic Games, Inc. All Rights Reserved.
/*===========================================================================
	Generated code exported from UnrealHeaderTool.
	DO NOT modify this manually! Edit the corresponding .h files instead!
===========================================================================*/

#include "UObject/GeneratedCppIncludes.h"
#include "SeniorCareBridge/Public/MuJoCoBridgeSubsystem.h"
PRAGMA_DISABLE_DEPRECATION_WARNINGS
void EmptyLinkFunctionForGeneratedCodeMuJoCoBridgeSubsystem() {}
// Cross Module References
	EDITORSUBSYSTEM_API UClass* Z_Construct_UClass_UEditorSubsystem();
	SENIORCAREBRIDGE_API UClass* Z_Construct_UClass_UMuJoCoBridgeSubsystem();
	SENIORCAREBRIDGE_API UClass* Z_Construct_UClass_UMuJoCoBridgeSubsystem_NoRegister();
	UPackage* Z_Construct_UPackage__Script_SeniorCareBridge();
// End Cross Module References
	DEFINE_FUNCTION(UMuJoCoBridgeSubsystem::execGetLastFrameSeq)
	{
		P_FINISH;
		P_NATIVE_BEGIN;
		*(int64*)Z_Param__Result=P_THIS->GetLastFrameSeq();
		P_NATIVE_END;
	}
	DEFINE_FUNCTION(UMuJoCoBridgeSubsystem::execGetFramesReceived)
	{
		P_FINISH;
		P_NATIVE_BEGIN;
		*(int64*)Z_Param__Result=P_THIS->GetFramesReceived();
		P_NATIVE_END;
	}
	DEFINE_FUNCTION(UMuJoCoBridgeSubsystem::execGetEndpoint)
	{
		P_FINISH;
		P_NATIVE_BEGIN;
		*(FString*)Z_Param__Result=P_THIS->GetEndpoint();
		P_NATIVE_END;
	}
	DEFINE_FUNCTION(UMuJoCoBridgeSubsystem::execReconnect)
	{
		P_GET_PROPERTY(FStrProperty,Z_Param_Endpoint);
		P_FINISH;
		P_NATIVE_BEGIN;
		P_THIS->Reconnect(Z_Param_Endpoint);
		P_NATIVE_END;
	}
	void UMuJoCoBridgeSubsystem::StaticRegisterNativesUMuJoCoBridgeSubsystem()
	{
		UClass* Class = UMuJoCoBridgeSubsystem::StaticClass();
		static const FNameNativePtrPair Funcs[] = {
			{ "GetEndpoint", &UMuJoCoBridgeSubsystem::execGetEndpoint },
			{ "GetFramesReceived", &UMuJoCoBridgeSubsystem::execGetFramesReceived },
			{ "GetLastFrameSeq", &UMuJoCoBridgeSubsystem::execGetLastFrameSeq },
			{ "Reconnect", &UMuJoCoBridgeSubsystem::execReconnect },
		};
		FNativeFunctionRegistrar::RegisterFunctions(Class, Funcs, UE_ARRAY_COUNT(Funcs));
	}
	struct Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics
	{
		struct MuJoCoBridgeSubsystem_eventGetEndpoint_Parms
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
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::NewProp_ReturnValue = { "ReturnValue", nullptr, (EPropertyFlags)0x0010000000000580, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoBridgeSubsystem_eventGetEndpoint_Parms, ReturnValue), METADATA_PARAMS(nullptr, 0) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::NewProp_ReturnValue,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "ModuleRelativePath", "Public/MuJoCoBridgeSubsystem.h" },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_UMuJoCoBridgeSubsystem, nullptr, "GetEndpoint", nullptr, nullptr, sizeof(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::MuJoCoBridgeSubsystem_eventGetEndpoint_Parms), Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x54020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	struct Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics
	{
		struct MuJoCoBridgeSubsystem_eventGetFramesReceived_Parms
		{
			int64 ReturnValue;
		};
		static const UECodeGen_Private::FInt64PropertyParams NewProp_ReturnValue;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
	const UECodeGen_Private::FInt64PropertyParams Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::NewProp_ReturnValue = { "ReturnValue", nullptr, (EPropertyFlags)0x0010000000000580, UECodeGen_Private::EPropertyGenFlags::Int64, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoBridgeSubsystem_eventGetFramesReceived_Parms, ReturnValue), METADATA_PARAMS(nullptr, 0) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::NewProp_ReturnValue,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "ModuleRelativePath", "Public/MuJoCoBridgeSubsystem.h" },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_UMuJoCoBridgeSubsystem, nullptr, "GetFramesReceived", nullptr, nullptr, sizeof(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::MuJoCoBridgeSubsystem_eventGetFramesReceived_Parms), Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x54020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	struct Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics
	{
		struct MuJoCoBridgeSubsystem_eventGetLastFrameSeq_Parms
		{
			int64 ReturnValue;
		};
		static const UECodeGen_Private::FInt64PropertyParams NewProp_ReturnValue;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
	const UECodeGen_Private::FInt64PropertyParams Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::NewProp_ReturnValue = { "ReturnValue", nullptr, (EPropertyFlags)0x0010000000000580, UECodeGen_Private::EPropertyGenFlags::Int64, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoBridgeSubsystem_eventGetLastFrameSeq_Parms, ReturnValue), METADATA_PARAMS(nullptr, 0) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::NewProp_ReturnValue,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "ModuleRelativePath", "Public/MuJoCoBridgeSubsystem.h" },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_UMuJoCoBridgeSubsystem, nullptr, "GetLastFrameSeq", nullptr, nullptr, sizeof(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::MuJoCoBridgeSubsystem_eventGetLastFrameSeq_Parms), Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x54020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	struct Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics
	{
		struct MuJoCoBridgeSubsystem_eventReconnect_Parms
		{
			FString Endpoint;
		};
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_Endpoint_MetaData[];
#endif
		static const UECodeGen_Private::FStrPropertyParams NewProp_Endpoint;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Function_MetaDataParams[];
#endif
		static const UECodeGen_Private::FFunctionParams FuncParams;
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::NewProp_Endpoint_MetaData[] = {
		{ "NativeConst", "" },
	};
#endif
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::NewProp_Endpoint = { "Endpoint", nullptr, (EPropertyFlags)0x0010000000000080, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(MuJoCoBridgeSubsystem_eventReconnect_Parms, Endpoint), METADATA_PARAMS(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::NewProp_Endpoint_MetaData, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::NewProp_Endpoint_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::NewProp_Endpoint,
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::Function_MetaDataParams[] = {
		{ "Category", "SeniorCare|Bridge" },
		{ "Comment", "/** Restart the SUB thread on a new endpoint. Call from python/editor. */" },
		{ "ModuleRelativePath", "Public/MuJoCoBridgeSubsystem.h" },
		{ "ToolTip", "Restart the SUB thread on a new endpoint. Call from python/editor." },
	};
#endif
	const UECodeGen_Private::FFunctionParams Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::FuncParams = { (UObject*(*)())Z_Construct_UClass_UMuJoCoBridgeSubsystem, nullptr, "Reconnect", nullptr, nullptr, sizeof(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::MuJoCoBridgeSubsystem_eventReconnect_Parms), Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::PropPointers, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::PropPointers), RF_Public|RF_Transient|RF_MarkAsNative, (EFunctionFlags)0x04020401, 0, 0, METADATA_PARAMS(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::Function_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::Function_MetaDataParams)) };
	UFunction* Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect()
	{
		static UFunction* ReturnFunction = nullptr;
		if (!ReturnFunction)
		{
			UECodeGen_Private::ConstructUFunction(&ReturnFunction, Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect_Statics::FuncParams);
		}
		return ReturnFunction;
	}
	IMPLEMENT_CLASS_NO_AUTO_REGISTRATION(UMuJoCoBridgeSubsystem);
	UClass* Z_Construct_UClass_UMuJoCoBridgeSubsystem_NoRegister()
	{
		return UMuJoCoBridgeSubsystem::StaticClass();
	}
	struct Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics
	{
		static UObject* (*const DependentSingletons[])();
		static const FClassFunctionLinkInfo FuncInfo[];
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam Class_MetaDataParams[];
#endif
#if WITH_METADATA
		static const UECodeGen_Private::FMetaDataPairParam NewProp_Endpoint_MetaData[];
#endif
		static const UECodeGen_Private::FStrPropertyParams NewProp_Endpoint;
		static const UECodeGen_Private::FPropertyParamsBase* const PropPointers[];
		static const FCppClassTypeInfoStatic StaticCppClassTypeInfo;
		static const UECodeGen_Private::FClassParams ClassParams;
	};
	UObject* (*const Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::DependentSingletons[])() = {
		(UObject* (*)())Z_Construct_UClass_UEditorSubsystem,
		(UObject* (*)())Z_Construct_UPackage__Script_SeniorCareBridge,
	};
	const FClassFunctionLinkInfo Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::FuncInfo[] = {
		{ &Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetEndpoint, "GetEndpoint" }, // 1397269612
		{ &Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetFramesReceived, "GetFramesReceived" }, // 2575169665
		{ &Z_Construct_UFunction_UMuJoCoBridgeSubsystem_GetLastFrameSeq, "GetLastFrameSeq" }, // 2869993192
		{ &Z_Construct_UFunction_UMuJoCoBridgeSubsystem_Reconnect, "Reconnect" }, // 2595609022
	};
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::Class_MetaDataParams[] = {
		{ "Comment", "/**\n * Editor subsystem that runs a background thread subscribing to\n * MuJoCo state frames over ZMQ (tcp://localhost:5556 by default)\n * and exposes the latest frame per asset for drivers to read.\n */" },
		{ "IncludePath", "MuJoCoBridgeSubsystem.h" },
		{ "ModuleRelativePath", "Public/MuJoCoBridgeSubsystem.h" },
		{ "ToolTip", "Editor subsystem that runs a background thread subscribing to\nMuJoCo state frames over ZMQ (tcp://localhost:5556 by default)\nand exposes the latest frame per asset for drivers to read." },
	};
#endif
#if WITH_METADATA
	const UECodeGen_Private::FMetaDataPairParam Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::NewProp_Endpoint_MetaData[] = {
		{ "ModuleRelativePath", "Public/MuJoCoBridgeSubsystem.h" },
	};
#endif
	const UECodeGen_Private::FStrPropertyParams Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::NewProp_Endpoint = { "Endpoint", nullptr, (EPropertyFlags)0x0040000000000000, UECodeGen_Private::EPropertyGenFlags::Str, RF_Public|RF_Transient|RF_MarkAsNative, 1, nullptr, nullptr, STRUCT_OFFSET(UMuJoCoBridgeSubsystem, Endpoint), METADATA_PARAMS(Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::NewProp_Endpoint_MetaData, UE_ARRAY_COUNT(Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::NewProp_Endpoint_MetaData)) };
	const UECodeGen_Private::FPropertyParamsBase* const Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::PropPointers[] = {
		(const UECodeGen_Private::FPropertyParamsBase*)&Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::NewProp_Endpoint,
	};
	const FCppClassTypeInfoStatic Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::StaticCppClassTypeInfo = {
		TCppClassTypeTraits<UMuJoCoBridgeSubsystem>::IsAbstract,
	};
	const UECodeGen_Private::FClassParams Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::ClassParams = {
		&UMuJoCoBridgeSubsystem::StaticClass,
		nullptr,
		&StaticCppClassTypeInfo,
		DependentSingletons,
		FuncInfo,
		Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::PropPointers,
		nullptr,
		UE_ARRAY_COUNT(DependentSingletons),
		UE_ARRAY_COUNT(FuncInfo),
		UE_ARRAY_COUNT(Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::PropPointers),
		0,
		0x001000A0u,
		METADATA_PARAMS(Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::Class_MetaDataParams, UE_ARRAY_COUNT(Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::Class_MetaDataParams))
	};
	UClass* Z_Construct_UClass_UMuJoCoBridgeSubsystem()
	{
		if (!Z_Registration_Info_UClass_UMuJoCoBridgeSubsystem.OuterSingleton)
		{
			UECodeGen_Private::ConstructUClass(Z_Registration_Info_UClass_UMuJoCoBridgeSubsystem.OuterSingleton, Z_Construct_UClass_UMuJoCoBridgeSubsystem_Statics::ClassParams);
		}
		return Z_Registration_Info_UClass_UMuJoCoBridgeSubsystem.OuterSingleton;
	}
	template<> SENIORCAREBRIDGE_API UClass* StaticClass<UMuJoCoBridgeSubsystem>()
	{
		return UMuJoCoBridgeSubsystem::StaticClass();
	}
	DEFINE_VTABLE_PTR_HELPER_CTOR(UMuJoCoBridgeSubsystem);
	UMuJoCoBridgeSubsystem::~UMuJoCoBridgeSubsystem() {}
	struct Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoBridgeSubsystem_h_Statics
	{
		static const FClassRegisterCompiledInInfo ClassInfo[];
	};
	const FClassRegisterCompiledInInfo Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoBridgeSubsystem_h_Statics::ClassInfo[] = {
		{ Z_Construct_UClass_UMuJoCoBridgeSubsystem, UMuJoCoBridgeSubsystem::StaticClass, TEXT("UMuJoCoBridgeSubsystem"), &Z_Registration_Info_UClass_UMuJoCoBridgeSubsystem, CONSTRUCT_RELOAD_VERSION_INFO(FClassReloadVersionInfo, sizeof(UMuJoCoBridgeSubsystem), 675529129U) },
	};
	static FRegisterCompiledInInfo Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoBridgeSubsystem_h_314839981(TEXT("/Script/SeniorCareBridge"),
		Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoBridgeSubsystem_h_Statics::ClassInfo, UE_ARRAY_COUNT(Z_CompiledInDeferFile_FID_python_benchmark_senior_care_unreal_MyProject3_Plugins_SeniorCareBridge_Source_SeniorCareBridge_Public_MuJoCoBridgeSubsystem_h_Statics::ClassInfo),
		nullptr, 0,
		nullptr, 0);
PRAGMA_ENABLE_DEPRECATION_WARNINGS
