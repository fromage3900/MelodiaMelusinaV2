// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AscentSaveSystemEditor.h"
#include "SALSSaveSlotPicker.h"

#include "ALSLoadAndSaveSubsystem.h"
#include "ALSLoadTask.h"
#include "Editor.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Misc/ConfigCacheIni.h"
#include "ToolMenu.h"
#include "ToolMenuEntry.h"
#include "ToolMenus.h"
#include "UnrealEdGlobals.h"

#define LOCTEXT_NAMESPACE "FAscentSaveSystemEditorModule"

/** GEditorPerProjectIni config section shared with SALSSaveSlotPicker. */
static const TCHAR* GAlsPIEConfigSection = TEXT("AscentSaveSystem.PIEOverride");

void FAscentSaveSystemEditorModule::StartupModule()
{
	// Register the Play toolbar widget after the editor menus are fully built.
	UToolMenus::RegisterStartupCallback(
		FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FAscentSaveSystemEditorModule::RegisterMenus));

	// After PIE starts, load current-level data. Components receive the load
	// completion event and restore themselves when the save is ready.
	PostPIEStartedHandle = FEditorDelegates::PostPIEStarted.AddRaw(
		this, &FAscentSaveSystemEditorModule::OnPostPIEStarted);
}

void FAscentSaveSystemEditorModule::ShutdownModule()
{
	UToolMenus::UnRegisterStartupCallback(this);
	UToolMenus::UnregisterOwner(this);

	FEditorDelegates::PostPIEStarted.Remove(PostPIEStartedHandle);
}

void FAscentSaveSystemEditorModule::RegisterMenus()
{
	FToolMenuOwnerScoped OwnerScoped(this);

	UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu(
		"LevelEditor.LevelEditorToolBar.PlayToolBar");

	FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("ALSSavePIETools");
	Section.Label = LOCTEXT("SectionLabel", "Save System");

	FToolMenuEntry WidgetEntry = FToolMenuEntry::InitWidget(
		"ALSSaveSlotPicker",
		SNew(SALSSaveSlotPicker),
		LOCTEXT("PickerLabel", "PIE Save Slot"),
		/*bNoIndent=*/true,
		/*bSearchable=*/false);

	Section.AddEntry(WidgetEntry);
}

void FAscentSaveSystemEditorModule::OnPostPIEStarted(bool bIsSimulating)
{
	if (bIsSimulating)
	{
		return;
	}

	bool bNewGame = true;
	FString SlotName;
	GConfig->GetBool(GAlsPIEConfigSection, TEXT("PIENewGame"), bNewGame, GEditorPerProjectIni);
	GConfig->GetString(GAlsPIEConfigSection, TEXT("PIESlotName"), SlotName, GEditorPerProjectIni);

	if (bNewGame || SlotName.IsEmpty())
	{
		return;
	}

	// Find the active PIE world context.
	UWorld* PIEWorld = nullptr;
	if (GEngine)
	{
		for (const FWorldContext& Ctx : GEngine->GetWorldContexts())
		{
			if (Ctx.WorldType == EWorldType::PIE && Ctx.World())
			{
				PIEWorld = Ctx.World();
				break;
			}
		}
	}

	if (!PIEWorld)
	{
		return;
	}

	UGameInstance* GI = PIEWorld->GetGameInstance();
	if (!GI)
	{
		return;
	}

	UALSLoadAndSaveSubsystem* SaveSys = GI->GetSubsystem<UALSLoadAndSaveSubsystem>();
	if (!SaveSys)
	{
		return;
	}

	UE_LOG(LogTemp, Log,
		TEXT("[AscentSaveSystemEditor] PIE started - loading full game world from save slot \"%s\""), *SlotName);

	SaveSys->LoadGameWorld(SlotName, FOnLoadFinished(), /*reloadPlayer=*/true);
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAscentSaveSystemEditorModule, AscentSaveSystemEditor)
