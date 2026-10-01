// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Game/ACFDamageType.h"
#include "ACFDamageWidget.generated.h"

struct FACFDamageEvent;

/**
 * Widget used to display a single damage number or damage event (e.g. floating damage text).
 * Implement SetupDamageWidget in Blueprint to show value, type, and optional animation.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFDamageWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Called to set up the widget with the damage event; implement in Blueprint to display it. */
	UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = ACF)
	void SetupDamageWidget(const FACFDamageEvent& damageEvent);
};
