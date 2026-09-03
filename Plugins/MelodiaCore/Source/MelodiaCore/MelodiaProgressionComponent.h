#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaProgressionComponent.generated.h"

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaInventoryItem
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Inventory")
	FName ItemId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Inventory")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Inventory")
	int32 Quantity = 0;
};

UCLASS(Blueprintable, ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class MELODIACORE_API UMelodiaProgressionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaProgressionComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Progression")
	int32 Level = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Progression")
	int32 CurrentXP = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Progression")
	int32 XPToNextLevel = 100;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Progression")
	int32 Currency = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Inventory")
	TArray<FMelodiaInventoryItem> Inventory;

	UFUNCTION(BlueprintCallable, Category="Melodia|Progression")
	int32 AddXP(int32 Amount);

	UFUNCTION(BlueprintCallable, Category="Melodia|Progression")
	int32 AddCurrency(int32 Amount);

	/** Restore durable currency from the profile save without treating it as a gameplay award. */
	void RestoreCurrency(int64 SavedCurrency);

	UFUNCTION(BlueprintCallable, Category="Melodia|Progression")
	bool CanLevelUp() const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Progression")
	void AddItem(FName ItemId, FText DisplayName, int32 Quantity = 1);

	UFUNCTION(BlueprintCallable, Category="Melodia|Progression")
	bool HasItem(FName ItemId, int32 Quantity = 1) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Progression")
	int32 GetItemQuantity(FName ItemId) const;
};
