// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFInventoryComponent.h"
#include "ACFItemSystemFunctionLibrary.h"
#include "Components/ACFStorageComponent.h"
#include "Items/ACFConsumable.h"
#include "Items/ACFItem.h"
#include "Items/ACFItemFragment.h"
#include "Logging.h"
#include <Engine/ActorChannel.h>
#include <GameFramework/Character.h>
#include <GameplayTagContainer.h>
#include <GenericPlatform/GenericPlatformMath.h>
#include <Kismet/KismetMathLibrary.h>
#include <Net/Serialization/FastArraySerializer.h>
#include <Net/UnrealNetwork.h>

FInventoryItem::FInventoryItem(const FBaseItem& inItem)
{
	Count = inItem.Count;
	ItemGuid = inItem.GetItemGuid();
	ItemClass = inItem.ItemClass.Get();
}

FInventoryItem::FInventoryItem(const FStartingItem& inItem)
{
	Count = inItem.Count;
	ItemGuid = FGuid::NewGuid();
	ItemClass = inItem.ItemClass.Get();
	DropChancePercentage = inItem.DropChancePercentage;
};

TArray<FInventoryItem> FACFInventoryList::GetAllItems() const
{
	return Inventory;
}

bool FACFInventoryList::GetItemByIndex(const int32 index, FInventoryItem& outItem) const
{
	if (Inventory.IsValidIndex(index)) {
		outItem = Inventory[index];
		return true;
	}
	return false;
}

bool FACFInventoryList::ContainsItem(const FInventoryItem& Item) const
{
	return Inventory.Contains(Item);
}

bool FACFInventoryList::Contains(const FGuid& ItemGUID) const
{
	return Inventory.Contains(ItemGUID);
}

UACFInventoryComponent* FACFInventoryList::GetOwnerComponent() const
{
	if (!actorOwner)
	{
		return nullptr;
	}
	return actorOwner->FindComponentByClass<UACFInventoryComponent>();
}

// -----------------------------------------------------------------------------
// FInventoryItem: FastArray item-level callbacks (client-side notifications).
// These fire on remote clients when the entry is replicated. The authority
// (server/listen-server) broadcasts the same delegates directly from the
// Add/Remove flow, so each machine receives exactly one notification per change.
// -----------------------------------------------------------------------------

void FInventoryItem::BroadcastCountDelta(UACFInventoryComponent* InvComp, int32 OldCount, int32 NewCount) const
{
	if (!InvComp)
	{
		return;
	}
	const int32 Delta = NewCount - OldCount;
	if (Delta > 0)
	{
		InvComp->OnItemAdded.Broadcast(FBaseItem(ItemClass, Delta));
	}
	else if (Delta < 0)
	{
		InvComp->OnItemRemoved.Broadcast(FBaseItem(ItemClass, -Delta));
	}
}

void FInventoryItem::PostReplicatedAdd(const FACFInventoryList& InArraySerializer)
{
	// New entry on this client: LastObservedCount is 0, so the delta is the full
	// Count of the freshly added stack.
	UACFInventoryComponent* InvComp = InArraySerializer.GetOwnerComponent();
	BroadcastCountDelta(InvComp, LastObservedCount, Count);
	LastObservedCount = Count;
}

void FInventoryItem::PostReplicatedChange(const FACFInventoryList& InArraySerializer)
{
	// Existing entry mutated: report the difference against the last seen Count.
	UACFInventoryComponent* InvComp = InArraySerializer.GetOwnerComponent();
	BroadcastCountDelta(InvComp, LastObservedCount, Count);
	LastObservedCount = Count;
	if (InvComp)
	{
		InvComp->OnInventoryChanged.Broadcast();
	}
}

void FInventoryItem::PreReplicatedRemove(const FACFInventoryList& InArraySerializer)
{
	// Entry going away entirely: the removed amount is the last observed Count.
	UACFInventoryComponent* InvComp = InArraySerializer.GetOwnerComponent();
	BroadcastCountDelta(InvComp, LastObservedCount, 0);
	LastObservedCount = 0;
}

void FACFInventoryList::ValidateChanges(const TArrayView<int32> AddedIndices)
{
	for (const int32 index : AddedIndices)
	{
		if (Inventory.IsValidIndex(index) && actorOwner)
		{
			FInventoryItem& item = Inventory[index];
			if (!item.Item && item.ItemClass)
			{
				item.Item = NewObject<UACFItem>(actorOwner, item.ItemClass);
				if (item.Item)
				{
					item.Item->SetItemOwner(actorOwner);
				}
			}
			// Fragment UPROPERTY(Replicated) state arrives automatically
			// via subobject replication no manual deserialization needed.
		}
	}
}

// Sets default values for this component's properties
UACFInventoryComponent::UACFInventoryComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
	bReplicateUsingRegisteredSubObjectList = true;
	InventoryList.Init(GetOwner());

	// ...
}

// Called when the game starts
void UACFInventoryComponent::BeginPlay()
{
	Super::BeginPlay();
	actorOwner = GetOwner();
	InventoryList.Init(actorOwner);
	// ...
}

void UACFInventoryComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UACFInventoryComponent, InventoryList);
	DOREPLIFETIME(UACFInventoryComponent, currentInventoryWeight);
}

// ========================================================================
// Fragment Subobject Replication
// ========================================================================

bool UACFInventoryComponent::RegisterFragment(UACFItemFragment* Fragment)
{
	if (!IsValid(Fragment)) { return false; }

	RegisteredFragments.AddUnique(Fragment);
	AddReplicatedSubObject(Fragment);
	return true;
}

bool UACFInventoryComponent::UnregisterFragment(UACFItemFragment* Fragment)
{
	if (!IsValid(Fragment)) { return false; }

	RegisteredFragments.Remove(Fragment);
	RemoveReplicatedSubObject(Fragment);
	return true;
}

void UACFInventoryComponent::RegisterFragmentsForItem(UACFItem* Item)
{
	if (!IsValid(Item)) { return; }

	for (UACFItemFragment* Frag : Item->Fragments)
	{
		if (Frag) { RegisterFragment(Frag); }
	}
}

void UACFInventoryComponent::UnregisterFragmentsForItem(UACFItem* Item)
{
	if (!IsValid(Item)) { return; }

	for (UACFItemFragment* Frag : Item->Fragments)
	{
		if (Frag) { UnregisterFragment(Frag); }
	}
}

TArray<UACFItemFragment*> UACFInventoryComponent::GetRegisteredFragments() const
{
	TArray<UACFItemFragment*> Result;
	for (const TObjectPtr<UACFItemFragment>& Frag : RegisteredFragments)
	{
		if (Frag)
		{
			Result.Add(Frag);
		}
	}
	return Result;
}

bool UACFInventoryComponent::ReplicateSubobjects(UActorChannel* Channel, FOutBunch* Bunch, FReplicationFlags* RepFlags)
{
	// UE 5.1+ uses the registered subobject list automatically via bReplicateUsingRegisteredSubObjectList.
	// This override exists for legacy compatibility only.
	return Super::ReplicateSubobjects(Channel, Bunch, RepFlags);
}

// ========================================================================
// Inventory Logic
// ========================================================================

int32 UACFInventoryComponent::NumberOfItemCanTake(const TSubclassOf<UACFItem>& itemToCheck)
{
	int32 addeditemstotal = 0;
	TArray<FInventoryItem> outItems;
	GetAllItemsOfClassInInventory(itemToCheck, outItems);
	FItemDescriptor itemInfo;
	UACFItemSystemFunctionLibrary::GetItemData(itemToCheck, itemInfo);
	float MaxByWeight = 999.f;
	if (itemInfo.ItemWeight > 0) {
		MaxByWeight = (MaxInventoryWeight - currentInventoryWeight) / itemInfo.ItemWeight;
	}
	const int32 maxAddableByWeight = FMath::TruncToInt(MaxByWeight);
	const int32 FreeSpaceInInventory = MaxInventorySlots - GetInventoryList().Num();
	int32 maxAddableByStack = FreeSpaceInInventory * itemInfo.MaxInventoryStack;
	// IF WE ALREADY HAVE SOME ITEMS LIKE THAT, INCREMENT ACTUAL VALUE
	if (outItems.Num() > 0) {
		for (const auto& outItem : outItems) {
			maxAddableByStack += itemInfo.MaxInventoryStack - outItem.Count;
		}
	}
	addeditemstotal = FGenericPlatformMath::Min(maxAddableByStack, maxAddableByWeight);
	return addeditemstotal;
}

void UACFInventoryComponent::RefreshTotalWeight()
{
	currentInventoryWeight = 0.f;
	const auto& allItems = GetInventoryList().GetAllItems();

	for (const auto& item : allItems) {
		FItemDescriptor itemInfo;
		if (!UACFItemSystemFunctionLibrary::GetItemData(item.ItemClass, itemInfo)) {
			continue;
		}
		currentInventoryWeight += itemInfo.ItemWeight * item.Count;
	}
}

bool UACFInventoryComponent::Internal_CollapseItemsOfClass(const TSubclassOf<UACFItem>& itemClass)
{
	if (!itemClass) {
		return false;
	}

	FItemDescriptor itemData;
	if (!UACFItemSystemFunctionLibrary::GetItemData(itemClass, itemData)) {
		return false;
	}

	const int32 maxStack = itemData.MaxInventoryStack;
	// Nothing to merge for non-stackable items.
	if (maxStack <= 1) {
		return false;
	}

	TArray<FInventoryItem> stacks;
	GetAllItemsOfClassInInventory(itemClass, stacks);
	// A single stack (or none) can never be collapsed further.
	if (stacks.Num() <= 1) {
		return false;
	}

	int32 totalCount = 0;
	for (const FInventoryItem& stack : stacks) {
		totalCount += stack.Count;
	}

	// Build the target distribution: as many full stacks as possible, then a
	// single remainder stack. This is always <= the current number of stacks,
	// so we only ever reuse or remove existing entries (never create new ones).
	const int32 numFullStacks = totalCount / maxStack;
	const int32 remainder = totalCount % maxStack;

	bool bModified = false;
	for (int32 i = 0; i < stacks.Num(); ++i) {
		int32 desiredCount = 0;
		if (i < numFullStacks) {
			desiredCount = maxStack;
		} else if (i == numFullStacks && remainder > 0) {
			desiredCount = remainder;
		}

		FInventoryItem& stack = stacks[i];
		if (stack.Count == desiredCount) {
			continue;
		}

		if (desiredCount <= 0) {
			// Emptied stack: unregister fragments and drop the entry.
			if (stack.Item) {
				UnregisterFragmentsForItem(stack.Item);
			}
			GetInventoryList().RemoveEntry(stack);
		} else {
			stack.Count = desiredCount;
			GetInventoryList().ChangeEntry(stack);
		}
		bModified = true;
	}

	return bModified;
}

void UACFInventoryComponent::CollapseItemsOfClass_Implementation(TSubclassOf<UACFItem> itemClass)
{
	if (Internal_CollapseItemsOfClass(itemClass)) {
		OnInventoryChanged.Broadcast();
	}
}

void UACFInventoryComponent::CollapseInventory_Implementation()
{
	// Gather the unique stackable classes currently in the inventory.
	TArray<TSubclassOf<UACFItem>> uniqueClasses;
	for (const FInventoryItem& item : GetInventoryListConst().GetAllItems()) {
		if (item.ItemClass) {
			uniqueClasses.AddUnique(item.ItemClass);
		}
	}

	bool bModified = false;
	for (const TSubclassOf<UACFItem>& itemClass : uniqueClasses) {
		bModified |= Internal_CollapseItemsOfClass(itemClass);
	}

	if (bModified) {
		OnInventoryChanged.Broadcast();
	}
}

void UACFInventoryComponent::AddItemToInventory_Implementation(const FBaseItem& ItemToAdd, bool bAutoEquip)
{
	Internal_AddItem(ItemToAdd, bAutoEquip);
}

void UACFInventoryComponent::AddInventoryItem_Implementation(const FInventoryItem& ItemToAdd)
{
	Internal_AddInventoryItem(ItemToAdd);
}

void UACFInventoryComponent::AddItemToInventoryByClass_Implementation(TSubclassOf<UACFItem> inItem, int32 count /*= 1*/, bool bAutoEquip)
{
	AddItemToInventory(FBaseItem(inItem, count), bAutoEquip);
}

void UACFInventoryComponent::RemoveItemByIndex_Implementation(const int32 index, int32 count /*= 1*/)
{
	FInventoryItem outItem;
	if (GetInventoryList().GetItemByIndex(index, outItem)) {
		RemoveItem(outItem, count);
	}
}

void UACFInventoryComponent::RemoveItem_Implementation(const FInventoryItem& item, int32 count /*= 1*/)
{
	FInventoryItem outItem;

	if (GetItemByGuid(item.GetItemGuid(), outItem)) {
		const int32 finalCount = FMath::Min(count, outItem.Count);
		FItemDescriptor itemInfo;
		if (!UACFItemSystemFunctionLibrary::GetItemData(outItem.ItemClass, itemInfo)) {
			return;
		}
		const float weightRemoved = finalCount * itemInfo.ItemWeight;
		outItem.Count -= finalCount;


		if (outItem.Count <= 0) {
			// Unregister fragments from replication before removing the entry
			if (outItem.Item)
			{
				UnregisterFragmentsForItem(outItem.Item);
			}
			GetInventoryList().RemoveEntry(outItem);
		}
		else {
			GetInventoryList().ChangeEntry(outItem);
		}

		currentInventoryWeight -= weightRemoved;
		HandleItemRemoved(outItem, count);
		OnItemRemoved.Broadcast(FBaseItem(item.ItemClass, finalCount));

		OnInventoryChanged.Broadcast();
	}
}

bool UACFInventoryComponent::HasEnoughItemsOfType(const TArray<FBaseItem>& ItemsToCheck) const
{
	for (const FBaseItem& item : ItemsToCheck) {
		int32 numberToCheck = item.Count;
		TArray<FInventoryItem> invItems;

		GetAllItemsOfClassInInventory(item.ItemClass, invItems);
		int32 TotItems = 0;
		for (const auto& invItem : invItems) {
			TotItems += invItem.Count;
		}

		if (TotItems < numberToCheck) {
			return false;
		}
	}
	return true;
}

bool UACFInventoryComponent::HasAnyItemOfType(const TSubclassOf<UACFItem>& itemToCheck) const
{
	const auto& allItems = GetInventoryListConst().GetAllItems();

	for (const auto& item : allItems) {
		if (item.ItemClass == itemToCheck) {
			return true;
		}
	}
	return false;
}

void UACFInventoryComponent::ConsumeItems_Implementation(const TArray<FBaseItem>& ItemsToCheck)
{
	for (const auto& item : ItemsToCheck) {
		int32 remainingToRemove = item.Count;
		TArray<FInventoryItem> invItems;
		GetAllItemsOfClassInInventory(item.ItemClass, invItems);

		// Loop through all stacks of this item type until we've removed the required count
		for (const auto& invItem : invItems) {
			if (remainingToRemove <= 0) {
				break;
			}

			// Remove as much as we can from this stack
			const int32 toRemoveFromThisStack = FMath::Min(remainingToRemove, invItem.Count);
			RemoveItem(invItem, toRemoveFromThisStack);
			remainingToRemove -= toRemoveFromThisStack;
		}

		// Optional: Log warning if we couldn't remove all required items
		if (remainingToRemove > 0) {
			UE_LOG(ACFInventoryLog, Warning, TEXT("ConsumeItems: Could not remove all required items. Still need %d of %s"),
				remainingToRemove, *item.ItemClass->GetName());
		}
	}
}

void UACFInventoryComponent::MoveItemsFromInventory_Implementation(const TArray<FInventoryItem>& inItems, UACFInventoryComponent* sourceInventory)
{
	if (!sourceInventory) {
		UE_LOG(ACFInventoryLog, Error,
			TEXT("Invalid StsourceInventoryorage, verify that the owner of this component is "
				"replicated! - ACFEquipmentComp"));
		return;
	}
	for (const auto& item : inItems) {

		const int32 numItems = Internal_AddInventoryItem(item);
		if (numItems > 0) {
			sourceInventory->RemoveItem(item, numItems);
		}
	}
}

void UACFInventoryComponent::HandleItemRemoved(const FInventoryItem& item, int32 count)
{
}

void UACFInventoryComponent::HandleItemAdded(const FInventoryItem& item, int32 count /*= 1*/, bool bTryToEquip /*= true*/, FGameplayTag equipSlot)
{
}

void UACFInventoryComponent::OnRep_Inventory()
{
	OnInventoryChanged.Broadcast();
}

/**
 * Helper: Re-outer all fragment instances on an item to the given Actor.
 * This is required for subobject replication
 * by walking the outer chain, which must lead to a replicated Actor.
 * Fragments created by the CDO/archetype system have UACFItem as their outer,
 * which is a non-replicated UObject and can't be resolved on the client.
 */
static void ReparentFragmentsToActor(UACFItem* Item, AActor* Actor)
{
	if (!Item || !Actor) { return; }
	for (UACFItemFragment* Frag : Item->Fragments)
	{
		if (Frag && Frag->GetOuter() != Actor)
		{
			Frag->Rename(nullptr, Actor);
		}
	}
}

int32 UACFInventoryComponent::Internal_AddInventoryItem(const FInventoryItem& ItemToAdd, bool bTryToEquip)
{
	if (ItemToAdd.ItemClass) {
		FItemDescriptor itemData;
		UACFItemSystemFunctionLibrary::GetItemData(ItemToAdd.ItemClass, itemData);
		// we don't check the stack size if the max is 1, we just add the item to the inventory
		if (itemData.MaxInventoryStack == 1 && ItemToAdd.Count == 1 && NumberOfItemCanTake(ItemToAdd.ItemClass) > 0) {
			FInventoryItem toAdd = ItemToAdd;
			toAdd.bIsEquipped = false;

			// Reuse the live UACFItem* if present (preserves runtime state through transfers).
			// Only create a new instance if the incoming item has no live pointer.
			if (toAdd.Item && IsValid(toAdd.Item))
			{
				toAdd.Item->Rename(nullptr, GetOwner());
				toAdd.Item->SetItemOwner(GetOwner());
			}
			else if (toAdd.ItemClass && GetOwner())
			{
				toAdd.Item = NewObject<UACFItem>(GetOwner(), toAdd.ItemClass);
				if (toAdd.Item) { toAdd.Item->SetItemOwner(GetOwner()); }
			}
			// Re-outer fragments to the Actor so the replication system can resolve them,
			// then register for replication directly on this component
			if (toAdd.Item)
			{
				ReparentFragmentsToActor(toAdd.Item, GetOwner());
				RegisterFragmentsForItem(toAdd.Item);
			}
			GetInventoryList().AddEntry(toAdd);
			currentInventoryWeight += itemData.ItemWeight;
			OnInventoryChanged.Broadcast();
			OnItemAdded.Broadcast(FBaseItem(ItemToAdd.ItemClass, ItemToAdd.Count));
			HandleItemAdded(toAdd, toAdd.Count, bTryToEquip, FGameplayTag()); // HandleItemAdded with default equip slot
			return ItemToAdd.Count;
		}
		else {
			const int32 addedItems = Internal_AddItem(FBaseItem(ItemToAdd), bTryToEquip, ItemToAdd.DropChancePercentage);
			if (addedItems > 0) {
				OnInventoryChanged.Broadcast();
				//OnItemAdded.Broadcast(FBaseItem(ItemToAdd.ItemClass, addedItems));
			}
			return addedItems;
		}
	}
	else {
		UE_LOG(ACFInventoryLog, Error, TEXT("Invalid ItemInstance in AddInventoryItem_Implementation! - UACFInventoryComponent"));
	}
	return -1;
}

int32 UACFInventoryComponent::Internal_AddItem(const FBaseItem& itemToAdd, bool bTryToEquip /*= false*/, float dropChancePercentage /*= 0.f*/, FGameplayTag equipSlot /*= FGameplayTag()*/)
{

	if (!itemToAdd.ItemClass) {
		UE_LOG(ACFInventoryLog, Warning,
			TEXT("Invalid ItemClass! - UACFEquipmentComponent::Internal_AddItem"));
		return -1;
	}
	int32 addeditemstotal = 0;
	int32 addeditemstmp = 0;
	bool bSuccessful = false;

	FItemDescriptor itemData;

	UACFItemSystemFunctionLibrary::GetItemData(itemToAdd.ItemClass, itemData);

	if (itemData.MaxInventoryStack == 0) {
		UE_LOG(ACFInventoryLog, Warning,
			TEXT("Max Inventory Stack cannot be 0!!!! - UACFEquipmentComponent::Internal_AddItem"));
		return -1;
	}

	if (currentInventoryWeight >= MaxInventoryWeight) {
		return -1;
	}
	const float itemweight = itemData.ItemWeight;
	int32 maxAddableByWeightTotal = itemToAdd.Count;
	if (itemweight > 0) {
		maxAddableByWeightTotal = FMath::TruncToInt(
			(MaxInventoryWeight - currentInventoryWeight) / itemweight);
	}
	int32 count = itemToAdd.Count;
	if (maxAddableByWeightTotal < itemToAdd.Count) {
		count = maxAddableByWeightTotal;
	}

	if (count <= 0) {
		return -1;
	}

	TArray<FInventoryItem> outItems;
	GetAllItemsOfClassInInventory(itemToAdd.ItemClass, outItems);
	// IF WE ALREADY HAVE SOME ITEMS LIKE THAT, INCREMENT ACTUAL VALUE

	if (outItems.Num() > 0) {
		for (auto& outItem : outItems) {
			if (outItem.Count < itemData.MaxInventoryStack) {
				// `count` is already constrained by the max inventory weight.
				if (outItem.Count + count <= itemData.MaxInventoryStack) {
					addeditemstmp = count;
				}
				else {
					int32 maxAddableByStack = itemData.MaxInventoryStack - outItem.Count;
					addeditemstmp = maxAddableByStack;
				}

				outItem.Count += addeditemstmp;
				addeditemstotal += addeditemstmp;
				count -= addeditemstmp;
				outItem.DropChancePercentage = dropChancePercentage;
				GetInventoryList().ChangeEntry(outItem);
				HandleItemAdded(outItem, addeditemstmp, bTryToEquip, equipSlot);

				bSuccessful = true;
			}
		}
	}

	// If an existing item hasn't had its count incremeneted, then we add a new item
	const int32 NumberOfItemNeed = FMath::CeilToInt((float)count / (float)itemData.MaxInventoryStack);
	const int32 FreeSpaceInInventory = MaxInventorySlots - GetInventoryList().Num();
	const int32 NumberOfStackToCreate = FGenericPlatformMath::Min(NumberOfItemNeed, FreeSpaceInInventory);
	for (int32 i = 0; i < NumberOfStackToCreate; i++) {
		if (GetInventoryList().Num() < MaxInventorySlots) {
			FInventoryItem newItem(itemToAdd);
			newItem.ResetGuid();//this
			if (count > itemData.MaxInventoryStack) {
				newItem.Count = itemData.MaxInventoryStack;
			}
			else {
				newItem.Count = count;
			}
			newItem.DropChancePercentage = dropChancePercentage;
			if (newItem.ItemClass && GetOwner()) {
				newItem.Item = NewObject<UACFItem>(GetOwner(), newItem.ItemClass);
				if (newItem.Item)
				{
					newItem.Item->SetItemOwner(GetOwner());
					ReparentFragmentsToActor(newItem.Item, GetOwner());
					RegisterFragmentsForItem(newItem.Item);
				}
			}
			addeditemstotal += newItem.Count;
			count -= newItem.Count;
			GetInventoryList().AddEntry(newItem);

			HandleItemAdded(newItem, newItem.Count, bTryToEquip, equipSlot);

			bSuccessful = true;
		}
	}
	if (bSuccessful) {
		currentInventoryWeight += itemData.ItemWeight * addeditemstotal;
		OnInventoryChanged.Broadcast();
		if (addeditemstotal > 0) {
			OnItemAdded.Broadcast(FBaseItem(itemToAdd.ItemClass, addeditemstotal));
		}
		return addeditemstotal;
	}

	return addeditemstotal;
}

bool UACFInventoryComponent::GetItemByGuid(const FGuid& itemGuid, FInventoryItem& outItem) const
{
	return GetInventoryListConst().GetItem(itemGuid, outItem);
}

void UACFInventoryComponent::SetItemGridIndex_Implementation(const FGuid& itemGuid, const int32 index)
{
	GetInventoryList().SetItemIndex(itemGuid, index);
}


int32 UACFInventoryComponent::GetTotalCountOfItemsByClass(const TSubclassOf<UACFItem>& ItemClass) const
{
	int32 totalItems = 0;
	TArray<FInventoryItem> outItems;
	GetAllItemsOfClassInInventory(ItemClass, outItems);

	for (const auto& item : outItems) {
		totalItems += item.Count;
	}
	return totalItems;
}

void UACFInventoryComponent::GetAllItemsOfClassInInventory(const TSubclassOf<UACFItem>& ItemClass, TArray<FInventoryItem>& outItems) const
{
	outItems.Empty();
	const auto& allItems = GetInventoryListConst().GetAllItems();

	for (const auto& item : allItems) {
		if (item.ItemClass == ItemClass) {
			outItems.Add(item);
		}
	}
}

void UACFInventoryComponent::GetAllSellableItemsInInventory(TArray<FInventoryItem>& outItems) const
{
	outItems.Empty();
	const auto& allItems = GetInventoryListConst().GetAllItems();
	for (const auto& item : allItems) {
		FItemDescriptor itemData;
		UACFItemSystemFunctionLibrary::GetItemData(item.ItemClass, itemData);
		if (itemData.bSellable) {
			outItems.Add(item);
		}
	}
}

bool UACFInventoryComponent::FindFirstItemOfClassInInventory(const TSubclassOf<UACFItem>& ItemClass, FInventoryItem& outItem) const
{
	TArray<FInventoryItem> outItems;
	GetAllItemsOfClassInInventory(ItemClass, outItems);
	if (outItems.Num() > 0) {
		outItem = outItems[0];
		return true;
	}

	return false;
}

void UACFInventoryComponent::UseConsumableOnTarget(const FInventoryItem& Inventoryitem, APawn* target)
{
	UACFConsumable* consumable = Cast<UACFConsumable>(Inventoryitem.Item);
	if (consumable && consumable->CanBeUsed(target)) {
		Internal_UseItem(consumable, target, Inventoryitem);
	}
}

bool UACFInventoryComponent::CanUseConsumable(const FInventoryItem& Inventoryitem, APawn* target) const
{
	UACFConsumable* consumable = Cast<UACFConsumable>(Inventoryitem.Item);
	return consumable && consumable->CanBeUsed(target);
}

void UACFInventoryComponent::Internal_UseItem(UACFConsumable* consumable, APawn* target, const FInventoryItem& Inventoryitem)
{
	if (consumable && consumable->CanBeUsed(target)) {

		consumable->Internal_UseItem(target);
		if (consumable->GetConsumeOnUse()) {
			RemoveItem(Inventoryitem, 1);
		}
	}
	else {
		UE_LOG(ACFInventoryLog, Error, TEXT("Invalid Consumable!!! - UACFEquipmentComponent::UseConsumableOnTarget"));
	}
}

void FACFInventoryList::Empty()
{
	// Unregister all fragments before clearing
	if (actorOwner)
	{
		if (UACFInventoryComponent* InvComp = actorOwner->FindComponentByClass<UACFInventoryComponent>())
		{
			for (FInventoryItem& InvItem : Inventory)
			{
				if (InvItem.Item)
				{
					InvComp->UnregisterFragmentsForItem(InvItem.Item);
				}
			}
		}
	}
	Inventory.Empty();
	MarkArrayDirty();
}

void FACFInventoryList::PreReplicatedRemove(const TArrayView<int32> RemovedIndices, int32 FinalSize)
{
	if (actorOwner)
	{
		if (UACFInventoryComponent* InvComp = actorOwner->FindComponentByClass<UACFInventoryComponent>())
		{
			for (const int32 Index : RemovedIndices)
			{
				if (Inventory.IsValidIndex(Index) && Inventory[Index].Item)
				{
					InvComp->UnregisterFragmentsForItem(Inventory[Index].Item);
				}
			}
		}
	}
}

void UACFInventoryComponent::Serialize(FArchive& Ar)
{
	Super::Serialize(Ar);

	if (!Ar.IsSaveGame())
	{
		return;
	}

	// Super::Serialize does not properly restore FACFInventoryList.Inventory because
	// FFastArraySerializer overrides archive serialization for network delta use.
	// We handle inventory composition explicitly here, then let SaveLoad restore UACFItem objects.

	if (Ar.IsSaving())
	{
		TArray<FInventoryItem> Items = InventoryList.GetAllItems();
		int32 Count = Items.Num();
		Ar << Count;
		for (FInventoryItem& Item : Items)
		{
			UClass* Class = Item.ItemClass;
			Ar << Class;
			Ar << Item.Count;
			FGuid Guid = Item.GetItemGuid();
			Ar << Guid;
			Ar << Item.bIsEquipped;
			Ar << Item.EquipmentSlot;
			Ar << Item.DropChancePercentage;
			Ar << Item.ItemIndex;
		}
	}
	else
	{
		InventoryList.Empty();
		int32 Count = 0;
		Ar << Count;
		for (int32 i = 0; i < Count; ++i)
		{
			UClass* Class = nullptr;
			int32 ItemCount = 1;
			FGuid Guid;
			bool bEquipped = false;
			FGameplayTag Slot;
			float DropChance = 0.f;
			int32 Index = 0;

			Ar << Class;
			Ar << ItemCount;
			Ar << Guid;
			Ar << bEquipped;
			Ar << Slot;
			Ar << DropChance;
			Ar << Index;

			if (Class)
			{
				FInventoryItem NewItem;
				NewItem.ItemClass = TSubclassOf<UACFItem>(Class);
				NewItem.Count = ItemCount;
				NewItem.ForceGuid(Guid);
				NewItem.bIsEquipped = bEquipped;
				NewItem.EquipmentSlot = Slot;
				NewItem.DropChancePercentage = DropChance;
				NewItem.ItemIndex = Index;
				InventoryList.AddEntry(NewItem);
			}
		}
	}

	InventoryList.SaveLoad(Ar);
}

void FACFInventoryList::SaveLoad(FArchive& Ar)
{
	constexpr int32 VersionSentinel = -1;

	if (Ar.IsSaving())
	{
		int32 Sentinel = VersionSentinel;
		int32 Version = 1;
		int32 ItemCount = Inventory.Num();
		Ar << Sentinel;
		Ar << Version;
		Ar << ItemCount;

		for (int32 i = 0; i < ItemCount; ++i)
		{
			FInventoryItem& InvItem = Inventory[i];
			bool bHasItem = (InvItem.Item != nullptr);
			Ar << bHasItem;
			if (InvItem.Item)
			{
				InvItem.Item->Serialize(Ar);
			}
		}
	}
	else
	{
		if (Ar.AtEnd())
		{
			for (FInventoryItem& InvItem : Inventory)
			{
				if (!InvItem.Item && InvItem.ItemClass && actorOwner)
				{
					InvItem.Item = NewObject<UACFItem>(actorOwner, InvItem.ItemClass);
					if (InvItem.Item) { InvItem.Item->SetItemOwner(actorOwner); }
				}
			}
			return;
		}

		int32 MaybeSentinel = 0;
		Ar << MaybeSentinel;

		if (MaybeSentinel != VersionSentinel)
		{
			for (FInventoryItem& InvItem : Inventory)
			{
				if (!InvItem.Item && InvItem.ItemClass && actorOwner)
				{
					InvItem.Item = NewObject<UACFItem>(actorOwner, InvItem.ItemClass);
					if (InvItem.Item) { InvItem.Item->SetItemOwner(actorOwner); }
				}
			}
			return;
		}

		int32 Version = 1;
		int32 ItemCount = 0;
		Ar << Version;
		Ar << ItemCount;
		ItemCount = FMath::Min(ItemCount, Inventory.Num());

		for (int32 i = 0; i < ItemCount; ++i)
		{
			FInventoryItem& InvItem = Inventory[i];
			bool bHasItem = false;
			Ar << bHasItem;
			if (bHasItem)
			{
				if (!InvItem.Item && InvItem.ItemClass && actorOwner)
				{
					InvItem.Item = NewObject<UACFItem>(actorOwner, InvItem.ItemClass);
					if (InvItem.Item) { InvItem.Item->SetItemOwner(actorOwner); }
				}
				if (InvItem.Item)
				{
					InvItem.Item->Serialize(Ar);
				}
			}
		}

		for (int32 i = ItemCount; i < Inventory.Num(); ++i)
		{
			FInventoryItem& InvItem = Inventory[i];
			if (!InvItem.Item && InvItem.ItemClass && actorOwner)
			{
				InvItem.Item = NewObject<UACFItem>(actorOwner, InvItem.ItemClass);
				if (InvItem.Item) { InvItem.Item->SetItemOwner(actorOwner); }
			}
		}
	}
}