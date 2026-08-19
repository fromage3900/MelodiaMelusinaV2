// MelodiaNPR — toon material applier implementation.

#include "MelodiaToonMaterial.h"

#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace MelodiaToonParamNames
{
	static const FName RimIntensity(TEXT("RimIntensity"));
	static const FName RimFalloff(TEXT("RimFalloff"));
	static const FName SdfThreshold(TEXT("SdfThreshold"));
	static const FName OutlineWidth(TEXT("OutlineWidth"));
	static const FName Metallic(TEXT("Metallic"));
	static const FName Roughness(TEXT("Roughness"));
	static const FName OutlineColor(TEXT("OutlineColor"));
	static const FName BaseTint(TEXT("BaseTint"));
	static const FName OutfitLayer(TEXT("OutfitLayer"));
}

UMaterialInstanceDynamic* UMelodiaToonMaterial::InitializeFrom(UMaterialInterface* SourceMaterial)
{
	if (!SourceMaterial)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_NPR: InitializeFrom called with a null material."));
		return nullptr;
	}

	ToonInstance = UMaterialInstanceDynamic::Create(SourceMaterial, this);
	return ToonInstance;
}

void UMelodiaToonMaterial::ApplyToonParams(const FMelodiaToonParams& Params)
{
	if (!ToonInstance)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_NPR: ApplyToonParams before InitializeFrom; nothing applied."));
		return;
	}

	using namespace MelodiaToonParamNames;
	ToonInstance->SetScalarParameterValue(RimIntensity, Params.RimIntensity);
	ToonInstance->SetScalarParameterValue(RimFalloff, Params.RimFalloff);
	ToonInstance->SetScalarParameterValue(SdfThreshold, Params.SdfThreshold);
	ToonInstance->SetScalarParameterValue(OutlineWidth, Params.OutlineWidth);
	ToonInstance->SetScalarParameterValue(Metallic, Params.Metallic);
	ToonInstance->SetScalarParameterValue(Roughness, Params.Roughness);
	ToonInstance->SetVectorParameterValue(OutlineColor, Params.OutlineColor);
	ToonInstance->SetVectorParameterValue(BaseTint, Params.BaseTint);
}

void UMelodiaToonMaterial::SetOutfitLayer(int32 LayerIndex)
{
	OutfitLayer = LayerIndex;
	if (ToonInstance)
	{
		ToonInstance->SetScalarParameterValue(
			MelodiaToonParamNames::OutfitLayer, static_cast<float>(LayerIndex));
	}
}

int32 UMelodiaToonMaterial::GetOutfitLayer() const
{
	return OutfitLayer;
}
