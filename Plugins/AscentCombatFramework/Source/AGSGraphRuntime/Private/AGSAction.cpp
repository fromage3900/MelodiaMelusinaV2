// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "AGSAction.h"
#include "AGSGraphNode.h"
#include "AGSGraph.h"

void UAGSAction::Execute(class APlayerController* playerController, UAGSGraphNode* nodeOwner)
{
	Controller = playerController;
	NodeOwner = nodeOwner;
	ExecuteAction(Controller, nodeOwner);
}

void UAGSAction::ExecuteAction_Implementation(class APlayerController* playerController, UAGSGraphNode* nodeOwner)
{

}

AActor* UAGSAction::GetGraphOwnerActor() const
{
	return NodeOwner ? NodeOwner->GetGraph()->GetOwnerActor() : nullptr;
}

UWorld* UAGSAction::GetWorld() const
{
	if(Controller){
		return Controller->GetWorld();
	}
	return nullptr;
}
