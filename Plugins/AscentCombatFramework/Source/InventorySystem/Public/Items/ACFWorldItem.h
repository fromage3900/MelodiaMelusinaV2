// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ALSSavableInterface.h"
#include "Components/ACFEquipmentComponent.h"
#include "CoreMinimal.h"
#include "Interfaces/ACFInteractableInterface.h"
#include "Items/ACFItem.h"

#include "ACFWorldItem.generated.h"

class UACFStorageComponent;
class UStaticMeshComponent;
class USceneComponent;

/**
 * @class AACFWorldItem
 * Represents a world item in ACF.
 *
 * This class implements interaction and saving functionality for items that exist in the game world.
 */
UCLASS()
class INVENTORYSYSTEM_API AACFWorldItem : public AActor, public IACFInteractableInterface, public IALSSavableInterface {
	GENERATED_BODY()

public:
	/**
	 * Default constructor.
	 */
	AACFWorldItem();

	/**
	 * Called when the game starts or when spawned.
	 */
	virtual void BeginPlay() override;

	/**
	 * Sets the item mesh based on the provided item data.
	 * @param inItem The item data used to set the mesh.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetItemMesh(const FBaseItem& inItem);

	/**
	 * Adds an item to this world item.
	 * @param inItem The item to add.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void AddItem(const FBaseItem& inItem);

	/** Adds an inventory item preserving the live UACFItem* and its runtime state. */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void AddInventoryItem(const FInventoryItem& inItem);

	/**
	 * Adds currency to this world item.
	 * @param currencyAmount The amount of currency to add.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void AddCurrency(float currencyAmount);

	// INTERACTION INTERFACE

	/**
	 * Called when a pawn interacts with this object.
	 * @param Pawn The pawn that interacted.
	 * @param interactionType The type of interaction.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");
	virtual void OnInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "") override;

	/**
	 * Called when a local interaction happens (client-side).
	 * @param Pawn The interacting pawn.
	 * @param interactionType The type of interaction.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnLocalInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");
	void OnLocalInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "");

	/**
	 * Called when a pawn registers this item as interactable.
	 * @param Pawn The pawn that registered the interaction.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnInteractableRegisteredByPawn(class APawn* Pawn);
	virtual void OnInteractableRegisteredByPawn_Implementation(class APawn* Pawn) override;

	/**
	 * Called when a pawn unregisters this item as interactable.
	 * @param Pawn The pawn that unregistered the interaction.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnInteractableUnregisteredByPawn(class APawn* Pawn);
	virtual void OnInteractableUnregisteredByPawn_Implementation(class APawn* Pawn) override;

	/**
	 * Determines if this item can be interacted with.
	 * @param Pawn The pawn attempting interaction.
	 * @return True if the item can be interacted with, false otherwise.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	bool CanBeInteracted(class APawn* Pawn);
	virtual bool CanBeInteracted_Implementation(class APawn* Pawn) override;

	/**
	 * Retrieves the name of the interactable object.
	 * @return The interactable name as an FText.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	FText GetInteractableName();
	virtual FText GetInteractableName_Implementation() override;

	// END INTERACTION INTERFACE

	/**
	 * Returns the items related to this world item.
	 * @return An array of FBaseItem representing the items.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	TArray<FInventoryItem> GetItems() const;

	/**
	 * Retrieves the descriptor of the first item in storage.
	 * @return An FItemDescriptor of the first item.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FItemDescriptor GetFirstItemInfo() const { return ItemInfo; }

	/**
	 * Determines whether the actor should be destroyed when all items are gathered.
	 * @return True if the actor should be destroyed, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE bool DestroyOnAllItemsGathered() const { return bDestroyOnGather; }

	/**
	 * Handles changes in the storage content.
	 * @param items The updated list of items in storage.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void HandleStorageChanged(const FBaseItem& items);
	virtual void HandleStorageChanged_Implementation(const FBaseItem& items);

	UFUNCTION(BlueprintCallable, Category = ACF)
	void GatherItem(UACFInventoryComponent* SourceInventoryComp);

protected:
	/** Determines if the actor should be destroyed once all items are gathered. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	bool bDestroyOnGather = true;

	/** Default source for inventory operations when gathering items from world pickups. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	EInventorySource InventorySource = EInventorySource::Pawn;

	/** Determines if the actor should visualize the World Mesh from the first item in the Invantory. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	bool bUseWorldMeshFromFirstItem = true;

	/** The mesh component representing the world item. */
	UPROPERTY(BlueprintReadWrite, VisibleAnywhere, Category = ACF)
	TObjectPtr<UStaticMeshComponent> ObjectMesh;

	/** The storage component that holds the items. */
	UPROPERTY(BlueprintReadWrite, VisibleAnywhere, Category = ACF)
	TObjectPtr<UACFStorageComponent> StorageComponent;

	/** The root component of the item. */
	UPROPERTY(BlueprintReadWrite, VisibleAnywhere, Category = ACF)
	TObjectPtr<USceneComponent> RootComp;

	/** The descriptor of the first stored item. */
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	FItemDescriptor ItemInfo;

	/**
	 * Called when the item is loaded.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ALS)
	void OnLoaded();

	TObjectPtr<UACFInventoryComponent> GetInventoryComponentFromSource(APawn* Pawn) const;

};
