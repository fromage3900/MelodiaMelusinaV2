// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Graph/AQSQuestFailedNode.h"

UAQSQuestFailedNode::UAQSQuestFailedNode()
{
#if WITH_EDITOR
	BackgroundColor = FLinearColor::Red;
	#endif
	bIsSuccessful = false;
}


