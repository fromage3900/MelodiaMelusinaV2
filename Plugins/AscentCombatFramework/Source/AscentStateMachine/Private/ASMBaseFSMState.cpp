// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ASMBaseFSMState.h"
#include "Graph/ASMStateMachine.h"

void UASMBaseFSMState::OnEnter_Implementation()
{

}

void UASMBaseFSMState::Internal_OnEnter(class APlayerController* playerController,  UASMStateMachine* inFSM)
{
	FSM = inFSM;
	LocalController = playerController;
	actorOwner = inFSM->GetFSMOwner();
	OnEnter();
}

void UASMBaseFSMState::Internal_OnExit()
{
	OnExit();
}

bool UASMBaseFSMState::TriggerTransition(const FGameplayTag& transition)
{
	if (FSM) {
		return FSM->TriggerTransition(transition);
	}
	return false;
}

void UASMBaseFSMState::OnExit_Implementation()
{

}

void UASMBaseFSMState::OnUpdate_Implementation(float deltaTime)
{

}

void UASMBaseFSMState::OnTransition_Implementation(const UASMBaseFSMState* previousState)
{

}

 UWorld* UASMBaseFSMState::GetWorldContextObject() const
 {
     return LocalController->GetWorld();
}

