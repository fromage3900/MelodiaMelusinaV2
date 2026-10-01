// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "CommonActivatableWidget.h"
#include "ACFHUDUserWidget.generated.h"

/**
 * Optional base for HUD widgets shown by AACFHUD. Set HUD Class to any UUserWidget; use this
 * (or a Blueprint child) when you need OnPossessedCharacterChanged when the possessed pawn changes.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFHUDUserWidget : public UCommonActivatableWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UFUNCTION()
	void HandlePossessedCharacterChanged(const class APawn* NewChar);

	/** Called when the possessed character changes; implement in Blueprint to update HUD. */
	UFUNCTION(BlueprintImplementableEvent, Category = ACF)
	void OnPossessedCharacterChanged(const class APawn* newChar);
};
  