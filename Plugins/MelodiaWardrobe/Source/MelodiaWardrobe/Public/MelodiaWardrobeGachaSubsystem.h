// MelodiaWardrobe — gacha loop (Decision 043, hand-rolled per Decision 045).
//
// Weighted random pull, 1 Golden per pull, idempotent on GrantId via its own
// runtime ConsumedGrantIds set. Quantum ranking is a later swap-in behind the
// same signature (AGENTS.md section "Quantum usage").

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaWardrobeGachaSubsystem.generated.h"

class UMelodiaWardrobeSubsystem;
class UMelodiaTokenWalletSubsystem;
class UMelodiaCosmeticCatalog;

USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaPullResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wardrobe|Gacha")
	bool bSuccess = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wardrobe|Gacha")
	FName CosmeticId;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wardrobe|Gacha")
	FName GrantId;
};

UCLASS()
class MELODIAWARDROBE_API UMelodiaWardrobeGachaSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe|Gacha", meta=(WorldContext="WorldContextObject"))
	static UMelodiaWardrobeGachaSubsystem* Get(const UObject* WorldContextObject);

	/** One pull: 1 Golden -> one weighted-random cosmetic, atomic and idempotent on GrantId. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe|Gacha")
	FMelodiaPullResult PullOnce();

private:
	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWardrobeSubsystem> Wardrobe;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaTokenWalletSubsystem> Wallet;

	/** Runtime-only same-session dedupe (handoff gotcha #3). */
	UPROPERTY()
	TSet<FName> ConsumedGrantIds;
};