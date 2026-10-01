// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Groups/ACFVolumeAIGroupSpawner.h"
#include "Components/ACFGroupAIComponent.h"

/**
 * * Constructor: Initializes default values.
 */
AACFVolumeAIGroupSpawner::AACFVolumeAIGroupSpawner()
{
    // Create the detection sphere and attach it to the root component
    DetectionSphere = CreateDefaultSubobject<USphereComponent>(TEXT("DetectionSphere"));
    DetectionSphere->SetupAttachment(RootComponent);
    DetectionSphere->SetSphereRadius(2500.f);
    DetectionSphere->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    DetectionSphere->SetCollisionResponseToAllChannels(ECR_Ignore);
    DetectionSphere->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

    // Bind overlap events
    DetectionSphere->OnComponentBeginOverlap.AddDynamic(this, &AACFVolumeAIGroupSpawner::OnPlayerEnterDetectionSphere);
    DetectionSphere->OnComponentEndOverlap.AddDynamic(this, &AACFVolumeAIGroupSpawner::OnPlayerExitDetectionSphere);

    bIsDistanceSpawnerEnabled = false;
}

/**
 * * Called when the game starts.
 */
void AACFVolumeAIGroupSpawner::BeginPlay()
{
    Super::BeginPlay();
}

/**
 * * Enables or disables the spawner.
 */
void AACFVolumeAIGroupSpawner::SetSpawnerEnabled(bool bEnable)
{
    bIsDistanceSpawnerEnabled = bEnable;
    DetectionSphere->SetCollisionEnabled(bEnable ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);

    if (bIsDistanceSpawnerEnabled && IsPlayerInsideDetectionSphere()) {
        SpawnAIGroup();
    }
}

/**
 * * Handles player entering the detection sphere.
 */
void AACFVolumeAIGroupSpawner::OnPlayerEnterDetectionSphere(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep,
    const FHitResult& SweepResult)
{
    APawn* Pawn = Cast<APawn>(OtherActor);
    if (bIsDistanceSpawnerEnabled && Pawn && Pawn->IsPlayerControlled() && !GetAIGroupComponent()->IsGroupSpawned()) {
        SpawnAIGroup();
    }
}

/**
 * * Handles player exiting the detection sphere.
 */
void AACFVolumeAIGroupSpawner::OnPlayerExitDetectionSphere(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
    APawn* Pawn = Cast<APawn>(OtherActor);
    if (bIsDistanceSpawnerEnabled && Pawn && Pawn->IsPlayerControlled() && GetAIGroupComponent()->IsGroupSpawned()) {
        GetAIGroupComponent()->DespawnGroup(true);
    }
}

/**
 * * Spawns the AI group when the player enters the detection sphere.
 */
void AACFVolumeAIGroupSpawner::SpawnAIGroup()
{
    GetAIGroupComponent()->SpawnGroup();
}

/**
 * * Checks if a player-controlled pawn is inside the detection sphere.
 */
bool AACFVolumeAIGroupSpawner::IsPlayerInsideDetectionSphere() const
{
    TArray<AActor*> OverlappingActors;
    DetectionSphere->GetOverlappingActors(OverlappingActors);

    for (AActor* Actor : OverlappingActors) {
        APawn* Pawn = Cast<APawn>(Actor);
        if (Pawn && Pawn->IsPlayerControlled()) {
            return true;
        }
    }
    return false;
}
