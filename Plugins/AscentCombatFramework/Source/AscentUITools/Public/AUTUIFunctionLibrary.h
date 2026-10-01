// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AUTTypes.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "AUTUIFunctionLibrary.generated.h"

class USoundClass;
class UUserWidget;



/**
 * Blueprint Function Library providing utility functions for the Ascent UI Tools system.
 * Exposes style retrieval, settings access, and audio configuration to Blueprints.
 */
UCLASS()
class ASCENTUITOOLS_API UAUTUIFunctionLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:

	/**
	 * Retrieves the game user settings instance.
	 * @return The AUT game user settings singleton.
	 */
	UFUNCTION(BlueprintPure, Category = "AUT|Settings")
	static class UAUTGameUserSettings* GetGameUserSettings();

	/**
	 * Attempts to retrieve a button style by index from the settings.
	 * @param StyleIndex - Index of the button style to retrieve.
	 * @param OutStyle - The retrieved button style if found.
	 * @return True if the style was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "AUT|Styles")
	static bool TryGetButtonStyle(int32 StyleIndex, FAUTButtonStyle& OutStyle);

	/**
	 * Attempts to retrieve a slider style by index from the settings.
	 * @param StyleIndex - Index of the slider style to retrieve.
	 * @param OutStyle - The retrieved slider style if found.
	 * @return True if the style was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "AUT|Styles")
	static bool TryGetSliderStyle(int32 StyleIndex, FAUTSliderStyle& OutStyle);

    UFUNCTION(BlueprintCallable, Category = AUT)
    static bool TryGetSpinnerStyle(int32 styleIndex, FAUTSpinnerStyle& outStyle);

	/**
	 * Attempts to retrieve a combo box style by index from the settings.
	 * @param StyleIndex - Index of the combo box style to retrieve.
	 * @param OutStyle - The retrieved combo box style if found.
	 * @return True if the style was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "AUT|Styles")
	static bool TryGetComboBoxStyle(int32 StyleIndex, FAUTComboBoxStyle& OutStyle);

	/**
	 * Attempts to retrieve a check box style by index from the settings.
	 * @param StyleIndex - Index of the check box style to retrieve.
	 * @param OutStyle - The retrieved check box style if found.
	 * @return True if the style was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "AUT|Styles")
	static bool TryGetCheckBoxStyle(int32 StyleIndex, FAUTCheckBoxStyle& OutStyle);

	/**
	 * Attempts to retrieve a title text style by index from the settings.
	 * @param StyleIndex - Index of the title style to retrieve.
	 * @param OutStyle - The retrieved title text style if found.
	 * @return True if the style was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "AUT|Styles")
	static bool TryGetTitleStyle(int32 StyleIndex, FAUTBaseTextStyle& OutStyle);

	/**
	 * Attempts to retrieve a background brush style by index from the settings.
	 * @param StyleIndex - Index of the background style to retrieve.
	 * @param OutStyle - The retrieved slate brush if found.
	 * @return True if the style was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "AUT|Styles")
	static bool TryGetBackgroundStyle(int32 StyleIndex, FSlateBrush& OutStyle);

	/**
	 * Attempts to retrieve a spacer brush style by index from the settings.
	 * @param StyleIndex - Index of the spacer style to retrieve.
	 * @param OutStyle - The retrieved slate brush if found.
	 * @return True if the style was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "AUT|Styles")
	static bool TryGetSpacerStyle(int32 StyleIndex, FSlateBrush& OutStyle);

	/**
	 * Returns the default menu level configured in the settings.
	 * @return Soft reference to the default menu world asset.
	 */
	UFUNCTION(BlueprintPure, Category = "AUT|Levels")
	static TSoftObjectPtr<UWorld> GetDefaultMenuLevel();

	/**
	 * Returns the default new game level configured in the settings.
	 * @return Soft reference to the default new game world asset.
	 */
	UFUNCTION(BlueprintPure, Category = "AUT|Levels")
	static TSoftObjectPtr<UWorld> GetDefaultNewGameLevel();

	/**
	 * Returns the array of sound classes configured for volume control.
	 * @return Array of soft references to sound class assets.
	 */
	UFUNCTION(BlueprintPure, Category = "AUT|Audio")
	static TArray<TSoftObjectPtr<USoundClass>> GetDefaultSoundClasses();

	/**
	 * Sets the volume multiplier for a specific sound class.
	 * @param TargetClass - The sound class to modify.
	 * @param NewVolume - The new volume multiplier (0.0 to 1.0).
	 */
	UFUNCTION(BlueprintCallable, Category = "AUT|Audio")
	static void SetSoundClassVolume(USoundClass* TargetClass, float NewVolume);

	/**
	 * Checks if a user widget is both valid and currently displayed on screen.
	 * @param widget - The user widget to check.
	 * @return True if the widget is valid and added to the viewport, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = "AUT|UI")
	static bool IsValidAndOnScreen(UUserWidget* widget);

};
