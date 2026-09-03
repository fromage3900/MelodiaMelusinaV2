// Placeable state anchor for authored opening maps.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaOpeningStateComponent.h"
#include "MelodiaOpeningStateAnchor.generated.h"

UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaOpeningStateAnchor : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaOpeningStateAnchor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Opening")
	TObjectPtr<UMelodiaResonanceBondComponent> ResonanceBond;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Opening")
	TObjectPtr<UMelodiaDissonanceComponent> Dissonance;
};
