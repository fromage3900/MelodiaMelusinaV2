// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Abilities/Tasks/AbilityTask.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACMActivateDamageAbilityTask.generated.h"


class UACMCollisionManagerComponent;
class AActor;

/**
 * Delegate fired when any actor is hit by damage traces
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnTraceHit, AActor*, HitActor, const FHitResult&, HitResult);

/**
 * Delegate fired when traces are completed (timed out or manually stopped)
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnTracesCompleted);

/**
 * Gameplay Task that activates damage traces using ACMCollisionManagerComponent
 * and provides callbacks when actors are hit or traces complete
 */
UCLASS()
class COLLISIONSMANAGER_API UACMActivateDamageAbilityTask : public UAbilityTask {
    GENERATED_BODY()

public:
    UACMActivateDamageAbilityTask(const FObjectInitializer& ObjectInitializer);

    /**
     * Creates a task that activates damage traces on the target actor
     *
     * @param OwningAbility The ability that owns this task
     * @param TaskInstanceName Name for this task instance
     * @param TargetActor Actor with ACMCollisionManagerComponent to activate traces on
     * @param TracesToActivate Array of trace names to activate (empty = all traces)
     * @param Duration How long to keep traces active (0 = until manually stopped)
     * @param bStopOnFirstHit Whether to stop all traces after first hit
     */
    UFUNCTION(BlueprintCallable, Category = "Ability|Tasks", meta = (HidePin = "OwningAbility", DefaultToSelf = "OwningAbility", BlueprintInternalUseOnly = "TRUE"))
    static UACMActivateDamageAbilityTask* ActivateDamageTraces(
        UGameplayAbility* OwningAbility,
        FName TaskInstanceName,
        AActor* TargetActor,
        const TArray<FName>& TracesToActivate,
        float Duration = 0.0f,
        bool bStopOnFirstHit = false);

    /**
     * Called when any actor is hit by the damage traces
     */
    UPROPERTY(BlueprintAssignable)
    FOnTraceHit OnHit;

    /**
     * Called when traces are completed (timed out or stopped)
     */
    UPROPERTY(BlueprintAssignable)
    FOnTracesCompleted OnCompleted;

    virtual void Activate() override;
    virtual void OnDestroy(bool bInOwnerFinished) override;

    /**
     * Manually stops all active traces
     */
    UFUNCTION(BlueprintCallable, Category = "Ability|Tasks")
    void StopTraces();

protected:
    /**
     * The actor with the collision manager component
     */
    UPROPERTY()
    AActor* TargetActor;

    /**
     * Array of trace names to activate (empty = all)
     */
    UPROPERTY()
    TArray<FName> TracesToActivate;

    /**
     * Duration to keep traces active
     */
    UPROPERTY()
    float Duration;

    /**
     * Whether to stop on first hit
     */
    UPROPERTY()
    bool bStopOnFirstHit;

    /**
     * Reference to the collision manager component
     */
    UPROPERTY()
    UACMCollisionManagerComponent* CollisionManager;

    /**
     * Timer handle for duration-based traces
     */
    FTimerHandle DurationTimerHandle;

    /**
     * Track if traces are currently active
     */
    bool bTracesActive;

    /**
     * Handles collision detection from the collision manager
     */
    UFUNCTION()
    void HandleCollisionDetected(const FHitResult& HitResult);

    /**
     * Handles actor damaged events from the collision manager
     */
    UFUNCTION()
    void HandleActorDamaged(AActor* DamagedActor);

    /**
     * Called when the duration timer expires
     */
    void HandleDurationExpired();

    /**
     * Starts the specified traces or all traces if array is empty
     */
    void StartTraces();

    /**
     * Internal cleanup when stopping traces
     */
    void CleanupTraces();
};
