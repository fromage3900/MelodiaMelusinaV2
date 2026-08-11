// Runtime interaction bridge for a lightweight exploration NPC.

#include "MelodiaNPCInteractionComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Core/QuillscriptAsset.h"
#include "Utils/Quill.h"

namespace
{
	FName QuestForNPC(const FName NPCId)
	{
		if (NPCId == TEXT("SD_02_PetalPriestess")) return TEXT("melodia_q_echo_01");
		if (NPCId == TEXT("CW_01_StarWeaver")) return TEXT("melodia_q_echo_02");
		if (NPCId == TEXT("MD_01_TwilightDancer")) return TEXT("melodia_q_echo_03");
		return NAME_None;
	}

	void NotifyPersonaQuest(UWorld* World, const FName NPCId)
	{
		const FName QuestId = QuestForNPC(NPCId);
		UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
		UClass* PersonaClass = FindObject<UClass>(nullptr, TEXT("/Script/BS_GodFile.MelodiaPersonaSubsystem"));
		UGameInstanceSubsystem* Persona = GameInstance && PersonaClass ? GameInstance->GetSubsystemBase(PersonaClass) : nullptr;
		UFunction* Handler = Persona ? Persona->FindFunction(TEXT("HandleNarrativeQuest")) : nullptr;
		if (Handler && !QuestId.IsNone())
		{
			struct FQuestParams { FName QuestId; } Params{QuestId};
			Persona->ProcessEvent(Handler, &Params);
		}
	}
}

FText UMelodiaNPCInteractionComponent::GetPromptText() const
{
	return InteractionPrompt;
}

bool UMelodiaNPCInteractionComponent::HasDialogue() const
{
	return !QuillDialogue.IsNull() || !DialogueLines.IsEmpty() || !EncounterGuidance.IsEmpty();
}

static void TryAcceptQuest(UWorld* World, const FMelodiaQuestDef& QuestDef)
{
	if (!World || QuestDef.QuestId == NAME_None) return;
	if (AMelodiaQuestManagerBase* QuestManager = AMelodiaQuestManagerBase::Get(World))
	{
		QuestManager->AcceptQuest(QuestDef);
	}
}

static void TryCompleteQuest(UWorld* World, FName QuestId)
{
	if (!World || QuestId == NAME_None) return;
	if (AMelodiaQuestManagerBase* QuestManager = AMelodiaQuestManagerBase::Get(World))
	{
		QuestManager->CompleteQuest(QuestId);
	}
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

	// No Quill asset assigned — fall through to legacy DialogueLines / EncounterGuidance.
	UE_LOG(LogTemp, Log, TEXT("MELUSINA_NPC_LEGACY_DIALOGUE npc=%s dialogue_lines=%d guidance=%s"),
		*NPCId.ToString(), DialogueLines.Num(), *EncounterGuidance.ToString());

	NotifyPersonaQuest(GetWorld(), NPCId);

	// Cozy: accept quest on first interaction (no-penalty duplicate guards inside AcceptQuest).
	if (bIsQuestGiver)
	{
		TryAcceptQuest(GetWorld(), QuestToGive);
	}

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
	TryCompleteQuest(GetWorld(), QuestToCompleteOnEnd);
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
	TryCompleteQuest(GetWorld(), QuestToCompleteOnEnd);
	OnInteractionFinished.Broadcast(NPCId);
}
