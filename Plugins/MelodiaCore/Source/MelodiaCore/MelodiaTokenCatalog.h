// Melody Token catalog — the Unreal-side token VARIANT definitions.
//
// The wallet (UMelodiaTokenWalletSubsystem) owns balances and transactions, keyed by
// ELEMENT. It deliberately knows nothing about how a token looks or what a pickup is
// worth. This catalog is that missing half: the art variant a player actually sees
// ("heart", "swirl") and what it resolves to.
//
// WHY A CATALOG RATHER THAN A HARDCODED TABLE
//
// The canonical model is Content/Python/gmm/game/tokens.py TOKEN_TYPES, which the wallet
// header names as the source it mirrors. There is NO runtime GMM<->Unreal channel, so a
// hand-typed C++ copy would be a third vocabulary drifting from the other two. Rows are
// generated from tokens.py instead, and Tools/wardrobe_draft_lint.py already reads that
// same model to validate cosmetic token_cost.
//
// Do NOT hand-edit rows. Regenerate them.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaTokenCatalog.generated.h"

class UMaterialInterface;
class UTexture2D;

/**
 * One token art variant and the element it resolves to.
 *
 * VariantId is the authoring-facing key ("heart", "star", "swirl", "water") and is what
 * cosmetic drafts price in. Element is what the wallet actually stores. Keeping both
 * means a designer prices in tokens they can see while the economy stays element-keyed.
 */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaTokenDefinition
{
	GENERATED_BODY()

	/** Art variant key from gmm TOKEN_TYPES: heart, star, swirl, water. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	FName VariantId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	FText DisplayName;

	/** The wallet element this variant grants and spends. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	EMelodiaSpellElement Element = EMelodiaSpellElement::Forte;

	/** Stat-economy weight from the canonical model. Heart 10, Radiant 12, Arcane 15, Tide 12. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token", meta=(ClampMin="0"))
	int32 Value = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	FName Rarity;

	/** Presentation only. The wallet never reads these. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token|Presentation")
	TSoftObjectPtr<UTexture2D> Icon;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token|Presentation")
	TSoftObjectPtr<UMaterialInterface> Material;
};

/**
 * Every token variant in the game. One asset, generated from the canonical model.
 *
 * A universal wallet widget binds to this for icons, names and values, and to
 * UMelodiaTokenWalletSubsystem for balances. Neither knows about the other.
 */
UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaTokenCatalog : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	TArray<FMelodiaTokenDefinition> Tokens;

	/** Source model these rows were generated from, for provenance. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	FString GeneratedFrom = TEXT("Content/Python/gmm/game/tokens.py");

	/** Definition for an art variant ("heart"), or nullptr. */
	const FMelodiaTokenDefinition* FindByVariant(FName VariantId) const;

	/** Blueprint-facing wrapper. bFound is false when the variant is unknown. */
	UFUNCTION(BlueprintPure, Category="Melodia|Token")
	FMelodiaTokenDefinition GetTokenByVariant(FName VariantId, bool& bFound) const;

	/**
	 * Every variant that resolves to an element. More than one variant may map to the
	 * same element, so this returns a list rather than a single definition.
	 */
	UFUNCTION(BlueprintPure, Category="Melodia|Token")
	TArray<FMelodiaTokenDefinition> GetTokensForElement(EMelodiaSpellElement Element) const;

	/**
	 * Resolve a draft-style cost map ({"heart": 5}) into element totals.
	 *
	 * Returns false and leaves OutElementCost empty if ANY variant is unknown — a
	 * partially-resolved price is worse than a rejected one, because it silently
	 * undercharges. Unknown variants are named in OutUnknownVariants.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Token")
	bool ResolveCost(const TMap<FName, int32>& VariantCost,
		TMap<FName, int32>& OutElementCost,
		TArray<FName>& OutUnknownVariants) const;

	/** Duplicate VariantIds, which make FindByVariant ambiguous. Empty is healthy. */
	TArray<FName> FindDuplicateVariants() const;

	virtual void PostLoad() override;
};
