// ===== ACFCraftingComponent.h =====
#pragma once

#include "ACFVendorComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Items/ACFItem.h"
#include "Engine/NetSerialization.h"
#include "ACFCraftingComponent.generated.h"

class UACFCraftRecipeDataAsset;

// FastArraySerializer item for runtime recipes
USTRUCT(BlueprintType)
struct FACFRuntimeRecipeItem : public FFastArraySerializerItem
{
    GENERATED_BODY()

    UPROPERTY(SaveGame)
    UACFCraftRecipeDataAsset* RecipeDataAsset;

    FACFRuntimeRecipeItem()
        : RecipeDataAsset(nullptr)
    {
    }

    FACFRuntimeRecipeItem(UACFCraftRecipeDataAsset* InRecipe)
        : RecipeDataAsset(InRecipe)
    {
    }

    bool operator==(const FACFRuntimeRecipeItem& Other) const
    {
        return RecipeDataAsset == Other.RecipeDataAsset;
    }
};

// FastArraySerializer for runtime recipes
USTRUCT(BlueprintType)
struct FACFRuntimeRecipesFastArray : public FFastArraySerializer
{
    GENERATED_BODY()

    UPROPERTY(SaveGame)
    TArray<FACFRuntimeRecipeItem> Items;

    UPROPERTY()
    TWeakObjectPtr<class UACFCraftingComponent> OwnerComponent;

    // FastArraySerializer interface - ✅ Signatures corrette
    void PreReplicatedRemove(const TArrayView<int32> RemovedIndices, int32 FinalSize);
    void PostReplicatedAdd(const TArrayView<int32> AddedIndices, int32 FinalSize);
    void PostReplicatedChange(const TArrayView<int32> ChangedIndices, int32 FinalSize);

    bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
    {
        return FFastArraySerializer::FastArrayDeltaSerialize<FACFRuntimeRecipeItem, FACFRuntimeRecipesFastArray>(Items, DeltaParms, *this);
    }

    // Utility functions
    void AddRecipe(UACFCraftRecipeDataAsset* Recipe);
    bool RemoveRecipe(UACFCraftRecipeDataAsset* Recipe);
    bool ContainsRecipe(UACFCraftRecipeDataAsset* Recipe) const;
    void ClearAllRecipes();
    TArray<UACFCraftRecipeDataAsset*> GetAllRecipes() const;

    void SetOwnerComponent(UACFCraftingComponent* InOwner)
    {
        OwnerComponent = InOwner;
    }
};

// Template specialization for NetDeltaSerializer
template<>
struct TStructOpsTypeTraits<FACFRuntimeRecipesFastArray> : public TStructOpsTypeTraitsBase2<FACFRuntimeRecipesFastArray>
{
    enum
    {
        WithNetDeltaSerializer = true,
    };
};

UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CRAFTINGSYSTEM_API UACFCraftingComponent : public UACFVendorComponent
{
    GENERATED_BODY()

public:
    UACFCraftingComponent();

    /*------------------- RECIPE MANAGEMENT (NEW) -----------------------------------*/
    
    UFUNCTION(BlueprintCallable, Category = "ACF | Crafting")
    void AddRecipe(UACFCraftRecipeDataAsset* Recipe);

    UFUNCTION(BlueprintCallable, Category = "ACF | Crafting")
    bool RemoveRecipe(UACFCraftRecipeDataAsset* Recipe);

    UFUNCTION(BlueprintPure, Category = "ACF | Crafting")
    bool HasRecipe(UACFCraftRecipeDataAsset* Recipe) const;

    UFUNCTION(BlueprintCallable, Category = "ACF | Crafting")
    void AddRecipes(const TArray<UACFCraftRecipeDataAsset*>& RecipesToAdd);

    UFUNCTION(BlueprintCallable, Category = "ACF | Crafting")
    void RemoveRecipes(const TArray<UACFCraftRecipeDataAsset*>& RecipesToRemove);

    UFUNCTION(BlueprintCallable, Category = "ACF | Crafting")
    void ClearRuntimeRecipes();

    UFUNCTION(BlueprintPure, Category = "ACF | Crafting")
    TArray<UACFCraftRecipeDataAsset*> GetAllRecipeDataAssets() const;

    /*------------------- CHECKS (UNCHANGED) -----------------------------------*/
    
    UFUNCTION(BlueprintCallable, Category = "ACF | Checks")
    bool CanPawnUpgradeItem(const FInventoryItem& itemToUpgrade, const APawn* pawnOwner) const;

    UFUNCTION(BlueprintCallable, Category = "ACF | Checks")
    bool CanPawnCraftItem(const FACFCraftingRecipe& itemToCraft, const APawn* buyer) const;

    /*------------------- SERVER SIDE (UNCHANGED) -----------------------------------*/
    
    UFUNCTION(BlueprintCallable, Category = "ACF | Crafting")
    void CraftItem(const FACFCraftingRecipe& ItemToCraft, APawn* instigator);

    UFUNCTION(BlueprintCallable, Category = "ACF | Crafting")
    void UpgradeItem(const FInventoryItem& itemToUpgrade, APawn* instigator);

    /*-------------------PLAYER STUFF (UNCHANGED) -----------------------------------*/
    
    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    TArray<FInventoryItem> GetAllPawnUpgradableItems(const APawn* pawn) const;

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    TArray<FACFCraftingRecipe> GetCraftableRecipes() const
    {
        return CraftableItems;
    }

    UFUNCTION(BlueprintCallable, Category = "ACF | Getters")
    bool TryGetCraftableRecipeForItem(const FBaseItem& recipe, FACFCraftingRecipe& outRecipe) const;

    // DEPRECATED - Kept for backwards compatibility
    UFUNCTION(BlueprintCallable, Category = "ACF | Setters", meta = (DeprecatedFunction, DeprecationMessage = "Use AddRecipe(DataAsset) instead"))
    void AddNewRecipe(const FACFCraftingRecipe& recipe)
    {
        CraftableItems.Add(recipe);
    }

    UFUNCTION(BlueprintCallable, Category = "ACF | Setters", meta = (DeprecatedFunction, DeprecationMessage = "Use RemoveRecipe(DataAsset) instead"))
    void RemoveOldRecipe(const FACFCraftingRecipe& recipe)
    {
        CraftableItems.Remove(recipe);
    }

    /*-------------------BLUEPRINT EVENTS (NEW) -----------------------------------*/
    
    UFUNCTION(BlueprintImplementableEvent, Category = "ACF | Crafting")
    void OnRecipeAdded(UACFCraftRecipeDataAsset* Recipe);

    UFUNCTION(BlueprintImplementableEvent, Category = "ACF | Crafting")
    void OnRecipeRemoved(UACFCraftRecipeDataAsset* Recipe);

    UFUNCTION(BlueprintImplementableEvent, Category = "ACF | Crafting")
    void OnRecipesChanged();

        // Internal callbacks from FastArray
    void HandleRecipeAdded(UACFCraftRecipeDataAsset* Recipe);
    void HandleRecipeRemoved(UACFCraftRecipeDataAsset* Recipe);

protected:
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    // BACKWARDS COMPATIBLE: Original static recipes
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TArray<UACFCraftRecipeDataAsset*> ItemsRecipes;

    // NEW: Runtime recipes with replication
    UPROPERTY(Replicated, SaveGame)
    FACFRuntimeRecipesFastArray RuntimeRecipesFastArray;

private:
    UPROPERTY()
    TArray<FACFCraftingRecipe> CraftableItems;

    void RebuildCraftableItemsCache();
    

};