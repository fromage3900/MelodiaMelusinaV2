#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "MelodiaPresentationSettings.generated.h"

/** Shared, user-facing presentation preferences for future UMG surfaces. */
UCLASS(Config=Game, DefaultConfig, meta=(DisplayName="Melodia Presentation"))
class BS_GODFILE_API UMelodiaPresentationSettings final : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Accessibility")
	bool bReduceMotion = false;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="Accessibility")
	bool bHighContrastText = false;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="HUD")
	bool bMinimalReactiveHUD = true;

	UPROPERTY(Config, EditAnywhere, BlueprintReadWrite, Category="HUD", meta=(ClampMin="0.8", ClampMax="1.3"))
	float UIScale = 1.0f;
};
