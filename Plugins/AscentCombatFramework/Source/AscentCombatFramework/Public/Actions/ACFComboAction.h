// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actions/ACFActionAbility.h"
#include "CoreMinimal.h"

#include "ACFComboAction.generated.h"

/**
 * Base class for all combo-based actions in the ACF system.
 * Handles combo counting, validation and combo input triggering.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFComboAction : public UACFActionAbility {
    GENERATED_BODY()

public:
    UACFComboAction();

    /**
     * Returns the combo step for the CURRENT activation, taken from the payload carried with
     * the (predicted) activation. Identical on client and server, so no replication is needed.
     * @return The combo step index of this activation.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    int32 GetComboCounter() const
    {
        return StoredPayload.ComboCounter;
    }

    /**
     * Returns whether the combo was successfully executed.
     * @return True if the combo is successful, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool IsSuccessfulCombo() const { return bSuccesfulCombo; }

    /**
     * Resets the combo counter associated with this action tag.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ResetComboCounter();

    /**
     * Forces the combo counter to a specific value.
     * @param val The new value to assign to the combo counter.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ForceComboCounter(int32 val)
    {
        GetACFAbilityComponent()->SetComboCounter(GetTriggeringTag(), val);
    }

    /**
     * Sends an input to advance the combo (e.g. player presses attack again).
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SendComboInput();

    /**
     * Handles late-arriving combo input when the ability has already ended (network lag recovery).
     * Called by the ability system when a StoreAbilityInBuffer RPC arrives after the ability ended.
     */
    virtual void OnBufferedInputReceived(const FGameplayTag& inputTag) override;

protected:
    virtual void PreActivate(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo,
        FOnGameplayAbilityEnded::FDelegate* OnGameplayAbilityEndedDelegate = nullptr, const FGameplayEventData* TriggerEventData = nullptr) override;

    virtual void OnActionStarted_Implementation() override;

    virtual FName GetMontageSectionName_Implementation() override;

    virtual void EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled) override;

    virtual void OnActionEnded_Implementation() override;

    virtual void OnGameplayEventReceived_Implementation(const FGameplayTag eventTag);

    UPROPERTY()
    bool bSuccesfulCombo = false;
};
