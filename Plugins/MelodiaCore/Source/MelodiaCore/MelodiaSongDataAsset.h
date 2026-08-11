#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaSongSkillLibrary.h"
#include "MelodiaSongDataAsset.generated.h"

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaSongChart
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Song Chart")
	FText SongTitle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Song Chart")
	FText ArtistName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Song Chart")
	float BPM = 128.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Song Chart")
	TArray<FMelodiaSongSkillRecipe> SkillVariants;

	/** Optional Basic-command chart for this song (lanes authored, not Index%4). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Song Chart")
	TArray<FMelodiaChartNote> BasicChartNotes;
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaSongDataAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Songs")
	TArray<FMelodiaSongChart> Songs;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Songs")
	TMap<FName, FMelodiaSongSkillRecipe> SkillOverrides;
};
