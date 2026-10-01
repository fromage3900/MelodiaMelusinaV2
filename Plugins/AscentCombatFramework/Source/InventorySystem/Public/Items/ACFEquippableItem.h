// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFRPGTypes.h"
#include "ARSTypes.h"
#include "CoreMinimal.h"
#include "Items/ACFItem.h"
#include <ActiveGameplayEffectHandle.h>
#include <Components/SkeletalMeshComponent.h>
#include <GameplayEffect.h>
#include <GameplayEffectTypes.h>

#include "ACFEquippableItem.generated.h"

/**
 *
 */
class UACFEquipmentComponent;
class UGameplayEffect;
class UAbilitySystemComponent;
struct FActiveGameplayEffectHandle;

/**
 *  Base class for items that can be equipped by characters.
 */
UCLASS()
class INVENTORYSYSTEM_API UACFEquippableItem : public UACFItem {
	GENERATED_BODY()

public:
	/** Default constructor. */
	UACFEquippableItem();

	/**
	 * Returns the attribute modifier
	 * @return The attribute set modifier.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FAttributesSetModifier GetAttributeSetModifier() const
	{
		return AttributeModifier;
	}

	/**
	 * Sets the attribute modifier
	 * @param inAttributeModifier The modifier to apply when equipped.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetAttributeSetModifier(const FAttributesSetModifier& inAttributeModifier)
	{
		AttributeModifier = inAttributeModifier;
	}

	/**
	 * Returns the GameplayEffect class to be applied when the item is equipped.
	 * @return A subclass of UGameplayEffect.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	TSubclassOf<UGameplayEffect> GetGEAttributeModifier() const { return AttributeModifier.GameplayEffectModifier; }

	/**
	 * Called when the item is equipped.
	 * Can be overridden in Blueprint to define custom equip behavior.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnItemEquipped();

	/**
	 * Called when the item is unequipped.
	 * Can be overridden in Blueprint to define custom unequip behavior.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnItemUnEquipped();

	/**
	 * Checks if the item can be equipped.
	 * @param equipComp The equipment component attempting to equip this item.
	 * @return True if the item meets all conditions to be equipped.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	bool CanBeEquipped(UACFEquipmentComponent* equipComp);

	virtual void Internal_OnEquipped(class APawn* owner);
	virtual void Internal_OnUnEquipped();
	void RemoveModifierToOwner(const FActiveGameplayEffectHandle& inModifier);
	void AddModifierToOwner(const FAttributesSetModifier& inModifier);
	void RemoveCurrentModifierFromOwner();

protected:
	/** Attribute modifier used when GAS is disabled or with SetByCaller type. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Equippable")
	FAttributesSetModifier AttributeModifier;

private:
	FActiveGameplayEffectHandle ModifierHandle;
};
