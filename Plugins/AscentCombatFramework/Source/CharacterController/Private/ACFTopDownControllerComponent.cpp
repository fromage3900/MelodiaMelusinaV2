// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFTopDownControllerComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "Blueprint/AIBlueprintHelperLibrary.h"
#include <GameFramework/Pawn.h>
#include <GameFramework/PlayerController.h>
#include <Engine/World.h>

// Called when the game starts
void UACFTopDownControllerComponent::BeginPlay()
{
    Super::BeginPlay();

    if (!GetOwnerController()) {
        UE_LOG(LogTemp, Error, TEXT("TopDown Component needs to be added to a Player Controller! - UACFTopDownControllerComponent"));
    }
    // ...
}

void UACFTopDownControllerComponent::OnInputStarted()
{
    GetOwnerController()->StopMovement();
}

APlayerController* UACFTopDownControllerComponent::GetOwnerController() const
{
    return Cast<APlayerController>(GetOwner());
}

 UACFTopDownControllerComponent::UACFTopDownControllerComponent()
{
    bEnabled = true;
    ShortPressThreshold = 0.3f;
 }

// Triggered every frame when the input is held down
void UACFTopDownControllerComponent::SetDestinationTriggered()
{
    // We flag that the input is being pressed
    FollowTime += GetWorld()->GetDeltaSeconds();

    // We look for the location in the world where the player has pressed the input
    FHitResult Hit;
    const bool bHitSuccessful = GetOwnerController()->GetHitResultUnderCursor(ECollisionChannel::ECC_Visibility, true, Hit);
   

    // If we hit a surface, cache the location
    if (bHitSuccessful) {
        CachedDestination = Hit.Location;
    }

    // Move towards mouse pointer or touch
    APawn* ControlledPawn = GetOwnerController()->GetPawn();
    if (ControlledPawn != nullptr) {
        FVector WorldDirection = (CachedDestination - ControlledPawn->GetActorLocation()).GetSafeNormal();
        ControlledPawn->AddMovementInput(WorldDirection, 1.0, false);
    }
}

void UACFTopDownControllerComponent::SetDestinationReleased()
{
    // If it was a short press
    if (FollowTime <= ShortPressThreshold) {
        // We move there and spawn some particles
        UAIBlueprintHelperLibrary::SimpleMoveToLocation(GetOwnerController(), CachedDestination);
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(GetOwnerController(), FXCursor, CachedDestination, FRotator::ZeroRotator, FVector(1.f, 1.f, 1.f), true, true, ENCPoolMethod::None, true);
    }

    FollowTime = 0.f;
}
