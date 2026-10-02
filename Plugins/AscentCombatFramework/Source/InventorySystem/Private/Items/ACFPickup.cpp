// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Items/ACFPickup.h"
#include "ARSStatisticsComponent.h"
#include <GameFramework/Pawn.h>

// Sets default values
AACFPickup::AACFPickup()
{
    // Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = false;
    PickUpCapsule = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Pickup Collision"));
}

// Called when the game starts or when spawned
void AACFPickup::BeginPlay()
{
    Super::BeginPlay();
}

void AACFPickup::OnInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType /*= ""*/)
{
    Super::OnInteractedByPawn(Pawn, interactionType);

    if (Pawn) {
        UARSStatisticsComponent* statComp = Pawn->FindComponentByClass<UARSStatisticsComponent>();
        if (statComp) {
            for (const auto& stat : OnPickupEffect) {
                statComp->ModifyStat(stat);
            }
            for (const auto& att : OnPickupBuff) {
                statComp->AddTimedAttributeSetModifier(att.modifier, att.duration);
            }
        }
    }
}

void AACFPickup::OnInteractableRegisteredByPawn_Implementation(class APawn* Pawn)
{
    if (HasAuthority() && bPickOnOverlap && IACFInteractableInterface::Execute_CanBeInteracted(this, Pawn)) {
        IACFInteractableInterface::Execute_OnInteractedByPawn(this, Pawn, "");
    }
}
