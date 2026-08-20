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
			FLinearColor(0.08f, 0.06f, 0.12f, 0.85f));

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
				&WhiteBrush, ESlateDrawEffect::None, FLinearColor(0.2f, 0.9f, 0.2f, 0.9f));
		}

		// Glide indicator (blue square)
		if (bIsGliding)
		{
			const float IconSize = 12.0f;
			const FVector2D IconPos(BarX + BarW + 4.0f, BarY);
			FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 2,
				AllottedGeometry.ToPaintGeometry(FVector2D(IconSize, IconSize), FSlateLayoutTransform(IconPos)),
				&WhiteBrush, ESlateDrawEffect::None, FLinearColor(0.3f, 0.5f, 0.9f, 0.9f));
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
			FLinearColor(0.08f, 0.06f, 0.12f, 0.85f));

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
				bFilled ? FLinearColor(0.42f, 0.68f, 1.0f, 0.95f) : FLinearColor(0.2f, 0.18f, 0.28f, 0.6f));
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
			FLinearColor(0.08f, 0.06f, 0.12f, 0.7f));

		const FLinearColor GaugeFill = bUltimateReadyVisible
			? FLinearColor(1.0f, 0.86f, 0.42f, 1.0f) // Gold when ready
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
			FLinearColor(0.08f, 0.06f, 0.12f, 0.6f));

		const FLinearColor ToughFill = bEnemyBreakVisible
			? FLinearColor(0.96f, 0.28f, 0.42f, 1.0f) // Red when broken
			: BreakGaugeTint;

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
			AllottedGeometry.ToPaintGeometry(FVector2D(BarW * ToughFraction, BarH), FSlateLayoutTransform(FVector2D(BarX, BarY))),
			&WhiteBrush, ESlateDrawEffect::None,
			ToughFill);
	}

	// --- Judgment text (center, fades out) ---
	{
		const float TimeSinceJudgment = GetHUDTimeSeconds() - LastPulseTime;
		if (TimeSinceJudgment < 1.5f && !LastJudgmentText.IsEmpty())
		{
			const float Alpha = FMath::Clamp(1.0f - TimeSinceJudgment / 1.5f, 0.0f, 1.0f);
			const float Scale = 1.0f + TimeSinceJudgment * 0.15f;
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
					AllottedGeometry.ToPaintGeometry(GradeSize, FSlateLayoutTransform(FVector2D(W * 0.5f - GradeSize.X * 0.5f, H * 0.45f - GradeSize.Y * 0.5f))),
					&GradeBrush, ESlateDrawEffect::None, FLinearColor(1.0f, 1.0f, 1.0f, Alpha));
			}
			else
			{
				const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", FMath::RoundToInt(28.0f * Scale));
				FSlateDrawElement::MakeText(OutDrawElements, CurrentLayer + 2,
					AllottedGeometry.ToPaintGeometry(FVector2D(200.0f, 40.0f), FSlateLayoutTransform(FVector2D(W * 0.5f - 100.0f, H * 0.45f - 20.0f))),
					GradeText, Font, ESlateDrawEffect::None, FLinearColor(1.0f, 1.0f, 1.0f, Alpha));
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
			FLinearColor(0.98f, 0.92f, 0.72f, 0.95f));
	}

	if (!LastActionPromptText.IsEmpty() && ActiveHUDMode != EMelodiaHUDMode::Exploration)
	{
		const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Regular", 14);
		FSlateDrawElement::MakeText(OutDrawElements, CurrentLayer + 2,
			AllottedGeometry.ToPaintGeometry(FVector2D(W * 0.6f, 24.0f), FSlateLayoutTransform(FVector2D(W * 0.2f, H * 0.96f))),
			LastActionPromptText,
			Font, ESlateDrawEffect::None,
			FLinearColor(0.8f, 0.78f, 0.86f, 0.9f));
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
				FLinearColor(0.96f, 0.15f, 0.15f, Alpha));
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

	// One background column per lane, so the lane boundaries are visible at rest.
	for (int32 Lane = 0; Lane < LaneCount; ++Lane)
	{
		const float LaneX = RowLeft + Lane * LaneW;
		// Alternate tint so adjacent lanes stay distinguishable without a divider mesh.
		const float Shade = (Lane % 2 == 0) ? 0.8f : 0.66f;
		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer,
			AllottedGeometry.ToPaintGeometry(FVector2D(LaneW - 2.0f, ApproachH), FSlateLayoutTransform(FVector2D(LaneX + 1.0f, TopY))),
			HighwayBackgroundTexture ? &HighwayBrush : &WhiteBrush, ESlateDrawEffect::None,
			FLinearColor(0.06f, 0.04f, 0.1f, Shade));
	}

	// Hit line spans the whole row — this is the "press now" reference.
	FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 1,
		AllottedGeometry.ToPaintGeometry(FVector2D(RowWidth, 3.0f), FSlateLayoutTransform(FVector2D(RowLeft, HitLineY))),
		HitLineTexture ? &HitLineBrush : &WhiteBrush, ESlateDrawEffect::None,
		FLinearColor(1.0f, 1.0f, 1.0f, 0.9f));

	// Notes
	const float NoteSize = HighwayNoteSize;
	for (const FMelodiaHighwayNote& Note : HighwayNotes)
	{
		const float BeatOffset = Note.TargetBeat - HighwayBeatPosition;
		if (BeatOffset < -0.5f || BeatOffset > HighwayScrollBeatsAhead + 0.5f)
		{
			continue;
		}

		// 0 = at the hit line, 1 = at the top of the approach. Time maps to distance,
		// so a steady BPM gives steady visual speed.
		const float Normalized = FMath::Clamp(BeatOffset / FMath::Max(0.1f, HighwayScrollBeatsAhead), 0.0f, 1.0f);
		const int32 Lane = FMath::Clamp(Note.LaneIndex, 0, LaneCount - 1);
		const float NoteX = RowLeft + (Lane + 0.5f) * LaneW - NoteSize * 0.5f;
		const float NoteY = HitLineY - Normalized * ApproachH - NoteSize * 0.5f;

		FLinearColor NoteColor;
		if (Note.bResolved)
		{
			switch (Note.Grade)
			{
			case EMelodiaRhythmGrade::Perfect: NoteColor = FLinearColor(0.42f, 1.0f, 0.72f, 0.6f); break;
			case EMelodiaRhythmGrade::Great:   NoteColor = FLinearColor(0.62f, 0.92f, 1.0f, 0.5f); break;
			case EMelodiaRhythmGrade::Good:    NoteColor = FLinearColor(0.98f, 0.88f, 0.36f, 0.4f); break;
			default:                           NoteColor = FLinearColor(0.96f, 0.28f, 0.42f, 0.3f); break;
			}
		}
		else
		{
			NoteColor = SparkleTint;
		}

		FSlateDrawElement::MakeBox(OutDrawElements, CurrentLayer + 2,
			AllottedGeometry.ToPaintGeometry(FVector2D(NoteSize, NoteSize), FSlateLayoutTransform(FVector2D(NoteX, NoteY))),
			NoteHeadTexture ? &NoteBrush : &WhiteBrush, ESlateDrawEffect::None,
			NoteColor);
	}

	CurrentLayer += 3;
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
	LastPulseTime = GetHUDTimeSeconds();
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
	bNoteHighwayActive = bActive;
	HighwayNotes = Notes;
	HighwayBeatPosition = BeatPosition;
	HighwayScrollBeatsAhead = ScrollBeatsAhead;
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
