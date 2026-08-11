// Comic Orrery world-navigator data ("C6" in Docs/MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md
// section 4): maps each orrery sphere (Sakura/Stage/Celestial/Village, ...) to a travel map and
// the opening-flow phase required to unlock it. WBP_ComicOrrery reads this to build its sphere
// buttons instead of hardcoding level names in UMG.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaOrreryRegistry.generated.h"

USTRUCT(BlueprintType)
struct FMelodiaOrrerySphereDef
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Orrery")
	FName SphereId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Orrery")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Orrery")
	FName MapName;

	/** Minimum opening-flow phase required before this sphere is selectable. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Orrery")
	EMelodiaOpeningPhase RequiredPhase = EMelodiaOpeningPhase::NotStarted;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Orrery")
	TSoftObjectPtr<UTexture2D> Icon;
};

/** Data asset backing WBP_ComicOrrery — one instance authored per project, spheres in display order. */
UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaOrreryRegistry : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Orrery")
	TArray<FMelodiaOrrerySphereDef> Spheres;

	/** True if CurrentPhase is at or beyond the sphere's RequiredPhase (enum is ordered by unlock progression). */
	UFUNCTION(BlueprintPure, Category="Melodia|Orrery")
	bool IsSphereUnlocked(const FMelodiaOrrerySphereDef& Sphere, EMelodiaOpeningPhase CurrentPhase) const
	{
		return static_cast<uint8>(CurrentPhase) >= static_cast<uint8>(Sphere.RequiredPhase);
	}
};
