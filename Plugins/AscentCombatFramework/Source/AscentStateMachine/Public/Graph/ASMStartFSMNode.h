// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Graph/ASMStateNode.h"
#include "ASMStartFSMNode.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTSTATEMACHINE_API UASMStartFSMNode : public UASMStateNode
{
	GENERATED_BODY()
	
public: 

	UASMStartFSMNode();

#if WITH_EDITOR

	virtual FText GetNodeTitle() const {
		return FText::FromString("FSM Start");
	}

#endif

};
