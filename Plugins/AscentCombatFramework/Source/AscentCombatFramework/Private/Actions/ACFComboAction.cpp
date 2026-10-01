// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFComboAction.h"
#include "Actions/ACFActionAbility.h"
#include <Abilities/Tasks/AbilityTask_WaitGameplayEvent.h>
#include <GameplayTask.h>

void UACFComboAction::PreActivate(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo,
    FOnGameplayAbilityEnded::FDelegate* OnGameplayAbilityEndedDelegate, const FGameplayEventData* TriggerEventData)
{
    Super::PreActivate(Handle, ActorInfo, ActivationInfo, OnGameplayAbilityEndedDelegate, TriggerEventData);

    // Runs on BOTH client and server at every activation (OnActionStarted is authority-only),
    // so the locally-predicted client can advance the combo on each step too.
    bSuccesfulCombo = false;
}

void UACFComboAction::OnActionStarted_Implementation()
{
    bSuccesfulCombo = false;

    Super::OnActionStarted_Implementation();
}

FName UACFComboAction::GetMontageSectionName_Implementation()
{
    if (animMontage) {
        // The combo step for this activation is the counter requested by the client and
        // carried in the payload. It is identical on client and server (predicted activation),
        // so both pick the same montage section without replicating the counter.
        const int32 currentCount = GetComboCounter();
        const FName SectionName = animMontage->GetSectionName(currentCount);

        if (SectionName != NAME_None) {
            return SectionName;
        } else {
            return animMontage->GetSectionName(0);
        }
    }
    return NAME_None;
}

void UACFComboAction::OnActionEnded_Implementation()
{
    Super::OnActionEnded_Implementation();

    if (!bSuccesfulCombo) {
        ResetComboCounter();
    }
}

void UACFComboAction::EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled)
{
    if (!HasAuthority(&ActivationInfo) && !bSuccesfulCombo) {
        ResetComboCounter();
    }

    Super::EndAbility(Handle, ActorInfo, ActivationInfo, bReplicateEndAbility, bWasCancelled);
}

void UACFComboAction::ResetComboCounter()
{
    GetACFAbilityComponent()->ResetComboCount(GetTriggeringTag());
    bSuccesfulCombo = false;
}

void UACFComboAction::SendComboInput()
{
    if (bSuccesfulCombo) {
        // we can increment the counter only once per attack
        return;
    }
    if (!animMontage) {
        return;
    }

    // Current step comes from this activation's payload; compute the NEXT step and stash it
    // locally so EvaluateBuffer ships it in the next predicted activation's payload.
    int32 nextCount = GetComboCounter() + 1;
    if (nextCount >= animMontage->CompositeSections.Num()) {
        nextCount = 0;
    }
    GetACFAbilityComponent()->SetComboCounter(GetTriggeringTag(), nextCount);
    bSuccesfulCombo = true;
}

void UACFComboAction::OnGameplayEventReceived_Implementation(const FGameplayTag eventTag)
{
    if (eventTag.MatchesTag(GetTriggeringTag())) {
        SendComboInput();
        bSuccesfulCombo = true;

        // Handle the race where the combo input arrives AFTER the ExitNotify already fired
        // (Scenario B). If the ExitNotify set bExitRequested=true and lowered priority to -1
        // but didn't exit because there was no stored action yet, exit now that the combo
        // input arrived, avoiding a visible delay until montage BlendOut.
        if (bExitRequested && GetACFAbilityComponent()->HasStoredActions()) {
            ExitAction(false);
        }
    }
}

void UACFComboAction::OnBufferedInputReceived(const FGameplayTag& inputTag)
{
    // Combo input arrived AFTER the ability already ended (Scenario C - high lag).
    // Advance the counter so the next predicted activation carries the correct step
    // in its payload (EvaluateBuffer will ship it).
    if (inputTag.MatchesTag(GetTriggeringTag())) {
        SendComboInput();
    }
}

UACFComboAction::UACFComboAction()
{
    NetExecutionPolicy = EGameplayAbilityNetExecutionPolicy::LocalPredicted;
    bAllowPhysicalRotation = true;
}
