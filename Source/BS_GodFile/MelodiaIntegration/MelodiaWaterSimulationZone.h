#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterSimulationZone.generated.h"

class UMelodiaWaterNativeSimulationComponent;
class UMelodiaWaterProfile;

/** Placeable project-owned container for a promoted native Water interaction
 * zone. Engine Water assets remain untouched and can be upgraded independently. */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaWaterSimulationZone final : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaWaterSimulationZone();

	UFUNCTION(BlueprintCallable, Category="Melodia|Water|Native")
	UMelodiaWaterNativeSimulationComponent* GetNativeSimulationComponent() const { return NativeSimulationComponent; }

	/** Blueprint-owned engine component configuration seam for the placed zone. */
	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Water|Native")
	void ConfigureEngineWaterComponents(UMelodiaWaterProfile* ProfileAsset);

	/** Blueprint-owned routing seam for the engine Water fluid force API. */
	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Water|Native")
	void RouteImpulseToNativeWater(const FMelodiaWaterFluidImpulse& Impulse);

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Water|Native")
	TObjectPtr<UMelodiaWaterNativeSimulationComponent> NativeSimulationComponent;
};
