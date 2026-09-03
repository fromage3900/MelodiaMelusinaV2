// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "RhythmInputComponent.h"
#include "RhythmCombatUI.generated.h"

class UTextBlock;
class UImage;
class USizeBox;

/**
 * UI Widget for displaying rhythm combat feedback
 * Shows beat indicators, accuracy feedback, combo counters, and damage multipliers
 */
UCLASS()
class BS_GODFILE_API URhythmCombatUI : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;

    /** Update accuracy display */
    UFUNCTION(BlueprintCallable, Category="Rhythm UI")
    void UpdateAccuracy(ERhythmAccuracy Accuracy);

    /** Update combo counter */
    UFUNCTION(BlueprintCallable, Category="Rhythm UI")
    void UpdateCombo(int32 ComboCount, int32 MaxCombo);

    /** Update damage multiplier */
    UFUNCTION(BlueprintCallable, Category="Rhythm UI")
    void UpdateDamageMultiplier(float Multiplier);

    /** Show/hide beat indicator */
    UFUNCTION(BlueprintCallable, Category="Rhythm UI")
    void SetBeatIndicatorVisible(bool bVisible);

    /** Pulse beat indicator (call on each beat) */
    UFUNCTION(BlueprintCallable, Category="Rhythm UI")
    void PulseBeatIndicator();

protected:
    /** Accuracy text display */
    UPROPERTY(meta=(BindWidgetOptional))
    UTextBlock* AccuracyText;

    /** Combo counter text */
    UPROPERTY(meta=(BindWidgetOptional))
    UTextBlock* ComboText;

    /** Max combo text */
    UPROPERTY(meta=(BindWidgetOptional))
    UTextBlock* MaxComboText;

    /** Damage multiplier text */
    UPROPERTY(meta=(BindWidgetOptional))
    UTextBlock* MultiplierText;

    /** Beat indicator image */
    UPROPERTY(meta=(BindWidgetOptional))
    UImage* BeatIndicator;

    /** Beat indicator size box (for scaling animation) */
    UPROPERTY(meta=(BindWidgetOptional))
    USizeBox* BeatIndicatorSizeBox;

private:
    /** Default beat indicator size */
    FVector2D DefaultBeatSize;

    /** Pulse animation target size */
    FVector2D PulseBeatSize;

    /** Current pulse animation progress */
    float PulseProgress;

    /** Update pulse animation */
    void UpdatePulseAnimation(float DeltaTime);
};