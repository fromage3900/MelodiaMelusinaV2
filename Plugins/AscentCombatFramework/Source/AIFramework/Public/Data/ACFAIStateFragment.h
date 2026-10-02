// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Data/ACFCharacterFragment.h"
#include "Data/ACFAIRoutineDataAsset.h"
#include "GameplayTagContainer.h"
#include "ACFAIStateFragment.generated.h"

class AACFSplinePath;
class UACFAIRoutineComponent;
class AACFAIController;

/**
 * Fragment that configures the initial AI state on the character's AI controller.
 * Sets the DefaultState gameplay tag and optionally assigns a patrol path or a routine data asset.
 * Replaces UACFAIRoutineFragment — add this fragment to a UACFCharacterDataAsset's Fragments array.
 */
UCLASS(Blueprintable, EditInlineNew, DefaultToInstanced)
class AIFRAMEWORK_API UACFAIStateFragment : public UACFCharacterFragment
{
	GENERATED_BODY()

public:
	/** The gameplay tag set as the AI controller's default state on init (e.g. AIState.Patrol, AIState.Idle). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "AIState"), Category = "ACF|AI State")
	FGameplayTag DefaultState;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (InlineEditConditionToggle), Category = "ACF|AI State")
	bool bHasPatrolPath = false;

	/** Patrol path assigned to the AI's patrol component on init. Only used when bHasPatrolPath is enabled. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bHasPatrolPath", EditConditionHides), Category = "ACF|AI State")
	TSoftObjectPtr<AACFSplinePath> PatrolPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (InlineEditConditionToggle), Category = "ACF|AI State")
	bool bHasRoutine = false;

	/** Routine data asset assigned to the AI's routine component on init. Only used when bHasRoutine is enabled. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bHasRoutine", EditConditionHides), Category = "ACF|AI State")
	TObjectPtr<UACFAIRoutineDataAsset> RoutineDataAsset;

	virtual void ApplyFragment_Implementation(APawn* pawnOwner) override;
};
