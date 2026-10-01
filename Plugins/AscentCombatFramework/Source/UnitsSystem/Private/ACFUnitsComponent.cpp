// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFUnitsComponent.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFGroupAIComponent.h"
#include "Net/UnrealNetwork.h"

// Sets default values for this component's properties
UACFUnitsComponent::UACFUnitsComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    // ...
}

// Called when the game starts
void UACFUnitsComponent::BeginPlay()
{
    Super::BeginPlay();

    // ...
}

void UACFUnitsComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFUnitsComponent, Units);
}

void UACFUnitsComponent::AddUnit(const FBaseUnit& unit)
{
    Units.Add(unit);
   
    OnUnitAdded.Broadcast(unit);
    OnUnitsChanged.Broadcast(Units);
}

bool UACFUnitsComponent::RemoveUnit(const FBaseUnit& unit)
{
    const int32 unitIndex = Units.Find(unit);

    if (Units.IsValidIndex(unitIndex)) {
        const FBaseUnit removedUnit = Units[unitIndex];
        Units.RemoveAt(unitIndex);
        OnUnitRemoved.Broadcast(removedUnit);
        OnUnitsChanged.Broadcast(Units);
        return true;
    }
    return false;
}

bool UACFUnitsComponent::MoveUnitToGroup(const FBaseUnit& unit, UACFGroupAIComponent* groupAI)
{
    if (groupAI && Units.Contains(unit) && groupAI->AddAIToSpawn(FAISpawnInfo(unit))) {
        RemoveUnit(unit);
        return true;
    }
    return false;
}

bool UACFUnitsComponent::MoveUnitFromGroup(const FBaseUnit& unit, UACFGroupAIComponent* groupAI)
{
    if (groupAI && groupAI->RemoveAIToSpawnUnit(unit)) {
        AddUnit(unit);
        return true;
    }
    return false;
}

void UACFUnitsComponent::OnRepUnits()
{
    OnUnitsChanged.Broadcast(Units);
}
