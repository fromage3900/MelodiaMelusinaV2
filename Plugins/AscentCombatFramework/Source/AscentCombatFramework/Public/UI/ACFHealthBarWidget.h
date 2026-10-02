// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "ACFHealthBarWidget.generated.h"

/**
 * Widget that displays a health bar for a pawn. Implement SetupWithPawn in Blueprint to bind
 * to the pawn's health/attributes and update the bar visual.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFHealthBarWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Called to initialize the health bar for the given pawn; implement in Blueprint to bind to health. */
	UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = ACF)
	void SetupWithPawn(const APawn* pawn);
};
