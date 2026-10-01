// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Data/ACFCharacterFragment.h"
#include "ACFExecutionConditionsFragment.generated.h"

class UCASAnimCondition;

/**
 * Character fragment that replaces the AnimStartingConditions array on the pawn's
 * UACFCombinedAnimSlaveComponent at character initialization.
 *
 * Use it to drive the execution / contextual-animation gating rules of a character
 * purely from data: add this fragment to UACFCharacterDataAsset::Fragments and author
 * the conditions in-place. When the character is initialized the existing conditions
 * on the slave component are discarded and replaced with the ones authored here.
 *
 * Safe to re-apply at runtime to hot-swap the condition set (e.g. on phase change).
 */
UCLASS(Blueprintable, EditInlineNew, DefaultToInstanced)
class EXECUTIONSSYSTEM_API UACFExecutionConditionsFragment : public UACFCharacterFragment
{
    GENERATED_BODY()

public:
    /**
     * Conditions to assign to the slave component. They fully replace whatever was
     * previously configured on the component (Defaults, Blueprint or runtime).
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Instanced, Category = "ACF|Executions")
    TArray<TObjectPtr<UCASAnimCondition>> Conditions;

    virtual void ApplyFragment_Implementation(APawn* pawnOwner) override;
};
