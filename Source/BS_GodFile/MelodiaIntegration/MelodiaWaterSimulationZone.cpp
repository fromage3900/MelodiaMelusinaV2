#include "MelodiaWaterSimulationZone.h"

#include "MelodiaWaterNativeSimulationComponent.h"

AMelodiaWaterSimulationZone::AMelodiaWaterSimulationZone()
{
	PrimaryActorTick.bCanEverTick = false;
	NativeSimulationComponent = CreateDefaultSubobject<UMelodiaWaterNativeSimulationComponent>(TEXT("NativeWaterSimulation"));
}
