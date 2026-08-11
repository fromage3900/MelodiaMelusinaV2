#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "MelodiaRoguelikeAuthorityTypes.h"
#include "MelodiaDungeonRecipeConsumer.generated.h"

UINTERFACE(BlueprintType)
class MELODIACORE_API UMelodiaDungeonRecipeConsumer : public UInterface
{
	GENERATED_BODY()
};

/** Implemented by the ProceduralDungeon generator that spatially executes MelodiaCore recipes.
 * Implementations may choose compatible RoomData and doors, but may not mutate run state. */
class MELODIACORE_API IMelodiaDungeonRecipeConsumer
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Roguelike|Generation")
	bool ApplyStageRecipe(const FMelodiaAuthoritativeStageRecipe& Recipe);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Roguelike|Generation")
	bool ValidateStageRecipe(const FMelodiaAuthoritativeStageRecipe& Recipe, FText& OutError) const;
};
