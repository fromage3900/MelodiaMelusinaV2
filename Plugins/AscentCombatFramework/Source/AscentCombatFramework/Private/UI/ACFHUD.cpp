// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "UI/ACFHUD.h"
#include "Blueprint/UserWidget.h"
#include <Kismet/GameplayStatics.h>

void AACFHUD::BeginPlay()
{
	Super::BeginPlay();
	// Create the HUD widget here (not in PostInitProperties): by BeginPlay the actor has a
	// valid world and an owning PlayerController. PostInitProperties runs during construction
	// (and on the CDO), where GetPlayerController(0) can be null in packaged/standalone builds
	// but not in PIE - so the HUD widget (and its RegisterLayer calls) would silently never run.
	InitHUD();
}

void AACFHUD::PostInitProperties()
{
	Super::PostInitProperties();
}

void AACFHUD::PostRender()
{
	Super::PostRender();
	if (HUDWidget) {
		if (bShowHUD != enabled) {
			SetHudEnabled(bShowHUD);
		}

	}
}

void AACFHUD::InitHUD()
{
	// Prefer this HUD's own owning controller (always valid for a HUD); fall back to player 0.
	APlayerController* playerController = GetOwningPlayerController();
	if (!playerController) {
		playerController = UGameplayStatics::GetPlayerController(this, 0);
	}
	if (HUDClass && playerController) {
		HUDWidget = CreateWidget<UUserWidget>(playerController, HUDClass);
		HUDWidget->AddToViewport(0);
	}
}



void AACFHUD::SetHudEnabled(bool bEnabled)
{
	bShowHUD = bEnabled;
	enabled = bShowHUD;
	if (!HUDWidget) {
		return;
	}

	if (bEnabled) {
		HUDWidget->SetVisibility(ESlateVisibility::Visible);

	}
	else {
		HUDWidget->SetVisibility(ESlateVisibility::Hidden);
	}
}
