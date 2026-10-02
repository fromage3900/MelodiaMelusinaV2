// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/SphereComponent.h"
#include "CoreMinimal.h"
#include "Groups/ACFAIGroupSpawner.h"

#include "ACFVolumeAIGroupSpawner.generated.h"

/**
 *  When Enabled, this component
 */
UCLASS()
class AIFRAMEWORK_API AACFVolumeAIGroupSpawner : public AACFAIGroupSpawner {
    GENERATED_BODY()

public:
    /**
     * * Default constructor.
     */
    AACFVolumeAIGroupSpawner();

    /**
     * * Enables or disables the spawner.
     *
     * If enabled, it immediately checks if a player-controlled pawn is inside the detection sphere.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF")
    void SetSpawnerEnabled(bool bEnable);

    /**
     * * Checks if a player-controlled pawn is inside the detection sphere.
     *
     * @return True if a player-controlled pawn is present, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = "ACF")
    bool IsPlayerInsideDetectionSphere() const;

    UFUNCTION(BlueprintPure, Category = "ACF")
    bool IsDistanceSpawnEnabled() const
    {
        return bIsDistanceSpawnerEnabled;
    }

protected:
    /**
     * * Called when the game starts or when spawned.
     */
    virtual void BeginPlay() override;

    /**
     * * Sphere component used to detect player presence.
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<USphereComponent> DetectionSphere;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF")
    bool bIsDistanceSpawnerEnabled;

    /**
     * * Handles overlap events when an actor enters the detection sphere.
     */
    UFUNCTION()
    void OnPlayerEnterDetectionSphere(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

    /**
     * * Handles overlap events when an actor exits the detection sphere.
     */
    UFUNCTION()
    void OnPlayerExitDetectionSphere(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

private:
    /**
     * * Spawns the AI group when the player enters the detection sphere.
     */
    void SpawnAIGroup();
};
