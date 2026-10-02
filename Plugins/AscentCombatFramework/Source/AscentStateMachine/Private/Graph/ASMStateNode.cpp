// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Graph/ASMStateNode.h"
#include <Kismet/GameplayStatics.h>
#include "ASMBaseFSMState.h"
#include "Graph/ASMStateMachine.h"
#include "Math/Color.h"


void UASMStateNode::ActivateNode()
{
	Super::ActivateNode();
	if (State) {
		APlayerController* control = UGameplayStatics::GetPlayerController(this, 0);
		State->Internal_OnEnter(control,
			Cast<UASMStateMachine>(GetGraph()));
	}
	else {
		UE_LOG(LogTemp, Error, TEXT("Invalid State - UASMStateNode::ActivateNode "));
	}
}

void UASMStateNode::DeactivateNode()
{
	Super::DeactivateNode();
	if (State) {
		State->Internal_OnExit();
	}
	else {
		UE_LOG(LogTemp, Error, TEXT("Invalid State - UASMStateNode::DectivateNode"));
	}
}

void UASMStateNode::OnTransition(const UASMBaseFSMState* previousState)
{
	if (State) {
		State->OnTransition(previousState);
	}
	else {
		UE_LOG(LogTemp, Error, TEXT("Invalid State - UASMStateNode::OnTransition"));
	}
}

UASMStateNode::UASMStateNode()
{
#if WITH_EDITOR
	BackgroundColor = FLinearColor::Black;
	#endif
}
