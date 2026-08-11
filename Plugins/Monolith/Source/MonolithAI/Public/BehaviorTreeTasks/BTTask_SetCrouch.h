// Copyright Monolith. All Rights Reserved.
//
// Reusable BT task: crouch / uncrouch the possessed ACharacter pawn.
// Project-agnostic.

#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/BTTaskNode.h"

#include "BTTask_SetCrouch.generated.h"   // MUST be last include

class UBehaviorTreeComponent;

/**
 * Calls ACharacter::Crouch() (bCrouch == true) or UnCrouch() (bCrouch == false)
 * on the AI pawn. Returns Succeeded when the pawn is an ACharacter; Failed
 * otherwise. The actual crouch state change replicates via the standard
 * Character/CharacterMovementComponent path.
 */
UCLASS(MinimalAPI, meta = (DisplayName = "Set Crouch"))
class UBTTask_SetCrouch : public UBTTaskNode
{
	GENERATED_UCLASS_BODY()

public:

	/** True -> Crouch(); False -> UnCrouch(). */
	UPROPERTY(EditAnywhere, Category = "Movement")
	bool bCrouch;

	virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;
	virtual FString GetStaticDescription() const override;
};
