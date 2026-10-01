// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actions/ACFActionAbility.h"

#include "ACFUseItemAction.generated.h"


/**
 * Ability that attempts to use an item from a specific item slot.
 * Can optionally equip offhand weapons, ammo, and activate hand IK constraints.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFUseItemAction : public UACFActionAbility {
    GENERATED_BODY()

public:
    UACFUseItemAction();

protected:
    // Gameplay tag identifying the item slot from which to use the item
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    FGameplayTag ItemSlot;

    // If true, the item will still be used even if the action was interrupted
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bShouldUseIfInterrupted = false;

    // If true, the system will try to equip an offhand item before use
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bTryToEquipOffhand = false;

    // If true, the system will attempt to equip required ammo before use
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bTryToEquipAmmo = true;

    // If true, will check if hands IK constraints are valid before using the item
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bCheckHandsIK = true;

    // Slot to equip the offhand item from, used only if bTryToEquipOffhand is true
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bTryToEquipOffhand"), Category = ACF)
    FGameplayTag OffHandSlot;

    bool bSuccess = false;

    // Returns the item slot to be used; can be overridden in Blueprint or C++
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    FGameplayTag GetItemSlot() const;
  
    // Returns the offhand slot to be used; can be overridden in Blueprint or C++
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    FGameplayTag GetOffHandSlot() const;

    /* Parent Overrides*/
    virtual void OnNotablePointReached_Implementation() override;

    virtual void OnActionEnded_Implementation() override;

    virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, 
        const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData) override;

	virtual void EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, 
		const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled) override;

    virtual bool CanActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayTagContainer* SourceTags /* = nullptr */, const FGameplayTagContainer* TargetTags /* = nullptr */, OUT FGameplayTagContainer* OptionalRelevantTags /* = nullptr */) const override;
    /* End Overrides*/
private:
    void UseItem();
};
