// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "BehavioralThree/ACFCheckRoutineBTService.h"
#include "ACFAIController.h"
#include "BehaviorTree/BehaviorTree.h"
#include "GameFramework/Pawn.h"
#include "AIController.h"
#include "Components/ACFAIRoutineComponent.h"


UACFCheckRoutineBTService::UACFCheckRoutineBTService()
{
	bCreateNodeInstance = true; 
	Interval = 0.25f;
	RandomDeviation = 0.f;
}

/**
 * Called when the service becomes relevant on this BT branch.
 * Resolves and caches the UACFAIRoutineComponent for later ticks.
 *
 * @param OwnerComp	Behavior tree component owning this service instance.
 * @param NodeMemory	Pointer to this node's memory block (unused here).
 */
void UACFCheckRoutineBTService::OnBecomeRelevant(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory)
{
	Super::OnBecomeRelevant(OwnerComp, NodeMemory);
	ResolveRoutineComponent(OwnerComp);
}

/**
 * Called when the service ceases to be relevant on this BT branch.
 * Stops all currently active routine tasks to ensure a clean exit
 * when the branch is no longer running.
 *
 * @param OwnerComp	Behavior tree component owning this service instance.
 * @param NodeMemory	Pointer to this node's memory block (unused here).
 */
void UACFCheckRoutineBTService::OnCeaseRelevant(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory)
{
	Super::OnCeaseRelevant(OwnerComp, NodeMemory);

	// if (RoutineComp)
	// {
	// 	RoutineComp->StopAll();
	// }
}

/**
 * Resolve and cache the UACFAIRoutineComponent from the BT owner (AIController).
 * Safe to call multiple times; re-validates world consistency.
 *
 * @param OwnerComp	Behavior tree component used to access the owning AI and world.
 */
void UACFCheckRoutineBTService::ResolveRoutineComponent(UBehaviorTreeComponent& OwnerComp)
{
	if (RoutineComp && RoutineComp->IsValidLowLevelFast())
	{
		if (RoutineComp->GetWorld() == OwnerComp.GetWorld())
		{
			return;
		}
	}

	RoutineComp = nullptr;

	const AAIController* AI = OwnerComp.GetAIOwner();
	
	if (AI)
	{
		RoutineComp = AI->FindComponentByClass<UACFAIRoutineComponent>();
	}
}

/**
 * Periodic tick executed while the service is relevant.
 * Ensures the routine component is valid and triggers the routine update by time-of-day.
 *
 * @param OwnerComp	Behavior tree component owning this service instance.
 * @param NodeMemory	Pointer to this node's memory block (unused here).
 * @param DeltaSeconds	Time elapsed since the last tick.
 */
void UACFCheckRoutineBTService::TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds)
{
	Super::TickNode(OwnerComp, NodeMemory, DeltaSeconds);

	if (!RoutineComp || RoutineComp->GetWorld() != OwnerComp.GetWorld())
	{
		ResolveRoutineComponent(OwnerComp);
	}

	if (!RoutineComp)
	{
		return;
	}

	if (const AAIController* const AI = OwnerComp.GetAIOwner())
	{
		if (const AACFAIController* const ACF = Cast<AACFAIController>(AI))
		{
			if (ACF->IsExecutingCommand())
			{
				return;
			}
		}
	}

	RoutineComp->UpdateByTime();
}