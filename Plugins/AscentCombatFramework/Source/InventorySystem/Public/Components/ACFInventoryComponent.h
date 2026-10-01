// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCurrencyComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Items/ACFItem.h"
#include <GameFramework/Character.h>
#include <GameplayTagContainer.h>

#include "ACFInventoryComponent.generated.h"

class UACFStorageComponent;
class UACFConsumable;
class UACFItemFragment;
class UACFInventoryComponent;
struct FBaseItem;
struct FACFInventoryList;

USTRUCT(BlueprintType)
struct INVENTORYSYSTEM_API FStartingItem : public FBaseItem {
	GENERATED_BODY()

public:
	FStartingItem() {};

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	bool bAutoEquip = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.0", ClampMax = "100.0"), Category = ACF)
	float DropChancePercentage = 0.f;

	FORCEINLINE bool operator==(const FStartingItem& Other) const
	{
		return this->ItemClass == Other.ItemClass;
	}

	FORCEINLINE bool operator!=(const FStartingItem& Other) const
	{
		return this->ItemClass != Other.ItemClass;
	}
};

USTRUCT(BlueprintType)
struct INVENTORYSYSTEM_API FInventoryItem : public FBaseItem {
	GENERATED_BODY()

public:
	FInventoryItem() {};

	FInventoryItem(const FBaseItem& inItem);

	FInventoryItem(const FStartingItem& inItem);

	// Delegate to FBaseItem's copy so the FFastArraySerializerItem base
	// (ReplicationID/ReplicationKey) and ItemGuid/ItemClass/Count are carried
	// over. Dropping the base here was breaking FastArray identity, turning
	// stack-count changes into remove+add on clients.
	FInventoryItem(const FInventoryItem& inItem)
		: FBaseItem(inItem)
	{
		bIsEquipped = inItem.bIsEquipped;        
		EquipmentSlot = inItem.EquipmentSlot;   
		DropChancePercentage = inItem.DropChancePercentage;  
		ItemIndex = inItem.ItemIndex;
		Item = inItem.Item;  // Share cached instance for CanBeUsed etc.
		LastObservedCount = inItem.LastObservedCount;
	};

	/*Cached UACFItem instance for CanBeUsed etc. Created on add (server) or on replicate (client). Not replicated.*/
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = ACF)
	class UACFItem* Item = nullptr;

	/*Identifies if this item is equipped*/
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = ACF)
	bool bIsEquipped = false;

	/*If this item is equipped, this is the slot in which is equipped.
	Not set if the item is not equipped*/
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = ACF)
	FGameplayTag EquipmentSlot;

	/*Chance of this item of being dropped on death*/
	UPROPERTY(SaveGame, BlueprintReadOnly, meta = (ClampMin = "0.0", ClampMax = "100.0"), Category = ACF)
	float DropChancePercentage = 0.f;

	/*Usable for modifiable indexes, not used by default*/
	UPROPERTY(SaveGame, BlueprintReadOnly, meta = (ClampMin = "0.0", ClampMax = "100.0"), Category = ACF)
	int32 ItemIndex = 0;

	/* Client-side mirror of the last Count seen through replication. Used by the
	 * FastArray callbacks to derive the stack-count delta (amount added/removed)
	 * rather than reporting the new total. Not replicated, transient. */
	UPROPERTY(NotReplicated)
	int32 LastObservedCount = 0;

	FORCEINLINE bool operator==(const FInventoryItem& Other) const
	{
		return this->GetItemGuid() == Other.GetItemGuid();
	}

	FORCEINLINE bool operator!=(const FInventoryItem& Other) const
	{
		return this->GetItemGuid() != Other.GetItemGuid();
	}

	FORCEINLINE bool operator==(const FGuid& Other) const
	{
		return this->GetItemGuid() == Other;
	}

	FORCEINLINE bool operator!=(const FGuid& Other) const
	{
		return this->GetItemGuid() != Other;
	}

	//~ FFastArraySerializerItem contract: fire client-side events when this entry
	// is added / changed / removed through FastArray replication.
	void PreReplicatedRemove(const FACFInventoryList& InArraySerializer);
	void PostReplicatedAdd(const FACFInventoryList& InArraySerializer);
	void PostReplicatedChange(const FACFInventoryList& InArraySerializer);

	/* Broadcasts the signed count delta (NewCount - OldCount) on the owning
	 * component as OnItemAdded (positive) or OnItemRemoved (negative). */
	void BroadcastCountDelta(class UACFInventoryComponent* InvComp, int32 OldCount, int32 NewCount) const;
};

/** List of inventory items */
USTRUCT(BlueprintType)
struct INVENTORYSYSTEM_API FACFInventoryList : public FFastArraySerializer {
	GENERATED_BODY()

	FACFInventoryList()
		: actorOwner(nullptr)
	{
	}

	TArray<FInventoryItem> GetAllItems() const;
	bool GetItemByIndex(const int32 index, FInventoryItem& outItem) const;
	bool ContainsItem(const FInventoryItem& Item) const;
	bool Contains(const FGuid& ItemGUID) const;

	void Init(AActor* owner)
	{
		actorOwner = owner;
	}

	/** Owning actor (used to resolve the component in FastArray callbacks). */
	AActor* GetActorOwner() const { return actorOwner; }

	/** Returns the owning UACFInventoryComponent on the owner actor, or nullptr. */
	UACFInventoryComponent* GetOwnerComponent() const;

	/** Declared here, defined in .cpp to keep header lightweight */
	void Empty();

	bool IsEmpty() const
	{
		return Inventory.Num() == 0;
	}
	int32 Num() const { return Inventory.Num(); }

	bool GetItem(const FGuid& itemToSearch, FInventoryItem& outItem) const
	{
		if (Inventory.Contains(itemToSearch)) {
			outItem = *Inventory.FindByKey(itemToSearch);
			return true;
		}
		return false;
	}

	bool IsValidIndex(int32 index)
	{
		return Inventory.IsValidIndex(index);
	}

	void MarkItemAsEquipped(const FGuid& item, bool bIsEquipped, const FGameplayTag& itemSlot)
	{
		FInventoryItem* itemPtr = Inventory.FindByKey(item);
		if (itemPtr) {
			itemPtr->bIsEquipped = bIsEquipped;
			itemPtr->EquipmentSlot = itemSlot;
			MarkItemDirty(*itemPtr);
		}
	}

	void SetItemIndex(const FGuid& item, int32 index)
	{
		FInventoryItem* itemPtr = Inventory.FindByKey(item);
		if (itemPtr) {
			itemPtr->ItemIndex = index;
			MarkItemDirty(*itemPtr);
		}
	}

public:
	//~FFastArraySerializer contract
	void PreReplicatedRemove(const TArrayView<int32> RemovedIndices, int32 FinalSize);
	void PostReplicatedAdd(const TArrayView<int32> AddedIndices, int32 FinalSize)
	{
		ValidateChanges(AddedIndices);
	}

	void ValidateChanges(const TArrayView<int32> AddedIndices);

	void PostReplicatedChange(const TArrayView<int32> ChangedIndices, int32 FinalSize)
	{
		ValidateChanges(ChangedIndices);
	}
	//~End of FFastArraySerializer contract

	bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
	{
		return FFastArraySerializer::FastArrayDeltaSerialize<FInventoryItem, FACFInventoryList>(Inventory, DeltaParms, *this);
	}

	/** Custom save/load to persist UACFItem instances and their fragment state.
	 *  Called from UACFInventoryComponent::Serialize -- NOT a WithSerializer override. */
	void SaveLoad(FArchive& Ar);

	void AddEntry(const FInventoryItem& Instance)
	{
		if (!Inventory.Contains(Instance)) {
			const int32 NewIndex = Inventory.Add(Instance);
			FInventoryItem& Added = Inventory[NewIndex];
			// Instance may be a copy carrying a ReplicationID from another
			// inventory; force a fresh FastArray identity so MarkItemDirty mints
			// a new ID for this list (avoids ID collisions on item transfers).
			Added.ReplicationID = INDEX_NONE;
			Added.ReplicationKey = 0;
			MarkItemDirty(Added);
		}
	}

	void RemoveEntry(const FInventoryItem& Instance)
	{
		const int32 Removed = Inventory.Remove(Instance);
		if (Removed > 0) {
			MarkArrayDirty();
		}
	}

	void ChangeEntry(FInventoryItem Instance)
	{
		FInventoryItem* itemPtr = Inventory.FindByKey(Instance);
		if (itemPtr) {
			// Always keep the identity of the entry that already lives in THIS
			// list. The incoming Instance is a copy (possibly originating from a
			// different inventory), so its ReplicationID must not overwrite ours;
			// otherwise the client would see a remove+add (PostReplicatedAdd with
			// the full stack total) instead of a change (PostReplicatedChange with
			// the delta).
			const int32 SavedReplicationID = itemPtr->ReplicationID;
			const int32 SavedReplicationKey = itemPtr->ReplicationKey;
			*itemPtr = Instance;
			itemPtr->ReplicationID = SavedReplicationID;
			itemPtr->ReplicationKey = SavedReplicationKey;
			MarkItemDirty(*itemPtr);
		}
	}

private:
	// Replicated list of items
	UPROPERTY(SaveGame)
	TArray<FInventoryItem> Inventory;

	UPROPERTY(NotReplicated)
	TObjectPtr<AActor> actorOwner;
};

template <>
struct TStructOpsTypeTraits<FACFInventoryList> : public TStructOpsTypeTraitsBase2<FACFInventoryList> {
	enum { 
		WithNetDeltaSerializer = true,
	};
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnInventoryChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemAdded, const FBaseItem&, item);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemRemoved, const FBaseItem&, item);

/**
 * UACFInventoryComponent
 *
 * Component that manages the character's inventory, including item addition, removal, storage handling, and weight management.
 * Handles replication, usage of consumables, and interaction with currency and equipment systems.
 *
 * Fragment subobject replication is handled directly by this component via
 * UE's registered subobject list (bReplicateUsingRegisteredSubObjectList).
 * No separate replication component is needed.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class INVENTORYSYSTEM_API UACFInventoryComponent : public UACFCurrencyComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UACFInventoryComponent();

	/** Persist UACFItem instances and fragment state through save/load. */
	virtual void Serialize(FArchive& Ar) override;

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	virtual bool ReplicateSubobjects(UActorChannel* Channel, FOutBunch* Bunch, FReplicationFlags* RepFlags) override;

public:
	// ========================================================================
	// Fragment Subobject Replication (built-in)
	// ========================================================================

	/** Register a fragment instance for subobject replication. Server-only. */
	UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "ACF|Replication")
	bool RegisterFragment(UACFItemFragment* Fragment);

	/** Unregister a fragment from subobject replication. */
	UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "ACF|Replication")
	bool UnregisterFragment(UACFItemFragment* Fragment);

	/** Register all fragments from an item for replication. */
	UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "ACF|Replication")
	void RegisterFragmentsForItem(UACFItem* Item);

	/** Unregister all fragments belonging to the given item. */
	UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "ACF|Replication")
	void UnregisterFragmentsForItem(UACFItem* Item);

	/** Get all currently registered fragment subobjects. */
	UFUNCTION(BlueprintPure, Category = "ACF|Replication")
	TArray<UACFItemFragment*> GetRegisteredFragments() const;

	// ========================================================================
	// Inventory API
	// ========================================================================

	/**
		* Adds an item to the inventory from its class type.
		*
		* @param inItem The class of the item to add.
		* @param count Number of items to add.
		* @param bAutoEquip Whether to automatically equip the item if possible.
		*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void AddItemToInventoryByClass(TSubclassOf<UACFItem> inItem, int32 count = 1, bool bAutoEquip = true);

	/**
	 * Adds a base item instance to the inventory.
	 *
	 * @param ItemToAdd The base item data to add.
	 * @param bAutoEquip Whether to automatically equip the item if possible.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void AddItemToInventory(const FBaseItem& ItemToAdd, bool bAutoEquip = true);

	/**
	 * Adds an inventory item struct to the inventory.
	 *
	 * @param ItemToAdd The inventory item to add.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void AddInventoryItem(const FInventoryItem& ItemToAdd);

	/**
	* Removes the specified amount of an item from the inventory.
	* Automatically unequips it if it is equipped.
	*
	* @param item The item to remove.
	* @param count The number of items to remove.
	*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void RemoveItem(const FInventoryItem& item, int32 count = 1);

	/**
	 * Removes an item from the inventory by its index.
	 *
	 * @param index The index of the item in the inventory list.
	 * @param count The number of items to remove.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void RemoveItemByIndex(const int32 index, int32 count = 1);

	/*------------------------ STORAGE -----------------------------------------*/
   /**
	 * Moves a collection of items from another inventory to this one.
	 *
	 * @param inItems The items to move.
	 * @param sourceInventory The inventory component from which the items are moved.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void MoveItemsFromInventory(const TArray<FInventoryItem>& inItems, UACFInventoryComponent* sourceInventory);

	/**
	 * Retrieves all items currently in the inventory.
	 *
	 * @return Array of all inventory items.
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE TArray<FInventoryItem> GetInventory() const
	{
		return GetInventoryListConst().GetAllItems();
	}


	/**
	 * Returns the number of available slots in the inventory.
	 *
	 * @return number of available slots in the inventory.
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE int32 GetAvailableSlots() const
	{
		return MaxInventorySlots - GetInventoryListConst().Num();
	}

	/**
	 * Checks whether an item exists in the inventory.
	 *
	 * @param item The item to check.
	 * @return True if the item exists in the inventory, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE bool IsInInventory(const FInventoryItem& item) const
	{
		return GetInventoryListConst().ContainsItem(item);
	}


	/**
	* Finds an item in the inventory by its unique GUID.
	*
	* @param itemGuid The GUID of the item to search for.
	* @param outItem The resulting item, if found.
	* @return True if the item is found, false otherwise.
	*/
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	bool GetItemByGuid(const FGuid& itemGuid, FInventoryItem& outItem) const;

	/**
	 * Finds an item in the inventory by its index.
	 *
	 * @param index The index of the item.
	 * @param outItem The resulting item, if found.
	 * @return True if the item exists at the given index.
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	bool GetItemByIndex(const int32 index, FInventoryItem& outItem) const
	{
		return GetInventoryListConst().GetItemByIndex(index, outItem);
	}

	UFUNCTION(BlueprintCallable, Server, Reliable, Category = "ACF|Setters")
	void SetItemGridIndex(const FGuid& itemGuid, const int32 index);

	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	int32 GetItemGridIndex(const FGuid& itemGuid) const
	{
		FInventoryItem outItem;
		GetInventoryListConst().GetItem(itemGuid, outItem);
		return outItem.ItemIndex;
	}

	/**
	 * Returns the total number of items of a specific class in the inventory.
	 *
	 * @param itemClass The class of the item.
	 * @return The total count of items matching that class.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Getters")
	int32 GetTotalCountOfItemsByClass(const TSubclassOf<UACFItem>& itemClass) const;

	/**
	 * Retrieves all items of a given class from the inventory.
	 *
	 * @param itemClass The class of the items to find.
	 * @param outItems The array of matching items.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Getters")
	void GetAllItemsOfClassInInventory(const TSubclassOf<UACFItem>& itemClass, TArray<FInventoryItem>& outItems) const;


	/**
	 * Retrieves all items marked as sellable from the inventory.
	 *
	 * @param outItems The array of sellable items.
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	void GetAllSellableItemsInInventory(TArray<FInventoryItem>& outItems) const;

	/**
	 * Finds the first item of a specified class in the inventory.
	 *
	 * @param itemClass The class of the item to search for.
	 * @param outItem The resulting item, if found.
	 * @return True if a matching item is found.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Getters")
	bool FindFirstItemOfClassInInventory(const TSubclassOf<UACFItem>& itemClass, FInventoryItem& outItem) const;

	/**
	 * Consumes a collection of base items from the inventory.
	 *
	 * @param ItemsToCheck The items to consume.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void ConsumeItems(const TArray<FBaseItem>& ItemsToCheck);

	/**
	 * Uses a consumable item on a target pawn.
	 *
	 * @param Inventoryitem The consumable item to use.
	 * @param target The pawn receiving the effect.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Inventory")
	void UseConsumableOnTarget(const FInventoryItem& Inventoryitem, APawn* target);

	/**
	 * Checks whether a consumable can be used on the given target.
	 *
	 * @param Inventoryitem The consumable item.
	 * @param target The pawn to check against.
	 * @return True if the consumable can be used.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Inventory")
	bool CanUseConsumable(const FInventoryItem& Inventoryitem, APawn* target) const;

	/**
	 * Checks whether the inventory has enough of each item in the given list.
	 *
	 * @param ItemsToCheck The list of items and amounts to verify.
	 * @return True if all required items are present.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Checks")
	bool HasEnoughItemsOfType(const TArray<FBaseItem>& ItemsToCheck) const;

	/**
		* Checks whether the inventory contains at least one instance of a given item type.
		*
		* @param itemToCheck The class of the item to check for.
		* @return True if at least one item of that class is present.
		*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Checks")
	bool HasAnyItemOfType(const TSubclassOf<UACFItem>& itemToCheck) const;

	/**
	 * Gets the total current weight of all items in the inventory.
	 *
	 * @return The total weight of the inventory.
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE float GetCurrentInventoryTotalWeight() const
	{
		return currentInventoryWeight;
	}

	/**
	 * Sets a new maximum allowed inventory weight.
	 *
	 * @param newMax The new maximum weight value.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Setters")
	void SetMaxInventoryWeight(int32 newMax)
	{
		MaxInventoryWeight = newMax;
	}

	/**
	 * Sets a new maximum number of inventory slots.
	 *
	 * @param newMax The new maximum slot count.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Setters")
	void SetMaxInventorySlots(int32 newMax)
	{
		MaxInventorySlots = newMax;
	}

	/**
	 * Returns how many more items of the specified type the inventory can hold.
	 *
	 * @param itemToCheck The item class to evaluate.
	 * @return The number of items that can still be added before reaching the limit.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Checks")
	int32 NumberOfItemCanTake(const TSubclassOf<UACFItem>& itemToCheck);

	/**
	 * Recalculates the total inventory weight.
	 * Should be called whenever an item is added, removed, or modified.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void RefreshTotalWeight();

	/**
	 * Collapses (merges) all non-full stacks of every stackable item type in the
	 * inventory. For each item class the total count is redistributed into the
	 * fewest possible stacks: as many full stacks (MaxInventoryStack) as possible
	 * plus a single remainder stack.
	 *
	 * Example (arrows, MaxInventoryStack = 20):
	 *  - stacks of 10 + 5           -> one stack of 15
	 *  - stacks of 12 + 12          -> one stack of 20 + one stack of 4
	 *
	 * Existing stack GUIDs / cached item instances are reused where possible to
	 * keep replication churn minimal; emptied stacks are removed. Total item
	 * count and inventory weight are preserved. Server authoritative.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void CollapseInventory();

	/**
	 * Collapses (merges) all non-full stacks of a single item class. See
	 * CollapseInventory for the redistribution rules. Server authoritative.
	 *
	 * @param itemClass The item class whose stacks should be collapsed.
	 */
	// Passed by value (not const&): UHT's RPC Parms marshalling for Server/Reliable
	// functions cannot assign into a const-qualified TSubclassOf Parms member.
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void CollapseItemsOfClass(TSubclassOf<UACFItem> itemClass);

	/** Event triggered whenever the inventory content changes. */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnInventoryChanged OnInventoryChanged;

	/** Event triggered when an item is added to the inventory. */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnItemAdded OnItemAdded;

	/** Event triggered when an item is removed from the inventory. */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnItemRemoved OnItemRemoved;

	const FACFInventoryList& GetInventoryListConst() const { return InventoryList; }
	bool GetIsInitialized() const { return bIsInitialized; }
	void SetIsInitialized(bool val) { bIsInitialized = val; }
protected:
	FACFInventoryList& GetInventoryList() { return InventoryList; }

	/*Maximum number of Slot items in Inventory*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Savegame, Category = "ACF|Inventory")
	int32 MaxInventorySlots = 40;

	/*Max cumulative weight on*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Savegame, Category = "ACF|Inventory")
	float MaxInventoryWeight = 180.f;

	/* Merges the non-full stacks of a single item class into the fewest possible
	 * stacks. Returns true if the inventory list was modified. Does not broadcast. */
	bool Internal_CollapseItemsOfClass(const TSubclassOf<UACFItem>& itemClass);

	virtual void HandleItemRemoved(const FInventoryItem& item, int32 count = 1);
	virtual void HandleItemAdded(const FInventoryItem& item, int32 count = 1, bool bTryToEquip = true, FGameplayTag equipSlot = FGameplayTag());
	virtual int32 Internal_AddItem(const FBaseItem& item, bool bTryToEquip = false, float dropChancePercentage = 0.f, FGameplayTag equipSlot = FGameplayTag());
	void Internal_UseItem(UACFConsumable* consumable, APawn* target, const FInventoryItem& Inventoryitem);
	int32 Internal_AddInventoryItem(const FInventoryItem& ItemToAdd, bool bTryToEquip = true);

	UPROPERTY(Replicated)
	float currentInventoryWeight = 0.f;

private:
	/*Inventory of this character*/
	UPROPERTY(SaveGame, Replicated, ReplicatedUsing = OnRep_Inventory)
	FACFInventoryList InventoryList;

	UFUNCTION()
	void OnRep_Inventory();

	TObjectPtr<AActor> actorOwner;

	UPROPERTY(SaveGame)
	bool bIsInitialized = false;

	/** Registered fragment subobjects for replication. */
	UPROPERTY()
	TArray<TObjectPtr<UACFItemFragment>> RegisteredFragments;
};
