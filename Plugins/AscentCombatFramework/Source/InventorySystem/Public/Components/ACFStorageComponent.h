// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFInventoryComponent.h"
#include "ACFItemTypes.h"
#include "Components/ACFCurrencyComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Items/ACFItem.h"

#include "ACFStorageComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemsChanged, const TArray<FBaseItem>&, currentItems);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnStorageEmpty);

/**
 * Storage component that manages items and currency within an inventory system.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class INVENTORYSYSTEM_API UACFStorageComponent : public UACFInventoryComponent {
    GENERATED_BODY()

public:
    /** Sets default values for this component's properties */
    UACFStorageComponent();

protected:
    /** Called when the game starts */
    virtual void BeginPlay() override;

    /** The array of stored items */
    UPROPERTY(EditAnywhere, Category = ACF)
    TArray<FBaseItem> Items;

    /** Called when the component is loaded */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnComponentLoaded();

    /** Called when the component is saved */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnComponentSaved();

public:
    /** Adds a single item to storage */
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void AddItem(const FBaseItem& inItems);

    /** Adds multiple items to storage */
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void AddItems(const TArray<FBaseItem>& inItems);

    /** Checks if a pawn can gather a specific item */
    UFUNCTION(BlueprintPure, Category = "ACF | Checks")
    bool CanPawnGatherItems(const APawn* pawn, const FBaseItem& itemsToGather);


    /** Retrieves the currency component of a given pawn */
    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    class UACFCurrencyComponent* GetPawnCurrencyComponent(const APawn* pawn) const;

    /** Retrieves the current currency amount of a given pawn */
    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    float GetPawnCurrency(const APawn* pawn) const;

    /** Retrieves the equipment component of a given pawn */
    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    class UACFEquipmentComponent* GetPawnEquipment(const APawn* pawn) const;

    /** Retrieves the inventory items of a given pawn */
    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    TArray<FInventoryItem> GetPawnInventory(const APawn* pawn) const;

    /** Checks if the storage is empty */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsStorageEmpty();

    /** Event triggered when storage becomes empty */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnStorageEmpty OnStorageEmpty;

    /** Handles currency changes in storage */
    virtual void HandleCurrencyChanged() override;

    virtual void HandleItemRemoved(const FInventoryItem& item, int32 count /* = 1 */) override;

private:
    /** Checks if storage is empty and triggers appropriate events */
    void CheckEmpty();

    UFUNCTION()
    void OnInventoryChangedClient();
};
