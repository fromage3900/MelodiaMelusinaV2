// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "AQSFinishQuestNode.h"
#include "AQSQuestSuccededNode.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTQUESTSYSTEM_API UAQSQuestSuccededNode : public UAQSFinishQuestNode
{
	GENERATED_BODY()

public:

	
protected: 

	UAQSQuestSuccededNode();

#if WITH_EDITOR


	virtual FText GetNodeTitle() const {
		return FText::FromString("Quest Succeded");
	}

#endif
};
