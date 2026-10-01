// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AQSQuestTrigger.h"
#include "Components/ShapeComponent.h"
#include "Components/SphereComponent.h"
#include "Components/BillboardComponent.h"
#include "GameFramework/Pawn.h"

AAQSQuestTrigger::AAQSQuestTrigger()
{
    PrimaryActorTick.bCanEverTick = false;

    // Default radius: 200 cm (2 metres)
    if (USphereComponent* Sphere = Cast<USphereComponent>(GetCollisionComponent()))
    {
        Sphere->InitSphereRadius(200.f);
    }
}

void AAQSQuestTrigger::BeginPlay()
{
    Super::BeginPlay();

    // Start deactivated: no collision and sprite hidden in game
    if (GetCollisionComponent())
    {
        GetCollisionComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }

    if (UBillboardComponent* Sprite = FindComponentByClass<UBillboardComponent>())
    {
        Sprite->SetHiddenInGame(true, false);
        Sprite->SetVisibility(false);
    }
}

void AAQSQuestTrigger::NotifyActorBeginOverlap(AActor* OtherActor)
{
    Super::NotifyActorBeginOverlap(OtherActor);

    APawn* OverlappingPawn = Cast<APawn>(OtherActor);
    if (OverlappingPawn && OverlappingPawn->IsPlayerControlled())
    {
        OnPlayerControlledPawnOverlap.Broadcast(OverlappingPawn);
    }
}

void AAQSQuestTrigger::ActivateTrigger()
{
    if (GetCollisionComponent())
    {
        GetCollisionComponent()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    }
}

void AAQSQuestTrigger::DeactivateTrigger()
{
    if (GetCollisionComponent())
    {
        GetCollisionComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
}
