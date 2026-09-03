#include "MelodiaBattleKeyboardLegendWidget.h"

#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Engine/Font.h"
#include "UObject/ConstructorHelpers.h"

UMelodiaBattleKeyboardLegendWidget::UMelodiaBattleKeyboardLegendWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	static ConstructorHelpers::FObjectFinder<UFont> MelodiaUIFont(
		TEXT("/Game/Melodia/UI/Fonts/F_Melodia_UI.F_Melodia_UI"));
	LegendFont = MelodiaUIFont.Object;
}

int32 UMelodiaBattleKeyboardLegendWidget::NativePaint(
	const FPaintArgs& Args,
	const FGeometry& AllottedGeometry,
	const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements,
	const int32 LayerId,
	const FWidgetStyle& InWidgetStyle,
	const bool bParentEnabled) const
{
	const int32 SuperLayerId = Super::NativePaint(
		Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	FPaintContext Context(AllottedGeometry, MyCullingRect, OutDrawElements, SuperLayerId, InWidgetStyle, bParentEnabled);

	const FVector2D ViewportSize = AllottedGeometry.GetLocalSize();
	if (ViewportSize.X <= 1.0f || ViewportSize.Y <= 1.0f)
	{
		return SuperLayerId;
	}

	const FVector2D PanelSize(690.0f, 42.0f);
	const FVector2D PanelPosition((ViewportSize.X - PanelSize.X) * 0.5f, ViewportSize.Y - 86.0f);
	const FLinearColor PanelColor(0.10f, 0.06f, 0.14f, 0.84f);
	const FLinearColor AccentColor(0.95f, 0.74f, 0.88f, 0.96f);

	UWidgetBlueprintLibrary::DrawBox(Context, PanelPosition, PanelSize, nullptr, PanelColor);
	UWidgetBlueprintLibrary::DrawBox(
		Context,
		PanelPosition + FVector2D(0.0f, 39.0f),
		FVector2D(PanelSize.X, 3.0f),
		nullptr,
		AccentColor);

	// A missing authored font suppresses this label rather than leaking Unreal's default font.
	if (LegendFont)
	{
		UWidgetBlueprintLibrary::DrawTextFormatted(
			Context,
			FText::FromString(TEXT("[J] Attack   [K] Skill   [I] Item   [F] Flee   [Enter / Space] Confirm   [Esc] Back")),
			PanelPosition + FVector2D(18.0f, 11.0f),
			LegendFont,
			15,
			NAME_None,
			FLinearColor::White);
	}

	return Context.MaxLayer;
}
