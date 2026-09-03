// Copyright Monolith. All Rights Reserved.
//
// Reusable BT task: set the possessed pawn's CharacterMovementComponent
// MaxWalkSpeed. Supports a literal float OR an optional Blackboard float key
// (key wins when set). Project-agnostic — no game-specific values baked in.

#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/BTTaskNode.h"
#include "BehaviorTree/BehaviorTreeTypes.h"   // FBlackboardKeySelector

#include "BTTask_SetMaxWalkSpeed.generated.h"   // MUST be last include

class UBehaviorTreeComponent;

/**
 * Sets MaxWalkSpeed on the AI pawn's UCharacterMovementComponent.
 *
 * Resolution order:
 *   1. If SpeedKey is configured (resolves to a valid Blackboard float key),
 *      use the Blackboard value.
 *   2. Otherwise use the literal Speed.
 *
 * Returns Succeeded whenever a CharacterMovementComponent is found; Failed
 * only when the pawn (or its movement component) is missing.
 */
UCLASS(MinimalAPI, meta = (DisplayName = "Set Max Walk Speed"))
class UBTTask_SetMaxWalkSpeed : public UBTTaskNode
{
	GENERATED_UCLASS_BODY()

public:

	/** Literal speed (cm/s) applied when SpeedKey is not configured. */
	UPROPERTY(EditAnywhere, Category = "Movement", meta = (ClampMin = "0.0"))
	float Speed;

	/**
	 * Optional Blackboard float key. When set to a valid key, its value
	 * overrides the literal Speed. Leave unset to always use Speed.
	 */
	UPROPERTY(EditAnywhere, Category = "Movement")
	FBlackboardKeySelector SpeedKey;

	virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;
	virtual void InitializeFromAsset(UBehaviorTree& Asset) override;
	virtual FString GetStaticDescription() const override;
};
