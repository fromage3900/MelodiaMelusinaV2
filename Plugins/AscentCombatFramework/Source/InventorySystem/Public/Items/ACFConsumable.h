// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFItem.h"
#include "ACFRPGTypes.h"
#include "ACMTypes.h"
#include "ARSTypes.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>

#include "ACFConsumable.generated.h"

class UGameplayEffect;
class APawn;
class UAbilitySystemComponent;

/**
 * Represents a consumable item that applies effects when used.
 * Effects may include stat modifications, gameplay effects, or visual/audio feedback.
 */
UCLASS()
class INVENTORYSYSTEM_API UACFConsumable : public UACFItem {
    GENERATED_BODY()

public:
    UACFConsumable();

    /**
     * Returns the flat statistic modifiers applied when this item is used.
     * @return The list of stat modifiers.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    TArray<FStatisticValue> GetStatsModifiers() const { return StatModifier; }

    /**
     * Returns the timed attribute modifiers applied when this item is used.
     * @return The list of timed modifiers.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    TArray<FTimedAttributeSetModifier> GetTimedModifiers() const { return TimedAttributeSetModifier; }

    /**
     * Returns the GameplayEffects applied when this item is used.
     * @return The list of GameplayEffect configurations.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    TArray<FGameplayEffectConfig> GetGameplayEffects() const;

    /**
     * Returns the tag representing the desired use action for this item.
     * @return The use action tag.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetDesiredUseAction() const { return DesiredUseAction; }

    /**
     * Checks if this item can be used to the given pawn.
     * @param pawn The pawn the item is used on.
     * @return true if the item can be used, false otherwise.
     */
    UFUNCTION(BlueprintPure, BlueprintNativeEvent, Category = ACF)
    bool CanBeUsed(const APawn* Pawn) const;

    /**
     * Returns whether the item should be consumed after use.
     * @return true if the item is consumed on use.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetConsumeOnUse() const { return bConsumeOnUse; }

    /**
     * Sets whether the item should be consumed after use.
     * @param val If true, the item will be removed from inventory after use.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetConsumeOnUse(bool val) { bConsumeOnUse = val; }

    /**
     * Returns the visual/audio effect played when the item is used.
     * @return The on-used action effect.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FActionEffect GetOnUsedEffect() const { return OnUsedEffect; }

    /**
     * Sets the visual/audio effect to play when the item is used.
     * @param val The effect to assign.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetOnUsedEffect(FActionEffect val) { OnUsedEffect = val; }

protected:
    /**
     * Called when the item is used. Override to implement custom logic.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnItemUsed(APawn* target);

    /** Flat statistic modifiers applied once the item is used  */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Consumable")
    TArray<FStatisticValue> StatModifier;

    /** Timed attribute modifiers applied once the item is used  */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Consumable")
    TArray<FTimedAttributeSetModifier> TimedAttributeSetModifier;

    /** Action effect (VFX/SFX) to play when the item is used. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Consumable")
    FActionEffect OnUsedEffect;

    /** Tag that defines what kind of use action should be triggered (e.g. Drink, Eat). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Consumable")
    FGameplayTag DesiredUseAction;

    /** Optional GameplayCue triggered when the item is used. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Consumable")
    FGameplayTag OnUsedGameplayCue;

    /** If true, the item is consumed and removed from inventory after use. */
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "ACF|Consumable")
    bool bConsumeOnUse = true;

    friend class UACFInventoryComponent;

private:
    void Internal_UseItem(class APawn* target);
    UAbilitySystemComponent* GetAbilityComponent(APawn* target) const;
};
