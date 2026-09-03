#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaRoguelikeRunSubsystem.h"
#include "MelodiaRoguelikeRewardWidget.generated.h"

class AMelodiaDungeonRunCoordinator;

/** Native fallback reward screen; Blueprint art can subclass it without changing gameplay. */
UCLASS(Blueprintable)
class MELODIACORE_API UMelodiaRoguelikeRewardWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	TArray<FMelodiaRunRewardCandidate> Candidates;

	UPROPERTY(BlueprintReadWrite, Category="Melodia|Roguelike")
	TObjectPtr<AMelodiaDungeonRunCoordinator> Coordinator;

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void ShowCandidates(const TArray<FMelodiaRunRewardCandidate>& InCandidates);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void HideChoices();

	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry,
		const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements,
		int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};
