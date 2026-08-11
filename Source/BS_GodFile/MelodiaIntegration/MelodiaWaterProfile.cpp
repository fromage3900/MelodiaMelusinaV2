#include "MelodiaWaterProfile.h"

FPrimaryAssetId UMelodiaWaterProfile::GetPrimaryAssetId() const
{
	return FPrimaryAssetId(FPrimaryAssetType(TEXT("MelodiaWaterProfile")), GetFName());
}
