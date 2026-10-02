// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/BTService.h"
#include "ACFUpdatePatrolBTService.generated.h"

/**
 * 
 */
UCLASS()
class AIFRAMEWORK_API UACFUpdatePatrolBTService : public UBTService
{
	GENERATED_BODY()
protected: 

	virtual void TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds) override;
};
