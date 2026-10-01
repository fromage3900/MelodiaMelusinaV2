// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFSustainedAction.h"
#include "Actions/ACFActionAbility.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Kismet/GameplayStatics.h"

UACFSustainedAction::UACFSustainedAction()
{
    bBindActionToAnimation = false;
    bAutoCommit = false;
    ReleaseActionPriority = EActionPriority::EHigh;
}

void UACFSustainedAction::ReleaseAction()
{
    if (ActionState == ESustainedActionState::EStarted) {
        const float secondsHeld = GetActionElapsedTime();
        ActionState = ESustainedActionState::EReleased;
        EndAbility(CurrentSpecHandle, CurrentActorInfo, CurrentActivationInfo, true, false);
        if (GetACFAbilityComponent()) {
            FACFAbilityPayload Payload;
            Payload.bIsValid = true;
            Payload.FloatPayload = secondsHeld;
            GetACFAbilityComponent()->TriggerActionWithPayload(ReleaseActionTag, Payload, ReleaseActionPriority, false);
        }
    }
}


float UACFSustainedAction::GetActionElapsedTime() const
{
    const float time = UGameplayStatics::GetRealTimeSeconds(CharacterOwner);
    return time - startTime;
}

void UACFSustainedAction::Internal_OnActivated(class UACFAbilitySystemComponent* actionmanger, class UAnimMontage* inAnimMontage)
{
    startTime = UGameplayStatics::GetRealTimeSeconds(actionmanger);
    Super::Internal_OnActivated(actionmanger, inAnimMontage);
}

void UACFSustainedAction::Internal_OnDeactivated()
{
    Super::Internal_OnDeactivated();
}

void UACFSustainedAction::ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData)
{
    Super::ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData);
    ActionState = ESustainedActionState::EStarted;
}

void UACFSustainedAction::EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled)
{

    Super::EndAbility(Handle, ActorInfo, ActivationInfo, bReplicateEndAbility, bWasCancelled);
    ActionState = ESustainedActionState::ENotStarted;
}
