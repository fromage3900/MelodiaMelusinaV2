// Bare-minimum debug HUD for Melodia battle state.
// Text-only NativePaint overlay: battle phase, HP, SP, grade feedback, crescendo gauge.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaMinimalHUD.generated.h"

class UMelodiaBattleSession;
class UMelodiaCombatStateComponent;

/**
 * Bare-minimum battle HUD ΓÇö renders phase info, HP bars, SP, and grade feedback
 * via NativePaint. Designed as a throwaway debug HUD to be replaced by a proper
 * Slate/UMG HUD in a later phase.
 */
UCLASS(Blueprintable)
class MELODIACORE_API UMelodiaMinimalHUD : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Last rhythm grade displayed as feedback flash. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|HUD")
	FString LastGradeText;

	/** Flash timer ΓÇö grade text fades after this countdown. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|HUD")
	float GradeFlashTimer = 0.0f;

	/** Show the grade feedback text (called externally or from BattleSession delegate). */
	UFUNCTION(BlueprintCallable, Category="Melodia|HUD")
	void FlashGrade(const FString& GradeString, FLinearColor Color);

private:
	void DrawBar(FPaintContext& InContext, const FVector2D& Position, const FVector2D& Size,
		float FillRatio, FLinearColor FillColor, FLinearColor BackColor, const FString& Label) const;

	UPROPERTY()
	FLinearColor LastGradeColor = FLinearColor::White;

	UPROPERTY()
	mutable FSlateFontInfo CachedFont;

	UPROPERTY()
	mutable bool bFontCached = false;
};
