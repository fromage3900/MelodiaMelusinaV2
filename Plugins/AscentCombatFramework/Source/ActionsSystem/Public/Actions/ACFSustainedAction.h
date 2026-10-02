// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actions/ACFActionAbility.h"
#include "CoreMinimal.h"

#include "ACFSustainedAction.generated.h"

/**
 *
 */
UCLASS()
class ACTIONSSYSTEM_API UACFSustainedAction : public UACFActionAbility {
    GENERATED_BODY()

public:
    UACFSustainedAction();

    UFUNCTION(BlueprintCallable, Category = ACF)
    void ReleaseAction();

    UFUNCTION(BlueprintPure, Category = ACF)
    float GetActionElapsedTime() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    ESustainedActionState GetActionState() const
    {
        return ActionState;
    }

protected:
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FGameplayTag ReleaseActionTag;

    UPROPERTY(EditDefaultsOnly, Category = ACF)
    EActionPriority ReleaseActionPriority;

    /*Called when release action is triggered during the execution
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnActionReleased(float elapsedTimeSeconds);
    virtual void OnActionReleased_Implementation(float elapsedTimeSeconds);*/

    float startTime;

    UPROPERTY()
    ESustainedActionState ActionState;

    virtual void Internal_OnActivated(class UACFAbilitySystemComponent* actionmanger,
        class UAnimMontage* inAnimMontage) override;

    virtual void Internal_OnDeactivated() override;
    virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData) override;

    virtual void EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled) override;
};
