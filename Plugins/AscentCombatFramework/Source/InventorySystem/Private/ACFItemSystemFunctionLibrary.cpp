// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFItemSystemFunctionLibrary.h"
#include "ACFInventorySettings.h"
#include "ACFRPGFunctionLibrary.h"
#include "ACFRPGTypes.h"
#include "AIController.h"
#include "Components/ACFCurrencyComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "GameplayTagsManager.h"
#include "Items/ACFConsumable.h"
#include "Items/ACFEquippableItem.h"
#include "Items/ACFItem.h"
#include "Items/ACFRangedWeapon.h"
#include "Items/ACFWorldItem.h"
#include "Kismet/GameplayStatics.h"
#include "NavigationSystem.h"
#include "UObject/SoftObjectPtr.h"
#include <GameFramework/Actor.h>
#include <GameFramework/Controller.h>
#include <Logging.h>
#include "Components/ACFInventoryComponent.h"

AACFWorldItem* UACFItemSystemFunctionLibrary::SpawnWorldItemNearLocation(UObject* WorldContextObject, const TArray<FBaseItem>& ContainedItem,
	const FVector& location, float acceptanceRadius /*= 100.f*/)
{

	if (ContainedItem.Num() <= 0) {
		return nullptr;
	}

	AACFWorldItem* worldItem = SpawnWorldItem(WorldContextObject, location, acceptanceRadius);

	if (worldItem) {
		for (const auto& item : ContainedItem) {
			worldItem->AddItem(item);
		}
		UGameplayStatics::FinishSpawningActor(worldItem, FTransform(location));

		return worldItem;
	}
	UE_LOG(ACFInventoryLog, Error, TEXT("Impossible to Spawn Item!! - UACFFunctionLibrary::SpawnWorldItemNearLocation"));

	return nullptr;
}

AACFWorldItem* UACFItemSystemFunctionLibrary::SpawnCurrencyItemNearLocation(UObject* WorldContextObject, float currencyAmount, const FVector& location, float acceptanceRadius /*= 100.f*/)
{
	AACFWorldItem* worldItem = SpawnWorldItem(WorldContextObject, location, acceptanceRadius);

	if (worldItem) {
		worldItem->AddCurrency(currencyAmount);
		UGameplayStatics::FinishSpawningActor(worldItem, FTransform(location));
		return worldItem;
	}
	UE_LOG(ACFInventoryLog, Error, TEXT("Impossible to Spawn Item!! MISSING NAVMESH - UACFFunctionLibrary::SpawnWorldItemNearLocation"));

	return nullptr;
}

AACFWorldItem* UACFItemSystemFunctionLibrary::SpawnWorldItemWithItemsAndCurrencyNearLocation(UObject* WorldContextObject,
	const TArray<FBaseItem>& ContainedItems, float CurrencyAmount, const FVector& Location, float AcceptanceRadius /*= 100.f*/)
{
	if (ContainedItems.Num() <= 0 && CurrencyAmount <= 0.f) {
		return nullptr;
	}

	AACFWorldItem* worldItem = SpawnWorldItem(WorldContextObject, Location, AcceptanceRadius);

	if (worldItem) {
		for (const auto& item : ContainedItems) {
			worldItem->AddItem(item);
		}
		if (CurrencyAmount > 0.f) {
			worldItem->AddCurrency(CurrencyAmount);
		}
		UGameplayStatics::FinishSpawningActor(worldItem, FTransform(Location));
		return worldItem;
	}
	UE_LOG(ACFInventoryLog, Error, TEXT("Impossible to Spawn Item!! - UACFFunctionLibrary::SpawnWorldItemWithItemsAndCurrencyNearLocation"));

	return nullptr;
}

AACFWorldItem* UACFItemSystemFunctionLibrary::SpawnWorldItem(UObject* WorldContextObject, const FVector& location, float acceptanceRadius /*= 100.f*/)
{
	FVector outLoc;
	if (UNavigationSystemV1::K2_ProjectPointToNavigation(WorldContextObject, location, outLoc, nullptr, nullptr)) {
	}
	else if (!UNavigationSystemV1::K2_GetRandomReachablePointInRadius(WorldContextObject, location, outLoc, acceptanceRadius)) {
		outLoc = location;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

	TSubclassOf<AACFWorldItem> WorldItemClass = UACFItemSystemFunctionLibrary::GetDefaultWorldItemClass();
	ensure(WorldItemClass);

	APlayerController* playerController = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
	if (!playerController) {
		return nullptr;
	}
	UWorld* world = playerController->GetWorld();

	if (!world) {
		return nullptr;
	}

	if (world && WorldItemClass) {
		// for some reasons the Z gets fucked up
		outLoc.Z = location.Z;
		const FTransform startTrans = FTransform(FRotator(0), outLoc);
		return world->SpawnActorDeferred<AACFWorldItem>(WorldItemClass, startTrans, playerController, playerController->GetPawn(), ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn);

	}
	else {
		UE_LOG(ACFInventoryLog, Error, TEXT("Impossible to Spawn Item!! MISSING NAVMESH - UACFFunctionLibrary::SpawnWorldItemNearLocation"));
	}
	return nullptr;
}

bool UACFItemSystemFunctionLibrary::GetItemData(const TSubclassOf<class UACFItem>& item, FItemDescriptor& outData)
{
	/*	item.LoadSynchronous();*/
	if (item) {
		const UACFItem* itemInstance = Cast<UACFItem>(item.Get()->GetDefaultObject());
		if (itemInstance) {
			outData = itemInstance->GetItemInfo();
			return true;
		}
	}
	return false;
}

bool UACFItemSystemFunctionLibrary::GetEquippableAttributeSetModifier(const TSubclassOf<class UACFItem>& itemClass, FAttributesSetModifier& outModifier)
{
	/*	itemClass.LoadSynchronous();*/
	if (itemClass) {
		const UACFEquippableItem* itemInstance = Cast<UACFEquippableItem>(itemClass.GetDefaultObject());
		if (itemInstance) {
			outModifier = itemInstance->GetAttributeSetModifier();
			return true;
		}
	}
	return false;
}

bool UACFItemSystemFunctionLibrary::GetEquippableGameplayEffects(const TSubclassOf<class UACFItem>& itemClass, TArray<FGEModifier>& outModifiers)
{

	if (itemClass) {
		const UACFEquippableItem* itemInstance = Cast<UACFEquippableItem>(itemClass.GetDefaultObject());
		if (itemInstance) {
			TArray<FGameplayEffectConfig> Effects;

			const TSubclassOf<UGameplayEffect> ge = itemInstance->GetGEAttributeModifier();
			Effects.Add(FGameplayEffectConfig(ge, itemInstance->GetLevel()));
			return UACFRPGFunctionLibrary::TryGetModifiersFromGameplayEffects(Effects, outModifiers);
		}
	}
	return false;
}

bool UACFItemSystemFunctionLibrary::GetEquippableGEType(const TSubclassOf<class UACFItem>& itemClass, EGEType& outType)
{
	if (itemClass) {
		const UACFEquippableItem* itemInstance = Cast<UACFEquippableItem>(itemClass.GetDefaultObject());
		if (itemInstance) {
			outType = itemInstance->GetAttributeSetModifier().GEModifierType;
			return true;
		}
	}
	return false;
}

bool UACFItemSystemFunctionLibrary::GetConsumableGameplayEffects(const TSubclassOf<class UACFItem>& itemClass, TArray<FGEModifier>& outModifiers)
{

	if (itemClass) {
		const UACFConsumable* itemInstance = Cast<UACFConsumable>(itemClass.GetDefaultObject());
		if (itemInstance) {
			TArray<FGameplayEffectConfig> Effects = itemInstance->GetGameplayEffects();
			return UACFRPGFunctionLibrary::TryGetModifiersFromGameplayEffects(Effects, outModifiers);
		}
	}
	return false;
}

bool UACFItemSystemFunctionLibrary::GetConsumableTimedAttributeSetModifier(const TSubclassOf<class UACFItem>& itemClass, TArray<FTimedAttributeSetModifier>& outModifiers)
{
	/*	itemClass.LoadSynchronous();*/
	if (itemClass) {
		const UACFConsumable* itemInstance = Cast<UACFConsumable>(itemClass.GetDefaultObject());
		if (itemInstance) {
			outModifiers = itemInstance->GetTimedModifiers();
			return true;
		}
	}
	return false;
}

bool UACFItemSystemFunctionLibrary::GetConsumableStatModifier(const TSubclassOf<class UACFItem>& itemClass, TArray<FStatisticValue>& outModifiers)
{
	/*itemClass.LoadSynchronous();*/
	if (itemClass) {
		const UACFConsumable* itemInstance = Cast<UACFConsumable>(itemClass.GetDefaultObject());
		if (itemInstance) {
			outModifiers = itemInstance->GetStatsModifiers();
			return true;
		}
	}
	return false;
}

FBaseItem UACFItemSystemFunctionLibrary::MakeBaseItemFromInventory(const FInventoryItem& inItem)
{
	return FBaseItem(inItem.ItemClass, inItem.GetItemGuid(), inItem.Count);
}

FInventoryItem UACFItemSystemFunctionLibrary::MakeInventoryItemFromBase(const FBaseItem& inItem)
{
	return FInventoryItem(inItem);
}

FInventoryItem UACFItemSystemFunctionLibrary::MakeInventoryItemFromBaseWithNewGUID(const FBaseItem& inItem)
{	
	FInventoryItem Item = FInventoryItem(inItem);
	Item.ForceGuid(FGuid::NewGuid());
	return Item;
}

FGameplayTag UACFItemSystemFunctionLibrary::GetItemTypeTagRoot()
{
	return UGameplayTagsManager::Get().RequestGameplayTag(FName("Item"));
}

FGameplayTag UACFItemSystemFunctionLibrary::GetItemSlotTagRoot()
{


	return UGameplayTagsManager::Get().RequestGameplayTag(FName("Itemslot"));
}

TSubclassOf<AACFWorldItem> UACFItemSystemFunctionLibrary::GetDefaultWorldItemClass()
{
	UACFInventorySettings* settings = GetMutableDefault<UACFInventorySettings>();

	if (settings) {
		return settings->WorldItemClass;
	}
	UE_LOG(ACFInventoryLog, Warning, TEXT("Missing Default Item Class! - UACFFunctionLibrary "));

	return nullptr;
}

TArray<TEnumAsByte<ECollisionChannel>> UACFItemSystemFunctionLibrary::GetDefaultHitTraceChannels()
{
	UACFInventorySettings* settings = GetMutableDefault<UACFInventorySettings>();

	if (settings) {
		return settings->DefaultDamageTraceChannel;
	}
	UE_LOG(ACFInventoryLog, Warning, TEXT("Missing DefaultDamageTraceChannel! - UACFFunctionLibrary "));

	return {};
}

FText UACFItemSystemFunctionLibrary::GetDefaultCurrencyName()
{
	UACFInventorySettings* settings = GetMutableDefault<UACFInventorySettings>();

	if (settings) {
		return settings->DefaultCurrencyName;
	}
	UE_LOG(ACFInventoryLog, Warning, TEXT("Missing Default Currency Name! - UACFFunctionLibrary "));

	return FText::FromString(TEXT(""));
}

void UACFItemSystemFunctionLibrary::FilterByItemType(const TArray<FInventoryItem>& inItems, EItemType inType, TArray<FInventoryItem>& outItems)
{
	outItems.Empty();

	for (const FInventoryItem& item : inItems) {
		FItemDescriptor itemInfo;
		if (!UACFItemSystemFunctionLibrary::GetItemData(item.ItemClass, itemInfo)) {
			return;
		}
		if (itemInfo.ItemType == inType) {
			outItems.Add(item);
		}
	}
}

void UACFItemSystemFunctionLibrary::FilterByItemSlot(const TArray<FInventoryItem>& inItems, FGameplayTag inSlot, TArray<FInventoryItem>& outItems)
{
	outItems.Empty();

	for (const FInventoryItem& item : inItems) {
		FItemDescriptor itemInfo;
		if (!UACFItemSystemFunctionLibrary::GetItemData(item.ItemClass, itemInfo)) {
			return;
		}
		if (itemInfo.ItemSlots.Contains(inSlot)) {
			outItems.Add(item);
		}
	}
}

void UACFItemSystemFunctionLibrary::FilterByItemSlots(const TArray<FInventoryItem>& inItems,
    TArray<FGameplayTag> inSlots, TArray<FInventoryItem>& outItems)
{
    outItems.Empty();

    for (const FInventoryItem& item : inItems) {
        FItemDescriptor itemInfo;
        if (!UACFItemSystemFunctionLibrary::GetItemData(item.ItemClass, itemInfo)) {
            return;
        }
        for (const FGameplayTag& slot : inSlots)
        {
            if (itemInfo.ItemSlots.Contains(slot)) {
                outItems.AddUnique(item);
            }
        }
    }
}

UACFItemFragment* UACFItemSystemFunctionLibrary::FindFragmentByClass(const UACFItem* inItem, TSubclassOf<UACFItemFragment> FragmentClass)
{
	if (!inItem) {
		return nullptr;
	}


	for (UACFItemFragment* Fragment : inItem->Fragments) {
		if (Fragment && Fragment->IsA(FragmentClass)) {
			return Fragment;
		}
	}
	UE_LOG(ACFInventoryLog, Warning, TEXT("Missing Fragment! - UACFFunctionLibrary "));

	return nullptr;
}

UACFItemFragment* UACFItemSystemFunctionLibrary::FindFragmentInItemClassByClass(
	const TSubclassOf<UACFItem> InItemClass, 
	TSubclassOf<UACFItemFragment> FragmentClass,
	bool& OutFoundFragment)
{
	OutFoundFragment = false;

	if (InItemClass)
	{
		const UACFItem* ItemInstance = Cast<UACFItem>(InItemClass.GetDefaultObject());
		if (ItemInstance)
		{
			UACFItemFragment* Fragment = FindFragmentByClass(ItemInstance, FragmentClass);
			if (Fragment)
			{
				OutFoundFragment = true;
				return Fragment;
			}
		}
	}

	UE_LOG(ACFInventoryLog, Warning, TEXT("Missing Fragment! - UACFItemSystemFunctionLibrary"));
	return nullptr;
}
bool UACFItemSystemFunctionLibrary::IsValidItemTypeTag(FGameplayTag TagToCheck)
{
	const FGameplayTag root = GetItemTypeTagRoot();
	return UGameplayTagsManager::Get().RequestGameplayTagChildren(root).HasTag(TagToCheck);
}

bool UACFItemSystemFunctionLibrary::IsValidItemSlotTag(FGameplayTag TagToCheck)
{
	const FGameplayTag root = GetItemSlotTagRoot();
	return UGameplayTagsManager::Get().RequestGameplayTagChildren(root).HasTag(TagToCheck);
}

FTransform UACFItemSystemFunctionLibrary::GetShootTransform(APawn* SourcePawn, EShootTargetType targetType, FVector& outSourceLoc)
{

	check(SourcePawn);

	UACFEquipmentComponent* equipComp = SourcePawn->FindComponentByClass<UACFEquipmentComponent>();

	check(equipComp);
	const FVector ActorLoc = SourcePawn->GetActorLocation();
	FQuat AimQuat = SourcePawn->GetActorQuat();
	AController* Controller = SourcePawn->GetController();
	// FVector SourceLoc;

	TArray<AActor*> actorsToIgnore;
	actorsToIgnore.Add(SourcePawn);

	float FocalDistance; // = GetCameraShootOffset();
	FVector FocalLoc;

	FVector CamLoc;
	FRotator CamRot;
	bool bFoundFocus = false;

	if ((Controller) && ((targetType == EShootTargetType::CameraTowardsFocus) || (targetType == EShootTargetType::PawnTowardsFocus) || (targetType == EShootTargetType::WeaponTowardsFocus))) {

		// Get camera position for later
		bFoundFocus = true;

		APlayerController* PC = Cast<APlayerController>(Controller);
		if (PC) {
			PC->GetPlayerViewPoint(/*out*/ CamLoc, /*out*/ CamRot);
		}
		else {

			Controller->GetPlayerViewPoint(CamLoc, CamRot);
			//             outSourceLoc = equipComp->GetMainWeaponSocketLocation();
			//             CamLoc = outSourceLoc;
			//             CamRot = Controller->GetControlRotation();
		}
		const FVector start = CamLoc;
		const FVector AimDir = CamRot.Vector().GetSafeNormal();

		const FVector end = CamLoc + (AimDir * 3000);

		FHitResult outResult;
		if (UKismetSystemLibrary::LineTraceSingle(
			Controller, start, end, ETraceTypeQuery::TraceTypeQuery1, false, actorsToIgnore, EDrawDebugTrace::None, outResult, true)) {
			FocalDistance = (outResult.ImpactPoint - SourcePawn->GetActorLocation()).Size() - 2.f;
		}
		else {
			FocalDistance = 1024.f; // Arbitrary if we don't have an hit
		}

		const float cameraDistance = (CamLoc - ActorLoc).Size();

		// Determine initial focal point to
		FocalLoc = CamLoc + (AimDir * FocalDistance);

		if (targetType == EShootTargetType::CameraTowardsFocus) {
			outSourceLoc = CamLoc + (AimDir * cameraDistance); // 150 is a randomic
			// If we're camera -> focus then we're done
			return FTransform(CamRot, FocalLoc);
		}
		// Move the start and focal point up in front of pawn
		if (targetType == EShootTargetType::WeaponTowardsFocus) {
			const FVector WeaponLoc = equipComp->GetMainWeaponSocketLocation();
			CamLoc = FocalLoc + (((WeaponLoc - FocalLoc) | AimDir) * AimDir);
			FocalLoc = CamLoc + (AimDir * FocalDistance);
		}
	}

	if ((targetType == EShootTargetType::WeaponForward) || (targetType == EShootTargetType::WeaponTowardsFocus)) {
		outSourceLoc = equipComp->GetMainWeaponSocketLocation();
	}
	else {
		// Either we want the pawn's location, or we failed to find a camera
		outSourceLoc = ActorLoc;
	}

	if (bFoundFocus && ((targetType == EShootTargetType::PawnTowardsFocus) || (targetType == EShootTargetType::WeaponTowardsFocus))) {
		// Return a rotator pointing at the focal point from the source
		return FTransform((FocalLoc - outSourceLoc).Rotation(), outSourceLoc);
	}

	// If we got here, either we don't have a camera or we don't want to use it, either way go forward
	return FTransform(AimQuat, outSourceLoc);
}

float UACFItemSystemFunctionLibrary::GetPawnCurrency(const APawn* pawn)
{
	if (!pawn) {
		return -1.f;
	}

	const UACFCurrencyComponent* currencyComp = GetPawnCurrencyComponent(pawn);
	if (currencyComp) {
		return currencyComp->GetCurrentCurrencyAmount();
	}
	return -1.f;
}

UACFEquipmentComponent* UACFItemSystemFunctionLibrary::GetPawnEquipment(const APawn* pawn)
{
	if (!pawn) {
		return nullptr;
	}

	return pawn->FindComponentByClass<UACFEquipmentComponent>();
}

UACFCurrencyComponent* UACFItemSystemFunctionLibrary::GetPawnCurrencyComponent(const APawn* pawn)
{
	if (!pawn) {
		return nullptr;
	}

	UACFCurrencyComponent* currencyComp = pawn->FindComponentByClass<UACFCurrencyComponent>();
	if (currencyComp) {
		return currencyComp;
	}
	AController* pawnContr = pawn->GetController();
	if (pawnContr) {
		UACFCurrencyComponent* currency = pawnContr->FindComponentByClass<UACFCurrencyComponent>();
		if (currency) {
			return currency;
		}
	}
	UE_LOG(ACFInventoryLog, Error, TEXT("Add Currency Component to your Player Controller! - UACFItemSystemFunctionLibrary::GetPawnEquipment"));

	return nullptr;
}

bool UACFItemSystemFunctionLibrary::CanUseConsumableItem(const APawn* pawn, const TSubclassOf<class UACFConsumable>& itemClass)
{
	UACFConsumable* itemInstance = Cast<UACFConsumable>(itemClass.Get()->GetDefaultObject());
	if (itemInstance) {
		return itemInstance->CanBeUsed(pawn);
	}
	return false;
}

FGameplayTag UACFItemSystemFunctionLibrary::GetDesiredUseAction(const TSubclassOf<class UACFConsumable>& itemClass)
{
	UACFConsumable* itemInstance = Cast<UACFConsumable>(itemClass.Get()->GetDefaultObject());
	if (itemInstance) {
		return itemInstance->GetDesiredUseAction();
	}
	return FGameplayTag();
}

AACFWorldItem* UACFItemSystemFunctionLibrary::SpawnWorldItemWithInstance(UObject* WorldContextObject,
	const FInventoryItem& ItemToSpawn, const FVector& location, float acceptanceRadius /*= 100.f*/)
{
	if (!ItemToSpawn.ItemClass) {
		return nullptr;
	}

	AACFWorldItem* worldItem = SpawnWorldItem(WorldContextObject, location, acceptanceRadius);
	if (worldItem) {
		worldItem->AddInventoryItem(ItemToSpawn);
		UGameplayStatics::FinishSpawningActor(worldItem, FTransform(location));
		return worldItem;
	}
	UE_LOG(ACFInventoryLog, Error, TEXT("Impossible to Spawn Item!! - UACFFunctionLibrary::SpawnWorldItemWithInstance"));
	return nullptr;
}
