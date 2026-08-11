#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaUIFeedbackSubsystem.generated.h"

class USoundBase;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
	FMelodiaUIFeedbackRequested,
	FName, FeedbackId,
	FVector2D, ScreenPosition);

/**
 * Presentation-only seam for UI sound, animation, sparkle, and optional haptics.
 * Semantic requests are still broadcast for authored listeners; an audible
 * project cue is also provided so feedback never silently disappears.
 */
UCLASS()
class BS_GODFILE_API UMelodiaUIFeedbackSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UMelodiaUIFeedbackSubsystem();

	UFUNCTION(BlueprintPure, Category = "Melodia|UI|Feedback", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaUIFeedbackSubsystem* Get(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Feedback", meta = (WorldContext = "WorldContextObject"))
	static bool RequestFeedback(
		const UObject* WorldContextObject,
		FName FeedbackId,
		FVector2D ScreenPosition);

	UPROPERTY(BlueprintAssignable, Category = "Melodia|UI|Feedback")
	FMelodiaUIFeedbackRequested OnFeedbackRequested;

private:
	void PlayDefaultFeedback();

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|UI|Feedback")
	TSoftObjectPtr<USoundBase> DefaultFeedbackSound;

	UPROPERTY(Transient)
	TObjectPtr<USoundBase> LoadedDefaultFeedbackSound;
};
