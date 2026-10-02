// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFBuildRecipe.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <Net/Serialization/FastArraySerializer.h>
#include "Engine/NetSerialization.h"

#include "ACFBuildINGManagerComponent.generated.h"

UENUM(BlueprintType)
enum class EBuildingMode : uint8 {
	ENone = 0 UMETA(DisplayName = "None"),
	EBuilding = 1 UMETA(DisplayName = "Building"),
	EDismantling = 2 UMETA(DisplayName = "Dismantling"),
};

class IACFBuildableInterface;
class UInputMappingContext;

// Fast Array Item per i Recipe 
USTRUCT()
struct FACFRecipeIdItem : public FFastArraySerializerItem
{
	GENERATED_BODY()

	UPROPERTY()
	TObjectPtr<UACFBuildRecipe> Recipe;

	FACFRecipeIdItem() {}
	FACFRecipeIdItem(UACFBuildRecipe* InRecipe) : Recipe(InRecipe) {}

	void PreReplicatedRemove(const struct FACFRecipeIdArray& InArraySerializer) {}
	void PostReplicatedAdd(const struct FACFRecipeIdArray& InArraySerializer) {}
	void PostReplicatedChange(const struct FACFRecipeIdArray& InArraySerializer) {}
};

// Fast Array Serializer per i Recipe IDs
USTRUCT()
struct FACFRecipeIdArray : public FFastArraySerializer
{
	GENERATED_BODY()

public:
	UPROPERTY()
	TArray<FACFRecipeIdItem> Items;

	UPROPERTY(NotReplicated)
	class UACFBuildingManagerComponent* OwnerComponent;

	FACFRecipeIdArray() {
		OwnerComponent = nullptr;
	}

	bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
	{
		return FFastArraySerializer::FastArrayDeltaSerialize<FACFRecipeIdItem, FACFRecipeIdArray>(Items, DeltaParms, *this);
	}

	/*
	void PreReplicatedRemove(const TArrayView<int32> RemovedIndices, int32 FinalSize);
	void PostReplicatedAdd(const TArrayView<int32> AddedIndices, int32 FinalSize);
	void PostReplicatedChange(const TArrayView<int32> ChangedIndices, int32 FinalSize);*/
};

template<>
struct TStructOpsTypeTraits<FACFRecipeIdArray> : public TStructOpsTypeTraitsBase2<FACFRecipeIdArray>
{
	enum
	{
		WithNetDeltaSerializer = true,
	};
};


DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBuildingModeChanged, EBuildingMode, buildingMode);

/*
 * A component that handles the logic for placement, validation, and replication of buildable objects.
 * Can be added to any actor to make it compatible with the building system
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTBUILDINGSYSTEM_API UACFBuildingManagerComponent : public UActorComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UACFBuildingManagerComponent();

	/**
	 * Initiates dismantling mode for removing placed structures.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StartDismantling();

	/**
	 * Ends the current building mode.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void EndBuildMode();

	/**
	 * Gets the current building mode.
	 * @return The current building mode.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	EBuildingMode GetBuildingMode() const;

	/**
	 * Finalizes the current build placement and spawns the structure.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void Build();

	/**
	 * Server-side function to build a structure with a given ID, location, and rotation.
	 * @param Id The primary asset ID of the structure.
	 * @param Location The world location to place the structure.
	 * @param Rotation The rotation to apply to the structure.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void ServerBuild(const FPrimaryAssetId& Id, const FVector& Location, const FRotator& Rotation);

	/**
	 * Server-side function to dismantle a buildable
	 * @param buildable The actor to be dismantled
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void Dismantle(AActor* buildable);

	/**
	 * Checks if the system is currently in building mode.
	 * @return True if in building mode.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsBuilding() const;

	/**
	 * Checks if the system is currently in dismantling mode.
	 * @return True if in dismantling mode.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsDismantling() const;

	/**
	 * Utility wrapper to check if an actor implementing IACFBuildableInterface
	 * can be placed at its current location and rotation.
	 * @param BuildableActor - Actor to check.
	 * @return True if placement is valid, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsBuildablePlaceable(AActor* BuildableActor) const;

	/**
	 * Starts the build mode using the specified recipe.
	 * @param Recipe The build recipe to use.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StartBuild(UACFBuildRecipe* Recipe);

	/**
	 * Rotates the current building preview by the specified amount.
	 * @param Rotation The rotation offset to apply.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void RotateBuildingBy(const FRotator& Rotation);

	/**
	 * Rotates the current building preview by the default amount.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void RotateBuildingByStep();

	/**
	 * Retrieves the list of available build recipes.
	 * @return An array of build recipes.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	const TArray<UACFBuildRecipe*>& GetRecipes() const;

	/**
	 * Adds a new recipe to the list of available build options.
	 * @param Recipe The recipe to add.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void AddRecipe(UACFBuildRecipe* Recipe);

	UFUNCTION(BlueprintPure, Category = ACF)
	APlayerController* GetPlayerController() const;

	UFUNCTION(BlueprintPure, Category = ACF)
	UACFInventoryComponent* GetInventoryComponent() const;

	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnBuildingModeChanged OnBuildingModeChanged;
	
	bool bRecipesCacheDirty = true;
protected:
	// List of available build recipes
	UPROPERTY(EditAnywhere, SaveGame, Category = ACF)
	TArray<UACFBuildRecipe*> Recipes;

	// Material to indicate valid placement
	UPROPERTY(Category = ACF, EditAnywhere)
	TObjectPtr<UMaterialInterface> ValidMaterial;

	// Material to indicate invalid placement
	UPROPERTY(Category = ACF, EditAnywhere)
	TObjectPtr<UMaterialInterface> InvalidMaterial;

	// Priority of this input mapping
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Input Context")
	FRotator DefaultRotationStep = FRotator(0.f, 45.f, 0.f);

	// Input Mapping Context to be activated with these bindings
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Input Context")
	UInputMappingContext* BuildInputMappingContext = nullptr;

	// Priority of this input mapping
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Input Context")
	int32 MappingContextPriority = 0;

	UACFBuildRecipe* GetRecipeCheckedById(const FPrimaryAssetId& Id);

	UACFBuildRecipe* GetRecipeCheckedByClass(UClass* ItemType);

	TScriptInterface<IACFBuildableInterface> GetCurrentObject() const;

	void TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	void BeginPlay() override;

	FVector GetLocation(const APlayerController* Controller, const TArray<AActor*>& ToIgnore);

private:
	// Server-side async loading callback
	void OnServerActorClassLoaded(const FPrimaryAssetId& Id, const FVector& Location, const FRotator& Rotation);

	// Helper per spawn finale sul server
	void SpawnActorOnServer(UACFBuildRecipe* Recipe, UClass* ActorClass, const FVector& Location, const FRotator& Rotation);

	UFUNCTION(Server, Reliable)
	void SetBuildingMode(EBuildingMode val);


	void OnActorClassLoaded(const APlayerController* Controller);

	void SpawnPreviewActor(UClass* ActorClass, const APlayerController* Controller);
	void MoveBuildingTo(const FVector& Location);

	UFUNCTION(Server, Reliable)
	void AddRecipeServer(UACFBuildRecipe* RecipeId);

	void UpdateValidityFeedback();

	UPROPERTY()
	TScriptInterface<IACFBuildableInterface> CurrentObject;

	UPROPERTY(ReplicatedUsing = OnRep_RecipesIds, SaveGame)
	FACFRecipeIdArray  RecipesIds;

	UFUNCTION()
	void OnRep_RecipesIds();

	UFUNCTION()
	void OnRep_BuildingMode();

	void UpdateMappingContext();

	UPROPERTY(ReplicatedUsing = OnRep_BuildingMode)
	EBuildingMode BuildingMode = EBuildingMode::ENone;

	UPROPERTY()
	TObjectPtr<UACFBuildRecipe> CurrentRecipe;

	FVector LastLocation;
	/** Cached last placement validity state to avoid redundant material updates */
	bool bLastPlacementValid = false;

	bool bFirstCheck = true;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UACFBuildRecipe>> CachedRecipes;



	void RebuildCachedRecipes();
};
