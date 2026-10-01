// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actors/ACFActor.h"
#include "Game/ACFDamageType.h"

#include "ACFDestructable.generated.h"

class UGeometryCollectionComponent;

/**
 * ACF actor that breaks with Chaos (Geometry Collection) on death.
 * Damage from hostile actors is validated by UACFDamageHandlerComponent plus team rules
 * (same pipeline used by UACMCollisionManagerComponent::ApplyDamage via CanActorDamageActor).
 *
 * Assign a Geometry Collection asset on the GeometryCollection component. Collision traces from
 * weapons using the collisions manager will call TakeDamage on this actor when teams allow it.
 */
UCLASS(Blueprintable, BlueprintType)
class ASCENTCOMBATFRAMEWORK_API AACFDestructable : public AACFActor {
    GENERATED_BODY()

public:
    AACFDestructable();

protected:
    virtual void BeginPlay() override;

    /** Chaos visual / collision body. Attach a fractured Geometry Collection asset in the editor. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF|Destructable")
    TObjectPtr<UGeometryCollectionComponent> GeometryCollectionComp;

    /** If true, any first hostile hit (after team check) finishes the prop even if health would remain. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Destructable")
    bool bDestroyOnFirstHostileHit = true;

    /** Extra damage applied server-side to force death when bDestroyOnFirstHostileHit triggers. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Destructable", meta = (EditCondition = "bDestroyOnFirstHostileHit", ClampMin = "1"))
    float FirstHitFinisherDamage = 100000.f;

    /** Radius for ApplyExternalStrain (world units). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Destructable|Chaos", meta = (ClampMin = "1"))
    float ExternalStrainRadius = 400.f;

    /** Propagation depth for strain (cluster hierarchy levels). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Destructable|Chaos", meta = (ClampMin = "0"))
    int32 ExternalStrainPropagationDepth = 1000;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Destructable|Chaos", meta = (ClampMin = "0"))
    float ExternalStrainPropagationFactor = 1.f;

    /** Higher values break cluster bonds more aggressively. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Destructable|Chaos", meta = (ClampMin = "0"))
    float ExternalStrainMagnitude = 2400000.f;

    /** Impulse scale applied along the last hit direction on broken pieces. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Destructable|Chaos", meta = (ClampMin = "0"))
    float BreakScatterImpulse = 800.f;

    /** Fallback impulse if hit direction is zero. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Destructable|Chaos")
    FVector FallbackBreakImpulse = FVector(0.f, 0.f, 600.f);

    UFUNCTION()
    void HandleDestructableDeath();

    UFUNCTION()
    void HandleDamageForFirstHitDestroy(const FACFDamageEvent& DamageEvent);

    UFUNCTION(NetMulticast, Reliable)
    void Multicast_PlayDestruction(FVector StrainWorldLocation, FVector ImpulseDirection);

    void ApplyChaosDestructionAt(FVector StrainWorldLocation, FVector ImpulseDirection);

    void ServerTryFinishOnFirstHit(const FACFDamageEvent& DamageEvent);

    void DeferredApplyFirstHitKill();

    FACFDamageEvent PendingFirstHitKillEvent;

    bool bFirstHitKillFlushPending = false;
};
