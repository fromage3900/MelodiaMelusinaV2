// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSTypes.h"
#include "Actions/ACFActionAbility.h"
#include "CoreMinimal.h"

#include "ACFCureAction.generated.h"

/**
 * Represents a healing or restorative action that modifies a specific statistic (e.g., Health, Mana).
 * Typically used as part of a spell 
 */
UCLASS()
class SPELLACTIONS_API UACFCureAction : public UACFActionAbility {
    GENERATED_BODY()

protected:
    // The stat to be modified by this action (e.g., +50 Health)
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACF)
    FStatisticValue StatModifier;

    virtual void OnNotablePointReached_Implementation() override;
};
