// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFMountActionAbility.h"
#include "ACFMountableComponent.h"
#include "ACFRiderComponent.h"
#include "Logging.h"
#include <GameFramework/Character.h>

UACFMountActionAbility::UACFMountActionAbility()
{
    // Motion-warped by default: the rider smoothly approaches the mount socket.
    // Override per-instance in Blueprints when a different reproduction type is needed.
    ActionConfig.MontageReproductionType = EMontageReproductionType::EMotionWarped;
    ActionConfig.WarpInfo.SyncPoint      = FName("MountPoint");

    // Mount actions are player-driven; no BT to pause.
    ActionConfig.bStopBehavioralThree = false;
}

// ---------------------------------------------------------------------------
// UACFGameplayAbility interface
// ---------------------------------------------------------------------------

bool UACFMountActionAbility::CanActivateAbility(
    const FGameplayAbilitySpecHandle Handle,
    const FGameplayAbilityActorInfo* ActorInfo,
    const FGameplayTagContainer* SourceTags,
    const FGameplayTagContainer* TargetTags,
    OUT FGameplayTagContainer* OptionalRelevantTags) const
{
    if (!Super::CanActivateAbility(Handle, ActorInfo, SourceTags, TargetTags, OptionalRelevantTags))
    {
        return false;
    }

    // Require a valid mount pawn in the payload before activating.
    const UACFMountableComponent* MountComp = GetTargetMountableComponent();
    if (!MountComp)
    {
        UE_LOG(ACFLog, Warning,
            TEXT("ACFMountActionAbility: CanActivate failed — no UACFMountableComponent "
                 "found on StoredPayload.TargetActor. Pass the mount pawn as TargetActor."));
        return false;
    }

    if (!MountComp->CanBeMounted())
    {
        return false;
    }

    const UACFRiderComponent* RiderComp = GetRiderComponent();
    if (RiderComp && RiderComp->IsRiding())
    {
        return false;
    }

    return true;
}

// ---------------------------------------------------------------------------
// UACFActionAbility interface
// ---------------------------------------------------------------------------

void UACFMountActionAbility::OnActionEnded_Implementation()
{
    Super::OnActionEnded_Implementation();

    // OnActionEnded is called server-side from Internal_OnDeactivated.
    // Calling StartMount here triggers the full mount sequence:
    //   1. Attach rider to mount socket (camera locked to avoid snap)
    //   2. Smooth camera blend: frozen rider view → live mount camera
    //   3. Deferred possession swap after the blend
    UACFMountableComponent* MountComp = GetTargetMountableComponent();
    UACFRiderComponent*     RiderComp = GetRiderComponent();

    if (MountComp && RiderComp)
    {
        RiderComp->StartMount(MountComp);
    }
    else
    {
        UE_LOG(ACFLog, Warning,
            TEXT("ACFMountActionAbility: OnActionEnded — missing MountComp or RiderComp."));
    }
}

// ---------------------------------------------------------------------------
// UACFGameplayAbility interface – warp
// ---------------------------------------------------------------------------

FTransform UACFMountActionAbility::GetWarpTransform_Implementation()
{
    if (const UACFMountableComponent* MountComp = GetTargetMountableComponent())
    {
        // Warp toward the mount socket so the motion-warping window in the montage
        // brings the rider close to the saddle before the attach snap.
        return MountComp->GetMountPointTransform();
    }
    return Super::GetWarpTransform_Implementation();
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

UACFMountableComponent* UACFMountActionAbility::GetTargetMountableComponent() const
{
    if (!StoredPayload.bIsValid || !IsValid(StoredPayload.TargetActor))
    {
        return nullptr;
    }
    return StoredPayload.TargetActor->FindComponentByClass<UACFMountableComponent>();
}

UACFRiderComponent* UACFMountActionAbility::GetRiderComponent() const
{
    const ACharacter* Character = GetCharacterOwner();
    if (!Character)
    {
        return nullptr;
    }
    return Character->FindComponentByClass<UACFRiderComponent>();
}
