// Melody Token wallet — the single Unreal-side authority for the token stat economy.
//
// Mirrors GMM's TokenWallet (Content/Python/gmm/game/tokens.py), which owns the canonical
// model and arithmetic rules. There is no runtime GMM<->Unreal channel; this is a parallel
// implementation of the same contract, kept honest by matching test expectations.
//
// Why this exists: Kiro's pickup/HUD lane is blocked without a typed seam that can return an
// authoritative snapshot, accept/reject a transaction, publish one changed event, persist
// through the canonical save record, and reject duplicate grants. Building any of that inside
// a widget or pickup actor would create a second wallet, which is explicitly forbidden.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaTokenWalletSubsystem.generated.h"

class UMelodiaSaveGame;
class UMelodiaCurrencyRegistry;

/** Immutable read model handed to UI. UI renders this and never computes balances itself. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaWalletSnapshot
{
	GENERATED_BODY()

	/** Integer balances for every Shard and Premium currency, keyed by CurrencyId. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	TMap<FName, int32> Balances;

	/** Float balances for every Resource currency, keyed by CurrencyId. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	TMap<FName, float> Resources;

	/** Registry caps for Resource currencies, keyed by CurrencyId. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	TMap<FName, float> ResourceMax;

	/** Shard balances keyed by element: Forte, Tide, Gale, Stone, Radiant, Umbral, Arcane. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	TMap<FName, int32> Shards;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	float ManaCurrent = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	float ManaMax = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	int32 GoldenTokens = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	int32 TotalCollected = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaWalletChanged, const FMelodiaWalletSnapshot&, Snapshot);

/**
 * Presentation contract:
 *   gameplay/pickup -> this subsystem -> OnWalletChanged -> UI
 *
 * UI must never increment optimistically, infer success from an animation, or hold its own
 * balances. Every mutator returns whether it was accepted; a rejected call fires no event and
 * changes no state.
 */
UCLASS()
class MELODIACORE_API UMelodiaTokenWalletSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Canonical element list, matching GMM's TokenWallet.shards default keys. */
	static const TArray<FName>& GetElementNames();

	UFUNCTION(BlueprintPure, Category="Melodia|Wallet", meta=(WorldContext="WorldContextObject"))
	static UMelodiaTokenWalletSubsystem* Get(const UObject* WorldContextObject);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Authoritative read model. Safe to call every frame; it is a copy. */
	UFUNCTION(BlueprintPure, Category="Melodia|Wallet")
	FMelodiaWalletSnapshot GetSnapshot() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Wallet")
	int32 GetShards(FName Element) const;

	/** Generic integer balance read for Shard and Premium currencies. */
	UFUNCTION(BlueprintPure, Category="Melodia|Wallet")
	float GetBalance(FName CurrencyId) const;

	/** Generic Resource read. Returns zero for unknown or non-Resource currencies. */
	UFUNCTION(BlueprintPure, Category="Melodia|Wallet")
	float GetResource(FName CurrencyId) const;

	/** Generic Resource cap read. Returns zero for unknown or non-Resource currencies. */
	UFUNCTION(BlueprintPure, Category="Melodia|Wallet")
	float GetResourceMax(FName CurrencyId) const;

	/** Registry-driven grant. Integer lanes require a whole-number Amount. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TryGrantCurrency(FName CurrencyId, float Amount, FName GrantId);

	/** Registry-driven spend. A rejected spend never mutates state or broadcasts. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TrySpendCurrency(FName CurrencyId, float Amount);

	/** Refund only currencies whose registry row explicitly permits it. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TryRefundCurrency(FName CurrencyId, float Amount);

	/** Atomic affordability check for integer currency costs. */
	UFUNCTION(BlueprintPure, Category="Melodia|Wallet")
	bool CanAfford(const TMap<FName, int32>& Cost) const;

	/** Atomic multi-currency spend with exactly one change event on success. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TrySpendMany(const TMap<FName, int32>& Cost);

	/**
	 * Grant shards for a collection or reward.
	 *
	 * @param GrantId  Stable identity for this grant — a battle instance ID or a placed
	 *                 pickup's ID. Pass NAME_None only for grants that are genuinely
	 *                 repeatable. A non-None GrantId already consumed is REJECTED, and that
	 *                 rejection survives a full process restart because consumed IDs persist.
	 * @return true if the grant was applied.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TryGrantShards(FName Element, int32 Amount, FName GrantId);

	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TrySpendShards(FName Element, int32 Amount);

	/** Adds mana, clamped to ManaMax. Returns false only if Amount <= 0. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TryAddMana(float Amount);

	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TrySpendMana(float Amount);

	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TryGrantGolden(int32 Amount, FName GrantId);

	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TrySpendGolden(int32 Amount);

	/** Refund a previously accepted Golden spend after a downstream operation fails. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	bool TryRefundGolden(int32 Amount);

	/** True if this grant has already been consumed (and therefore would be rejected). */
	UFUNCTION(BlueprintPure, Category="Melodia|Wallet")
	bool IsGrantConsumed(FName GrantId) const;

	/** Fires exactly once per ACCEPTED transaction. Never fires on a rejection. */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Wallet")
	FMelodiaWalletChanged OnWalletChanged;

	// --- Save integration. Called by UMelodiaSaveGameSubsystem; not for gameplay use. ---

	/** Write wallet state into the save record. */
	void CaptureToSave(UMelodiaSaveGame* Save) const;

	/**
	 * Restore wallet state from the save record.
	 * Performs a ONE-WAY migration of the legacy per-variant HeartMelodyTokens /
	 * SwirlMelodyTokens ints into element-keyed shards the first time a pre-v4 save is
	 * loaded. The "already migrated" flag is held on the wallet and written back out by
	 * CaptureToSave, which keeps this side const-correct — the save subsystem hands out a
	 * const record on load, and const-casting it would be lying about ownership.
	 */
	void RestoreFromSave(const UMelodiaSaveGame* Save);

public:
	/**
	 * Hard cap on the persisted consumed-grant ledger. The ledger only exists to make grants
	 * idempotent across restarts; without a bound it grows for the life of a save and is paid
	 * for on every capture, restore, and AddUnique scan.
	 */
	static constexpr int32 MaxConsumedGrantEntries = 4096;

private:
	void EnsureElementKeys();
	void SyncLegacyViews();
	const UMelodiaCurrencyRegistry* GetRegistry() const;
	void BroadcastChanged();

	/** Record a consumed grant id and trim the ledger oldest-first to MaxConsumedGrantEntries. */
	void RecordConsumedGrant(FName GrantId);

	/**
	 * Re-read Resource caps from the registry. Saves store the caps that were live at capture
	 * time, so a registry cap change would otherwise never reach an existing save.
	 */
	void RefreshResourceCapsFromRegistry();

	UPROPERTY()
	TMap<FName, int32> Shards;

	/** Authoritative integer lane for every Shard and Premium currency. */
	UPROPERTY()
	TMap<FName, int32> Balances;

	/** Authoritative float lane for every Resource currency. */
	UPROPERTY()
	TMap<FName, float> Resources;

	/** Authoritative Resource caps, copied from the registry at initialization/restore. */
	UPROPERTY()
	TMap<FName, float> ResourceMax;

	UPROPERTY()
	float ManaCurrent = 50.0f;

	UPROPERTY()
	float ManaMax = 100.0f;

	UPROPERTY()
	int32 GoldenTokens = 0;

	UPROPERTY()
	int32 TotalCollected = 0;

	UPROPERTY()
	TSet<FName> ConsumedGrantIds;

	/** Stable insertion order for save-ledger trimming. */
	UPROPERTY()
	TArray<FName> ConsumedGrantOrder;

	/** Mirrors UMelodiaSaveGame::bWalletMigratedFromLegacyTokens; written back on capture. */
	UPROPERTY()
	bool bMigratedFromLegacy = false;
};
