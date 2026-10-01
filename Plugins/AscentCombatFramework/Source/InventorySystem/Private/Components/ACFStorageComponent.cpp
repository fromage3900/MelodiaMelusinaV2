// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFStorageComponent.h"
#include "ACFItemSystemFunctionLibrary.h"
#include "Components/ACFCurrencyComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Items/ACFItem.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "Net/UnrealNetwork.h"
#include <GameFramework/Pawn.h>

// Sets default values for this component's properties
UACFStorageComponent::UACFStorageComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;

	SetIsReplicatedByDefault(true);
	// ...
}

// Called when the game starts
void UACFStorageComponent::BeginPlay()
{
	Super::BeginPlay();
	if (GetOwner()->HasAuthority()) {
		AddItems(Items);
		CheckEmpty();
	} else {
		OnInventoryChanged.AddDynamic(this, &UACFStorageComponent::OnInventoryChangedClient);
	}
}

void UACFStorageComponent::OnComponentLoaded_Implementation()
{
}

void UACFStorageComponent::OnComponentSaved_Implementation()
{
}



void UACFStorageComponent::AddItems_Implementation(const TArray<FBaseItem>& inItems)
{
	for (const auto& item : inItems) {
		AddItem(item);
	}
}

void UACFStorageComponent::AddItem_Implementation(const FBaseItem& inItem)
{
	AddItemToInventory(inItem, false);
}

void UACFStorageComponent::CheckEmpty()
{
	if (IsStorageEmpty()) {
		OnStorageEmpty.Broadcast();
	}
}

bool UACFStorageComponent::IsStorageEmpty()
{
	return GetInventoryListConst().IsEmpty() && GetCurrentCurrencyAmount() <= 0;
}

bool UACFStorageComponent::CanPawnGatherItems(const APawn* pawn, const FBaseItem& itemsToGather)
{
	UACFEquipmentComponent* equipComp = GetPawnEquipment(pawn);
	if (equipComp) {
		return equipComp->NumberOfItemCanTake(itemsToGather.ItemClass) >= itemsToGather.Count;
	}
	return false;
}



UACFCurrencyComponent* UACFStorageComponent::GetPawnCurrencyComponent(const APawn* pawn) const
{
	return UACFItemSystemFunctionLibrary::GetPawnCurrencyComponent(pawn);
}

float UACFStorageComponent::GetPawnCurrency(const APawn* pawn) const
{
	return UACFItemSystemFunctionLibrary::GetPawnCurrency(pawn);
}

class UACFEquipmentComponent* UACFStorageComponent::GetPawnEquipment(const APawn* pawn) const
{
	return UACFItemSystemFunctionLibrary::GetPawnEquipment(pawn);
}

TArray<FInventoryItem> UACFStorageComponent::GetPawnInventory(const APawn* pawn) const
{
	const UACFEquipmentComponent* equipComp = GetPawnEquipment(pawn);
	if (equipComp) {
		return equipComp->GetInventory();
	}
	return TArray<FInventoryItem>();
}

void UACFStorageComponent::HandleCurrencyChanged()
{
	CheckEmpty();
}

void UACFStorageComponent::HandleItemRemoved(const FInventoryItem& item, int32 count /* = 1 */)
{
	Super::HandleItemRemoved(item, count);
	CheckEmpty();
}

void UACFStorageComponent::OnInventoryChangedClient()
{
	CheckEmpty();
}
