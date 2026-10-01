// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ItemActors/ACFEquippableActor.h"
#include "Items/ACFWeapon.h"

#include "ACFWeaponActor.generated.h"

class UACFWeapon;

/**
 *
 */
UCLASS()
class INVENTORYSYSTEM_API AACFWeaponActor : public AACFEquippableActor {
    GENERATED_BODY()

public:
    AACFWeaponActor();
    /**
     * Returns the skeletal mesh component used by this weapon.
     *
     * @return The weapon's mesh component.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    FORCEINLINE class USkeletalMeshComponent* GetMeshComponent() const { return Mesh; };

    /**
     * Returns the world position of the left-hand IK handle.
     *
     * @return The world location of the left-hand IK component.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FVector GetLeftHandleIKPosition() const { return LeftHandleIKPos->GetComponentLocation(); }

    /**
     * Plays a weapon-specific animation associated with the given gameplay tag.
     *
     * @param weaponAnim The tag identifying the weapon animation to play.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void PlayWeaponAnim(const FGameplayTag& weaponAnim);

    /**
     * Returns the handle type used by this weapon (e.g., OneHanded, TwoHanded).
     *
     * @return The handle type enum of the weapon.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE EHandleType GetHandleType() const { return GetWeaponDefinition() ? GetWeaponDefinition()->GetHandleType() : EHandleType::OneHanded; }

    /**
     * Returns the gameplay tag representing the type of weapon (e.g., Sword, Bow).
     *
     * @return The weapon type gameplay tag.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetWeaponType() const { return GetWeaponDefinition() ? GetWeaponDefinition()->GetWeaponType() : FGameplayTag(); }

    /**
     * Returns the gameplay tag of the moveset associated with this weapon.
     *
     * @return The moveset tag used when this weapon is equipped.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetAssociatedMovesetTag() const { return GetWeaponDefinition() ? GetWeaponDefinition()->GetAssociatedMovesetTag() : FGameplayTag(); }

    /**
     * Returns the gameplay tag for the action set associated with the moveset.
     *
     * @return The tag defining the available actions for this moveset.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetAssociatedMovesetActionsTag() const { return GetWeaponDefinition() ? GetWeaponDefinition()->GetAssociatedMovesetActionsTag() : FGameplayTag(); }

    /**
     * Returns the gameplay tag for the overlay (animation layer) associated with the moveset.
     *
     * @return The overlay tag used for animation blending.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetAssociatedMovesetOverlayTag() const { return GetWeaponDefinition() ? GetWeaponDefinition()->GetAssociatedMovesetOverlayTag() : FGameplayTag(); }

    /**
     * Returns the name of the socket where this weapon is attached when stored on the body.
     *
     * @return The socket name used for holstered state.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FName GetOnBodySocketName() const { return GetWeaponDefinition() ? GetWeaponDefinition()->GetOnBodySocketName() : NAME_None; }

    /**
     * Returns the name of the socket where this weapon is attached when equipped in hands.
     *
     * @return The socket name used for the equipped state.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FName GetEquippedSocketName() const { return GetWeaponDefinition() ? GetWeaponDefinition()->GetEquippedSocketName() : NAME_None; }

    /**
     * Checks whether this weapon overrides the main hand's default moveset.
     *
     * @return True if it overrides the default moveset, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool OverridesMainHandMoveset() const { return GetWeaponDefinition() ? GetWeaponDefinition()->OverridesMainHandMoveset() : false; }

    /**
     * Checks whether this weapon overrides the main hand's animation overlay.
     *
     * @return True if it overrides the default overlay, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool OverridesMainHandOverlay() const { return GetWeaponDefinition() ? GetWeaponDefinition()->OverridesMainHandOverlay() : false; }

    /**
     * Checks whether this weapon overrides the main hand's moveset actions.
     *
     * @return True if it overrides the default moveset actions, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool OverridesMainHandMovesetActions() const { return GetWeaponDefinition() ? GetWeaponDefinition()->OverridesMainHandMovesetActions() : false; }

    /**
     * Checks whether this weapon uses a custom left-hand IK position.
     *
     * @return True if left-hand IK is used, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool IsUsingLeftHandIK() const { return GetWeaponDefinition() ? GetWeaponDefinition()->IsUsingLeftHandIK() : false; }

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFWeapon* GetWeaponDefinition() const;

    virtual void InitItemActor(APawn* inOwner, UACFItem* inItemDefinition) override;

protected:
    /**
     * Called when the weapon is unsheathed.
     * Override this in Blueprint or C++ to implement unsheathe behavior.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnWeaponUnsheathed();

    /**
     * Called when the weapon is sheathed.
     * Override this in Blueprint or C++ to implement sheathe behavior.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnWeaponSheathed();

    /**
     * Called when the weapon is equipped.
     * Override this in Blueprint or C++ to implement Equip behavior.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnEquipped();

    /**
     * Called when the weapon is Unequipped.
     * Override this in Blueprint or C++ to implement Unequipped behavior.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnUnequipped();

    /** Scene component representing the main handle position of the weapon. */
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "ACF|Weapon")
    TObjectPtr<class USceneComponent> HandlePos;

    /** Scene component used for left-hand IK positioning. */
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "ACF|Weapon")
    TObjectPtr<class USceneComponent> LeftHandleIKPos;

    /** Collision manager component used for weapon hit detection. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACMCollisionManagerComponent> CollisionComp;

    /*The skeletalMesh used by this weapon*/
    UPROPERTY(BlueprintReadWrite, VisibleAnywhere, Category = ACF)
    TObjectPtr<class USkeletalMeshComponent> Mesh;

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type reason) override;
    friend class UACFEquipmentComponent;

private:
    UFUNCTION()
    void Internal_OnWeaponUnsheathed();

    UFUNCTION()
    void Internal_OnWeaponSheathed();

    UFUNCTION()
    void OnAssetLoaded();

    FActiveGameplayEffectHandle UnsheatedModifierHandle;

    void AlignWeapon();
};
