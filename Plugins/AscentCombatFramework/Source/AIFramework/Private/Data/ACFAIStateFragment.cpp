// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Data/ACFAIStateFragment.h"
#include "ACFAIController.h"
#include "ACFSplinePath.h"
#include "Components/ACFAIRoutineComponent.h"
#include "GameFramework/Pawn.h"

void UACFAIStateFragment::ApplyFragment_Implementation(APawn* pawnOwner)
{
	if (!pawnOwner)
	{
		return;
	}

	AACFAIController* AICont = Cast<AACFAIController>(pawnOwner->GetController());
	if (!AICont)
	{
		return;
	}

	if (DefaultState.IsValid())
	{
		AICont->SetDefaultState(DefaultState);
	}

	if (bHasPatrolPath)
	{
		AACFSplinePath* ResolvedPath = PatrolPath.Get();
		if (ResolvedPath)
		{
			AICont->SetPatrolPath(ResolvedPath);
		}
	}

	if (bHasRoutine && RoutineDataAsset)
	{
		UACFAIRoutineComponent* RoutineComp = AICont->FindComponentByClass<UACFAIRoutineComponent>();
		if (RoutineComp)
		{
			RoutineComp->SetRoutineDataAsset(RoutineDataAsset);
		}
	}
}
