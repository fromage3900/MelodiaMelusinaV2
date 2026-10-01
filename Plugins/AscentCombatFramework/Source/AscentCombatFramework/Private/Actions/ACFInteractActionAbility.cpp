// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFInteractActionAbility.h"
#include "Components/ACFInteractableComponent.h"
#include "Components/ACFInteractionComponent.h"
#include "CCMCameraFunctionLibrary.h"
#include "GameFramework/Character.h"
#include "Interfaces/ACFInteractableInterface.h"

UACFInteractActionAbility::UACFInteractActionAbility()
{
    // Motion-warped by default so the pawn flows to the warp point in the montage.
    // Override per-instance in Blueprints when a different reproduction type is needed.
    ActionConfig.MontageReproductionType = EMontageReproductionType::EMotionWarped;
    ActionConfig.WarpInfo.SyncPoint = FName("Interactable");
}

FTransform UACFInteractActionAbility::GetWarpTransform_Implementation()
{
    if (const UACFInteractableComponent* Comp = GetCurrentInteractableComponent())
    {
        return Comp->GetComponentTransform();
    }
    return Super::GetWarpTransform_Implementation();
}

UAnimMontage* UACFInteractActionAbility::GetMontage_Implementation() const
{
    if (const UACFInteractableComponent* Comp = GetCurrentInteractableComponent())
    {
        if (UAnimMontage* Override = Comp->GetInteractionMontageOverride())
        {
            return Override;
        }
    }
    return Super::GetMontage_Implementation();
}

void UACFInteractActionAbility::ClientsOnActionStarted_Implementation()
{
    Super::ClientsOnActionStarted_Implementation();

    if (const UACFInteractableComponent* Comp = GetCurrentInteractableComponent())
    {
        const FName CameraEventName = Comp->GetInteractionCameraEventName();
        if (CameraEventName != NAME_None)
        {
            UCCMCameraFunctionLibrary::TriggerCameraEvent(this, CameraEventName);
        }

        if (Comp->ShouldLockCameraOnOwner())
        {
            UCCMCameraFunctionLibrary::LockCameraOnActor(this, Comp->GetOwner(),
                Comp->GetLockCameraType(), Comp->GetLockCameraStrength());
        }
    }
}

void UACFInteractActionAbility::ClientsOnNotablePointReached_Implementation()
{
    Super::ClientsOnNotablePointReached_Implementation();

    if (const UACFInteractableComponent* Comp = GetCurrentInteractableComponent())
    {
        const FName CameraEventName = Comp->GetInteractionCameraEventName();
        if (CameraEventName != NAME_None)
        {
            UCCMCameraFunctionLibrary::StopCameraEvent(this, CameraEventName);
        }

        if (Comp->ShouldLockCameraOnOwner())
        {
            UCCMCameraFunctionLibrary::StopLockingCameraOnActor(this);
        }
    }
}

void UACFInteractActionAbility::OnNotablePointReached_Implementation()
{
    Super::OnNotablePointReached_Implementation();

    if (ACharacter* Character = GetCharacterOwner())
    {
        if (UACFInteractionComponent* InteractionComp = Character->FindComponentByClass<UACFInteractionComponent>())
        {
            InteractionComp->OnInteracted();
        }
    }
}

void UACFInteractActionAbility::EndAbility(const FGameplayAbilitySpecHandle Handle,
    const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo,
    bool bReplicateEndAbility, bool bWasCancelled)
{
    if (HasAuthority(&ActivationInfo))
    {
        if (ACharacter* Character = GetCharacterOwner())
        {
            if (UACFInteractionComponent* InteractionComp = Character->FindComponentByClass<UACFInteractionComponent>())
            {
                InteractionComp->EndInteraction();
            }
        }
    }

    Super::EndAbility(Handle, ActorInfo, ActivationInfo, bReplicateEndAbility, bWasCancelled);
}

bool UACFInteractActionAbility::CanActivateAbility(const FGameplayAbilitySpecHandle Handle,
    const FGameplayAbilityActorInfo* ActorInfo, const FGameplayTagContainer* SourceTags,
    const FGameplayTagContainer* TargetTags, FGameplayTagContainer* OptionalRelevantTags) const
{
    if (!Super::CanActivateAbility(Handle, ActorInfo, SourceTags, TargetTags, OptionalRelevantTags))
    {
        return false;
    }

    APawn* Pawn = ActorInfo ? Cast<APawn>(ActorInfo->AvatarActor.Get()) : nullptr;
    if (!Pawn)
    {
        return false;
    }

    const UACFInteractionComponent* InteractionComp = Pawn->FindComponentByClass<UACFInteractionComponent>();
    AActor* InteractableActor = InteractionComp ? InteractionComp->GetCurrentBestInteractableActor() : nullptr;
    if (!IsValid(InteractableActor) ||
        !InteractableActor->GetClass()->ImplementsInterface(UACFInteractableInterface::StaticClass()))
    {
        return false;
    }

    if (!IACFInteractableInterface::Execute_CanBeInteracted(InteractableActor, Pawn))
    {
        return false;
    }

    if (const UACFInteractableComponent* InteractableComp = InteractableActor->FindComponentByClass<UACFInteractableComponent>())
    {
        return InteractableComp->CanBeInteracted(Pawn);
    }

    return true;
}

UACFInteractableComponent* UACFInteractActionAbility::GetCurrentInteractableComponent() const
{
    const ACharacter* Character = GetCharacterOwner();
    if (!Character)
    {
        return nullptr;
    }

    const UACFInteractionComponent* InteractionComp =
        Character->FindComponentByClass<UACFInteractionComponent>();
    if (!InteractionComp)
    {
        return nullptr;
    }

    AActor* InteractableActor = InteractionComp->GetCurrentInteractingActor();
    if (!IsValid(InteractableActor))
    {
        InteractableActor = InteractionComp->GetCurrentBestInteractableActor();
    }

    if (!IsValid(InteractableActor))
    {
        return nullptr;
    }

    return InteractableActor->FindComponentByClass<UACFInteractableComponent>();
}
