// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFActionsSet.generated.h"

/**
 * Stores a collection of action states associated with gameplay tags.
 * Used to define all actions available to a character or asset in a modular way.
 * Each entry represents a specific gameplay action (e.g., attack, dodge, interact).
 */
UCLASS(BlueprintType, Blueprintable, Category = ACF)
class ACTIONSSYSTEM_API UACFActionsSet : public UObject {
    GENERATED_BODY()

protected:
    /**
     * Array of all gameplay actions available in this set.
     * Each FActionState contains configuration data for one actionable gameplay state.
     * Displayed using the action tag as label in the editor.
     */
    UPROPERTY(EditAnywhere, meta = (TitleProperty = "TagName"), BlueprintReadWrite, Category = "ACF | Actions")
    TArray<FActionState> Actions;

public:
    TArray<FActionState>& GetActionsRef()
    {
        return Actions;
    }

    bool GetActionByTag(const FGameplayTag& action, FActionState& outAction) const;

    void GetActions(TArray<FActionState>& outActions) const
    {
        outActions = Actions;
    }
};
