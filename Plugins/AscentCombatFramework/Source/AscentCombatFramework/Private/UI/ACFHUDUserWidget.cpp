// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "UI/ACFHUDUserWidget.h"
#include "Game/ACFPlayerController.h"

void UACFHUDUserWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (AACFPlayerController* ACFPC = Cast<AACFPlayerController>(GetOwningPlayer()))
	{
		ACFPC->OnPossessedCharacterChanged.AddDynamic(this, &UACFHUDUserWidget::HandlePossessedCharacterChanged);
	}
}

void UACFHUDUserWidget::NativeDestruct()
{
	if (AACFPlayerController* ACFPC = Cast<AACFPlayerController>(GetOwningPlayer()))
	{
		ACFPC->OnPossessedCharacterChanged.RemoveDynamic(this, &UACFHUDUserWidget::HandlePossessedCharacterChanged);
	}

	Super::NativeDestruct();
}

void UACFHUDUserWidget::HandlePossessedCharacterChanged(const APawn* NewChar)
{
	OnPossessedCharacterChanged(NewChar);
}
