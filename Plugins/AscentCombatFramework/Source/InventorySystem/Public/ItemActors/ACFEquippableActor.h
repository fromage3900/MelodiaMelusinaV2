// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ItemActors/ACFItemActor.h"
#include "Items/ACFEquippableItem.h"

#include "ACFEquippableActor.generated.h"


struct FAttributesSetModifier;

/**
 *
 */
UCLASS()
class INVENTORYSYSTEM_API AACFEquippableActor : public AACFItemActor {
    GENERATED_BODY()

protected:

    AACFEquippableActor();
    /**
     * Returns the attribute modifier
     * @return The attribute set modifier.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FAttributesSetModifier GetAttributeSetModifier() const
    {
        return GetEquippableDefinition()->GetAttributeSetModifier();
    }

    /**
     * Sets the attribute modifier
     * @param inAttributeModifier The modifier to apply when equipped.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetAttributeSetModifier(const FAttributesSetModifier& inAttributeModifier)
    {
        GetEquippableDefinition()->SetAttributeSetModifier(inAttributeModifier);
    }

    /**
     * Returns the GameplayEffect class to be applied when the item is equipped.
     * @return A subclass of UGameplayEffect.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    TSubclassOf<UGameplayEffect> GetGEAttributeModifier() const { return GetEquippableDefinition()->GetGEAttributeModifier(); }

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFEquippableItem* GetEquippableDefinition() const
    {
        return Cast<UACFEquippableItem>(GetItemDefinition());
    }


};
