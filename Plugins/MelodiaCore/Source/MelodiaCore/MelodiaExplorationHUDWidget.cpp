#include "MelodiaExplorationHUDWidget.h"

#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Engine/Font.h"
#include "UObject/ConstructorHelpers.h"

UMelodiaExplorationHUDWidget::UMelodiaExplorationHUDWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	static ConstructorHelpers::FObjectFinder<UFont> MelodiaUIFont(
		TEXT("/Game/Melodia/UI/Fonts/F_Melodia_UI.F_Melodia_UI"));
	UIFont = MelodiaUIFont.Object;
	SetVisibility(ESlateVisibility::HitTestInvisible);
}

int32 UMelodiaExplorationHUDWidget::NativePaint(
	const FPaintArgs& Args,
	const FGeometry& AllottedGeometry,
	const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements,
	const int32 LayerId,
	const FWidgetStyle& InWidgetStyle,
	const bool bParentEnabled) const
{
	const int32 SuperLayer = Super::NativePaint(
		Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	FPaintContext Context(AllottedGeometry, MyCullingRect, OutDrawElements, SuperLayer, InWidgetStyle, bParentEnabled);
	const FVector2D Size = AllottedGeometry.GetLocalSize();
	if (Size.X < 2.0f || Size.Y < 2.0f || !UIFont)
	{
		return SuperLayer;
	}

	const FVector2D PanelSize(500.0f, 38.0f);
	const FVector2D Position(Size.X - PanelSize.X - 28.0f, Size.Y - PanelSize.Y - 24.0f);
	UWidgetBlueprintLibrary::DrawBox(
		Context, Position, PanelSize, nullptr, FLinearColor(0.055f, 0.035f, 0.08f, 0.82f));
	UWidgetBlueprintLibrary::DrawTextFormatted(
		Context,
		FText::FromString(TEXT("[M / TAB] ORRERY    [E / F] INTERACT    [SHIFT] SPRINT")),
		Position + FVector2D(15.0f, 9.0f),
		UIFont,
		15.0f,
		NAME_None,
		FLinearColor(0.96f, 0.90f, 0.98f, 1.0f));
	return Context.MaxLayer;
}
