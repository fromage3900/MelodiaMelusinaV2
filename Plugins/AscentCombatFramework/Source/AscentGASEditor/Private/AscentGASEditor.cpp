// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AscentGASEditor.h"
#include "ACFGASCommands.h"
#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"
#include <ToolMenuSection.h>
#include <ToolMenus.h>
#include <Templates/SharedPointer.h>

#define LOCTEXT_NAMESPACE "FAscentGASEditorModule"

void FAscentGASEditorModule::StartupModule()
{
	// Register the group, not individual factory
	FACFGASCommands::Register();

	PluginCommands = MakeShareable(new FUICommandList);
	PluginCommands->MapAction(
		FACFGASCommands::Get().OpenAttributeCreator,
		FExecuteAction::CreateLambda([this]() { FAscentGASEditorModule::OnClicked(); }),
		FCanExecuteAction());

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateLambda(
		[this]() {
			UToolMenu* FileMenu = UToolMenus::Get()->ExtendMenu("MainFrame.MainMenu.Tools");
			FToolMenuSection& Section = FileMenu->FindOrAddSection("Programming");
			Section.AddMenuEntryWithCommandList(FACFGASCommands::Get().OpenAttributeCreator, PluginCommands);
		}));
}

void FAscentGASEditorModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
}

void FAscentGASEditorModule::OnClicked()
{
	const FString widgetPath = "/" + PluginName + "/GASEditor/ACF_AttributesCreator_EUW";
	UEditorUtilityWidgetBlueprint* editorWidget = LoadObject<UEditorUtilityWidgetBlueprint>(nullptr, *widgetPath);

	if (editorWidget) {
		UEditorUtilitySubsystem* EditorUtilitySubsystem = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();
		EditorUtilitySubsystem->SpawnAndRegisterTab(editorWidget);
	}
	else {
		FText DialogText = FText::Format(
			LOCTEXT("PluginButtonDialogText", "Missing AttributeCreator Widget!"),
			FText::FromString(TEXT("FAscentGASEditorModule::OnClicked()")));
		FMessageDialog::Open(EAppMsgType::Ok, DialogText);
	}

}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAscentGASEditorModule, AscentGASEditor)
