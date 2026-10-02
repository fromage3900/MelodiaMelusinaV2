// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Chaos/Array.h"
#include <GameplayTagContainer.h>
#include "AUTTypes.h"
#include "AUTThemeDataAsset.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTUITOOLS_API UAUTThemeDataAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public: 

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
	FGameplayTag ThemeTag;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
    TArray<FAUTBaseTextStyle> TitlesStyle;

	/** Style of the buttons for this theme */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
	TArray<FAUTButtonStyle> ButtonsStyle;

	/** Style of the combo boxes for this theme */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
	TArray<FAUTComboBoxStyle> ComboBoxesStyle;

	/** Style of the spinners for this theme */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
	TArray<FAUTSpinnerStyle> SpinnersStyle;

	/** Style of the sliders for this theme */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
	TArray<FAUTSliderStyle> SlidersStyle;

	/** Style of the checkboxes for this theme */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
	TArray<FAUTCheckBoxStyle> CheckBoxesStyle;

	/** Brush to drag as the background */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
	TArray<FSlateBrush> Background;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Style)
	TArray<FSlateBrush> SpacerStyle;
	
};
