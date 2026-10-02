// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AGSGraphEdge.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>
#include "ACFActionCondition.h"
#include "ACFTransition.generated.h"


/**
 *
 */
UCLASS()
class ASCENTCOMBOGRAPH_API UACFTransition : public UAGSGraphEdge {
    GENERATED_BODY()

protected:
    UPROPERTY(EditDefaultsOnly, Category = "ACF")
    FGameplayTag TransitionInputTag;

    // Array of conditions that must be satisfied for the transition
    UPROPERTY(EditAnywhere, Instanced, BlueprintReadWrite, Category = "ACF|Conditions")
    TArray<UACFActionCondition*> Conditions;

    

public:
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetTransitionInputTag() const
    {
        return TransitionInputTag;
    }

    /** Use weighted priorities instead of traditional sorting */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    bool bUseWeightedPriorities = false;

    /** Weight for probabilistic selection (if weighted priorities are enabled) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Transition", meta = (EditCondition = "bUseWeightedPriorities", ClampMin = "0.0", UIMin = "0.0"))
    float Weight = 1.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Transition")
    int32 Priority = 0; // Default priority
    
    // Evaluate all conditions to check if the transition is valid
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool AreConditionsMet(const class ACharacter* Character) const;
};
