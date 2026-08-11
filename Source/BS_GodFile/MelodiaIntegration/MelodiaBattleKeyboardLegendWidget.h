#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaBattleKeyboardLegendWidget.generated.h"

class UFont;

/**
 * Presentation-only keyboard legend for the stock JRPG battle UI.
 * It deliberately owns no focus, input binding, battle state, or widget-tree
 * relationship with the stock BattleUI package.
 */
UCLASS()
class BS_GODFILE_API UMelodiaBattleKeyboardLegendWidget final : public UUserWidget
{
	GENERATED_BODY()

public:
	UMelodiaBattleKeyboardLegendWidget(const FObjectInitializer& ObjectInitializer);

protected:
	virtual int32 NativePaint(
		const FPaintArgs& Args,
		const FGeometry& AllottedGeometry,
		const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements,
		int32 LayerId,
		const FWidgetStyle& InWidgetStyle,
		bool bParentEnabled) const override;

private:
	/** Canonical Melodia UI font. No engine-default fallback is intentionally allowed. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Presentation")
	TObjectPtr<UFont> LegendFont;
};
