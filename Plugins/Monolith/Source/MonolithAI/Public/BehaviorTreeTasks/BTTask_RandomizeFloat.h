// Copyright Monolith. All Rights Reserved.
//
// Reusable BT task: write a random float in [Min, Max] to a Blackboard float
// key. Generic — drives wait times, gait speeds, intervals, etc.

#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/Tasks/BTTask_BlackboardBase.h"

#include "BTTask_RandomizeFloat.generated.h"   // MUST be last include

class UBehaviorTreeComponent;

/**
 * Writes FMath::FRandRange(Min, Max) to the selected Blackboard float key
 * (inherited BlackboardKey from UBTTask_BlackboardBase). Returns Succeeded
 * when the key resolves and the Blackboard is present; Failed otherwise.
 *
 * Pairs with UBTTask_SetMaxWalkSpeed's Blackboard-key mode to randomize gait:
 * RandomizeFloat -> SetMaxWalkSpeed(SpeedKey = same key).
 */
UCLASS(MinimalAPI, meta = (DisplayName = "Randomize Float"))
class UBTTask_RandomizeFloat : public UBTTask_BlackboardBase
{
	GENERATED_UCLASS_BODY()

public:

	/** Inclusive lower bound of the random range. */
	UPROPERTY(EditAnywhere, Category = "Random")
	float Min;

	/** Inclusive upper bound of the random range. */
	UPROPERTY(EditAnywhere, Category = "Random")
	float Max;

	virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;
	virtual void InitializeFromAsset(UBehaviorTree& Asset) override;
	virtual FString GetStaticDescription() const override;
};
