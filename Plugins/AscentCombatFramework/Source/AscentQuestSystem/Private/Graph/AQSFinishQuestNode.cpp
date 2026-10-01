// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Graph/AQSFinishQuestNode.h"
#include "Graph/AQSQuest.h"
#include "AQSQuestManagerComponent.h"

UAQSFinishQuestNode::UAQSFinishQuestNode()
{
}

void UAQSFinishQuestNode::ActivateNode()
{
	Super::ActivateNode();

	UAQSQuest* quest = Cast< UAQSQuest>(GetGraph());
	quest->CompleteQuest(bIsSuccessful);

	if (NextQuestTag != FGameplayTag()) {
		UAQSQuestManagerComponent* questManager = quest->GetQuestManager();
		if (questManager) {
			questManager->StartQuest(NextQuestTag);
		}
	}
}

