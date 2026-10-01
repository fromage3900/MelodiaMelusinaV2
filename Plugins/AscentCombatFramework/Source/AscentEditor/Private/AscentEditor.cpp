// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AscentEditor.h"
#include "ACFActionsBlueprint.h"
#include "ACFActionsSetBlueprint.h"
#include "Actions/ACFActionsSet.h"
#include "Actions/ACFActionAbility.h"
#include "AscentEditorCommands.h"
#include "AscentEditorStyle.h"
#include "AssetToolsModule.h"
#include "AssetTypeActions/AssetTypeActions_Blueprint.h"
#include "AssetTypeActions_Base.h"
#include "AssetTypeCategories.h"
#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"
#include "Misc/MessageDialog.h"
#include "ToolMenus.h"
#include <AssetRegistry/AssetRegistryModule.h>
#include <Interfaces/IPluginManager.h>

static const FName AscentEditorTabName("AscentEditor");

#define LOCTEXT_NAMESPACE "FAscentEditorModule"

void FAscentEditorModule::StartupModule()
{
    // This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module

    FAscentEditorStyle::Initialize();
    FAscentEditorStyle::ReloadTextures();

    FAscentEditorCommands::Register();

    PluginCommands = MakeShareable(new FUICommandList);

    PluginCommands->MapAction(
        FAscentEditorCommands::Get().PluginAction,
        FExecuteAction::CreateRaw(this, &FAscentEditorModule::PluginButtonClicked),
        FCanExecuteAction());

    UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FAscentEditorModule::RegisterMenus));
}

void FAscentEditorModule::ShutdownModule()
{
    // This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
    // we call this function before unloading the module.

    UToolMenus::UnRegisterStartupCallback(this);

    UToolMenus::UnregisterOwner(this);
    FAscentEditorStyle::Shutdown();

    FAscentEditorCommands::Unregister();
}

void FAscentEditorModule::PluginButtonClicked()
{
    // Put your "OnButtonClicked" stuff here
    UEditorUtilityWidgetBlueprint* editorWidget = LoadObject<UEditorUtilityWidgetBlueprint>(nullptr, TEXT("/AscentCombatFramework/Editor/ACFAssistant_EUW"));

    if (editorWidget) {
        UEditorUtilitySubsystem* EditorUtilitySubsystem = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();
        EditorUtilitySubsystem->SpawnAndRegisterTab(editorWidget);
    } else {
        FText DialogText = FText::Format(
            LOCTEXT("PluginButtonDialogText", "Missing ACF Editor Widget"),
            FText::FromString(TEXT("FAscentEditorModule::PluginButtonClicked()")),
            FText::FromString(TEXT("AscentEditor.cpp")));
        FMessageDialog::Open(EAppMsgType::Ok, DialogText);
    }
}

void FAscentEditorModule::RegisterMenus()
{
    // Owner will be used for cleanup in call to UToolMenus::UnregisterOwner
    FToolMenuOwnerScoped OwnerScoped(this);

    {
        UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
        {
            FToolMenuSection& Section = Menu->FindOrAddSection("WindowLayout");
            Section.AddMenuEntryWithCommandList(FAscentEditorCommands::Get().PluginAction, PluginCommands);
        }
    }

    {
        UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.PlayToolBar");
        {
            FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("ACFTools");
            {
                FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(FAscentEditorCommands::Get().PluginAction));
                Entry.SetCommandList(PluginCommands);
            }
        }
    }
}

FString FAscentEditorModule::GetPluginNameForModule(const FString& ModuleName)
{
	TArray<TSharedRef<IPlugin>> EnabledPlugins = IPluginManager::Get().GetEnabledPlugins();

	for (const TSharedRef<IPlugin>& Plugin : EnabledPlugins)
	{
		const FPluginDescriptor& Descriptor = Plugin->GetDescriptor();

		for (const FModuleDescriptor& Module : Descriptor.Modules)
		{
			if (Module.Name.ToString() == ModuleName)
			{
				return Plugin->GetName();
			}
		}
	}

	return FString();
}

FString FAscentEditorModule::GetPluginName()
{
	FString ResolvedName = GetPluginNameForModule("AscentEditor");
	if (ResolvedName.IsEmpty())
	{
		ResolvedName = "AscentCombatFramework";
	}
	return ResolvedName;
}

FString FAscentEditorModule::GetPluginFriendlyName()
{
	const FString Name = GetPluginName();
	TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(Name);
	if (Plugin.IsValid())
	{
		return Plugin->GetDescriptor().FriendlyName;
	}
	return Name;
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAscentEditorModule, AscentEditor)