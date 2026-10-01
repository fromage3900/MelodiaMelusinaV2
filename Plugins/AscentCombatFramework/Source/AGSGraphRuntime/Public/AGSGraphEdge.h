// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "AGSGraphNode.h"
#include "AGSGraphEdge.generated.h"

class UAGSGraph;

UCLASS(Blueprintable)
class AGSGRAPHRUNTIME_API UAGSGraphEdge : public UObject
{
	GENERATED_BODY()

public:
	UAGSGraphEdge();
	virtual ~UAGSGraphEdge();

	UPROPERTY()
	UAGSGraph* Graph;

	UPROPERTY(BlueprintReadOnly, Category = "Edge")
	UAGSGraphNode* StartNode;

	UPROPERTY(BlueprintReadOnly, Category = "Edge")
	UAGSGraphNode* EndNode;

	UFUNCTION(BlueprintPure, Category = "Edge")
	UAGSGraph* GetGraph() const;
};
