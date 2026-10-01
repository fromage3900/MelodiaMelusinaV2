// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "BehavioralThree/ACFCheckActionsBTService.h"
#include <BehaviorTree/BehaviorTreeComponent.h>
#include <BehaviorTree/BlackboardComponent.h>
#include "ACFAIController.h"
#include "Components/ACFCombatBehaviourComponent.h"
#include <Logging.h>

void UACFCheckActionsBTService::TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds)
{
	UBlackboardComponent* const bbc = OwnerComp.GetBlackboardComponent();

	const AACFAIController* aiController = Cast<AACFAIController>(OwnerComp.GetAIOwner());

	if (aiController == nullptr)
	{
		UE_LOG(ACFAILog, Warning, TEXT("UACFCheckActionsBTService get controller failed"));
		return;
	}

	UACFCombatBehaviourComponent* combatBehav = aiController->GetCombatBehavior();
	if (combatBehav == nullptr)
	{
		UE_LOG(ACFAILog, Warning, TEXT("UACFCheckActionsBTService get behav failed"));
		return;
	}

	combatBehav->TryExecuteConditionAction();
}