// MelodiaNPR — modular clothing blendshape sync.
//
// Decision 044: the UMelodiaOutfitComponent algorithm is re-hosted in the MelodiaWardrobe
// plugin. This component is the rendering-side bridge: it takes an outfit id from the
// wardrobe and applies the matching blendshape weights to the skeletal mesh.
//
// Scaffold status: weights are validated and cached; the mesh-side application is a
// documented TODO, not a silent no-op.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaNPRClothingComponent.generated.h"

UCLASS(ClassGroup = (Melodia), meta = (BlueprintSpawnableComponent))
class MELODIANPR_API UMelodiaNPRClothingComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaNPRClothingComponent();

	/**
	 * Cache blendshape weights for an outfit, clamped to [0,1].
	 * @param OutfitId          The cosmetic ID from the wardrobe catalog.
	 * @param BlendshapeWeights One weight per blendshape target.
	 */
	UFUNCTION(BlueprintCallable, Category = "NPR|Clothing")
	void SyncBlendshapes(FName OutfitId, const TArray<float>& BlendshapeWeights);

	/** The currently active outfit ID. */
	UFUNCTION(BlueprintPure, Category = "NPR|Clothing")
	FName GetCurrentOutfit() const;

	/** Set the active outfit. Does not itself push weights — call SyncBlendshapes. */
	UFUNCTION(BlueprintCallable, Category = "NPR|Clothing")
	void SetCurrentOutfit(FName OutfitId);

	/** Cached weights for an outfit, empty if never synced. */
	UFUNCTION(BlueprintPure, Category = "NPR|Clothing")
	TArray<float> GetCachedWeights(FName OutfitId) const;

private:
	UPROPERTY(Transient)
	FName CurrentOutfitId;

	/** Not a UPROPERTY: TMap<FName, TArray<float>> is not a reflected container shape. */
	TMap<FName, TArray<float>> OutfitBlendshapeCache;
};
