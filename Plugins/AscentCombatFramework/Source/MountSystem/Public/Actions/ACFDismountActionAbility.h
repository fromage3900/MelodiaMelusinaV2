// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Actions/ACFActionAbility.h"
#include "ACFDismountActionAbility.generated.h"

class UACFRiderComponent;
class UACFMountableComponent;

/**
 * Action ability that plays a dismount montage on the rider and then performs
 * the full dismount sequence (camera blend back → possession swap → detach).
 *
 * ## Setup
 *
 * Because during a ride the player controller possesses the MOUNT pawn (not the
 * rider), this ability must be triggered on the RIDER's ability system via
 * UACFMountableComponent::TriggerActionOnRider.
 *
 * Typical call site on the mount pawn Blueprint:
 *   MountableComp->TriggerActionOnRider(DismountActionTag, EActionPriority::EHigh);
 *
 * ## Sequence
 *
 * 1. The dismount montage plays on the rider (still attached to the mount socket).
 * 2. When the montage ends, UACFRiderComponent::StartDismount is called, which:
 *      a. Starts a smooth camera blend from mount → rider (bLockOutgoing=false
 *         so the mount camera keeps updating during the transition).
 *      b. After the blend completes, the possession is swapped back to the rider
 *         (the SetViewTarget call from ClientRestart is a no-op — no snap).
 *      c. The rider is detached and placed at the dismount point.
 *
 * ## Optional motion-warping toward the dismount point
 *
 * Set bWarpToDismountPoint = true, set ActionConfig.MontageReproductionType =
 * EMotionWarped, and configure ActionConfig.WarpInfo.SyncPoint to the name used
 * in the montage's MotionWarping notify-state.
 * The warp target will be the UACFMountPointComponent matching DismountPointName
 * (or the default dismount point if NAME_None).
 */
UCLASS(Blueprintable, BlueprintType)
class MOUNTSYSTEM_API UACFDismountActionAbility : public UACFActionAbility
{
    GENERATED_BODY()

public:
    UACFDismountActionAbility();

protected:
    /**
     * Named dismount point passed to UACFRiderComponent::StartDismount.
     * Leave as NAME_None to use UACFMountableComponent::DefaultDismountPoint.
     */
    UPROPERTY(EditDefaultsOnly, Category = "ACF|Mount")
    FName DismountPointName = NAME_None;

    /**
     * When true the dismount montage uses motion warping toward the dismount point.
     * Set ActionConfig.MontageReproductionType = EMotionWarped and configure
     * ActionConfig.WarpInfo.SyncPoint to match the notify-state in the montage.
     */
    UPROPERTY(EditDefaultsOnly, Category = "ACF|Mount")
    bool bWarpToDismountPoint = false;

    /**
     * Returns the world-space transform of the target dismount point for
     * optional motion warping.  Called only when bWarpToDismountPoint is true.
     */
    virtual FTransform GetWarpTransform_Implementation() override;

    /**
     * Checks that the rider is currently mounted before allowing activation.
     */
    virtual bool CanActivateAbility(const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayTagContainer* SourceTags = nullptr,
        const FGameplayTagContainer* TargetTags = nullptr,
        OUT FGameplayTagContainer* OptionalRelevantTags = nullptr) const override;

    /**
     * Called on the server when the dismount montage ends.
     * Triggers UACFRiderComponent::StartDismount which handles the camera blend
     * and the deferred possession swap back to the rider.
     */
    virtual void OnActionEnded_Implementation() override;

private:
    UACFRiderComponent*     GetRiderComponent() const;
    UACFMountableComponent* GetMountableComponent() const;
};
