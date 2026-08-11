#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaStorySequenceWidget.generated.h"

class UButton;
class UImage;
class UTextBlock;
class UMelodiaStorySequenceData;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaStorySequenceFinished, UMelodiaStorySequenceData*, Sequence);

/** A reusable UMG presenter for FMelodiaStorySlide data. */
UCLASS(Abstract, Blueprintable)
class MELODIACORE_API UMelodiaStorySequenceWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category="Melodia|Story")
	FMelodiaStorySequenceFinished OnSequenceFinished;

	UFUNCTION(BlueprintCallable, Category="Melodia|Story")
	bool SetSequence(UMelodiaStorySequenceData* InSequence);

	UFUNCTION(BlueprintCallable, Category="Melodia|Story")
	void Advance();

	UFUNCTION(BlueprintCallable, Category="Melodia|Story")
	void Skip();

	UFUNCTION(BlueprintPure, Category="Melodia|Story")
	int32 GetSlideIndex() const { return CurrentSlideIndex; }

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UImage> SlideArtwork;

	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UTextBlock> KickerText;

	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UTextBlock> TitleText;

	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UTextBlock> BodyText;

	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UButton> AdvanceButton;

	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UButton> SkipButton;

private:
	void ApplyCurrentSlide();
	void FinishSequence();

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaStorySequenceData> Sequence;

	int32 CurrentSlideIndex = 0;
	FTimerHandle AutoAdvanceTimer;
};
