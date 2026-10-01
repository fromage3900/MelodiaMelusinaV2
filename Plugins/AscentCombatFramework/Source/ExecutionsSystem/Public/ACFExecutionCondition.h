// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "CASAnimCondition.h"
#include <GameplayTagContainer.h>
#include "ACFExecutionCondition.generated.h"

/**
 * 
 */
UCLASS()
class EXECUTIONSSYSTEM_API UACFExecutionCondition : public UCASAnimCondition
{
	GENERATED_BODY()

protected: 

	virtual bool VerifyCondition_Implementation(const FCombinedAnimConfig& contextAnim, const class ACharacter* animMaster) override;


	/*Executions can be triggered only if the healt of the owner if belo*/
	UPROPERTY(EditDefaultsOnly, Category = ACF)
	float RemainingHealthPercentage = 15.f;

	/*Chances that the execution will be triggered*/
	UPROPERTY(EditDefaultsOnly, Category = ACF)
	float ExecutionChance = 75.f;
	
};

