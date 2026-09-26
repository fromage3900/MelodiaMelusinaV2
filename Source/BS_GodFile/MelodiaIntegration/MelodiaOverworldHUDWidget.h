#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaOverworldHUDWidget.generated.h"

class UProgressBar;
class UTextBlock;
class UWidget;

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

	/** Seconds the area caption stays up after the HUD appears. */
	UPROPERTY(EditAnywhere, Category = "Melodia|HUD", meta = (ClampMin = "0.0"))
	float AreaCaptionSeconds = 4.0f;

	UPROPERTY(EditAnywhere, Category = "Melodia|HUD", meta = (ClampMin = "0.05"))
	float RefreshSeconds = 0.25f;

private:
	void RefreshVitals();
	void RefreshQuest();

	float RefreshAccumulator = 0.0f;
	float CaptionRemaining = 0.0f;
};
