// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Items/ACFEquippableItem.h"
#include "ACFItem.h"
#include <Engine/SkeletalMesh.h>
#include <UObject/SoftObjectPtr.h>

#include "ACFWeapon.generated.h"

class AACFWeaponActor;
class AACFItemActor;

/**
 * Container for the sound and particle effects associated with weapon attacks.
 */
USTRUCT(BlueprintType)
struct FWeaponEffects {
    GENERATED_BODY()

public:
    FWeaponEffects()
    {
        AttackSound = nullptr;
        AttackParticle = nullptr;
    }
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    class USoundBase* AttackSound;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    class UParticleSystem* AttackParticle;
};

/**
 * Base class for all weapons in ACF.
 */
UCLASS()
class INVENTORYSYSTEM_API UACFWeapon : public UACFEquippableItem {
    GENERATED_BODY()

public:
    UACFWeapon();

    /**
     * Returns the handle type used by this weapon (e.g., OneHanded, TwoHanded).
     *
     * @return The handle type enum of the weapon.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE EHandleType GetHandleType() const { return HandleType; }

    /**
     * Returns the gameplay tag representing the type of weapon (e.g., Sword, Bow).
     *
     * @return The weapon type gameplay tag.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetWeaponType() const { return WeaponType; }

    /**
     * Returns the gameplay tag of the moveset associated with this weapon.
     *
     * @return The moveset tag used when this weapon is equipped.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetAssociatedMovesetTag() const { return Moveset; }

    /**
     * Returns the gameplay tag for the action set associated with the moveset.
     *
     * @return The tag defining the available actions for this moveset.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetAssociatedMovesetActionsTag() const { return MovesetActions; }

    /**
     * Returns the gameplay tag for the overlay (animation layer) associated with the moveset.
     *
     * @return The overlay tag used for animation blending.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetAssociatedMovesetOverlayTag() const { return MovesetOverlay; }

    /**
     * Returns the name of the socket where this weapon is attached when stored on the body.
     *
     * @return The socket name used for holstered state.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FName GetOnBodySocketName() const { return OnBodySocketName; }

    /**
     * Returns the name of the socket where this weapon is attached when equipped in hands.
     *
     * @return The socket name used for the equipped state.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FName GetEquippedSocketName() const { return InHandsSocketName; }

    /**
     * Checks whether this weapon overrides the main hand's default moveset.
     *
     * @return True if it overrides the default moveset, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool OverridesMainHandMoveset() const { return bOverrideMainHandMoveset; }

    /**
     * Checks whether this weapon overrides the main hand's animation overlay.
     *
     * @return True if it overrides the default overlay, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool OverridesMainHandOverlay() const { return bOverrideMainHandOverlay; }

    /**
     * Checks whether this weapon overrides the main hand's moveset actions.
     *
     * @return True if it overrides the default moveset actions, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool OverridesMainHandMovesetActions() const { return bOverrideMainHandMovesetActions; }

    /**
     * Checks whether this weapon uses a custom left-hand IK position.
     *
     * @return True if left-hand IK is used, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool IsUsingLeftHandIK() const { return bUseLeftHandIKPosition; }

    /**
     * Sets the handle type of the weapon (e.g., OneHanded, TwoHanded).
     *
     * @param newType The new handle type to assign.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetHandleType(EHandleType newType) { HandleType = newType; }

    /**
     * Enables or disables the use of a custom left-hand IK position.
     *
     * @param newVal Set to true to use left-hand IK positioning.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetIsUsingLeftHandIK(bool newVal)
    {
        bUseLeftHandIKPosition = newVal;
    }

    /**
     * Sets the attribute modifier to be applied when the weapon is unsheathed.
     *
     * @param inAttributeModifier The attribute set modifier to apply.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetUnsheatedAttributeSetModifier(const FAttributesSetModifier& inAttributeModifier) { UnsheathedAttributeModifier = inAttributeModifier; }

    /**
     * Returns the attribute modifier applied when the weapon is unsheathed.
     *
     * @return The attribute modifier struct for unsheathed state.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FAttributesSetModifier GetUnsheatedAttributeSetModifier() const { return UnsheathedAttributeModifier; }

    /**
     * Returns the Gameplay Effect to apply when the weapon is unsheathed.
     *
     * @return The gameplay effect class used while the weapon is unsheathed.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    TSubclassOf<UGameplayEffect> GetUnsheatedGameplayEffect() const
    {
        return UnsheathedAttributeModifier.GameplayEffectModifier;
    }

    /**
     * Returns the TMap of possible weaponanimations.
     *
     * @return the TMap of possible weaponanimations.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    TMap<FGameplayTag, UAnimMontage*> GetWeaponAnimations() const { return WeaponAnimations; }

    /*The actor to be spawned when this item is used*/
    virtual TSubclassOf<AACFItemActor> GetItemActorClass_Implementation() const override;

    UFUNCTION(BlueprintPure, Category = ACF)
    FTransform GetAttachmentOffset() const { return AttachmentOffset; }
    
    void SetAttachmentOffset(FTransform val) { AttachmentOffset = val; }

    UFUNCTION(BlueprintPure, Category = ACF)
    TSoftObjectPtr<USkeletalMesh> GetWeaponMesh() const;

    void SetWeaponMesh(TSoftObjectPtr<USkeletalMesh> val) { WeaponMesh = val; }


protected:
    /** Defines the handle type (OneHanded, TwoHanded, OffHand). */
    UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACF|Weapon")
    EHandleType HandleType = EHandleType::OneHanded;

    // The Mesh to be used when this weapon is equipped
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Weapon")
    TSoftObjectPtr<USkeletalMesh> WeaponMesh; 

    // The soft reference to the item actor class to spawn
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Weapon")
    TSoftClassPtr<AACFWeaponActor> ItemActorClass;

    /** If true, overrides the main hand's moveset when equipped as off-hand. */
    UPROPERTY(BlueprintReadOnly, meta = (EditCondition = "HandleType == EHandleType::OffHand"), EditDefaultsOnly, Category = "ACF|Weapon")
    bool bOverrideMainHandMoveset = false;

    /** If true, overrides the main hand's moveset actions when equipped as off-hand. */
    UPROPERTY(BlueprintReadOnly, meta = (EditCondition = "HandleType == EHandleType::OffHand"), EditDefaultsOnly, Category = "ACF|Weapon")
    bool bOverrideMainHandMovesetActions = false;

    /** If true, overrides the main hand's animation overlay when equipped as off-hand. */
    UPROPERTY(BlueprintReadOnly, meta = (EditCondition = "HandleType == EHandleType::OffHand"), EditDefaultsOnly, Category = "ACF|Weapon")
    bool bOverrideMainHandOverlay = false;

    /** Enables use of left-hand IK position when using a two-handed weapon. */
    UPROPERTY(BlueprintReadOnly, meta = (EditCondition = "HandleType == EHandleType::TwoHanded"), EditDefaultsOnly, Category = "ACF|Weapon")
    bool bUseLeftHandIKPosition = false;

    /*Tag identifying the actual weapontype*/
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, meta = (Categories = "Item"), Category = "ACF|Weapon")
    FGameplayTag WeaponType;

    /*Once this weapon is equipped, the equipping character will try to switch to this moveset*/
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, meta = (Categories = "Moveset"), Category = "ACF|Weapon")
    FGameplayTag Moveset;

    /*Once this weapon is equipped, the equipping character will try to add this overlay*/
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, meta = (Categories = "Moveset"), Category = "ACF|Weapon")
    FGameplayTag MovesetOverlay;

    /*Once this weapon is equipped, those are the actions that can be triggered*/
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, meta = (Categories = "Moveset"), Category = "ACF|Weapon")
    FGameplayTag MovesetActions;

    /*Socket in which this weapon will be attached once it is equipped on the back of the character*/
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Weapon")
    FName OnBodySocketName;

    /*Socket in which this weapon will be attached once it is unsheathed*/
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Weapon")
    FName InHandsSocketName;

    /*Modifier applied once this item is equipped in hands*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Weapon")
    FAttributesSetModifier UnsheathedAttributeModifier;

    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Weapon")
    TMap<FGameplayTag, UAnimMontage*> WeaponAnimations;

    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Weapon")
    FTransform AttachmentOffset;

    /* OVERRIDES*/
    virtual void OnItemEquipped_Implementation() override;
    virtual void OnItemUnEquipped_Implementation() override;
    virtual bool CanBeEquipped_Implementation(class UACFEquipmentComponent* equipComp) override;
};
