// MelodiaWardrobe — cosmetic DataAsset definition + global catalog.
//
// One UMelodiaCosmeticDefinition wraps one Cos_<X>_<Y>.json draft; the catalog
// DataAsset is the global registry (first pass: 1 entry, Cos_Dress_Melusina).

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaCosmeticTypes.h"
#include "MelodiaCosmeticDefinition.generated.h"

/**
 * One cosmetic: wraps a Cos_<X>_<Y>.json draft. PostLoad validates the draft
 * JSON when it is available so a broken draft surfaces in the editor, not in PIE.
 */
UCLASS(BlueprintType)
class MELODIAWARDROBE_API UMelodiaCosmeticDefinition : public UDataAsset
{
	GENERATED_BODY()

public:
	/** The cosmetic's identity, slot, rarity, and mesh. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	FMelodiaCosmeticRecord Record;

	/** Relative path of the source draft JSON under Content/ or Imports/. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	FString SourceDraftPath;

	/** True when PostLoad validation succeeded. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wardrobe")
	bool bValid = false;

	virtual void PostLoad() override;
};

/** Global registry of every cosmetic in the collection. */
UCLASS(BlueprintType)
class MELODIAWARDROBE_API UMelodiaCosmeticCatalog : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Wardrobe")
	TArray<FMelodiaCosmeticRecord> Cosmetics;

	/**
	 * Resonant Forms, authored alongside the cosmetics that present them.
	 * Several cosmetics may reference one form; a form referenced by none is a
	 * valid authoring state (the ability exists before its outfit is modelled).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Form")
	TArray<FMelodiaResonantForm> ResonantForms;

	// NOTE: there is deliberately no StyleAxisIds array here any more. The axis set
	// is EMelodiaSpellElement, so the enum IS the declaration and the compiler is
	// the validator -- a declared-names array would be a second copy of a fixed
	// vocabulary that could drift out of agreement with it.

	/**
	 * Per-slot contribution weight for styling scores.
	 *
	 * Silhouette-defining slots should outweigh accessories, or every challenge
	 * degrades into "equip the maximum number of items" rather than a composition
	 * decision. A slot absent from this map contributes at weight 1.0.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Style")
	TMap<EMelodiaWardrobeSlot, float> SlotStyleWeights;

	virtual void PostLoad() override;

	/** Lookup by id. Returns nullptr when absent. */
	const FMelodiaCosmeticRecord* FindById(FName CosmeticId) const;

	/** Form lookup by id. Returns nullptr when absent. */
	const FMelodiaResonantForm* FindFormById(FName FormId) const;

	/**
	 * Every cosmetic whose ResonantFormId names a form NOT present in ResonantForms.
	 * A dangling reference means an outfit that silently grants nothing -- exactly
	 * the silent-no-op class this project keeps paying for -- so it is surfaced as
	 * data rather than discovered in PIE. Empty is the healthy state.
	 */
	TArray<FName> FindCosmeticsWithDanglingForm() const;

	/** Slot weight, defaulting to 1.0 when the slot is not in SlotStyleWeights. */
	float GetSlotStyleWeight(EMelodiaWardrobeSlot Slot) const;
};