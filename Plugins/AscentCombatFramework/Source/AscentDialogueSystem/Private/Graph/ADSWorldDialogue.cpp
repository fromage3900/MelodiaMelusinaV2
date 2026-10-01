// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "Graph/ADSWorldDialogue.h"
#include "Graph/ADSDialogueNode.h"
#include "ADSTypes.h"


UADSWorldDialogue::UADSWorldDialogue()
{
	NodeType = UADSDialogueNode::StaticClass();
	UseDefaultCameraSettings = false;
#if WITH_EDITORONLY_DATA
	// World dialogues never use button-answer nodes — force linear player nodes.
	AIPlayerResponseMode = EADSAIPlayerResponseMode::DialogueNodes;
#endif
}
