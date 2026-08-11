#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaPrototypeCaptureSubsystem.generated.h"

UENUM(BlueprintType)
enum class EMelodiaCaptureSurface : uint8
{
	MainMenu,
	Exploration,
	Battle
};

/**
 * Presentation-only capture utility. It does not create UI or alter gameplay;
 * it gives the prototype three named, repeatable screenshot surfaces.
 */
UCLASS()
class BS_GODFILE_API UMelodiaPrototypeCaptureSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Melodia|Presentation")
	void SetCaptureSurface(EMelodiaCaptureSurface Surface);

	UFUNCTION(BlueprintPure, Category = "Melodia|Presentation")
	EMelodiaCaptureSurface GetCaptureSurface() const { return ActiveSurface; }

	UFUNCTION(BlueprintCallable, Category = "Melodia|Presentation")
	bool CapturePrototypeScreenshot(const FString& OptionalLabel);

	UFUNCTION(BlueprintPure, Category = "Melodia|Presentation")
	FText GetCaptureSurfaceLabel() const;

private:
	EMelodiaCaptureSurface ActiveSurface = EMelodiaCaptureSurface::Exploration;
};
