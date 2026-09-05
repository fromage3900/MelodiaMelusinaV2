// MelodiaWardrobe — universal outfit slot vocabulary and cosmetic records.
//
// The slot enum itself (EMelodiaWardrobeSlot) lives in MelodiaNarrativeTypes.h
// (BS_GodFile/MelodiaIntegration) because the canonical save record keys its
// equipped map by it (Decision 043); this header adds the cosmetic-facing
// records on top of that shared vocabulary.

#pragma once

#include "CoreMinimal.h"
#include "MelodiaNarrativeTypes.h" // EMelodiaWardrobeSlot (shared with the save record)
#include "MelodiaSpellTypes.h"     // EMelodiaSpellElement (shared with skills/enemies/keys)
#include "MelodiaCosmeticTypes.generated.h"

class USkeletalMesh;

UENUM(BlueprintType)
enum class EMelodiaCosmeticRarity : uint8
{
	Common,
	Uncommon,
	Rare,
	Epic,
	Legendary,
	Grandmaster
};

/**
 * A traversal capability a Resonant Form may unlock.
 *
 * These are the capabilities UMelodiaTraversalComponent ACTUALLY implements today
 * (glide with stamina, dash, swim) -- not aspirational ones. Adding a value here
 * without a matching implementation creates a form that promises something the
 * traversal authority cannot deliver.
 */
UENUM(BlueprintType)
enum class EMelodiaFormCapability : uint8
{
	Glide,
	Dash,
	Swim
};

/**
 * A Resonant Form -- Melodia's ability-outfit identity, kept SEPARATE from the
 * cosmetic that presents it.
 *
 * Why the separation: an ability must not be hardcoded to one mesh. Several
 * cosmetics (seasonal variants, recolours, a Grandmaster version) can all carry
 * the same FormId, so the gameplay gate reads the form and the wardrobe reads the
 * mesh. Binding the capability to the cosmetic directly would mean every visual
 * variant needed its own gameplay wiring.
 *
 * This struct DECLARES; it does not grant. UMelodiaTraversalComponent remains the
 * traversal authority and UMelodiaNarrativeSubsystem remains the flag authority --
 * a form states which capabilities it unlocks and which flags gate it, and those
 * authorities decide. Nothing here may become a second authority.
 */
USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaResonantForm
{
	GENERATED_BODY()

	/** Stable identity. Cosmetics reference this, never the other way round. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Form")
	FName FormId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Form")
	FText DisplayName;

	/**
	 * Narrative flags that must ALL be true before this form is available.
	 * Resolved against FMelodiaNarrativeRecord::Flags, which is the single
	 * persistence seam -- the form does not track its own unlock state.
	 * Empty means ungated.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Form|Gating")
	TArray<FName> RequiredFlagIds;

	/**
	 * Capabilities this form unlocks. A SOFT gate: the world is authored so these
	 * open new routes rather than blocking a critical path, so a player without the
	 * form is delayed, never stuck.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Form|Gating")
	TArray<EMelodiaFormCapability> GrantedCapabilities;

	/**
	 * Contexts where this form's capabilities are suppressed -- boss arenas,
	 * authored set pieces, interiors. Named contexts rather than a bool so a
	 * designer can add a restriction without a code change.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Form|Gating")
	TArray<FName> RestrictedContextIds;
};

/**
 * Body-region clipping contract for one garment (Nikki-translation §6, precompute
 * tier: Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md).
 *
 * A garment declares which body regions it covers. At equip time the wardrobe
 * resolves the union across the equipped set and collapses those regions on the
 * body mesh via AUTHORED region-hide morph targets (the body SK has ~4 material
 * sections, so section visibility is too coarse for region hiding).
 *
 * Contract:
 *  - Region ids MUST equal morph-target names on the body SK (mel_body_hide_*).
 *  - The morph for a declared region may not exist yet (authoring lag). That is a
 *    WARN-ONCE and no visual collapse -- never a crash, never a guessed section
 *    index. The declaration is inert until the body mesh grows the morph.
 *  - This struct DECLARES coverage; the wardrobe APPLIES it at equip time. Nothing
 *    here stores runtime state and nothing caches the resolved set: the equipped
 *    map on the narrative record stays the only durable state (Decision 043).
 *  - Authored by Tools/wardrobe_intersection_audit.py from real garment/body
 *    geometry penetration samples, not by hand.
 */
USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaCosmeticCompatibility
{
	GENERATED_BODY()

	/**
	 * Body regions this garment covers and the body should collapse beneath it.
	 * Empty = decorative from the clipping perspective (the default and the
	 * correct value for accessories, hair charms, and trails).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe|Clipping")
	TArray<FName> HiddenBodyRegionIds;

	/**
	 * Optional explicit exceptions: combos (other cosmetic ids) this garment is
	 * KNOWN to clip against regardless of region coverage. The audit tool emits
	 * these when two authored garments interpenetrate in bind pose. v1 is
	 * advisory data only -- no runtime consumer reads it yet, and it must never
	 * gate an equip on its own (a forced refusal here would strand a save).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe|Clipping")
	TArray<FName> KnownClipPairCosmeticIds;
};

/**
 * Grade of one garment against one style axis. A stable scale, not a taxonomy --
 * safe as an enum because adding a grade is a balance change, not content.
 */
UENUM(BlueprintType)
enum class EMelodiaStyleGrade : uint8
{
	D,
	C,
	B,
	A,
	S,
	SS,
	SSS
};

/**
 * How well one garment expresses one harmonic element.
 *
 * The axis IS EMelodiaSpellElement -- the same seven elements skills, enemies and
 * equippable keys already use (MelodiaSpellTypes.h). This was briefly an FName on
 * the theory that the axis set was content and would grow; that was wrong. The set
 * is fixed, already typed, and already load-bearing in combat, so an FName here
 * created a THIRD copy of one vocabulary (the enum, the generator daemon's
 * hardcoded list, and the catalog's declared names) with nothing keeping them
 * agreeing.
 *
 * Reusing the combat enum also means an outfit's styling and the weakness system
 * speak the same language -- FMelodiaElementKeyDefinition already matches an
 * element for bonus damage, so a Tide-strong outfit and a Tide key are relatable
 * rather than coincidentally similarly named.
 */
USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaStyleScore
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Style")
	EMelodiaSpellElement Element = EMelodiaSpellElement::Forte;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Style")
	EMelodiaStyleGrade Grade = EMelodiaStyleGrade::D;
};

/** One cosmetic record: identity, slot, rarity, optional pack provenance, and mesh. */
USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaCosmeticRecord
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	FName CosmeticId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	EMelodiaWardrobeSlot Slot = EMelodiaWardrobeSlot::Body;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	EMelodiaCosmeticRarity Rarity = EMelodiaCosmeticRarity::Common;

	/**
	 * Optional content-pack provenance from source drafts. This is catalog metadata
	 * only: collection/entitlement ownership remains a separate future authority.
	 * Missing means the source did not assign a pack; it must never be inferred.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	FName ContentPackId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	TSoftObjectPtr<USkeletalMesh> Mesh;

	/**
	 * Optional Resonant Form this cosmetic presents. NAME_None = purely decorative,
	 * which most cosmetics should be.
	 *
	 * Many cosmetics may share one FormId -- that is the point. The gameplay gate
	 * reads the form; the wardrobe reads the mesh. Do NOT add capability fields to
	 * this record: a cosmetic describes appearance, a form describes ability, and
	 * collapsing them is how you end up unable to ship a recolour.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	FName ResonantFormId;

	/** Narrative reward that grants this cosmetic. Empty means no automatic grant. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe|Unlock")
	FName UnlockRewardId;

	/** Equip immediately when UnlockRewardId is received, using the owning pawn's
	 * wardrobe component so presentation and canonical state change together. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe|Unlock")
	bool bAutoEquipOnUnlock = false;

	/**
	 * This garment's grade on each style axis it expresses. Omit an axis entirely
	 * rather than scoring it D -- absent means "does not express", which reads
	 * differently from "expresses badly" when a designer scans the asset.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Style")
	TArray<FMelodiaStyleScore> StyleScores;

	/**
	 * Body-region clipping contract (see FMelodiaCosmeticCompatibility). Empty by
	 * default: most cosmetics hide nothing, and an absent declaration must never
	 * be read as "collapse everything beneath this garment".
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe|Clipping")
	FMelodiaCosmeticCompatibility Compatibility;
};

/** Immutable read model handed to UI. UI renders this and never computes state itself. */
USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaWardrobeState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wardrobe")
	TSet<FName> OwnedCosmeticIds;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wardrobe")
	TMap<EMelodiaWardrobeSlot, FName> EquippedCosmeticIds;
};
