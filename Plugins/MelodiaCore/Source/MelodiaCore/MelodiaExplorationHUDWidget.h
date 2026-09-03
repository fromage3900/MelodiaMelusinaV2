#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaExplorationHUDWidget.generated.h"

class UFont;

/** Minimal presentation-only exploration legend; it owns no gameplay actions. */
UCLASS()
class MELODIACORE_API UMelodiaExplorationHUDWidget final : public UUserWidget
{
	GENERATED_BODY()

public:
	UMelodiaExplorationHUDWidget(const FObjectInitializer& ObjectInitializer);

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
	UPROPERTY()
	TObjectPtr<UFont> UIFont;
};
