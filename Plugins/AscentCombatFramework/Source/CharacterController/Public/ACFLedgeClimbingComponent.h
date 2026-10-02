// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#pragma once

#include "ACFClimbingTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFLedgeClimbingComponent.generated.h"

class UACFGripPointComponent;
class UACFClimbingMontageDataAsset;
class UACFAbilitySystemComponent;
class ACharacter;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLedgeClimbingStateChanged, bool, bIsClimbing);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnGripChanged, UACFGripPointComponent*, NewGrip, EClimbingDirection, Direction);

/**
 * Add this component to an AACFCharacter (or any ACharacter that also has an
 * UACFAbilitySystemComponent) to get Assassin's Creed-style ledge-to-ledge
 * climbing.
 *
 * Usage:
 *   1. Place UACFGripPointComponent on climbable meshes.
 *   2. Assign a UACFClimbingMontageDataAsset with per-direction montages/tags.
 *   3. Call JumpToNearestGripPoint(DirectionVector) from input (e.g. jump button + stick).
 *
 * Multiplayer:
 *   - Grip detection and ability triggering run on authority and are replicated
 *     through the existing ACF ability system replication.
 *   - CurrentGripPoint is replicated so clients can query it.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent),
    DisplayName = "ACF Climbing Component")
class CHARACTERCONTROLLER_API UACFLedgeClimbingComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UACFLedgeClimbingComponent();

    // -----------------------------------------------------------------------
    //  Core API
    // -----------------------------------------------------------------------

    /**
     * Main entry point: given a world-space (or local-space) direction input
     * (e.g. from the player's thumbstick / WASD), finds the best nearby grip
     * point in that direction and triggers the appropriate climbing ability.
     *
     * @param DirectionInput   Normalised 2D input vector (X = right, Y = up in
     *                         the character's local XY plane, or world-space –
     *                         see bInputIsWorldSpace).
     * @param bInputIsWorldSpace  When true DirectionInput is treated as world-
     *                            space and projected onto the wall plane.
     *                            When false (default) it is interpreted as
     *                            character-local right/up axes.
     * @return True if a valid grip was found and the ability was triggered.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool JumpToNearestGripPoint(FVector2D DirectionInput, bool bInputIsWorldSpace = false);

    /**
     * Attaches the character to the specified grip point without playing a
     * transition montage.  Useful for the initial grab (e.g. from a jump).
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void GrabGripPoint(UACFGripPointComponent* GripPoint);

    /** Releases the current grip point and returns the character to normal locomotion. */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ReleaseGrip();

    // -----------------------------------------------------------------------
    //  Queries
    // -----------------------------------------------------------------------

    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsClimbing() const { return bIsClimbing; }

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFGripPointComponent* GetCurrentGripPoint() const { return CurrentGripPoint; }

    /**
     * Collects all grip points within SearchRadius of the character.
     * Results are sorted by distance (closest first).
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    TArray<UACFGripPointComponent*> FindNearbyGripPoints() const;

    /**
     * Among all nearby grip points, returns the one that best matches the
     * supplied direction.  Returns nullptr when none qualify.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    UACFGripPointComponent* FindBestGripInDirection(FVector WorldDirection) const;

    // -----------------------------------------------------------------------
    //  Events
    // -----------------------------------------------------------------------

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnLedgeClimbingStateChanged OnClimbingStateChanged;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnGripChanged OnGripChanged;

    // -----------------------------------------------------------------------
    //  Configuration
    // -----------------------------------------------------------------------

    /** Data asset containing per-direction montages and ability tags. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TObjectPtr<UACFClimbingMontageDataAsset> ClimbingMontageData;

    /** Sphere radius within which grip points are considered reachable. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF, meta = (ClampMin = "50.0"))
    float SearchRadius = 300.f;

    /**
     * Minimum dot product between the desired direction and the direction to a
     * candidate grip.  Higher values (→ 1.0) require closer alignment.
     * 0.5 corresponds to ±60°.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF, meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float DirectionDotThreshold = 0.4f;

    /**
     * Collision channel used to scan for actors that carry grip point
     * components.  Climbable actors should respond to this channel.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TEnumAsByte<ECollisionChannel> GripSearchChannel = ECC_WorldDynamic;

    /**
     * If true the character is kept glued to the current grip (movement input
     * blocked, gravity off) while bIsClimbing is true.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    bool bFreezePawnWhileClimbing = true;

protected:
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
    // -----------------------------------------------------------------------
    //  Internal helpers
    // -----------------------------------------------------------------------

    /** Resolves and caches the ACFAbilitySystemComponent on the owning character. */
    void CacheComponents();

    /**
     * Converts a 2D input vector into a world-space 3D direction aligned with
     * the wall plane of the current grip.
     */
    FVector InputToWorldDirection(FVector2D Input2D, bool bIsWorldSpace) const;

    /** Classifies a world-space direction into one of the 8 EClimbingDirection values. */
    EClimbingDirection ClassifyDirection(FVector WorldDir) const;

    /** Triggers the ACF action ability for the given direction. Returns true on success. */
    bool TriggerClimbAbility(EClimbingDirection Direction, UACFGripPointComponent* TargetGrip);

    /** Server-side RPC to replicate the grip jump request. */
    UFUNCTION(Server, Reliable)
    void Server_JumpToGrip(UACFGripPointComponent* TargetGrip, EClimbingDirection Direction);

    /** Applies / removes climbing movement constraints. */
    void SetClimbingMovementMode(bool bEnter);

    UFUNCTION()
    void OnRep_CurrentGripPoint();

    UFUNCTION()
    void OnRep_IsClimbing();

    // -----------------------------------------------------------------------
    //  State (replicated)
    // -----------------------------------------------------------------------

    UPROPERTY(ReplicatedUsing = OnRep_CurrentGripPoint)
    TObjectPtr<UACFGripPointComponent> CurrentGripPoint;

    UPROPERTY(ReplicatedUsing = OnRep_IsClimbing)
    bool bIsClimbing = false;

    // -----------------------------------------------------------------------
    //  Cached refs (not replicated)
    // -----------------------------------------------------------------------

    UPROPERTY()
    TObjectPtr<ACharacter> CharOwner;

    UPROPERTY()
    TObjectPtr<UACFAbilitySystemComponent> AbilityComp;
};
