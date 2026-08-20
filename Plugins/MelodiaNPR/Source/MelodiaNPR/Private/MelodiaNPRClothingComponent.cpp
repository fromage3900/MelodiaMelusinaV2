// MelodiaNPR — modular clothing blendshape sync implementation.

#include "MelodiaNPRClothingComponent.h"

UMelodiaNPRClothingComponent::UMelodiaNPRClothingComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaNPRClothingComponent::SyncBlendshapes(FName OutfitId, const TArray<float>& BlendshapeWeights)
{
	TArray<float> Clamped;
	Clamped.Reserve(BlendshapeWeights.Num());
	for (const float W : BlendshapeWeights)
	{
		Clamped.Add(FMath::Clamp(W, 0.0f, 1.0f));
	}

	OutfitBlendshapeCache.Add(OutfitId, MoveTemp(Clamped));

	// TODO: apply to the skeletal mesh. This needs the outfit's blendshape target names
	// from the wardrobe catalog; until that mapping exists, weights are cached only and
	// this component changes nothing visually. Do not treat a call here as a visual change.
	UE_LOG(LogTemp, Log, TEXT("MELODIA_NPR: cached %d blendshape weights for outfit %s"),
		BlendshapeWeights.Num(), *OutfitId.ToString());
}

FName UMelodiaNPRClothingComponent::GetCurrentOutfit() const
{
	return CurrentOutfitId;
}

void UMelodiaNPRClothingComponent::SetCurrentOutfit(FName OutfitId)
{
	CurrentOutfitId = OutfitId;
	UE_LOG(LogTemp, Log, TEXT("MELODIA_NPR: current outfit set to %s"), *OutfitId.ToString());
}

TArray<float> UMelodiaNPRClothingComponent::GetCachedWeights(FName OutfitId) const
{
	if (const TArray<float>* Found = OutfitBlendshapeCache.Find(OutfitId))
	{
		return *Found;
	}
	return TArray<float>();
}
