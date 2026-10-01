   // // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFConqueringElementComponent.h"
#include "ACFAssaultPoint.h"
#include "ACFConquestFunctionLibrary.h"

// Sets default values for this component's properties
UACFConqueringElementComponent::UACFConqueringElementComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    // ...
}

// Called when the game starts
void UACFConqueringElementComponent::BeginPlay()
{
    Super::BeginPlay();

    relatedPoint = UACFConquestFunctionLibrary::GetAssaultPoint(this, AssaultPointTag);
    if (relatedPoint && !relatedPoint->OnConquerStateChanged.IsAlreadyBound(this, &UACFConqueringElementComponent::HandleStateChanged)) {
        relatedPoint->OnConquerStateChanged.AddDynamic(this, &UACFConqueringElementComponent::HandleStateChanged);
        HandleStateChanged(relatedPoint->GetConqueringState());
    }
}

void UACFConqueringElementComponent::HandleStateChanged(const EConqueredState& newState)
{  
    if (bShowOnlyInDisplayState) {
        if (DisplayInState == newState) {
            GetOwner()->SetActorHiddenInGame(false);
            GetOwner()->SetActorEnableCollision(true);
        } else {
            GetOwner()->SetActorHiddenInGame(true);
            GetOwner()->SetActorEnableCollision(false);
        }
    }
    OnConquerStateChanged.Broadcast(newState);
}
