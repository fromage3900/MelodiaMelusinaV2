// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "ASMBaseFSMState.h"
#include <GameplayTagContainer.h>
#include "ASMNestedFSMState.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTSTATEMACHINE_API UASMNestedFSMState : public UASMBaseFSMState
{
	GENERATED_BODY()

public:

	/*Triggers the provided transition in the SubFSM, returns whether the transition is succesful*/
	UFUNCTION(BlueprintCallable, Category = ASM)
	bool TriggerSubFSMTransition(const FGameplayTag& transition);
protected: 

	/*The actual FSM. SubFSMs are currently not replicated*/
	UPROPERTY(EditDefaultsOnly, Category = ASM)
	UASMStateMachine* SubFSM;
	
	/*Sets if this fsm should tick. 
	Please notice that SubFSMs can tick only if main fsm ticks*/
	UPROPERTY(EditDefaultsOnly, Category = ASM)
	bool bCanFsmTick = false;


	virtual void OnEnter_Implementation() override;

	virtual void OnExit_Implementation() override;

	virtual void OnUpdate_Implementation(float deltaTime) override;
};
