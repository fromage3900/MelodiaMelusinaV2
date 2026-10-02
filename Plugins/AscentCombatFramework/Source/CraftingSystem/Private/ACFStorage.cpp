// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFStorage.h"

#include "Components/ACFInteractableComponent.h"
#include "Components/ACFStorageComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"

AACFStorage::AACFStorage()
{
    bReplicates = true;
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    StorageMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("StorageMesh"));
    StorageMesh->SetupAttachment(SceneRoot);

    InteractableComponent = CreateDefaultSubobject<UACFInteractableComponent>(TEXT("InteractableComponent"));
    InteractableComponent->SetupAttachment(SceneRoot);

    StorageComponent = CreateDefaultSubobject<UACFStorageComponent>(TEXT("StorageComponent"));
}

// ── IACFInteractableInterface ─────────────────────────────────────────────────

void AACFStorage::OnInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType)
{
    // Override in Blueprint to open the storage widget or run custom interaction logic.
}

void AACFStorage::OnLocalInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType)
{
    // Override in Blueprint to handle local (client-side) interaction feedback.
}

void AACFStorage::OnInteractableRegisteredByPawn_Implementation(APawn* Pawn)
{
    // Override in Blueprint to react when a pawn enters the interaction range.
}

void AACFStorage::OnInteractableUnregisteredByPawn_Implementation(APawn* Pawn)
{
    // Override in Blueprint to react when a pawn leaves the interaction range (e.g. auto-close widget).
}
