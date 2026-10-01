// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Graph/ADSDialogueResponseNode.h"
#include "Graph/ADSDialogue.h"
#include "Graph/ADSGraphNode.h"
#include <ADSDialoguePartecipantComponent.h>
#include "ADSDialogueDeveloperSettings.h"

bool UADSDialogueResponseNode::CanBeActivated(class APlayerController* inController) 
{
	participant = GatherPartecipant();
	if (!IsValid(participant)) {
		return false;
	}
	if (PartecipantTag != GetDialogueParticipant()->GetParticipantTag() && !bAllowedForEveryPlayer) {
		return false;
	}
	return Super::CanBeActivated(inController);
}

#if WITH_EDITOR

void UADSDialogueResponseNode::InitializeNode()
{
    Super::InitializeNode();
    UADSDialogueDeveloperSettings* settings = GetMutableDefault<UADSDialogueDeveloperSettings>();

    if (settings) {
        PartecipantTag = settings->GetDefaultPlayerResponseTag();
    }
}
#endif

UADSDialogueResponseNode::UADSDialogueResponseNode()
{
#if WITH_EDITOR

	BackgroundColor = FLinearColor::White;
	ContextMenuName = FText::FromString("Response Button Node");
#endif
}

UADSDialogueNode* UADSDialogueResponseNode::ResponseSelected()
{
	UADSDialogue* dialogue = Cast< UADSDialogue>(GetGraph());
	if (dialogue && dialogue->ActivateNode(this))
	{
		return dialogue->MoveToNextNode();
	}
	return nullptr;
}

