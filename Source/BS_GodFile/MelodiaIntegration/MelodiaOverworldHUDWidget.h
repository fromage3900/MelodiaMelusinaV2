#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaOverworldHUDWidget.generated.h"

class UButton;
class UImage;
class UProgressBar;
class UTextBlock;
class UWidget;
class USoundBase;

/**
 * Native base for WBP_Melodia_OverworldHUD. Fills the HUD from its authorities: party vitals from
 * the JRPG template's BP_JRPGPlayerController.playerUnits (read by name -- guarded by
 * Melodia.Wiring.OverworldHUDTemplateContract), the active quest from UMelodiaPersonaSubsystem,
 * the area caption from the map. Fields with no authority are hidden, never faked.
 */
UCLASS(Abstract)
class BS_GODFILE_API UMelodiaOverworldHUDWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Names read from the template by reflection; the contract test asserts they still resolve. */
	static const FName PlayerUnitsProperty;
	static const TCHAR* CurrentHPPrefix;
	static const TCHAR* CurrentMPPrefix;
	static const TCHAR* ExpPrefix;
	static const FName FirstLevelStatsProperty;
	static const TCHAR* MaxHPPrefix;
	static const TCHAR* MaxMPPrefix;

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UProgressBar> VitalityBar;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UProgressBar> ResonanceBar;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> VitalsText;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> PlayerName;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> PlayerLevel;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> AreaName;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> AreaTitle;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> ChapterLine;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UWidget> TitleBlock;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UProgressBar> TitleResonance;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> TitleResonanceText;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UWidget> QuestCard;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> QuestHeader;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> QuestTitle;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> QuestBody;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> QuestMotifs;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UProgressBar> QuestProgress;

	/** Top-level navigation buttons bound to WBP_Melodia_OverworldHUD */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UButton> Sys_1;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UButton> Sys_2;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UButton> Sys_Journal;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UButton> Sys_Settings;

	/** Optional button icons */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UImage> Sys_1_Icon;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UImage> Sys_2_Icon;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UImage> Sys_Journal_Icon;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UImage> Sys_Settings_Icon;

	/** Optional minimap compass and framing elements */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UImage> Minimap_NorthStar;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UImage> Minimap_Bezel;

	/** Optional contextual interaction prompt */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> InteractPrompt;

	/** Optional center-screen reticle */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> Reticle;

	/** Sound cues for UI interactions */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|UI|Audio")
	TObjectPtr<USoundBase> MenuOpenSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|UI|Audio")
	TObjectPtr<USoundBase> MenuCloseSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|UI|Audio")
	TObjectPtr<USoundBase> ButtonHoverSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|UI|Audio")
	TObjectPtr<USoundBase> ButtonClickSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|UI|Audio")
	TObjectPtr<USoundBase> LowVitalityPulseSound;

	/** Configurable destination class for the Cosmic Orrery menu */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|UI|Navigation")
	TSoftClassPtr<UUserWidget> OrreryMenuClass;

	/** Configurable destination class for the Compendium / Journal archive */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|UI|Navigation")
	TSoftClassPtr<UUserWidget> CompendiumMenuClass;

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSysSettingsClicked();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSysJournalClicked();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSys1Clicked();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSys2Clicked();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSysSettingsHovered();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSysSettingsUnhovered();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSysJournalHovered();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSysJournalUnhovered();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSys1Hovered();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSys1Unhovered();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSys2Hovered();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void HandleSys2Unhovered();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Navigation")
	void OpenOrreryWithArchetype(int32 ArchetypeIndex);

	UFUNCTION()
	void HandleOrreryClosed();

	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	/** Seconds the area caption stays up after the HUD appears. */
	UPROPERTY(EditAnywhere, Category = "Melodia|HUD", meta = (ClampMin = "0.0"))
	float AreaCaptionSeconds = 4.0f;

	UPROPERTY(EditAnywhere, Category = "Melodia|HUD", meta = (ClampMin = "0.05"))
	float RefreshSeconds = 0.25f;

private:
	void RefreshVitals();
	void RefreshQuest();

	UPROPERTY(Transient)
	TObjectPtr<UUserWidget> ActiveOrreryWidget;

	FMelodiaInputContextHandle OrreryContextHandle;

	float RefreshAccumulator = 0.0f;
	float CaptionRemaining = 0.0f;
	float RunningTime = 0.0f;

	float SysSettingsHoverAlpha = 0.0f;
	float SysJournalHoverAlpha = 0.0f;
	float Sys1HoverAlpha = 0.0f;
	float Sys2HoverAlpha = 0.0f;

	bool bSysSettingsHovered = false;
	bool bSysJournalHovered = false;
	bool bSys1Hovered = false;
	bool bSys2Hovered = false;

	float CachedVitalityPercent = 1.0f;
};
