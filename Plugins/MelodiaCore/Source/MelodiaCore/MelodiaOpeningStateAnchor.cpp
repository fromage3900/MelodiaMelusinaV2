#include "MelodiaOpeningStateAnchor.h"

AMelodiaOpeningStateAnchor::AMelodiaOpeningStateAnchor()
{
	PrimaryActorTick.bCanEverTick = false;
	ResonanceBond = CreateDefaultSubobject<UMelodiaResonanceBondComponent>(TEXT("ResonanceBond"));
	Dissonance = CreateDefaultSubobject<UMelodiaDissonanceComponent>(TEXT("Dissonance"));
}
