// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ADSBaseDialoguePartecipantComponent.h"
#include "ADSTypes.h"
#include "AGSGraph.h"
#include "CoreMinimal.h"
#include <Engine/DataTable.h>
#include <GameFramework/Character.h>

#include "ADSDialogue.generated.h"

class UADSDialoguePartecipantComponent;
class UADSStartDialogueNode;
class UADSGraphNode;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueNodeActivated, const FGuid&, nodeId);

/**
 * Represents a dialogue asset built on top of UAGSGraph, managing the flow and logic of dialogue nodes.
 * Handles dialogue participants, node transitions, and broadcasting dialogue-related events.
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSDialogue : public UAGSGraph {
	GENERATED_BODY()

public:
	UADSDialogue();


	/**
	 * Starts the dialogue sequence with the provided participants and player controller.
	 * Broadcasts OnDialogueStarted and activates the first node of the dialogue.
	 *
	 * @param inController The player controller starting the dialogue.
	 * @param participants The array of dialogue participants involved in this conversation.
	 * @return The first dialogue node that gets activated.
	 */
	UFUNCTION(BlueprintCallable, Category = ADS)
	class UAGSGraphNode* StartDialogue(class APlayerController* inController, const TArray<UADSBaseDialoguePartecipantComponent*>& participants);

	/**
	 * Retrieves all response nodes available for the current active dialogue node.
	 *
	 * @return An array of dialogue response nodes representing the player's possible answers.
	 */
	UFUNCTION(BlueprintCallable, Category = ADS)
	TArray<class UADSDialogueResponseNode*> GetAllButtonAnswersForCurrentNode() const;

	/**
	 * Moves the dialogue to the next node based on the current node's output or selected response.
	 * Broadcasts OnDialogueNodeActivated when a new node is reached.
	*
	* @return The next dialogue node, or nullptr if the dialogue has ended.
	*/
	UFUNCTION(BlueprintCallable, Category = ADS)
	class UADSDialogueNode* MoveToNextNode();

	/**
	 * Checks whether the dialogue has a participant with the specified tag.
	 *
	 * @param partecipantTag The gameplay tag identifying the participant.
	 * @return True if the participant is part of this dialogue, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ADS)
	bool HasPartecipant(const FGameplayTag& partecipantTag) const { return partecipantsRef.Contains(partecipantTag); }

	/**
	 * Returns whether the dialogue has started.
	 *
	 * @return True if the dialogue has been initiated, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ADS)
	bool IsDialogueStarted() const { return bIsStarted; }

	/**
	* Finds and returns a dialogue participant component by gameplay tag.
	*
	* @param partecipantTag The gameplay tag identifying the participant.
	* @return The participant component if found, nullptr otherwise.
	*/
	UFUNCTION(BlueprintCallable, Category = ADS)
	UADSBaseDialoguePartecipantComponent* FindPartecipant(FGameplayTag partecipantTag) const;

	/** Event triggered when the dialogue starts. */
	UPROPERTY(BlueprintAssignable, Category = ADS)
	FOnDialogueStarted OnDialogueStarted;

	/** Event triggered when the dialogue ends. */
	UPROPERTY(BlueprintAssignable, Category = ADS)
	FOnDialogueEnded OnDialogueEnded;

	/** Event triggered when a dialogue node is activated. */
	UPROPERTY(BlueprintAssignable, Category = ADS)
	FOnDialogueNodeActivated OnDialogueNodeActivated;


	/**
	 * Returns the current active dialogue node.
	 *
	 * @return The currently active node in the dialogue graph.
	 */
	UFUNCTION(BlueprintPure, Category = ADS)
	FORCEINLINE class UADSGraphNode* GetCurrentNode() const { return currentNode; }

	/**
	 * Returns the gameplay tag identifying this dialogue.
	 *
	 * @return The dialogue tag.
	 */
	UFUNCTION(BlueprintPure, Category = ADS)
	FORCEINLINE FGameplayTag GetDialogueTag() const { return DialogueTag; }

	/**
	 * Returns the default participant tag used when no explicit participant is defined.
	 *
	 * @return The default participant tag.
	 */
	UFUNCTION(BlueprintPure, Category = ADS)
	FORCEINLINE FGameplayTag GetDefaultParticipantTag() const { return DefaultParticipantTag; }

	FORCEINLINE bool operator==(const FGameplayTag& OtherTag) const
	{
		return this->DialogueTag == OtherTag;
	}

	FORCEINLINE bool operator!=(const FGameplayTag& OtherTag) const
	{
		return this->DialogueTag != OtherTag;
	}
	FORCEINLINE bool operator==(const UADSDialogue*& Other) const
	{
		return DialogueTag == Other->DialogueTag;
	}

	FORCEINLINE bool operator!=(const UADSDialogue*& Other) const
	{
		return DialogueTag != Other->DialogueTag;
	}

	
#if WITH_EDITORONLY_DATA
	/** Directory path for exporting/importing dialogue screenplay files */
	UPROPERTY(EditDefaultsOnly, Category = "Export Import")
	FDirectoryPath ExportImportDirectory;

	/** Textual description / constraints of what this conversation should be about.
	 *  Used as the main prompt when generating the entire dialogue with AI.
	 *  To add player branching, explicitly mention it here, e.g.:
	 *  "The player can decide whether to help the guard or refuse." */
	UPROPERTY(EditDefaultsOnly, Category = "AI Generation", meta = (MultiLine = true))
	FString AIConversationDescription;

	/** Characters that must appear in the generated dialogue.
	 *  The AI will use ONLY these tags as speakers — it will never invent new characters.
	 *  Only the tag containing "Player" can have response options (branching);
	 *  all other characters always speak in linear dialogue nodes. */
	UPROPERTY(EditDefaultsOnly, Category = "AI Generation")
	TArray<FGameplayTag> AIParticipantTags;

	/** Approximate number of dialogue beats (speaker turns) to generate.
	 *  This is a soft hint to the AI — the actual length may vary slightly
	 *  depending on the conversation description and branching. */
	UPROPERTY(EditAnywhere, Category = "AI Generation")
	int32 AIDialogueTreeLength = 8;

	/** Controls the node type used for player lines:
	 *  - Player Answers: all player lines are button-answer nodes (1 button per beat by default).
	 *  - Player Nodes: all player lines are normal dialogue nodes (no button answers).
	 *  - Mixed: AI picks button-answer or dialogue node per beat.
	 *  In ALL modes, branches (multiple options) are generated ONLY when the
	 *  AI Conversation Description explicitly describes a player choice. */
	UPROPERTY(EditDefaultsOnly, Category = "AI Generation")
	EADSAIPlayerResponseMode AIPlayerResponseMode = EADSAIPlayerResponseMode::Mixed;
#endif

	bool ActivateNode(class UAGSGraphNode* node) override;
	void EndDialogue();
	bool GetUseDefaultCameraSettings() const { return UseDefaultCameraSettings; }
	void SetUseDefaultCameraSettings(bool val) { UseDefaultCameraSettings = val; }
protected:
	/*Unique Tag for this Dialogue*/
	UPROPERTY(EditDefaultsOnly, Category = ADS)
	FGameplayTag DialogueTag;

	UPROPERTY(EditDefaultsOnly, meta = (Categories = "Character"), Category = ADS)
	FGameplayTag DefaultParticipantTag;

	UPROPERTY(EditDefaultsOnly, Category = ADS)
	bool UseDefaultCameraSettings;

private:
	TMap<FGameplayTag, TObjectPtr<UADSBaseDialoguePartecipantComponent>> partecipantsRef;

	TObjectPtr<UADSGraphNode> currentNode;

	TObjectPtr<UADSStartDialogueNode> currentDialogueStart;

	bool bIsStarted;


};
