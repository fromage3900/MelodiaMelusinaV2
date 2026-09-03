// Native base for rhythm HUD ΓÇö NativePaint rendering of note highway, vitals, combat text.
// Adapted from MelodiaMelusina_PROD (600 lines) ΓÇö battle HUD only, no exploration/minimap/quest chrome.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaRhythmExecutionComponent.h"
#include "MelodiaRhythmHUDWidget.generated.h"

class UTexture2D;

/** Accessibility/perf motion-amplitude gate -- see Imports/UI/Specs/_MOTION_CHANNELS.md F-d.
 * Every cue's amplitude scales by tier; Off = no cue (parity with prefers-reduced-motion). */
UENUM(BlueprintType)
enum class EMelodiaMotionTier : uint8
{
	Full UMETA(DisplayName="Full"),
	Soft UMETA(DisplayName="Soft"),
	Chrome UMETA(DisplayName="Chrome"),
	Off UMETA(DisplayName="Off")
};

USTRUCT(BlueprintType)
struct FMelodiaFloatingCombatText
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	FString Text;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float SpawnTime = -1000.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	bool bAnchorEnemy = true;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	FLinearColor Tint = FLinearColor::White;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LateralSeed = 0.0f;
};

UCLASS(Blueprintable)
class MELODIACORE_API UMelodiaRhythmHUDWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="Melodia|HUD", meta=(WorldContext="WorldContextObject"))
	static UMelodiaRhythmHUDWidget* FindFirst(const UObject* WorldContextObject);

	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual void NativeConstruct() override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

	// --- Battle HUD setters ---
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetHUDMode(EMelodiaHUDMode NewMode);
	virtual void SetHUDMode_Implementation(EMelodiaHUDMode NewMode);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetJudgment(const FText& NewText);
	virtual void SetJudgment_Implementation(const FText& NewText);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void DoPulse();
	virtual void DoPulse_Implementation();

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void TriggerSparkleBurst();
	virtual void TriggerSparkleBurst_Implementation();

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetEnemyVitals(float CurrentHP, float MaxHP);
	virtual void SetEnemyVitals_Implementation(float CurrentHP, float MaxHP);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetPartyVitals(float CurrentHP, float MaxHP);
	virtual void SetPartyVitals_Implementation(float CurrentHP, float MaxHP);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetSkillPoints(int32 CurrentValue, int32 MaxValue);
	virtual void SetSkillPoints_Implementation(int32 CurrentValue, int32 MaxValue);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetUltimateGauge(float CurrentValue, float MaxValue, bool bReady);
	virtual void SetUltimateGauge_Implementation(float CurrentValue, float MaxValue, bool bReady);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetEnemyBreakGauge(float CurrentValue, float MaxValue, bool bBroken);
	virtual void SetEnemyBreakGauge_Implementation(float CurrentValue, float MaxValue, bool bBroken);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetNoteHighwayActive(bool bActive, const TArray<FMelodiaHighwayNote>& Notes, float BeatPosition, float ScrollBeatsAhead);
	virtual void SetNoteHighwayActive_Implementation(bool bActive, const TArray<FMelodiaHighwayNote>& Notes, float BeatPosition, float ScrollBeatsAhead);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void ShowActionPrompt(const FString& PromptText);
	virtual void ShowActionPrompt_Implementation(const FString& PromptText);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void SetBattlePhaseBanner(const FString& PhaseLabel);
	virtual void SetBattlePhaseBanner_Implementation(const FString& PhaseLabel);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void PushFloatingCombatText(const FString& Text, bool bAnchorEnemy, FLinearColor Tint);
	virtual void PushFloatingCombatText_Implementation(const FString& Text, bool bAnchorEnemy, FLinearColor Tint);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void TriggerDamageFlash(float DamageValue);
	virtual void TriggerDamageFlash_Implementation(float DamageValue);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Rhythm HUD")
	void ShowBattleStatus(const FString& StatusText);
	virtual void ShowBattleStatus_Implementation(const FString& StatusText);

	// --- Style config ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Style")
	FLinearColor PanelTint = FLinearColor(0.09f, 0.07f, 0.14f, 0.90f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Style")
	FLinearColor FiligreeTint = FLinearColor(0.98f, 0.82f, 0.38f, 0.94f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Style")
	FLinearColor SparkleTint = FLinearColor(0.86f, 0.74f, 1.0f, 0.96f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Style")
	FLinearColor UltimateGaugeTint = FLinearColor(0.62f, 0.48f, 0.98f, 0.95f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Style")
	FLinearColor EnemyHPBarTint = FLinearColor(0.96f, 0.28f, 0.42f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Style")
	FLinearColor PartyHPBarTint = FLinearColor(0.42f, 1.0f, 0.72f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Style")
	FLinearColor BreakGaugeTint = FLinearColor(0.98f, 0.88f, 0.36f, 1.0f);

	// --- Note highway geometry ---
	// PaintNoteHighway drew every note at one Y regardless of LaneIndex, so a four-lane
	// chart rendered as a single undifferentiated strip: the player could not tell which
	// of Q/W/O/P a note belonged to. These values place the painted lanes over the UMG
	// LaneRow (Lane_D/F/J/K, bottom-anchored, 880x140) so notes land on the key they
	// actually map to. They are EditAnywhere because the UMG row is authored in the
	// widget and these must follow it — if you move LaneRow, move these.

	/** Number of lanes. Must match the UMG LaneRow child count and the input map. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Highway", meta=(ClampMin="1", ClampMax="8"))
	int32 HighwayLaneCount = 4;

	/** Total width of the lane block, matching the UMG LaneRow width. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Highway", meta=(ClampMin="1.0"))
	float HighwayLaneRowWidth = 880.0f;

	/** Distance from the bottom edge to the hit line, matching where LaneRow sits. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Highway", meta=(ClampMin="0.0"))
	float HighwayHitLineFromBottom = 188.0f;

	/** How far above the hit line notes spawn. Larger = more read time at the same BPM. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Highway", meta=(ClampMin="50.0"))
	float HighwayApproachHeight = 620.0f;

	/** Note square size in pixels. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Highway", meta=(ClampMin="4.0"))
	float HighwayNoteSize = 28.0f;

	// --- State (readable from Blueprint) ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	EMelodiaHUDMode ActiveHUDMode = EMelodiaHUDMode::Exploration;

	// Sprint and Glide state flags
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	bool bIsSprinting = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	bool bIsGliding = false;

	UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm HUD")
	void SetSprintGlide(bool bSprint, bool bGlide);

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	FString LastActionPromptText;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	FString LastBattleStatusText;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	FString LastBattlePhaseLabel;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastEnemyHP = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastEnemyMaxHP = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastPartyHP = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastPartyMaxHP = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	int32 LastSkillPoints = 3;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	int32 LastSkillPointMax = 5;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastUltimateGaugeValue = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastUltimateGaugeMax = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	bool bUltimateReadyVisible = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastEnemyToughness = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastEnemyToughnessMax = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	bool bEnemyBreakVisible = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	bool bNoteHighwayActive = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	TArray<FMelodiaHighwayNote> HighwayNotes;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float HighwayBeatPosition = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float HighwayScrollBeatsAhead = 2.5f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	TArray<FMelodiaFloatingCombatText> FloatingCombatTexts;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	FText LastJudgmentText;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastPulseTime = -1000.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastSparkleBurstTime = -1000.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastDamageFlashTime = -1000.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD")
	float LastBannerTime = -1000.0f;

	// --- Motion-channel cues (Imports/UI/Specs/_MOTION_CHANNELS.md F-a/F-b/F-c) ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD|Motion")
	float LastBassPulseTime = -1000.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD|Motion")
	float LastPerfectHitTime = -1000.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm HUD|Motion")
	float LastBreakRevealTime = -1000.0f;

	/** F-d motion-tier gate; every cue's amplitude should scale by this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm HUD|Motion")
	EMelodiaMotionTier MotionTier = EMelodiaMotionTier::Full;

	/** Returns 0 for Off, else 1 -- multiply cue amplitude/opacity by this so Off is a true no-op. */
	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm HUD|Motion")
	float GetMotionAmplitude() const { return MotionTier == EMelodiaMotionTier::Off ? 0.0f : 1.0f; }

	/** F-b: call on a Perfect-grade hit to drive the NoteTrailIri cue. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm HUD|Motion")
	void NotifyPerfectHit();

private:
	int32 BeatCountForBassProxy = 0;

public:

	// Smoothed display values (lerped in NativeTick)
	UPROPERTY(BlueprintReadOnly, Transient, Category="Melodia|Rhythm HUD|Style")
	float DisplayedEnemyHP = 0.0f;

	UPROPERTY(BlueprintReadOnly, Transient, Category="Melodia|Rhythm HUD|Style")
	float DisplayedPartyHP = 100.0f;

	UPROPERTY(BlueprintReadOnly, Transient, Category="Melodia|Rhythm HUD|Style")
	float DisplayedUltimate = 0.0f;

	UPROPERTY(BlueprintReadOnly, Transient, Category="Melodia|Rhythm HUD|Style")
	float DisplayedEnemyToughness = 100.0f;

private:
	float GetHUDTimeSeconds() const;
	void UpdateSmoothedBars(float InDeltaTime);
	void PaintBattleHUD(FSlateWindowElementList& OutDrawElements, const FGeometry& AllottedGeometry, int32& CurrentLayer) const;
	void PaintNoteHighway(FSlateWindowElementList& OutDrawElements, const FGeometry& AllottedGeometry, int32& CurrentLayer) const;
	void PaintFloatingCombatTexts(FSlateWindowElementList& OutDrawElements, const FGeometry& AllottedGeometry, int32& CurrentLayer) const;
	void LoadPresentationTextures();

	bool bDisplayedValuesInitialized = false;

	/**
	 * True when the execution-component sync lane in NativeTick is the last
	 * writer of the note highway. The ambient lane only clears what IT set:
	 * another integration (the stock JRPG rhythm subsystem) drives the same
	 * native-painted highway, and an unconditional clear every tick would erase
	 * its notes one frame after PushHighwayToHUD sets them.
	 */
	bool bExecutionDrivingHighway = false;

	// Figma exports are optional presentation resources. The HUD remains functional
	// with primitive Slate fallback painting if an asset is unavailable.
	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> HighwayBackgroundTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> HitLineTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> NoteHeadTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> NoteHeadBeamTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> EnemyGlowTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> SkillChipTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> FiligreeCornerTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> GradePerfectTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> GradeGreatTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> GradeGoodTexture;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> GradeMissTexture;
};
