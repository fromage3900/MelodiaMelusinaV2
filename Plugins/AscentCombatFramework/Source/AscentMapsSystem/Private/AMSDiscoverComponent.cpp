// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSDiscoverComponent.h"
#include "AMSMapArea.h"
#include "AMSMapSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include <Engine/GameInstance.h>

// Sets default values for this component's properties
UAMSDiscoverComponent::UAMSDiscoverComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = true;

    // ...
}

// Called when the game starts
void UAMSDiscoverComponent::BeginPlay()
{
    Super::BeginPlay();

    // ...
}

// Called every frame
void UAMSDiscoverComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!GetOwner())
        return;

    const UGameInstance* GameInstance = UGameplayStatics::GetGameInstance(this);
    if (!GameInstance)
        return;

    UAMSMapSubsystem* mapSubsystem = GameInstance->GetSubsystem<UAMSMapSubsystem>();
    if (!mapSubsystem || !mapSubsystem->GetCurrentMapArea())
        return;

    const FVector actorLocation = GetOwner()->GetActorLocation();
    mapSubsystem->GetCurrentMapArea()->UpdateFogOfWar(actorLocation);
}
