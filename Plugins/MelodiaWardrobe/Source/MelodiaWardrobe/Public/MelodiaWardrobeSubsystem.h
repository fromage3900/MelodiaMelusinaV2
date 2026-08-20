// MelodiaWardrobe — wardrobe state authority (Decision 043).
//
// GameInstanceSubsystem that owns the owned-set, the equipped-map, save/load via
// FMelodiaNarrativeRecord (additive v3 fields, no schema break), and the purchase
// path. It reads and writes through the canonical narrative record rather than
// holding its own copy (mirrors the Persona-lite social-stat pattern, Decision 013).

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaCosmeticTypes.h"
#include "MelodiaTraversalCapabilityProvider.h"
#include "MelodiaWardrobeSubsystem.generated.h"

class UMelodiaNarrativeSubsystem;
class UMelodiaTokenWalletSubsystem;
class UMelodiaCosmeticCatalog;
class UMelodiaCosmeticDefinition;
class UMelodiaTraversalCapabilityRegistry;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaWardrobeChanged, EMelodiaWardrobeSlot, Slot, FName, CosmeticId);

UCLASS()
class MELODIAWARDROBE_API UMelodiaWardrobeSubsystem final
	: public UGameInstanceSubsystem
	, public IMelodiaTraversalCapabilityProvider
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe", meta=(WorldContext="WorldContextObject"))
	static UMelodiaWardrobeSubsystem* Get(const UObject* WorldContextObject);

	/** Immutable read model for UI. */
	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe")
	FMelodiaWardrobeState GetState() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe")
	bool IsOwned(FName CosmeticId) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe")
	FName GetEquipped(EMelodiaWardrobeSlot Slot) const;

	/**
	 * Registers a cosmetic as owned.
	 *
	 * CATALOG-FIRST AND FAIL-CLOSED: the id must resolve to a catalog record with an
	 * authored mesh before anything is written. OwnedCosmeticIds lives in the canonical
	 * narrative record, so an unvalidated grant writes a permanent unresolvable id into
	 * the save -- the mesh lookup then returns null forever and the slot silently stays
	 * empty. Validation happens before the record is touched, never after.
	 *
	 * IDEMPOTENCY, precisely:
	 *  - Across a process restart the guarantee is OWNERSHIP. OwnedCosmeticIds is a
	 *    persisted set, so re-granting an owned cosmetic is a no-op that returns true
	 *    and does NOT re-broadcast.
	 *  - Within a session GrantId adds a second, faster guard. ConsumedGrantIds is
	 *    runtime-only and empty after a restart, so GrantId alone is NOT a durable
	 *    receipt. Callers needing durable once-only semantics must key off ownership
	 *    or the wallet's persisted consumed-grant set.
	 *
	 * @return true when the cosmetic is owned on return (newly granted OR already owned).
	 *         false only when the grant was refused: unknown id, missing catalog,
	 *         unauthored mesh, missing mesh asset, or a GrantId already consumed
	 *         this session.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	bool GrantCosmetic(FName CosmeticId, FName GrantId = NAME_None);

	/**
	 * Equips an owned cosmetic into its catalog slot.
	 * Returns false when not owned, or when the id does not resolve to a catalog
	 * record with an authored mesh -- an equip that cannot present anything must not
	 * write an equipped-slot entry into the save record.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	bool EquipCosmetic(FName CosmeticId);

	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	bool UnequipSlot(EMelodiaWardrobeSlot Slot);

	/** Purchase path: spends Golden through the wallet, then grants. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	bool PurchaseCosmetic(FName CosmeticId, int32 GoldenPrice);

	/**
	 * Purchase priced in element shards, which is how cosmetics are actually authored.
	 *
	 * Cosmetic drafts price in token art variants (`{"heart": 5, "swirl": 2}`), which
	 * resolve to Forte/Arcane shards in the one Melody Token wallet. `PurchaseCosmetic`
	 * above takes a flat Golden price and cannot express that at all.
	 *
	 * Atomic in the way that matters: every shard cost is checked BEFORE anything is
	 * spent, and if a later spend fails the earlier ones are refunded. A partial spend
	 * would take the player's shards and hand back nothing.
	 *
	 * @param ElementCost Element name -> amount, as produced by
	 *                    UMelodiaTokenCatalog::ResolveCost. Pass resolved elements, not
	 *                    art-variant keys.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	bool PurchaseCosmeticWithShards(FName CosmeticId, const TMap<FName, int32>& ElementCost);

	/** Resolves the cosmetic's mesh through the catalog. */
	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe")
	USkeletalMesh* GetCosmeticMesh(FName CosmeticId) const;

	/** Resolves the slot a cosmetic belongs to (from its catalog record). */
	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe")
	EMelodiaWardrobeSlot GetSlotForCosmetic(FName CosmeticId) const;

	/** Fires on every accepted equip/unequip/grant. UI listens here. */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Wardrobe")
	FMelodiaWardrobeChanged OnWardrobeChanged;

	// --- Resonant Forms: read-only gating queries ---------------------------
	// These ANSWER, they do not decide. UMelodiaTraversalComponent stays the
	// traversal authority and UMelodiaNarrativeSubsystem stays the flag authority;
	// this is the lookup those authorities consult. Nothing here writes state.

	/**
	 * True when every RequiredFlagId on the form is set in the canonical narrative
	 * record. A form with no requirements is ungated and always unlocked.
	 * An unknown FormId is NOT unlocked -- fail closed, so a typo'd id withholds an
	 * ability rather than silently granting one.
	 */
	UFUNCTION(BlueprintPure, Category="Melodia|Form")
	bool IsFormUnlocked(FName FormId) const;

	/** The form id an equipped cosmetic presents, or None. */
	UFUNCTION(BlueprintPure, Category="Melodia|Form")
	FName GetEquippedFormId(EMelodiaWardrobeSlot Slot) const;

	/**
	 * Capabilities currently active: union across every equipped cosmetic whose
	 * form is unlocked, minus anything the form restricts in ContextId.
	 *
	 * Pass NAME_None for ContextId to ask "unrestricted". Passing a context that
	 * appears in a form's RestrictedContextIds removes that form's contribution --
	 * a boss arena suppressing glide, for example.
	 */
	UFUNCTION(BlueprintPure, Category="Melodia|Form")
	TArray<EMelodiaFormCapability> GetActiveCapabilities(FName ContextId) const;

	/** Convenience predicate over GetActiveCapabilities. */
	UFUNCTION(BlueprintPure, Category="Melodia|Form")
	bool IsCapabilityActive(EMelodiaFormCapability Capability, FName ContextId) const;

	/** Native module-neutral adapter consumed by UMelodiaTraversalComponent. */
	virtual bool QueryTraversalCapability(
		FName CapabilityId,
		FName ContextId,
		FName& OutBlockReason) const override;

private:
	/**
	 * The catalog, resolved once and held.
	 *
	 * Previously every call ran StaticLoadObject and kept no reference, so the asset
	 * was unrooted and could be collected between calls -- and GetActiveCapabilities()
	 * sits on the traversal query path, which asks per request.
	 */
	const UMelodiaCosmeticCatalog* GetCatalog() const;
	const UMelodiaCosmeticCatalog* ResolveCatalog();

	/**
	 * Catalog record for CosmeticId, or nullptr with OutReason set to a short
	 * machine-greppable token: no_catalog, unknown_id, unauthored_mesh, or
	 * missing_mesh.
	 * The single validation seam for grant and equip, so both fail the same way.
	 */
	const FMelodiaCosmeticRecord* FindGrantableRecord(FName CosmeticId, FName& OutReason) const;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaNarrativeSubsystem> Narrative;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaTokenWalletSubsystem> Wallet;

	/**
	 * Strong ref: nothing else roots the catalog DataAsset.
	 * Non-const because UHT cannot reflect TObjectPtr<const T>; the accessors above
	 * hand out const pointers, so callers still cannot mutate the catalog.
	 */
	UPROPERTY(Transient)
	TObjectPtr<UMelodiaCosmeticCatalog> CachedCatalog;

	/** Keeps the missing-catalog error to one line per session instead of per query. */
	bool bLoggedMissingCatalog = false;

	TWeakObjectPtr<UMelodiaTraversalCapabilityRegistry> CapabilityRegistry;

	/**
	 * Runtime-only same-session dedupe. NOT a durable receipt -- this is empty after a
	 * restart by design. Persistent once-only lives in OwnedCosmeticIds; see
	 * GrantCosmetic's contract.
	 */
	UPROPERTY()
	TSet<FName> ConsumedGrantIds;
};
