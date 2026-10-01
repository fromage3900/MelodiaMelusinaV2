// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/BTService.h"
#include "ACFUpdateStateBTService.generated.h"

/**
 * Service that updates the AI state during behavior tree execution.
 */
UCLASS()
class AIFRAMEWORK_API UACFUpdateStateBTService : public UBTService
{
	GENERATED_BODY()

protected:

	/** Reference to the AI Controller that owns this service */
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	TObjectPtr<class AACFAIController> aiController;

	/** Cached pawn owner controlled by the AI */
	UPROPERTY(BlueprintReadOnly, Category = ACF)
    TObjectPtr<class APawn> CharOwner;


public:
	
	void TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds) override;
};
