// ===== ACFCraftingComponent.cpp =====

#include "ACFCraftingComponent.h"
#include "ACFCraftRecipeDataAsset.h"
#include "ACFItemSystemFunctionLibrary.h"
#include "ACFItemsManagerComponent.h"
#include "Components/ACFCurrencyComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Net/UnrealNetwork.h"

UACFCraftingComponent::UACFCraftingComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UACFCraftingComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    
    DOREPLIFETIME(UACFCraftingComponent, RuntimeRecipesFastArray);
}

void UACFCraftingComponent::BeginPlay()
{
    Super::BeginPlay();
    
    // Setup FastArray owner
    RuntimeRecipesFastArray.SetOwnerComponent(this);
    
    // BACKWARDS COMPATIBLE: Load initial static recipes as before
    for (UACFCraftRecipeDataAsset* recipeAsset : ItemsRecipes)
    {
        if (recipeAsset)
        {
            CraftableItems.Add(recipeAsset->GetCraftingRecipe());
        }
    }
}

// ===== FastArray Implementation =====

void FACFRuntimeRecipesFastArray::AddRecipe(UACFCraftRecipeDataAsset* Recipe)
{
    if (Recipe && !ContainsRecipe(Recipe))
    {
        FACFRuntimeRecipeItem NewItem(Recipe);
        Items.Add(NewItem);
        MarkItemDirty(NewItem);
    }
}

bool FACFRuntimeRecipesFastArray::RemoveRecipe(UACFCraftRecipeDataAsset* Recipe)
{
    for (int32 i = Items.Num() - 1; i >= 0; --i)
    {
        if (Items[i].RecipeDataAsset == Recipe)
        {
            Items.RemoveAt(i);
            MarkArrayDirty();
            return true;
        }
    }
    return false;
}

bool FACFRuntimeRecipesFastArray::ContainsRecipe(UACFCraftRecipeDataAsset* Recipe) const
{
    return Items.ContainsByPredicate([Recipe](const FACFRuntimeRecipeItem& Item)
    {
        return Item.RecipeDataAsset == Recipe;
    });
}

void FACFRuntimeRecipesFastArray::ClearAllRecipes()
{
    Items.Empty();
    MarkArrayDirty();
}

TArray<UACFCraftRecipeDataAsset*> FACFRuntimeRecipesFastArray::GetAllRecipes() const
{
    TArray<UACFCraftRecipeDataAsset*> Result;
    Result.Reserve(Items.Num());
    
    for (const FACFRuntimeRecipeItem& Item : Items)
    {
        if (Item.RecipeDataAsset)
        {
            Result.Add(Item.RecipeDataAsset);
        }
    }
    
    return Result;
}

void FACFRuntimeRecipesFastArray::PreReplicatedRemove(const TArrayView<int32> RemovedIndices, int32 FinalSize)
{
    if (OwnerComponent.IsValid())
    {
        for (int32 Index : RemovedIndices)
        {
            if (Items.IsValidIndex(Index))
            {
                OwnerComponent->HandleRecipeRemoved(Items[Index].RecipeDataAsset);
            }
        }
    }
}

void FACFRuntimeRecipesFastArray::PostReplicatedAdd(const TArrayView<int32> AddedIndices, int32 FinalSize)
{
    if (OwnerComponent.IsValid())
    {
        for (int32 Index : AddedIndices)
        {
            if (Items.IsValidIndex(Index))
            {
                OwnerComponent->HandleRecipeAdded(Items[Index].RecipeDataAsset);
            }
        }
    }
}

void FACFRuntimeRecipesFastArray::PostReplicatedChange(const TArrayView<int32> ChangedIndices, int32 FinalSize)
{
    if (OwnerComponent.IsValid())
    {
        OwnerComponent->OnRecipesChanged();
    }
}

// ===== Component API Implementation =====

void UACFCraftingComponent::AddRecipe(UACFCraftRecipeDataAsset* Recipe)
{
    if (!Recipe)
    {
        UE_LOG(LogTemp, Warning, TEXT("AddRecipe: Recipe is null"));
        return;
    }

    if (GetOwnerRole() == ROLE_Authority)
    {
        RuntimeRecipesFastArray.AddRecipe(Recipe);
    }
}

bool UACFCraftingComponent::RemoveRecipe(UACFCraftRecipeDataAsset* Recipe)
{
    if (!Recipe)
    {
        return false;
    }

    if (GetOwnerRole() == ROLE_Authority)
    {
        return RuntimeRecipesFastArray.RemoveRecipe(Recipe);
    }
    
    return false;
}

bool UACFCraftingComponent::HasRecipe(UACFCraftRecipeDataAsset* Recipe) const
{
    if (!Recipe)
    {
        return false;
    }

    // Check runtime recipes
    if (RuntimeRecipesFastArray.ContainsRecipe(Recipe))
    {
        return true;
    }

    // Check static recipes (backwards compatible)
    return ItemsRecipes.Contains(Recipe);
}

void UACFCraftingComponent::AddRecipes(const TArray<UACFCraftRecipeDataAsset*>& RecipesToAdd)
{
    if (GetOwnerRole() != ROLE_Authority)
    {
        return;
    }

    for (UACFCraftRecipeDataAsset* Recipe : RecipesToAdd)
    {
        if (Recipe)
        {
            RuntimeRecipesFastArray.AddRecipe(Recipe);
        }
    }
}

void UACFCraftingComponent::RemoveRecipes(const TArray<UACFCraftRecipeDataAsset*>& RecipesToRemove)
{
    if (GetOwnerRole() != ROLE_Authority)
    {
        return;
    }

    for (UACFCraftRecipeDataAsset* Recipe : RecipesToRemove)
    {
        if (Recipe)
        {
            RuntimeRecipesFastArray.RemoveRecipe(Recipe);
        }
    }
}

void UACFCraftingComponent::ClearRuntimeRecipes()
{
    if (GetOwnerRole() == ROLE_Authority)
    {
        RuntimeRecipesFastArray.ClearAllRecipes();
    }
}

TArray<UACFCraftRecipeDataAsset*> UACFCraftingComponent::GetAllRecipeDataAssets() const
{
    TArray<UACFCraftRecipeDataAsset*> AllRecipes;
    
    // Add static recipes (backwards compatible)
    AllRecipes.Append(ItemsRecipes);
    
    // Add runtime recipes
    AllRecipes.Append(RuntimeRecipesFastArray.GetAllRecipes());
    
    return AllRecipes;
}

void UACFCraftingComponent::RebuildCraftableItemsCache()
{
    CraftableItems.Empty();
    
    // Add static recipes
    for (UACFCraftRecipeDataAsset* Recipe : ItemsRecipes)
    {
        if (Recipe)
        {
            CraftableItems.Add(Recipe->GetCraftingRecipe());
        }
    }
    
    // Add runtime recipes
    TArray<UACFCraftRecipeDataAsset*> RuntimeRecipes = RuntimeRecipesFastArray.GetAllRecipes();
    for (UACFCraftRecipeDataAsset* Recipe : RuntimeRecipes)
    {
        if (Recipe)
        {
            CraftableItems.Add(Recipe->GetCraftingRecipe());
        }
    }
}

void UACFCraftingComponent::HandleRecipeAdded(UACFCraftRecipeDataAsset* Recipe)
{
    if (Recipe)
    {
        CraftableItems.Add(Recipe->GetCraftingRecipe());
        OnRecipeAdded(Recipe);
    }
}

void UACFCraftingComponent::HandleRecipeRemoved(UACFCraftRecipeDataAsset* Recipe)
{
    if (Recipe)
    {
        FACFCraftingRecipe RecipeData = Recipe->GetCraftingRecipe();
        CraftableItems.Remove(RecipeData);
        OnRecipeRemoved(Recipe);
    }
}

// ===== UNCHANGED FUNCTIONS (same as before) =====

bool UACFCraftingComponent::CanPawnUpgradeItem(const FInventoryItem& itemToUpgrade, const APawn* pawnOwner) const
{
    if (!GetPawnInventory(pawnOwner).Contains(itemToUpgrade))
    {
        return false;
    }
    
    UACFEquipmentComponent* equipComp = GetPawnEquipment(pawnOwner);
    FItemDescriptor itemData;
    UACFItemSystemFunctionLibrary::GetItemData(itemToUpgrade.ItemClass, itemData);
    
    if (equipComp)
    {
        if (itemData.bUpgradable && GetPawnCurrency(pawnOwner) >= PriceMultiplierOnSell * itemData.UpgradeCurrencyCost)
        {
            return equipComp->HasEnoughItemsOfType(itemData.RequiredItemsToUpgrade);
        }
    }
    
    return false;
}

bool UACFCraftingComponent::CanPawnCraftItem(const FACFCraftingRecipe& itemToCraft, const APawn* buyer) const
{
    UACFEquipmentComponent* equipComp = GetPawnEquipment(buyer);
    
    if (equipComp->NumberOfItemCanTake(itemToCraft.OutputItem.ItemClass) < itemToCraft.OutputItem.Count)
    {
        return false;
    }
    
    return equipComp->HasEnoughItemsOfType(itemToCraft.RequiredItems) && 
           GetPawnCurrency(buyer) >= PriceMultiplierOnSell * itemToCraft.CraftingCost;
}

void UACFCraftingComponent::UpgradeItem(const FInventoryItem& itemToUpgrade, APawn* instigator)
{
    if (GetItemsManager())
    {
        GetItemsManager()->UpgradeItem(itemToUpgrade, instigator, this);
    }
}

void UACFCraftingComponent::CraftItem(const FACFCraftingRecipe& ItemToCraft, APawn* instigator)
{
    if (GetItemsManager())
    {
        GetItemsManager()->CraftItem(ItemToCraft, instigator, this);
    }
}

TArray<FInventoryItem> UACFCraftingComponent::GetAllPawnUpgradableItems(const APawn* pawn) const
{
    TArray<FInventoryItem> upgradables;
    const TArray<FInventoryItem> playerInventory = GetPawnInventory(pawn);
    
    for (const auto& elem : playerInventory)
    {
        FItemDescriptor itemData;
        UACFItemSystemFunctionLibrary::GetItemData(elem.ItemClass, itemData);
        
        if (itemData.bUpgradable)
        {
            upgradables.Add(elem);
        }
    }
    
    return upgradables;
}

bool UACFCraftingComponent::TryGetCraftableRecipeForItem(const FBaseItem& recipe, FACFCraftingRecipe& outRecipe) const
{
    if (CraftableItems.Contains(recipe))
    {
        outRecipe = *CraftableItems.FindByKey(recipe);
        return true;
    }
    
    return false;
}