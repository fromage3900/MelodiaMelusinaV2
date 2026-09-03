#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaStorySequenceData.generated.h"

class UTexture2D;
class USoundBase;

/** One editable storybook card. It is presentation data only. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaStorySlide
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	TSoftObjectPtr<UTexture2D> Artwork;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	FText Kicker;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story", meta=(MultiLine=true))
	FText Body;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story|Audio")
	TSoftObjectPtr<USoundBase> Stinger;

	/** Zero means manual advance only. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story", meta=(ClampMin="0.0", ClampMax="60.0"))
	float AutoAdvanceAfterSeconds = 0.0f;
};

/**
 * Reusable authored sequence asset. It owns no save, quest, input, battle, or
 * travel authority; the caller decides what completion means.
 */
UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaStorySequenceData final : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	FName SequenceId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	TArray<FMelodiaStorySlide> Slides;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	bool bAllowSkip = true;
};
