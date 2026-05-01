// Copyright SeniorCare.

#include "SeniorCareBridge.h"

DEFINE_LOG_CATEGORY(LogSeniorCareBridge);

#define LOCTEXT_NAMESPACE "FSeniorCareBridgeModule"

void FSeniorCareBridgeModule::StartupModule()
{
	UE_LOG(LogSeniorCareBridge, Log, TEXT("SeniorCareBridge module loaded"));
}

void FSeniorCareBridgeModule::ShutdownModule()
{
	UE_LOG(LogSeniorCareBridge, Log, TEXT("SeniorCareBridge module unloaded"));
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FSeniorCareBridgeModule, SeniorCareBridge)
