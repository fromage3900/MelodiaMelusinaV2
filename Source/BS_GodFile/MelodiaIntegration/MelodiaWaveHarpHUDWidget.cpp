#include "MelodiaWaveHarpHUDWidget.h"
#include "MelodiaWaveHarpCombatComponent.h"
#include "MelodiaHybridEncounterComponent.h"
#include "MelodiaWorldSlimeNode.h"
#include "MelodiaMusicClockSubsystem.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Misc/PackageName.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"

// Figma source: MelodiaMelusina Yx8ud7n39NdWZvnNvo4Xlf, "Bow HUD / v3.7 - Cartouche Lookdev (handpaint
// slots)" 256:6496 (colour pass over v3.6 250:5312). All positions below are Figma design px inside the
// 704x396 "Overworld HUD Template" frame; the reticle centre is (352,198).
namespace MelodiaBowHUD
{
 constexpr float DesignW = 704.f, DesignH = 396.f;
 const FVector2D DesignCenter(352.f, 198.f);

 // v3.7 palette (sRGB hex -> linear): gold ONLY in Perfect; pearl text; coral/blush bow energy.
 constexpr FLinearColor Pearl(0.9216f, 0.8550f, 0.7682f, 1.f); // #F6EEE3
 constexpr FLinearColor Coral(0.9131f, 0.2384f, 0.3916f, 1.f); // #F586A8
 constexpr FLinearColor Blush(0.9216f, 0.3763f, 0.5776f, 1.f); // #F6A5C8
 constexpr FLinearColor Peach(1.0000f, 0.6376f, 0.4793f, 1.f); // #FFD1B8
 constexpr FLinearColor HotCoral(1.0000f, 0.1144f, 0.3613f, 1.f); // #FF5FA2
 constexpr FLinearColor Gold(0.5841f, 0.3916f, 0.1441f, 1.f); // #C9A86A
 constexpr FLinearColor GoldLight(0.7231f, 0.5711f, 0.3278f, 1.f); // #DDC79B
 constexpr FLinearColor Ink(0.0037f, 0.0056f, 0.0160f, .82f); // #0C1122

 // Chord petals: hand-placed in Figma (offset from reticle centre, Figma rotation in degrees, CCW+).
 const FVector2D PetalOffset[5] = { {0.f,-44.f}, {45.8f,-21.2f}, {23.8f,21.9f}, {-35.6f,25.7f}, {-50.3f,-15.f} };
 const float PetalFigmaRotation[5] = { 0.f, 72.f, 144.f, -144.f, -72.f };
 const FVector2D GlintPos[5] = { {290.5f,158.5f}, {407.5f,150.5f}, {280.5f,243.5f}, {413.5f,236.5f}, {347.5f,120.5f} };

 float Diameter(EMelodiaBowHUDState S)
 {
  switch (S) { case EMelodiaBowHUDState::Idle: return 70.f; case EMelodiaBowHUDState::Aim: return 64.f;
   case EMelodiaBowHUDState::Sequence: return 40.f; default: return 58.f; }
 }
 float Clamp01(float V) { return FMath::Clamp(V, 0.f, 1.f); }
 float EaseOut(float T) { T = Clamp01(T); return 1.f - FMath::Pow(1.f - T, 3.f); }
 /** 0 -> 1 -> 0 bump over [0,1]. */
 float Bump(float T) { T = Clamp01(T); return FMath::Sin(T * PI); }

 TSoftObjectPtr<UTexture2D> Tex(const TCHAR* Name)
 {
  return TSoftObjectPtr<UTexture2D>(FSoftObjectPath(FString::Printf(TEXT("/Game/Melodia/UI/BowHUD/Textures/%s.%s"), Name, Name)));
 }
}
UMelodiaWaveHarpHUDWidget::UMelodiaWaveHarpHUDWidget(const FObjectInitializer& ObjectInitializer)
 : Super(ObjectInitializer)
{
 using namespace MelodiaBowHUD;
 // Defaults = IMPORT_MANIFEST.md paths. Handpaint swap = reimport over the same asset.
 ApertureRing.Base = Tex(TEXT("T_BowHUD_ApertureRing")); ApertureRing.Perfect = Tex(TEXT("T_BowHUD_ApertureRing_Perfect"));
 InnerAperture.Base = Tex(TEXT("T_BowHUD_InnerAperture"));
 TensionArc1.Base = Tex(TEXT("T_BowHUD_TensionArc1")); TensionArc1.Perfect = Tex(TEXT("T_BowHUD_TensionArc1_Perfect"));
 TensionArc2.Base = Tex(TEXT("T_BowHUD_TensionArc2")); TensionArc2.Perfect = Tex(TEXT("T_BowHUD_TensionArc2_Perfect"));
 TensionArc3.Base = Tex(TEXT("T_BowHUD_TensionArc3")); TensionArc3.Perfect = Tex(TEXT("T_BowHUD_TensionArc3_Perfect"));
 Petal.Base = Tex(TEXT("T_BowHUD_Petal")); Petal.Lit = Tex(TEXT("T_BowHUD_Petal_Lit")); Petal.Perfect = Tex(TEXT("T_BowHUD_Petal_Perfect"));
 CenterRosette.Base = Tex(TEXT("T_BowHUD_CenterRosette"));
 CenterDot.Base = Tex(TEXT("T_BowHUD_CenterDot")); CenterDot.Perfect = Tex(TEXT("T_BowHUD_CenterDot_Perfect"));
 TargetLock.Base = Tex(TEXT("T_BowHUD_TargetLock")); TargetLock.Perfect = Tex(TEXT("T_BowHUD_TargetLock_Perfect"));
 ReleaseRipple.Base = Tex(TEXT("T_BowHUD_ReleaseRipple"));
 SequenceCollapse.Base = Tex(TEXT("T_BowHUD_SequenceCollapse"));
 CompassRadialScore.Base = Tex(TEXT("T_BowHUD_CompassRadialScore"));
 CompassChromaticSpokes.Base = Tex(TEXT("T_BowHUD_CompassChromaticSpokes"));
 ModeCrest.Base = Tex(TEXT("T_BowHUD_ModeCrest")); ModeCrest.Perfect = Tex(TEXT("T_BowHUD_ModeCrest_Perfect"));
 PromptCartouche.Base = Tex(TEXT("T_BowHUD_PromptCartouche")); PromptCartouche.Perfect = Tex(TEXT("T_BowHUD_PromptCartouche_Perfect"));
 TargetCartouche.Base = Tex(TEXT("T_BowHUD_TargetCartouche")); TargetCartouche.Perfect = Tex(TEXT("T_BowHUD_TargetCartouche_Perfect"));
 ScoreCornerSprig.Base = Tex(TEXT("T_BowHUD_ScoreCornerSprig")); ScoreCornerSprig.Perfect = Tex(TEXT("T_BowHUD_ScoreCornerSprig_Perfect"));
 ScoreStem.Base = Tex(TEXT("T_BowHUD_ScoreStem")); ScoreStem.Perfect = Tex(TEXT("T_BowHUD_ScoreStem_Perfect"));
 FrameCorner.Base = Tex(TEXT("T_BowHUD_FrameCorner"));
 PerfectBloomRipple.Base = Tex(TEXT("T_BowHUD_PerfectBloomRipple"));
 PerfectBloomFiligree.Base = Tex(TEXT("T_BowHUD_PerfectBloomFiligree"));
 PerfectReleaseCrest.Base = Tex(TEXT("T_BowHUD_PerfectReleaseCrest"));
 PerfectGlint.Base = Tex(TEXT("T_BowHUD_PerfectGlint"));
 LabelFont = TSoftObjectPtr<UFont>(FSoftObjectPath(TEXT("/Game/Melodia/UI/Fonts/InterTokens/F_Inter_Token.F_Inter_Token")));
}

FMelodiaBowHUDTextureSlot* UMelodiaWaveHarpHUDWidget::SlotProperty(ESlot InSlot)
{
 switch (InSlot)
 {
 case SApertureRing: return &ApertureRing; case SInnerAperture: return &InnerAperture;
 case SArc1: return &TensionArc1; case SArc2: return &TensionArc2; case SArc3: return &TensionArc3;
 case SPetal: return &Petal; case SRosette: return &CenterRosette; case SDot: return &CenterDot;
 case STargetLock: return &TargetLock; case SRipple: return &ReleaseRipple; case SCollapse: return &SequenceCollapse;
 case SCompassScore: return &CompassRadialScore; case SCompassSpokes: return &CompassChromaticSpokes;
 case SCrest: return &ModeCrest; case SPrompt: return &PromptCartouche; case STargetCart: return &TargetCartouche;
 case SSprig: return &ScoreCornerSprig; case SStem: return &ScoreStem; case SCorner: return &FrameCorner;
 case SBloomRipple: return &PerfectBloomRipple; case SBloomFiligree: return &PerfectBloomFiligree;
 case SReleaseCrest: return &PerfectReleaseCrest; case SGlint: return &PerfectGlint;
 default: return nullptr;
 }
}

bool UMelodiaWaveHarpHUDWidget::ResolveBrush(const TSoftObjectPtr<UTexture2D>& Soft, FSlateBrush& Out)
{
 if (Soft.IsNull()) return false;
 UTexture2D* Texture = Soft.Get();
 if (!Texture)
 {
  // Not imported yet (manifest step 3): stay silent and use the code-drawn fallback.
  const FSoftObjectPath& Path = Soft.ToSoftObjectPath();
  if (!FPackageName::DoesPackageExist(Path.GetLongPackageName())) return false;
  Texture = Soft.LoadSynchronous();
 }
 if (!Texture) return false;
 LoadedTextures.AddUnique(Texture);
 Out = FSlateBrush();
 Out.SetResourceObject(Texture);
 Out.ImageSize = FVector2D(Texture->GetSizeX(), Texture->GetSizeY());
 Out.DrawAs = ESlateBrushDrawType::Image;
 Out.Tiling = ESlateBrushTileType::NoTile;
 return true;
}

void UMelodiaWaveHarpHUDWidget::ResolveArt()
{
 LoadedTextures.Reset();
 for (int32 Index = 0; Index < SNum; ++Index)
 {
  FResolvedSlot& R = Art[Index];
  R = FResolvedSlot();
  if (const FMelodiaBowHUDTextureSlot* TexSlot = SlotProperty(ESlot(Index)))
  {
   R.bBase = ResolveBrush(TexSlot->Base, R.Base);
   R.bLit = ResolveBrush(TexSlot->Lit, R.Lit);
   R.bPerfect = ResolveBrush(TexSlot->Perfect, R.Perfect);
  }
 }
}

void UMelodiaWaveHarpHUDWidget::NativeConstruct()
{
 Super::NativeConstruct();
 InterFont = LabelFont.IsNull() ? nullptr : LabelFont.LoadSynchronous();
 ResolveArt();
}

const UMelodiaWaveHarpCombatComponent* UMelodiaWaveHarpHUDWidget::FindCombat() const
{
 const APawn* Pawn = GetOwningPlayer() ? GetOwningPlayer()->GetPawn() : nullptr;
 return Pawn ? Pawn->FindComponentByClass<UMelodiaWaveHarpCombatComponent>() : nullptr;
}

float UMelodiaWaveHarpHUDWidget::BeatSeconds() const
{
 // Beat authority is UMelodiaMusicClockSubsystem (Harmonix/Quartz). It deliberately reports 0 when
 // there is no tempo; then we fall back to the Figma motion grid (128 BPM: 469/234/117 ms).
 float Bpm = FallbackBPM;
 if (const UMelodiaMusicClockSubsystem* Clock = UMelodiaMusicClockSubsystem::Get(this))
 {
  const float Tempo = Clock->GetTempoBPM();
  if (Tempo > 1.f) Bpm = Tempo;
 }
 return 60.f / FMath::Clamp(Bpm, 40.f, 240.f);
}

void UMelodiaWaveHarpHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
 Super::NativeTick(MyGeometry, InDeltaTime);
 using namespace MelodiaBowHUD;
 const UWorld* World = GetWorld();
 Now = World ? World->GetTimeSeconds() : Now + InDeltaTime;
 Beat = BeatSeconds();

 // Breathe on a two-beat cycle (~0.94 s at 128 BPM); phase-locked to the music clock when it has time.
 bool bLocked = false;
 if (const UMelodiaMusicClockSubsystem* Clock = UMelodiaMusicClockSubsystem::Get(this))
 {
  const FMelodiaMusicTime Time = Clock->GetMusicTime();
  if (Time.bValid) { BreathePhase = FMath::Fmod(Time.BeatInBar, 2.f) * .5f; bLocked = true; }
 }
 if (!bLocked) BreathePhase = FMath::Fmod(float(Now) / (2.f * Beat), 1.f);

 const UMelodiaWaveHarpCombatComponent* Combat = FindCombat();
 if (!Combat)
 {
  if (IsDesignTime())
  {
   // UMG designer / lookdev preview only (NativeConstruct does not run there): resolve art once
   // here so NativePaint never has to mutate state through const_cast, then seed a representative
   // Target-state reticle. Never used at runtime.
   if (!InterFont && !LabelFont.IsNull()) InterFont = LabelFont.LoadSynchronous();
   if (!Art[0].bBase && !Art[0].bLit && !Art[0].bPerfect) ResolveArt();
   State = EMelodiaBowHUDState::Target;
   bReticleVisible = true;
   bIsAiming = true;
   bIsDrawing = true;
   DrawTension = 0.85f;
   LooseCount = 3;
   ReticleFade = 1.0f;
   ArcLight[0] = 1.0f;
   ArcLight[1] = 1.0f;
   ArcLight[2] = 0.75f;
   bHasTarget = true;
   TargetHP = 750.f;
   TargetMaxHP = 1000.f;
   return;
  }
  // Runtime with no WaveHarp combat component: draw nothing extra. bReticleVisible=false lets the
  // bridge restore the stock OverworldHUD reticle.
  bReticleVisible = false; State = EMelodiaBowHUDState::Idle; ReticleFade = 0.f;
  return;
 }
 // ---- Figma inputs ----
 bIsAiming = Combat->IsAiming();                    // is_aiming
 bIsDrawing = Combat->IsDrawing();
 DrawTension = Combat->GetDrawTension();            // draw_tension 0..1 (0.8 s full draw)
 ChordFeedback = Combat->GetChordFeedback();
 // loose_count: the combat component's ComboStep is the loose counter (1..4 within the C-maj7 chord,
 // reset to 0 on the 5th loose / 1.25 s idle). The chord-complete flash lights all 5 petals.
 LooseCount = ChordFeedback > 0.f ? 5 : FMath::Clamp(Combat->ComboStep, 0, 5);
 HitFeedback = Combat->GetHitFeedback();
 LastHitDamage = Combat->LastHitDamage;
 const bool bSequence = Combat->IsInSequence();
 bCombatLocked = Combat->IsCombatLocked();
 bHasTarget = false; TargetHP = TargetMaxHP = 0.f; Resonance01 = 0.f;
 if (const UMelodiaHybridEncounterComponent* TargetComp = Combat->GetTarget())
 {
  Resonance01 = TargetComp->GetResonanceNormalized();
  if (const AMelodiaWorldSlimeNode* Slime = Cast<AMelodiaWorldSlimeNode>(TargetComp->GetOwner()))
  {
   bHasTarget = !Slime->bIsDead; TargetHP = Slime->CurrentHP; TargetMaxHP = Slime->MaxHP;
  }
  else bHasTarget = true;
 }

 const bool bWasPerfect = State == EMelodiaBowHUDState::Perfect;
 if (Combat->ShotsFired != LastShotsFired)
 {
  if (Combat->ShotsFired > LastShotsFired)
  {
   LooseStartedAt = Now;
   if (bWasPerfect) BloomStartedAt = Now;   // perfect release: one outward ripple
  }
  LastShotsFired = Combat->ShotsFired;
 }
 if (ChordFeedback > .95f) BloomStartedAt = FMath::Max(BloomStartedAt, Now - InDeltaTime);

 const float PetalBloomEnd = Beat * (769.f / 469.f);
 const bool bPerfectNow = bIsDrawing && DrawTension >= 1.f;
 const bool bBloomHold = (Now - BloomStartedAt) < PetalBloomEnd;
 const bool bActive = bIsAiming || bIsDrawing;
 EMelodiaBowHUDState NewState = EMelodiaBowHUDState::Idle;
 if (bSequence) NewState = EMelodiaBowHUDState::Sequence;
 else if (bPerfectNow || (bBloomHold && bActive)) NewState = EMelodiaBowHUDState::Perfect;
 else if (bActive && bHasTarget) NewState = EMelodiaBowHUDState::Target;
 else if (bActive) NewState = EMelodiaBowHUDState::Aim;
 if (NewState != State)
 {
  PrevState = State; State = NewState; StateEnteredAt = Now;
  if (NewState == EMelodiaBowHUDState::Perfect && !bBloomHold) BloomStartedAt = Now; // pearl -> gold snap
 }

 // reticle_visible. The bridge reads this and hides/restores the stock OverworldHUD Reticle.
 bReticleVisible = !bSequence && (bShowReticleWhenIdle || State != EMelodiaBowHUDState::Idle);
 // FLOW <-> SEQUENCE: 469 ms (one beat) fade/scale.
 ReticleFade = FMath::FInterpConstantTo(ReticleFade, bReticleVisible ? 1.f : 0.f, InDeltaTime, 1.f / Beat);
 SequenceBlend = FMath::FInterpConstantTo(SequenceBlend, bSequence ? 1.f : 0.f, InDeltaTime, 1.f / Beat);
 // Arcs react in 117 ms (quarter beat) as draw_tension crosses each threshold.
 const float Thresholds[3] = { ArcTensionThresholds.X, ArcTensionThresholds.Y, ArcTensionThresholds.Z };
 for (int32 Arc = 0; Arc < 3; ++Arc)
 {
  const bool bLit = State == EMelodiaBowHUDState::Perfect || (bIsDrawing && DrawTension >= Thresholds[Arc]);
  ArcLight[Arc] = FMath::FInterpConstantTo(ArcLight[Arc], bLit ? 1.f : 0.f, InDeltaTime, 4.f / Beat);
 }
}

int32 UMelodiaWaveHarpHUDWidget::NativePaint(const FPaintArgs& Args, const FGeometry& G,
 const FSlateRect& Cull, FSlateWindowElementList& E, int32 L, const FWidgetStyle& Style, bool Enabled) const
{
 using namespace MelodiaBowHUD;
 L = Super::NativePaint(Args, G, Cull, E, L, Style, Enabled);

 // Runtime with no combat component: nothing extra is drawn (the bridge restores the stock reticle).
 // In the UMG designer the preview state is seeded in NativeTick; paint only reads.
 if (!IsDesignTime() && !FindCombat()) return L;

 const FVector2D Size = G.GetLocalSize();
 const float S = (Size.Y / DesignH) * LayoutScale * .65f;          // compact frame for a full-screen viewport
 const FVector2D C = Size * .5;
 const auto At = [&](FVector2D Design) { return C + (Design - DesignCenter) * S; };
 const float T117 = Beat * .25f, T234 = Beat * .5f, T469 = Beat, T703 = Beat * 1.5f, T50 = Beat * (50.f / 469.f);
 const float T769 = Beat * (769.f / 469.f);
 const bool bPerfect = State == EMelodiaBowHUDState::Perfect;
 const bool bSequence = State == EMelodiaBowHUDState::Sequence;
 const bool bTargetish = State == EMelodiaBowHUDState::Target || bPerfect;
 const float SinceState = float(Now - StateEnteredAt);
 const float SinceBloom = float(Now - BloomStartedAt);
 const float SinceLoose = float(Now - LooseStartedAt);
 const float Opacity = Style.GetColorAndOpacityTint().A;

 // ---- primitives ----
 const auto Tint = [&](FLinearColor Col, float A) { Col.A *= A * Opacity; return Col; };
 /** Draw a slot centred at Center (slate units), DesignSize in Figma px. Returns false when unassigned. */
 const auto Draw = [&](ESlot InSlot, bool bWantPerfect, bool bWantLit, FVector2D Center, FVector2D DesignSize,
  float Scale, float FigmaRotationDeg, float Alpha, int32 Layer) -> bool
 {
  const FSlateBrush* Brush = Art[InSlot].Pick(bWantPerfect, bWantLit);
  if (!Brush || Alpha <= .002f) return Brush != nullptr;
  const FVector2D Box = DesignSize * S * Scale;
  const FPaintGeometry PG = G.ToPaintGeometry(Box, FSlateLayoutTransform(Center - Box * .5));
  const FLinearColor White = Tint(FLinearColor::White, Alpha);
  if (FMath::IsNearlyZero(FigmaRotationDeg))
   FSlateDrawElement::MakeBox(E, Layer, PG, Brush, ESlateDrawEffect::None, White);
  else // Figma rotation is CCW-positive; Slate angles are clockwise-positive (y down).
   FSlateDrawElement::MakeRotatedBox(E, Layer, PG, Brush, ESlateDrawEffect::None,
    FMath::DegreesToRadians(-FigmaRotationDeg), TOptional<FVector2f>(), FSlateDrawElement::RelativeToElement, White);
  return true;
 };
 const auto Arc = [&](FVector2D Center, float Radius, float FromDeg, float ToDeg, FLinearColor Col, float Thick, int32 Layer)
 {
  // Code-drawn fallback (0 deg = up, clockwise).
  TArray<FVector2f> Points;
  const int32 Steps = FMath::Max(8, int32(FMath::Abs(ToDeg - FromDeg) / 7.5f));
  for (int32 I = 0; I <= Steps; ++I)
  {
   const float A = FMath::DegreesToRadians(FMath::Lerp(FromDeg, ToDeg, float(I) / Steps));
   Points.Add(FVector2f(Center + FVector2D(FMath::Sin(A), -FMath::Cos(A)) * Radius));
  }
  FSlateDrawElement::MakeLines(E, Layer, G.ToPaintGeometry(), Points, ESlateDrawEffect::None, Col, true, Thick);
 };
 const auto Ring = [&](FVector2D Center, float Radius, FLinearColor Col, float Thick, int32 Layer)
 { Arc(Center, Radius, 0.f, 360.f, Col, Thick, Layer); };
 const auto Font = [&](float DesignPx, bool bBold) -> FSlateFontInfo
 {
  const int32 Pt = FMath::Max(6, FMath::RoundToInt(DesignPx * S * .75f)); // px -> Slate pt (96 dpi)
  FSlateFontInfo F = InterFont ? FSlateFontInfo(InterFont, Pt) : FCoreStyle::GetDefaultFontStyle(bBold ? "Bold" : "Regular", Pt);
  F.LetterSpacing = 120;
  return F;
 };
 const auto TextCentered = [&](FVector2D Center, const FString& Str, const FSlateFontInfo& F, FLinearColor Col, int32 Layer)
 {
  FVector2D Measured(Str.Len() * F.Size * .6f, F.Size * 1.3f);
  if (FSlateApplication::IsInitialized())
   Measured = FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Str, F);
  FSlateDrawElement::MakeText(E, Layer, G.ToPaintGeometry(Measured, FSlateLayoutTransform(Center - Measured * .5)),
   Str, F, ESlateDrawEffect::None, Col);
 };
 const auto Plate = [&](FVector2D Center, FVector2D DesignSize, FLinearColor Outline, float Alpha, int32 Layer)
 {
  const FVector2D Box = DesignSize * S;
  const FSlateRoundedBoxBrush Rounded(Ink, Box.Y * .5f, Tint(Outline, .9f), FMath::Max(1.f, S * .6f));
  FSlateDrawElement::MakeBox(E, Layer, G.ToPaintGeometry(Box, FSlateLayoutTransform(Center - Box * .5)), &Rounded,
   ESlateDrawEffect::None, Tint(Ink, Alpha));
 };

 const int32 LBack = L + 1, LRet = L + 2, LTop = L + 3, LText = L + 4, LFx = L + 5;

 // ================= CENTRE RETICLE (yields entirely in SEQUENCE) =================
 if (ReticleFade > .002f)
 {
  const FVector2D RC = At(DesignCenter);
   const bool bIdle = State == EMelodiaBowHUDState::Idle;
   // Idle: small + translucent until the player aims or draws; breathes on a two-beat cycle.
   const float IdleScale = bIdle ? .5f : 1.f;
   const float IdleAlpha = bIdle ? .32f : 1.f;
   const float Breath = bIdle ? .5f * (1.f - FMath::Cos(2.f * PI * BreathePhase)) : 0.f;
   const float Fade = ReticleFade * (bIdle ? FMath::Lerp(.86f, 1.f, Breath) : 1.f) * IdleAlpha;
   const float Group = (1.f + .025f * Breath) * FMath::Lerp(.6f, 1.f, ReticleFade) * IdleScale; // SEQUENCE collapses to .6

  // Aperture react 117 ms, damped settle 469..703 ms.
  const float FromD = Diameter(PrevState), ToD = Diameter(State);
  const float Settle = Clamp01((SinceState - T117) / FMath::Max(.01f, T703 - T117));
  const float RingD = (FMath::Lerp(FromD, ToD, EaseOut(SinceState / T117))
   - (ToD - FromD) * .12f * FMath::Sin(Settle * PI) * (1.f - Settle)) * Group;

  // Compass rosettes behind the reticle (v3.3/v3.4 layers carried into v3.6/3.7).
  const float CompassA = bPerfect ? .70f : bTargetish ? .6f : bIdle ? .40f : .5f;
  Draw(SCompassScore, false, false, RC, {164.f,164.f}, Group, 0.f, CompassA * Fade, LBack);
  Draw(SCompassSpokes, false, false, RC, {176.f,176.f}, Group, bPerfect ? 7.f : 0.f, (bIdle ? .18f : CompassA) * Fade, LBack);

  // Aperture ring: pearl/coral -> gold snap over 117 ms in PERFECT.
  const float GoldK = bPerfect ? EaseOut(SinceBloom / T117) : 0.f;
  const FVector2D RingBox(RingD / Group, RingD / Group);
  if (!Draw(SApertureRing, false, false, RC, RingBox, Group, 0.f, Fade * (1.f - GoldK), LRet))
   Ring(RC, RingD * .5f * S, Tint(Coral, Fade), 1.25f * S, LRet);
  if (GoldK > 0.f && !Draw(SApertureRing, true, false, RC, RingBox, Group, 0.f, Fade * GoldK, LRet))
   Ring(RC, RingD * .5f * S, Tint(GoldLight, Fade * GoldK), 1.25f * S, LRet);

  if (!Draw(SInnerAperture, false, false, RC, {28.f,28.f}, Group, 0.f, Fade, LRet))
   Ring(RC, 14.f * S * Group, Tint(Blush, Fade), .9f * S, LRet);

  // Tension arcs 1..3 (82/90/98 px). Idle: faint .14 -> .24 ripple, 180 ms stagger. Lit: full.
  const FLinearColor ArcCol[3] = { Coral, Blush, Peach };
  const float ArcD[3] = { 82.f, 90.f, 98.f };
  const ESlot ArcSlot[3] = { SArc1, SArc2, SArc3 };
  for (int32 A = 0; A < 3; ++A)
  {
   const float Ripple = .5f * (1.f - FMath::Cos(2.f * PI * FMath::Fmod(BreathePhase + A * (.18f / (2.f * Beat)) + 1.f, 1.f)));
   const float Faint = FMath::Lerp(.14f, .24f, Ripple);
   const float Alpha = FMath::Lerp(Faint, 1.f, ArcLight[A]) * Fade;
   if (!Draw(ArcSlot[A], bPerfect, false, RC, {ArcD[A], ArcD[A]}, Group, 0.f, Alpha, LRet))
   {
    const float Span = bPerfect ? 141.f : bTargetish ? 114.f : 53.f; // Figma half-spans per state
    Arc(RC, ArcD[A] * .5f * S * Group, -Span, Span, Tint(bPerfect && A > 0 ? GoldLight : ArcCol[A], Alpha), (.95f + .12f * A) * S, LRet);
   }
  }

  // Chord petals: loose_count lights them; each new loose pops 117 -> 234 ms; PERFECT ripples to 769 ms.
  for (int32 P = 0; P < 5; ++P)
  {
   const bool bLit = P < LooseCount;
   float Pop = 1.f;
   if (bLit && P == LooseCount - 1 && SinceLoose < T234)
    Pop = SinceLoose < T117 ? FMath::Lerp(1.f, 1.35f, EaseOut(SinceLoose / T117)) : FMath::Lerp(1.35f, 1.f, EaseOut((SinceLoose - T117) / T117));
   if (bPerfect && SinceBloom < T769)
   {
    const float Delay = T50 + P * ((T769 - T234) / 5.f);
    Pop *= 1.f + .3f * Bump((SinceBloom - Delay) / T234);
   }
   const FVector2D PC = RC + PetalOffset[P] * S * Group;
   const bool bGoldPetal = bPerfect && bLit;
   if (!Draw(SPetal, bGoldPetal, bLit, PC, {7.f,13.f}, Group * Pop, PetalFigmaRotation[P], Fade, LRet))
   {
    const FLinearColor Col = bGoldPetal ? GoldLight : bLit ? Coral : Blush;
    Ring(PC, 3.5f * S * Group * Pop, Tint(Col, Fade), .9f * S, LRet);
   }
  }

  // Target lock (Target/Perfect): punch 1.18 -> 1.0 between 117 and 234 ms, slow 32-beat rotation.
  if (bTargetish)
  {
   const float Punch = SinceState < T117 ? 1.18f : FMath::Lerp(1.18f, 1.f, EaseOut((SinceState - T117) / T117));
   const float In = EaseOut(SinceState / T117);
   const float Spin = -FMath::Fmod(float(Now) / (32.f * Beat), 1.f) * 360.f;
   if (!Draw(STargetLock, bPerfect, false, RC, {78.f,78.f}, Group * Punch, Spin, Fade * In, LRet))
    Ring(RC, 39.f * S * Group * Punch, Tint(bPerfect ? GoldLight : HotCoral, Fade * In), 1.f * S, LRet);
  }

  // Centre rosette + dot. PERFECT: 50 ms flash on the dot.
  const float Flash = bPerfect && SinceBloom < T117 ? FMath::Lerp(2.2f, 1.f, EaseOut((SinceBloom - T50) / (T117 - T50))) : 1.f;
  Draw(SRosette, false, false, RC, bPerfect ? FVector2D(38.f,38.f) : FVector2D(32.f,32.f), Group, 0.f, (bPerfect ? .30f : .18f) * Fade, LRet);
  if (!Draw(SDot, bPerfect, false, RC, bPerfect ? FVector2D(5.f,5.f) : FVector2D(4.f,4.f), Group * Flash, 0.f, Fade, LTop))
   Ring(RC, 1.5f * S * Group * Flash, Tint(bPerfect ? GoldLight : Peach, Fade), 2.f * S, LTop);
 }

 // ================= PERFECT BLOOM (50 / 117 / 234 / 469 ms) =================
 if (!bSequence && SinceBloom < T769)
 {
  const FVector2D RC = At(DesignCenter);
  const float R = SinceBloom / T234; // one 234 ms outward ripple
  if (R <= 1.f && !Draw(SRipple, false, false, RC, {108.f,108.f}, FMath::Lerp(.72f, 1.12f, EaseOut(R)), 0.f, 1.f - R, LFx))
   Ring(RC, 54.f * S * FMath::Lerp(.72f, 1.12f, EaseOut(R)), Tint(HotCoral, 1.f - R), 1.f * S, LFx);
  const float B = SinceBloom / T469;
  if (B <= 1.f)
  {
   Draw(SBloomRipple, false, false, RC, {122.f,122.f}, FMath::Lerp(.8f, 1.3f, EaseOut(B)), 0.f, .8f * (1.f - B), LFx);
   Draw(SReleaseCrest, false, false, At({352.f,198.f}), {74.f,74.f}, 1.f, 0.f, .9f * Bump(B), LFx);
   for (int32 Gl = 0; Gl < 5; ++Gl)
    Draw(SGlint, false, false, At(GlintPos[Gl]), Gl == 4 ? FVector2D(9.f,9.f) : FVector2D(7.f,7.f), 1.f, 45.f,
     Bump((SinceBloom - Gl * T50 * .5f) / T469), LFx);
  }
  // Bloom filigree (ReticleNE) grows 234 -> 769 ms.
  Draw(SBloomFiligree, false, false, At({442.f,178.f}), {132.f,96.f}, 1.f, -22.f, .85f * Bump((SinceBloom - T234) / (T769 - T234)), LFx);
 }

 // ================= FRAME: mode crest / prompt cartouche / target cartouche =================
 // SEQUENCE handoff: prompt slides out 0..234 ms and the new copy slides in 234..469 ms.
 const bool bHandoff = (State == EMelodiaBowHUDState::Sequence) != (PrevState == EMelodiaBowHUDState::Sequence) && SinceState < T469;
 float Slide = 0.f, SlideA = 1.f;
 if (bHandoff)
 {
  if (SinceState < T234) { Slide = 10.f * EaseOut(SinceState / T234); SlideA = 1.f - EaseOut(SinceState / T234); }
  else { const float K = EaseOut((SinceState - T234) / T234); Slide = 10.f * (1.f - K); SlideA = K; }
 }

 // Top-centre ornate mode crest (FLOW / SEQUENCE).
 {
  const FVector2D CC = At({352.f, 23.f});
  const float A = bPerfect ? .96f : bSequence ? .70f : .82f;
  if (!Draw(SCrest, bPerfect, false, CC, {122.f,36.f}, 1.f, 0.f, A, LBack)) Plate(CC, {96.f,22.f}, Coral, A, LBack);
  TextCentered(CC, bSequence ? TEXT("SEQUENCE") : TEXT("FLOW"), Font(7.5f, true), Tint(Pearl, 1.f), LText);
 }

  // Bottom-centre prompt cartouche + corner sprig.
  // Lifted clear of the overworld interact line (WBP_MelodiaInteractionPrompt sits at ~371).
  // Idle drift: a gentle ±2 design-px float on the two-beat breathe so the
  // prompt never sits laser-static while the reticle breathes beneath it.
  {
   const float Drift = State == EMelodiaBowHUDState::Idle ? 2.f * FMath::Sin(2.f * PI * BreathePhase) : 0.f;
   const FVector2D PC = At({352.f, 341.f + Drift + Slide});
   const float A = bPerfect ? .98f : bSequence ? .48f : bTargetish ? .90f : State == EMelodiaBowHUDState::Aim ? .82f : .68f;
   if (!Draw(SPrompt, bPerfect, false, PC, {270.f,51.f}, 1.f, 0.f, A * SlideA, LBack)) Plate(PC, {236.f,24.f}, Coral, A * SlideA, LBack);
   Draw(SSprig, bPerfect, false, At({235.f, 320.f + Drift + Slide}), {54.f,54.f}, 1.f, 0.f, (bPerfect ? .78f : .46f) * SlideA, LBack);
  FString Prompt;
  switch (State)
  {
  case EMelodiaBowHUDState::Idle: Prompt = bHasTarget ? FString::Printf(TEXT("RESONANCE %d%%    T LOCK    F SCYTHE"), FMath::RoundToInt(Resonance01 * 100.f)) : TEXT("RMB  AIM"); break;
  case EMelodiaBowHUDState::Aim: Prompt = bIsDrawing ? TEXT("LMB  RELEASE   \u2022   X  CANCEL") : TEXT("LMB  HOLD TO DRAW   \u2022   X  CANCEL"); break;
  case EMelodiaBowHUDState::Target: Prompt = bIsDrawing ? TEXT("LMB  RELEASE   \u2022   X  CANCEL") : FString::Printf(TEXT("RESONANCE %d%%    F SCYTHE    TAB PHRASE"), FMath::RoundToInt(Resonance01 * 100.f)); break;
  case EMelodiaBowHUDState::Perfect: Prompt = FString::Printf(TEXT("RESONANCE %d%%"), FMath::RoundToInt(Resonance01 * 100.f)); break;
  case EMelodiaBowHUDState::Sequence: Prompt = FString::Printf(TEXT("Q   W   O   P      %d%%"), FMath::RoundToInt(Resonance01 * 100.f)); break;
  }
   TextCentered(At({352.f, 338.f + Drift + Slide}), Prompt, Font(7.5f, false), Tint(Pearl, SlideA), LText);
 }

 // Target cartouche + score stem + target sprig (Target / Perfect only). 117 -> 234 ms punch-in.
 if ((bTargetish || bSequence || bCombatLocked) && bHasTarget)
 {
  const float In = SinceState < T117 && PrevState != EMelodiaBowHUDState::Target && PrevState != EMelodiaBowHUDState::Perfect
   ? EaseOut(SinceState / T117) : 1.f;
  const FVector2D TC = At({349.f, 79.f});
  if (!Draw(STargetCart, bPerfect, false, TC, {226.f,66.f}, FMath::Lerp(1.06f, 1.f, In), 0.f, (bPerfect ? 1.f : .9f) * In, LBack))
   Plate(TC, {196.f,38.f}, bPerfect ? Gold : Coral, In, LBack);
  Draw(SSprig, bPerfect, false, At({469.f, 60.f}), {54.f,54.f}, 1.f, -16.f, (bPerfect ? .86f : .7f) * In, LBack);
  Draw(SStem, bPerfect, false, At({463.f, 253.5f}), {154.f,75.f}, 1.f, 0.f, (bPerfect ? .82f : .56f) * In, LBack);
  TextCentered(At({352.f, 70.f}), TEXT("ECHO"), Font(8.f, true), Tint(Pearl, In), LText);
  TextCentered(At({352.f, 88.f}), FString::Printf(TEXT("%.0f / %.0f"), TargetHP, TargetMaxHP), Font(6.7f, false),
   Tint(bPerfect ? GoldLight : Blush, In), LText);
 }

 // HUD anchor corner (top-left filigree beside vitals).
 Draw(SCorner, false, false, At({43.5f, 87.5f}), bPerfect ? FVector2D(23.f,23.f) : FVector2D(19.f,19.f), 1.f, 0.f, bPerfect ? .64f : .34f, LBack);

 // Hit confirmation (kept from the previous HUD; recoloured to the bow palette).
 if (!bSequence && HitFeedback > 0.f)
 {
  const FLinearColor Feedback = Tint(HotCoral, HitFeedback);
  for (const FVector2D Sign : {FVector2D(-1,-1), FVector2D(1,-1), FVector2D(-1,1), FVector2D(1,1)})
  {
   TArray<FVector2f> Points = { FVector2f(C + Sign * 13.f * S * .5f), FVector2f(C + Sign * 19.f * S * .5f) };
   FSlateDrawElement::MakeLines(E, LFx, G.ToPaintGeometry(), Points, ESlateDrawEffect::None, Feedback, true, 1.5f);
  }
  TextCentered(C + FVector2D(34.f, -30.f) * S * .5f, FString::Printf(TEXT("-%.0f"), LastHitDamage), Font(9.f, true), Tint(Pearl, HitFeedback), LFx);
 }
 return LFx + 1;
}
