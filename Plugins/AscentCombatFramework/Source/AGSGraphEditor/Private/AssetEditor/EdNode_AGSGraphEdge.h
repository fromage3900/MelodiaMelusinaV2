// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraph.h"
#include "EdNode_AGSGraphEdge.generated.h"

class UAGSGraphNode;
class UAGSGraphEdge;
class UEdNode_AGSGraphNode;

UCLASS(MinimalAPI)
class UEdNode_AGSGraphEdge : public UEdGraphNode {
	GENERATED_BODY()

public:
	UPROPERTY()
	class UEdGraph* Graph;

	UPROPERTY(VisibleAnywhere, Instanced, Category = "AGSGraph")
	UAGSGraphEdge* AGSGraphEdge;

	void SetEdge(UAGSGraphEdge* Edge);

	virtual void AllocateDefaultPins() override;

	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;

	virtual void PinConnectionListChanged(UEdGraphPin* Pin) override;

	virtual void PrepareForCopying() override;

	virtual UEdGraphPin* GetInputPin() const { return Pins[0]; }
	virtual UEdGraphPin* GetOutputPin() const { return Pins[1]; }

	void CreateConnections(UEdNode_AGSGraphNode* Start, UEdNode_AGSGraphNode* End);

	UEdNode_AGSGraphNode* GetStartNode();
	UEdNode_AGSGraphNode* GetEndNode();
};
