// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once


#include "Components/ACFStorageComponent.h"
#include "CoreMinimal.h"

#include "ACFVendorComponent.generated.h"

class UACFCurrencyComponent;

/**
 *
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CRAFTINGSYSTEM_API UACFVendorComponent : public UACFStorageComponent {
    GENERATED_BODY()

public:
    UACFVendorComponent();

    /*------------------- CHECKS -----------------------------------*/

    /*Returns the maximum amount of itemsToBuy that Buyer can buy from this seller considering his currency amount*/
    UFUNCTION(BlueprintCallable, Category = "ACF | Checks")
    int32 HowManyItemsCanBuy(const FBaseItem& itemsToBuy, const APawn* buyer) const;

    /*Returns the maximum amount of itemsToSell that Seller can sell considering to this seller's currency amount.
    Always the player amount if UseVendorCurrencyComponent is set to false */
    UFUNCTION(BlueprintCallable, Category = "ACF | Checks")
    int32 HowManyItemsCanSell(const FBaseItem& itemsToSell, const APawn* seller) const;

    UFUNCTION(BlueprintCallable, Category = "ACF | Checks")
    bool CanPawnBuyItems(const FInventoryItem& itemsToBuy, const APawn* buyer) const;

    UFUNCTION(BlueprintCallable, Category = "ACF | Checks")
    bool CanPawnSellItemFromHisInventory(const FInventoryItem& itemTobeSold, const APawn* seller, int32 count = 1) const;

    /*------------------- SERVER SIDE -----------------------------------*/

    UFUNCTION(BlueprintCallable, Category = "ACF | Vendor")
    void BuyItems(const FInventoryItem& item, APawn* instigator);

    UFUNCTION(BlueprintCallable, Category = "ACF | Vendor")
    void SellItemsToVendor(const FInventoryItem& itemTobeSold, APawn* instigator, int32 count = 1);

    /*-------------------PLAYER STUFF-----------------------------------*/

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    UACFItemsManagerComponent* GetItemsManager() const;

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    float GetVendorCurrency() const;

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    class UACFCurrencyComponent* GetVendorCurrencyComp() const
    {
        return sellerCurrency;
    }

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    float GetVendorPriceMultiplierOnBuy() const
    {
        return PriceMultiplierOnBuy;
    }

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    float GetVendorPriceMultiplierOnSell() const
    {
        return PriceMultiplierOnSell;
    }

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    bool VendorUsesCurrency() const
    {
        return bUseVendorCurrencyComponent;
    }

    UFUNCTION(BlueprintCallable, Category = "ACF | Getters")
    float GetItemCostPerUnit(const TSubclassOf<UACFItem>& itemClass) const;

    /*------------------- FUNCTION LIBRAR WRAPPERS-----------------------------------*/

    UFUNCTION(BlueprintCallable, Category = "ACF | Library")
    bool TryGetItemDescriptor(const FBaseItem& item, FItemDescriptor& outItemDescriptor) const;

    UFUNCTION(BlueprintCallable, Category = "ACF | Library")
    bool TryGetItemDescriptorByClass(const TSubclassOf<UACFItem>& ItemClass, FItemDescriptor& outItemDescriptor) const;

protected:
    /*The multiplier this vendor is going to apply to the item value when selling to the player*/
    /*With this set to 0 this can be used as a chest that can be gathered without removing currencies*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float PriceMultiplierOnSell = 1.f;

    /*If this is set to false, this Vendor can purchase unlimited items from the interacting player*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    bool bUseVendorCurrencyComponent = true;

    /*The multiplier this vendor is going to apply to the item value when buying from the player*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float PriceMultiplierOnBuy = 0.2f;

    // Called when the game starts
    virtual void BeginPlay() override;

private:

    TObjectPtr<UACFCurrencyComponent> sellerCurrency;
};
