// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Graph/ADSDialogue.h"
#include "ADSDialogueWidgetInterface.generated.h"

class UADSAIDialoguePartecipantComponent;

/** Interface for widgets that display or drive dialogue (UI that shows lines and choices). */
UINTERFACE(Blueprintable)
class UADSDialogueWidgetInterface : public UInterface {
    GENERATED_BODY()
};

/**
 * Implement this interface on widgets that need to be initialized with a dialogue or AI participant.
 * Used by the dialogue system to set up the UI when starting or progressing dialogue.
 */
class ASCENTDIALOGUESYSTEM_API IADSDialogueWidgetInterface
{
	GENERATED_BODY()

public:
	/** Initialize the widget with a dialogue asset to play. */
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category = ADS)
	void SetupWithDialogue(UADSDialogue* dialogueToPlay);

	/** Initialize the widget for AI-driven dialogue with the given participant and optional player message. */
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category = "ADS|AI")
	void SetupWithAIDialogue(UADSAIDialoguePartecipantComponent* AIParticipant, const FString& PlayerMessage);

	/** Progress the AI dialogue with a new player message and message count. */
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category = "ADS|AI")
	void ProgressWithAIDialogue(UADSAIDialoguePartecipantComponent* AIParticipant, const FString& PlayerMessage, int32 MessageCount);
};
