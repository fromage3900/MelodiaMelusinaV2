#include "MelodiaRoguelikeRewardWidget.h"

#include "Fonts/SlateFontInfo.h"
#include "InputCoreTypes.h"
#include "Input/Reply.h"
#include "MelodiaDungeonRunCoordinator.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

void UMelodiaRoguelikeRewardWidget::ShowCandidates(const TArray<FMelodiaRunRewardCandidate>& InCandidates)
{
	Candidates = InCandidates;
	if (!IsInViewport())
	{
		AddToViewport(100);
	}
	SetVisibility(ESlateVisibility::Visible);
	SetIsFocusable(true);
	SetKeyboardFocus();
}

void UMelodiaRoguelikeRewardWidget::HideChoices()
{
	SetVisibility(ESlateVisibility::Collapsed);
}

FReply UMelodiaRoguelikeRewardWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	int32 Index = INDEX_NONE;
	if (Key == EKeys::One || Key == EKeys::NumPadOne) Index = 0;
	else if (Key == EKeys::Two || Key == EKeys::NumPadTwo) Index = 1;
	else if (Key == EKeys::Three || Key == EKeys::NumPadThree) Index = 2;
	if (Index != INDEX_NONE && Coordinator && Coordinator->CommitReward(Index))
	{
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

int32 UMelodiaRoguelikeRewardWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry,
	const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements, int32 LayerId,
	const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	const int32 BaseLayer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	const FVector2D Size = AllottedGeometry.GetLocalSize();
	FSlateDrawElement::MakeBox(OutDrawElements, BaseLayer + 1,
		AllottedGeometry.ToPaintGeometry(FVector2D(Size.X * 0.88f, Size.Y * 0.52f), FSlateLayoutTransform(FVector2D(Size.X * 0.06f, Size.Y * 0.22f))),
		FCoreStyle::Get().GetBrush(TEXT("WhiteBrush")), ESlateDrawEffect::None, FLinearColor(0.035f, 0.02f, 0.08f, 0.94f));
	const FSlateFontInfo TitleFont = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 28);
	const FSlateFontInfo CardFont = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 19);
	FSlateDrawElement::MakeText(OutDrawElements, BaseLayer + 2,
		AllottedGeometry.ToPaintGeometry(FVector2D(Size.X * 0.68f, 45.0f), FSlateLayoutTransform(FVector2D(Size.X * 0.16f, Size.Y * 0.26f))),
		TEXT("Choose the harmony carried into the next doorway"), TitleFont, ESlateDrawEffect::None, FLinearColor(1.0f, 0.82f, 0.95f));
	for (int32 Index = 0; Index < Candidates.Num(); ++Index)
	{
		const float X = Size.X * (0.10f + Index * 0.29f);
		const FString Label = FString::Printf(TEXT("[%d] %s"), Index + 1, *Candidates[Index].DisplayName.ToString());
		FSlateDrawElement::MakeText(OutDrawElements, BaseLayer + 2,
			AllottedGeometry.ToPaintGeometry(FVector2D(Size.X * 0.25f, 130.0f), FSlateLayoutTransform(FVector2D(X, Size.Y * 0.40f))),
			Label, CardFont, ESlateDrawEffect::None, Index == 1 ? FLinearColor(1.0f, 0.35f, 0.55f) : FLinearColor(0.72f, 0.88f, 1.0f));
	}
	return BaseLayer + 2;
}
