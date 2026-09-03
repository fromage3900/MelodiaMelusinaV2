#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaQuestManagerBase.h"
#include "MelodiaSaveGame.generated.h"

/** Narrow, provisional profile save: opening-flow phase + persistent party stats only.
 * Deliberately excludes any run/recipe/seed data, which belongs to the roguelike
 * run subsystem's own (separate) persistence layer. Safe to merge into a future,
 * broader profile-save system without touching that boundary. */
// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (second save authority). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API UMelodiaSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	FString SaveSlotName = TEXT("MelusinaSlot0");

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	int32 UserIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	FDateTime SavedAtUtc;

	/**
	 * Serialized save-schema version. This is the version stamped into the save record and
	 * asserted by MelodiaPersistenceTests.cpp. It is NOT the same counter as the
	 * "additive v2/v3/v4" field-generation labels used in the comments below:
	 * those describe which additive field batches were introduced, while this value is the
	 * on-disk schema generation. Do not bump this without a matching migration path and a
	 * corresponding update to FMelodiaSaveGameDefaultsTest.
	 *
	 * 3 (2026-08-22): currency balances are registry-keyed. The legacy fields below remain
	 * populated as a compatibility mirror so older builds degrade instead of reading zeroes.
	 */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	int32 SaveSystemVersion = 3;

	// --- Mirrors UMelodiaOpeningFlowSubsystem ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Opening")
	EMelodiaOpeningPhase OpeningPhase = EMelodiaOpeningPhase::NotStarted;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Opening")
	bool bHeartMelodyTokenGranted = false;

	// --- Mirrors UMelodiaBattleSession's Persistent Party block ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Party")
	float PersistentPartyHP = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Party")
	float PersistentPartyMaxHP = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Party")
	int32 PersistentSkillPoints = 3;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Party")
	int32 PersistentSkillPointMax = 5;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Party")
	float PersistentUltimateGauge = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Party")
	EMelodiaSpellElement PersistentEquippedKeyElement = EMelodiaSpellElement::Forte;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Party")
	bool bPersistentHarmonicKeyEquipped = false;

	// --- Explore-mode party swap state (UMelodiaPartySubsystem) ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Explore")
	int32 ActivePartyIndex = 0;

	/** Last explore transform per roster index. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Explore")
	TMap<int32, FTransform> PartyPawnTransforms;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Explore")
	FName CurrentMapName;

	// --- Monetization & durable progression (additive fields v2 -- safe defaults for v1 saves) ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Monetization")
	int64 Currency = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Monetization")
	int32 HeartMelodyTokens = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Monetization")
	int32 SwirlMelodyTokens = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Monetization")
	TArray<FName> OwnedContentPacks;

	/** Accessibility/perf motion-amplitude gate (Full/Soft/Chrome/Off) -- see Imports/UI/Specs/_MOTION_CHANNELS.md F-d.
	 * Every WBP_Sparkle instance reads this via UMelodiaSaveGameSubsystem::GetMotionTier(). */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Settings")
	EMelodiaMotionTier MotionTier = EMelodiaMotionTier::Full;

	// --- Quest state (additive v3 -- safe defaults for v1/v2 saves) ---

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Quest")
	TArray<FMelodiaQuestDef> SavedActiveQuests;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Quest")
	TArray<FName> SavedCompletedQuestIds;

	// --- Melody Token wallet (additive v4 -- safe defaults for v1/v2/v3 saves) ---
	// Mirrors GMM's TokenWallet (gmm/game/tokens.py), which is the canonical economy model:
	// shards keyed by ELEMENT (Forte/Tide/Gale/Stone/Radiant/Umbral/Arcane), plus mana,
	// golden tokens and a lifetime collected count.
	//
	// NOTE on the pre-existing Monetization block above: HeartMelodyTokens/SwirlMelodyTokens
	// are per-VARIANT ints owned by UMelodiaRoguelikeRunSubsystem for run-scoped purposes.
	// They are deliberately NOT removed or re-pointed here -- that would change an authority
	// that currently works. UMelodiaTokenWalletSubsystem performs a ONE-WAY migration of those
	// two legacy values on first load into the element-keyed wallet, then leaves them alone.

	/** Elemental shard balances keyed by element name. Empty on legacy saves. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	TMap<FName, int32> WalletShards;

	/** Registry-keyed integer balances for Shard and Premium currencies. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	TMap<FName, int32> WalletBalances;

	/** Registry-keyed float balances for Resource currencies. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	TMap<FName, float> WalletResources;

	/** Resource caps copied from the registry at capture time. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	TMap<FName, float> WalletResourceMax;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	float WalletManaCurrent = 50.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	float WalletManaMax = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	int32 WalletGoldenTokens = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	int32 WalletTotalCollected = 0;

	/**
	 * Grant IDs already consumed -- battle instance IDs and pickup IDs.
	 * This is what makes grants idempotent ACROSS a full process restart, not merely
	 * within a session: an in-memory-only guard passes the reopen-dialogue test and still
	 * double-pays after relaunch.
	 */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	TSet<FName> WalletConsumedGrantIds;

	/** Insertion order for trimming the consumed-grant ledger oldest-first. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	TArray<FName> WalletConsumedGrantOrder;

	/** UMelodiaCurrencyRegistry::RegistrySchemaVersion at capture time. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	int32 WalletRegistrySchemaVersion = 0;

	/** False on legacy saves; set true once the one-way legacy token migration has run. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save|Wallet")
	bool bWalletMigratedFromLegacyTokens = false;
};
