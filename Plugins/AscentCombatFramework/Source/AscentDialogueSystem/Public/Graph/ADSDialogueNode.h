// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ADSTypes.h"
#include "CoreMinimal.h"
#include "Graph/ADSGraphNode.h"

#include "ADSDialogueNode.generated.h"

class ACineCameraActor;
class ATargetPoint;
class UAGSCondition;
class UADSDialogueResponseNode;

/**
 * Dialogue node that can auto-progress to the next node when audio finishes.
 * Used primarily in ADSDialogues for conversations for both player and NPCs
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSDialogueNode : public UADSGraphNode {
	GENERATED_BODY()

protected:
	// If true, this node will automatically progress to the next node after a calculated duration
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Auto Progress")

	bool bAutoProgressNode = false;

	// How to calculate the duration before auto-progressing
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Auto Progress",
		meta = (EditCondition = "bAutoProgressNode", EditConditionHides))
	EDialogueNodeDurationType DurationType = EDialogueNodeDurationType::Auto;

	// Custom duration in seconds (used when DurationType is Custom)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Auto Progress",
		meta = (EditCondition = "bAutoProgressNode && DurationType == EDialogueNodeDurationType::Custom", EditConditionHides, ClampMin = "0.1"))
	float CustomDuration = 2.0f;

	// Average reading speed in characters per second (used for text-based calculation)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Auto Progress",
		meta = (EditCondition = "bAutoProgressNode && DurationType == EDialogueNodeDurationType::TextBased", EditConditionHides, ClampMin = "1.0"))
	float ReadingSpeed = 15.0f; // ~15 characters per second is average reading speed


	// The camera used to frame the speaking character during dialogue
	UPROPERTY(EditAnywhere, Category = "ADS|Camera")
	FDialogueCinematic CameraSettings;


	virtual void ActivateNode() override;

	/**
	 * Calculates the duration for this dialogue node based on the selected DurationType.
	 *
	 * Priority:
	 * 1. Custom duration (if DurationType is Custom)
	 * 2. Audio duration (if DurationType is Auto and audio exists)
	 * 3. Text-based duration (if DurationType is TextBased)
	 *
	 * @return The calculated duration in seconds
	 */
	UFUNCTION(BlueprintPure, Category = "ADS|Auto Progress")
	float CalculateNodeDuration() const;

	/**
	 * Checks if this node should auto-progress.
	 * Node auto-progresses if:
	 * 1. The node's bAutoProgressNode flag is true, OR
	 * 2. The owning dialogue is a World Dialogue with auto-progression enabled
	 */
	UFUNCTION(BlueprintPure, Category = "ADS|Auto Progress")
	virtual bool ShouldAutoProgress();

public:
	UADSDialogueNode();

	UFUNCTION(BlueprintCallable, Category = ADS)
	TArray<UADSDialogueResponseNode*> GetAllValidAnswers(APlayerController* inController);

	virtual bool CanBeActivated(APlayerController* inController) override;

	virtual void DeactivateNode() override;

private:
    // Timer handle for auto-progression
    FTimerHandle AutoProgressTimerHandle;

    // Callback when audio finishes and dialogue should auto-progress
    UFUNCTION()
    void OnAudioFinished();

    // Helper to calculate duration from text length
    float GetTextBasedDuration() const;

    // Helper to get audio duration safely
    float GetAudioDuration() const;
};
