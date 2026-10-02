// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFInventoryComponent.h"
#include "ACFItemTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Items/ACFItem.h"
#include <Components/SkeletalMeshComponent.h>
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>
#include <Net/Serialization/FastArraySerializer.h>
#include "ItemActors/ACFWeaponActor.h"

#include "ACFEquipmentComponent.generated.h"

class USkeletalMeshComponent;
class UACFConsumable;
class UACFStorageComponent;
class AACFWeaponActor;
class USkeletalMesh;
class AActor;

USTRUCT(BlueprintType)
struct INVENTORYSYSTEM_API FEquippedItem : public FFastArraySerializerItem {
	GENERATED_BODY()

public:
	FEquippedItem()
	{
		Item = nullptr;
		ItemActor = nullptr;
	};

	FEquippedItem(const FInventoryItem& item, const FGameplayTag& itemSlot, UACFItem* itemPtr, AACFItemActor* inActor, const TSubclassOf<UACFItem>& inItemClass);

	void Init(TObjectPtr<UACFEquipmentComponent> ownerComp);

	bool IsValid();

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FGameplayTag ItemSlot;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	FGuid ItemGuid;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	class UACFItem* Item;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	class AACFItemActor* ItemActor;

	UPROPERTY()
	TSubclassOf<UACFItem> ItemClass;

	FGameplayTag GetItemSlot() const
	{
		return ItemSlot;
	}

	TSubclassOf<UACFItem> GetItemClass() const
	{
		if (!Item) {
			return nullptr;
		}
		return Item->GetClass();
	}

	FORCEINLINE bool operator==(const FEquippedItem& Other) const
	{
		return this->ItemSlot == Other.ItemSlot;
	}

	FORCEINLINE bool operator!=(const FEquippedItem& Other) const
	{
		return this->ItemSlot != Other.ItemSlot;
	}

	FORCEINLINE bool operator==(const FGameplayTag& Other) const
	{
		return this->ItemSlot.MatchesTag(Other);
	}

	FORCEINLINE bool operator!=(const FGameplayTag& Other) const
	{
		return !this->ItemSlot.MatchesTag(Other);
	}

	FORCEINLINE bool operator==(const FGuid& Other) const
	{
		return this->ItemGuid == Other;
	}

	FORCEINLINE bool operator!=(const FGuid& Other) const
	{
		return this->ItemGuid != Other;
	}
};

USTRUCT(BlueprintType)
struct INVENTORYSYSTEM_API FEquipment : public FFastArraySerializer {
	GENERATED_BODY()

public:
	FEquipment()
	{
	}

	//~FFastArraySerializer contract
	void PreReplicatedRemove(const TArrayView<int32> RemovedIndices, int32 FinalSize) {};
	void PostReplicatedAdd(const TArrayView<int32> AddedIndices, int32 FinalSize)
	{
		ValidateChanges(AddedIndices);
	}

	void PostReplicatedChange(const TArrayView<int32> ChangedIndices, int32 FinalSize)
	{
		ValidateChanges(ChangedIndices);
	}
	//~End of FFastArraySerializer contract

	void ValidateChanges(const TArrayView<int32> AddedIndices);

	void Init(TObjectPtr<UACFEquipmentComponent> owner)
	{
		ownerComp = owner;
	}
	void Empty()
	{
		EquippedItems.Empty();
		MarkArrayDirty();
	}
	int32 Num() { return EquippedItems.Num(); }

	void AddEntry(FEquippedItem Instance)
	{
		if (!EquippedItems.Contains(Instance)) {
			Instance.Init(ownerComp);
			EquippedItems.Add(Instance);
			MarkItemDirty(Instance);
		}
	}

	void RemoveEntry(FEquippedItem& Instance)
	{
		EquippedItems.Remove(Instance);
		MarkItemDirty(Instance);
	}

	void RemoveAt(int32 index)
	{
		if (!EquippedItems.IsValidIndex(index)) {
			return;
		}
		FEquippedItem Instance = EquippedItems[index];
		EquippedItems.Remove(Instance);
		MarkItemDirty(Instance);
	}

	void ChangeEntry(const FEquippedItem& Instance)
	{
		FEquippedItem* itemPtr = EquippedItems.FindByKey(Instance);
		if (itemPtr) {
			*itemPtr = Instance;
			MarkItemDirty(*itemPtr);
		}
	}

	const TArray<FEquippedItem> GetEquippedItems() const { return EquippedItems; }

	bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
	{
		return FFastArraySerializer::FastArrayDeltaSerialize<FEquippedItem, FEquipment>(EquippedItems, DeltaParms, *this);
	}

protected:
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	TArray<FEquippedItem> EquippedItems;

	UPROPERTY(NotReplicated)
	TObjectPtr<UACFEquipmentComponent> ownerComp;
};

template <>
struct TStructOpsTypeTraits<FEquipment> : public TStructOpsTypeTraitsBase2<FEquipment> {
	enum { WithNetDeltaSerializer = true };
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnEquipmentChanged, const FEquipment&, Equipment);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnEquippedArmorChanged, const FGameplayTag&, ArmorSlot);

/**
 * UACFEquipmentComponent
 *
 * Manages all equipment-related logic for an actor, extending inventory functionalities.
 * Handles equipping, unequipping, dropping, using, and initializing equipment, as well as
 * mesh management and synchronization of equipped items.
 * Works with any AActor, using a component tag system to identify the main skeletal mesh.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class INVENTORYSYSTEM_API UACFEquipmentComponent : public UACFInventoryComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UACFEquipmentComponent();

	/*------------------------ INVENTORY -----------------------------------------*/

	 /**
	* Removes the selected amount of the provided item from the inventory,
	* unequips it if equipped, and spawns a WorldItem near the owner's location.
	*
	* @param item The item to drop.
	* @param count The number of items to drop.
	*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void DropItem(const FInventoryItem& item, int32 count = 1);

	/**
	 * Removes and drops an item from the inventory based on its index.
	 *
	 * @param itemIndex The index of the item to drop.
	 * @param count The number of items to drop.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void DropItemByInventoryIndex(int32 itemIndex, int32 count);

	/* Use this only on Server!!!
	*
	* Initialize the actor's inventory and equipment with starting items.
	* The main mesh is determined by the MainMeshTag or automatically from ACharacter if applicable.
	*/
	UFUNCTION(BlueprintCallable, Category = ACF)
	void InitializeStartingItems();

	/**
	* Moves the item at the provided from the Inventory to the Equipment
	*
	* @param item The item to use.
	*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void UseInventoryItem(const FInventoryItem& item);

	/**
	* Moves the item at the provided from the Inventory to the Equipment
	*
	* @param index The index of the inventory item.
	*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Inventory")
	void UseInventoryItemByIndex(int32 index);


	/* ------------------------ EQUIPMENT ----------------------------------------- */

		/**
		 * @brief Moves the Inventory Item to the Equipment.
		 *
		 * @param inItem The item to equip.
		 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Equipment")
	void EquipItemFromInventory(const FInventoryItem& inItem);

	/**
	 * @brief Moves the Inventory Item to the Equipment.
	 *
	 * @param inItem The item to equip.
	 * @param slot The slot to equip the item in.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Equipment")
	void EquipItemFromInventoryInSlot(const FInventoryItem& inItem, FGameplayTag slot);

	/**
	* @brief Use the item in the specified slot of the Equipment.
	*
	* @param itemSlot The slot containing the item.
	*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Equipment")
	void UseEquippedItemBySlot(FGameplayTag itemSlot);

	/**
	 * @brief Use the item in the specified slot of the Equipment.
	 *
	 * @param itemSlot The slot containing the consumable.
	 * @param target The pawn target.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Equipment")
	void UseConsumableOnActorBySlot(FGameplayTag itemSlot, APawn* target);
	/**
	* Unequips the item in the specified slot.
	*
	* @param itemSlot The slot to unequip from.
	*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Equipment")
	void UnequipItemBySlot(FGameplayTag itemSlot);


	/**
	* Unequips the item identified by the provided GUID.
	*
	* @param itemGuid The unique ID of the item to unequip.
	*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Equipment")
	void UnequipItemByGuid(const FGuid& itemGuid);


	/**
	* Removes the currently equipped weapon from the hand.
	*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Equipment")
	void SheathCurrentWeapon();


	/**
	* Enables or disables damage tracing for the weapon.
	*
	* @param isActive True to enable tracing, false to disable.
	* @param traceChannels The weapon trace channels.
	* @param isLeftWeapon Whether the trace applies to the left-hand weapon.
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void SetDamageActivation(bool isActive, const TArray<FName>& traceChannels, bool isLeftWeapon = false);


	/**
	* Overrides the main mesh with the provided one.
	*
	* @param newMesh The new skeletal mesh component.
	* @param bRefreshEquipment Whether to refresh equipment after setting the mesh.
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void SetMainMesh(USkeletalMeshComponent* newMesh, bool bRefreshEquipment = true);


	/**
	* Returns the main skeletal mesh used for equipment attachments.
	*
	* @return The main skeletal mesh component.
	*/
	UFUNCTION(BlueprintPure, Category = "ACF|Equipment")
	USkeletalMeshComponent* GetMainMesh() const
	{
		return MainCharacterMesh;
	}

	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	bool SwapItemFromInventory(const FInventoryItem& ItemToEquip, UACFInventoryComponent* SourceInventory);

	/**
	 * Destroys all equipped item actors on the server. When @p bSpawnDrops is true,
	 * it also rolls the inventory drop chances, folds in any deferred death drops
	 * (projectiles stuck on the corpse, currency) and spawns the resulting world
	 * item(s). When false, ONLY the equipped item actors are destroyed and NO drop
	 * is spawned: this is the path the AACFCharacter::EndPlay safety net must use
	 * (e.g. World Partition streaming out, map unload, dedicated-server cleanup)
	 * so that streamed-out characters do not litter the world with drops.
	 */
	UFUNCTION(Server, Reliable, Category = "ACF|Equipment")
	void DestroyEquippedItems(bool bSpawnDrops);

	/**
	 * Returns true when this equipment component will produce a single collapsed
	 * world item on death (i.e. both bDropItemsOnDeath and
	 * bCollapseDropInASingleWorldItem are enabled). Sibling components (e.g.
	 * UACFCurrencyComponent) can query this to defer their own death drops into
	 * the single world item produced by DestroyEquippedItems. Note: equipped
	 * ItemActors are always destroyed on death regardless of bDropItemsOnDeath;
	 * the flag here only gates whether their drop is spawned.
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Drop")
	bool WillCollapseDeathDrops() const
	{
		return bDropItemsOnDeath && bCollapseDropInASingleWorldItem;
	}

	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment", meta = (DisplayName = "Show Equipped Items"))
	void ShowEquippedItems() { SetEquippedItemsVisible(true); }

	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment", meta = (DisplayName = "Hide Equipped Items"))
	void HideEquippedItems() { SetEquippedItemsVisible(false); }

	/*------------------------ SETTERS -----------------------------------------*/


	/**
	* Refresh the appearence of the owner based on current Equipment.
	* USEFULL FOR LATE JOINING CONSISTENCY!
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void RefreshEquipment();

	/**
	* Clears all inventory and equipment.
	* Removes all items from inventory and unequips all equipped items.
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void ClearAllInventoryAndEquipment();

	/**
	* Copies equipment from another Equipment Component.
	* Clears current equipment and copies all equipped items from source.
	* 
	* @param SourceEquipment The equipment component to copy from.
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void CopyEquipmentFrom(UACFEquipmentComponent* SourceEquipment);


	/**
	* Returns whether left-hand IK should be used.
	*
	* @return True if left-hand IK is active.
	*/
	UFUNCTION(BlueprintPure, Category = "ACF|Equipment")
	bool ShouldUseLeftHandIK() const;


	/**
	* Returns the left hand IK position.
	*
	* @return The vector location of the left-hand IK.
	*/
	UFUNCTION(BlueprintPure, Category = "ACF|Equipment")
	FVector GetLeftHandIkPos() const;

	/** Sets a generic left-hand IK override (e.g. from a glider or any equippable item). */
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void SetLeftHandIKOverride(USceneComponent* Component);

	/** Clears the left-hand IK override. */
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void ClearLeftHandIKOverride();


	/**
	* Returns true if the provided slot is available.
	*
	* @param itemSlot The slot to check.
	* @return True if the slot is free.
	*/
	UFUNCTION(BlueprintPure, Category = "ACF|Equipment")
	bool IsSlotAvailable(const FGameplayTag& itemSlot) const;

	/**
	* Tries to find an available slot among the provided ones.
	*
	* @param itemSlots Array of candidate slots.
	* @param outAvailableSlot The first found available slot.
	* @return True if a valid slot was found.
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	bool TryFindAvailableItemSlot(const TArray<FGameplayTag>& itemSlots, FGameplayTag& outAvailableSlot);


	/**
	* Returns true if at least one of the provided slots is valid.
	*
	* @param itemSlots The list of candidate slots.
	* @return True if any slot is valid.
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	bool HaveAtLeastAValidSlot(const TArray<FGameplayTag>& itemSlots);

	/**
	* Unsheathes the first available weapon found in equipment slots.
	* Also equips any compatible offhand weapon if the main weapon is one-handed.
	* Useful for turn-based combat initialization where actors need weapons drawn.
	* @return True if at least a main weapon was successfully unsheathed.
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	bool UnsheatheFirstAvailableWeapon();

	/*------------------------ SETTERS -----------------------------------------*/

	/**
	* Sets whether items should be dropped on death.
	*
	* @param bDrop True to drop equipped items on death.
	*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Setters")
	void SetDropItemsOnDeath(bool bDrop)
	{
		bDropItemsOnDeath = bDrop;
	}

	/*------------------------ GETTERS -----------------------------------------*/

	/** Returns the maximum number of inventory slots. */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE int32 GetMaxInventorySlots() const { return MaxInventorySlots; }


	/** Returns the maximum allowed inventory weight. */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE int32 GetMaxInventoryWeight() const { return MaxInventoryWeight; }


	/** Returns the currently equipped main weapon actor. */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE AACFWeaponActor* GetCurrentMainWeapon() const { return MainWeapon; }


	/** Returns the currently equipped offhand weapon actor. */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE AACFWeaponActor* GetCurrentOffhandWeapon() const { return SecondaryWeapon; }


	/** Returns the current equipment struct. */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE FEquipment GetCurrentEquipment() const { return Equipment; }


	/** Returns the socket location of the main weapon. */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FVector GetMainWeaponSocketLocation() const;


	/** Returns all modular meshes currently equipped. */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	FORCEINLINE TArray<FModularPart> GetModularMeshes() const { return ModularMeshes; }


	/** Returns the equipped item in the specified slot. */
	UFUNCTION(BlueprintCallable, Category = "ACF|Getters")
	bool GetEquippedItemSlot(const FGameplayTag& itemSlot, FEquippedItem& outSlot) const;


	/** Returns the equipped item with the specified GUID. */
	UFUNCTION(BlueprintCallable, Category = "ACF|Getters")
	bool GetEquippedItem(const FGuid& itemGuid, FEquippedItem& outSlot) const;


	/** Returns the modular mesh in the given slot. */
	UFUNCTION(BlueprintCallable, Category = "ACF|Getters")
	bool GetModularMesh(FGameplayTag itemSlot, FModularPart& outMesh) const;

	/** Returns the list of starting items for this character. */
	UFUNCTION(BlueprintPure, Category = "ACF|Getters")
	TArray<FStartingItem> GetStartingItems() const { return StartingItems; }

	/*------------------------ CHECKS -----------------------------------------*/

	/** Checks if there is any item equipped in the specified slot. */
	UFUNCTION(BlueprintCallable, Category = "ACF|Checks")
	bool HasAnyItemInEquipmentSlot(FGameplayTag itemSlor) const;


	/** Returns true if the actor can switch to ranged combat. */
	UFUNCTION(BlueprintPure, Category = "ACF|Checks")
	bool CanSwitchToRanged();


	/** Returns true if the actor can switch to melee combat. */
	UFUNCTION(BlueprintPure, Category = "ACF|Checks")
	bool CanSwitchToMelee();


	/** Determines if the provided item class can be equipped. */
	UFUNCTION(BlueprintPure, Category = "ACF|Checks")
	bool CanBeEquipped(const TSubclassOf<UACFItem>& equippable);


	/** Checks whether the actor has any weapon of the specified class equipped on body. */
	UFUNCTION(BlueprintCallable, Category = "ACF|Checks")
	bool HasOnBodyAnyWeaponOfType(TSubclassOf<UACFWeapon> weaponClass) const;

	/*------------------------ DELEGATES
	 * -----------------------------------------*/

	 /** Event triggered when the equipment changes. */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnEquipmentChanged OnEquipmentChanged;


	/** Event triggered when the equipped armor piece in a specific slot changes. */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnEquippedArmorChanged OnEquippedArmorChanged;

	/*------------------------ MOVESETS
	 * -----------------------------------------*/
	UFUNCTION(BlueprintCallable, Category = "ACF|Movesets")
	FGameplayTag GetCurrentDesiredMovesetTag() const;

	UFUNCTION(BlueprintCallable, Category = "ACF|Movesets")
	FGameplayTag GetCurrentDesiredMovesetActionTag() const;

	UFUNCTION(BlueprintCallable, Category = "ACF|Movesets")
	FGameplayTag GetCurrentDesiredOverlayTag() const;

	// addition code
	virtual void BeginPlay() override;

	void GatherActorOwner();

	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	void DestroyEquipment();

	UFUNCTION(BlueprintPure, Category = "ACF|Equipment")
	TArray<FGameplayTag> GetAvailableEquipmentSlot() const { return AvailableEquipmentSlot; }

	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void SetAvailableEquipmentSlot(const TArray<FGameplayTag>& val) { AvailableEquipmentSlot = val; }

	UFUNCTION(BlueprintPure, Category = "ACF|Equipment")
	TArray<FGameplayTag> GetAllowedWeaponTypes() const { return AllowedWeaponTypes; }

	UFUNCTION(BlueprintCallable, Category = "ACF|Equipment")
	void SetAllowedWeaponTypes(const TArray<FGameplayTag>& val) { AllowedWeaponTypes = val; }

	void SetStartingItems(TArray<FStartingItem> val);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnEntityOwnerDeath();


	void GatherMainMesh();

protected:
	/* Tag to identify the main skeletal mesh component on the owner actor.
	 * If set, the component will search for a SkeletalMeshComponent with this tag in BeginPlay.
	 * If not set or not found, it will fallback to ACharacter's Mesh if the owner is a Character. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	FName MainMeshTag = "Mesh";

	/* Slots available for equipment on this actor */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "ItemSlot"), Category = ACF)
	TArray<FGameplayTag> AvailableEquipmentSlot;

	/* Weapon types usable by this actor */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "Item"), Category = ACF)
	TArray<FGameplayTag> AllowedWeaponTypes;

	/*Defines if the Entity should destroy all his equipped items when dying*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Drop")
	bool bDestroyItemsOnDeath = true;

	/*Defines if the Entity should drop all his droppable invnentory Items when it
	 * dies*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Drop")
	bool bDropItemsOnDeath = true;

	/*If true, all the drops (inventory items, projectiles stuck on the corpse,
	 * and currency from sibling Currency components) will be collapsed in a
	 * single world item on death*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Drop")
	bool bCollapseDropInASingleWorldItem = true;

	/*Defines if one of the equipped armors can hide / unhide the main mesh of the
	 * owner entity*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	bool bUpdateMainMeshVisibility = true;

	/* The main skeletal mesh used for equipment attachments */
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	USkeletalMeshComponent* MainCharacterMesh;

	/*Define if an item should be automatically Equipped On Body, if it is picked
	 * up from world */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	bool bAutoEquipItem = true;

	/* Starting items for this actor */
	UPROPERTY(EditAnywhere, meta = (TitleProperty = "ItemClass"), BlueprintReadWrite, Category = ACF)
	TArray<FStartingItem> StartingItems;

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnComponentLoaded();

	virtual void BeginDestroy() override;

	UPROPERTY(ReplicatedUsing = OnRep_SheathedWeap, BlueprintReadOnly, Category = ACF)
	TObjectPtr<AACFWeaponActor> MainWeapon;

	UPROPERTY(ReplicatedUsing = OnRep_SheathedWeap, BlueprintReadOnly, Category = ACF)
	TObjectPtr<AACFWeaponActor> SecondaryWeapon;

	virtual void HandleItemRemoved(const FInventoryItem& item, int32 count = 1) override;
	virtual void HandleItemAdded(const FInventoryItem& item, int32 count = 1, bool bTryToEquip = true, FGameplayTag equipSlot = FGameplayTag()) override;

	void SetEquippedItemsVisible(bool bVisible);

	/** Immediately sets a 0.1s lifespan on all equipped item actors and clears their
	 *  ItemActor pointer. Never spawns drops. Called from DestroyEquippedItems
	 *  (Server RPC, both with and without drops) and from the AACFCharacter::EndPlay
	 *  safety net (via DestroyEquippedItems with bSpawnDrops=false) for non-death
	 *  removal paths such as World Partition streaming. */
	void Internal_DestroyEquipment();

private:

	UPROPERTY(Replicated, ReplicatedUsing = OnRep_Equipment)
	FEquipment Equipment;

	TWeakObjectPtr<USceneComponent> LeftHandIKOverride;

	void SetMainWeapon(class AACFWeaponActor* val) { MainWeapon = val; }
	void SetSecondaryWeapon(class AACFWeaponActor* val) { SecondaryWeapon = val; }

	TArray<FModularPart> ModularMeshes;

	UFUNCTION()
	void OnRep_Equipment();

	UFUNCTION()
	void OnRep_SheathedWeap();

	void FillModularMeshes();

	UPROPERTY()
	TObjectPtr<AActor> ActorOwner;

	/** The skeletal mesh used by the Owner. */
	UPROPERTY()
	TObjectPtr<USkeletalMesh> originalMesh;

	UPROPERTY(Replicated)
	FGameplayTag CurrentlyEquippedSlotType;

	/** Transient buffer used to collapse drops produced by OnEntityOwnerDeath
	 *  (e.g. arrows stuck on the corpse) into the same world item generated
	 *  by DestroyEquippedItems when bCollapseDropInASingleWorldItem is enabled. */
	UPROPERTY(Transient)
	TArray<FBaseItem> PendingDeathDropsAccumulator;


	void RemoveItemFromEquipment(const FEquippedItem& equippedItem);
	void MarkItemOnInventoryAsEquipped(const FGuid& item, bool bIsEquipped, const FGameplayTag& itemSlot);

	void AttachWeaponOnBody(AACFWeaponActor* WeaponToEquip);

	void AttachWeaponOnHand(AACFWeaponActor* _localWeapon);

	void AddSkeletalMeshComponent(const FEquippedItem& equipItem);

	void Internal_OnArmorUnequipped(const FGameplayTag& slot);

	void SpawnWorldItem(const TArray<FBaseItem>& items, float currencyAmount = 0.f);

	void UseEquippedConsumable(FEquippedItem& EquipSlot, APawn* target);
};
