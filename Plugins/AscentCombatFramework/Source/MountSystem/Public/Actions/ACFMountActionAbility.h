// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Actions/ACFActionAbility.h"
#include "ACFMountActionAbility.generated.h"

class UACFMountableComponent;
class UACFRiderComponent;

/**
 * Action ability that warps the rider toward the mount socket and then performs
 * the full mount sequence (attach + camera blend + possession swap).
 *
 * ## Setup
 *
 * 1. Assign this ability (or a Blueprint subclass) to the rider character's ability set.
 *    Use the same GameplayTag stored in UACFMountableComponent::MountActionTag.
 *
 * 2. Trigger the action with a payload whose TargetActor is set to the mount pawn.
 *    The ability resolves UACFMountableComponent from that actor automatically.
 *
 * 3. Set ActionConfig.MontageReproductionType = EMotionWarped (default) and
 *    ActionConfig.WarpInfo.SyncPoint to the name used in the montage's
 *    MotionWarping notify-state (default "MountPoint").
 *    The warp target is the world transform of UACFMountableComponent::MountPointSocket.
 *
 * 4. When the montage ends, OnActionEnded automatically calls
 *    UACFRiderComponent::StartMount which handles:
 *      - Attaching the rider to the mount socket (bLockOutgoing freeze for camera)
 *      - Smooth camera blend from frozen rider view → live mount view
 *      - Deferred possession swap after the blend completes
 */
UCLASS(Blueprintable, BlueprintType)
class MOUNTSYSTEM_API UACFMountActionAbility : public UACFActionAbility
{
    GENERATED_BODY()

public:
    UACFMountActionAbility();

protected:
    /**
     * Returns the world-space transform of the mount socket for use as the
     * motion-warp target.  Override in Blueprint to provide a custom approach
     * position (e.g. a ground-level point beside the mount).
     */
    virtual FTransform GetWarpTransform_Implementation() override;

    /**
     * Checks that a valid mount target was passed in the ability payload.
     */
    virtual bool CanActivateAbility(const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayTagContainer* SourceTags = nullptr,
        const FGameplayTagContainer* TargetTags = nullptr,
        OUT FGameplayTagContainer* OptionalRelevantTags = nullptr) const override;

    /**
     * Called on the server when the mount montage ends.
     * Triggers UACFRiderComponent::StartMount which handles attachment,
     * camera blend, and the deferred possession swap.
     */
    virtual void OnActionEnded_Implementation() override;

private:
    /** Resolves UACFMountableComponent from StoredPayload.TargetActor. */
    UACFMountableComponent* GetTargetMountableComponent() const;

    /** Finds UACFRiderComponent on the character owner. */
    UACFRiderComponent* GetRiderComponent() const;
};
