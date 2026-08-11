#pragma once

#include "CoreMinimal.h"
#include "MelodiaWaterGameplayTypes.h"
#include "MelodiaNarrativeTypes.generated.h"

UENUM(BlueprintType)
enum class EMelodiaBattleResult : uint8
{
	Victory,
	Defeat,
	Fled,
	Rejected,
	Unavailable
};

UENUM(BlueprintType)
enum class EMelodiaIntentFailure : uint8
{
	None,
	UnknownIntent,
	UnknownIdentifier,
	Busy,
	Duplicate,
	MissingRuntime,
	IncompatibleSave
};

/**
 * Universal outfit slot vocabulary shared with the MelodiaWardrobe plugin
 * (Decision 043, 2026-08-07). Lives in MelodiaIntegration because the save
 * record keys the equipped map by it; the wardrobe plugin includes this
 * header to consume the enum. Values are stable identifiers; do not renumber
 * or rename without a v3 -> v4 migration case in UMelodiaNarrativeSubsystem.
 *
 * Named EMelodiaWardrobeSlot rather than EMelodiaOutfitSlot to avoid colliding
 * with the same-named enum in the quarantined MelodiaCore plugin (UMHT rejects
 * duplicate reflected enum names project-wide; the quarantined module is still
 * compiled, just runtime-guarded). When Decision 3.1 (move MelodiaCore's 65
 * dead headers to _Reference) eventually lands, this can be renamed.
 */
UENUM(BlueprintType)
enum class EMelodiaWardrobeSlot : uint8
{
	Body,
	Hat,
	Gloves,
	Shawl,
	Trail,
	HairCharm
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaNarrativeRecord
{
	GENERATED_BODY()

	/**
	 * Schema version.
	 *
	 * 1 -> 2 (2026-07-30): added SocialStats, BondRanks, PhaseIndex, SpawnContext.
	 * 2 -> 3 (2026-08-07, Decision 043): added OwnedCosmeticIds, EquippedCosmeticIds,
	 *                                    LastPullUnixSeconds for the MelodiaWardrobe
	 *                                    universal outfit collection. Defaults are
	 *                                    empty, so the migration is a no-op.
	 * 3 -> 4 (2026-08-10): added the logical PCG/water gameplay snapshot. Raw
	 *                      physics velocity and arbitrary transforms are never
	 *                      serialized; buoyant bodies re-settle on load.
	 *
	 * Bumping this requires a matching case in
	 * UMelodiaNarrativeSubsystem::MigrateRecord.  Never bump it without one:
	 * RestoreNarrativeRecord resets any record it cannot migrate.
	 */
	static constexpr int32 CurrentVersion = 4;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	int32 Version = CurrentVersion;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TMap<FName, bool> Flags;

	/**
	 * Persistent, namespaced Quill state.  Only variables beginning melodia_
	 * enter this record; Quill's temporary UI/local values remain runtime-only.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TMap<FName, FText> QuillVariables;

	/**
	 * Quill's own serialized variables/history payload. This is captured through
	 * its public serializer, embedded in the canonical JRPG save record, and
	 * restored before any new VN scene is started. It is not an independent
	 * save file or a second persistence authority.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TArray<uint8> QuillPersistentData;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	FName ScriptCheckpoint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TArray<FName> ConsumedIntentIds;

	/** Active Persona-lite quest IDs; completion remains represented by typed narrative flags. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TArray<FName> ActiveQuestIds;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TArray<FName> ConsumedRewardIds;

	/**
	 * Persona-lite social stats.  The canonical store -- UMelodiaPersonaSubsystem
	 * reads and writes through here rather than holding its own copy, so stats
	 * survive a reload.  Added in version 2.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TMap<FName, int32> SocialStats;

	/**
	 * Confidant / social-link ranks, keyed by bond ID.  Reserved in version 2:
	 * nothing writes it yet, but a rank axis is impossible to retrofit into a
	 * shipped save schema, so the field exists from the start.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TMap<FName, int32> BondRanks;

	/**
	 * Monotonic story-phase counter.  Reserved in version 2.  Even a game with
	 * no calendar needs some way to express "this happened after that"; four
	 * bytes now avoids a schema migration later.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	int32 PhaseIndex = 0;

	/**
	 * Destination map ID -> authored spawn tag, so travel can return the player
	 * to a defined location.  Required by the Orrery travel adapter described in
	 * Docs/CORE_QOL_AUDIT_2026-07-29.md.  Reserved in version 2.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative")
	TMap<FName, FName> SpawnContext;

	// --- Wardrobe (additive v3 -- safe defaults for v1/v2 saves, Decision 043) ---
	//
	// Owned/equipped cosmetic set for the MelodiaWardrobe plugin. Lives on the
	// canonical narrative record so the wardrobe survives the same save/load
	// round-trip as quests and social stats; the wardrobe subsystem reads and
	// writes through here rather than holding its own copy, mirroring the
	// Persona-lite social-stat pattern (Decision 013).
	//
	// The wardrobe is a presentation/collection axis; it does not gate any
	// gameplay (foundation closeout §2.2 "soft gates" stay deferred). All
	// three fields default to empty/zero, so a v2 save loaded into a v3 build
	// trivially upgrades with nothing to migrate.

	/** Every cosmetic the player has ever acquired (granted, pulled, or purchased). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative|Wardrobe")
	TSet<FName> OwnedCosmeticIds;

	/** One cosmetic per slot, at most. Equipping writes here; the wardrobe component mirrors the visual state. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative|Wardrobe")
	TMap<EMelodiaWardrobeSlot, FName> EquippedCosmeticIds;

	/** Monotonic timestamp of the last gacha pull. Optional, reserved for future pity-counter work. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative|Wardrobe")
	int32 LastPullUnixSeconds = 0;

	/** Logical water/platform state; the water gameplay subsystem remains the runtime authority. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Narrative|Water")
	FMelodiaWaterGameplaySaveData WaterGameplayState;
};
