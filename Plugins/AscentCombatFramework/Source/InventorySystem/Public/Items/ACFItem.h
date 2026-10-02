// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFItemFragment.h"
#include "ACFItemTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameFramework/Actor.h"
#include <AbilitySystemComponent.h>
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>
#include <Net/Serialization/FastArraySerializer.h>
#include <Engine/StaticMesh.h>

#include "ACFItem.generated.h"

class UGameplayEffect;
struct FGameplayEffectSpecHandle;
class AACFItemActor;

/**
 *
 */
USTRUCT(BlueprintType)
struct INVENTORYSYSTEM_API FBaseItem : public FFastArraySerializerItem {

public:
	GENERATED_BODY()

	FBaseItem() { ItemGuid = FGuid::NewGuid(); };

	FBaseItem(const TSubclassOf<class UACFItem>& inItem, const FGuid forcedGuid, int32 inCount)
		: ItemClass(inItem)
		, Count(inCount)
		, ItemGuid(forcedGuid)
	{
	};

	FBaseItem(const TSubclassOf<class UACFItem>& inItem, int32 inCount)
	{
		ItemGuid = FGuid::NewGuid();
		ItemClass = inItem;
		Count = inCount;
	};

	bool IsValid() const;

	void Init(AActor* owner);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = ACF)
	TSubclassOf<class UACFItem> ItemClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = ACF)
	int32 Count = 1;


	FGuid GetItemGuid() const
	{
		return ItemGuid;
	}

	void ForceGuid(const FGuid& newGuid)
	{
		ItemGuid = newGuid;
	}

	void ResetGuid()
	{
		ItemGuid = FGuid::NewGuid();
	}

	FORCEINLINE bool operator==(const FBaseItem& Other) const
	{
		return this->ItemClass == Other.ItemClass;
	}

	FORCEINLINE bool operator!=(const FBaseItem& Other) const
	{
		return this->ItemClass != Other.ItemClass;
	}

	FORCEINLINE bool operator!=(const TSubclassOf<class UACFItem>& Other) const
	{
		return this->ItemClass != Other;
	}

	FORCEINLINE bool operator==(const TSubclassOf<class UACFItem>& Other) const
	{
		return this->ItemClass == Other;
	}

protected:
	UPROPERTY(SaveGame, BlueprintReadOnly, Meta = (IgnoreForMemberInitializationTest), Category = ACF)
	FGuid ItemGuid = FGuid();
};

USTRUCT(BlueprintType)
struct FItemDescriptor {
	GENERATED_BODY()

public:
	FItemDescriptor()
	{
		ThumbNail = nullptr;
		WorldMesh = nullptr;
		// GameSpecificData = nullptr;
		ItemType = EItemType::Other;
		Scale = FVector2D(1.f, 1.f);
	};

	/*Icon to be displayed in UI*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "ACF|Icon")
	class UTexture2D* ThumbNail;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "ACF|Icon")
	FVector2D Scale;

	/*Name of the item*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	FText Name;

	/*Long description of the item*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	FText Description;

	/*Type of item*/
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	EItemType ItemType;

	/*Decide the amount of stackable units when this item is in inventory*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	uint8 MaxInventoryStack = 1;

	/*Weight of this item in the inventory*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	float ItemWeight = 5.0;

	/*mesh to be used when spawned in world as world mesh, not mandatory*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	TSoftObjectPtr<UStaticMesh> WorldMesh;

	/* If the item is droppable in the world*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	bool bDroppable = true;

	/* If this item can be upgraded*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	bool bUpgradable = false;

	/*If upgrading this item has a cost in currency*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, meta = (EditCondition = "bUpgradable == true"), Category = ACF)
	float UpgradeCurrencyCost = 0.f;

	/* The items required to upgrade this item*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, meta = (EditCondition = "bUpgradable == true"), Category = ACF)
	TArray<FBaseItem> RequiredItemsToUpgrade;

	/* Next level of this item*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, meta = (EditCondition = "bUpgradable == true"), Category = ACF)
	TSubclassOf<UACFItem> NextLevelClass;

	/* If this item can be sold to or from a Vendor*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	bool bSellable = true;

	/*base price for selling / buying this item*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, meta = (EditCondition = "bSellable == true"), Category = ACF)
	float CurrencyValue = 5.0;

	/*A Tag to identify the rarity of the item*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	FGameplayTag Rarity;

	/*Slots in which this item can be equipped*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, meta = (Categories = "Itemslot"), Category = ACF)
	TArray<FGameplayTag> ItemSlots;

	TArray<FGameplayTag> GetPossibleItemSlots() const { return ItemSlots; }

	/*Usable to add game specific data to any item
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
	UPrimaryDataAsset* GameSpecificData;*/
};

/**
 * Base class for all items in ACF.
 * Each item holds a descriptor and can be extended to define specific behaviors.
 */
UCLASS(Blueprintable, BlueprintType)
class INVENTORYSYSTEM_API UACFItem : public UObject {
	GENERATED_BODY()

protected:
	/**
	 *  Runtime descriptor containing core data such as name, icon, type, and slot definitions.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FItemDescriptor ItemInfo;

	/**
	 *  The Pawn that owns this item. Must always be valid after initialization.
	 */
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	AActor* ItemOwner = nullptr;

public:
	/** Default constructor. */
	UACFItem();

	virtual bool IsSupportedForNetworking() const override { return true; }

	/**
	 *  Gets the item's thumbnail image for UI display.
	 * @return The thumbnail texture defined in the item descriptor.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UTexture2D* GetThumbnailImage() const { return ItemInfo.ThumbNail; }

	/**
	 *  Gets the item's display name.
	 * @return The localized name from the item descriptor.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FText GetItemName() const { return ItemInfo.Name; }

	/**
	 *  Gets the item's description text.
	 * @return The localized description from the item descriptor.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FText GetItemDescription() const { return ItemInfo.Description; }

	/**
	 *  Gets the type of this item.
	 * @return The item type defined in the item descriptor.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE EItemType GetItemType() const { return ItemInfo.ItemType; }

	/**
	 * Gets the full item descriptor that defines this item's data.
	 * @return The item descriptor instance.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FItemDescriptor GetItemInfo() const { return ItemInfo; }

	/**
	 * Gets the gameplay tag slots where this item can be equipped.
	 * @return A list of valid equipment slot tags.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE TArray<FGameplayTag> GetPossibleItemSlots() const { return ItemInfo.GetPossibleItemSlots(); }

	/**
	 *  Gets the level of the item.
	 * Can be overridden in derived classes for items with scalable attributes.
	 * @return The level of the item (default is 1).
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	virtual int32 GetLevel() const { return 1; }

	/**
	 *  Sets the descriptor data for this item.
	 * @param itemDesc The item descriptor to assign.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetItemDescriptor(const FItemDescriptor& itemDesc)
	{
		ItemInfo = itemDesc;
	}

	/*The actor to be spawned when this item is used, implement in child classes*/
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	TSubclassOf<AACFItemActor> GetItemActorClass() const;
	virtual TSubclassOf<AACFItemActor> GetItemActorClass_Implementation() const;

	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class AActor* GetItemOwner() const { return ItemOwner; }

	/**
	 *  Sets the owning Pawn of this item.
	 * @param inOwner The Pawn who owns this item. Must be valid.
	 */
	void SetItemOwner(AActor* inOwner)
	{
		check(inOwner); // Ensure at runtime
		ItemOwner = inOwner;
	}

	/** All fragments contained in this instance */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Instanced, Category = "ACF")
	TArray<UACFItemFragment*> Fragments;

	UWorld* GetWorld() const override;

	/**
	 * Return the first fragment matching the class (or subclass) passed.
	 * Fully Blueprintable and extensible.
	 */
	UFUNCTION(BlueprintCallable, Category = "Fragments", meta = (DeterminesOutputType = "FragmentClass"))
	UACFItemFragment* GetFragmentByClass(TSubclassOf<UACFItemFragment> FragmentClass) const;

	/**
	 * Custom serialization to persist per-instance fragment state.
	 * Only serializes UPROPERTY(SaveGame) fields on fragments.
	 * Called by FACFInventoryList's save/load path.
	 */
	virtual void Serialize(FArchive& Ar) override;
};
