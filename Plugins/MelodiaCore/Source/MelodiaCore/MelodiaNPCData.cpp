#include "MelodiaNPCData.h"

bool FMelodiaNPCDef::IsValid(FText* OutError) const
{
	if (NPCId.IsNone())
	{
		if (OutError) { *OutError = FText::FromString(TEXT("NPCId must not be None.")); }
		return false;
	}
	if (StaticMesh.IsNull() && SkeletalMesh.IsNull())
	{
		if (OutError) { *OutError = FText::FromString(TEXT("NPC requires a static or skeletal mesh.")); }
		return false;
	}
	return true;
}

FPrimaryAssetId UMelodiaNPCDefinitionAsset::GetPrimaryAssetId() const
{
	const FName StableName = Definition.NPCId.IsNone() ? GetFName() : Definition.NPCId;
	return FPrimaryAssetId(TEXT("MelodiaNPC"), StableName);
}