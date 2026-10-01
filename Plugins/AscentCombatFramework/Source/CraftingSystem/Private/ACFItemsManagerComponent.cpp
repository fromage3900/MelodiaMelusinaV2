// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFItemsManagerComponent.h"
#include "ACFBuildableComponent.h"
#include "ACFCraftingComponent.h"
#include "ACFItemSystemFunctionLibrary.h"
#include "ACFVendorComponent.h"
#include "Components/ACFCurrencyComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFInventoryComponent.h"
#include "Engine/DataTable.h"
#include "GameplayTagsManager.h"
#include "Items/ACFItem.h"
#include "Kismet/KismetMathLibrary.h"
#include <GameFramework/Pawn.h>

// Sets default values for this component's properties
UACFItemsManagerComponent::UACFItemsManagerComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;

	// ...
}

// Called when the game starts
void UACFItemsManagerComponent::BeginPlay()
{
	Super::BeginPlay();
}

bool UACFItemsManagerComponent::GenerateItemsFromRules(const TArray<FACFItemGenerationRule>& generationRules, TArray<FBaseItem>& outItems)
{
	outItems.Empty();
	bool bIsSuccessful = true;

	if (generationRules.Num() == 0) {
		UE_LOG(LogTemp, Warning, TEXT("Missing generation rules! - UACFItemsManagerComponent"));
		return false;
	}

	for (auto genRule : generationRules) {
		FBaseItem outItem;
		if (GenerateItemFromRule(genRule, outItem)) {
			outItems.Add(outItem);
		}
		else {
			bIsSuccessful = false;
		}
	}
	return bIsSuccessful;
}

bool UACFItemsManagerComponent::GenerateItemFromRule(const FACFItemGenerationRule& generationRules, FBaseItem& outItem)
{
	TArray<FItemGenerationSlot> matchingItems;
	if (GetItemsDB()) {
		const auto items = GetItemsDB()->GetRowMap();
		for (const auto itemItr : items) {
			FItemGenerationSlot* itemSlot = (FItemGenerationSlot*)itemItr.Value;
			if (itemSlot) {
				if (DoesSlotMatchesRule(generationRules, *itemSlot)) {
					matchingItems.Add(*itemSlot);
				}
			}
			else {
				return false;
			}
		}

		if (matchingItems.Num() == 0) {
			UE_LOG(LogTemp, Warning, TEXT("No Matching Items in DB! - UACFItemsManagerComponent"));
			return false;
		}

		const int32 selectedSlot = FMath::RandRange(0, matchingItems.Num() - 1);
		const int32 selectedCount = FMath::RandRange(generationRules.MinItemCount, generationRules.MaxItemCount);
		if (matchingItems.IsValidIndex(selectedSlot) && selectedCount > 0) {
			const TSubclassOf<UACFItem> ItemClass = matchingItems[selectedSlot].ItemClass.LoadSynchronous();
			if (ItemClass) {
				outItem = FBaseItem(ItemClass, selectedCount);
				return true;
			}
		}
	}
	else {
		UE_LOG(LogTemp, Error, TEXT("No  ItemsDB! in ItemsManager!!!!- UACFItemsManagerComponent"));
	}
	return false;
}

bool UACFItemsManagerComponent::DoesSlotMatchesRule(const FACFItemGenerationRule& generationRules, const FItemGenerationSlot& item)
{
	return (
		(item.Category == generationRules.Category || UGameplayTagsManager::Get().RequestGameplayTagChildren(generationRules.Category).HasTag(item.Category))
		&& (item.Rarity == generationRules.Rarity || UGameplayTagsManager::Get().RequestGameplayTagChildren(generationRules.Rarity).HasTag(item.Rarity)));
}


void UACFItemsManagerComponent::SellItemsToVendor_Implementation(const FInventoryItem& itemTobeSold, APawn* instigator, int32 count /*= 1*/, UACFVendorComponent* vendorComp)
{
	if (!vendorComp) {
		return;
	}

	if (!vendorComp->CanPawnSellItemFromHisInventory(itemTobeSold, instigator, count)) {
		return;
	}

	UACFEquipmentComponent* equipComp = vendorComp->GetPawnEquipment(instigator);
	UACFCurrencyComponent* currencyComp = vendorComp->GetPawnCurrencyComponent(instigator);
	FItemDescriptor itemData;
	if (!UACFItemSystemFunctionLibrary::GetItemData(itemTobeSold.ItemClass, itemData)) {
		return;
	}
	const float totalCost = itemData.CurrencyValue * count * vendorComp->GetVendorPriceMultiplierOnBuy();
	if (equipComp && currencyComp) {
		// Capture the live inventory item (with UACFItem* and fragment state)
		// BEFORE RemoveItem destroys the entry.
		FInventoryItem liveItem;
		equipComp->GetItemByGuid(itemTobeSold.GetItemGuid(), liveItem);

		equipComp->RemoveItem(itemTobeSold, count);
		currencyComp->AddCurrency(totalCost);
		if (vendorComp->VendorUsesCurrency() && vendorComp->GetVendorCurrencyComp()) {
			vendorComp->GetVendorCurrencyComp()->RemoveCurrency(totalCost);
		}

		// Transfer the live item with its UACFItem* pointer intact
		FInventoryItem toBeSold = liveItem;
		toBeSold.Count = count;
		vendorComp->AddInventoryItem(toBeSold);
		OnItemSold.Broadcast(toBeSold);
	}
}

void UACFItemsManagerComponent::BuyItems_Implementation(const FInventoryItem& item, APawn* instigator, UACFVendorComponent* vendorComp)
{
	if (!vendorComp) {
		return;
	}

	if (!vendorComp->CanPawnBuyItems(item, instigator)) {
		return;
	}
	UACFEquipmentComponent* equipComp = vendorComp->GetPawnEquipment(instigator);

	BuyItemsFromVendor(vendorComp, item, equipComp);
	return;
}

void UACFItemsManagerComponent::BuyItemsFromVendor(UACFVendorComponent* vendorComp, const FInventoryItem& item, UACFEquipmentComponent* equipComp)
{
	FItemDescriptor itemToBuyDesc;
	if (vendorComp->TryGetItemDescriptor(item, itemToBuyDesc)) {
		const float totalCost = (itemToBuyDesc.CurrencyValue * item.Count * vendorComp->GetVendorPriceMultiplierOnSell());
		//UACFCurrencyComponent* currencyComp = vendorComp->GetPawnCurrencyComponent(instigator);
		if (equipComp) {
			// Capture the live UACFItem* from the vendor's inventory BEFORE removal
			FInventoryItem vendorItem;
			vendorComp->GetItemByGuid(item.GetItemGuid(), vendorItem);

			equipComp->RemoveCurrency(totalCost);

			// Use AddInventoryItem (takes FInventoryItem) so the Item* pointer
			// flows through to Internal_AddInventoryItem and gets adopted.
			FInventoryItem toTransfer = vendorItem;
			toTransfer.Count = item.Count;
			equipComp->AddInventoryItem(toTransfer);

			vendorComp->RemoveItem(item, item.Count);
			if (vendorComp->GetVendorCurrencyComp()) {
				vendorComp->GetVendorCurrencyComp()->AddCurrency(totalCost);
			}
			OnItemPurchased.Broadcast(item);
			return;
		}
	}
	return;
}


void UACFItemsManagerComponent::CraftItem_Implementation(const FACFCraftingRecipe& ItemToCraft, APawn* instigator, class UACFCraftingComponent* craftingComp)
{
	if (!craftingComp) {
		return;
	}

	if (!craftingComp->CanPawnCraftItem(ItemToCraft, instigator)) {
		return;
	}
	UACFEquipmentComponent* equipComp = craftingComp->GetPawnEquipment(instigator);

	if (!equipComp) {
		return;
	}

	craftingComp->GetPawnCurrencyComponent(instigator)->RemoveCurrency(craftingComp->GetVendorPriceMultiplierOnSell() * ItemToCraft.CraftingCost);
	equipComp->ConsumeItems(ItemToCraft.RequiredItems);
	equipComp->AddItemToInventoryByClass(ItemToCraft.OutputItem.ItemClass, ItemToCraft.OutputItem.Count);
	OnItemCrafted.Broadcast(ItemToCraft);
	return;
}

void UACFItemsManagerComponent::UpgradeItem_Implementation(const FInventoryItem& itemToUpgrade, APawn* instigator, class UACFCraftingComponent* craftingComp)
{
	if (!craftingComp) {
		return;
	}

	if (!craftingComp->CanPawnUpgradeItem(itemToUpgrade, instigator)) {
		return;
	}

	UACFEquipmentComponent* equipComp = craftingComp->GetPawnEquipment(instigator);
	UACFCurrencyComponent* currencyComp = craftingComp->GetPawnCurrencyComponent(instigator);
	if (equipComp && currencyComp) {

		FItemDescriptor itemInfo;
		if (!UACFItemSystemFunctionLibrary::GetItemData(itemToUpgrade.ItemClass, itemInfo)) {
			return;
		}

		if (itemInfo.NextLevelClass) {
			equipComp->ConsumeItems(itemInfo.RequiredItemsToUpgrade);
			currencyComp->RemoveCurrency(craftingComp->GetVendorPriceMultiplierOnSell() * itemInfo.UpgradeCurrencyCost);
			equipComp->RemoveItem(itemToUpgrade, 1);
			equipComp->AddItemToInventoryByClass(itemInfo.NextLevelClass, 1);
			OnItemUpgraded.Broadcast(itemToUpgrade);
			return;
		}
	}
	return;
}

void UACFItemsManagerComponent::DropItem_Implementation(UACFEquipmentComponent* targetComponent, const FInventoryItem& itemToDrop, int32 count /*= 1*/)
{
	if (targetComponent) {
		targetComponent->DropItem(itemToDrop, count);
	}
}

void UACFItemsManagerComponent::UseInventoryItem_Implementation(UACFEquipmentComponent* targetComponent, const FInventoryItem& itemToUse)
{
	if (targetComponent) {
		targetComponent->UseInventoryItem(itemToUse);
	}
}

void UACFItemsManagerComponent::EquipItemFromInventoryInSlot_Implementation(UACFEquipmentComponent* targetComponent, const FInventoryItem& itemToUse, const FGameplayTag& slot)
{
	if (targetComponent) {
		targetComponent->EquipItemFromInventoryInSlot(itemToUse, slot);
	}
}

void UACFItemsManagerComponent::ConstructBuildable_Implementation(APawn* instigator, class UACFBuildableComponent* buildComp)
{
	if (buildComp && instigator && buildComp->CanBeBuildByPawn(instigator)) {
		buildComp->GetPawnCurrencyComponent(instigator)->RemoveCurrency(buildComp->GetBuildingCost());
		TArray<FBaseItem> outItems;
		buildComp->GetBuildingRequirements(outItems);
		buildComp->GetPawnEquipment(instigator)->ConsumeItems(outItems);
		buildComp->SetBuildingState(EBuildableState::EBuilded);
	}
}
