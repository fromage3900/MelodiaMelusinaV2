// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "Components/ACFFrontTracerComponent.h"
#include "Actors/ACFCharacter.h"
#include "Game/ACFFunctionLibrary.h"
#include <CollisionQueryParams.h>
#include <Components/ActorComponent.h>
#include <GameFramework/Actor.h>
#include <Kismet/KismetSystemLibrary.h>

// Sets default values for this component's properties
UACFFrontTracerComponent::UACFFrontTracerComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = true;

    SetComponentTickEnabled(false);
}

// Called when the game starts
void UACFFrontTracerComponent::BeginPlay()
{
    Super::BeginPlay();

    SetComponentTickEnabled(false);
}

// Called every frame
void UACFFrontTracerComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    PerformTrace();
}

void UACFFrontTracerComponent::PerformTrace()
{
    AActor* actor = PerformFrontTraceSingle();
    if (IsValid(actor) && actor->GetClass()->IsChildOf(ActorToFind) && actor != currentTracedActor) {
        SetCurrentTracedActor(actor);
    } else if (currentTracedActor) {
        SetCurrentTracedActor(nullptr);
    }
}

AActor* UACFFrontTracerComponent::PerformFrontTraceSingle()
{
    const FVector start = GetComponentLocation();
    const FVector end = start + (GetOwner()->GetActorForwardVector() * TraceLength);

    TArray<AActor*> actorsToIgnore;
    actorsToIgnore.Add(UACFFunctionLibrary::GetLocalACFPlayerCharacter(this));

  /*  const EDrawDebugTrace::Type debugType = bShowDebugTrace ? EDrawDebugTrace::Type::ForOneFrame : EDrawDebugTrace::Type::None;*/

    FHitResult outResult;
    if (UKismetSystemLibrary::LineTraceSingleForObjects(
            this, start, end, ChannelsToTrace, false, actorsToIgnore, ShowDebug, outResult, true)) {
        return outResult.GetActor();
    }
    return nullptr;
}

void UACFFrontTracerComponent::StartContinuousTrace()
{
    if (ActorToFind) {
        SetComponentTickEnabled(true);
    }
}

void UACFFrontTracerComponent::StopContinuousTrace()
{
    SetComponentTickEnabled(false);
    SetCurrentTracedActor(nullptr);
}

void UACFFrontTracerComponent::SetCurrentTracedActor(AActor* newActor)
{
    currentTracedActor = newActor;
    OnNewActorDetected.Broadcast(currentTracedActor);
}
