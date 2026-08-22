// Melodia currency registry — the editable authority for WHICH currencies exist.
//
// The wallet (UMelodiaTokenWalletSubsystem) owns balances and transaction rules. The token
// catalog (UMelodiaTokenCatalog) owns what a pickup LOOKS like and which currency it grants.
// This registry is the third and outermost layer: the list of currencies themselves.
//
// WHY THIS IS DATA AND NOT AN ENUM
//
// Adding a currency used to mean editing EMelodiaSpellElement, the GMelodiaElements array,
// and the wallet's per-currency API (TryGrantGolden, TryAddMana, ...) — three hardcoded lists
// that had to move together, plus a recompile, plus a save-schema risk. A registry row makes
// all three data. See Decision 054.
//
// WHAT IS STILL C++
//
// EMelodiaCurrencyKind. There are exactly three storage lanes with genuinely different
// arithmetic — an uncapped integer with GrantId idempotency, a refundable integer, and a
// float clamped to a maximum — and those rules are code, not data. A row picks a lane and
// inherits its whole contract. That is the difference between "new currencies are free" and
// "new currencies need a programmer".
//
// AUTHORING (Decision 055): this DataAsset is CANONICAL. Edit it in the editor, then run
// Content/Python/export_melodia_currency_registry.py to refresh specs/economy/*.v1.json,
// which Python, Tools/wardrobe_draft_lint.py, CI and the MCP tools all read. The
// melodia_economy_registry_export_fresh CI gate fails if you skip that step.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaCurrencyRegistry.generated.h"

class UMaterialInterface;
class UTexture2D;

/**
 * Which storage lane a currency lives in, and therefore which arithmetic it obeys.
 *
 * Append only. The value is not serialized into saves (balances are FName-keyed), but it IS
 * serialized into the registry asset, so reordering would silently repoint existing rows.
 */
UENUM(BlueprintType)
enum class EMelodiaCurrencyKind : uint8
{
	/** Integer, uncapped, grants are GrantId-idempotent. The seven elemental shards. */
	Shard UMETA(DisplayName = "Shard"),

	/** Integer, uncapped, GrantId-idempotent, and refundable after a failed purchase. Golden. */
	Premium UMETA(DisplayName = "Premium"),

	/** Float, clamped to MaxValue, not idempotent (it regenerates). Mana. */
	Resource UMETA(DisplayName = "Resource")
};

/** One currency. Everything a designer can change about it without touching C++. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaCurrencyDefinition
{
	GENERATED_BODY()

	/** Wallet key. This is what balances, costs and save records are keyed by. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	FName CurrencyId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	EMelodiaCurrencyKind Kind = EMelodiaCurrencyKind::Shard;

	/** Balance a fresh wallet starts with. Mana starts at 50; shards start at 0. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency", meta = (ClampMin = "0.0"))
	float DefaultValue = 0.0f;

	/** Upper bound for Resource currencies. Ignored (and must stay 0) for Shard and Premium. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency", meta = (ClampMin = "0.0"))
	float MaxValue = 0.0f;

	/** Whether TryRefund is permitted. Only Golden sets this today. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	bool bRefundable = false;

	/** Whether grants of this currency advance the lifetime TotalCollected counter. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	bool bCountsTowardTotalCollected = true;

	/** HUD row order. The universal wallet widget builds its rows in this order. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	int32 SortOrder = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency|Presentation")
	FLinearColor AccentColor = FLinearColor::White;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency|Presentation")
	TSoftObjectPtr<UTexture2D> Icon;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency|Presentation")
	TSoftObjectPtr<UMaterialInterface> Material;

	/**
	 * Compatibility bridge for the pre-registry element enum, used by UMelodiaTokenCatalog
	 * (whose rows still carry an EMelodiaSpellElement) and by the legacy wallet shims.
	 *
	 * New currencies leave this false. A currency invented after the registry landed has no
	 * enum value to map to, and that is the entire point.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency|Compatibility")
	bool bHasLegacyElement = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency|Compatibility",
		meta = (EditCondition = "bHasLegacyElement"))
	EMelodiaSpellElement LegacyElement = EMelodiaSpellElement::Forte;
};

/**
 * Every currency in the game. One asset at /Game/Melodia/Data/DA_MelodiaCurrencyRegistry.
 *
 * Get() falls back to a hardcoded nine-row seed when the asset is missing, so a cook, a
 * headless automation run, or a fresh clone can never hard-fail on a wallet that has no
 * currencies. The fallback is a safety net, not the authority — if you see the "using
 * fallback seed" warning in a normal editor session, the asset is missing and should be
 * restored with Content/Python/author_melodia_currency_registry.py.
 */
UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaCurrencyRegistry : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	TArray<FMelodiaCurrencyDefinition> Currencies;

	/** Bumped when the row SHAPE changes. Persisted into saves so a migration can branch on it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Currency")
	int32 RegistrySchemaVersion = 1;

	/** Canonical asset path. */
	static const TCHAR* GetRegistryAssetPath();

	/**
	 * The registry every consumer should use. Never returns null.
	 * WorldContextObject is accepted for Blueprint ergonomics and is not currently required.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Currency", meta = (WorldContext = "WorldContextObject"))
	static const UMelodiaCurrencyRegistry* Get(const UObject* WorldContextObject);

	/** The nine-row seed: seven elements, Golden, Mana. Also what author_* bootstraps from. */
	static const UMelodiaCurrencyRegistry* GetFallbackSeed();

	UFUNCTION(BlueprintPure, Category = "Melodia|Currency")
	bool IsKnownCurrency(FName CurrencyId) const;

	const FMelodiaCurrencyDefinition* Find(FName CurrencyId) const;

	/** Blueprint-facing wrapper. bFound is false when the currency is unknown. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Currency")
	FMelodiaCurrencyDefinition GetCurrency(FName CurrencyId, bool& bFound) const;

	/** Every currency of one kind, in SortOrder. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Currency")
	TArray<FName> GetCurrencyIds(EMelodiaCurrencyKind Kind) const;

	/** Every currency, in SortOrder. This is what the universal wallet widget iterates. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Currency")
	TArray<FMelodiaCurrencyDefinition> GetSortedCurrencies() const;

	/**
	 * Compatibility map from the legacy element enum to a currency id.
	 * Returns NAME_None when no row claims that element.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Currency")
	FName CurrencyIdForElement(EMelodiaSpellElement Element) const;

	/** Duplicate CurrencyIds, which make Find ambiguous. Empty is healthy. */
	TArray<FName> FindDuplicateCurrencyIds() const;

	virtual void PostLoad() override;

private:
	/** Shared, lazily built fallback. Rooted so GC cannot collect it out from under callers. */
	static UMelodiaCurrencyRegistry* FallbackSeedInstance;
};
