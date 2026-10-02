// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "AQSTypes.h"
#include "Graph/AQSQuest.h"

FAQSQuestRecord::FAQSQuestRecord(const  UAQSQuest* quest)
{
    if (quest) {
        Quest = quest->GetQuestTag();
        for (const auto& obj : quest->GetAllActiveObjectives()) {
            if (obj) {
                Objectives.Add(FAQSObjectiveRecord(obj));
            }
        }
        CompletedObjectives = quest->GetCompletedObjectives();
    }

}