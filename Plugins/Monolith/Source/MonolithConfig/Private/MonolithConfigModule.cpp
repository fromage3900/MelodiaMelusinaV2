#include "MonolithConfigModule.h"
#include "MonolithConfigActions.h"
#include "MonolithToolRegistry.h"
#include "MonolithJsonUtils.h"
#include "MonolithSettings.h"

#define LOCTEXT_NAMESPACE "FMonolithConfigModule"

void FMonolithConfigModule::StartupModule()
{
	if (!GetDefault<UMonolithSettings>()->bEnableConfig) return;

	FMonolithConfigActions::RegisterActions(FMonolithToolRegistry::Get());
	UE_LOG(LogMonolith, Log, TEXT("Monolith — Config module loaded (6 actions)"));
}

void FMonolithConfigModule::ShutdownModule()
{
	FMonolithToolRegistry::Get().UnregisterNamespace(TEXT("config"));
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMonolithConfigModule, MonolithConfig)
