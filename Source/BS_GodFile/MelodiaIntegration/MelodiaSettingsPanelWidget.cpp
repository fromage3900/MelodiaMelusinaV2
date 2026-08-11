#include "MelodiaSettingsPanelWidget.h"

#include "Components/CheckBox.h"
#include "Components/Button.h"
#include "Components/Slider.h"
#include "CommonAnimatedSwitcher.h"
#include "MelodiaGameUserSettings.h"

void UMelodiaSettingsPanelWidget::NativeConstruct()
{
	Super::NativeConstruct();

	UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get();
	if (Settings)
	{
		if (Slider_MasterVolume) Slider_MasterVolume->SetValue(Settings->MasterVolume);
		if (Slider_MusicVolume) Slider_MusicVolume->SetValue(Settings->MusicVolume);
		if (Slider_SFXVolume) Slider_SFXVolume->SetValue(Settings->SFXVolume);
		if (Slider_UIScale) Slider_UIScale->SetValue((Settings->UIScale - 0.8f) / 0.5f);
		if (Check_ReduceMotion) Check_ReduceMotion->SetIsChecked(Settings->bReduceMotion);
		if (Check_HighContrast) Check_HighContrast->SetIsChecked(Settings->bHighContrastText);
		if (Check_MinimalHUD) Check_MinimalHUD->SetIsChecked(Settings->bMinimalReactiveHUD);
	}

	if (Slider_MasterVolume) Slider_MasterVolume->OnValueChanged.AddUniqueDynamic(this, &ThisClass::HandleMasterVolumeChanged);
	if (Slider_MusicVolume) Slider_MusicVolume->OnValueChanged.AddUniqueDynamic(this, &ThisClass::HandleMusicVolumeChanged);
	if (Slider_SFXVolume) Slider_SFXVolume->OnValueChanged.AddUniqueDynamic(this, &ThisClass::HandleSFXVolumeChanged);
	if (Slider_UIScale) Slider_UIScale->OnValueChanged.AddUniqueDynamic(this, &ThisClass::HandleUIScaleChanged);
	if (Check_ReduceMotion) Check_ReduceMotion->OnCheckStateChanged.AddUniqueDynamic(this, &ThisClass::HandleReduceMotionChanged);
	if (Check_HighContrast) Check_HighContrast->OnCheckStateChanged.AddUniqueDynamic(this, &ThisClass::HandleHighContrastChanged);
	if (Check_MinimalHUD) Check_MinimalHUD->OnCheckStateChanged.AddUniqueDynamic(this, &ThisClass::HandleMinimalHUDChanged);
	if (Btn_TabAudio) Btn_TabAudio->OnClicked.AddUniqueDynamic(this, &ThisClass::ShowAudioTab);
	if (Btn_TabDisplay) Btn_TabDisplay->OnClicked.AddUniqueDynamic(this, &ThisClass::ShowDisplayTab);
	if (Btn_TabAccessibility) Btn_TabAccessibility->OnClicked.AddUniqueDynamic(this, &ThisClass::ShowAccessibilityTab);
	if (Btn_TabControls) Btn_TabControls->OnClicked.AddUniqueDynamic(this, &ThisClass::ShowControlsTab);
	SetActiveTab(0);
}

void UMelodiaSettingsPanelWidget::ApplyCurrentPreferences()
{
	if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get())
	{
		Settings->ApplyMelodiaPreferences(this);
	}
}

void UMelodiaSettingsPanelWidget::HandleMasterVolumeChanged(float Value)
{
	if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get()) Settings->MasterVolume = Value;
	ApplyCurrentPreferences();
}
void UMelodiaSettingsPanelWidget::HandleMusicVolumeChanged(float Value)
{
	if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get()) Settings->MusicVolume = Value;
	ApplyCurrentPreferences();
}
void UMelodiaSettingsPanelWidget::HandleSFXVolumeChanged(float Value)
{
	if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get()) Settings->SFXVolume = Value;
	ApplyCurrentPreferences();
}
void UMelodiaSettingsPanelWidget::HandleUIScaleChanged(float NormalizedValue)
{
	if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get()) Settings->UIScale = 0.8f + (FMath::Clamp(NormalizedValue, 0.0f, 1.0f) * 0.5f);
	ApplyCurrentPreferences();
}
void UMelodiaSettingsPanelWidget::HandleReduceMotionChanged(bool bChecked)
{
	if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get()) Settings->bReduceMotion = bChecked;
	ApplyCurrentPreferences();
}
void UMelodiaSettingsPanelWidget::HandleHighContrastChanged(bool bChecked)
{
	if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get()) Settings->bHighContrastText = bChecked;
	ApplyCurrentPreferences();
}
void UMelodiaSettingsPanelWidget::HandleMinimalHUDChanged(bool bChecked)
{
	if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get()) Settings->bMinimalReactiveHUD = bChecked;
	ApplyCurrentPreferences();
}

void UMelodiaSettingsPanelWidget::SetActiveTab(const int32 TabIndex)
{
	if (ContentSwitcher && ContentSwitcher->GetNumWidgets() > TabIndex)
	{
		ContentSwitcher->SetActiveWidgetIndex(TabIndex);
	}
}

void UMelodiaSettingsPanelWidget::ShowAudioTab() { SetActiveTab(0); }
void UMelodiaSettingsPanelWidget::ShowDisplayTab() { SetActiveTab(1); }
void UMelodiaSettingsPanelWidget::ShowAccessibilityTab() { SetActiveTab(2); }
void UMelodiaSettingsPanelWidget::ShowControlsTab() { SetActiveTab(3); }
