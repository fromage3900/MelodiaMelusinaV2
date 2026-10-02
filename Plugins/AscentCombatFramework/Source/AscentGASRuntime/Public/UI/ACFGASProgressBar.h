// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ProgressBar.h"
#include "CoreMinimal.h"
#include <Blueprint/UserWidget.h>
#include <AttributeSet.h>
#include <AbilitySystemComponent.h>
#include <GameplayEffectTypes.h>

#include "ACFGASProgressBar.generated.h"

class UAbilitySystemComponent;
class UProgressBar;

/**
 * Progress bar widget bound to GAS attributes (e.g. Health, Stamina). Reads current and max
 * from an Ability System Component and optionally smooth-interpolates the fill.
 */
UCLASS()
class ASCENTGASRUNTIME_API UACFGASProgressBar : public UUserWidget {
	GENERATED_BODY()

public:
    /** Returns the attribute used for the current value of the progress bar. */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayAttribute GetCurrentAttribute() const { return CurrentAttribute; }

    /** Returns the attribute used for the max value of the progress bar. */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayAttribute GetMaxAttribute() const { return MaxAttribute; }

    /**
     * Initializes the progress bar with an Ability System Component reference.
     * @param inAbilityComp - The ASC to read attribute values from
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void InitBar(UAbilitySystemComponent* inAbilityComp);

    UACFGASProgressBar(const FObjectInitializer& ObjectInitializer);

protected:
    /** The attribute used to display the current value for the bar. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FGameplayAttribute CurrentAttribute;

    /** The attribute used to display the max value for the bar. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FGameplayAttribute MaxAttribute;

    /** The fill color of the progress bar. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FLinearColor FillColor;

    /** Whether to smoothly interpolate the bar when values change. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    bool bSmoothInterpolation = true;

    /** The speed of interpolation when bSmoothInterpolation is enabled. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float InterpolationSpeed = 3.f;

    /** The progress bar widget to update. */
    UPROPERTY(meta = (BindWidget), EditAnywhere, BlueprintReadWrite, Category = ACF)
    UProgressBar* ACFProgressBar;

    /** Manually updates the progress bar to reflect current attribute values. */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void UpdateBar();

    UFUNCTION(BlueprintImplementableEvent, Category = ACF)
    void OnBarUpdated();

    /** Returns the current value of the tracked attribute. */
    UFUNCTION(BlueprintPure, Category = ACF)
    float GetCurrentValue() const;

    /** Returns the max value of the tracked attribute. */
    UFUNCTION(BlueprintPure, Category = ACF)
    float GetMaxValue() const;

    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
    /** Cached reference to the Ability System Component. */
    TObjectPtr<UAbilitySystemComponent> abilityComp;

    /**
     * Callback fired when a tracked attribute value changes.
     * @param Data - Contains the old and new attribute values
     */
    void OnValueChanged(const FOnAttributeChangeData& Data);

    /** The target percentage for smooth interpolation. */
    float targetPercentage;
};
