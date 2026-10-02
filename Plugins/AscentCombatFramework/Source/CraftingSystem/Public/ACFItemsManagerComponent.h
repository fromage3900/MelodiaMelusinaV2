// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCraftRecipeDataAsset.h"
#include "ACFItemTypes.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFInventoryComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "Items/ACFItem.h"

#include "ACFItemsManagerComponent.generated.h"

struct FInventoryItem;
class UACFVendorComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemCrafted, const FACFCraftingRecipe&, recipe);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemSold, const FInventoryItem&, item);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemPurchased, const FInventoryItem&, item);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemUpgraded, const FInventoryItem&, item);

UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class CRAFTINGSYSTEM_API UACFItemsManagerComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFItemsManagerComponent();

    /**
     * Returns the Items DataTable used for item generation
     * @return The item database DataTable.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UDataTable* GetItemsDB() const { return ItemsDB; }

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, meta = (RowType = "ItemGenerationSlot"), Category = ACF)
    UDataTable* ItemsDB;

public:
    /*------------------- SERVER SIDE -----------------------------------*/

    /**
     * Server RPC to buy an item from a vendor
     * @param item - The item to buy.
     * @param instigator - The pawn performing the action.
     * @param vendorComp - The vendor component handling the transaction.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void BuyItems(const FInventoryItem& item, APawn* instigator, class UACFVendorComponent* vendorComp);

    /**
     * Server RPC to sell items to a vendor
     * @param itemTobeSold - The item to sell.
     * @param instigator - The pawn performing the action.
     * @param count - Quantity of items to sell.
     * @param vendorComp - The vendor component receiving the item.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void SellItemsToVendor(const FInventoryItem& itemTobeSold, APawn* instigator, int32 count, class UACFVendorComponent* vendorComp);

    /**
     * Server RPC to craft an item using a recipe
     * @param ItemToCraft - The recipe of the item to craft.
     * @param instigator - The pawn performing the crafting.
     * @param craftingComp - The crafting component handling the logic.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void CraftItem(const FACFCraftingRecipe& ItemToCraft, APawn* instigator, class UACFCraftingComponent* craftingComp);

    /**
     * Server RPC to upgrade an existing item
     * @param itemToUpgrade - The item to upgrade.
     * @param instigator - The pawn performing the upgrade.
     * @param craftingComp - The crafting component applying the upgrade.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void UpgradeItem(const FInventoryItem& itemToUpgrade, APawn* instigator, class UACFCraftingComponent* craftingComp);

    /**
     * Server RPC to drop an item from the inventory
     * @param targetComponent - The equipment component from which the item will be dropped.
     * @param itemToDrop - The inventory item to drop.
     * @param count - The number of items to drop. Defaults to 1.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void DropItem(UACFEquipmentComponent* targetComponent, const FInventoryItem& itemToDrop, int32 count = 1);

    /**
     * Server RPC to use an item directly from the inventory
     * @param targetComponent - The equipment component that will use the item.
     * @param itemToUse - The inventory item to use.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void UseInventoryItem(UACFEquipmentComponent* targetComponent, const FInventoryItem& itemToUse);

    /**
     * Server RPC to equip an inventory item into a specific slot
     * @param targetComponent - The equipment component where the item will be equipped.
     * @param itemToUse - The inventory item to equip.
     * @param slot - The gameplay tag identifying the equipment slot.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void EquipItemFromInventoryInSlot(UACFEquipmentComponent* targetComponent, const FInventoryItem& itemToUse, const FGameplayTag& slot);

    /**
     * Server RPC to construct a buildable object
     * @param instigator - The pawn initiating the construction.
     * @param buildComp - The buildable component managing the construction.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void ConstructBuildable(APawn* instigator, class UACFBuildableComponent* buildComp);

    /* Generates an array of FBaseItem matching the provided rules by selecting them from the provided ItemsDB
    returns true only if we are able to find matching items for ALL the provided rules*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool GenerateItemsFromRules(const TArray<FACFItemGenerationRule>& generationRules, TArray<FBaseItem>& outItems);

    /* Generates an  FBaseItem matching the provide rule by selecting it from the provided ItemsDB
    returns true if at least one item is found*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool GenerateItemFromRule(const FACFItemGenerationRule& generationRules, FBaseItem& outItems);

    /* Returns true if the provided itemSlot matches the provided slot rules*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool DoesSlotMatchesRule(const FACFItemGenerationRule& generationRules, const FItemGenerationSlot& item);

    void BuyItemsFromVendor(UACFVendorComponent* vendorComp, const FInventoryItem& item, UACFEquipmentComponent* equipComp);

    /**
     * Event triggered when an item is crafted successfully
     */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnItemCrafted OnItemCrafted;

    /**
     * Event triggered when an item is sold to a vendor
     */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnItemSold OnItemSold;

    /**
     * Event triggered when an item is purchased from a vendor
     */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnItemPurchased OnItemPurchased;

    /**
     * Event triggered when an item is successfully upgraded
     */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnItemUpgraded OnItemUpgraded;
};
