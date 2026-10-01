// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFConqueringComponent.h"
#include "ACFAssaultPoint.h"
#include "Kismet/GameplayStatics.h"
#include "Net/UnrealNetwork.h"

// Sets default values for this component's properties
UACFConqueringComponent::UACFConqueringComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    SetIsReplicatedByDefault(true);
    // ...
}

// Called when the game starts
void UACFConqueringComponent::BeginPlay()
{
    Super::BeginPlay();
}

void UACFConqueringComponent::SetConqueringState_Implementation(const FGameplayTag& point, const EConqueredState& newState)
{
    bConquerInProgress = newState == EConqueredState::EConquerInProgress;
    OnConquerStateChanged.Broadcast(point, newState);
}

EConqueredState UACFConqueringComponent::GetConqueringStateForPoint(const FGameplayTag& point) const
{
    AACFAssaultPoint* assPoint = GetAssaultPoint(point);
    if (assPoint) {
        return assPoint->GetConqueringState();
    }
    UE_LOG(LogTemp, Warning, TEXT("Missing Assault Point! - UACFConqueringComponent::GetConqueringStateForPoint "));

    return EConqueredState::ENotConquered;
}

bool UACFConqueringComponent::IsAnyConquerInProgress() const
{
    return bConquerInProgress;
}

class AACFAssaultPoint* UACFConqueringComponent::GetAssaultPoint(const FGameplayTag& point) const
{
    TArray<AActor*> outActors;
    UGameplayStatics::GetAllActorsOfClass(this, AACFAssaultPoint::StaticClass(), outActors);
    for (AActor* actor : outActors) {
        AACFAssaultPoint* assPoint = Cast<AACFAssaultPoint>(actor);
        if (assPoint && assPoint->GetAssaultPointTag() == point) {
            return assPoint;
        }
    }
    UE_LOG(LogTemp, Warning, TEXT("Missing Assault Point! -  UACFConqueringComponent::GetAssaultPoint"));

    return nullptr;
}
