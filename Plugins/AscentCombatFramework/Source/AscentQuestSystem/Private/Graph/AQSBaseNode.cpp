// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Graph/AQSBaseNode.h"
#include "AGSAction.h"
#include <Kismet/GameplayStatics.h>

void UAQSBaseNode::ActivateNode()
{
	Super::ActivateNode();

	if (GetPlayerController() && GetPlayerController()->HasAuthority()) {
		for (UAGSAction* action : ActivationActions) {
			if (IsValid(action)) {
				action->Execute(GetPlayerController(), this);
			}
			else {
				UE_LOG(LogTemp, Warning, TEXT("UAQSBaseNode::ActivateNode - Invalid action in ActivationActions for node %s"), *GetName());
				continue;
			}
		}
	}

}

void UAQSBaseNode::DeactivateNode()
{
	Super::DeactivateNode();

}

bool UAQSBaseNode::CanBeActivated() const
{
	for (auto parent : ParentNodes) {
		UAQSBaseNode* parentNode = Cast<UAQSBaseNode>(parent);

		if (parentNode && parentNode->IsCompleted()) {
			continue;
		}
		else {
			return false;
		}
	}
	return true;
}

UAQSBaseNode::UAQSBaseNode()
{
#if WITH_EDITOR
	BackgroundColor = FLinearColor::Black;
#endif
}

void UAQSBaseNode::CompleteNode()
{
	if (GetPlayerController() && GetPlayerController()->HasAuthority()) {

		for (UAGSAction* action : OnCompletionActions) {
			action->Execute(GetPlayerController(), this);
		}
	}
}
