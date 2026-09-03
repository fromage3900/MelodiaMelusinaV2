#include "MelodiaFurBackend.h"

bool UMelodiaFurBackendAdapter::Initialize_Implementation(const FMelodiaFurProfile& InProfile)
{
	FText ValidationError;
	if (!InProfile.IsValid(&ValidationError))
	{
		return false;
	}

	ActiveProfile = InProfile;
	ActiveBackend = UMelodiaFurLibrary::SelectBackendForDistance(ActiveProfile, 0.0f);
	ResonanceIntensity = 0.0f;
	return true;
}

void UMelodiaFurBackendAdapter::SetDistance_Implementation(const float Distance)
{
	ActiveBackend = UMelodiaFurLibrary::SelectBackendForDistance(ActiveProfile, Distance);
}

void UMelodiaFurBackendAdapter::ApplyResonance_Implementation(const float Intensity)
{
	ResonanceIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
}
