#pragma once

#include "CoreMinimal.h"
#include "CommonActivatableWidget.h"
#include "MelodiaSettingsPanelWidget.generated.h"

class UCheckBox;
class UButton;
class UCommonAnimatedSwitcher;
class USlider;

/** Native behavior for the authored WBP_MelodiaSettings surface. */
UCLASS(Abstract)
class BS_GODFILE_API UMelodiaSettingsPanelWidget : public UCommonActivatableWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;

	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<USlider> Slider_MasterVolume;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<USlider> Slider_MusicVolume;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<USlider> Slider_SFXVolume;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<USlider> Slider_UIScale;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UCheckBox> Check_ReduceMotion;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UCheckBox> Check_HighContrast;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UCheckBox> Check_MinimalHUD;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UCommonAnimatedSwitcher> ContentSwitcher;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UButton> Btn_TabAudio;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UButton> Btn_TabDisplay;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UButton> Btn_TabAccessibility;
	UPROPERTY(meta=(BindWidgetOptional))
	TObjectPtr<UButton> Btn_TabControls;

	UFUNCTION()
	void HandleMasterVolumeChanged(float Value);
	UFUNCTION()
	void HandleMusicVolumeChanged(float Value);
	UFUNCTION()
	void HandleSFXVolumeChanged(float Value);
	UFUNCTION()
	void HandleUIScaleChanged(float NormalizedValue);
	UFUNCTION()
	void HandleReduceMotionChanged(bool bChecked);
	UFUNCTION()
	void HandleHighContrastChanged(bool bChecked);
	UFUNCTION()
	void HandleMinimalHUDChanged(bool bChecked);
	UFUNCTION()
	void ShowAudioTab();
	UFUNCTION()
	void ShowDisplayTab();
	UFUNCTION()
	void ShowAccessibilityTab();
	UFUNCTION()
	void ShowControlsTab();

private:
	void ApplyCurrentPreferences();
	void SetActiveTab(int32 TabIndex);
};
