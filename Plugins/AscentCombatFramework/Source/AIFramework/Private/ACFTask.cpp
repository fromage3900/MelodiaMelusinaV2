// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 



#include "ACFTask.h"
#include "Engine/Engine.h"
#include <GameFramework/Pawn.h>

void UACFTask::OnTaskStarted_Implementation(const APawn* ControlledPawn)
{

	

}

void UACFTask::OnTaskEnded_Implementation()
{
}

void UACFTask::Internal_OnTaskStarted(const APawn* ControlledPawn)
{
	Controller = ControlledPawn->GetController();
	OnTaskStarted(ControlledPawn);
}
