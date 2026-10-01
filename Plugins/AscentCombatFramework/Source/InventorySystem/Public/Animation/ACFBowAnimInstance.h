// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFItemTypes.h"
#include "Animation/AnimInstance.h"
#include "CoreMinimal.h"

#include "ACFBowAnimInstance.generated.h"

class UACFWeapon;
class ACharacter;
class AACFWeaponActor;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBowStateChanged, const EBowState&, newState);

/**
 * Animation instance class for bow weapons.
 * Manages bow state (idle, pulled, released) and exposes events
 * for state changes to drive both gameplay and animation logic.
 */
UCLASS()
class INVENTORYSYSTEM_API UACFBowAnimInstance : public UAnimInstance {
    GENERATED_BODY()

public:
    /** Default constructor */
    UACFBowAnimInstance();

    /**
     * Gets the current bow state.
     * @return Current EBowState.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    EBowState GetBowState() const { return bowState; }

    /**
     * Sets the bow state.
     * @param val New state to assign.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetBowState(EBowState val);

    /** Called to release the bow string */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ReleaseString();

    /** Called to pull the bow string */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void PullString();

    /** Delegate broadcast when the bow state changes */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnBowStateChanged OnBowStateChanged;

protected:
    /**
     * Gets the weapon actor that owns this anim instance.
     * @return AACFWeaponActor pointer or nullptr if not valid.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    AACFWeaponActor* GetWeaponOwner() const
    {
        return weaponOwner;
    }

    /**
     * Gets the character that owns this bow item.
     * @return Owning ACharacter pointer or nullptr if not valid.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    AActor* GetItemOwner() const;

    virtual void NativeThreadSafeUpdateAnimation(float DeltaSeconds) override;

    virtual void NativeInitializeAnimation() override;

    UPROPERTY(EditAnywhere, Category = ACF)
    FName PullSocket;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    TObjectPtr<AACFWeaponActor> weaponOwner;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    EBowState bowState;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    float Alpha;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    TObjectPtr<AActor> itemOwner;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    TObjectPtr<USkeletalMeshComponent> mainMesh;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    FVector SocketLocation;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACF)
    float InterpSpeed;

    void GatherOwner();

};
