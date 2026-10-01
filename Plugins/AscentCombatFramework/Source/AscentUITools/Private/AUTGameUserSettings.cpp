// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AUTGameUserSettings.h"

void UAUTGameUserSettings::SetToDefaults()
{
    Super::SetToDefaults();

    YSensitivity = 1.f;
    XSensitivity = 1.f;
    bInvertY = false;
    bToggleSprint = true;
    PreferredDifficultyLevel = FGameplayTag::RequestGameplayTag(FName("ACF.Difficulty.Normal"));
}

FVector2D UAUTGameUserSettings::GetAxisSensitivity() const
{
    return FVector2D(XSensitivity, YSensitivity);
}

void UAUTGameUserSettings::SetAxisSensitivity(FVector2D axisSensitivity)
{
    XSensitivity = axisSensitivity.X;
    YSensitivity = axisSensitivity.Y;
}

void UAUTGameUserSettings::SetYAxisInverted(bool inYinverted)
{
    bInvertY = inYinverted;
}

void UAUTGameUserSettings::SetToggleSprint(bool inToggleSprint)
{
    bToggleSprint = inToggleSprint;
}

void UAUTGameUserSettings::SetPreferredDifficultyLevel(const FGameplayTag& InDifficulty)
{
    if (PreferredDifficultyLevel != InDifficulty)
    {
        PreferredDifficultyLevel = InDifficulty;
        OnDifficultyPreferenceChanged.Broadcast(InDifficulty);
    }
}

void UAUTGameUserSettings::ApplySettings(bool bCheckForCommandLineOverrides)
{
    Super::ApplySettings(bCheckForCommandLineOverrides);
    BPApplySettings();
    OnGameSettingsApplied.Broadcast();
}

void UAUTGameUserSettings::BPApplySettings_Implementation()
{
}
