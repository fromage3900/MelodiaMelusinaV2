// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "Actions/ACFSustainedChooserAction.h"
#include "Animation/AnimMontage.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "GameFramework/Character.h"
#include "Logging.h"
#include <Engine/World.h>
#include <Animation/AnimInstance.h>
#include <Components/SkeletalMeshComponent.h>

UACFSustainedChooserAction::UACFSustainedChooserAction()
{
    // Chooser functionality inherited from UACFChooserAction
    // Just set sustained-specific defaults
    ReleaseActionPriority = EActionPriority::EHigh;
}

void UACFSustainedChooserAction::OnActionStarted_Implementation()
{
    Super::OnActionStarted_Implementation();

    // Start tracking elapsed time
    startTime = GetWorld()->GetTimeSeconds();
    ActionState = ESustainedActionState::EStarted;

    UE_LOG(ACFLog, Verbose, TEXT("[SustainedChooserAction] Action started, tracking time"));
}

void UACFSustainedChooserAction::OnActionEnded_Implementation()
{
    ActionState = ESustainedActionState::ENotStarted;

    Super::OnActionEnded_Implementation();
}

void UACFSustainedChooserAction::ReleaseAction()
{
    if (ActionState == ESustainedActionState::EStarted)
    {
        const float secondsHeld = GetActionElapsedTime();
        ActionState = ESustainedActionState::EReleased;

        // Trigger another action via tag (like original UACFSustainedAction)
        if (ReleaseActionTag.IsValid() && GetACFAbilityComponent())
        {
            EndAbility(CurrentSpecHandle, CurrentActorInfo, CurrentActivationInfo, true, false);
            FACFAbilityPayload Payload;
            Payload.bIsValid = true;
            Payload.FloatPayload = secondsHeld;
            GetACFAbilityComponent()->TriggerActionWithPayload(ReleaseActionTag, Payload, ReleaseActionPriority, false);
        }
    }
}

void UACFSustainedChooserAction::PlayActionSection(FName sectionName)
{
    // Always jump section locally for instant response
    if (ACharacter* Owner = GetCharacterOwner())
    {
        if (UAnimInstance* AnimInstance = Owner->GetMesh()->GetAnimInstance())
        {
            if (UAnimMontage* ActiveMontage = AnimInstance->GetCurrentActiveMontage())
            {
                AnimInstance->Montage_JumpToSection(sectionName, ActiveMontage);
            }
        }
    }

    // Also send to server to ensure sync
    if (GetCharacterOwner() && GetCharacterOwner()->GetLocalRole() < ROLE_Authority)
    {
        Server_PlayActionSection(sectionName);
    }
}

void UACFSustainedChooserAction::Server_PlayActionSection_Implementation(FName sectionName)
{
    if (ACharacter* Owner = GetCharacterOwner())
    {
        if (UAnimInstance* AnimInstance = Owner->GetMesh()->GetAnimInstance())
        {
            if (UAnimMontage* ActiveMontage = AnimInstance->GetCurrentActiveMontage())
            {
                AnimInstance->Montage_JumpToSection(sectionName, ActiveMontage);
            }
        }
    }
}

float UACFSustainedChooserAction::GetActionElapsedTime() const
{
    if (ActionState == ESustainedActionState::EStarted || ActionState == ESustainedActionState::EReleased)
    {
        return GetWorld()->GetTimeSeconds() - startTime;
    }
    return 0.f;
}
