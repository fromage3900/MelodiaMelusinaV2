// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Graph/AQSStartQuestNode.h"
#include <WorldPartition/DataLayer/DataLayerManager.h>

UAQSStartQuestNode::UAQSStartQuestNode()
{
#if WITH_EDITOR
	BackgroundColor = FLinearColor::Blue;
	#endif
	bIsCompleted = true;
}


