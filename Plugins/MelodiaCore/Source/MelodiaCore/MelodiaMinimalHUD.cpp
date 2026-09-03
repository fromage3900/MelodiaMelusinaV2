// Bare-minimum debug HUD for Melodia battle state.
// NativePaint text overlay: battle phase, HP bars, SP, grade feedback, crescendo gauge.

#include "MelodiaMinimalHUD.h"
#include "MelodiaRulesGenerated.h"

#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaBattleSession.h"
#include "MelodiaCombatStateComponent.h"

void UMelodiaMinimalHUD::NativeConstruct()
{
	Super::NativeConstruct();
	LastGradeText = TEXT("");
	GradeFlashTimer = 0.0f;
}

void UMelodiaMinimalHUD::NativeTick(const FGeometry& MyGeometry, const float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (GradeFlashTimer > 0.0f)
	{
		GradeFlashTimer -= InDeltaTime;
		if (GradeFlashTimer <= 0.0f)
		{
			LastGradeText.Reset();
		}
	}
}

void UMelodiaMinimalHUD::FlashGrade(const FString& GradeString, FLinearColor Color)
{
	LastGradeText = GradeString;
	LastGradeColor = Color;
	GradeFlashTimer = 1.5f;
}

void UMelodiaMinimalHUD::DrawBar(FPaintContext& InContext, const FVector2D& Position, const FVector2D& Size,
	const float FillRatio, const FLinearColor FillColor, const FLinearColor BackColor, const FString& Label) const
{
	// Background
	UWidgetBlueprintLibrary::DrawBox(InContext, Position, Size, nullptr, BackColor);

	// Fill
	const float ClampedFill = FMath::Clamp(FillRatio, 0.0f, 1.0f);
	const FVector2D FillSize(Size.X * ClampedFill, Size.Y);
	UWidgetBlueprintLibrary::DrawBox(InContext, Position, FillSize, nullptr, FillColor);

	// Label
	if (!bFontCached)
	{
		CachedFont = FSlateFontInfo(FPaths::EngineContentDir() / TEXT("Slate/Fonts/Roboto-Regular.ttf"), 14);
		bFontCached = true;
	}

	const FVector2D TextPos(Position.X + 4.0f, Position.Y + 1.0f);
	UWidgetBlueprintLibrary::DrawTextFormatted(InContext, FText::FromString(Label), TextPos, nullptr, 14, FName(), FLinearColor::White);
}

int32 UMelodiaMinimalHUD::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements, const int32 LayerId, const FWidgetStyle& InWidgetStyle, const bool bParentEnabled) const
{
	const int32 SuperLayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	FPaintContext InContext(AllottedGeometry, MyCullingRect, OutDrawElements, SuperLayerId, InWidgetStyle, bParentEnabled);

	const UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this);
	if (!Session)
	{
		return SuperLayerId;
	}

	const EMelodiaBattlePhase Phase = Session->GetBattlePhase();

	// Only draw during active encounters
	if (Phase == EMelodiaBattlePhase::None)
	{
		return SuperLayerId;
	}

	if (!bFontCached)
	{
		CachedFont = FSlateFontInfo(FPaths::EngineContentDir() / TEXT("Slate/Fonts/Roboto-Regular.ttf"), 14);
		bFontCached = true;
	}

	// --- Layout constants ---
	constexpr float LeftMargin = 30.0f;
	constexpr float TopMargin = 30.0f;
	constexpr float BarWidth = 220.0f;
	constexpr float BarHeight = 22.0f;
	constexpr float VerticalSpacing = 8.0f;
	float CurrentY = TopMargin;

	// --- Semi-transparent panel background ---
	const FVector2D PanelPos(LeftMargin - 10.0f, TopMargin - 10.0f);
	const FVector2D PanelSize(BarWidth + 20.0f, 260.0f);
	UWidgetBlueprintLibrary::DrawBox(InContext, PanelPos, PanelSize, nullptr,
		FLinearColor(0.05f, 0.03f, 0.1f, 0.75f));

	// --- Phase indicator ---
	const FString PhaseText = FString::Printf(TEXT("[ %s ]"),
		*StaticEnum<EMelodiaBattlePhase>()->GetDisplayNameTextByValue(static_cast<int64>(Phase)).ToString());
	FLinearColor PhaseColor = FLinearColor::White;
	if (Phase == EMelodiaBattlePhase::Victory)
	{
		PhaseColor = FLinearColor(0.2f, 1.0f, 0.4f);
	}
	else if (Phase == EMelodiaBattlePhase::Defeat)
	{
		PhaseColor = FLinearColor(1.0f, 0.2f, 0.2f);
	}
	else if (Phase == EMelodiaBattlePhase::RhythmExecution)
	{
		PhaseColor = FLinearColor(0.4f, 0.7f, 1.0f);
	}
	UWidgetBlueprintLibrary::DrawTextFormatted(InContext, FText::FromString(PhaseText),
		FVector2D(LeftMargin, CurrentY), nullptr, 16, FName(), PhaseColor);
	CurrentY += BarHeight + VerticalSpacing;

	// --- Enemy HP bar ---
	const float EnemyHPRatio = Session->EnemyMaxHP > 0.0f ? Session->EnemyHP / Session->EnemyMaxHP : 0.0f;
	const FString EnemyLabel = FString::Printf(TEXT("Enemy HP: %.0f / %.0f"), Session->EnemyHP, Session->EnemyMaxHP);
	const_cast<UMelodiaMinimalHUD*>(this)->DrawBar(InContext,
		FVector2D(LeftMargin, CurrentY), FVector2D(BarWidth, BarHeight),
		EnemyHPRatio, FLinearColor(0.85f, 0.15f, 0.15f), FLinearColor(0.2f, 0.05f, 0.05f, 0.8f), EnemyLabel);
	CurrentY += BarHeight + VerticalSpacing;

	// --- Party HP bar ---
	const UMelodiaCombatStateComponent* CombatState = Session->GetCombatState();
	if (CombatState)
	{
		const float PartyHPRatio = CombatState->PartyMaxHP > 0.0f ? CombatState->PartyHP / CombatState->PartyMaxHP : 0.0f;
		const FString PartyLabel = FString::Printf(TEXT("Party HP: %.0f / %.0f"), CombatState->PartyHP, CombatState->PartyMaxHP);
		const_cast<UMelodiaMinimalHUD*>(this)->DrawBar(InContext,
			FVector2D(LeftMargin, CurrentY), FVector2D(BarWidth, BarHeight),
			PartyHPRatio, FLinearColor(0.15f, 0.7f, 0.3f), FLinearColor(0.05f, 0.15f, 0.05f, 0.8f), PartyLabel);
		CurrentY += BarHeight + VerticalSpacing;

		// --- SP indicator ---
		const FString SPLabel = FString::Printf(TEXT("SP: %d / %d"), CombatState->SkillPoints, CombatState->SkillPointMax);
		const float SPRatio = CombatState->SkillPointMax > 0 ? static_cast<float>(CombatState->SkillPoints) / static_cast<float>(CombatState->SkillPointMax) : 0.0f;
		const_cast<UMelodiaMinimalHUD*>(this)->DrawBar(InContext,
			FVector2D(LeftMargin, CurrentY), FVector2D(BarWidth, BarHeight),
			SPRatio, FLinearColor(0.3f, 0.5f, 1.0f), FLinearColor(0.05f, 0.05f, 0.2f, 0.8f), SPLabel);
		CurrentY += BarHeight + VerticalSpacing;

		// --- Crescendo / Ultimate gauge ---
		const float UltRatio = CombatState->UltimateMax > 0.0f ? CombatState->UltimateGauge / CombatState->UltimateMax : 0.0f;
		const FLinearColor UltColor = CombatState->bUltimateReady
			? FLinearColor(1.0f, 0.85f, 0.2f)
			: FLinearColor(0.6f, 0.4f, 0.15f);
		const FString UltLabel = CombatState->bUltimateReady
			? TEXT("ULTIMATE READY! [R]")
			: FString::Printf(TEXT("Crescendo: %.0f / %.0f"), CombatState->UltimateGauge, CombatState->UltimateMax);
		const_cast<UMelodiaMinimalHUD*>(this)->DrawBar(InContext,
			FVector2D(LeftMargin, CurrentY), FVector2D(BarWidth, BarHeight),
			UltRatio, UltColor, FLinearColor(0.1f, 0.08f, 0.02f, 0.8f), UltLabel);
		CurrentY += BarHeight + VerticalSpacing;

		// --- Enemy toughness / break ---
		if (CombatState->EnemyToughnessMax > 0.0f)
		{
			const float ToughRatio = CombatState->EnemyToughness / CombatState->EnemyToughnessMax;
			const FLinearColor ToughColor = CombatState->bEnemyBroken
				? FLinearColor(1.0f, 0.5f, 0.0f)
				: FLinearColor(0.5f, 0.5f, 0.6f);
			const FString ToughLabel = CombatState->bEnemyBroken
				? TEXT("BROKEN!")
				: FString::Printf(TEXT("Toughness: %.0f / %.0f"), CombatState->EnemyToughness, CombatState->EnemyToughnessMax);
			const_cast<UMelodiaMinimalHUD*>(this)->DrawBar(InContext,
				FVector2D(LeftMargin, CurrentY), FVector2D(BarWidth, BarHeight),
				ToughRatio, ToughColor, FLinearColor(0.1f, 0.1f, 0.1f, 0.8f), ToughLabel);
			CurrentY += BarHeight + VerticalSpacing;
		}
	}

	// --- Grade flash feedback ---
	if (!LastGradeText.IsEmpty() && GradeFlashTimer > 0.0f)
	{
		const float Alpha = FMath::Clamp(GradeFlashTimer / 1.5f, 0.0f, 1.0f);
		FLinearColor FadeColor = LastGradeColor;
		FadeColor.A = Alpha;

		FSlateFontInfo LargeFont = CachedFont;
		LargeFont.Size = 28;
		UWidgetBlueprintLibrary::DrawTextFormatted(InContext, FText::FromString(LastGradeText),
			FVector2D(LeftMargin + BarWidth + 40.0f, TopMargin + 40.0f), nullptr, 28, FName(), FadeColor);
	}

	// --- Input hint (only when awaiting command) ---
	if (Phase == EMelodiaBattlePhase::AwaitingPlayerCommand)
	{
		const float BreakMultiplier = CombatState && CombatState->bEnemyBroken
			? MelodiaRulesGen::ToughnessBrokenEnemyDamageMult
			: 1.0f;
		const float IntentDamage = Session->ActiveEnemyIntentDamage * BreakMultiplier;
		const FString IntentName = Session->ActiveEnemyIntentName.IsEmpty()
			? TEXT("Strike")
			: Session->ActiveEnemyIntentName.ToString();
		const FString IntentText = CombatState && CombatState->bEnemyBroken
			? FString::Printf(TEXT("Enemy intent: WEAKENED %s %.0f"), *IntentName, IntentDamage)
			: FString::Printf(TEXT("Enemy intent: %s %.0f"), *IntentName, IntentDamage);
		UWidgetBlueprintLibrary::DrawTextFormatted(InContext, FText::FromString(IntentText),
			FVector2D(LeftMargin, CurrentY + 8.0f), nullptr, 13, FName(), FLinearColor(1.0f, 0.72f, 0.42f, 0.95f));

		const FString HintText = TEXT("[1] Basic (+1 SP)  [2] Skill (-1 SP)  [R] Crescendo  [Tab] Cycle  [Esc] Flee");
		UWidgetBlueprintLibrary::DrawTextFormatted(InContext, FText::FromString(HintText),
			FVector2D(LeftMargin, CurrentY + 28.0f), nullptr, 12, FName(), FLinearColor(0.8f, 0.82f, 0.9f, 0.9f));
	}
	else if (Phase == EMelodiaBattlePhase::Victory)
	{
		const FString VictoryText = TEXT("VICTORY! Press [Space] to continue.");
		FSlateFontInfo VictoryFont = CachedFont;
		VictoryFont.Size = 20;
		UWidgetBlueprintLibrary::DrawTextFormatted(InContext, FText::FromString(VictoryText),
			FVector2D(LeftMargin, CurrentY + 10.0f), nullptr, 20, FName(), FLinearColor(0.2f, 1.0f, 0.4f));
	}
	else if (Phase == EMelodiaBattlePhase::Defeat)
	{
		const FString DefeatText = TEXT("DEFEAT. Press [Esc] to flee.");
		FSlateFontInfo DefeatFont = CachedFont;
		DefeatFont.Size = 20;
		UWidgetBlueprintLibrary::DrawTextFormatted(InContext, FText::FromString(DefeatText),
			FVector2D(LeftMargin, CurrentY + 10.0f), nullptr, 20, FName(), FLinearColor(1.0f, 0.2f, 0.2f));
	}

	return InContext.MaxLayer;
}
