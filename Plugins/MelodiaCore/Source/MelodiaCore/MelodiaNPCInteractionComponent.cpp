// Runtime interaction bridge for a lightweight exploration NPC.

#include "MelodiaNPCInteractionComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Core/QuillscriptAsset.h"
#include "Utils/Quill.h"

FText UMelodiaNPCInteractionComponent::GetPromptText() const
{
	return InteractionPrompt;
}

bool UMelodiaNPCInteractionComponent::HasDialogue() const
{
	return !QuillDialogue.IsNull() || !DialogueLines.IsEmpty() || !EncounterGuidance.IsEmpty();
}

bool UMelodiaNPCInteractionComponent::BeginInteraction()
{
	if (!HasDialogue())
	{
		return false;
	}

	bInteractionActive = true;
	bGuidanceDelivered = false;
	CurrentDialogueIndex = 0;
	OnInteractionStarted.Broadcast(NPCId);
	if (UQuillscriptAsset* QuillAsset = QuillDialogue.LoadSynchronous())
	{
		// Quill owns the visible VN overlay and issues only typed melodia: intents.
		// Do not also advance the legacy line/quest lane or acceptance will duplicate.
		UE_LOG(LogTemp, Log, TEXT("MELUSINA_NPC_QUILL_HANDOFF npc=%s asset=%s label=%s"),
			*NPCId.ToString(), *QuillAsset->GetName(), *QuillStartingLabel.ToString());
		UQuill::PlayScript(this, QuillAsset, QuillStartingLabel, GetOwner());
		bInteractionActive = false;
		OnInteractionFinished.Broadcast(NPCId);
		return true;
	}

	// No Quill asset assigned — legacy dialogue remains presentation-only. Quest
	// mutation is deliberately unavailable here: authored Quill notifications are
	// the sole shipping route into UMelodiaNarrativeSubsystem.
	UE_LOG(LogTemp, Log, TEXT("MELUSINA_NPC_LEGACY_DIALOGUE npc=%s dialogue_lines=%d guidance=%s"),
		*NPCId.ToString(), DialogueLines.Num(), *EncounterGuidance.ToString());

	if (DialogueLines.IsValidIndex(CurrentDialogueIndex))
	{
		OnDialogueLine.Broadcast(SpeakerName, DialogueLines[CurrentDialogueIndex]);
	}
	else
	{
		OnEncounterGuidance.Broadcast(SpeakerName, EncounterGuidance);
		bGuidanceDelivered = true;
	}
	return true;
}

bool UMelodiaNPCInteractionComponent::AdvanceInteraction()
{
	if (!bInteractionActive)
	{
		return false;
	}

	++CurrentDialogueIndex;
	if (DialogueLines.IsValidIndex(CurrentDialogueIndex))
	{
		OnDialogueLine.Broadcast(SpeakerName, DialogueLines[CurrentDialogueIndex]);
		return true;
	}

	if (!bGuidanceDelivered && !EncounterGuidance.IsEmpty())
	{
		OnEncounterGuidance.Broadcast(SpeakerName, EncounterGuidance);
		bGuidanceDelivered = true;
		return true;
	}

	bInteractionActive = false;
	OnInteractionFinished.Broadcast(NPCId);
	return false;
}

void UMelodiaNPCInteractionComponent::CancelInteraction()
{
	if (!bInteractionActive)
	{
		return;
	}

	bInteractionActive = false;
	OnInteractionFinished.Broadcast(NPCId);
}
