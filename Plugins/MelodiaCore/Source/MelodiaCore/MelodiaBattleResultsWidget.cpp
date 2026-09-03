#include "MelodiaBattleResultsWidget.h"

#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Input/Reply.h"
#include "InputCoreTypes.h"
#include "MelodiaBattleSession.h"

void UMelodiaBattleResultsWidget::NativeConstruct()
{
	Super::NativeConstruct();
	bDismissed = false;

	SetIsFocusable(true);
	SetKeyboardFocus();

	if (Btn_Continue)
	{
		Btn_Continue->OnClicked.RemoveDynamic(this, &ThisClass::HandleDismissClicked);
		Btn_Continue->OnClicked.AddDynamic(this, &ThisClass::HandleDismissClicked);
	}
	if (Btn_Dismiss)
	{
		Btn_Dismiss->OnClicked.RemoveDynamic(this, &ThisClass::HandleDismissClicked);
		Btn_Dismiss->OnClicked.AddDynamic(this, &ThisClass::HandleDismissClicked);
	}

	RefreshFromBattleSession();
}

void UMelodiaBattleResultsWidget::NativeDestruct()
{
	if (!bDismissed)
	{
		bDismissed = true;
		OnResultsDismissed.Broadcast();
	}
	Super::NativeDestruct();
}

FReply UMelodiaBattleResultsWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Escape
		|| Key == EKeys::Gamepad_FaceButton_Bottom || Key == EKeys::Gamepad_Special_Right)
	{
		Dismiss();
		return FReply::Handled();
	}

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

FReply UMelodiaBattleResultsWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		Dismiss();
		return FReply::Handled();
	}

	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

void UMelodiaBattleResultsWidget::HandleDismissClicked()
{
	Dismiss();
}

void UMelodiaBattleResultsWidget::Dismiss()
{
	if (bDismissed)
	{
		return;
	}

	bDismissed = true;
	OnResultsDismissed.Broadcast();
	RemoveFromParent();
}

void UMelodiaBattleResultsWidget::RefreshFromBattleSession()
{
	const UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this);
	if (!Session)
	{
		return;
	}

	const FMelodiaBattleResultsSummary& Results = Session->GetLastBattleResults();
	if (TXT_Rank) TXT_Rank->SetText(FText::Format(NSLOCTEXT("Melodia", "ResultRank", "Rank: {0}"), Results.Rank));
	if (TXT_Score) TXT_Score->SetText(FText::AsNumber(FMath::RoundToInt(Results.Score)));
	if (TXT_Perfect) TXT_Perfect->SetText(FText::Format(NSLOCTEXT("Melodia", "ResultPerfect", "Perfect: {0}"), FText::AsNumber(Results.PerfectCount)));
	if (TXT_Hit) TXT_Hit->SetText(FText::Format(NSLOCTEXT("Melodia", "ResultHit", "Hits: {0}"), FText::AsNumber(Results.HitCount)));
	if (TXT_Miss) TXT_Miss->SetText(FText::Format(NSLOCTEXT("Melodia", "ResultMiss", "Misses: {0}"), FText::AsNumber(Results.MissCount)));
	if (TXT_Damage) TXT_Damage->SetText(FText::Format(NSLOCTEXT("Melodia", "ResultDamage", "Damage: {0}"), FText::AsNumber(FMath::RoundToInt(Results.DamageDealt))));
	if (TXT_MaxCombo) TXT_MaxCombo->SetText(FText::Format(NSLOCTEXT("Melodia", "ResultCombo", "Max Combo: {0}"), FText::AsNumber(Results.MaxCombo)));
}
