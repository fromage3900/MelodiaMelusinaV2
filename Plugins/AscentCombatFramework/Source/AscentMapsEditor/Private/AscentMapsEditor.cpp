// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AscentMapsEditor.h"
#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"
#include "Logging.h"
#include "Modules/ModuleManager.h"
#include "ToolMenus.h"
#include "AMSMapEditorStyle.h"
#include "AMSMapEditorCommands.h"
#include "Interfaces/IPluginManager.h"
#include <Editor/EditorEngine.h>

static const FName AscentMapEditorTabName("AMSMapEditor");

#define LOCTEXT_NAMESPACE "FAscentMapsEditorModule"

void FAscentMapsEditor::StartupModule()
{
    FAMSMapsEditorStyle::Initialize();
    FAMSMapsEditorStyle::ReloadTextures();

    FAMSMapEditorCommands::Register();

    PluginCommands = MakeShareable(new FUICommandList);

    PluginCommands->MapAction(
        FAMSMapEditorCommands::Get().PluginAction,
        FExecuteAction::CreateRaw(this, &FAscentMapsEditor::PluginButtonClicked),
        FCanExecuteAction());

    UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FAscentMapsEditor::RegisterMenus));
}

void FAscentMapsEditor::ShutdownModule()
{
    UToolMenus::UnRegisterStartupCallback(this);

    UToolMenus::UnregisterOwner(this);

    FAMSMapsEditorStyle::Shutdown();

    FAMSMapEditorCommands::Unregister();
}

FString FAscentMapsEditor::GetPluginNameForModule(const FString& ModuleName)
{
	// Iterate through all enabled plugins
	TArray<TSharedRef<IPlugin>> EnabledPlugins = IPluginManager::Get().GetEnabledPlugins();
	
	for (const TSharedRef<IPlugin>& Plugin : EnabledPlugins)
	{
		// Get the plugin descriptor
		const FPluginDescriptor& Descriptor = Plugin->GetDescriptor();
		
		// Check if this plugin contains the specified module
		for (const FModuleDescriptor& Module : Descriptor.Modules)
		{
			if (Module.Name.ToString() == ModuleName)
			{
				return Plugin->GetName();
			}
		}
	}
	
	// If not found, return empty string
	return FString();
}

FString FAscentMapsEditor::GetPluginName()
{
	FString PluginName = GetPluginNameForModule("AscentMapsEditor");
	if (PluginName.IsEmpty())
	{
		PluginName = "AscentCombatFramework"; // Fallback to main plugin name
	}
	return PluginName;
}

void FAscentMapsEditor::PluginButtonClicked()
{
    const FString widgetPath = "/" + GetPluginName() + "/UITools/Maps/AMS_MapGenerator_EUW";
    UEditorUtilityWidgetBlueprint* editorWidget = LoadObject<UEditorUtilityWidgetBlueprint>(nullptr, *widgetPath);

    if (editorWidget) {
        UEditorUtilitySubsystem* EditorUtilitySubsystem = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();
        EditorUtilitySubsystem->SpawnAndRegisterTab(editorWidget);
    } else {
        FText DialogText = FText::Format(
            LOCTEXT("PluginButtonDialogText", "Missing Map Widget!"),
            FText::FromString(TEXT("FAscentMapsEditor::PluginButtonClicked()")),
            FText::FromString(TEXT("FAscentEditor.cpp")));
        FMessageDialog::Open(EAppMsgType::Ok, DialogText);
    }
}

void FAscentMapsEditor::RegisterMenus()
{
    // Owner will be used for cleanup in call to UToolMenus::UnregisterOwner
    FToolMenuOwnerScoped OwnerScoped(this);

    {
        UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
        {
            FToolMenuSection& Section = Menu->FindOrAddSection("WindowLayout");
            Section.AddMenuEntryWithCommandList(FAMSMapEditorCommands::Get().PluginAction, PluginCommands);
        }
    }

    {
        UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.PlayToolBar");
        {
            FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("MapTools");
            {
                FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(FAMSMapEditorCommands::Get().PluginAction));
                Entry.SetCommandList(PluginCommands);
            }
        }
    }
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAscentMapsEditor, AscentMapsEditor);
