// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFEquipmentComponent.h"

#include <GameFramework/CharacterMovementComponent.h>
#include <GameplayTagContainer.h>
#include <Kismet/KismetSystemLibrary.h>
#include <NavigationSystem.h>

#include "ACFItemSystemFunctionLibrary.h"
#include "ARSStatisticsComponent.h"
#include "Components/ACFArmorSlotComponent.h"
#include "Components/ACFStorageComponent.h"
#include "GameFramework/Character.h"
#include "ItemActors/ACFItemActor.h"
#include "ItemActors/ACFMeleeWeaponActor.h"
#include "ItemActors/ACFProjectileActor.h"
#include "ItemActors/ACFRangedWeaponActor.h"
#include "ItemActors/ACFWeaponActor.h"
#include "Items/ACFAccessory.h"
#include "Items/ACFArmor.h"
#include "Items/ACFConsumable.h"
#include "Items/ACFEquippableItem.h"
#include "Items/ACFItem.h"
#include "Items/ACFMeleeWeapon.h"
#include "Items/ACFProjectile.h"
#include "Items/ACFRangedWeapon.h"
#include "Items/ACFWeapon.h"
#include "Items/ACFWorldItem.h"
#include "Kismet/KismetMathLibrary.h"
#include "Net/UnrealNetwork.h"
#include <GameFramework/Actor.h>
#include <Logging.h>

#include "DelayAction.h"

FEquippedItem::FEquippedItem(const FInventoryItem& item, const FGameplayTag& itemSlot, UACFItem* itemPtr, AACFItemActor* inActor, const TSubclassOf<UACFItem>& inItemClass)

{
	ItemSlot = itemSlot;
	ItemGuid = item.GetItemGuid();
	ItemActor = inActor;
	Item = itemPtr;
	ItemClass = inItemClass;
}

void FEquippedItem::Init(TObjectPtr<UACFEquipmentComponent> ownerComp)
{
	if (ownerComp) {
		//FInventoryItem item;
		//ownerComp->GetItemByGuid(ItemGuid, item);
		ensure(ItemClass);
		//TO DO: Try to replicate the original instance for runtime item edits
		if (!Item && ItemClass) {
			Item = NewObject<UACFItem>(ownerComp->GetOwner(), ItemClass);

		}
		APawn* itemOwner = Cast<APawn>(ownerComp->GetOwner());
		if (ItemActor) {
			ItemActor->InitItemActor(itemOwner, Item);
		}
	}
}

bool FEquippedItem::IsValid()
{
	return Item && ItemActor && ItemActor->IsFullyInit();
}

void FEquipment::ValidateChanges(const TArrayView<int32> AddedIndices)
{
	for (const int32 index : AddedIndices) {
		if (EquippedItems.IsValidIndex(index) && !EquippedItems[index].IsValid()) {
			EquippedItems[index].Init(ownerComp);
		}
	}
}

void UACFEquipmentComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFEquipmentComponent, Equipment);
	DOREPLIFETIME(UACFEquipmentComponent, CurrentlyEquippedSlotType);
	DOREPLIFETIME(UACFEquipmentComponent, MainWeapon);
	DOREPLIFETIME(UACFEquipmentComponent, SecondaryWeapon);
}

// Sets default values for this component's properties
UACFEquipmentComponent::UACFEquipmentComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked
	// every frame.  You can turn these features off to improve performance if you
	// don't need them.
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
	Equipment.Init(this);
}

void UACFEquipmentComponent::BeginPlay()
{
	Super::BeginPlay();

	GatherActorOwner();
	GatherMainMesh();
}

void UACFEquipmentComponent::GatherActorOwner()
{
	if (!ActorOwner) {
		ActorOwner = GetOwner();
		
		GatherMainMesh();

		
		Equipment.Init(this);
	}
}

void UACFEquipmentComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{

	if (EndPlayReason == EEndPlayReason::RemovedFromWorld) {
		SheathCurrentWeapon();
	}
	Super::EndPlay(EndPlayReason);
}

void UACFEquipmentComponent::OnComponentLoaded_Implementation()
{
	DestroyEquipment();
	//DestroyEquippedItems();
	Equipment.Empty();
	const auto& allItems = GetInventoryList().GetAllItems();
	for (const auto& slot : allItems) {
		if (slot.bIsEquipped) {
			EquipItemFromInventory(slot);
		}
	}
	RefreshTotalWeight();
}

void UACFEquipmentComponent::DropItem_Implementation(const FInventoryItem& item, int32 count /*= 1*/)
{
	GetInventoryList().ContainsItem(item);
	FItemDescriptor itemInfo;
	if (!UACFItemSystemFunctionLibrary::GetItemData(item.ItemClass, itemInfo)) {
		return;
	}
	if (itemInfo.bDroppable) {
		// Capture the live inventory item BEFORE RemoveItem destroys the entry.
		FInventoryItem liveItem;
		if (!GetItemByGuid(item.GetItemGuid(), liveItem)) {
			return;
		}

		// Build drop carrying the live UACFItem* pointer
		FInventoryItem dropItem = liveItem;
		dropItem.Count = FMath::Min(count, liveItem.Count);

		if (ActorOwner) {
			FVector DropLocation = ActorOwner->GetActorLocation();
			if (const ACharacter* Character = Cast<ACharacter>(ActorOwner)) {
				DropLocation.Z -= Character->GetSimpleCollisionHalfHeight();
			}
			UACFItemSystemFunctionLibrary::SpawnWorldItemWithInstance(this, dropItem, DropLocation);
		}

		RemoveItem(item, count);
	}
}

void UACFEquipmentComponent::InitializeStartingItems()
{
	if (GetOwner()->HasAuthority()) {
		SetIsInitialized(true);
		GetInventoryList().Empty();
		currentInventoryWeight = 0.f;
		for (const FStartingItem& item : GetStartingItems()) {
			Internal_AddItem(item, item.bAutoEquip, item.DropChancePercentage);
			if (GetInventoryList().Num() > MaxInventorySlots) {
				UE_LOG(ACFInventoryLog, Log, TEXT("Invalid Inventory setup, too many slots on character!!! - "
					"ACFEquipmentComp"));
			}
		}
	}
}

void UACFEquipmentComponent::UseInventoryItem_Implementation(const FInventoryItem& item)
{
	FInventoryItem invItem;
	if (GetItemByGuid(item.GetItemGuid(), invItem)) {
		if (!invItem.bIsEquipped) {
			EquipItemFromInventory(invItem);
		}
		else {
			UnequipItemBySlot(invItem.EquipmentSlot);
		}
	}
}

void UACFEquipmentComponent::UseInventoryItemByIndex_Implementation(int32 index)
{
	FInventoryItem item;
	if (GetInventoryList().GetItemByIndex(index, item)) {
		UseInventoryItem(item);
	}
}

FGameplayTag UACFEquipmentComponent::GetCurrentDesiredMovesetTag() const
{
	if (GetCurrentOffhandWeapon() && GetCurrentOffhandWeapon()->OverridesMainHandMoveset()) {
		return GetCurrentOffhandWeapon()->GetAssociatedMovesetTag();
	}
	else if (GetCurrentMainWeapon()) {
		return GetCurrentMainWeapon()->GetAssociatedMovesetTag();
	}
	return FGameplayTag();
}

FGameplayTag UACFEquipmentComponent::GetCurrentDesiredMovesetActionTag() const
{
	if (GetCurrentOffhandWeapon() && GetCurrentOffhandWeapon()->OverridesMainHandMovesetActions()) {
		return GetCurrentOffhandWeapon()->GetAssociatedMovesetActionsTag();
	}
	else if (GetCurrentMainWeapon()) {
		return GetCurrentMainWeapon()->GetAssociatedMovesetActionsTag();
	}
	return FGameplayTag();
}

FGameplayTag UACFEquipmentComponent::GetCurrentDesiredOverlayTag() const
{
	if (GetCurrentOffhandWeapon() && GetCurrentOffhandWeapon()->OverridesMainHandOverlay()) {
		return GetCurrentOffhandWeapon()->GetAssociatedMovesetOverlayTag();
	}
	else if (GetCurrentMainWeapon()) {
		return GetCurrentMainWeapon()->GetAssociatedMovesetOverlayTag();
	}
	return FGameplayTag();
}

void UACFEquipmentComponent::OnRep_Equipment()
{
	RefreshEquipment();
	OnEquipmentChanged.Broadcast(Equipment);
}

void UACFEquipmentComponent::RefreshEquipment()
{
	if (!ActorOwner) {
		ActorOwner = GetOwner();
	}
	FillModularMeshes();
	APawn* PawnOwner = Cast<APawn>(ActorOwner);
	for (const auto& item : Equipment.GetEquippedItems()) {
		if (item.Item && PawnOwner) {
			item.Item->SetItemOwner(PawnOwner);
		}
		UACFEquippableItem* equippable = Cast<UACFEquippableItem>(item.Item);
		if (equippable) {
			AACFWeaponActor* WeaponToEquip = Cast<AACFWeaponActor>(item.ItemActor);
			if (WeaponToEquip) {
				if (WeaponToEquip == GetCurrentMainWeapon() || WeaponToEquip == GetCurrentOffhandWeapon()) {
					continue;
				}
				else {
					AttachWeaponOnBody(WeaponToEquip);
				}
			}

			UACFArmor* ArmorToEquip = Cast<UACFArmor>(equippable);
			if (ArmorToEquip) {
				AddSkeletalMeshComponent(item);
			}
		}
	}
}

void UACFEquipmentComponent::ClearAllInventoryAndEquipment()
{	
	// Remove all items from inventory properly (triggers events and UI updates)
	TArray<FInventoryItem> InventoryItemsCopy = GetInventoryList().GetAllItems();
	for (const FInventoryItem& InvItem : InventoryItemsCopy)
	{
		RemoveItem(InvItem, InvItem.Count);
	}
}

void UACFEquipmentComponent::CopyEquipmentFrom(UACFEquipmentComponent* SourceEquipment)
{
	if (!SourceEquipment)
	{
		return;
	}

	// Clear current equipment and inventory
	ClearAllInventoryAndEquipment();

	// Get all equipped items from source
	const TArray<FEquippedItem>& SourceEquippedItems = SourceEquipment->GetCurrentEquipment().GetEquippedItems();

	// Copy each equipped item
	for (const FEquippedItem& EquippedItem : SourceEquippedItems)
	{
		if (EquippedItem.ItemClass)
		{
			// Create a base item from the equipped item
			FBaseItem ItemToCopy;
			ItemToCopy.ItemClass = EquippedItem.ItemClass;
			ItemToCopy.Count = 1;

			// Add and equip the item
			Internal_AddItem(ItemToCopy, true, 0.f, EquippedItem.ItemSlot);
		}
	}

	// Refresh to apply visual changes
	RefreshEquipment();
}

bool UACFEquipmentComponent::ShouldUseLeftHandIK() const
{
	if (LeftHandIKOverride.IsValid())
	{
		return true;
	}
	if (GetCurrentMainWeapon()) {
		return GetCurrentMainWeapon()->IsUsingLeftHandIK();
	}
	return false;
}

FVector UACFEquipmentComponent::GetLeftHandIkPos() const
{
	if (LeftHandIKOverride.IsValid())
	{
		return LeftHandIKOverride->GetComponentLocation();
	}
	if (GetCurrentMainWeapon()) {
		return GetCurrentMainWeapon()->GetLeftHandleIKPosition();
	}
	return FVector();
}

void UACFEquipmentComponent::SetLeftHandIKOverride(USceneComponent* Component)
{
	LeftHandIKOverride = Component;
}

void UACFEquipmentComponent::ClearLeftHandIKOverride()
{
	LeftHandIKOverride = nullptr;
}

bool UACFEquipmentComponent::IsSlotAvailable(const FGameplayTag& itemSlot) const
{
	if (itemSlot == FGameplayTag()) {
		return false;
	}

	if (!UACFItemSystemFunctionLibrary::IsValidItemSlotTag(itemSlot)) {
		UE_LOG(ACFInventoryLog, Log, TEXT("Invalid item Slot Tag!!! -  " "UACFEquipmentComponent::IsSlotAvailable"));
		return false;
	}
	return !Equipment.GetEquippedItems().Contains(itemSlot) && GetAvailableEquipmentSlot().Contains(itemSlot);
}

bool UACFEquipmentComponent::TryFindAvailableItemSlot(const TArray<FGameplayTag>& itemSlots, FGameplayTag& outAvailableSlot)
{
	for (const auto& slot : itemSlots) {
		if (IsSlotAvailable(slot)) {
			outAvailableSlot = slot;
			return true;
		}
	}
	return false;
}

bool UACFEquipmentComponent::HaveAtLeastAValidSlot(const TArray<FGameplayTag>& itemSlots)
{
	for (const auto& slot : itemSlots) {
		if (GetAvailableEquipmentSlot().Contains(slot)) {
			return true;
		}
	}
	return false;
}

void UACFEquipmentComponent::OnRep_SheathedWeap()
{
	OnEquipmentChanged.Broadcast(Equipment);
}

void UACFEquipmentComponent::FillModularMeshes()
{
	TArray<UACFArmorSlotComponent*> slots;
	GetOwner()->GetComponents<UACFArmorSlotComponent>(slots, false);
	ModularMeshes.Empty();
	for (const auto& slot : slots) {
		ModularMeshes.Add(FModularPart(slot));
		if (Equipment.GetEquippedItems().Contains(slot->GetSlotTag())) {
			slot->SetLeaderPoseComponent(MainCharacterMesh);
		}
		else {
			Internal_OnArmorUnequipped(slot->GetSlotTag());
		}
	}
}

void UACFEquipmentComponent::OnEntityOwnerDeath_Implementation()
{
	if (ActorOwner && bDropItemsOnDeath) {
		TArray<AActor*> attachedActors;
		ActorOwner->GetAttachedActors(attachedActors, true);
		TArray<FBaseItem> projCount;
		for (const auto& actor : attachedActors) {
			if (IsValid(actor) && !actor->IsPendingKillPending()) {
				AACFProjectileActor* proj = Cast<AACFProjectileActor>(actor);
				if (IsValid(proj)) {
					UACFProjectile* projectile = Cast<UACFProjectile>(proj->GetProjectileDefinition());
					// If the projectile should be dropped on death, we check the drop chance.
					const float percentage = FMath::RandRange(0.f, 100.f);

					if (proj->ShouldBeDroppedOnDeath() && proj->GetDropOnDeathPercentage() >= percentage) {
						if (projCount.Contains(proj->GetClass())) {
							FBaseItem* actualItem = projCount.FindByKey(proj->GetClass());
							actualItem->Count += 1;
						}
						else {
							projCount.Add(FBaseItem(proj->GetClass(), 1));
						}
					}
					proj->SetLifeSpan(0.2f);
				}
			}
		}

		// World-item spawning is server-only (the actor is replicated). When collapsing,
		// hand the projectiles off to DestroyEquippedItems so everything ends up in a
		// single world item instead of one for projectiles + one for the inventory.
		if (GetOwner()->HasAuthority() && projCount.Num() > 0) {
			// We defer the projectile drops to PendingDeathDropsAccumulator only when
			// DestroyEquippedItems will actually spawn a collapsed world item that will
			// consume the accumulator (i.e. bDropItemsOnDeath is on, since that's what
			// we now pass as bSpawnDrops). Otherwise the accumulator would never be
			// consumed and the projectiles would silently disappear.
			const bool bWillCollapseWithInventory = bCollapseDropInASingleWorldItem && bDropItemsOnDeath;
			if (bWillCollapseWithInventory) {
				PendingDeathDropsAccumulator.Append(projCount);
			}
			else {
				UACFItemSystemFunctionLibrary::SpawnWorldItemNearLocation(this, projCount, ActorOwner->GetActorLocation(), 100.f);
			}
		}
	}
	// DestroyEquippedItems is a Server RPC: only call it from the authority.
	// OnEntityOwnerDeath fires on ALL machines (server via HandleStatReachedZero,
	// clients via OnRep_IsAlive → HandleCharacterDeath). Without the authority guard
	// the server would execute Internal_DestroyEquipment twice, causing it to call
	// SetLifeSpan on actors that are already pending kill.
	//
	// Note: the destruction of equipped ItemActors must happen ALWAYS on death (otherwise
	// they remain as orphaned replicated world actors on the corpse), regardless of
	// bDestroyItemsOnDeath. The drop, instead, is opt-in via bDropItemsOnDeath.
	if (GetOwner()->HasAuthority())
	{
		DestroyEquippedItems(/*bSpawnDrops=*/bDropItemsOnDeath);
	}
}


void UACFEquipmentComponent::GatherMainMesh()
{
	// Find main mesh using component tag if specified
	if (ActorOwner && MainMeshTag != NAME_None) {
		TArray<USkeletalMeshComponent*> SkeletalMeshes;
		ActorOwner->GetComponents<USkeletalMeshComponent>(SkeletalMeshes);
		for (USkeletalMeshComponent* MeshComp : SkeletalMeshes) {
			if (MeshComp && MeshComp->ComponentHasTag(MainMeshTag)) {
				MainCharacterMesh = MeshComp;
				break;
			}
		}
	}

	// Fallback: try to get mesh from ACharacter if ActorOwner is a Character
	if (!MainCharacterMesh) {
		ACharacter* CharacterOwner = Cast<ACharacter>(ActorOwner);
		if (CharacterOwner) {
			MainCharacterMesh = CharacterOwner->GetMesh();
		}
	}
}

void UACFEquipmentComponent::Internal_OnArmorUnequipped(const FGameplayTag& slot)
{
	FModularPart outMesh;
	FEquippedItem outEquip;

	if (GetModularMesh(slot, outMesh) && outMesh.meshComp) {
		outMesh.meshComp->ResetSlotToEmpty();
		OnEquippedArmorChanged.Broadcast(slot);
	}
}

bool UACFEquipmentComponent::CanBeEquipped(const TSubclassOf<UACFItem>& equippable)
{
	FItemDescriptor ItemData;
	UACFItemSystemFunctionLibrary::GetItemData(equippable, ItemData);

	GatherActorOwner();
	if (HaveAtLeastAValidSlot(ItemData.GetPossibleItemSlots())) {
		return true;
	}
	UE_LOG(ACFInventoryLog, Log, TEXT("No VALID item slots! Impossible to equip! - ACFEquipmentComp"));
	return false;
}

void UACFEquipmentComponent::BeginDestroy()
{
	// Internal_DestroyEquipment();
	Super::BeginDestroy();
}

void UACFEquipmentComponent::HandleItemRemoved(const FInventoryItem& item, int32 count /*= 1*/)
{
	if (item.Count <= 0) {
		if (item.bIsEquipped) {
			FEquippedItem equipItem;
			if (GetEquippedItemSlot(item.EquipmentSlot, equipItem)) {
				RemoveItemFromEquipment(equipItem);
			}
		}
	}
	else if (item.bIsEquipped && Equipment.GetEquippedItems().Contains(item.EquipmentSlot)) {

		if (item.ItemClass) {
			// No need to refresh for projectiles
			const UClass* ItemCls = item.ItemClass.Get();
			if (ItemCls && !ItemCls->IsChildOf(UACFProjectile::StaticClass())) {
				RefreshEquipment();
			}
		}
		OnEquipmentChanged.Broadcast(Equipment);
	}
}

void UACFEquipmentComponent::HandleItemAdded(const FInventoryItem& newItem, int32 count /*= 1*/, bool bTryToEquip /*= true*/, FGameplayTag equipSlot)
{
	FGameplayTag outTag;
	FItemDescriptor itemData;
	UACFItemSystemFunctionLibrary::GetItemData(newItem.ItemClass, itemData);
	if (newItem.bIsEquipped && Equipment.GetEquippedItems().Contains(newItem.EquipmentSlot)) {
		OnEquipmentChanged.Broadcast(Equipment);
	}
	if (bTryToEquip) {
		if (equipSlot != FGameplayTag() && itemData.GetPossibleItemSlots().Contains(equipSlot) && IsSlotAvailable(equipSlot)) {
			EquipItemFromInventoryInSlot(newItem, equipSlot);
		}
		else if (TryFindAvailableItemSlot(itemData.GetPossibleItemSlots(), outTag)) {
			EquipItemFromInventory(newItem);
		}
	}
}

void UACFEquipmentComponent::AttachWeaponOnBody(AACFWeaponActor* WeaponToEquip)
{

	if (MainCharacterMesh) {
		const FName socket = WeaponToEquip->GetOnBodySocketName();
		if (socket != NAME_None) {
			WeaponToEquip->AttachToComponent(MainCharacterMesh, FAttachmentTransformRules::SnapToTargetIncludingScale, socket);
			WeaponToEquip->SetActorHiddenInGame(false);
		}
		else {
			WeaponToEquip->SetActorHiddenInGame(true);
		}


	}
}

void UACFEquipmentComponent::AttachWeaponOnHand(AACFWeaponActor* localWeapon)
{
	if (MainCharacterMesh) {
		const FName socket = localWeapon->GetEquippedSocketName();
		if (socket != NAME_None) {
			localWeapon->AttachToComponent(MainCharacterMesh, FAttachmentTransformRules::SnapToTargetIncludingScale, socket);
			localWeapon->SetActorHiddenInGame(false);
		}
		else {
			localWeapon->SetActorHiddenInGame(true);
		}

	}
}

void UACFEquipmentComponent::AddSkeletalMeshComponent(const FEquippedItem& equipItem)
{
	if (!ActorOwner) {
		return;
	}
	FModularPart outMesh;
	UACFArmor* ArmorToAdd = Cast<UACFArmor>(equipItem.Item);

	if (!ArmorToAdd) {
		UE_LOG(ACFInventoryLog, Error, TEXT("Trying to wear an armor without armor class!!! - ACFEquipmentComp"));
		return;
	}
	/* TObjectPtr<USkinnedAsset> armorMesh = ArmorToAdd->GetArmorMesh(ActorOwner);
	if (!ArmorToAdd || !armorMesh) {
		UE_LOG(ACFInventoryLog, Error, TEXT("Trying to wear an armor without armor mesh!!! - ACFEquipmentComp"));
		return;
	}*/

	if (GetModularMesh(equipItem.GetItemSlot(), outMesh) && outMesh.meshComp) {
		outMesh.meshComp->InitArmor(ArmorToAdd);
		outMesh.meshComp->AttachToComponent(MainCharacterMesh, FAttachmentTransformRules(EAttachmentRule::SnapToTarget, true));
		outMesh.meshComp->SetLeaderPoseComponent(MainCharacterMesh);

	}
	else {
		UACFArmorSlotComponent* NewComp = NewObject<UACFArmorSlotComponent>(ActorOwner, ArmorToAdd->GetArmorComponentClass(), equipItem.GetItemSlot().GetTagName());

		NewComp->RegisterComponent();
		NewComp->SetWorldLocation(FVector::ZeroVector);
		NewComp->SetWorldRotation(FRotator::ZeroRotator);
		NewComp->SetSlotTag(equipItem.GetItemSlot());
		NewComp->AttachToComponent(MainCharacterMesh, FAttachmentTransformRules(EAttachmentRule::SnapToTarget, true));
		NewComp->InitArmor(ArmorToAdd);
		NewComp->SetLeaderPoseComponent(MainCharacterMesh);
		NewComp->bUseBoundsFromLeaderPoseComponent = true;

		ModularMeshes.Add(FModularPart(NewComp));
	}
	OnEquippedArmorChanged.Broadcast(equipItem.GetItemSlot());
}

void UACFEquipmentComponent::UseEquippedItemBySlot_Implementation(FGameplayTag ItemSlot)
{
	if (!UACFItemSystemFunctionLibrary::IsValidItemSlotTag(ItemSlot)) {
		UE_LOG(ACFInventoryLog, Log, TEXT("Invalid item Slot Tag!!! - ACFEquipmentComp"));
		return;
	}

	if (ItemSlot == CurrentlyEquippedSlotType) {
		SheathCurrentWeapon();
		return;
	}

	FEquippedItem EquipSlot;

	if (GetEquippedItemSlot(ItemSlot, EquipSlot)) {
		AACFWeaponActor* localWeapon = Cast<AACFWeaponActor>(EquipSlot.ItemActor);
		if (localWeapon) {
			if (localWeapon->GetHandleType() == EHandleType::OffHand) {
				if (GetCurrentMainWeapon() && GetCurrentMainWeapon()->GetHandleType() == EHandleType::OneHanded) {
					SetSecondaryWeapon(localWeapon);
				}
			}
			else {
				if (GetCurrentMainWeapon()) {
					SheathCurrentWeapon();
				}
				SetMainWeapon(localWeapon);
				CurrentlyEquippedSlotType = ItemSlot;
			}
			AttachWeaponOnHand(localWeapon);
			localWeapon->Internal_OnWeaponUnsheathed();

		}
		else if (EquipSlot.Item && EquipSlot.Item->IsA(UACFConsumable::StaticClass())) {
			APawn* PawnTarget = Cast<APawn>(ActorOwner);
			UseEquippedConsumable(EquipSlot, PawnTarget);
		}
		OnEquipmentChanged.Broadcast(Equipment);
	}
}

void UACFEquipmentComponent::UnequipItemBySlot_Implementation(FGameplayTag itemSlot)
{
	if (!UACFItemSystemFunctionLibrary::IsValidItemSlotTag(itemSlot)) {
		UE_LOG(ACFInventoryLog, Log, TEXT("Invalid item Slot Tag!!! - ACFEquipmentComp"));
		return;
	}

	if (itemSlot == CurrentlyEquippedSlotType) {
		SheathCurrentWeapon();
	}

	FEquippedItem EquipSlot;
	if (GetEquippedItemSlot(itemSlot, EquipSlot)) {
		RemoveItemFromEquipment(EquipSlot);
	}
}

void UACFEquipmentComponent::UnequipItemByGuid_Implementation(const FGuid& itemGuid)
{
	FEquippedItem EquipSlot;
	if (GetEquippedItem(itemGuid, EquipSlot)) {
		RemoveItemFromEquipment(EquipSlot);
	}
}

void UACFEquipmentComponent::SheathCurrentWeapon_Implementation()
{
	if (GetCurrentMainWeapon()) {
		AttachWeaponOnBody(GetCurrentMainWeapon());
		GetCurrentMainWeapon()->Internal_OnWeaponSheathed();
		SetMainWeapon(nullptr);

		if (GetCurrentOffhandWeapon()) {
			AttachWeaponOnBody(GetCurrentOffhandWeapon());
			GetCurrentOffhandWeapon()->Internal_OnWeaponSheathed();
			SetSecondaryWeapon(nullptr);
		}
	}

	OnEquipmentChanged.Broadcast(Equipment);
	CurrentlyEquippedSlotType = UACFItemSystemFunctionLibrary::GetItemSlotTagRoot();
}

void UACFEquipmentComponent::EquipItemFromInventory_Implementation(const FInventoryItem& inItem)
{
	EquipItemFromInventoryInSlot(inItem, FGameplayTag());
}

void UACFEquipmentComponent::EquipItemFromInventoryInSlot_Implementation(const FInventoryItem& inItem, FGameplayTag slot)
{
	FInventoryItem item;

	if (!GetInventoryList().GetItem(inItem.GetItemGuid(), item)) {
		return;
	}

	if (!CanBeEquipped(item.ItemClass)) {
		UE_LOG(ACFInventoryLog, Warning, TEXT("Item is not equippable  - ACFEquipmentComp"));
		return;
	}

	//First check if the slot is available
	if (item.bIsEquipped) {

		ensure(item.EquipmentSlot != FGameplayTag());
		FEquippedItem currentItem;
		if (slot == FGameplayTag()) {
			slot = item.EquipmentSlot;
		}
		if (GetEquippedItemSlot(slot, currentItem) && currentItem.ItemGuid == inItem.GetItemGuid()) {
			// already equipped in the same slot
			return;
		}
		else {
			// otherwise let's swap slot
			UnequipItemByGuid(inItem.GetItemGuid());
		}
	}


	UWorld* world = GetWorld();

	if (!world) {
		return;
	}

	// Use existing instance from inventory when available (same instance for equip + inventory)
	TObjectPtr<UACFItem> itemInstance = item.Item;
	if (!itemInstance && item.ItemClass) {
		itemInstance = NewObject<UACFItem>(ActorOwner, item.ItemClass);
	}
	if (!itemInstance) {
		UE_LOG(ACFInventoryLog, Error, TEXT("Item instance is null!!! - ACFEquipmentComp"));
		return;
	}

	UACFEquippableItem* equippable = Cast<UACFEquippableItem>(itemInstance);
	if (equippable && !equippable->CanBeEquipped(this)) {
		return;
	}

	FGameplayTag selectedSlot;
	if (slot == FGameplayTag()) {
		if (!TryFindAvailableItemSlot(itemInstance->GetItemInfo().ItemSlots, selectedSlot) && itemInstance->GetItemInfo().ItemSlots.Num() > 0) {
			selectedSlot = itemInstance->GetItemInfo().ItemSlots[0];
		}
	}
	else if (itemInstance->GetPossibleItemSlots().Contains(slot)) {
		selectedSlot = slot;
	}
	else {
		UE_LOG(ACFInventoryLog, Error, TEXT("Trying to equip an item in to an invalid Slot!!! - ACFEquipmentComp"));
		return;
	}

	UnequipItemBySlot(selectedSlot);

	APawn* PawnOwner = Cast<APawn>(ActorOwner);
	if (equippable && PawnOwner) {
		equippable->Internal_OnEquipped(PawnOwner);
	}
	TSubclassOf<AACFItemActor> itemActorClass = itemInstance->GetItemActorClass();
	AACFItemActor* itemActor = nullptr;
	FTransform spawnTrans = FTransform(ActorOwner->GetActorLocation());
	if (itemActorClass) {
		APawn* InstigatorPawn = PawnOwner ? PawnOwner : nullptr;
		itemActor = world->SpawnActorDeferred<AACFItemActor>(itemActorClass, spawnTrans, ActorOwner, InstigatorPawn, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);

		if (!itemActor) {
			UE_LOG(ACFInventoryLog, Error, TEXT("Impossible to spawn item!!! - ACFEquipmentComp"));
			return;
		}
		itemActor->InitItemActor(PawnOwner, itemInstance);
		itemActor->FinishSpawning(spawnTrans);
	}

	Equipment.AddEntry(FEquippedItem(inItem, selectedSlot, itemInstance, itemActor, item.ItemClass));
	MarkItemOnInventoryAsEquipped(inItem.GetItemGuid(), true, selectedSlot);

	RefreshEquipment();
	OnEquipmentChanged.Broadcast(Equipment);
}

void UACFEquipmentComponent::DropItemByInventoryIndex_Implementation(int32 itemIndex, int32 count)
{
	FInventoryItem outItem;
	if (GetItemByIndex(itemIndex, outItem)) {
		DropItem(outItem, count);
	}
}

void UACFEquipmentComponent::RemoveItemFromEquipment(const FEquippedItem& equippedItem)
{
	const int32 index = Equipment.GetEquippedItems().IndexOfByKey(equippedItem.GetItemSlot());
	MarkItemOnInventoryAsEquipped(equippedItem.ItemGuid, false, FGameplayTag());
	if (equippedItem.Item->IsValidLowLevelFast()) {
		UACFEquippableItem* equippable = Cast<UACFEquippableItem>(equippedItem.Item);

		if (equippable) {
			equippable->Internal_OnUnEquipped();
			if (equippable->IsA(UACFArmor::StaticClass())) {
				Internal_OnArmorUnequipped(equippedItem.GetItemSlot());
			}
		}
		if (equippedItem.ItemActor) {
			equippedItem.ItemActor->Destroy();
		}
	}
	FEquippedItem copy = Equipment.GetEquippedItems()[index];

	Equipment.RemoveEntry(copy);
	RefreshEquipment();
	OnEquipmentChanged.Broadcast(Equipment);
}

void UACFEquipmentComponent::MarkItemOnInventoryAsEquipped(const FGuid& item, bool bIsEquipped, const FGameplayTag& itemSlot)
{
	GetInventoryList().MarkItemAsEquipped(item, bIsEquipped, itemSlot);
}

FVector UACFEquipmentComponent::GetMainWeaponSocketLocation() const
{
	const AACFRangedWeaponActor* rangedWeap = Cast<AACFRangedWeaponActor>(GetCurrentMainWeapon());
	if (rangedWeap) {
		return rangedWeap->GetShootingSocket();
	}

	return FVector();
}

bool UACFEquipmentComponent::GetEquippedItemSlot(const FGameplayTag& itemSlot, FEquippedItem& outSlot) const
{
	if (Equipment.GetEquippedItems().Contains(itemSlot)) {
		const int32 index = Equipment.GetEquippedItems().IndexOfByKey(itemSlot);
		outSlot = Equipment.GetEquippedItems()[index];
		return true;
	}
	return false;
}

bool UACFEquipmentComponent::GetEquippedItem(const FGuid& itemGuid, FEquippedItem& outSlot) const
{
	if (Equipment.GetEquippedItems().Contains(itemGuid)) {
		const int32 index = Equipment.GetEquippedItems().IndexOfByKey(itemGuid);
		outSlot = Equipment.GetEquippedItems()[index];
		return true;
	}
	return false;
}

bool UACFEquipmentComponent::GetModularMesh(FGameplayTag itemSlot, FModularPart& outMesh) const
{
	const FModularPart* slot = ModularMeshes.FindByKey(itemSlot);
	if (slot) {
		outMesh = *slot;
		return true;
	}
	return false;
}

bool UACFEquipmentComponent::HasAnyItemInEquipmentSlot(FGameplayTag itemSlot) const
{
	return Equipment.GetEquippedItems().Contains(itemSlot);
}

void UACFEquipmentComponent::UseConsumableOnActorBySlot_Implementation(FGameplayTag itemSlot, APawn* target)
{
	if (!UACFItemSystemFunctionLibrary::IsValidItemSlotTag(itemSlot)) {
		UE_LOG(ACFInventoryLog, Log, TEXT("Invalid item Slot Tag!!! - ACFEquipmentComp"));
		return;
	}

	FEquippedItem EquipSlot;
	if (GetEquippedItemSlot(itemSlot, EquipSlot)) {
		UseEquippedConsumable(EquipSlot, target);
	}
}

void UACFEquipmentComponent::SetDamageActivation(bool isActive, const TArray<FName>& traceChannels, bool isSecondaryWeapon /*= false*/)
{
	TObjectPtr<AACFMeleeWeaponActor> weapon;
	if (isSecondaryWeapon && GetCurrentOffhandWeapon()) {
		weapon = Cast<AACFMeleeWeaponActor>(GetCurrentOffhandWeapon());
	}
	else if (!isSecondaryWeapon && GetCurrentMainWeapon()) {
		weapon = Cast<AACFMeleeWeaponActor>(GetCurrentMainWeapon());
	}
	else {
		return;
	}

	if (weapon) {
		if (isActive) {
			weapon->StartWeaponSwing(traceChannels);
		}
		else {
			weapon->StopWeaponSwing();
		}
	}
}

void UACFEquipmentComponent::SetMainMesh(USkeletalMeshComponent* newMesh, bool bRefreshEquipment)
{
	MainCharacterMesh = newMesh;
	if (bRefreshEquipment) {
		RefreshEquipment();
	}
}

bool UACFEquipmentComponent::SwapItemFromInventory(const FInventoryItem& ItemToEquip, UACFInventoryComponent* SourceInventory)
{
	if (!SourceInventory) {
		return false;
	}
	FItemDescriptor itemDesc;
	if (UACFItemSystemFunctionLibrary::GetItemData(ItemToEquip.ItemClass, itemDesc)) {
		//Let's remove the currently equipped item in that slot first
		const FGameplayTag currentSlot = itemDesc.ItemSlots[0];
		FEquippedItem toBeRemoved;
		if (GetEquippedItemSlot(currentSlot, toBeRemoved)) {
			FInventoryItem toBeRemovedItem;
			if (GetItemByGuid(toBeRemoved.ItemGuid, toBeRemovedItem)) {
				RemoveItem(toBeRemovedItem);
				toBeRemovedItem.bIsEquipped = false;
				SourceInventory->AddInventoryItem(toBeRemovedItem);

			}
			else {
				UE_LOG(ACFInventoryLog, Log, TEXT("Swapping item with nothing to remove! -  UACFEquipmentComponent::SwapItemFromInventory"));
			}

		}
		//Now let's equip the new item
		if (NumberOfItemCanTake(ItemToEquip.ItemClass) >= 1) {
			SourceInventory->RemoveItem(ItemToEquip);
			AddInventoryItem(ItemToEquip);
			EquipItemFromInventory(ItemToEquip);
			return true;
		}
	}
	return false;
}

bool UACFEquipmentComponent::CanSwitchToRanged()
{
	for (const auto& weap : Equipment.GetEquippedItems()) {
		if (weap.Item->IsA(UACFRangedWeapon::StaticClass())) {
			return true;
		}
	}
	return false;
}

bool UACFEquipmentComponent::CanSwitchToMelee()
{
	for (const auto& weap : Equipment.GetEquippedItems()) {
		if (weap.Item->IsA(UACFMeleeWeapon::StaticClass())) {
			return true;
		}
	}
	return false;
}

bool UACFEquipmentComponent::HasOnBodyAnyWeaponOfType(TSubclassOf<UACFWeapon> weaponClass) const
{
	for (const auto& weapon : Equipment.GetEquippedItems()) {
		if (weapon.Item->IsA(weaponClass)) {
			return true;
		}
	}
	return false;
}



void UACFEquipmentComponent::SpawnWorldItem(const TArray<FBaseItem>& items, float currencyAmount /*= 0.f*/)
{
	if (!ActorOwner) {
		return;
	}
	if (items.Num() <= 0 && currencyAmount <= 0.f) {
		return;
	}

	FVector DropLocation = ActorOwner->GetActorLocation();
	if (const ACharacter* Character = Cast<ACharacter>(ActorOwner)) {
		DropLocation.Z -= Character->GetSimpleCollisionHalfHeight();
	}

	if (currencyAmount > 0.f) {
		UACFItemSystemFunctionLibrary::SpawnWorldItemWithItemsAndCurrencyNearLocation(this, items, currencyAmount, DropLocation);
	}
	else {
		UACFItemSystemFunctionLibrary::SpawnWorldItemNearLocation(this, items, DropLocation);
	}
}

void UACFEquipmentComponent::UseEquippedConsumable(FEquippedItem& EquipSlot, APawn* target)
{
	if (EquipSlot.Item->IsA(UACFConsumable::StaticClass())) {
		UACFConsumable* consumable = Cast<UACFConsumable>(EquipSlot.Item);
		FInventoryItem invItem;
		if (GetItemByGuid(EquipSlot.ItemGuid, invItem)) {
			Internal_UseItem(consumable, target, invItem);
		}
	}
}

void UACFEquipmentComponent::SetEquippedItemsVisible(bool bVisible)
{
	for (const auto& Item : Equipment.GetEquippedItems())
	{
		if (Item.ItemActor == nullptr) continue;
		Item.ItemActor->SetActorHiddenInGame(!bVisible);
		Item.ItemActor->SetActorEnableCollision(bVisible);
	}
}

void UACFEquipmentComponent::DestroyEquipment()
{
	Internal_DestroyEquipment();
}

void UACFEquipmentComponent::SetStartingItems(TArray<FStartingItem> val)
{
	StartingItems = val;
	InitializeStartingItems();
}

void UACFEquipmentComponent::DestroyEquippedItems_Implementation(bool bSpawnDrops)
{
	Internal_DestroyEquipment();

	// Safety-net path (e.g. AACFCharacter::EndPlay on streaming-out / map unload):
	// caller explicitly opted out of drops, so we must NOT spawn anything in the world
	// and must NOT consume the accumulated death drops / currency. Just bail.
	if (!bSpawnDrops) {
		return;
	}

	TArray<FBaseItem> toDrop;

	if (bDropItemsOnDeath && GetInventoryList().Num() > 0) {
		for (int32 Index = GetInventoryList().Num() - 1; Index >= 0; --Index) {
			FInventoryItem currentItem;

			if (!GetInventoryList().GetItemByIndex(Index, currentItem)) {
				continue; // Skip if the item is not valid.
			}

			FItemDescriptor itemInfo;
			if (!UACFItemSystemFunctionLibrary::GetItemData(currentItem.ItemClass, itemInfo)) {
				continue;
			}
			if (GetInventoryList().IsValidIndex(Index) && itemInfo.bDroppable) {
				FBaseItem newItem(currentItem);
				newItem.Count = 0;

				for (uint8 i = 0; i < currentItem.Count; i++) {
					if (currentItem.DropChancePercentage > FMath::RandRange(0.f, 100.f)) {
						newItem.Count++;
					}
				}

				if (newItem.Count > 0) {
					if (bCollapseDropInASingleWorldItem) {
						toDrop.Add(newItem);
					}
					else {
						TArray<FBaseItem> newDrop;
						newDrop.Add(newItem);
						SpawnWorldItem(newDrop);
					}
					RemoveItem(currentItem, currentItem.Count);
				}
			}
		}
	}

	// Fold in any drops deferred by OnEntityOwnerDeath (projectiles stuck on the corpse, etc.)
	if (PendingDeathDropsAccumulator.Num() > 0) {
		if (bCollapseDropInASingleWorldItem) {
			toDrop.Append(PendingDeathDropsAccumulator);
		}
		else {
			SpawnWorldItem(PendingDeathDropsAccumulator);
		}
		PendingDeathDropsAccumulator.Reset();
	}

	// Pull currency from every UACFCurrencyComponent on the owner (including this one,
	// since UACFEquipmentComponent inherits from UACFCurrencyComponent). This guarantees
	// the wallet ends up in the same collapsed world item regardless of the order in
	// which OnHealthReachesZero listeners fire.
	float collapsedCurrency = 0.f;
	if (bCollapseDropInASingleWorldItem && GetOwner()) {
		TArray<UACFCurrencyComponent*> currencyComps;
		GetOwner()->GetComponents<UACFCurrencyComponent>(currencyComps);
		for (UACFCurrencyComponent* curComp : currencyComps) {
			if (IsValid(curComp)) {
				collapsedCurrency += curComp->ConsumePendingDeathCurrencyDrop();
			}
		}
	}

	if (bCollapseDropInASingleWorldItem && (toDrop.Num() > 0 || collapsedCurrency > 0.f)) {
		SpawnWorldItem(toDrop, collapsedCurrency);
	}
}

void UACFEquipmentComponent::Internal_DestroyEquipment()
{
	for (auto& equip : Equipment.GetEquippedItems()) {
		UACFEquippableItem* equippable = Cast<UACFEquippableItem>(equip.Item);
		if (equippable) {
			equippable->Internal_OnUnEquipped();
		}
		if (IsValid(equip.ItemActor)) {
			equip.ItemActor->SetLifeSpan(.1f);
		}
	}
}

bool UACFEquipmentComponent::UnsheatheFirstAvailableWeapon()
{
    // Already has a weapon in hand
    if (GetCurrentMainWeapon())
    {
        return true;
    }

    // First pass: find and equip main hand weapon
    for (const FEquippedItem& EquipItem : Equipment.GetEquippedItems())
    {
        AACFWeaponActor* WeaponActor = Cast<AACFWeaponActor>(EquipItem.ItemActor);
        if (!WeaponActor)
        {
            continue;
        }
        
        // Skip offhand-only weapons on first pass
        if (WeaponActor->GetHandleType() == EHandleType::OffHand)
        {
            continue;
        }

        UseEquippedItemBySlot(EquipItem.ItemSlot);
        break;
    }

    // Second pass: if main weapon is one-handed, try to equip offhand
    if (GetCurrentMainWeapon() && 
        GetCurrentMainWeapon()->GetHandleType() == EHandleType::OneHanded &&
        !GetCurrentOffhandWeapon())
    {
        for (const FEquippedItem& EquipItem : Equipment.GetEquippedItems())
        {
            AACFWeaponActor* WeaponActor = Cast<AACFWeaponActor>(EquipItem.ItemActor);
            if (!WeaponActor)
            {
                continue;
            }

            if (WeaponActor->GetHandleType() == EHandleType::OffHand)
            {
                UseEquippedItemBySlot(EquipItem.ItemSlot);
                break;
            }
        }
    }

    return GetCurrentMainWeapon() != nullptr;
}
