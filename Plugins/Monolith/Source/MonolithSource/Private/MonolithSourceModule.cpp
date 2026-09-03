#include "MonolithSourceModule.h"
#include "MonolithSourceActions.h"
#include "MonolithToolRegistry.h"
#include "MonolithSettings.h"
#include "MonolithJsonUtils.h"

#define LOCTEXT_NAMESPACE "FMonolithSourceModule"

void FMonolithSourceModule::StartupModule()
{
	if (!GetDefault<UMonolithSettings>()->bEnableSource) return;

	FMonolithSourceActions::RegisterAll();
	UE_LOG(LogMonolith, Log, TEXT("Monolith — Source module loaded (10 actions)"));
}

void FMonolithSourceModule::ShutdownModule()
{
	FMonolithToolRegistry::Get().UnregisterNamespace(TEXT("source"));
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMonolithSourceModule, MonolithSource)
