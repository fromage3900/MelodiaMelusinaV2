// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actors/ACFCharacter.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFTypes.h"

#include "ACFRagdollComponent.generated.h"

struct FACFDamageEvent;

// Delegate broadcasted when the ragdoll state changes (entered or exited)
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRagdollStateChanged, bool, bIsInRagdoll);

/**
 * UACFRagdollComponent
 *
 * Component responsible for handling full-body ragdoll simulation on  characters.
 * Allows triggering ragdoll via impulse or damage, and automatically recovers with get-up animations.
 * Supports both physics-based and kinematic characters
 *
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFRagdollComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFRagdollComponent();

public:
    /**
     * Triggers ragdoll based on a damage event.
     * @param damageEvent The damage data causing ragdoll.
     * @param RagdollDuration Duration before recovery. If < 0, you should manually call RecoverFrom Ragdoll
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void GoRagdollFromDamage(const FACFDamageEvent& damageEvent, float RagdollDuration = -1.f);

    /**
     * Applies a ragdoll impulse and enables physics simulation.
     * @param impulse The impulse to apply to the skeletal mesh.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void GoRagdoll(const FRagdollImpulse& impulse);

    /**
     * Applies a ragdoll impulse and recovers automatically after duration.
     * @param impulse The impulse to apply.
     * @param ragdollDuration Time to remain ragdolled.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void GoRagdollForDuration(const FRagdollImpulse& impulse, float ragdollDuration = -1.f);

    /**
     * Manually forces the character to recover from ragdoll.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void RecoverFromRagdoll();

    /**
     * Checks if the character is currently in ragdoll state.
     * @return True if ragdolled.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool IsInRagDoll() const { return bIsRagdoll; }

    /**
     * Determines if the character is facing up while ragdolled.
     * @return True if facing upward.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsFaceUp() const;

    /**
     * Called when the ragdoll state changes (start/end).
     */
    UPROPERTY(BlueprintAssignable)
    FOnRagdollStateChanged OnRagdollStateChanged;

    // Updates the owner's location based on the ragdoll pelvis position
    void UpdateOwnerLocation();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    /** Enables debug mode to test ragdoll triggering on hit. */
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bTestRagdollOnHit = true;

    /** Minimum impulse required to trigger ragdoll. */
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bTestRagdollOnHit), Category = ACF)
    float ImpulseResistance = 850.f;

    /** Duration after which ragdoll will automatically recover. */
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    float DefaultRagdollDuration = 5.f;

    /*If character owner is not kinematic, after the ragdoll ends it needs to be reattached
    to the actual capsule. Just check if your physics asset has it roots to set as kinematic*/
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bIsKinematic = true;

    /** Name of the pelvis bone used to anchor ragdoll physics. */
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FName PelvisBone = "Pelvis";

    /** Get-up action tag used for state transitions. */
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FGameplayTag GetUpAction;

    /** Collision channel assigned while ragdolled. */
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    TEnumAsByte<ECollisionChannel> RagdollChannel;

private:
    UFUNCTION()
    void TerminateRagdoll();

    FTransform beforeRagdollTransform;

    bool bIsRagdoll = false;

    TObjectPtr<USkeletalMeshComponent> GetMesh() const
    {
        return characterOwner ? characterOwner->GetMesh() : nullptr;
    }

    TObjectPtr<UCapsuleComponent> GetCapsuleComponent() const
    {
        return characterOwner ? characterOwner->GetCapsuleComponent() : nullptr;
    }

    TObjectPtr<AACFCharacter> characterOwner;

    UFUNCTION()
    void HandleDamageReceived(const FACFDamageEvent& damageEvent);

    void SetIsRagdoll(bool inIsRagdoll);

    ECollisionChannel oldChannel;
};
