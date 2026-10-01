// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAITypes.h"
#include "ACFAIController.h"
#include "Actors/ACFCharacter.h"

FAIAgentsInfo::FAIAgentsInfo(AACFCharacter* inChar)
{
    AICharacter = inChar;
    charLevel = 1;
    AILevel = 1;
    bHasSpawnInfo = false;
    if (inChar) {
        characterClass = inChar->GetClass();
        AIClassBP = inChar->GetClass();
    }
}

TObjectPtr<class AACFAIController> FAIAgentsInfo::GetController() const
{
    if (AICharacter) {
        return Cast<AACFAIController>(AICharacter->GetController());

    }

    return nullptr;
}
