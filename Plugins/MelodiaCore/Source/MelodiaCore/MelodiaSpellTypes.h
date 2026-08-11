// Element and harmonic key definitions for Melodia Lv1-30.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#pragma once

#include "CoreMinimal.h"
#include "MelodiaSpellTypes.generated.h"

/** Seven harmonic elements used by skills, enemies, and equippable keys. */
UENUM(BlueprintType)
enum class EMelodiaSpellElement : uint8
{
	Forte   UMETA(DisplayName = "Forte"),
	Tide    UMETA(DisplayName = "Tide"),
	Gale    UMETA(DisplayName = "Gale"),
	Stone   UMETA(DisplayName = "Stone"),
	Radiant UMETA(DisplayName = "Radiant"),
	Umbral  UMETA(DisplayName = "Umbral"),
	Arcane  UMETA(DisplayName = "Arcane")
};

/** Equippable harmonic key ΓÇö matches a spell element for weakness bonus damage. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaElementKeyDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Element Key")
	FName KeyId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Element Key")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Element Key")
	EMelodiaSpellElement Element = EMelodiaSpellElement::Forte;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Element Key", meta = (ClampMin = "1"))
	int32 MechanicLevelRequired = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Element Key")
	FText UnlockBlurb;
};
