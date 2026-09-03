#include "MelodiaCompanionData.h"

bool FMelodiaCompanionDefinition::IsValid(FText* OutError) const
{
	if (CompanionId.IsNone())
	{
		if (OutError) *OutError = FText::FromString(TEXT("Companion requires a stable CompanionId."));
		return false;
	}
	if (NPCDefinition.Role != EMelodiaNPCRole::Companion)
	{
		if (OutError) *OutError = FText::FromString(TEXT("Companion NPC definition must use the Companion role."));
		return false;
	}
	if (!NPCDefinition.IsValid(OutError))
	{
		return false;
	}
	if (NPCDefinition.SkeletalMesh.IsNull())
	{
		if (OutError) *OutError = FText::FromString(TEXT("Companion requires a skeletal-mesh presentation reference."));
		return false;
	}
	if (MeshRelativeTransform.ContainsNaN())
	{
		if (OutError) *OutError = FText::FromString(TEXT("Companion mesh presentation transform must be finite."));
		return false;
	}
	if (!FurProfile.IsValid(OutError))
	{
		return false;
	}
	if (!WardrobeProfile.PreferredCosmeticIds.IsEmpty() && !WardrobeProfile.IsValid(OutError))
	{
		return false;
	}
	if (MusicalMotif.IsNone())
	{
		if (OutError) *OutError = FText::FromString(TEXT("Companion requires a musical motif."));
		return false;
	}
	if (FollowDistance < 0.0f || FollowAcceptanceRadius < 0.0f)
	{
		if (OutError) *OutError = FText::FromString(TEXT("Companion follow distances cannot be negative."));
		return false;
	}
	if (SupportedInteractions.Num() == 0)
	{
		if (OutError) *OutError = FText::FromString(TEXT("Companion requires at least one interaction."));
		return false;
	}
	return true;
}

FPrimaryAssetId UMelodiaCompanionDefinitionAsset::GetPrimaryAssetId() const
{
	const FName StableName = Definition.CompanionId.IsNone() ? GetFName() : Definition.CompanionId;
	return FPrimaryAssetId(TEXT("MelodiaCompanion"), StableName);
}
