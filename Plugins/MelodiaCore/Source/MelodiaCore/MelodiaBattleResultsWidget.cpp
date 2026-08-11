#include "MelodiaBattleResultsWidget.h"

#include "Components/TextBlock.h"
#include "MelodiaBattleSession.h"

void UMelodiaBattleResultsWidget::NativeConstruct()
{
	Super::NativeConstruct();
	RefreshFromBattleSession();
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
