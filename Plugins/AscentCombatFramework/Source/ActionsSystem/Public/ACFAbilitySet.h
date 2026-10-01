// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "ACFRPGTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFAbilitySet.generated.h"

/**
 * Data Asset that defines a collection of abilities to be granted to an actor.
 * Used by ACF to initialize abilities 
 */
UCLASS()
class ACTIONSSYSTEM_API UACFAbilitySet : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    /**
     * List of standard gameplay abilities to be granted.
     * Each entry defines a gameplay ability class, its input, level, and optional trigger tag.
     */
    UPROPERTY(EditAnywhere, meta = (TitleProperty = "TriggeringTag"), BlueprintReadWrite, Category = "ACF|Abilities")
    TArray<FAbilityConfig> Abilities;

    /**
     * List of action abilities to be granted.
     * These are a subclass of standard abilities, used for executing ACF Combo or contextual actions.
     */
    UPROPERTY(EditAnywhere, meta = (TitleProperty = "TriggeringTag", DisplayName = "ACF Abilities"), BlueprintReadWrite, Category = "ACF|Abilities")
    TArray<FActionAbilityConfig> ActionAbilities;

    /**
     * Tries to get the standard ability config matching the provided tag.
     * @param Tag The gameplay tag used to find the ability
     * @param OutConfig The output config if found
     * @return true if a matching config was found, false otherwise
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Abilities")
    bool TryGetAbilityByTag(const FGameplayTag& Tag, FAbilityConfig& OutConfig) const
    {
        const FAbilityConfig* Found = Abilities.FindByPredicate([&](const FAbilityConfig& Config) {
            return Config.TriggeringTag == Tag;
        });

        if (Found) {
            OutConfig = *Found;
            return true;
        }

        return false;
    }

    /**
     * Tries to get the action ability config matching the provided tag.
     * @param Tag The gameplay tag used to find the action ability
     * @param OutConfig The output config if found
     * @return true if a matching config was found, false otherwise
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Abilities")
    bool TryGetActionAbilityByTag(const FGameplayTag& Tag, FActionAbilityConfig& OutConfig) const
    {
        const FActionAbilityConfig* Found = ActionAbilities.FindByPredicate([&](const FActionAbilityConfig& Config) {
            return Config.TriggeringTag == Tag;
        });

        if (Found) {
            OutConfig = *Found;
            return true;
        }

        return false;
    }
};