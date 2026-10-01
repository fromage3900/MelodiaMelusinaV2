// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFDismountActionAbility.h"
#include "ACFMountableComponent.h"
#include "ACFMountPointComponent.h"
#include "ACFRiderComponent.h"
#include "Logging.h"
#include <GameFramework/Character.h>

UACFDismountActionAbility::UACFDismountActionAbility()
{
    // Root motion by default; set bWarpToDismountPoint = true in Blueprints to
    // switch to EMotionWarped and enable the warp toward the landing point.
    ActionConfig.MontageReproductionType = EMontageReproductionType::ERootMotion;

    // Dismount is player-driven; no BT to pause.
    ActionConfig.bStopBehavioralThree = false;

    // The rider is in MOVE_None while mounted — allow the action to fire.
    // Default FActionConfig already includes MOVE_None, Walking, Falling, so
    // no extra modification is needed.
}

// ---------------------------------------------------------------------------
// UACFGameplayAbility interface
// ---------------------------------------------------------------------------

bool UACFDismountActionAbility::CanActivateAbility(
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

    // Only allow dismount when the rider is currently riding.
    const UACFRiderComponent* RiderComp = GetRiderComponent();
    if (!RiderComp || !RiderComp->IsRiding())
    {
        UE_LOG(ACFLog, Warning,
            TEXT("ACFDismountActionAbility: CanActivate failed — rider is not currently mounted."));
        return false;
    }

    return true;
}

// ---------------------------------------------------------------------------
// UACFActionAbility interface
// ---------------------------------------------------------------------------

void UACFDismountActionAbility::OnActionEnded_Implementation()
{
    Super::OnActionEnded_Implementation();

    // OnActionEnded is called server-side from Internal_OnDeactivated.
    // Calling StartDismount triggers:
    //   1. Smooth camera blend: live mount view → live rider view (bLockOutgoing=false)
    //   2. After the blend, possession is swapped back to the rider (no camera snap)
    //   3. Rider is detached and placed at the requested dismount point
    UACFRiderComponent* RiderComp = GetRiderComponent();
    if (RiderComp)
    {
        RiderComp->StartDismount(DismountPointName);
    }
    else
    {
        UE_LOG(ACFLog, Warning,
            TEXT("ACFDismountActionAbility: OnActionEnded — UACFRiderComponent not found."));
    }
}

// ---------------------------------------------------------------------------
// UACFGameplayAbility interface – warp
// ---------------------------------------------------------------------------

FTransform UACFDismountActionAbility::GetWarpTransform_Implementation()
{
    if (bWarpToDismountPoint)
    {
        if (const UACFMountableComponent* MountComp = GetMountableComponent())
        {
            if (const UACFMountPointComponent* DismountPt = MountComp->GetDismountPoint(DismountPointName))
            {
                return DismountPt->GetComponentTransform();
            }
        }
    }
    return Super::GetWarpTransform_Implementation();
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

UACFRiderComponent* UACFDismountActionAbility::GetRiderComponent() const
{
    const ACharacter* Character = GetCharacterOwner();
    if (!Character)
    {
        return nullptr;
    }
    return Character->FindComponentByClass<UACFRiderComponent>();
}

UACFMountableComponent* UACFDismountActionAbility::GetMountableComponent() const
{
    const UACFRiderComponent* RiderComp = GetRiderComponent();
    if (!RiderComp)
    {
        return nullptr;
    }
    return RiderComp->GetMountComp();
}
