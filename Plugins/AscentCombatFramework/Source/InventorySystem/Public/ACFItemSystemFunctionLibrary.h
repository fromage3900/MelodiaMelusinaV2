// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "ACFItemTypes.h"
#include "ARSTypes.h"
#include "CoreMinimal.h"
#include "Items/ACFItem.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "ACFItemSystemFunctionLibrary.generated.h"

class UACFCurrencyComponent;
class UACFEquipmentComponent;
class UACFItemsManagerComponent;

/**
 * Function library providing utility functions for the ACF Item System.
 * Contains helper functions for spawning items, filtering inventory, and retrieving item data.
 */
UCLASS()
class INVENTORYSYSTEM_API UACFItemSystemFunctionLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
		* Spawns a world item actor near the specified location containing the provided items.
		*
		* @param WorldContextObject - Context object for the world
		* @param ContainedItem - Array of items to be contained in the spawned world item
		* @param location - Target location where the item should spawn
		* @param acceptanceRadius - Maximum distance from target location where item can spawn (default: 100 units)
		* @return The spawned world item actor, or nullptr if spawn failed
		*/
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static AACFWorldItem* SpawnWorldItemNearLocation(UObject* WorldContextObject,
	                                                 const TArray<FBaseItem>& ContainedItem, const FVector& location,
	                                                 float acceptanceRadius = 100.f);

	/**
	 * Spawns a currency item near the specified location.
	 *
	 * @param WorldContextObject - Context object for the world
	 * @param currencyAmount - Amount of currency to spawn
	 * @param location - Target location where the currency should spawn
	 * @param acceptanceRadius - Maximum distance from target location where currency can spawn (default: 100 units)
	 * @return The spawned currency world item actor, or nullptr if spawn failed
	 */
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static AACFWorldItem* SpawnCurrencyItemNearLocation(UObject* WorldContextObject, float currencyAmount,
	                                                    const FVector& location, float acceptanceRadius = 100.f);

	/**
	 * Spawns a single world item near the specified location containing BOTH items and currency.
	 * Useful to collapse all death drops (inventory + dropped projectiles + wallet) into a single pickup.
	 *
	 * @param WorldContextObject - Context object for the world
	 * @param ContainedItems - Items to be added to the spawned world item (can be empty)
	 * @param CurrencyAmount - Currency to be added to the spawned world item (ignored if <= 0)
	 * @param Location - Target location where the item should spawn
	 * @param AcceptanceRadius - Maximum distance from target location where item can spawn (default: 100 units)
	 * @return The spawned world item actor, or nullptr if there is nothing to drop / spawn failed
	 */
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static AACFWorldItem* SpawnWorldItemWithItemsAndCurrencyNearLocation(UObject* WorldContextObject,
	                                                                    const TArray<FBaseItem>& ContainedItems,
	                                                                    float CurrencyAmount,
	                                                                    const FVector& Location,
	                                                                    float AcceptanceRadius = 100.f);

	/* FILTERS */

	/**
	 * Filters an array of inventory items by their item type.
	 *
	 * @param inItems - Input array of inventory items to filter
	 * @param inType - Item type to filter by
	 * @param outItems - Output array containing only items matching the specified type
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static void FilterByItemType(const TArray<FInventoryItem>& inItems, EItemType inType,
	                             TArray<FInventoryItem>& outItems);

	/**
	 * Filters an array of inventory items by their equipment slot.
	 *
	 * @param inItems - Input array of inventory items to filter
	 * @param inSlot - Equipment slot gameplay tag to filter by
	 * @param outItems - Output array containing only items matching the specified slot
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static void FilterByItemSlot(const TArray<FInventoryItem>& inItems, FGameplayTag inSlot,
	                             TArray<FInventoryItem>& outItems);

	/**
	* Filters an array of inventory items by their equipment slot.
	*
	* @param inItems - Input array of inventory items to filter
	* @param inSlots - Equipment slots gameplay tag to filter by
	* @param outItems - Output array containing only items matching the specified slot
	*/
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static void FilterByItemSlots(const TArray<FInventoryItem>& inItems, TArray<FGameplayTag> inSlots,
	                             TArray<FInventoryItem>& outItems);

	/**
	 * Finds and returns a specific fragment from an item by its class type.
	 *
	 * @param inItem - Item to search for the fragment
	 * @param FragmentClass - Class type of the fragment to find
	 * @return The found fragment, or nullptr if not found
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary, meta = (DeterminesOutputType = "FragmentClass"))
	static UACFItemFragment* FindFragmentByClass(const UACFItem* inItem, TSubclassOf<UACFItemFragment> FragmentClass);

	/*
	* Finds and returns a specific fragment from an item by its class type.
	*
	* @param inItemClass - Class of the Item to search for the fragment
	* @param FragmentClass - Class type of the fragment to find
	* @return The found fragment, or nullptr if not found
	*/
	UFUNCTION(BlueprintPure, Category = ACFLibrary, meta = (DeterminesOutputType = "FragmentClass"))
	static UACFItemFragment* FindFragmentInItemClassByClass(const TSubclassOf<UACFItem> inItemClass, TSubclassOf<UACFItemFragment> FragmentClass, bool& OutFoundFragment);


	/**
	 * Retrieves the item descriptor data for a given item class.
	 *
	 * @param item - Item class to retrieve data from
	 * @param outData - Output descriptor containing item information
	 * @return True if data was successfully retrieved, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool GetItemData(const TSubclassOf<class UACFItem>& item, FItemDescriptor& outData);

	/**
	 * Gets the attribute set modifier for an equippable item.
	 *
	 * @param itemClass - Equippable item class to query
	 * @param outModifier - Output modifier containing attribute modifications
	 * @return True if modifier was found, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool GetEquippableAttributeSetModifier(const TSubclassOf<class UACFItem>& itemClass,
	                                              FAttributesSetModifier& outModifier);

	/**
	 * Gets all timed attribute set modifiers for a consumable item.
	 *
	 * @param itemClass - Consumable item class to query
	 * @param outModifiers - Output array of timed attribute modifiers
	 * @return True if modifiers were found, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool GetConsumableTimedAttributeSetModifier(const TSubclassOf<class UACFItem>& itemClass,
	                                                   TArray<FTimedAttributeSetModifier>& outModifiers);

	/**
	 * Gets all statistic modifiers for a consumable item.
	 *
	 * @param itemClass - Consumable item class to query
	 * @param outModifiers - Output array of statistic value modifiers
	 * @return True if modifiers were found, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool GetConsumableStatModifier(const TSubclassOf<class UACFItem>& itemClass,
	                                      TArray<FStatisticValue>& outModifiers);

	/* GAS GETTERS */

	/**
	 * Gets all gameplay effects applied by an equippable item.
	 * Used with Gameplay Ability System (GAS).
	 *
	 * @param itemClass - Equippable item class to query
	 * @param outModifiers - Output array of gameplay effect modifiers
	 * @return True if effects were found, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool GetEquippableGameplayEffects(const TSubclassOf<class UACFItem>& itemClass,
	                                         TArray<FGEModifier>& outModifiers);

	/**
	 * Gets the gameplay effect type for an equippable item.
	 *
	 * @param itemClass - Equippable item class to query
	 * @param outType - Output gameplay effect type
	 * @return True if type was found, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool GetEquippableGEType(const TSubclassOf<class UACFItem>& itemClass, EGEType& outType);

	/**
	 * Gets all gameplay effects applied by a consumable item.
	 *
	 * @param itemClass - Consumable item class to query
	 * @param outModifiers - Output array of gameplay effect modifiers
	 * @return True if effects were found, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool GetConsumableGameplayEffects(const TSubclassOf<class UACFItem>& itemClass,
	                                         TArray<FGEModifier>& outModifiers);

	/**
	 * Converts an inventory item to a base item structure.
	 *
	 * @param inItem - Inventory item to convert
	 * @return Base item structure
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FBaseItem MakeBaseItemFromInventory(const FInventoryItem& inItem);

		/**
	 * Converts a base inventory item to a Inventory item structure.
	 *
	 * @param inItem - Inventory item to convert
	 * @return Base item structure
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FInventoryItem MakeInventoryItemFromBase(const FBaseItem& inItem);

	/**
	 * Converts a base inventory item to a Inventory item structure with a new GUID
	 *
	 * @param inItem - Inventory item to convert
	 * @return Base item structure
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FInventoryItem MakeInventoryItemFromBaseWithNewGUID(const FBaseItem& inItem);

	/**
	 * Calculates the transform for shooting based on the source pawn and target type.
	 *
	 * @param SourcePawn - Pawn performing the shoot action
	 * @param targetType - Type of targeting to use (e.g., camera, weapon)
	 * @param outSourceLoc - Output source location for the shoot
	 * @return Transform representing the shoot direction and position
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FTransform GetShootTransform(APawn* SourcePawn, EShootTargetType targetType, FVector& outSourceLoc);

	/**
	 * Gets the current currency amount for a pawn.
	 *
	 * @param pawn - Pawn to query currency from
	 * @return Current currency amount
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static float GetPawnCurrency(const APawn* pawn);

	/**
	 * Gets the equipment component from a pawn.
	 *
	 * @param pawn - Pawn to retrieve component from
	 * @return Equipment component, or nullptr if not found
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static UACFEquipmentComponent* GetPawnEquipment(const APawn* pawn);

	/**
	 * Gets the currency component from a pawn.
	 *
	 * @param pawn - Pawn to retrieve component from
	 * @return Currency component, or nullptr if not found
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static UACFCurrencyComponent* GetPawnCurrencyComponent(const APawn* pawn);

	/**
	 * Checks if a pawn can use a specific consumable item.
	 * Validates requirements and conditions for consumption.
	 *
	 * @param pawn - Pawn attempting to use the item
	 * @param itemClass - Consumable item class to check
	 * @return True if the pawn can use the item, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool CanUseConsumableItem(const APawn* pawn, const TSubclassOf<class UACFConsumable>& itemClass);

	/**
	 * Gets the gameplay tag representing the desired use action for a consumable item.
	 *
	 * @param itemClass - Consumable item class to query
	 * @return Gameplay tag for the use ability
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FGameplayTag GetDesiredUseAction(const TSubclassOf<class UACFConsumable>& itemClass);

	/* DEFAULTS */

	/**
	 * Gets the default world item class used by the system.
	 *
	 * @return Default world item class
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static TSubclassOf<class AACFWorldItem> GetDefaultWorldItemClass();

	/**
	* Gets the default hit trace channels used by the system.
	*
	* @return Default hit trace channels
	*/
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static TArray<TEnumAsByte<ECollisionChannel>> GetDefaultHitTraceChannels();

	/**
	 * Gets the default name for currency in the system.
	 *
	 * @return Default currency name text
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FText GetDefaultCurrencyName();

	/**
	 * Gets the root gameplay tag for item types.
	 * All item type tags should be children of this root tag.
	 *
	 * @return Root gameplay tag for item types
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FGameplayTag GetItemTypeTagRoot();

	/**
	 * Gets the root gameplay tag for item slots.
	 * All item slot tags should be children of this root tag.
	 *
	 * @return Root gameplay tag for item slots
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FGameplayTag GetItemSlotTagRoot();

	/**
	 * Validates if a gameplay tag is a valid item type tag.
	 * Checks if the tag is a child of the item type root tag.
	 *
	 * @param TagToCheck - Gameplay tag to validate
	 * @return True if the tag is a valid item type, false otherwise
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool IsValidItemTypeTag(FGameplayTag TagToCheck);

	/**
	 * Validates if a gameplay tag is a valid item slot tag.
	 * Checks if the tag is a child of the item slot root tag.
	 *
	 * @param TagToCheck - Gameplay tag to validate
	 * @return True if the tag is a valid item slot, false otherwise
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool IsValidItemSlotTag(FGameplayTag TagToCheck);

	static AACFWorldItem* SpawnWorldItem(UObject* WorldContextObject, const FVector& location,
	                                     float acceptanceRadius = 100.f);

	/**
	 * Spawns a world item preserving the live UACFItem* instance and its
	 * runtime state (modified fragments, changed properties, etc.).
	 * This is the Lyra-aligned path: the UObject IS the identity.
	 */
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static AACFWorldItem* SpawnWorldItemWithInstance(UObject* WorldContextObject,
	                                                 const FInventoryItem& ItemToSpawn,
	                                                 const FVector& location,
	                                                 float acceptanceRadius = 100.f);
};
