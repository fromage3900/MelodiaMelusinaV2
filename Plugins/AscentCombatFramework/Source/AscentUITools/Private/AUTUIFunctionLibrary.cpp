// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AUTUIFunctionLibrary.h"
#include "AUTDeveloperSettings.h"
#include "AUTGameUserSettings.h"
#include "AUTThemeDataAsset.h"
#include "AUTTypes.h"
#include "Engine/Engine.h"
#include "Blueprint/UserWidget.h"

UAUTGameUserSettings* UAUTUIFunctionLibrary::GetGameUserSettings()
{
    return Cast<UAUTGameUserSettings>(GEngine->GetGameUserSettings());
}

bool UAUTUIFunctionLibrary::TryGetButtonStyle(int32 styleIndex, FAUTButtonStyle& outStyle)
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();
    if (settings) {
        const UAUTThemeDataAsset* theme = settings->GetTheme();
        if (theme) {
            if (theme->ButtonsStyle.IsValidIndex(styleIndex)) {
                outStyle = theme->ButtonsStyle[styleIndex];
                return true;
            }
        }
    }
    return false;
}

bool UAUTUIFunctionLibrary::TryGetSliderStyle(int32 styleIndex, FAUTSliderStyle& outStyle)
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();
    if (settings) {
        const UAUTThemeDataAsset* theme = settings->GetTheme();
        if (theme) {
            if (theme->SlidersStyle.IsValidIndex(styleIndex)) {
                outStyle = theme->SlidersStyle[styleIndex];
                return true;
            }
        }
    }
    return false;
}

bool UAUTUIFunctionLibrary::TryGetComboBoxStyle(int32 styleIndex, FAUTComboBoxStyle& outStyle)
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();
    if (settings) {
        const UAUTThemeDataAsset* theme = settings->GetTheme();
        if (theme) {
            if (theme->ComboBoxesStyle.IsValidIndex(styleIndex)) {
                outStyle = theme->ComboBoxesStyle[styleIndex];
                return true;
            }
        }
    }
    return false;
}

bool UAUTUIFunctionLibrary::TryGetSpinnerStyle(int32 styleIndex, FAUTSpinnerStyle& outStyle)
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();
    if (settings) {
        const UAUTThemeDataAsset* theme = settings->GetTheme();
        if (theme) {
            if (theme->SpinnersStyle.IsValidIndex(styleIndex)) {
                outStyle = theme->SpinnersStyle[styleIndex];
                return true;
            }
        }
    }
    return false;
}

bool UAUTUIFunctionLibrary::TryGetCheckBoxStyle(int32 styleIndex, FAUTCheckBoxStyle& outStyle)
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();
    if (settings) {
        const UAUTThemeDataAsset* theme = settings->GetTheme();
        if (theme) {
            if (theme->CheckBoxesStyle.IsValidIndex(styleIndex)) {
                outStyle = theme->CheckBoxesStyle[styleIndex];
                return true;
            }
        }
    }
    return false;
}

bool UAUTUIFunctionLibrary::TryGetTitleStyle(int32 styleIndex, FAUTBaseTextStyle& outStyle)
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();

    if (settings) {
        const UAUTThemeDataAsset* theme = settings->GetTheme();
        if (theme) {
            if (theme->TitlesStyle.IsValidIndex(styleIndex)) {
                outStyle = theme->TitlesStyle[styleIndex];
                return true;
            }
        }
    }
    return false;
}

bool UAUTUIFunctionLibrary::TryGetBackgroundStyle(int32 styleIndex, FSlateBrush& outStyle)
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();

    if (settings) {
        const UAUTThemeDataAsset* theme = settings->GetTheme();
        if (theme) {
            if (theme->Background.IsValidIndex(styleIndex)) {
                outStyle = theme->Background[styleIndex];
                return true;
            }
        }
    }
    return false;
}

bool UAUTUIFunctionLibrary::TryGetSpacerStyle(int32 styleIndex, FSlateBrush& outStyle)
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();

    if (settings) {
        const UAUTThemeDataAsset* theme = settings->GetTheme();
        if (theme) {
            if (theme->SpacerStyle.IsValidIndex(styleIndex)) {
                outStyle = theme->SpacerStyle[styleIndex];
                return true;
            }
        }
    }
    return false;
}

TSoftObjectPtr<UWorld> UAUTUIFunctionLibrary::GetDefaultMenuLevel()
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();
    return settings->GetDefaultMenuMapRef();
}



TSoftObjectPtr<UWorld> UAUTUIFunctionLibrary::GetDefaultNewGameLevel()
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();
    return settings->GetDefaultNewGameMapRef();
}

TArray<TSoftObjectPtr<USoundClass>> UAUTUIFunctionLibrary::GetDefaultSoundClasses()
{
    const UAUTDeveloperSettings* settings = GetMutableDefault<UAUTDeveloperSettings>();
    TArray<TSoftObjectPtr<USoundClass>> outSounds;
    const TArray<FSoftObjectPath> softPtrs = settings->GetDefaultSoundClasses();

    for (FSoftObjectPath soundclass : softPtrs) {
        const TSoftObjectPtr<USoundClass> defaultClass = Cast<USoundClass>( soundclass.TryLoad());
        outSounds.Add(defaultClass);
    }
    return outSounds;
}

void UAUTUIFunctionLibrary::SetSoundClassVolume(USoundClass* TargetClass, float NewVolume)
{
    if (!TargetClass) {
        return;
    }
    TargetClass->Properties.Volume = NewVolume;
}

bool UAUTUIFunctionLibrary::IsValidAndOnScreen(UUserWidget* widget)
{
	if (!IsValid(widget))
    {
        return false;
    }
    
    return widget->IsInViewport();
}
