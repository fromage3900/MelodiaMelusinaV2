// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/BTService.h"
#include "ACFCheckRoutineBTService.generated.h"

class UACFAIRoutineComponent;
/**
 * BT Service that polls the actor's UACFAIRoutineComponent
 *
 * Typical usage:
 * - Place this service on a Behavior Tree branch that should react to AI routine changes. * 
 */
UCLASS()
class AIFRAMEWORK_API UACFCheckRoutineBTService : public UBTService
{
	GENERATED_BODY()

public:
	UACFCheckRoutineBTService();

	/**
	 * Called when the service becomes relevant (activated on the BT branch).
	 * @param OwnerComp Behavior tree component owning this service instance.
	 * @param NodeMemory Pointer to this node's memory block.
	 */
	virtual void OnBecomeRelevant(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;

	/**
	 * Called when the service ceases to be relevant (deactivated on the BT branch).
	 * @param OwnerComp Behavior tree component owning this service instance.
	 * @param NodeMemory Pointer to this node's memory block.
	 */
	virtual void OnCeaseRelevant(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;

	/**
	 * Tick function executed at the service's interval while relevant.
	 * Typically used to query the routine component and update Blackboard keys.
	 * @param OwnerComp Behavior tree component owning this service instance.
	 * @param NodeMemory Pointer to this node's memory block.
	 * @param DeltaSeconds Time elapsed since last tick.
	 */
	virtual void TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds) override;

private:

	/** Cached pointer to the actor's routine component (resolved on demand). */
	UPROPERTY(Transient)
	TObjectPtr<UACFAIRoutineComponent> RoutineComp = nullptr;

	/**
	 * Resolve and cache the UACFAIRoutineComponent from the BT owner (controller/pawn).
	 * Safe to call multiple times; will set RoutineComp if found.
	 * @param OwnerComp Behavior tree component used to access the owning AI and pawn.
	 */
	void ResolveRoutineComponent(UBehaviorTreeComponent& OwnerComp);
};
