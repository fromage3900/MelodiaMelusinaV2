// Runtime interaction bridge for a lightweight exploration NPC.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaQuestManagerBase.h"
#include "MelodiaNPCInteractionComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaNPCDialogueLineEvent, FText, Speaker, FText, Line);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaNPCInteractionEvent, FName, NPCId);

UCLASS(Blueprintable, ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class MELODIACORE_API UMelodiaNPCInteractionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	/** Optional authored VN scene. When assigned, Quill owns dialogue/choices and melodia: intents own quest actions. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Quill")
	TSoftObjectPtr<class UQuillscriptAsset> QuillDialogue;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Quill")
	FName QuillStartingLabel = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Interaction")
	FName NPCId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Interaction")
	FText SpeakerName = FText::FromString(TEXT("Guide"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Interaction")
	FText InteractionPrompt = FText::FromString(TEXT("Press E to talk"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Interaction", meta=(MultiLine=true))
	TArray<FText> DialogueLines;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Interaction", meta=(MultiLine=true))
	FText EncounterGuidance = FText::FromString(TEXT("Follow the lanterns to the rhythm echo ahead."));

	// --- Quest integration (cozy: quest givers accept on interaction start, complete on end) ---

	/** When true, AcceptQuest fires on BeginInteraction for QuestToGive. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Quest")
	bool bIsQuestGiver = false;

	/** Quest to accept when interaction begins and bIsQuestGiver is true. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Quest")
	FMelodiaQuestDef QuestToGive;

	/** If set, CompleteQuest fires when the interaction finishes (dialogue exhausted or cancelled). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC|Quest")
	FName QuestToCompleteOnEnd;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|NPC|Interaction")
	int32 CurrentDialogueIndex = INDEX_NONE;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|NPC|Interaction")
	bool bInteractionActive = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|NPC|Interaction")
	bool bGuidanceDelivered = false;

	UPROPERTY(BlueprintAssignable, Category="Melodia|NPC|Interaction")
	FMelodiaNPCInteractionEvent OnInteractionStarted;

	UPROPERTY(BlueprintAssignable, Category="Melodia|NPC|Interaction")
	FMelodiaNPCDialogueLineEvent OnDialogueLine;

	UPROPERTY(BlueprintAssignable, Category="Melodia|NPC|Interaction")
	FMelodiaNPCInteractionEvent OnInteractionFinished;

	UPROPERTY(BlueprintAssignable, Category="Melodia|NPC|Interaction")
	FMelodiaNPCDialogueLineEvent OnEncounterGuidance;

	UFUNCTION(BlueprintPure, Category="Melodia|NPC|Interaction")
	FText GetPromptText() const;

	UFUNCTION(BlueprintCallable, Category="Melodia|NPC|Interaction")
	bool BeginInteraction();

	UFUNCTION(BlueprintCallable, Category="Melodia|NPC|Interaction")
	bool AdvanceInteraction();

	UFUNCTION(BlueprintCallable, Category="Melodia|NPC|Interaction")
	void CancelInteraction();

	UFUNCTION(BlueprintPure, Category="Melodia|NPC|Interaction")
	bool HasDialogue() const;
};
