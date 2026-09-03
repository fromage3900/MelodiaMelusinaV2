#include "MelodiaResonanceGardenData.h"

namespace
{
	void SetResonanceGardenValidationError(FText* OutError, const TCHAR* Message)
	{
		if (OutError)
		{
			*OutError = FText::FromString(Message);
		}
	}
}

FMelodiaFurProfile::FMelodiaFurProfile()
{
	LODBands.Add({0.0f, 400.0f, EMelodiaFurBackendKind::NativeGroom});
	LODBands.Add({400.0f, 1200.0f, EMelodiaFurBackendKind::ShellCard});
	LODBands.Add({1200.0f, 1000000.0f, EMelodiaFurBackendKind::Impostor});
}

bool FMelodiaFurProfile::IsValid(FText* OutError) const
{
	if (ProfileId.IsNone())
	{
		SetResonanceGardenValidationError(OutError, TEXT("Fur profile requires a stable ProfileId."));
		return false;
	}

	if (LODBands.Num() == 0)
	{
		SetResonanceGardenValidationError(OutError, TEXT("Fur profile requires at least one LOD band."));
		return false;
	}

	float PreviousMax = -1.0f;
	for (int32 Index = 0; Index < LODBands.Num(); ++Index)
	{
		const FMelodiaFurLodBand& Band = LODBands[Index];
		if (Band.MinDistance < 0.0f || Band.MaxDistance <= Band.MinDistance)
		{
			SetResonanceGardenValidationError(OutError, TEXT("Fur LOD bands must have non-negative, increasing distances."));
			return false;
		}
		if (Index > 0 && !FMath::IsNearlyEqual(Band.MinDistance, PreviousMax))
		{
			SetResonanceGardenValidationError(OutError, TEXT("Fur LOD bands must be contiguous."));
			return false;
		}
		PreviousMax = Band.MaxDistance;
	}

	if (WoolClumpScale < 0.0f || SheenResponse < 0.0f || SheenResponse > 1.0f)
	{
		SetResonanceGardenValidationError(OutError, TEXT("Fur clump and sheen values are outside their valid ranges."));
		return false;
	}

	return true;
}

bool FMelodiaStyleGenome::IsValid(FText* OutError) const
{
	if (GenomeId.IsNone())
	{
		SetResonanceGardenValidationError(OutError, TEXT("Style genome requires a stable GenomeId."));
		return false;
	}
	if (MaterialFamily.IsNone())
	{
		SetResonanceGardenValidationError(OutError, TEXT("Style genome requires a material family."));
		return false;
	}
	if (MusicMotif.IsNone())
	{
		SetResonanceGardenValidationError(OutError, TEXT("Style genome requires a music motif."));
		return false;
	}
	if (Sheen < 0.0f || Sheen > 1.0f || Iridescence < 0.0f || Iridescence > 1.0f
		|| Sparkle < 0.0f || Sparkle > 1.0f || Bloom < 0.0f || Bloom > 1.0f
		|| RhythmSensitivity < 0.0f || RhythmSensitivity > 2.0f)
	{
		SetResonanceGardenValidationError(OutError, TEXT("Style genome material or rhythm values are outside their valid ranges."));
		return false;
	}
	return true;
}

FPrimaryAssetId UMelodiaStyleGenomeAsset::GetPrimaryAssetId() const
{
	const FName StableName = Genome.GenomeId.IsNone() ? GetFName() : Genome.GenomeId;
	return FPrimaryAssetId(TEXT("MelodiaStyleGenome"), StableName);
}

EMelodiaFurBackendKind UMelodiaFurLibrary::SelectBackendForDistance(const FMelodiaFurProfile& Profile, const float Distance)
{
	const float SafeDistance = FMath::Max(0.0f, Distance);
	for (const FMelodiaFurLodBand& Band : Profile.LODBands)
	{
		if (Band.Contains(SafeDistance))
		{
			return Band.Backend;
		}
	}
	return Profile.LODBands.Num() > 0
		? Profile.LODBands.Last().Backend
		: EMelodiaFurBackendKind::ShellCard;
}
