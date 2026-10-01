// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/TriggerSphere.h"
#include "AQSQuestTrigger.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPlayerControlledPawnOverlap, APawn*, Pawn);

/**
 * A trigger sphere that fires a delegate only when a player-controlled pawn overlaps it.
 * Starts deactivated (no collision) and must be explicitly activated via ActivateTrigger().
 */
UCLASS(Blueprintable, BlueprintType, ClassGroup = (AQS), meta = (BlueprintSpawnableComponent))
class ASCENTQUESTSYSTEM_API AAQSQuestTrigger : public ATriggerSphere
{
    GENERATED_BODY()

public:
    AAQSQuestTrigger();

protected:
    virtual void BeginPlay() override;
    virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;

public:
    /** Enables the trigger collision so it can receive overlaps. */
    UFUNCTION(BlueprintCallable, Category = AQS)
    void ActivateTrigger();

    /** Disables the trigger collision. */
    UFUNCTION(BlueprintCallable, Category = AQS)
    void DeactivateTrigger();

    /** Called when a player-controlled pawn overlaps this trigger. */
    UPROPERTY(BlueprintAssignable, Category = AQS)
    FOnPlayerControlledPawnOverlap OnPlayerControlledPawnOverlap;
};
