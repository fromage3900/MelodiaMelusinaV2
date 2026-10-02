// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Graph/ADSStartDialogueNode.h"
#include "ADSDialogueFunctionLibrary.h"
#include "ADSDialogueMasterComponent.h"
#include "ADSDialoguePartecipantComponent.h"
#include "AGSAction.h"
#include "AGSCondition.h"
#include <Components/ActorComponent.h>
#include <Engine/TargetPoint.h>
#include <Kismet/KismetMathLibrary.h>

UADSStartDialogueNode::UADSStartDialogueNode()
{
#if WITH_EDITOR
	BackgroundColor = FLinearColor::Green;
	ContextMenuName = FText::FromString("Start Dialogue Node");
#endif
}

bool UADSStartDialogueNode::CanBeActivated(APlayerController* inController)
{
	return Super::CanBeActivated(inController);
}

void UADSStartDialogueNode::ExecuteEndingActions()
{
	for (UAGSAction* action : DialogueEndedActions) {
		if (action) {
			action->Execute(controller, this);
		}
	}
}

void UADSStartDialogueNode::ActivateNode()
{
	Super::ActivateNode();

	const UADSDialogue* dialogue = Cast<UADSDialogue>(GetGraph());
	if (dialogue && dialogue->GetUseDefaultCameraSettings()) {
		UADSBaseDialoguePartecipantComponent* partCompBase = GetDialogueParticipant();
		UADSDialoguePartecipantComponent* partComp = Cast<UADSDialoguePartecipantComponent>(partCompBase);
		if (partComp) {
			partComp->SetDefaultCameraAndPosition();
		}
	}



}
