#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaCosmicOrreryWidget.generated.h"

class UButton;
class UImage;
class UProgressBar;
class UTextBlock;
class UWidget;
class USoundBase;

/**
 * Definition of an astrological planetary archetype in the Cosmic Orrery.
 */
USTRUCT(BlueprintType)
struct FMelodiaOrreryArchetype
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery")
	FName ArchetypeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery")
	FText Subtitle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery")
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery")
	FText MetricLabel;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery")
	float MetricValue = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery")
	FLinearColor AccentColor = FLinearColor(0.79f, 0.66f, 0.42f, 1.0f);
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaOrreryArchetypeSelected, int32, ArchetypeIndex, FName, ArchetypeId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FMelodiaOrreryClosed);

/**
 * Native C++ controller for WBP_Melodia_CosmicOrrery.
 * Provides:
 * - Real-time continuous celestial ring rotation and stardust drift
 * - 7-node elliptical trigonometric planetary orbit simulation
 * - Smooth camera / node focus interpolation
 * - Full Keyboard & Gamepad navigation (Arrows, D-Pad, Enter/Space, Esc/Back)
 * - Dynamic archetypes context switching (Party, Instruments, Skills, Journal, Map, Archive, Settings)
 * - Music Clock beat synchronization and harmonic sheen
 * - Clean input context isolation via UMelodiaInputContextSubsystem
 */
UCLASS(Abstract, BlueprintType, Blueprintable)
class BS_GODFILE_API UMelodiaCosmicOrreryWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UMelodiaCosmicOrreryWidget(const FObjectInitializer& ObjectInitializer);

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Orrery|Events")
	FMelodiaOrreryArchetypeSelected OnArchetypeSelected;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Orrery|Events")
	FMelodiaOrreryClosed OnOrreryClosed;

	/** Step orbit counter-clockwise (to previous planetary node) */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery|Navigation")
	void SelectPreviousArchetype();

	/** Step orbit clockwise (to next planetary node) */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery|Navigation")
	void SelectNextArchetype();

	/** Directly set the active focused archetype by index (0..6) */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery|Navigation")
	void SetFocusedArchetypeIndex(int32 NewIndex);

	/** Activate the currently focused archetype (Enter / Select) */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery|Navigation")
	void ActivateCurrentArchetype();

	/** Close the Orrery modal and restore exploration input context */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery|Navigation")
	void CloseOrrery();

	/** Current focused archetype index (0..6) */
	UFUNCTION(BlueprintPure, Category = "Melodia|Orrery")
	int32 GetFocusedArchetypeIndex() const { return FocusedIndex; }

	/** Total registered archetypes */
	UFUNCTION(BlueprintPure, Category = "Melodia|Orrery")
	int32 GetArchetypeCount() const { return Archetypes.Num(); }

	/** Get definition for a specific archetype */
	UFUNCTION(BlueprintPure, Category = "Melodia|Orrery")
	const FMelodiaOrreryArchetype& GetArchetype(int32 Index) const;

	/**
	 * Deprecated path: the Orrery pushes and pops its own Menu context. Kept for source compatibility;
	 * it only adopts a handle when the Orrery does not already own one, so it can never orphan a push.
	 */
	void SetContextHandle(FMelodiaInputContextHandle Handle) { if (!OwnContextHandle.IsValid()) { OwnContextHandle = Handle; } }

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnPreviewKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	/** Astronomical Orrery Core Visuals */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Orrery_Rings_Img;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Orrery_Hub_Img;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Orrery_Glow_Img;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Orrery_Backdrop;

	/** 7 Planetary Spheres (Both 1-based and 0-based support for UMG compatibility) */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Planet_1;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Planet_2;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Planet_3;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Planet_4;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Planet_5;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Planet_6;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Planet_7;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Planet_0;

	/** 7 Menu Row Items (Both 1-based and 0-based support) */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> MenuItem_1;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> MenuItem_2;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> MenuItem_3;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> MenuItem_4;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> MenuItem_5;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> MenuItem_6;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> MenuItem_7;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> MenuItem_0;

	/** Menu row texts */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> MenuItem_1_Text;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> MenuItem_2_Text;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> MenuItem_3_Text;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> MenuItem_4_Text;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> MenuItem_5_Text;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> MenuItem_6_Text;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> MenuItem_7_Text;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> MenuText_0;

	/** Storybook Context & Detail Presentation */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> ContextTitle;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> ContextCategory;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> ContextDesc;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> ContextStats;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Detail_Card;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Detail_Title;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Detail_Subtitle;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Detail_Description;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UProgressBar> Detail_MetricBar;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Detail_MetricLabel;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Detail_MetricValue;

	/** Persona presentation */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UImage> PersonaAvatar_Img;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> PersonaName;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> PersonaBadgeText;

	/** Bottom navigation ribbons and key prompts */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> BottomCurrencyText;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> BottomLegendText;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Key_Orbit;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Key_Select;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Key_Close;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Close_Button;

	/** Floating stardust elements */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Stardust_1;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Stardust_2;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Stardust_3;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Stardust_4;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Stardust_5;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Stardust_6;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Stardust_0;

	/** Configurable Archetypes */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery|Config")
	TArray<FMelodiaOrreryArchetype> Archetypes;

	/** Sound cues */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery|Audio")
	TObjectPtr<USoundBase> OrbitSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery|Audio")
	TObjectPtr<USoundBase> SelectSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery|Audio")
	TObjectPtr<USoundBase> CloseSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery|Audio")
	TObjectPtr<USoundBase> HoverSound;

	/** Orbit orbital radii */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery|Orbit")
	float OrbitRadiusX = 260.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery|Orbit")
	float OrbitRadiusY = 110.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery|Orbit")
	float RingRotationSpeed = 8.0f;

private:
	void InitArchetypesIfEmpty();
	void RefreshActivePresentation();
	void UpdateOrbitSimulation(float InDeltaTime);
	void UpdateStardustDrift(float InDeltaTime);
	/** Open-side presentation: collapse world combat HUDs, UI-only input with cursor, user focus. */
	void AcquireMenuPresentation();
	/** Idempotent close-side counterpart: restore combat HUDs, pop the one owned Menu context. */
	void ReleaseMenuOwnership();

	UFUNCTION() void HandlePlanet1Clicked();
	UFUNCTION() void HandlePlanet2Clicked();
	UFUNCTION() void HandlePlanet3Clicked();
	UFUNCTION() void HandlePlanet4Clicked();
	UFUNCTION() void HandlePlanet5Clicked();
	UFUNCTION() void HandlePlanet6Clicked();
	UFUNCTION() void HandlePlanet7Clicked();
	UFUNCTION() void HandlePlanet0Clicked();

	UFUNCTION() void HandleMenuItem1Clicked();
	UFUNCTION() void HandleMenuItem2Clicked();
	UFUNCTION() void HandleMenuItem3Clicked();
	UFUNCTION() void HandleMenuItem4Clicked();
	UFUNCTION() void HandleMenuItem5Clicked();
	UFUNCTION() void HandleMenuItem6Clicked();
	UFUNCTION() void HandleMenuItem7Clicked();
	UFUNCTION() void HandleMenuItem0Clicked();

	UFUNCTION() void HandleCloseButtonClicked();

	int32 FocusedIndex = 0;
	float CurrentOrbitAngle = 0.0f;
	float TargetOrbitAngle = 0.0f;
	float RingsContinuousAngle = 0.0f;
	float RunningTime = 0.0f;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UWidget>> Planets;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UWidget>> MenuItems;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UTextBlock>> MenuTexts;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UWidget>> StardustWidgets;

	FMelodiaInputContextHandle OwnContextHandle;
	bool bSuppressedWorldCombatUI = false;
};
