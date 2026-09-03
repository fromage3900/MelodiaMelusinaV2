#include "MonolithIndexModule.h"
#include "MonolithIndexDatabase.h"
#include "MonolithToolRegistry.h"
#include "Actions/ProjectSearchAction.h"
#include "Actions/ProjectFindReferencesAction.h"
#include "Actions/ProjectFindByTypeAction.h"
#include "Actions/ProjectGetStatsAction.h"
#include "Actions/ProjectGetAssetDetailsAction.h"
#include "Actions/ProjectListGameplayTagsAction.h"
#include "Actions/ProjectSearchGameplayTagsAction.h"
#include "Actions/ProjectRefreshAssetsAction.h"
#include "Actions/ProjectGetSavedAssetStateAction.h"
#include "Actions/ProjectCleanupGeneratedAssetsAction.h"
#include "Actions/ProjectExportAssetTextAction.h"

#define LOCTEXT_NAMESPACE "FMonolithIndexModule"

void FMonolithIndexModule::StartupModule()
{
	UE_LOG(LogMonolithIndex, Verbose, TEXT("Monolith -- Index module loaded (10 actions, SQLite+FTS5)"));

	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();

	Registry.RegisterAction(TEXT("project"), FProjectSearchAction::GetName(),
		FProjectSearchAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectSearchAction::Execute),
		FProjectSearchAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectFindReferencesAction::GetName(),
		FProjectFindReferencesAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectFindReferencesAction::Execute),
		FProjectFindReferencesAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectFindByTypeAction::GetName(),
		FProjectFindByTypeAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectFindByTypeAction::Execute),
		FProjectFindByTypeAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectGetStatsAction::GetName(),
		FProjectGetStatsAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectGetStatsAction::Execute),
		FProjectGetStatsAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectGetAssetDetailsAction::GetName(),
		FProjectGetAssetDetailsAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectGetAssetDetailsAction::Execute),
		FProjectGetAssetDetailsAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectListGameplayTagsAction::GetName(),
		FProjectListGameplayTagsAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectListGameplayTagsAction::Execute),
		FProjectListGameplayTagsAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectSearchGameplayTagsAction::GetName(),
		FProjectSearchGameplayTagsAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectSearchGameplayTagsAction::Execute),
		FProjectSearchGameplayTagsAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectRefreshAssetsAction::GetName(),
		FProjectRefreshAssetsAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectRefreshAssetsAction::Execute),
		FProjectRefreshAssetsAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectGetSavedAssetStateAction::GetName(),
		FProjectGetSavedAssetStateAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectGetSavedAssetStateAction::Execute),
		FProjectGetSavedAssetStateAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectCleanupGeneratedAssetsAction::GetName(),
		FProjectCleanupGeneratedAssetsAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectCleanupGeneratedAssetsAction::Execute),
		FProjectCleanupGeneratedAssetsAction::GetSchema());

	Registry.RegisterAction(TEXT("project"), FProjectExportAssetTextAction::GetName(),
		FProjectExportAssetTextAction::GetDescription(),
		FMonolithActionHandler::CreateStatic(&FProjectExportAssetTextAction::Execute),
		FProjectExportAssetTextAction::GetSchema());
}

void FMonolithIndexModule::ShutdownModule()
{
	FMonolithToolRegistry::Get().UnregisterNamespace(TEXT("project"));
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMonolithIndexModule, MonolithIndex)
