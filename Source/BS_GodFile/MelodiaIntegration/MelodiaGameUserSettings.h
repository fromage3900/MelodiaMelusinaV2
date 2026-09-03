#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "MelodiaGameUserSettings.generated.h"

/**
 * Player-local preferences.  This is deliberately separate from the stock
 * JRPG SaveGame: display, audio, and accessibility survive across journeys
 * without becoming narrative or gameplay state.
 */
UCLASS(Config=Game, DefaultConfig)
class BS_GODFILE_API UMelodiaGameUserSettings final : public UGameUserSettings
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category="Melodia|Settings")
	static UMelodiaGameUserSettings* Get();

	/** Applies runtime-safe presentation preferences and writes the user config. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Settings", meta=(WorldContext="WorldContextObject"))
	void ApplyMelodiaPreferences(const UObject* WorldContextObject);

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Audio", meta=(ClampMin="0.0", ClampMax="1.0"))
	float MasterVolume = 1.0f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Audio", meta=(ClampMin="0.0", ClampMax="1.0"))
	float MusicVolume = 0.8f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Audio", meta=(ClampMin="0.0", ClampMax="1.0"))
	float SFXVolume = 0.9f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Accessibility")
	bool bReduceMotion = false;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Accessibility")
	bool bHighContrastText = false;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="HUD")
	bool bMinimalReactiveHUD = true;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="HUD", meta=(ClampMin="0.8", ClampMax="1.3"))
	float UIScale = 1.0f;
};
