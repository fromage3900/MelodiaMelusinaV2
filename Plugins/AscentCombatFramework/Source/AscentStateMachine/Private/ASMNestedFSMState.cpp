// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ASMNestedFSMState.h"
#include "Graph/ASMStateMachine.h"

bool UASMNestedFSMState::TriggerSubFSMTransition(const FGameplayTag& transition)
{
	if (SubFSM) {
		return SubFSM->TriggerTransition(transition);
	}
	return false;
}

void UASMNestedFSMState::OnEnter_Implementation()
{
	if (SubFSM) {
		SubFSM->StartFSM(actorOwner);
	}
}

void UASMNestedFSMState::OnExit_Implementation()
{
	if (SubFSM) {
		SubFSM->StopFSM();
	}
}

void UASMNestedFSMState::OnUpdate_Implementation(float deltaTime)
{
	if (SubFSM && bCanFsmTick) {
		SubFSM->DispatchTick(deltaTime);
	}
}
