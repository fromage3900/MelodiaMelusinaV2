// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#pragma once

#include "ACFClimbingTypes.h"
#include "Actions/ACFActionAbility.h"
#include "CoreMinimal.h"

#include "ACFClimbingActionAbility.generated.h"

class UACFLedgeClimbingComponent;
class UACFGripPointComponent;
class UACFClimbingMontageDataAsset;

/**
 * Gameplay Ability that handles a single grip-to-grip climbing transition.
 *
 * Design contract:
 *   - Assign one instance (per direction) inside a UACFAbilitySet on the character.
 *   - Set ClimbingDirection to match the ability tag you use in the data asset.
 *   - The ability reads the pending grip from the owning character's
 *     UACFLedgeClimbingComponent, selects the correct montage from the data asset,
 *     configures motion warp to land exactly on the grip, and then aligns the
 *     character to the wall surface when the montage finishes.
 *
 * Alternatively you may create a single generic ability that is triggered for
 * every direction and overrides GetMontage() in Blueprint to pick the right
 * montage from ClimbingMontageData at runtime.  Both patterns work.
 */
UCLASS(Blueprintable, BlueprintType)
class CHARACTERCONTROLLER_API UACFClimbingActionAbility : public UACFActionAbility
{
    GENERATED_BODY()

public:
    UACFClimbingActionAbility();

    // -----------------------------------------------------------------------
    //  Configuration
    // -----------------------------------------------------------------------

    /**
     * The climbing direction this ability instance handles.
     * Must match the tag mapping in UACFClimbingMontageDataAsset.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    EClimbingDirection ClimbingDirection = EClimbingDirection::Up;

    /**
     * If set, overrides the data asset resolved from the owning
     * UACFLedgeClimbingComponent.  Useful for standalone ability blueprints.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TObjectPtr<UACFClimbingMontageDataAsset> MontageDataOverride;

    /**
     * Name of the motion-warp sync point defined in the montage.
     * Should match the Motion Warp notify window name in the anim asset.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FName WarpSyncPointName = TEXT("GripTarget");

    /**
     * When true the character's rotation is snapped to face the wall at the
     * END of the ability (after the montage finishes).
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    bool bAlignToWallOnEnd = true;

    // -----------------------------------------------------------------------
    //  UACFGameplayAbility / UACFActionAbility overrides
    // -----------------------------------------------------------------------

    /** Selects the montage from the data asset at activation time. */
    virtual UAnimMontage* GetMontage_Implementation() const override;

    /** Provides the warp target transform (grip world transform). */
    virtual FTransform GetWarpTransform_Implementation() override;

    /** Provides the warp target component (the grip point scene component). */
    virtual USceneComponent* GetWarpTargetComponent_Implementation() override;

    /** Fills warp reproduction info (sync point name, warp type). */
    virtual void GetWarpInfo_Implementation(FACFWarpReproductionInfo& outWarpInfo) override;

protected:
    /** Called when ability activates on server – caches the pending grip. */
    virtual void OnActionStarted_Implementation() override;

    /** Called when ability ends – aligns the character to the wall. */
    virtual void OnActionEnded_Implementation() override;

    /** Called on all clients when ability ends – aligns the character. */
    virtual void ClientsOnActionEnded_Implementation() override;

private:
    /** Resolves the active grip from the owning UACFLedgeClimbingComponent. */
    UACFGripPointComponent* GetPendingGrip() const;

    /** Resolves the data asset (override first, then component). */
    UACFClimbingMontageDataAsset* ResolveDataAsset() const;

    /** Snaps the character to face the wall at the current grip. */
    void AlignCharacterToWall() const;

    UPROPERTY()
    TObjectPtr<UACFGripPointComponent> CachedGripPoint;
};
