#include "MelodiaProgressionComponent.h"

UMelodiaProgressionComponent::UMelodiaProgressionComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

int32 UMelodiaProgressionComponent::AddXP(int32 Amount)
{
	if (Amount <= 0)
	{
		return CurrentXP;
	}

	CurrentXP += Amount;
	while (CurrentXP >= XPToNextLevel && Level < 99)
	{
		CurrentXP -= XPToNextLevel;
		Level++;
		XPToNextLevel = FMath::RoundToInt(static_cast<float>(XPToNextLevel) * 1.25f);
		UE_LOG(LogTemp, Log, TEXT("Melodia: Level up! Now level %d, next level at %d XP."), Level, XPToNextLevel);
	}

	return CurrentXP;
}

int32 UMelodiaProgressionComponent::AddCurrency(int32 Amount)
{
	Currency = FMath::Max(0, Currency + Amount);
	return Currency;
}

void UMelodiaProgressionComponent::RestoreCurrency(const int64 SavedCurrency)
{
	Currency = static_cast<int32>(FMath::Clamp<int64>(SavedCurrency, 0, MAX_int32));
}

bool UMelodiaProgressionComponent::CanLevelUp() const
{
	return CurrentXP >= XPToNextLevel && Level < 99;
}

void UMelodiaProgressionComponent::AddItem(FName ItemId, FText DisplayName, int32 Quantity)
{
	for (FMelodiaInventoryItem& Item : Inventory)
	{
		if (Item.ItemId == ItemId)
		{
			Item.Quantity += Quantity;
			return;
		}
	}

	FMelodiaInventoryItem NewItem;
	NewItem.ItemId = ItemId;
	NewItem.DisplayName = DisplayName;
	NewItem.Quantity = Quantity;
	Inventory.Add(NewItem);
}

bool UMelodiaProgressionComponent::HasItem(FName ItemId, int32 Quantity) const
{
	for (const FMelodiaInventoryItem& Item : Inventory)
	{
		if (Item.ItemId == ItemId && Item.Quantity >= Quantity)
		{
			return true;
		}
	}
	return false;
}

int32 UMelodiaProgressionComponent::GetItemQuantity(FName ItemId) const
{
	for (const FMelodiaInventoryItem& Item : Inventory)
	{
		if (Item.ItemId == ItemId)
		{
			return Item.Quantity;
		}
	}
	return 0;
}
