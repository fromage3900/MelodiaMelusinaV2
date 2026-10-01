// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Serialization/ObjectAndNameAsStringProxyArchive.h"
#include "Styling/SlateTypes.h"
#include "UObject/NoExportTypes.h"
#include "UObject/ObjectPtr.h"

#include "AUTTypes.generated.h"

class USoundCue;

/**
 *
 */
USTRUCT(BlueprintType)
struct FAUTBaseStyle {

    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FName StyleName = "Default Name";
};

USTRUCT(BlueprintType)
struct FAUTBaseTextStyle : public FAUTBaseStyle {

    GENERATED_BODY()

public:
    FAUTBaseTextStyle()
    {
        NormalColor = FSlateColor(FColor::Black);
    }

    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FSlateFontInfo Normal;

    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FSlateColor NormalColor;
};

USTRUCT(BlueprintType)
struct FAUTTextStyle : public FAUTBaseTextStyle {

    GENERATED_BODY()

public:
    FAUTTextStyle()
    {
        NormalColor = FSlateColor(FColor::Black);
        HoveredColor = FSlateColor(FColor::Black);
    }

    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FSlateFontInfo Hovered;

    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FSlateColor HoveredColor;
};

USTRUCT(BlueprintType)
struct FAUTButtonStyle : public FAUTBaseStyle {
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FButtonStyle ButtonStyle;

    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FAUTTextStyle FontStyle;
};

USTRUCT(BlueprintType)
struct FAUTHoverableStyle : public FAUTBaseStyle {
    GENERATED_BODY()

public:
    FAUTHoverableStyle()
        : PressedSound(nullptr)
        , HoveredSound(nullptr)
    {
    }

              UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
                  FAUTTextStyle FontStyle;

    /**
     * The sound the button should play when pressed
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Sound, meta = (DisplayName = "Pressed Sound"))
    USoundCue* PressedSound;

    /**
     * The sound the button should play when initially hovered over
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Sound, meta = (DisplayName = "Hovered Sound"))
    USoundCue* HoveredSound;
};

USTRUCT(BlueprintType)
struct FAUTSliderStyle : public FAUTHoverableStyle {
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FSliderStyle SliderStyle;
};

USTRUCT(BlueprintType)
struct FAUTComboBoxStyle : public FAUTHoverableStyle {
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FComboBoxStyle ComboBoxStyle;
};

USTRUCT(BlueprintType)
struct FAUTSpinnerStyle : public FAUTHoverableStyle {
    GENERATED_BODY()

};

USTRUCT(BlueprintType)
struct FAUTCheckBoxStyle : public FAUTHoverableStyle {
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, config, Category = Style)
    FCheckBoxStyle CheckBoxStyle;
};

USTRUCT(BlueprintType)
struct FAUTThemeConfig {
    GENERATED_BODY()

public:
    FAUTThemeConfig()
    {
        Theme = FGameplayTag();
    }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = Style)
    FGameplayTag Theme;
};

USTRUCT(BlueprintType)
struct FSliderConfig {
    GENERATED_BODY()

    FSliderConfig()
    {
        MinValue = 0.f;
        MaxValue = 1.f;
        DefaultValue = 1.f;
        StepSize = .1f;
    }

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = AUT)
    float MinValue;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = AUT)
    float MaxValue;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = AUT)
    float DefaultValue;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = AUT)
    float StepSize;
};

UCLASS()
class ASCENTUITOOLS_API UAUTTypes : public UObject {
    GENERATED_BODY()
};
