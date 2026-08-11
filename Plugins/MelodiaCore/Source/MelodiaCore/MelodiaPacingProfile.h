#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaPacingProfile.generated.h"

/**
 * Authored timing values, keyed by a stable FName ID, resolved through
 * UMelodiaPacingSubsystem. Follows the project's documented adapter pattern
 * (Docs/MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md): stable ID ->
 * DataAsset -> facade subsystem -> typed request -> consumer resolves.
 *
 * Not a replacement for every EditAnywhere timing float in the project --
 * only values worth tuning centrally without touching each actor. See
 * UMelodiaPacingSubsystem's comment for the degrade-gracefully contract that
 * makes this additive rather than a hard dependency.
 */
UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaPacingProfile : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Pacing")
	TMap<FName, float> Durations;
};
