// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "AGSGraphEdge.h"
#include <GameplayTagContainer.h>
#include "ASMTransition.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTSTATEMACHINE_API UASMTransition : public UAGSGraphEdge
{
	GENERATED_BODY()

protected: 

	UPROPERTY(EditDefaultsOnly, Category = ASM)
	FGameplayTag TransitionTag;

	UPROPERTY(EditDefaultsOnly, Instanced, Category = ASM)
	TArray<class UAGSCondition*> ActivationConditions;

public: 

	 FGameplayTag GetTransitionTag() const {
		return TransitionTag;
	}

	bool VerifyTransitionConditions() ;

};
