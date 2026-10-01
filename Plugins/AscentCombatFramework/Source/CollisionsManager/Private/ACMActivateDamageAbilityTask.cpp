// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACMActivateDamageAbilityTask.h"

#include "ACMCollisionManagerComponent.h"
#include "AbilitySystemComponent.h"
#include "Engine/World.h"
#include "TimerManager.h"

UACMActivateDamageAbilityTask::UACMActivateDamageAbilityTask(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    bTickingTask = false;
    bTracesActive = false;
}

UACMActivateDamageAbilityTask* UACMActivateDamageAbilityTask::ActivateDamageTraces(
    UGameplayAbility* OwningAbility,
    FName TaskInstanceName,
    AActor* InTargetActor,
    const TArray<FName>& InTracesToActivate,
    float InDuration,
    bool bInStopOnFirstHit)
{
    UACMActivateDamageAbilityTask* MyObj = NewAbilityTask<UACMActivateDamageAbilityTask>(OwningAbility, TaskInstanceName);
    MyObj->TargetActor = InTargetActor;
    MyObj->TracesToActivate = InTracesToActivate;
    MyObj->Duration = InDuration;
    MyObj->bStopOnFirstHit = bInStopOnFirstHit;

    return MyObj;
}

void UACMActivateDamageAbilityTask::Activate()
{
    Super::Activate();

    if (!IsValid(TargetActor)) {
        UE_LOG(LogTemp, Warning, TEXT("AbilityTask_ActivateDamageTraces: Invalid Target Actor"));
        EndTask();
        return;
    }

    // Find the ACMCollisionManagerComponent on the target actor
    CollisionManager = TargetActor->FindComponentByClass<UACMCollisionManagerComponent>();

    if (!IsValid(CollisionManager)) {
        UE_LOG(LogTemp, Warning, TEXT("AbilityTask_ActivateDamageTraces: Target Actor does not have ACMCollisionManagerComponent"));
        EndTask();
        return;
    }

    // Bind to collision events
    CollisionManager->OnCollisionDetected.AddDynamic(this, &UACMActivateDamageAbilityTask::HandleCollisionDetected);
    CollisionManager->OnActorDamaged.AddDynamic(this, &UACMActivateDamageAbilityTask::HandleActorDamaged);

    // Start the traces
    StartTraces();

    // Set up duration timer if specified
    if (Duration > 0.0f) {
        if (UWorld* World = GetWorld()) {
            World->GetTimerManager().SetTimer(
                DurationTimerHandle,
                this,
                &UACMActivateDamageAbilityTask::HandleDurationExpired,
                Duration,
                false);
        }
    }
}

void UACMActivateDamageAbilityTask::StartTraces()
{
    if (!IsValid(CollisionManager)) {
        return;
    }

    bTracesActive = true;

    // If no specific traces specified, activate all
    if (TracesToActivate.Num() == 0) {
        if (Duration > 0.0f) {
            CollisionManager->StartAllTimedTraces(Duration);
        } else {
            CollisionManager->StartAllTraces();
        }
    } else {
        // Activate specific traces
        for (const FName& TraceName : TracesToActivate) {
            if (Duration > 0.0f) {
                CollisionManager->StartTimedSingleTrace(TraceName, Duration);
            } else {
                CollisionManager->StartSingleTrace(TraceName);
            }
        }
    }
}

void UACMActivateDamageAbilityTask::HandleCollisionDetected(const FHitResult& HitResult)
{
    if (!bTracesActive) {
        return;
    }

    // Broadcast the hit event
    if (IsValid(HitResult.GetActor())) {
        OnHit.Broadcast(HitResult.GetActor(), HitResult);

        // Stop traces if configured to stop on first hit
        if (bStopOnFirstHit) {
            StopTraces();
        }
    }
}

void UACMActivateDamageAbilityTask::HandleActorDamaged(AActor* DamagedActor)
{
    // This can be used for additional damage tracking if needed
    // The main hit detection is handled through HandleCollisionDetected
}

void UACMActivateDamageAbilityTask::HandleDurationExpired()
{
    if (bTracesActive) {
        StopTraces();
    }
}

void UACMActivateDamageAbilityTask::StopTraces()
{
    if (!bTracesActive) {
        return;
    }

    CleanupTraces();

    // Broadcast completion
    OnCompleted.Broadcast();

    // End the task
    EndTask();
}

void UACMActivateDamageAbilityTask::CleanupTraces()
{
    bTracesActive = false;

    // Clear the timer
    if (UWorld* World = GetWorld()) {
        World->GetTimerManager().ClearTimer(DurationTimerHandle);
    }

    // Stop all traces in the collision manager
    if (IsValid(CollisionManager)) {
        if (TracesToActivate.Num() == 0) {
            CollisionManager->StopAllTraces();
        } else {
            for (const FName& TraceName : TracesToActivate) {
                CollisionManager->StopSingleTrace(TraceName);
            }
        }

        // Unbind delegates
        CollisionManager->OnCollisionDetected.RemoveDynamic(this, &UACMActivateDamageAbilityTask::HandleCollisionDetected);
        CollisionManager->OnActorDamaged.RemoveDynamic(this, &UACMActivateDamageAbilityTask::HandleActorDamaged);
    }
}

void UACMActivateDamageAbilityTask::OnDestroy(bool bInOwnerFinished)
{
    CleanupTraces();
    Super::OnDestroy(bInOwnerFinished);
}