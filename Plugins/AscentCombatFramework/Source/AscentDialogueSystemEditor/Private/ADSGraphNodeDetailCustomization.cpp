#include "ADSGraphNodeDetailCustomization.h"
#include "ADSEditorSubsystem.h"
#include "DetailCategoryBuilder.h"
#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "Graph/ADSDialogue.h"
#include "Graph/ADSGraphNode.h"
#include "Graph/ADSWorldDialogue.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/SBoxPanel.h"
#include <Editor/EditorEngine.h>
#include "ADSVoiceConfigDataAsset.h"

TSharedRef<IDetailCustomization> FADSGraphNodeDetailCustomization::MakeInstance()
{
    return MakeShareable(new FADSGraphNodeDetailCustomization());
}

void FADSGraphNodeDetailCustomization::CustomizeDetails(IDetailLayoutBuilder& DetailBuilder)
{
    // Get the object being customized
    TArray<TWeakObjectPtr<UObject>> Objects;
    DetailBuilder.GetObjectsBeingCustomized(Objects);

    if (Objects.Num() == 1) {
        CachedNode = Cast<UADSGraphNode>(Objects[0].Get());
    }

    if (!CachedNode.IsValid()) {
        return;
    }

    IDetailCategoryBuilder& AIGenCategory = DetailBuilder.EditCategory(
        "AI Generation",
        FText::FromString("AI Generation"),
        ECategoryPriority::Default);

    AIGenCategory.AddCustomRow(FText::FromString("AI Generation Actions"))
        .WholeRowContent()
            [SNew(SHorizontalBox)

                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(2.0f, 0.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Generate TTS"))
                                .ToolTipText(FText::FromString("Generate audio from this node's dialogue text using ElevenLabs TTS."))
                                .OnClicked_Lambda([this]() {
                                    if (CachedNode.IsValid())
                                    {
                                        UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                        EditorSubsystem->GenerateTTSAudio(CachedNode.Get());
                                    }
                                    return FReply::Handled();
                                })]

                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(2.0f, 0.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Generate Facial Animation"))
                                .ToolTipText(FText::FromString(
                                    "Generate facial animation using MetaHuman Animator from this node's audio.\n"
                                    "Uses the node's GenerateBlink and Mood settings.\n"
                                    "Requires a SoundWave assigned to this node."))
                                .OnClicked_Lambda([this]() {
                                    if (CachedNode.IsValid())
                                    {
                                        UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                        EditorSubsystem->GenerateFacialAnimation(CachedNode.Get());
                                    }
                                    return FReply::Handled();
                                })]
            ];
}

TSharedRef<IDetailCustomization> FADSAIVoiceGeneratorComponentDetails::MakeInstance()
{
    return MakeShareable(new FADSAIVoiceGeneratorComponentDetails());
}

void FADSAIVoiceGeneratorComponentDetails::CustomizeDetails(IDetailLayoutBuilder& DetailBuilder)
{
    // Get the object being customized
    TArray<TWeakObjectPtr<UObject>> Objects;
    DetailBuilder.GetObjectsBeingCustomized(Objects);

    // Find or create the ADS TTS category
    IDetailCategoryBuilder& TTSCategory = DetailBuilder.EditCategory("Voice Generation");

    if (Objects.Num() == 1) {
        CachedComponent = Cast<UADSVoiceConfigDataAsset>(Objects[0].Get());
    }

    if (!CachedComponent.IsValid()) {
        return;
    }

    // Add buttons row
    TTSCategory.AddCustomRow(FText::FromString("TTS Actions"))
        .WholeRowContent()
            [SNew(SHorizontalBox)

                // Preview Voice Button
                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(2.0f, 0.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Preview Voice"))
                                .ToolTipText(FText::FromString("Preview the selected voice with sample text"))
                                .OnClicked_Lambda([this]() {
                                    UADSEditorSubsystem* editorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();

                                    editorSubsystem->PreviewSelectedVoice(CachedComponent->VoiceID);

                                    return FReply::Handled();
                                })]

    ];

    // Add second row for utility buttons
    TTSCategory.AddCustomRow(FText::FromString("TTS Utils"))
        .WholeRowContent()
            [SNew(SHorizontalBox)

                // Refresh Voices Button
                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(2.0f, 0.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Refresh Voices"))
                                .ToolTipText(FText::FromString("Fetch latest voices from ElevenLabs API"))
                                .OnClicked_Lambda([this]() {
                                    UADSEditorSubsystem* editorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                    editorSubsystem->RefreshVoicesFromAPI();
                                    return FReply::Handled();
                                })]

                // Clear Cache Button
                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(2.0f, 0.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Clear Cache"))
                                .ToolTipText(FText::FromString("Clear cached voice data"))
                                .OnClicked_Lambda([this]() {
                                    UADSEditorSubsystem* editorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                    editorSubsystem->ClearVoiceCache();
                                    return FReply::Handled();
                                })]];
}

// ============================================================================
// FADSDialogueDetailCustomization - Export/Import buttons for UADSDialogue
// ============================================================================

TSharedRef<IDetailCustomization> FADSDialogueDetailCustomization::MakeInstance()
{
    return MakeShareable(new FADSDialogueDetailCustomization());
}

void FADSDialogueDetailCustomization::CustomizeDetails(IDetailLayoutBuilder& DetailBuilder)
{
    // Get the dialogue object being customized
    TArray<TWeakObjectPtr<UObject>> Objects;
    DetailBuilder.GetObjectsBeingCustomized(Objects);

    if (Objects.Num() == 1)
    {
        CachedDialogue = Cast<UADSDialogue>(Objects[0].Get());
    }

    if (!CachedDialogue.IsValid())
    {
        return;
    }

    // Create the Export/Import category
    IDetailCategoryBuilder& ExportImportCategory = DetailBuilder.EditCategory(
        "Export Import",
        FText::FromString("Export / Import"),
        ECategoryPriority::Important);

    // Export button row
    ExportImportCategory.AddCustomRow(FText::FromString("Dialogue Export/Import Actions"))
        .WholeRowContent()
            [SNew(SHorizontalBox)

                // Export Button
                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(4.0f, 2.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Export Dialogue to Text"))
                                .ToolTipText(FText::FromString(
                                    "Export all dialogue text to a screenplay-formatted .txt file.\n"
                                    "The file will be saved in the Export/Import Directory with the dialogue asset name."))
                                .OnClicked_Lambda([this]() {
                                    if (CachedDialogue.IsValid())
                                    {
                                        UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                        EditorSubsystem->ExportDialogueToFile(CachedDialogue.Get());
                                    }
                                    return FReply::Handled();
                                })]

                // Import Button
                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(4.0f, 2.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Import Dialogue from Text"))
                                .ToolTipText(FText::FromString(
                                    "Import a screenplay-formatted .txt file and build the dialogue graph.\n"
                                    "Creates all dialogue nodes, response options, and connections.\n"
                                    "Participant names are auto-matched to GameplayTags (e.g., Character.Name).\n"
                                    "WARNING: This will replace the current dialogue graph."))
                                .OnClicked_Lambda([this]() {
                                    if (CachedDialogue.IsValid())
                                    {
                                        UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                        EditorSubsystem->ImportDialogueFromFile(CachedDialogue.Get());
                                    }
                                    return FReply::Handled();
                                })
                        ]
            ];

    // AI Generation category: batch-generate TTS voices for every node in the dialogue.
    IDetailCategoryBuilder& AIGenCategory = DetailBuilder.EditCategory(
        "AI Generation",
        FText::FromString("AI Generation"),
        ECategoryPriority::Important);

    AIGenCategory.AddCustomRow(FText::FromString("Dialogue AI Generation Actions"))
        .WholeRowContent()
            [SNew(SHorizontalBox)

                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(4.0f, 2.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Generate Voices for All Nodes"))
                                // While a batch is running, the button is disabled and the tooltip reports progress.
                                .IsEnabled_Lambda([]() {
                                    UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                    return EditorSubsystem && !EditorSubsystem->IsBatchGeneratingVoices();
                                })
                                .ToolTipText_Lambda([]() {
                                    UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                    if (EditorSubsystem && EditorSubsystem->IsBatchGeneratingVoices())
                                    {
                                        return FText::FromString(TEXT("In Progress... generating voices for all nodes. Please wait until it finishes."));
                                    }
                                    return FText::FromString(
                                        TEXT("Generate TTS audio for EVERY dialogue node using ElevenLabs TTS.\n"
                                             "You will be asked to confirm first, as this can be expensive "
                                             "(one API call per node) and may consume API credits.\n"
                                             "Progress and any per-node errors are reported via notifications and the Output Log."));
                                })
                                .OnClicked_Lambda([this]() {
                                    if (CachedDialogue.IsValid())
                                    {
                                        UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                        if (EditorSubsystem)
                                        {
                                            EditorSubsystem->GenerateTTSAudioForAllNodes(CachedDialogue.Get());
                                        }
                                    }
                                    return FReply::Handled();
                                })]

                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(4.0f, 2.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Generate Facial Animations for All Nodes"))
                                // While a facial-animation batch is running, the button is disabled and the tooltip reports progress.
                                .IsEnabled_Lambda([]() {
                                    UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                    return EditorSubsystem && !EditorSubsystem->IsBatchGeneratingFacialAnims();
                                })
                                .ToolTipText_Lambda([]() {
                                    UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                    if (EditorSubsystem && EditorSubsystem->IsBatchGeneratingFacialAnims())
                                    {
                                        return FText::FromString(TEXT("In Progress... generating facial animations for all nodes. Please wait until it finishes."));
                                    }
                                    return FText::FromString(
                                        TEXT("Generate MetaHuman facial animation for EVERY dialogue node that already has a SoundWave.\n"
                                             "Generate TTS audio first, as facial animation is audio-driven.\n"
                                             "You will be asked to confirm first. Nodes are processed sequentially "
                                             "(the MetaHuman pipeline is blocking) and the editor may be unresponsive while it runs.\n"
                                             "Progress and any per-node errors are reported via notifications and the Output Log."));
                                })
                                .OnClicked_Lambda([this]() {
                                    if (CachedDialogue.IsValid())
                                    {
                                        UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                        if (EditorSubsystem)
                                        {
                                            EditorSubsystem->GenerateAnimationsForAllNodes(CachedDialogue.Get());
                                        }
                                    }
                                    return FReply::Handled();
                                })]
            ];

    // World dialogues never support button-answer nodes — hide the mode enum entirely.
    const bool bIsWorldDialogue = CachedDialogue.IsValid() && CachedDialogue->IsA<UADSWorldDialogue>();
    if (bIsWorldDialogue)
    {
        DetailBuilder.HideProperty(
            DetailBuilder.GetProperty(GET_MEMBER_NAME_CHECKED(UADSDialogue, AIPlayerResponseMode)));
    }

    // ---- Conversational AI: description, response mode and generation button ----
    // The AIConversationDescription and AIPlayerResponseMode UPROPERTY rows are already
    // displayed automatically by the engine (Category = "AI Generation"). We only add
    // the action button here so it sits right below those fields.
    AIGenCategory.AddCustomRow(FText::FromString("Generate Dialogue with AI"))
        .WholeRowContent()
            [SNew(SHorizontalBox)

                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(4.0f, 2.0f)
                        [SNew(SButton)
                                .Text(FText::FromString("Generate Dialogue with AI"))
                                .ToolTipText(FText::FromString(
                                    "Generate an entire dialogue with AI using the OpenAI key in the Dialogue Settings.\n"
                                    "Sends the AI Conversation Description, the dialogue context, each participant's\n"
                                    "personality (from the Voice Config asset) and the selected Player Response Mode to the AI.\n"
                                    "The generated dialogue is shown in a preview window for review/editing before importing."))
                                .OnClicked_Lambda([this]() {
                                    if (CachedDialogue.IsValid())
                                    {
                                        UADSEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UADSEditorSubsystem>();
                                        EditorSubsystem->GenerateDialogueWithAI(CachedDialogue.Get());
                                    }
                                    return FReply::Handled();
                                })]
            ];
}
