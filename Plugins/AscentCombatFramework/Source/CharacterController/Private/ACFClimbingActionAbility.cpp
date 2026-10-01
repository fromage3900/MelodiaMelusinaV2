// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#include "ACFClimbingActionAbility.h"
#include "ACFLedgeClimbingComponent.h"
#include "ACFClimbingMontageDataAsset.h"
#include "ACFGripPointComponent.h"
#include "GameFramework/Character.h"

UACFClimbingActionAbility::UACFClimbingActionAbility()
{
    // Motion-warped montages are expected for climbing transitions
    ActionConfig.MontageReproductionType = EMontageReproductionType::EMotionWarped;
    ActionConfig.WarpInfo.SyncPoint = WarpSyncPointName;
    ActionConfig.WarpInfo.TargetType = EWarpTargetType::ETargetComponent;

    // Climbing transitions should be allowed in any movement mode including custom
    ActionConfig.PerformableInMovementModes.Reset();
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Walking);
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Falling);
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Custom);
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_None);

    // Let physics handle rotation during root motion so the character tilts properly
    bAllowPhysicalRotation = false;
}

// ---------------------------------------------------------------------------
//  Activation
// ---------------------------------------------------------------------------

void UACFClimbingActionAbility::OnActionStarted_Implementation()
{
    // Cache the target grip at the moment the ability fires so
    // warp queries always resolve consistently even if the component state
    // changes mid-montage.
    CachedGripPoint = GetPendingGrip();

    // Update the warp sync point name in case it was changed in the data asset
    if (UACFClimbingMontageDataAsset* DS = ResolveDataAsset())
    {
        FClimbingDirectionEntry Entry;
        if (DS->GetEntryForDirection(ClimbingDirection, Entry) && Entry.Montage)
        {
            // Ensure the correct montage is set (may have been overridden by
            // the data asset since ability construction)
            SetAnimMontage(Entry.Montage);
        }
    }

    ActionConfig.WarpInfo.SyncPoint = WarpSyncPointName;
    ActionConfig.WarpInfo.TargetType = EWarpTargetType::ETargetComponent;

    Super::OnActionStarted_Implementation();
}

// ---------------------------------------------------------------------------
//  End / alignment
// ---------------------------------------------------------------------------

void UACFClimbingActionAbility::OnActionEnded_Implementation()
{
    Super::OnActionEnded_Implementation();

    if (bAlignToWallOnEnd && GetCharacterOwner() && GetCharacterOwner()->HasAuthority())
    {
        AlignCharacterToWall();
    }
}

void UACFClimbingActionAbility::ClientsOnActionEnded_Implementation()
{
    Super::ClientsOnActionEnded_Implementation();

    if (bAlignToWallOnEnd && GetCharacterOwner() && GetCharacterOwner()->IsLocallyControlled())
    {
        AlignCharacterToWall();
    }
}

// ---------------------------------------------------------------------------
//  Warp overrides
// ---------------------------------------------------------------------------

UAnimMontage* UACFClimbingActionAbility::GetMontage_Implementation() const
{
    if (UACFClimbingMontageDataAsset* DS = ResolveDataAsset())
    {
        UAnimMontage* DSMontage = DS->GetMontageForDirection(ClimbingDirection);
        if (DSMontage)
        {
            return DSMontage;
        }
    }
    // Fallback to whatever was set manually on the ability
    return Super::GetMontage_Implementation();
}

FTransform UACFClimbingActionAbility::GetWarpTransform_Implementation()
{
    if (CachedGripPoint)
    {
        return CachedGripPoint->GetCharacterAlignTransform();
    }
    return Super::GetWarpTransform_Implementation();
}

USceneComponent* UACFClimbingActionAbility::GetWarpTargetComponent_Implementation()
{
    // Return the grip point component itself as the warp target.
    // The engine's SkewWarp modifier will warp the root motion toward
    // the component's world transform.
    if (CachedGripPoint)
    {
        return CachedGripPoint;
    }
    return Super::GetWarpTargetComponent_Implementation();
}

void UACFClimbingActionAbility::GetWarpInfo_Implementation(FACFWarpReproductionInfo& outWarpInfo)
{
    Super::GetWarpInfo_Implementation(outWarpInfo);

    outWarpInfo.WarpConfig.SyncPoint = WarpSyncPointName;
    outWarpInfo.WarpConfig.TargetType = EWarpTargetType::ETargetComponent;

    if (CachedGripPoint)
    {
        outWarpInfo.TargetComponent = CachedGripPoint;
        const FTransform AlignTransform = CachedGripPoint->GetCharacterAlignTransform();
        outWarpInfo.WarpLocation = AlignTransform.GetLocation();
        outWarpInfo.WarpRotation = AlignTransform.GetRotation().Rotator();
    }
}

// ---------------------------------------------------------------------------
//  Private helpers
// ---------------------------------------------------------------------------

UACFGripPointComponent* UACFClimbingActionAbility::GetPendingGrip() const
{
    if (!GetCharacterOwner())
    {
        return nullptr;
    }
    UACFLedgeClimbingComponent* ClimbComp = GetCharacterOwner()->FindComponentByClass<UACFLedgeClimbingComponent>();
    if (ClimbComp)
    {
        return ClimbComp->GetCurrentGripPoint();
    }
    return nullptr;
}

UACFClimbingMontageDataAsset* UACFClimbingActionAbility::ResolveDataAsset() const
{
    if (MontageDataOverride)
    {
        return MontageDataOverride;
    }

    if (!GetCharacterOwner())
    {
        return nullptr;
    }
    UACFLedgeClimbingComponent* ClimbComp = GetCharacterOwner()->FindComponentByClass<UACFLedgeClimbingComponent>();
    if (ClimbComp)
    {
        return ClimbComp->ClimbingMontageData;
    }
    return nullptr;
}

void UACFClimbingActionAbility::AlignCharacterToWall() const
{
    if (!CachedGripPoint || !GetCharacterOwner())
    {
        return;
    }

    const FTransform AlignTransform = CachedGripPoint->GetCharacterAlignTransform();

    // Snap location
    GetCharacterOwner()->SetActorLocation(AlignTransform.GetLocation(), false, nullptr, ETeleportType::TeleportPhysics);

    // Snap rotation (yaw only)
    FRotator NewRot = GetCharacterOwner()->GetActorRotation();
    NewRot.Yaw = AlignTransform.GetRotation().Rotator().Yaw;
    GetCharacterOwner()->SetActorRotation(NewRot, ETeleportType::TeleportPhysics);
}
