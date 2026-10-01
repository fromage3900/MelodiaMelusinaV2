// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ANSNavPopUpWidget.h"
#include "ANSUIPlayerSubsystem.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"

UANSNavPopUpWidget::UANSNavPopUpWidget()
	: Super()
{
	bIsModal = true;
}

void UANSNavPopUpWidget::NativeOnDeactivated()
{
	Super::NativeOnDeactivated();


}

void UANSNavPopUpWidget::ResetFocusOnOwner()
{
	if (const UGameInstance* GameInst = UGameplayStatics::GetGameInstance(this))
	{
		if (UANSUIPlayerSubsystem* Subsystem = GameInst->GetSubsystem<UANSUIPlayerSubsystem>())
		{
			Subsystem->RestoreSuspendedPages();
		}
	}
}
