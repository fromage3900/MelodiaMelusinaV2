// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#pragma once

#include "Components/SphereComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFGripPointComponent.generated.h"

/**
 * A scene component placed on any mesh (static or skeletal) that marks a
 * hand-hold position for the ACF climbing system.
 *
 * Place one or several of these on a wall, ladder, or any climbable actor.
 * The owning actor's surface normal is derived from its mesh at runtime for
 * alignment purposes.
 *
 * In multiplayer this component does NOT need to replicate state; it is
 * a passive data point queried by UACFLedgeClimbingComponent on the owning client.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent),
    DisplayName = "ACF Grip Point Component")
class CHARACTERCONTROLLER_API UACFGripPointComponent : public USphereComponent
{
    GENERATED_BODY()

public:
    UACFGripPointComponent();

    // -----------------------------------------------------------------------
    //  Getters
    // -----------------------------------------------------------------------

    /** Returns the world-space position of this grip. */
    UFUNCTION(BlueprintPure, Category = ACF)
    FVector GetGripWorldLocation() const { return GetComponentLocation(); }

    /**
     * Computes the surface normal of the owning mesh at the grip location.
     * Works for both UStaticMeshComponent and USkeletalMeshComponent owners.
     * Falls back to the component's forward vector when no mesh is found.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FVector GetSurfaceNormal() const;

    /**
     * Returns the full transform the character should be snapped to when
     * grabbing this grip: location == grip world location,
     * rotation == facing away from the surface normal.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FTransform GetCharacterAlignTransform() const;

    /** Optional tag to filter grip points (e.g. only high reaches, only footholds). */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetGripTag() const { return GripTag; }

    /** Whether this grip can currently be grabbed (can be toggled at runtime). */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsGripEnabled() const { return bGripEnabled; }

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetGripEnabled(bool bEnabled) { bGripEnabled = bEnabled; }

    // -----------------------------------------------------------------------
    //  Editor / design properties
    // -----------------------------------------------------------------------

protected:
    /** Optional tag to categorise this grip (e.g. "Grip.High", "Grip.Low"). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FGameplayTag GripTag;

    /** When false this grip is ignored by the climbing component. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    bool bGripEnabled = true;

    /**
     * Offset applied on top of the component transform when building the
     * character warp target (useful to move the character slightly away from
     * the wall so it doesn't clip).
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FVector WallOffsetOverride = FVector(40.f, 0.f, 0.f);

    virtual void BeginPlay() override;

private:
    /** Attempts to find the mesh component that owns (or is a sibling of) this grip. */
    UPrimitiveComponent* FindOwningMeshComponent() const;
};
