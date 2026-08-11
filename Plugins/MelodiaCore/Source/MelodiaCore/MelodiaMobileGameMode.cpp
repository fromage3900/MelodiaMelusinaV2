#include "MelodiaMobileGameMode.h"
#include "MelodiaMobileHUD.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

AMelodiaMobileGameMode::AMelodiaMobileGameMode()
{
	// Mobile-specific defaults
	bForceLandscape = true;
	bUseTouchInput = true;

	// Use our mobile HUD
	if (MobileHUDClass)
	{
		HUDClass = MobileHUDClass;
	}
}

void AMelodiaMobileGameMode::BeginPlay()
{
	Super::BeginPlay();

#if PLATFORM_IOS || PLATFORM_ANDROID
	if (bForceLandscape)
	{
		// Force landscape orientation
		if (GEngine && GEngine->GameViewport)
		{
			GEngine->GameViewport->SetOrientation(FIntPoint(1920, 1080));
		}

		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		{
			PC->bAutoManageActiveCameraTarget = false;
		}
	}

	if (bUseTouchInput)
	{
		// Enable touch input
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		{
			PC->bEnableClickEvents = true;
			PC->bEnableTouchEvents = true;
			PC->bShowMouseCursor = false;
		}
	}
#endif
}
