// Copyright 1998-2019 Epic Games, Inc. All Rights Reserved.

#include "AscentDialogueSystemEditor.h"
#include "ADSGraphNodeDetailCustomization.h"
#include "ADSEditorSubsystem.h"
#include "Graph/ADSDialogue.h"
#include "Graph/ADSGraphNode.h"
#include "PropertyEditorModule.h"
#include "ADSDialogueDeveloperSettings.h"
#include "ADSVoiceConfigDataAsset.h"
#include "ContentBrowserModule.h"
#include "ContentBrowserDelegates.h"
#include "Editor.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"

#define LOCTEXT_NAMESPACE "FAscentDialogueSystemEditorModule"

void FAscentDialogueSystemEditorModule::StartupModule()
{
    // Register custom detail panel for ADSGraphNode
    FPropertyEditorModule& PropertyModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");

    PropertyModule.RegisterCustomClassLayout(
        UADSGraphNode::StaticClass()->GetFName(),
        FOnGetDetailCustomizationInstance::CreateStatic(&FADSGraphNodeDetailCustomization::MakeInstance));
    PropertyModule.RegisterCustomClassLayout(
        UADSVoiceConfigDataAsset::StaticClass()->GetFName(),
        FOnGetDetailCustomizationInstance::CreateStatic(&FADSAIVoiceGeneratorComponentDetails::MakeInstance));

    PropertyModule.RegisterCustomClassLayout(
        UADSDialogue::StaticClass()->GetFName(),
        FOnGetDetailCustomizationInstance::CreateStatic(&FADSDialogueDetailCustomization::MakeInstance));

    // Register a Content Browser context-menu extender so users can batch-generate voices and
    // facial animations for one or more selected Dialogue assets.
    FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    TArray<FContentBrowserMenuExtender_SelectedAssets>& MenuExtenders = ContentBrowserModule.GetAllAssetViewContextMenuExtenders();
    MenuExtenders.Add(FContentBrowserMenuExtender_SelectedAssets::CreateRaw(this, &FAscentDialogueSystemEditorModule::OnExtendDialogueAssetSelectionMenu));
    ContentBrowserExtenderHandle = MenuExtenders.Last().GetHandle();
}

void FAscentDialogueSystemEditorModule::ShutdownModule()
{
    // Unregister customizations
    if (FModuleManager::Get().IsModuleLoaded("PropertyEditor")) {
        FPropertyEditorModule& PropertyModule = FModuleManager::GetModuleChecked<FPropertyEditorModule>("PropertyEditor");
        PropertyModule.UnregisterCustomClassLayout(UADSGraphNode::StaticClass()->GetFName());
        PropertyModule.UnregisterCustomClassLayout(UADSVoiceConfigDataAsset::StaticClass()->GetFName());
        PropertyModule.UnregisterCustomClassLayout(UADSDialogue::StaticClass()->GetFName());
    }

    // Unregister the Content Browser context-menu extender
    if (ContentBrowserExtenderHandle.IsValid() && FModuleManager::Get().IsModuleLoaded("ContentBrowser")) {
        FContentBrowserModule& ContentBrowserModule = FModuleManager::GetModuleChecked<FContentBrowserModule>("ContentBrowser");
        ContentBrowserModule.GetAllAssetViewContextMenuExtenders().RemoveAll(
            [this](const FContentBrowserMenuExtender_SelectedAssets& Delegate) {
                return Delegate.GetHandle() == ContentBrowserExtenderHandle;
            });
        ContentBrowserExtenderHandle.Reset();
    }
}

TSharedRef<FExtender> FAscentDialogueSystemEditorModule::OnExtendDialogueAssetSelectionMenu(const TArray<FAssetData>& SelectedAssets)
{
    TSharedRef<FExtender> Extender = MakeShared<FExtender>();

    // Filter the selection down to Dialogue assets (without forcing a load).
    TArray<TWeakObjectPtr<UADSDialogue>> SelectedDialogues;
    for (const FAssetData& Asset : SelectedAssets) {
        const UClass* AssetClass = Asset.GetClass();
        if (AssetClass && AssetClass->IsChildOf(UADSDialogue::StaticClass())) {
            if (UADSDialogue* Dialogue = Cast<UADSDialogue>(Asset.GetAsset())) {
                SelectedDialogues.Add(Dialogue);
            }
        }
    }

    if (SelectedDialogues.Num() == 0) {
        return Extender;
    }

    Extender->AddMenuExtension(
        "CommonAssetActions",
        EExtensionHook::After,
        nullptr,
        FMenuExtensionDelegate::CreateRaw(this, &FAscentDialogueSystemEditorModule::PopulateDialogueBatchMenu, SelectedDialogues));

    return Extender;
}

void FAscentDialogueSystemEditorModule::PopulateDialogueBatchMenu(FMenuBuilder& MenuBuilder, TArray<TWeakObjectPtr<UADSDialogue>> Dialogues)
{
    auto ResolveDialogues = [Dialogues]() {
        TArray<UADSDialogue*> Resolved;
        for (const TWeakObjectPtr<UADSDialogue>& Weak : Dialogues) {
            if (UADSDialogue* Dialogue = Weak.Get()) {
                Resolved.Add(Dialogue);
            }
        }
        return Resolved;
    };

    MenuBuilder.BeginSection("AscentDialogueBatch", LOCTEXT("AscentDialogueBatchSection", "Ascent Dialogue"));

    MenuBuilder.AddMenuEntry(
        LOCTEXT("GenerateVoicesLabel", "Generate Voices (TTS) for Selected Dialogues"),
        LOCTEXT("GenerateVoicesTooltip", "Generates TTS audio for every dialogue node in the selected Dialogue assets (sequentially)."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda([ResolveDialogues]() {
            if (GEditor) {
                if (UADSEditorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>()) {
                    Subsystem->GenerateTTSForDialogues(ResolveDialogues());
                }
            }
        })));

    MenuBuilder.AddMenuEntry(
        LOCTEXT("GenerateFacialLabel", "Generate Facial Animations for Selected Dialogues"),
        LOCTEXT("GenerateFacialTooltip", "Generates MetaHuman facial animation for every dialogue node that already has a SoundWave (skipping nodes already animated), across the selected Dialogue assets (sequentially)."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda([ResolveDialogues]() {
            if (GEditor) {
                if (UADSEditorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>()) {
                    Subsystem->GenerateFacialAnimationForDialogues(ResolveDialogues(), /*bForceRegenerate*/ false);
                }
            }
        })));

    MenuBuilder.AddMenuEntry(
        LOCTEXT("ForceVoicesLabel", "Force Regenerate Voices (TTS) for Selected Dialogues"),
        LOCTEXT("ForceVoicesTooltip", "Regenerates TTS audio for EVERY dialogue node, including nodes that already have a sound assigned. Consumes API credits for all nodes."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda([ResolveDialogues]() {
            if (GEditor) {
                if (UADSEditorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>()) {
                    Subsystem->GenerateTTSForDialogues(ResolveDialogues(), /*bForceRegenerate*/ true);
                }
            }
        })));

    MenuBuilder.AddMenuEntry(
        LOCTEXT("ForceFacialLabel", "Force Regenerate Facial Animations for Selected Dialogues"),
        LOCTEXT("ForceFacialTooltip", "Regenerates MetaHuman facial animation for EVERY node that has a SoundWave, including nodes that already have a facial animation."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda([ResolveDialogues]() {
            if (GEditor) {
                if (UADSEditorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>()) {
                    Subsystem->GenerateFacialAnimationForDialogues(ResolveDialogues(), /*bForceRegenerate*/ true);
                }
            }
        })));

    MenuBuilder.EndSection();
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAscentDialogueSystemEditorModule, AscentDialogueSystemEditor)