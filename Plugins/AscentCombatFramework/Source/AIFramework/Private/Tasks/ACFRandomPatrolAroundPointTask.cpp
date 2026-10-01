// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Tasks/ACFRandomPatrolAroundPointTask.h"

#include "ACFAIController.h"
#include "ACFAITypes.h"
#include "Components/ACFAIPatrolComponent.h"
#include "GameplayTagsManager.h"
#include "GameFramework/Actor.h"

void UACFRandomPatrolAroundPointTask::OnTaskStarted_Implementation(const APawn* ControlledPawn)
{
	Super::OnTaskStarted_Implementation(ControlledPawn);

	if (!ControlledPawn) {
		return;
	}

	AACFAIController* AIController = Cast<AACFAIController>(ControlledPawn->GetController());
	if (!AIController) {
		return;
	}

	UACFAIPatrolComponent* PatrolComp = ControlledPawn->FindComponentByClass<UACFAIPatrolComponent>();
	if (!PatrolComp) {
		return;
	}

	FVector Center = ControlledPawn->GetActorLocation();
	if (!bUsePawnLocationAsCenter)
	{
		if (PatrolCenterActor)
		{
			Center = PatrolCenterActor->GetActorLocation();
		}
	}
	PatrolComp->SetPatrolType(EPatrolType::ERandomPoint);
	PatrolComp->SetRandomPatrolRadius(PatrolRadius);
	CachedPatrolComponent = PatrolComp;

	if (bSetHomeLocationToPatrolCenter) {
		AIController->SetHomeLocation(Center);
	}

	AIController->SetCurrentAIState(UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIRoutine));
	CachedPatrolComponent->StartPatrolLoop(bStartMovementOnTaskStart);
}

void UACFRandomPatrolAroundPointTask::OnTaskEnded_Implementation()
{
	if (CachedPatrolComponent) {
		CachedPatrolComponent->StopPatrolLoop();
	}
	CachedPatrolComponent = nullptr;
	Super::OnTaskEnded_Implementation();
}
