// Mobile Game Mode ΓÇö configures mobile-specific defaults (landscape, touch input, no mouse)

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "MelodiaMobileGameMode.generated.h"

class UMelodiaMobileHUD;

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (competing game mode). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API AMelodiaMobileGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AMelodiaMobileGameMode();

protected:
	virtual void BeginPlay() override;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Mobile")
	TSubclassOf<UMelodiaMobileHUD> MobileHUDClass;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Mobile")
	bool bForceLandscape = true;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Mobile")
	bool bUseTouchInput = true;
};
