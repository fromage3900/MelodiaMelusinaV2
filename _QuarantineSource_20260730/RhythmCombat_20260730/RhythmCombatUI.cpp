// Copyright Epic Games, Inc. All Rights Reserved.

#include "RhythmCombatUI.h"
#include "Components/TextBlock.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Animation/WidgetAnimation.h"

void URhythmCombatUI::NativeConstruct()
{
    Super::NativeConstruct();

    // Initialize default sizes
    DefaultBeatSize = FVector2D(100.0f, 100.0f);
    PulseBeatSize = FVector2D(150.0f, 150.0f);
    PulseProgress = 0.0f;

    // Set initial beat indicator size
    if (BeatIndicatorSizeBox)
    {
        BeatIndicatorSizeBox->SetWidthOverride(DefaultBeatSize.X);
        BeatIndicatorSizeBox->SetHeightOverride(DefaultBeatSize.Y);
    }

    // Hide beat indicator initially
    SetBeatIndicatorVisible(false);
}

void URhythmCombatUI::NativeDestruct()
{
    Super::NativeDestruct();
}

void URhythmCombatUI::UpdateAccuracy(ERhythmAccuracy Accuracy)
{
    if (!AccuracyText)
    {
        return;
    }

    FText AccuracyDisplay;
    FLinearColor AccuracyColor;

    switch (Accuracy)
    {
        case ERhythmAccuracy::Perfect:
            AccuracyDisplay = FText::FromString("PERFECT!");
            AccuracyColor = FLinearColor::Green;
            break;
        case ERhythmAccuracy::Good:
            AccuracyDisplay = FText::FromString("GOOD");
            AccuracyColor = FLinearColor::Yellow;
            break;
        case ERhythmAccuracy::Miss:
            AccuracyDisplay = FText::FromString("MISS");
            AccuracyColor = FLinearColor::Red;
            break;
        default:
            AccuracyDisplay = FText::GetEmpty();
            AccuracyColor = FLinearColor::White;
            break;
    }

    AccuracyText->SetText(AccuracyDisplay);
    AccuracyText->SetColorAndOpacity(AccuracyColor);
}

void URhythmCombatUI::UpdateCombo(int32 ComboCount, int32 MaxCombo)
{
    if (ComboText)
    {
        ComboText->SetText(FText::AsNumber(ComboCount));
    }

    if (MaxComboText)
    {
        MaxComboText->SetText(FText::AsNumber(MaxCombo));
    }
}

void URhythmCombatUI::UpdateDamageMultiplier(float Multiplier)
{
    if (!MultiplierText)
    {
        return;
    }

    FString MultiplierString = FString::Printf(TEXT("%.2fx"), Multiplier);
    MultiplierText->SetText(FText::FromString(MultiplierString));

    // Color based on multiplier value
    FLinearColor MultiplierColor;
    if (Multiplier >= 2.0f)
    {
        MultiplierColor = FLinearColor::Green;
    }
    else if (Multiplier >= 1.5f)
    {
        MultiplierColor = FLinearColor::Yellow;
    }
    else
    {
        MultiplierColor = FLinearColor::Red;
    }

    MultiplierText->SetColorAndOpacity(MultiplierColor);
}

void URhythmCombatUI::SetBeatIndicatorVisible(bool bVisible)
{
    if (BeatIndicator)
    {
        BeatIndicator->SetVisibility(bVisible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
}

void URhythmCombatUI::PulseBeatIndicator()
{
    if (!BeatIndicatorSizeBox)
    {
        return;
    }

    // Start pulse animation
    PulseProgress = 1.0f;
    BeatIndicatorSizeBox->SetWidthOverride(PulseBeatSize.X);
    BeatIndicatorSizeBox->SetHeightOverride(PulseBeatSize.Y);
}

void URhythmCombatUI::UpdatePulseAnimation(float DeltaTime)
{
    if (PulseProgress <= 0.0f || !BeatIndicatorSizeBox)
    {
        return;
    }

    // Animate back to default size
    PulseProgress -= DeltaTime * 4.0f; // Animation speed
    PulseProgress = FMath::Clamp(PulseProgress, 0.0f, 1.0f);

    float CurrentSize = FMath::Lerp(DefaultBeatSize.X, PulseBeatSize.X, PulseProgress);
    BeatIndicatorSizeBox->SetWidthOverride(CurrentSize);
    BeatIndicatorSizeBox->SetHeightOverride(CurrentSize);
}