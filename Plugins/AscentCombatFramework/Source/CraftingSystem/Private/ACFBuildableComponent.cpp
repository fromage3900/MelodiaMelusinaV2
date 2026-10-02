// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFBuildableComponent.h"
#include "Components/ACFCurrencyComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include <Kismet/GameplayStatics.h>
#include "ACFItemsManagerComponent.h"
#include <Net/UnrealNetwork.h>
#include "ACFItemSystemFunctionLibrary.h"

// Sets default values for this component's properties
UACFBuildableComponent::UACFBuildableComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    BuildingState = EBuildableState::ENotBuilded;
    BuildingCost = 0.f;
    SetIsReplicatedByDefault(true);
}

void UACFBuildableComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFBuildableComponent, BuildingState);
}

// Called when the game starts
void UACFBuildableComponent::BeginPlay()
{
    Super::BeginPlay();
   // SetBuildingState(BuildingState);

    // ...
}

void UACFBuildableComponent::OnComponentLoaded_Implementation()
{
    SetBuildingState(BuildingState);
}

void UACFBuildableComponent::OnComponentSaved_Implementation()
{
}

void UACFBuildableComponent::SetBuildingState(const EBuildableState newState)
{
    BuildingState = newState;
    OnBuildableStatusChanged.Broadcast(newState);
 }

float UACFBuildableComponent::GetPawnCurrency(const APawn* pawn) const
{
    return UACFItemSystemFunctionLibrary::GetPawnCurrency(pawn);
}

class UACFEquipmentComponent* UACFBuildableComponent::GetPawnEquipment(const APawn* pawn) const
{
    return UACFItemSystemFunctionLibrary::GetPawnEquipment(pawn);
}

UACFCurrencyComponent* UACFBuildableComponent::GetPawnCurrencyComponent(const APawn* pawn) const
{
    return UACFItemSystemFunctionLibrary::GetPawnCurrencyComponent(pawn);
}


UACFItemsManagerComponent* UACFBuildableComponent::GetItemsManager() const
{
    const APlayerController* gameState = UGameplayStatics::GetPlayerController(this, 0);
    if (gameState) {
        return gameState->FindComponentByClass<UACFItemsManagerComponent>();
    }
    return nullptr;
}


bool UACFBuildableComponent::CanBeBuildByPawn(const APawn* pawn) 
{
    UACFEquipmentComponent* equipComp = GetPawnEquipment(pawn);
    const float pawnCurrency = GetPawnCurrency(pawn);
    if (equipComp) {
        return equipComp->HasEnoughItemsOfType(BuildingRequirements) && pawnCurrency >= BuildingCost;
    }
    return false;
}

void UACFBuildableComponent::Build(APawn* pawn)
{
    if (GetItemsManager()) {
        GetItemsManager()->ConstructBuildable(pawn, this);
    }
}

void UACFBuildableComponent::OnRep_BuildingState()
{
    ClientsOnBuildableStatusChanged.Broadcast(BuildingState);
}
