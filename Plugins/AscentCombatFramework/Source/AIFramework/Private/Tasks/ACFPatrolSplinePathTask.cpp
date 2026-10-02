// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Tasks/ACFPatrolSplinePathTask.h"

#include "ACFAIController.h"
#include "ACFAITypes.h"
#include "Components/ACFAIPatrolComponent.h"
#include "GameplayTagsManager.h"

void UACFPatrolSplinePathTask::OnTaskStarted_Implementation(const APawn* ControlledPawn)
{
	Super::OnTaskStarted_Implementation(ControlledPawn);

	if (!ControlledPawn) {
		return;
	}

	AACFAIController* AIController = Cast<AACFAIController>(ControlledPawn->GetController());
	if (!AIController || !SplinePath) {
		return;
	}

	CachedPatrolComponent = ControlledPawn->FindComponentByClass<UACFAIPatrolComponent>();
	if (!CachedPatrolComponent) {
		return;
	}

	AIController->SetPatrolPath(SplinePath, bForceFollowSpline);
	AIController->SetCurrentAIState(UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIRoutine));
	CachedPatrolComponent->StartPatrolLoop(bStartMovementOnTaskStart);
}

void UACFPatrolSplinePathTask::OnTaskEnded_Implementation()
{
	if (CachedPatrolComponent) {
		CachedPatrolComponent->StopPatrolLoop();
	}
	CachedPatrolComponent = nullptr;
	Super::OnTaskEnded_Implementation();
}
