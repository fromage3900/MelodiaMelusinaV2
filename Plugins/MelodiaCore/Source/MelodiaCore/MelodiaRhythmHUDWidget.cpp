// Native rhythm HUD ΓÇö NativePaint rendering of battle elements.
// Adapted from MelodiaMelusina_PROD ΓÇö battle-only rendering.

#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaSmokeCharacter.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Blueprint/WidgetTree.h"
#include "MelodiaBattleSession.h"
#include "MelodiaCombatStateComponent.h"
#include "MelodiaRhythmExecutionComponent.h"
#include "Engine/Texture2D.h"
#include "UObject/UObjectIterator.h"

namespace
{
	FSlateBrush MakeTextureBrush(UTexture2D* Texture)
	{
		FSlateBrush Brush;
		Brush.SetResourceObject(Texture);
		return Brush;
	}

	// HL1-HL5 cue palette. Same design tokens the note boxes already use, so a grade
	// reads identically whether it is a note, a ring, or the judgement pop.
	FLinearColor GradeColor(const EMelodiaRhythmGrade Grade, const float Alpha)
	{
		switch (Grade)
		{
		case EMelodiaRhythmGrade::Perfect: return FLinearColor(0.368627f, 0.545098f, 0.494118f, Alpha); // feedback.success
		case EMelodiaRhythmGrade::Great:   return FLinearColor(0.541176f, 0.662745f, 0.839216f, Alpha); // accent.astral
		case EMelodiaRhythmGrade::Good:    return FLinearColor(0.721569f, 0.525490f, 0.184314f, Alpha); // feedback.warning
		default:                           return FLinearColor(0.658824f, 0.341176f, 0.317647f, Alpha); // feedback.error
		}
	}

	/** The judgement arrives as text (SetJudgment); this is the widget's only grade source. */
	EMelodiaRhythmGrade GradeFromText(const FString& Text)
	{
		if (Text.Contains(TEXT("Perfect"), ESearchCase::IgnoreCase)) { return EMelodiaRhythmGrade::Perfect; }
		if (Text.Contains(TEXT("Great"), ESearchCase::IgnoreCase))   { return EMelodiaRhythmGrade::Great; }
		if (Text.Contains(TEXT("Good"), ESearchCase::IgnoreCase))    { return EMelodiaRhythmGrade::Good; }
		return EMelodiaRhythmGrade::Miss;
	}

	/** Four thin boxes = a ring. Slate has no ring primitive and a filled box would read
	 *  as another note, which is exactly the confusion HL2 is meant to remove. */
	void PaintRing(FSlateWindowElementList& OutDrawElements, const FGeometry& Geometry, const int32 Layer,
		const FVector2D Center, const float Size, const float Thickness, const FLinearColor Color,
		const FSlateBrush& Brush)
	{
		const float Half = Size * 0.5f;
		const FVector2D Origin(Center.X - Half, Center.Y - Half);
		FSlateDrawElement::MakeBox(OutDrawElements, Layer, Geometry.ToPaintGeometry(FVector2D(Size, Thickness), FSlateLayoutTransform(Origin)), &Brush, ESlateDrawEffect::None, Color);
		FSlateDrawElement::MakeBox(OutDrawElements, Layer, Geometry.ToPaintGeometry(FVector2D(Size, Thickness), FSlateLayoutTransform(FVector2D(Origin.X, Origin.Y + Size - Thickness))), &Brush, ESlateDrawEffect::None, Color);
		FSlateDrawElement::MakeBox(OutDrawElements, Layer, Geometry.ToPaintGeometry(FVector2D(Thickness, Size), FSlateLayoutTransform(Origin)), &Brush, ESlateDrawEffect::None, Color);
		FSlateDrawElement::MakeBox(OutDrawElements, Layer, Geometry.ToPaintGeometry(FVector2D(Thickness, Size), FSlateLayoutTransform(FVector2D(Origin.X + Size - Thickness, Origin.Y))), &Brush, ESlateDrawEffect::None, Color);
	}
}

UMelodiaRhythmHUDWidget* UMelodiaRhythmHUDWidget::FindFirst(const UObject* WorldContextObject)
{
	if (!WorldContextObject)
	{
		return nullptr;
	}

	for (TObjectIterator<UMelodiaRhythmHUDWidget> It; It; ++It)
	{
		if (It->GetWorld() == WorldContextObject->GetWorld() && It->IsInViewport())
		{
			return *It;
		}
	}
	return nullptr;
}

float UMelodiaRhythmHUDWidget::GetHUDTimeSeconds() const
{
	if (const UWorld* World = GetWorld())
	{
		return World->GetRealTimeSeconds();
	}
	return 0.0f;
}

void UMelodiaRhythmHUDWidget::NativeConstruct()
{
	Super::NativeConstruct();
	LoadPresentationTextures();
}

void UMelodiaRhythmHUDWidget::LoadPresentationTextures()
{
	// Deprecated Batch N naming (HighwayBG/Hitline/NoteHead/NoteHeadBeam/FiligreeCorner) retired
	// 2026-07-16 per my-site-clean/generated/assets/melodia-game-ui/ART_SOURCE.json's
	// deprecated_batch_n.replacement map -- highway/notes now come from the SoftMG kit, filigree
	// from FiligreeBatchO_Baroque's CornerBaroque.
	HighwayBackgroundTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment.T_Melodia_SoftMG_Parchment"));
	HitLineTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Hitline.T_Melodia_SoftMG_Hitline"));
	NoteHeadTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_SealSP.T_Melodia_SoftMG_SealSP"));
	NoteHeadBeamTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Hitline.T_Melodia_SoftMG_Hitline"));
	FiligreeCornerTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_FiligreeCornerBaroque.T_Melodia_FiligreeCornerBaroque"));
	EnemyGlowTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_EnemyGlow.T_Melodia_EnemyGlow"));
	SkillChipTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SkillChipBG.T_Melodia_SkillChipBG"));
	GradePerfectTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_GradePerfect.T_Melodia_GradePerfect"));
	GradeGreatTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_GradeGreat.T_Melodia_GradeGreat"));
	GradeGoodTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_GradeGood.T_Melodia_GradeGood"));
	GradeMissTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_GradeMiss.T_Melodia_GradeMiss"));
}

void UMelodiaRhythmHUDWidget::NativeTick(const FGeometry& MyGeometry, const float InDeltaTime)
{
		Super::NativeTick(MyGeometry, InDeltaTime);

	UpdateSmoothedBars(InDeltaTime);

    // Sync sprint and glide flags from character
    if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
    {
        if (APawn* Pawn = PC->GetPawn())
        {
            if (AMelodiaSmokeCharacter* Char = Cast<AMelodiaSmokeCharacter>(Pawn))
            {
                SetSprintGlide(Char->bIsSprinting, Char->bIsGliding);
            }
        }
    }

	// Prune expired floating combat texts (>2 seconds old)
	const float CurrentTime = GetHUDTimeSeconds();
	FloatingCombatTexts.RemoveAll([CurrentTime](const FMelodiaFloatingCombatText& FCT)
	{
		return CurrentTime - FCT.SpawnTime > 2.0f;
	});

	// Auto-sync from battle session
	if (UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this))
	{
		SetEnemyVitals(Session->EnemyHP, Session->EnemyMaxHP);
		// A directly-driven note highway owns the presentation mode for its
		// lifetime. The ambient MelodiaBattleSession remains in Exploration while
		// the stock JRPG adapter is active; copying that mode every Slate tick made
		// a healthy, populated highway disappear from NativePaint.
		if (!bNoteHighwayActive)
		{
			SetHUDMode(Session->HUDMode);
		}

		if (UMelodiaCombatStateComponent* CombatState = Session->GetCombatState())
		{
			SetPartyVitals(CombatState->PartyHP, CombatState->PartyMaxHP);
			SetSkillPoints(CombatState->SkillPoints, CombatState->SkillPointMax);
			SetUltimateGauge(CombatState->UltimateGauge, CombatState->UltimateMax, CombatState->bUltimateReady);
			SetEnemyBreakGauge(CombatState->EnemyToughness, CombatState->EnemyToughnessMax, CombatState->bEnemyBroken);
		}

		if (const AActor* BattleController = Session->GetBattleController())
		{
			if (const UMelodiaRhythmExecutionComponent* Execution = BattleController->FindComponentByClass<UMelodiaRhythmExecutionComponent>())
			{
				const bool bExecutionActive = Execution->IsExecutionActive();
				TArray<FMelodiaHighwayNote> LiveHighwayNotes;
				float BeatPosition = 0.0f;
				float ScrollBeatsAhead = 2.5f;
				if (bExecutionActive)
				{
					LiveHighwayNotes = Execution->ActiveNotes;
					BeatPosition = Execution->GetCurrentBeatPosition();
					ScrollBeatsAhead = Execution->ScrollBeatsAhead;
				}

				// Only the execution component owns this synchronization lane. Other
				// gameplay integrations (including the stock JRPG rhythm subsystem)
				// drive the same native-painted highway directly. An unconditional
				// clear every tick merely because a MelodiaBattleSession exists erased
				// their live notes immediately after SetNoteHighwayActive(true, ...),
				// so the deactivation clear is gated on this lane being the writer.
				if (bExecutionActive)
				{
					SetNoteHighwayActive(true, LiveHighwayNotes, BeatPosition, ScrollBeatsAhead);
					bExecutionDrivingHighway = true;
				}
				else if (bExecutionDrivingHighway)
				{
					SetNoteHighwayActive(false, LiveHighwayNotes, BeatPosition, ScrollBeatsAhead);
					bExecutionDrivingHighway = false;
				}
			}
		}
	}
}

void UMelodiaRhythmHUDWidget::UpdateSmoothedBars(const float InDeltaTime)
{
	const float LerpSpeed = 8.0f;

	if (!bDisplayedValuesInitialized)
	{
		DisplayedEnemyHP = LastEnemyHP;
		DisplayedPartyHP = LastPartyHP;
		DisplayedUltimate = LastUltimateGaugeValue;
		DisplayedEnemyToughness = LastEnemyToughness;
		bDisplayedValuesInitialized = true;
		return;
	}

	DisplayedEnemyHP = FMath::FInterpTo(DisplayedEnemyHP, LastEnemyHP, InDeltaTime, LerpSpeed);
	DisplayedPartyHP = FMath::FInterpTo(DisplayedPartyHP, LastPartyHP, InDeltaTime, LerpSpeed);
	DisplayedUltimate = FMath::FInterpTo(DisplayedUltimate, LastUltimateGaugeValue, InDeltaTime, LerpSpeed);
	DisplayedEnemyToughness = FMath::FInterpTo(DisplayedEnemyToughness, LastEnemyToughness, InDeltaTime, LerpSpeed);
}

int32 UMelodiaRhythmHUDWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);

	if (ActiveHUDMode == EMelodiaHUDMode::Exploration)
	{
		return LayerId;
	}

	int32 CurrentLayer = LayerId;

	// Cast away const for painting helpers (Slate pattern ΓÇö NativePaint is const but we need to update paint counters)
	const_cast<UMelodiaRhythmHUDWidget*>(this)->PaintBattleHUD(OutDrawElements, AllottedGeometry, CurrentLayer);

	if (bNoteHighwayActive)
	{
		const_cast<UMelodiaRhythmHUDWidget*>(this)->PaintNoteHighway(OutDrawElements, AllottedGeometry, CurrentLayer);
	}

	const_cast<UMelodiaRhythmHUDWidget*>(this)->PaintFloatingCombatTexts(OutDrawElements, AllottedGeometry, CurrentLayer);

	return CurrentLayer;
}

void UMelodiaRhythmHUDWidget::PaintBattleHUD(FSlateWindowElementList& OutDrawElements, const FGeometry& AllottedGeometry, int32& CurrentLayer) const
{
	const FVector2D LocalSize = AllottedGeometry.GetLocalSize();
	const float W = LocalSize.X;
	const float H = LocalSize.Y;
	const FSlateBrush WhiteBrush;
	const FSlateBrush FiligreeBrush = MakeTextureBrush(FiligreeCornerTexture);

	// --- Enemy HP bar (top center) ---
	{
		const float BarX = W * 0.25f;
		const float BarY = H * 0.04f;
		const float BarW = W * 0.50f;
		const float BarH = 18.0f;
		const float HPFraction = LastEnemyMaxHP > 0.0f ? FMath::Clamp(DisplayedEnemyHP / LastEnemyMaxHP, 0.0f, 1.0f) : 0.0f;
		if (FiligreeCornerTexture)
		{
			FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer,
				AllottedGeometry.ToPaintGeometry(FVector2D(42.0f, 42.0f), FSlateLayoutTransform(FVector2D(BarX - 22.0f, BarY - 13.0f))),
				&FiligreeBrush, ESlateDrawEffect::None, FiligreeTint);
		}

		// Background
		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			FLinearColor(0.109804f, 0.078431f, 0.149020f, 0.85f)); // surface.sunken

		// Fill
		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW * HPFraction, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			EnemyHPBarTint);

		// Sprint indicator (green square)
		if (bIsSprinting)
		{
			const float IconSize = 12.0f;
			const FVector2D IconPos(BarX - IconSize - 4.0f, BarY);
			FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 2,
				AllottedGeometry.ToPaintGeometry(FVector2D(IconSize, IconSize), FSlateLayoutTransform(IconPos)),
				&WhiteBrush, ESlateDrawEffect::None, FLinearColor(0.368627f, 0.545098f, 0.494118f, 0.9f)); // feedback.success
		}

		// Glide indicator (blue square)
		if (bIsGliding)
		{
			const float IconSize = 12.0f;
			const FVector2D IconPos(BarX + BarW + 4.0f, BarY);
			FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 2,
				AllottedGeometry.ToPaintGeometry(FVector2D(IconSize, IconSize), FSlateLayoutTransform(IconPos)),
				&WhiteBrush, ESlateDrawEffect::None, FLinearColor(0.541176f, 0.662745f, 0.839216f, 0.9f)); // accent.astral
		}
	}
	

	// --- Party HP bar (bottom left) ---
	{
		const float BarX = W * 0.03f;
		const float BarY = H * 0.90f;
		const float BarW = W * 0.25f;
		const float BarH = 14.0f;
		const float HPFraction = LastPartyMaxHP > 0.0f ? FMath::Clamp(DisplayedPartyHP / LastPartyMaxHP, 0.0f, 1.0f) : 0.0f;

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			FLinearColor(0.109804f, 0.078431f, 0.149020f, 0.85f)); // surface.sunken

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW * HPFraction, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			PartyHPBarTint);
	}

	// --- SP dots (bottom left, below HP) ---
	{
		const float DotY = H * 0.94f;
		const float DotSize = 10.0f;
		const float DotSpacing = 14.0f;
		const float DotStartX = W * 0.03f;
		for (int32 Index = 0; Index < LastSkillPointMax; ++Index)
		{
			const bool bFilled = Index < LastSkillPoints;
			FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
				AllottedGeometry.ToPaintGeometry(FVector2D(DotSize, DotSize), FSlateLayoutTransform(FVector2D(DotStartX + Index * DotSpacing, DotY))),
				&WhiteBrush, ESlateDrawEffect::None,
				bFilled ? FLinearColor(0.541176f, 0.662745f, 0.839216f, 0.95f) // accent.astral
				        : FLinearColor(0.109804f, 0.078431f, 0.149020f, 0.6f)); // surface.sunken
		}
	}

	// --- Ultimate gauge (bottom right) ---
	{
		const float BarX = W * 0.72f;
		const float BarY = H * 0.92f;
		const float BarW = W * 0.25f;
		const float BarH = 10.0f;
		const float UltFraction = LastUltimateGaugeMax > 0.0f ? FMath::Clamp(DisplayedUltimate / LastUltimateGaugeMax, 0.0f, 1.0f) : 0.0f;

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			FLinearColor(0.109804f, 0.078431f, 0.149020f, 0.7f)); // surface.sunken

		const FLinearColor GaugeFill = bUltimateReadyVisible
			? FLinearColor(0.788235f, 0.658824f, 0.415686f, 1.0f) // accent.primary / gold.500, ready
			: UltimateGaugeTint;

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW * UltFraction, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			GaugeFill);
	}

	// --- Break gauge (below enemy HP) ---
	{
		const float BarX = W * 0.35f;
		const float BarY = H * 0.04f + 22.0f;
		const float BarW = W * 0.30f;
		const float BarH = 6.0f;
		const float ToughFraction = LastEnemyToughnessMax > 0.0f ? FMath::Clamp(DisplayedEnemyToughness / LastEnemyToughnessMax, 0.0f, 1.0f) : 0.0f;

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			FLinearColor(0.109804f, 0.078431f, 0.149020f, 0.6f)); // surface.sunken

		const FLinearColor ToughFill = bEnemyBreakVisible
			? FLinearColor(0.658824f, 0.341176f, 0.317647f, 1.0f) // feedback.error, broken
			: BreakGaugeTint;

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW * ToughFraction, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			ToughFill);
	}

	// --- Judgment text (center): HL1 -- beat-locked grade pop ---
	{
		// The pop owns its timestamp now. It used to read LastPulseTime, which DoPulse
		// rewrites on every beat, so a beat landing mid-pop restarted the fade and every
		// judgement appeared to linger and flicker.
		const float PopAge = GetHUDTimeSeconds() - LastGradePopTime;
		const float Motion = GetMotionAmplitude();
		// Beat-locked timeline scaled by the live tempo (117 / 234 / 469 / 703 ms at 128 BPM):
		// 0-1/8 anticipation to overshoot, 1/8-1/4 settle to rest, hold to the beat, fade.
		const float AnticipateEnd = FMath::Max(0.03f, SecondsPerBeat * 0.25f);
		const float SettleEnd = AnticipateEnd * 2.0f;
		const float HoldEnd = FMath::Max(SettleEnd + 0.03f, SecondsPerBeat);
		const float FadeEnd = HoldEnd + FMath::Max(0.05f, SecondsPerBeat * 0.5f);

		if (PopAge >= 0.0f && PopAge < FadeEnd && !LastJudgmentText.IsEmpty())
		{
			float Scale = 1.0f;
			float Alpha = 1.0f;
			if (PopAge < AnticipateEnd)
			{
				Scale = FMath::Lerp(0.85f, 1.18f, PopAge / AnticipateEnd);
			}
			else if (PopAge < SettleEnd)
			{
				Scale = FMath::Lerp(1.18f, 1.0f, (PopAge - AnticipateEnd) / (SettleEnd - AnticipateEnd));
			}
			else if (PopAge >= HoldEnd)
			{
				Alpha = FMath::Clamp(1.0f - (PopAge - HoldEnd) / (FadeEnd - HoldEnd), 0.0f, 1.0f);
			}
			// MotionTier=Off keeps the text readable and drops the motion, matching the
			// rest of the cue set.
			Scale = 1.0f + (Scale - 1.0f) * Motion;

			const FVector2D PopCenter(W * 0.5f, H * 0.45f);
			const FLinearColor PopColor = GradeColor(LastPopGrade, Alpha);

			// Perfect adds a ring flash that expands with the pop and is gone by the settle.
			if (LastPopGrade == EMelodiaRhythmGrade::Perfect && PopAge < SettleEnd)
			{
				const float RingT = FMath::Clamp(PopAge / SettleEnd, 0.0f, 1.0f);
				PaintRing(OutDrawElements, AllottedGeometry, CurrentLayer + 1, PopCenter,
					150.0f * Scale * (1.0f + 0.5f * RingT),
					FMath::Max(1.0f, 3.0f * (1.0f - RingT)),
					GradeColor(EMelodiaRhythmGrade::Perfect, Alpha * (1.0f - RingT) * 0.8f),
					WhiteBrush);
			}

			UTexture2D* GradeTexture = nullptr;
			const FString GradeText = LastJudgmentText.ToString();
			if (GradeText.Equals(TEXT("Perfect"), ESearchCase::IgnoreCase)) GradeTexture = GradePerfectTexture;
			else if (GradeText.Equals(TEXT("Great"), ESearchCase::IgnoreCase)) GradeTexture = GradeGreatTexture;
			else if (GradeText.Equals(TEXT("Good"), ESearchCase::IgnoreCase)) GradeTexture = GradeGoodTexture;
			else if (GradeText.Equals(TEXT("Miss"), ESearchCase::IgnoreCase)) GradeTexture = GradeMissTexture;

			if (GradeTexture)
			{
				const FSlateBrush GradeBrush = MakeTextureBrush(GradeTexture);
				const FVector2D GradeSize(220.0f * Scale, 64.0f * Scale);
				FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 2,
					AllottedGeometry.ToPaintGeometry(GradeSize, FSlateLayoutTransform(FVector2D(PopCenter.X - GradeSize.X * 0.5f, PopCenter.Y - GradeSize.Y * 0.5f))),
					&GradeBrush, ESlateDrawEffect::None, FLinearColor(1.0f, 1.0f, 1.0f, Alpha));
			}
			else
			{
				const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", FMath::RoundToInt(28.0f * Scale));
				FSlateDrawElement::MakeText(OutDrawElements, CurrentLayer + 2,
					AllottedGeometry.ToPaintGeometry(FVector2D(200.0f, 40.0f), FSlateLayoutTransform(FVector2D(PopCenter.X - 100.0f, PopCenter.Y - 20.0f))),
					GradeText, Font, ESlateDrawEffect::None, PopColor);
			}
		}
	}

	// --- Battle phase banner (top center, fades) ---
	{
		const float TimeSinceBanner = GetHUDTimeSeconds() - LastBannerTime;
		if (TimeSinceBanner < 3.0f && !LastBattlePhaseLabel.IsEmpty())
		{
			const float Alpha = FMath::Clamp(1.0f - TimeSinceBanner / 3.0f, 0.0f, 1.0f);
			const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", 22);

			FSlateDrawElement::MakeText(OutDrawElements, CurrentLayer + 2,
				AllottedGeometry.ToPaintGeometry(FVector2D(300.0f, 36.0f), FSlateLayoutTransform(FVector2D(W * 0.5f - 150.0f, H * 0.12f))),
				LastBattlePhaseLabel,
				Font, ESlateDrawEffect::None,
				FLinearColor(FiligreeTint.R, FiligreeTint.G, FiligreeTint.B, Alpha));
		}
	}

	// --- Action prompt (bottom center) ---
	if (!LastBattleStatusText.IsEmpty() && ActiveHUDMode != EMelodiaHUDMode::Exploration)
	{
		const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", 15);
		FSlateDrawElement::MakeText(OutDrawElements, CurrentLayer + 2,
			AllottedGeometry.ToPaintGeometry(FVector2D(W * 0.7f, 28.0f), FSlateLayoutTransform(FVector2D(W * 0.15f, H * 0.875f))),
			LastBattleStatusText,
			Font, ESlateDrawEffect::None,
			FLinearColor(0.988235f, 0.984314f, 0.972549f, 0.95f)); // text.primary
	}

	if (!LastActionPromptText.IsEmpty() && ActiveHUDMode != EMelodiaHUDMode::Exploration)
	{
		const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Regular", 14);
		FSlateDrawElement::MakeText(OutDrawElements, CurrentLayer + 2,
			AllottedGeometry.ToPaintGeometry(FVector2D(W * 0.6f, 24.0f), FSlateLayoutTransform(FVector2D(W * 0.2f, H * 0.96f))),
			LastActionPromptText,
			Font, ESlateDrawEffect::None,
			FLinearColor(0.682353f, 0.705882f, 0.749020f, 0.9f)); // text.secondary
	}

	// --- Damage flash overlay ---
	{
		const float TimeSinceFlash = GetHUDTimeSeconds() - LastDamageFlashTime;
		if (TimeSinceFlash < 0.3f)
		{
			const float Alpha = FMath::Clamp(1.0f - TimeSinceFlash / 0.3f, 0.0f, 1.0f) * 0.35f;
			FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 3,
				AllottedGeometry.ToPaintGeometry(FVector2D(W, H), FSlateLayoutTransform(FVector2D::ZeroVector)),
				&WhiteBrush, ESlateDrawEffect::None,
				FLinearColor(0.658824f, 0.341176f, 0.317647f, Alpha)); // feedback.error
		}
	}

	CurrentLayer += 4;
}

void UMelodiaRhythmHUDWidget::PaintNoteHighway(FSlateWindowElementList& OutDrawElements, const FGeometry& AllottedGeometry, int32& CurrentLayer) const
{
	const FVector2D LocalSize = AllottedGeometry.GetLocalSize();
	const float W = LocalSize.X;
	const float H = LocalSize.Y;
	const FSlateBrush WhiteBrush;
	const FSlateBrush HighwayBrush = MakeTextureBrush(HighwayBackgroundTexture);
	const FSlateBrush HitLineBrush = MakeTextureBrush(HitLineTexture);
	const FSlateBrush NoteBrush = MakeTextureBrush(NoteHeadTexture);

	// Lanes are columns above the UMG LaneRow, and notes fall DOWN onto their key.
	// Previously every note drew at one Y with LaneIndex ignored, which made a
	// four-lane chart unreadable — the note carried no indication of which key it was.
	const int32 LaneCount = FMath::Max(1, HighwayLaneCount);
	const float RowWidth = FMath::Min(HighwayLaneRowWidth, W);
	const float LaneW = RowWidth / static_cast<float>(LaneCount);
	const float RowLeft = (W - RowWidth) * 0.5f;
	const float HitLineY = H - HighwayHitLineFromBottom;
	const float TopY = FMath::Max(0.0f, HitLineY - HighwayApproachHeight);
	const float ApproachH = HitLineY - TopY;

	// HL4: the hit line pulses on the beat. Phase comes from the beat position the driver
	// already pushes -- the same music clock the orrery chassis reads -- so this adds no
	// second audio reader. The pulse decays over 1/8 note at the current BPM: a heartbeat,
	// not a strobe.
	const float Motion = GetMotionAmplitude();
	const float Now = GetHUDTimeSeconds();
	const float BeatPhase = HighwayBeatPosition - FMath::FloorToFloat(HighwayBeatPosition);
	const float PulseDecay = FMath::Max(0.03f, SecondsPerBeat * 0.25f);
	const float Pulse = Motion * FMath::Clamp(1.0f - (BeatPhase * SecondsPerBeat) / PulseDecay, 0.0f, 1.0f);

	// HL2: lane columns. At rest they alternate shade; for 1/8 note after a hit, the lane
	// the player just cleared flashes in its grade colour, so the flash and the ring agree
	// about what happened.
	const float LaneFlashLife = FMath::Max(0.04f, SecondsPerBeat * 0.25f);
	for (int32 Lane = 0; Lane < LaneCount; ++Lane)
	{
		const float LaneX = RowLeft + Lane * LaneW;
		// Alternate tint so adjacent lanes stay distinguishable without a divider mesh.
		const float Shade = (Lane % 2 == 0) ? 0.8f : 0.66f;
		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer,
			AllottedGeometry.ToPaintGeometry(FVector2D(LaneW - 2.0f, ApproachH), FSlateLayoutTransform(FVector2D(LaneX + 1.0f, TopY))),
			HighwayBackgroundTexture ? &HighwayBrush : &WhiteBrush, ESlateDrawEffect::None,
			FLinearColor(0.06f, 0.04f, 0.1f, Shade));

		if (LaneFlashTimes.IsValidIndex(Lane))
		{
			const float FlashAge = Now - LaneFlashTimes[Lane];
			if (FlashAge >= 0.0f && FlashAge < LaneFlashLife)
			{
				FLinearColor FlashColor = SparkleTint;
				for (int32 BurstIndex = HighwayBursts.Num() - 1; BurstIndex >= 0; --BurstIndex)
				{
					if (HighwayBursts[BurstIndex].LaneIndex == Lane)
					{
						FlashColor = GradeColor(HighwayBursts[BurstIndex].Grade, 1.0f);
						break;
					}
				}

				const float FlashAlpha = Motion * (1.0f - FlashAge / LaneFlashLife) * 0.35f;
				FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
					AllottedGeometry.ToPaintGeometry(FVector2D(LaneW - 2.0f, ApproachH), FSlateLayoutTransform(FVector2D(LaneX + 1.0f, TopY))),
					HighwayBackgroundTexture ? &HighwayBrush : &WhiteBrush, ESlateDrawEffect::None,
					FLinearColor(FlashColor.R, FlashColor.G, FlashColor.B, FlashAlpha));
			}
		}
	}

	// Hit line spans the whole row — this is the "press now" reference. It thickens and
	// brightens on the beat, so the moment to press is legible without watching a metronome.
	const float HitLineThickness = 3.0f + 4.0f * Pulse;
	FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
		AllottedGeometry.ToPaintGeometry(FVector2D(RowWidth, HitLineThickness), FSlateLayoutTransform(FVector2D(RowLeft, HitLineY - HitLineThickness * 0.5f + 1.5f))),
		HitLineTexture ? &HitLineBrush : &WhiteBrush, ESlateDrawEffect::None,
		FLinearColor(1.0f, 1.0f, 1.0f, FMath::Clamp(0.75f + 0.25f * Pulse, 0.0f, 1.0f)));

	// Notes
	const float NoteSize = HighwayNoteSize;
	const float CueLife = FMath::Max(0.08f, SecondsPerBeat * 0.5f); // 1/4 note: ring / miss drift
	for (const FMelodiaHighwayNote& Note : HighwayNotes)
	{
		const float BeatOffset = Note.TargetBeat - HighwayBeatPosition;
		if (BeatOffset < -0.5f || BeatOffset > HighwayScrollBeatsAhead + 0.5f)
		{
			continue;
		}

		// HL2/HL3: a resolved note no longer draws as a note. A hit is represented by its
		// ring and lane flash (drawn below); a miss drops away dimmed in the record loop.
		// Without this, a hit and a miss were visually identical, which was the whole
		// complaint about the highway reading flat.
		if (Note.bResolved)
		{
			const FMelodiaHighwayResolved* Record = ResolvedNotes.FindByPredicate([&Note](const FMelodiaHighwayResolved& Resolved)
			{
				return Resolved.LaneIndex == Note.LaneIndex && FMath::IsNearlyEqual(Resolved.TargetBeat, Note.TargetBeat, 0.01f);
			});
			if (Record || Note.bCountsAsHit)
			{
				continue; // already played out; the ring or the drift owns it now
			}

			// No record: a driver that hands us notes already resolved. Keep the old
			// static dim block rather than draw nothing at all.
			const int32 Lane = FMath::Clamp(Note.LaneIndex, 0, LaneCount - 1);
			const float Normalized = FMath::Clamp(BeatOffset / FMath::Max(0.1f, HighwayScrollBeatsAhead), 0.0f, 1.0f);
			const float DimX = RowLeft + (Lane + 0.5f) * LaneW - NoteSize * 0.5f;
			const float DimY = HitLineY - Normalized * ApproachH - NoteSize * 0.5f;
			FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 2,
				AllottedGeometry.ToPaintGeometry(FVector2D(NoteSize, NoteSize), FSlateLayoutTransform(FVector2D(DimX, DimY))),
				NoteHeadTexture ? &NoteBrush : &WhiteBrush, ESlateDrawEffect::None,
				GradeColor(Note.Grade, 0.35f));
			continue;
		}

		// 0 = at the hit line, 1 = at the top of the approach. Time maps to distance,
		// so a steady BPM gives steady visual speed.
		const float Normalized = FMath::Clamp(BeatOffset / FMath::Max(0.1f, HighwayScrollBeatsAhead), 0.0f, 1.0f);
		const int32 Lane = FMath::Clamp(Note.LaneIndex, 0, LaneCount - 1);
		const float LaneCenterX = RowLeft + (Lane + 0.5f) * LaneW;

		// HL5: inside the last 1/8 note the note grows and brightens, so the press moment
		// is readable before arrival rather than only after the grade lands.
		const float ApproachWindow = FMath::Max(0.05f, SecondsPerBeat * 0.25f);
		const float TimeToLine = BeatOffset * SecondsPerBeat;
		const float Approach = (BeatOffset <= 0.25f)
			? 1.0f - FMath::Clamp(TimeToLine / ApproachWindow, 0.0f, 1.0f)
			: 0.0f;

		const float DrawSize = NoteSize * (1.0f + 0.2f * Approach * Motion);
		const float Brighten = 1.0f + 0.35f * Approach * Motion;
		const FLinearColor NoteColor(
			FMath::Min(1.0f, SparkleTint.R * Brighten),
			FMath::Min(1.0f, SparkleTint.G * Brighten),
			FMath::Min(1.0f, SparkleTint.B * Brighten),
			SparkleTint.A);

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 2,
			AllottedGeometry.ToPaintGeometry(FVector2D(DrawSize, DrawSize), FSlateLayoutTransform(FVector2D(LaneCenterX - DrawSize * 0.5f, HitLineY - Normalized * ApproachH - DrawSize * 0.5f))),
			NoteHeadTexture ? &NoteBrush : &WhiteBrush, ESlateDrawEffect::None,
			NoteColor);
	}

	// HL3: misses drift down past the hit line and dim out. Keyed off the resolution
	// record, not the note, because the stock driver drops the note on the same frame it
	// resolves -- there would be nothing left to animate.
	for (const FMelodiaHighwayResolved& Record : ResolvedNotes)
	{
		if (Record.bCountsAsHit)
		{
			continue;
		}
		const float Age = Now - Record.ResolveTime;
		if (Age < 0.0f || Age > CueLife)
		{
			continue;
		}
		const int32 Lane = FMath::Clamp(Record.LaneIndex, 0, LaneCount - 1);
		const float LaneCenterX = RowLeft + (Lane + 0.5f) * LaneW;
		const float T = FMath::Clamp(Age / CueLife, 0.0f, 1.0f);
		const float Size = NoteSize * (1.0f - 0.25f * T);
		const float Drift = Motion * T * 56.0f;
		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 2,
			AllottedGeometry.ToPaintGeometry(FVector2D(Size, Size), FSlateLayoutTransform(FVector2D(LaneCenterX - Size * 0.5f, HitLineY - Size * 0.5f + Drift))),
			NoteHeadTexture ? &NoteBrush : &WhiteBrush, ESlateDrawEffect::None,
			GradeColor(EMelodiaRhythmGrade::Miss, 0.45f * (1.0f - T)));
	}

	// HL2: hit bursts — a ring expands out of the hit line in the lane that scored, in the
	// grade's colour, and is gone in 1/4 note. This is the "you hit it" that was missing.
	for (const FMelodiaHighwayBurst& Burst : HighwayBursts)
	{
		const float Age = Now - Burst.StartTime;
		if (Age < 0.0f || Age > CueLife)
		{
			continue;
		}
		const int32 Lane = FMath::Clamp(Burst.LaneIndex, 0, LaneCount - 1);
		const float LaneCenterX = RowLeft + (Lane + 0.5f) * LaneW;
		const float T = FMath::Clamp(Age / CueLife, 0.0f, 1.0f);
		const float RingSize = NoteSize * (1.0f + 1.6f * T * Motion);
		PaintRing(OutDrawElements, AllottedGeometry, CurrentLayer + 3,
			FVector2D(LaneCenterX, HitLineY), RingSize,
			FMath::Max(1.0f, 3.0f * (1.0f - T)),
			GradeColor(Burst.Grade, (1.0f - T) * 0.85f),
			WhiteBrush);
	}

	CurrentLayer += 4;
}

void UMelodiaRhythmHUDWidget::PaintFloatingCombatTexts(FSlateWindowElementList& OutDrawElements, const FGeometry& AllottedGeometry, int32& CurrentLayer) const
{
	const FVector2D LocalSize = AllottedGeometry.GetLocalSize();
	const float W = LocalSize.X;
	const float H = LocalSize.Y;
	const float CurrentTime = GetHUDTimeSeconds();
	const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", 18);

	for (const FMelodiaFloatingCombatText& FCT : FloatingCombatTexts)
	{
		const float Age = CurrentTime - FCT.SpawnTime;
		if (Age > 2.0f || Age < 0.0f)
		{
			continue;
		}

		const float Alpha = FMath::Clamp(1.0f - Age / 2.0f, 0.0f, 1.0f);
		const float RiseY = Age * 40.0f;
		const float BaseX = FCT.bAnchorEnemy ? W * 0.5f : W * 0.15f;
		const float BaseY = FCT.bAnchorEnemy ? H * 0.15f : H * 0.85f;

		FSlateDrawElement::MakeText(OutDrawElements, CurrentLayer,
			AllottedGeometry.ToPaintGeometry(FVector2D(200.0f, 28.0f), FSlateLayoutTransform(FVector2D(BaseX + FCT.LateralSeed * 30.0f - 100.0f, BaseY - RiseY))),
			FCT.Text,
			Font, ESlateDrawEffect::None,
			FLinearColor(FCT.Tint.R, FCT.Tint.G, FCT.Tint.B, Alpha));
	}

	++CurrentLayer;
}

// --- BlueprintNativeEvent implementations ---

void UMelodiaRhythmHUDWidget::SetHUDMode_Implementation(const EMelodiaHUDMode NewMode)
{
	ActiveHUDMode = NewMode;
}

void UMelodiaRhythmHUDWidget::SetJudgment_Implementation(const FText& NewText)
{
	LastJudgmentText = NewText;
	// HL1: the pop owns its own timestamp. This used to write LastPulseTime, which
	// DoPulse rewrites on every beat -- so a beat landing mid-pop restarted the fade,
	// and every judgement appeared to linger. LastPulseTime stays the DoPulse heartbeat
	// (it is BlueprintReadOnly, so a widget can still read pulse timing); the pop no
	// longer shares it.
	LastGradePopTime = GetHUDTimeSeconds();
	LastPopGrade = GradeFromText(NewText.ToString());

	// HL2, the other half of the pairing. UMelodiaRhythmCombatSubsystem drops a resolved
	// note from the array on one tick and posts its grade on another, so a grade landing
	// just AFTER a note vanished is still that note's grade. Without this the prompt only
	// ever paired grade-then-vanish, and every hit read as a miss (13 of 13 in the
	// 2026-09-26 gate run, with zero rings). Upgrade the most recent provisional miss
	// inside the window instead of recording it as a miss twice.
	if (LastPopGrade != EMelodiaRhythmGrade::Miss)
	{
		const float PairWindow = FMath::Max(0.12f, SecondsPerBeat * 0.5f);
		int32 UpgradeIndex = INDEX_NONE;
		for (int32 Index = 0; Index < ResolvedNotes.Num(); ++Index)
		{
			const FMelodiaHighwayResolved& Candidate = ResolvedNotes[Index];
			if (Candidate.bCountsAsHit || Candidate.Grade != EMelodiaRhythmGrade::Miss)
			{
				continue;
			}
			if (FMath::Abs(LastGradePopTime - Candidate.ResolveTime) > PairWindow)
			{
				continue;
			}
			UpgradeIndex = Index;
		}

		if (ResolvedNotes.IsValidIndex(UpgradeIndex))
		{
			FMelodiaHighwayResolved& Upgraded = ResolvedNotes[UpgradeIndex];
			Upgraded.bCountsAsHit = true;
			Upgraded.Grade = LastPopGrade;
			Upgraded.ResolveTime = LastGradePopTime;

			FMelodiaHighwayBurst Burst;
			Burst.LaneIndex = Upgraded.LaneIndex;
			Burst.StartTime = LastGradePopTime;
			Burst.Grade = LastPopGrade;
			HighwayBursts.Add(Burst);

			if (LaneFlashTimes.Num() < HighwayLaneCount)
			{
				LaneFlashTimes.SetNumZeroed(HighwayLaneCount);
			}
			if (LaneFlashTimes.IsValidIndex(Upgraded.LaneIndex))
			{
				LaneFlashTimes[Upgraded.LaneIndex] = LastGradePopTime;
			}

			UE_LOG(LogTemp, Log, TEXT("HL_CUE burst lane=%d beat=%.3f grade=%d via=late_grade"),
				Upgraded.LaneIndex, Upgraded.TargetBeat, static_cast<int32>(LastPopGrade));
		}
	}
}

bool UMelodiaRhythmHUDWidget::TryConsumeFreshGrade(const float WindowSeconds)
{
	const float Age = GetHUDTimeSeconds() - LastGradePopTime;
	if (LastGradePopTime <= LastConsumedGradeTime || Age < 0.0f || Age > WindowSeconds)
	{
		return false;
	}
	// One grade event pairs with one resolving note; a second vanish inside the same
	// window is a miss, not a replay of the same hit.
	LastConsumedGradeTime = LastGradePopTime;
	return true;
}

void UMelodiaRhythmHUDWidget::DoPulse_Implementation()
{
	LastPulseTime = GetHUDTimeSeconds();
	// F-a: no bass channel yet (Quartz/MPC proxy) -- pulse every 2nd beat, mirroring the web's
	// startBeatBus data-react-bass-on-every-2nd-beat proxy exactly. Feeds StaffShimmer/SPMeterShimmer.
	if (++BeatCountForBassProxy % 2 == 0)
	{
		LastBassPulseTime = LastPulseTime;
	}
}

void UMelodiaRhythmHUDWidget::NotifyPerfectHit()
{
	// F-b: feeds the NoteTrailIri cue (cyan->gold trail along the lane).
	LastPerfectHitTime = GetHUDTimeSeconds();
}

void UMelodiaRhythmHUDWidget::TriggerSparkleBurst_Implementation()
{
	LastSparkleBurstTime = GetHUDTimeSeconds();
}

void UMelodiaRhythmHUDWidget::SetEnemyVitals_Implementation(const float CurrentHP, const float MaxHP)
{
	LastEnemyHP = FMath::Max(0.0f, CurrentHP);
	LastEnemyMaxHP = FMath::Max(1.0f, MaxHP);
}

void UMelodiaRhythmHUDWidget::SetPartyVitals_Implementation(const float CurrentHP, const float MaxHP)
{
	LastPartyHP = FMath::Max(0.0f, CurrentHP);
	LastPartyMaxHP = FMath::Max(1.0f, MaxHP);
}

void UMelodiaRhythmHUDWidget::SetSprintGlide(bool bSprint, bool bGlide)
{
    // Update internal sprint/glide state flags
    bIsSprinting = bSprint;
    bIsGliding = bGlide;
}

void UMelodiaRhythmHUDWidget::SetSkillPoints_Implementation(const int32 CurrentValue, const int32 MaxValue)
{
	LastSkillPoints = FMath::Max(0, CurrentValue);
	LastSkillPointMax = FMath::Max(1, MaxValue);
}

void UMelodiaRhythmHUDWidget::SetUltimateGauge_Implementation(const float CurrentValue, const float MaxValue, const bool bReady)
{
	LastUltimateGaugeValue = FMath::Max(0.0f, CurrentValue);
	LastUltimateGaugeMax = FMath::Max(1.0f, MaxValue);
	bUltimateReadyVisible = bReady;
}

void UMelodiaRhythmHUDWidget::SetEnemyBreakGauge_Implementation(const float CurrentValue, const float MaxValue, const bool bBroken)
{
	LastEnemyToughness = FMath::Max(0.0f, CurrentValue);
	LastEnemyToughnessMax = FMath::Max(1.0f, MaxValue);
	// F-c: the false->true break edge is the cheapest new cue per the motion-channel spec --
	// feeds BreakCrestReveal (CrestFinale scale + gold flash) and doubles as a sparkle dopamine hit.
	if (bBroken && !bEnemyBreakVisible)
	{
		LastBreakRevealTime = GetHUDTimeSeconds();
		TriggerSparkleBurst();
	}
	bEnemyBreakVisible = bBroken;
}

void UMelodiaRhythmHUDWidget::SetNoteHighwayActive_Implementation(const bool bActive, const TArray<FMelodiaHighwayNote>& Notes, const float BeatPosition, const float ScrollBeatsAhead)
{
	const float Now = GetHUDTimeSeconds();

	// Lock every cue below to the music clock instead of a hardcoded 128 BPM: the push
	// carries the authoritative beat position, so its slope IS seconds-per-beat.
	if (bNoteHighwayActive && LastSampledBeatPosition > -999.0f)
	{
		const float DeltaBeats = BeatPosition - LastSampledBeatPosition;
		const float DeltaSeconds = Now - LastBeatSampleTime;
		if (DeltaBeats > 0.01f && DeltaBeats < 4.0f && DeltaSeconds > 0.0f)
		{
			const float Estimate = DeltaSeconds / DeltaBeats;
			if (Estimate > 0.1f && Estimate < 2.0f)
			{
				SecondsPerBeat = FMath::Lerp(SecondsPerBeat, Estimate, 0.25f);
			}
		}
	}
	LastSampledBeatPosition = BeatPosition;
	LastBeatSampleTime = Now;

	// HL2/HL3: react to each note resolving exactly once. Two signals can carry it:
	//  - the flag path -- a driver that pushes the note with bResolved set, and
	//  - the edge path -- UMelodiaRhythmCombatSubsystem filters resolved notes out
	//    before PushHighwayToHUD, so for that driver a note vanishing from the array
	//    IS the resolution, and its disappearance is all the widget will ever see.
	if (bNoteHighwayActive)
	{
		const auto RecordResolution = [this, Now](const int32 LaneIndex, const float TargetBeat, const bool bCountsAsHit, const EMelodiaRhythmGrade Grade)
		{
			FMelodiaHighwayResolved Record;
			Record.LaneIndex = LaneIndex;
			Record.TargetBeat = TargetBeat;
			Record.ResolveTime = Now;
			Record.bCountsAsHit = bCountsAsHit;
			Record.Grade = Grade;
			ResolvedNotes.Add(Record);

			if (bCountsAsHit)
			{
				FMelodiaHighwayBurst Burst;
				Burst.LaneIndex = LaneIndex;
				Burst.StartTime = Now;
				Burst.Grade = Grade;
				HighwayBursts.Add(Burst);

				if (LaneFlashTimes.Num() < HighwayLaneCount)
				{
					LaneFlashTimes.SetNumZeroed(HighwayLaneCount);
				}
				if (LaneFlashTimes.IsValidIndex(LaneIndex))
				{
					LaneFlashTimes[LaneIndex] = Now;
				}

				// Timestamped proof of the HL2 hit path. The ring and the lane flash live
				// 1/8 note, which is shorter than any remote poll, so the moment itself has
				// to be recorded where it happens.
				UE_LOG(LogTemp, Log, TEXT("HL_CUE burst lane=%d beat=%.3f grade=%d"), LaneIndex, TargetBeat, static_cast<int32>(Grade));
			}
			else
			{
				UE_LOG(LogTemp, Log, TEXT("HL_CUE miss lane=%d beat=%.3f"), LaneIndex, TargetBeat);
			}
		};

		for (const FMelodiaHighwayNote& Note : Notes)
		{
			if (!Note.bResolved)
			{
				continue;
			}
			const bool bKnown = ResolvedNotes.ContainsByPredicate([&Note](const FMelodiaHighwayResolved& R)
			{
				return R.LaneIndex == Note.LaneIndex && FMath::IsNearlyEqual(R.TargetBeat, Note.TargetBeat, 0.01f);
			});
			if (!bKnown)
			{
				RecordResolution(Note.LaneIndex, Note.TargetBeat, Note.bCountsAsHit, Note.Grade);
			}
		}

		for (const FMelodiaHighwayNote& Previous : PreviousHighwayNotes)
		{
			if (Previous.bResolved)
			{
				continue;
			}
			const bool bStillPresent = Notes.ContainsByPredicate([&Previous](const FMelodiaHighwayNote& Note)
			{
				return Note.LaneIndex == Previous.LaneIndex && FMath::IsNearlyEqual(Note.TargetBeat, Previous.TargetBeat, 0.01f);
			});
			if (bStillPresent)
			{
				continue;
			}

			// A grade event landing in the same window is the only evidence that this
			// vanish was earned rather than dropped; without one it reads as a miss.
			const float PairWindow = FMath::Max(0.05f, SecondsPerBeat * 0.25f);
			const bool bHit = TryConsumeFreshGrade(PairWindow);
			RecordResolution(Previous.LaneIndex, Previous.TargetBeat, bHit, bHit ? LastPopGrade : EMelodiaRhythmGrade::Miss);
		}

		// Drop what has finished playing out (the ring/drift life).
		const float CueLife = FMath::Max(0.08f, SecondsPerBeat * 0.5f);
		HighwayBursts.RemoveAll([Now, CueLife](const FMelodiaHighwayBurst& Burst)
		{
			return Now - Burst.StartTime > CueLife;
		});
		ResolvedNotes.RemoveAll([Now, CueLife](const FMelodiaHighwayResolved& Record)
		{
			return Now - Record.ResolveTime > CueLife;
		});
	}
	else
	{
		// Inactive highway: nothing to animate, and stale cues must not survive a restart.
		HighwayBursts.Reset();
		ResolvedNotes.Reset();
		LaneFlashTimes.Reset();
		LastSampledBeatPosition = -1000.0f;
		LastBeatSampleTime = -1000.0f;
	}

	bNoteHighwayActive = bActive;
	HighwayNotes = Notes;
	HighwayBeatPosition = BeatPosition;
	HighwayScrollBeatsAhead = ScrollBeatsAhead;
	PreviousHighwayNotes = Notes;
}

void UMelodiaRhythmHUDWidget::ShowActionPrompt_Implementation(const FString& PromptText)
{
	LastActionPromptText = PromptText;
}

void UMelodiaRhythmHUDWidget::SetBattlePhaseBanner_Implementation(const FString& PhaseLabel)
{
	LastBattlePhaseLabel = PhaseLabel;
	LastBannerTime = GetHUDTimeSeconds();
}

void UMelodiaRhythmHUDWidget::PushFloatingCombatText_Implementation(const FString& Text, const bool bAnchorEnemy, const FLinearColor Tint)
{
	FMelodiaFloatingCombatText FCT;
	FCT.Text = Text;
	FCT.SpawnTime = GetHUDTimeSeconds();
	FCT.bAnchorEnemy = bAnchorEnemy;
	FCT.Tint = Tint;
	FCT.LateralSeed = FMath::FRand() * 2.0f - 1.0f;
	FloatingCombatTexts.Add(FCT);
}

void UMelodiaRhythmHUDWidget::TriggerDamageFlash_Implementation(const float DamageValue)
{
	LastDamageFlashTime = GetHUDTimeSeconds();
}

void UMelodiaRhythmHUDWidget::ShowBattleStatus_Implementation(const FString& StatusText)
{
	LastBattleStatusText = StatusText;
}
