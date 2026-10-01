// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AQSBaseNode.h"
#include "CoreMinimal.h"

#include "AQSStartQuestNode.generated.h"

/**
 *
 */
UCLASS()
class ASCENTQUESTSYSTEM_API UAQSStartQuestNode : public UAQSBaseNode {
    GENERATED_BODY()

public:
    UAQSStartQuestNode();

#if WITH_EDITOR

    virtual FText GetNodeTitle() const
    {
        return FText::FromString("Quest Start");
    }

    virtual FText GetParagraphTitle() const
    {
        return FText::FromString("Right click to add Objectives");
    }


#endif


};
