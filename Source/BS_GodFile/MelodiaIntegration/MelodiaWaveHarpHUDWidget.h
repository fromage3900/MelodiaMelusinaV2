#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Styling/SlateBrush.h"
#include "MelodiaWaveHarpHUDWidget.generated.h"

class UFont;
class UTexture2D;
class UMelodiaWaveHarpCombatComponent;

/** Figma "Bow HUD v3.6/v3.7 Ornate Score Cartouches" reticle states. */
UENUM(BlueprintType)
enum class EMelodiaBowHUDState : uint8
{
 Idle,
 Aim,
 Target,
 Perfect,
 Sequence
};

/**
 * One swappable art slot. Base is required for textured drawing; Lit and Perfect are optional
 * state variants (gold #C9A86A lives ONLY in Perfect variants). A missing Base falls back to the
 * code-drawn primitive so the HUD never disappears while handpaint is in progress.
 */
USTRUCT(BlueprintType)
struct FMelodiaBowHUDTextureSlot
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD") TSoftObjectPtr<UTexture2D> Base;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD") TSoftObjectPtr<UTexture2D> Lit;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD") TSoftObjectPtr<UTexture2D> Perfect;
};

/**
 * Read-only bow guidance drawn over the existing UI bridge (UMelodiaUIBridgeSubsystem is the ONLY
 * writer that creates/removes this widget and the only one that toggles the stock OverworldHUD
 * Reticle). Layout follows Figma Yx8ud7n39NdWZvnNvo4Xlf section 256:6496 (v3.7 cartouche lookdev):
 * top-centre mode crest, centre layered reticle, target cartouche in Target/Perfect, bottom-centre
 * prompt cartouche. Inputs (Figma contract): reticle_visible, is_aiming, draw_tension, loose_count.
 */
UCLASS()
class BS_GODFILE_API UMelodiaWaveHarpHUDWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UMelodiaWaveHarpHUDWidget(const FObjectInitializer& ObjectInitializer);
 virtual void NativeConstruct() override;
 virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
 virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& Geometry,
  const FSlateRect& Cull, FSlateWindowElementList& Elements, int32 Layer,
  const FWidgetStyle& Style, bool bEnabled) const override;

 /** reticle_visible: true while the bow reticle owns screen centre (bridge hides the stock Reticle). */
 UFUNCTION(BlueprintPure, Category="Melodia|BowHUD") bool IsBowReticleVisible() const { return bReticleVisible; }
 /** SEQUENCE yields centre-screen: neither the bow reticle nor the stock reticle may draw. */
 UFUNCTION(BlueprintPure, Category="Melodia|BowHUD") bool IsCenterYielded() const { return State == EMelodiaBowHUDState::Sequence; }
 UFUNCTION(BlueprintPure, Category="Melodia|BowHUD") EMelodiaBowHUDState GetBowHUDState() const { return State; }

 // ---- Swappable art (defaults point at the IMPORT_MANIFEST.md UE paths; reimport a handpainted
 // PNG over the same asset, or override here in a WBP subclass -- no code change needed). ----
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot ApertureRing;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot InnerAperture;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot TensionArc1;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot TensionArc2;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot TensionArc3;
 /** One petal, drawn five times and rotated at runtime. Base = outline, Lit = loosed, Perfect = gold rim. */
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot Petal;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot CenterRosette;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot CenterDot;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot TargetLock;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot ReleaseRipple;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Reticle") FMelodiaBowHUDTextureSlot SequenceCollapse;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Compass") FMelodiaBowHUDTextureSlot CompassRadialScore;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Compass") FMelodiaBowHUDTextureSlot CompassChromaticSpokes;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Frame") FMelodiaBowHUDTextureSlot ModeCrest;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Frame") FMelodiaBowHUDTextureSlot PromptCartouche;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Frame") FMelodiaBowHUDTextureSlot TargetCartouche;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Frame") FMelodiaBowHUDTextureSlot ScoreCornerSprig;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Frame") FMelodiaBowHUDTextureSlot ScoreStem;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Frame") FMelodiaBowHUDTextureSlot FrameCorner;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Perfect") FMelodiaBowHUDTextureSlot PerfectBloomRipple;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Perfect") FMelodiaBowHUDTextureSlot PerfectBloomFiligree;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Perfect") FMelodiaBowHUDTextureSlot PerfectReleaseCrest;
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Art|Perfect") FMelodiaBowHUDTextureSlot PerfectGlint;

 /** Prompt/label font. Figma uses Kaisei Decol (not in project yet); Inter token is the stand-in. */
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Type") TSoftObjectPtr<UFont> LabelFont;

 /** 1.0 = Figma-faithful (704x396 template scaled to viewport height). */
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Layout", meta=(ClampMin="0.25", ClampMax="2.0")) float LayoutScale = 1.0f;
 /** Figma Idle shows the bow reticle while the WaveHarp is ready; turn off to only show it while aiming/drawing. */
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Layout") bool bShowReticleWhenIdle = true;
 /** Used only when UMelodiaMusicClockSubsystem reports no tempo. 128 BPM => 469/234/117 ms beats. */
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Motion", meta=(ClampMin="40", ClampMax="240")) float FallbackBPM = 128.0f;
 /** draw_tension thresholds that light tension arcs 1..3. */
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|BowHUD|Motion") FVector ArcTensionThresholds = FVector(0.2f, 0.55f, 0.9f);

private:
 enum ESlot : uint8 { SApertureRing, SInnerAperture, SArc1, SArc2, SArc3, SPetal, SRosette, SDot, STargetLock,
  SRipple, SCollapse, SCompassScore, SCompassSpokes, SCrest, SPrompt, STargetCart, SSprig, SStem, SCorner,
  SBloomRipple, SBloomFiligree, SReleaseCrest, SGlint, SNum };
 struct FResolvedSlot
 {
  FSlateBrush Base, Lit, Perfect;
  bool bBase = false, bLit = false, bPerfect = false;
  const FSlateBrush* Pick(bool bWantPerfect, bool bWantLit) const
  {
   if (bWantPerfect && bPerfect) return &Perfect;
   if (bWantLit && bLit) return &Lit;
   return bBase ? &Base : nullptr;
  }
 };
 FMelodiaBowHUDTextureSlot* SlotProperty(ESlot InSlot);
 void ResolveArt();
 bool ResolveBrush(const TSoftObjectPtr<UTexture2D>& Soft, FSlateBrush& Out);
 const UMelodiaWaveHarpCombatComponent* FindCombat() const;
 float BeatSeconds() const;

 // Game-thread state sampled in NativeTick; NativePaint only reads it.
 EMelodiaBowHUDState State = EMelodiaBowHUDState::Idle;
 EMelodiaBowHUDState PrevState = EMelodiaBowHUDState::Idle;
 bool bReticleVisible = false;
 bool bIsAiming = false;
 bool bIsDrawing = false;
 bool bHasTarget = false;
 float DrawTension = 0.f;
 int32 LooseCount = 0;
 float ChordFeedback = 0.f;
 float HitFeedback = 0.f;
 float LastHitDamage = 0.f;
 float TargetHP = 0.f, TargetMaxHP = 0.f;
 int32 LastShotsFired = 0;
 double Now = 0.0;
 double StateEnteredAt = -100.0;
 double BloomStartedAt = -100.0;
 double LooseStartedAt = -100.0;
 float Beat = 60.f / 128.f;
 float BreathePhase = 0.f;
 float ReticleFade = 0.f;
 float SequenceBlend = 0.f;
 float ArcLight[3] = {0.f, 0.f, 0.f};

 FResolvedSlot Art[SNum];
 UPROPERTY(Transient) TArray<TObjectPtr<UTexture2D>> LoadedTextures;
 UPROPERTY(Transient) TObjectPtr<UFont> InterFont;
};
