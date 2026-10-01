// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFVendorComponent.h"
#include "ACFItemSystemFunctionLibrary.h"
#include "ACFItemsManagerComponent.h"
#include "Components/ACFCurrencyComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFInventoryComponent.h"
#include "Components/ACFStorageComponent.h"
#include "Items/ACFItem.h"
#include <GameFramework/Pawn.h>
#include <Kismet/GameplayStatics.h>

UACFVendorComponent::UACFVendorComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
}

// Called when the game starts
void UACFVendorComponent::BeginPlay()
{
    Super::BeginPlay();

    sellerCurrency = GetOwner()->FindComponentByClass<UACFCurrencyComponent>();
    if (!sellerCurrency && bUseVendorCurrencyComponent) {
        const APawn* pawn = Cast<APawn>(GetOwner());
        if (pawn) {
            sellerCurrency = pawn->GetController()->FindComponentByClass<UACFCurrencyComponent>();
        }
    }

    if (!sellerCurrency && bUseVendorCurrencyComponent) {
        UE_LOG(LogTemp, Error, TEXT("Seller with No Currencies! - UACFVendorComponent::BeginPlay"))
    }
}

int32 UACFVendorComponent::HowManyItemsCanBuy(const FBaseItem& itemsToBuy, const APawn* buyer) const
{
    FItemDescriptor outItem;

    if (TryGetItemDescriptor(itemsToBuy, outItem)) {
        const float pawnCurrency = GetPawnCurrency(buyer);
        const float unitCost = GetItemCostPerUnit(itemsToBuy.ItemClass);
        if (unitCost <= 0.f) {
            return itemsToBuy.Count;
        }
        const int32 maxAmount = trunc(pawnCurrency / unitCost);
        return FMath::Min(maxAmount, itemsToBuy.Count);
    }

    return 0;
}

int32 UACFVendorComponent::HowManyItemsCanSell(const FBaseItem& itemsToSell, const APawn* seller) const
{
    FItemDescriptor outItem;

    if (!bUseVendorCurrencyComponent) {
        return itemsToSell.Count;
    }
    if (TryGetItemDescriptor(itemsToSell, outItem) && sellerCurrency) {

        const float pawnCurrency = sellerCurrency->GetCurrentCurrencyAmount();
        const int32 maxAmount = trunc(pawnCurrency / GetItemCostPerUnit(itemsToSell.ItemClass));
        return FMath::Min(maxAmount, itemsToSell.Count);
    }

    return 0;
}

bool UACFVendorComponent::CanPawnBuyItems(const FInventoryItem& itemsToBuy, const APawn* buyer) const
{
    if (!buyer) {
        return false;
    }

    const TArray<FBaseItem> itemsToBuyArray = { FBaseItem(itemsToBuy) };
    if (!HasEnoughItemsOfType(itemsToBuyArray)) {
        return false;
    }

    const int32 totalCount = GetTotalCountOfItemsByClass(itemsToBuy.ItemClass);
    if (totalCount >= itemsToBuy.Count) {
        if (PriceMultiplierOnSell == 0.f) {
            return true;
        }
        FItemDescriptor itemToBuyDesc;
        if (TryGetItemDescriptor(itemsToBuy, itemToBuyDesc)) {
            return (itemToBuyDesc.CurrencyValue * itemsToBuy.Count * PriceMultiplierOnSell) <= GetPawnCurrency(buyer);
        }
    }

    return false;
}

bool UACFVendorComponent::CanPawnSellItemFromHisInventory(const FInventoryItem& itemTobeSold, const APawn* seller, int32 count /*= 1*/) const
{
    UACFEquipmentComponent* equipComp = GetPawnEquipment(seller);
    if (!equipComp) {
        return false;
    }

    if (bUseVendorCurrencyComponent && !sellerCurrency) {
        return false;
    }
    FItemDescriptor itemInfo;
    if (!UACFItemSystemFunctionLibrary::GetItemData(itemTobeSold.ItemClass, itemInfo)) {
        return false;
    }
    if (bUseVendorCurrencyComponent) {

        return itemTobeSold.Count >= count && itemInfo.CurrencyValue * count * PriceMultiplierOnBuy <= sellerCurrency->GetCurrentCurrencyAmount();
    }

    return itemTobeSold.Count >= count && itemInfo.CurrencyValue;
}

/* ----------- TO SERVER---------------*/

void UACFVendorComponent::BuyItems(const FInventoryItem& item, APawn* instigator)
{
    if (GetItemsManager()) {
        GetItemsManager()->BuyItems(item, instigator, this);
    }
}

void UACFVendorComponent::SellItemsToVendor(const FInventoryItem& itemTobeSold, APawn* instigator, int32 count /*= 1 */)
{
    if (GetItemsManager()) {
        GetItemsManager()->SellItemsToVendor(itemTobeSold, instigator, count, this);
    }
}

/*-------------------PLAYER STUFF-----------------------------------*/

UACFItemsManagerComponent* UACFVendorComponent::GetItemsManager() const
{
    const APlayerController* gameState = UGameplayStatics::GetPlayerController(this, 0);
    if (gameState) {
        return gameState->FindComponentByClass<UACFItemsManagerComponent>();
    }
    return nullptr;
}

float UACFVendorComponent::GetVendorCurrency() const
{
    if (sellerCurrency) {
        return sellerCurrency->GetCurrentCurrencyAmount();
    }
    return -1.f;
}

bool UACFVendorComponent::TryGetItemDescriptor(const FBaseItem& item, FItemDescriptor& outItemDescriptor) const
{
    if (item.ItemClass) {
        return TryGetItemDescriptorByClass(item.ItemClass, outItemDescriptor);
    }
    return false;
}

bool UACFVendorComponent::TryGetItemDescriptorByClass(const TSubclassOf<UACFItem>& ItemClass, FItemDescriptor& outItemDescriptor) const
{
    return UACFItemSystemFunctionLibrary::GetItemData(ItemClass, outItemDescriptor);
}

float UACFVendorComponent::GetItemCostPerUnit(const TSubclassOf<UACFItem>& itemClass) const
{
    FItemDescriptor outItem;

    if (TryGetItemDescriptorByClass(itemClass, outItem)) {
        return outItem.CurrencyValue * PriceMultiplierOnSell;
    }
    return -1.f;
}
