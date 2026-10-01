// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFComboAttackAction.h"
#include "ACFComboComponent.h"
#include "ARSStatisticsComponent.h"
#include "Graph/ACFComboGraph.h"
#include "Graph/ACFComboNode.h"
#include "Logging.h"

void UACFComboAttackAction::OnActionStarted_Implementation()
{
    if (Combo && GetCharacterOwner()) {
        comboComponent = GetCharacterOwner()->FindComponentByClass<UACFComboComponent>();
        if (comboComponent) {
            // Use the runtime instance (DuplicateObject), not the source asset
            if (UACFComboGraph* activeCombo = comboComponent->GetCurrentCombo()) {
                node = activeCombo->GetCurrentComboNode();
            }

            if (node) {
                UARSStatisticsComponent* statComp = GetCharacterOwner()->FindComponentByClass<UARSStatisticsComponent>();
                if (statComp) {
                    geHandle = statComp->AddAttributeSetModifier(node->GetComboNodeModifier());
                }
            }
        }
    }
    Super::OnActionStarted_Implementation();
}

void UACFComboAttackAction::OnActionEnded_Implementation()
{
    ProcessComboStepEnd();

    Super::OnActionEnded_Implementation();
}

UACFComboAttackAction::UACFComboAttackAction()
{
    bAutoOpenBuffer = true;
}

void UACFComboAttackAction::PreActivate(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, FOnGameplayAbilityEnded::FDelegate* OnGameplayAbilityEndedDelegate, const FGameplayEventData* TriggerEventData)
{
    Super::PreActivate(Handle, ActorInfo, ActivationInfo, OnGameplayAbilityEndedDelegate, TriggerEventData);
    bComboStepEndProcessed = false;
    if (Combo && GetCharacterOwner()) {
        comboComponent = GetCharacterOwner()->FindComponentByClass<UACFComboComponent>();
        if (comboComponent) {
            if (!comboComponent->IsExecutingCombo(Combo)) {
                comboComponent->StartCombo(Combo, GetActionTag());
            }
            comboComponent->ClearInputTag();
            // Use the runtime instance (DuplicateObject), not the source asset
            if (UACFComboGraph* activeCombo = comboComponent->GetCurrentCombo()) {
                node = activeCombo->GetCurrentComboNode();
            }

            if (!node || !IsValid(node) || !node->IsValidLowLevel()) {
                UE_LOG(ACFLog, Error, TEXT("Invalid Combo Transition in %s! Node: %s, Combo: %s"),
                    *GetNameSafe(this),
                    node ? *GetNameSafe(node) : TEXT("nullptr"),
                    *GetNameSafe(Combo));

                // First stop the combo to prevent recursion
                //This is a fallback, combo should stop at the end of the ability
                if (comboComponent && comboComponent->IsExecutingCombo(Combo)) {
                    comboComponent->StopCombo(Combo);
                }

                ExitAction();
                return;
            }
            if (bAutoOpenBuffer) {
                comboComponent->SetInputBufferOpened(true);
            }

            if (node) {
                // FString MontageName = node ? node->GetMontage()->GetName() : "None";
                SetAnimMontage(node->GetMontage());
            }
        }
    } else {
        ExitAction(true);
    }
}

void UACFComboAttackAction::EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled)
{
    // Use the runtime instance (DuplicateObject), not the source asset
    if (comboComponent) {
        if (UACFComboGraph* activeCombo = comboComponent->GetCurrentCombo()) {
            node = activeCombo->GetCurrentComboNode();
        }
    }
    if (node && comboComponent) {
        if (bAutoOpenBuffer) {
            comboComponent->SetInputBufferOpened(false);
        }
    }

    if (!HasAuthority(&ActivationInfo)) {
        ProcessComboStepEnd();
    }

    Super::EndAbility(Handle, ActorInfo, ActivationInfo, bReplicateEndAbility, bWasCancelled);
}

void UACFComboAttackAction::ProcessComboStepEnd()
{
    if (bComboStepEndProcessed) {
        return;
    }
    bComboStepEndProcessed = true;

    if (!comboComponent || !GetCharacterOwner()) {
        return;
    }

    if (!node) {
        if (UACFComboGraph* activeCombo = comboComponent->GetCurrentCombo()) {
            node = activeCombo->GetCurrentComboNode();
        }
    }

    if (!node) {
        return;
    }

    if (geHandle.IsValid()) {
        UARSStatisticsComponent* statComp = GetCharacterOwner()->FindComponentByClass<UARSStatisticsComponent>();
        if (statComp) {
            statComp->RemoveAttributeSetModifier(geHandle);
        }
        geHandle.Invalidate();
    }

    bSuccesfulCombo = comboComponent->HasPendingInput();
    UACFComboGraph* activeCombo = comboComponent->GetCurrentCombo();
    if (bSuccesfulCombo && activeCombo && activeCombo->PerformTransition(comboComponent->GetLastTagInput(), GetCharacterOwner())) {
        ACFAbilityComponent->StoreAbilityInBuffer(GetActionTag());
    } else {
        comboComponent->StopCombo(Combo);
        ACFAbilityComponent->StoreAbilityInBuffer(FGameplayTag());
    }
}
