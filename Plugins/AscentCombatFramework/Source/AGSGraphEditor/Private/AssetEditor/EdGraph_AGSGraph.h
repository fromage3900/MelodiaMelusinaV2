// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#pragma once

#include "CoreMinimal.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph_AGSGraph.generated.h"

class UAGSGraph;
class UAGSGraphNode;
class UAGSGraphEdge;
class UEdNode_AGSGraphNode;
class UEdNode_AGSGraphEdge;

UCLASS()
class AGSGRAPHEDITOR_API UEdGraph_AGSGraph : public UEdGraph {
	GENERATED_BODY()

public:
	UEdGraph_AGSGraph();
	virtual ~UEdGraph_AGSGraph();

	virtual void RebuildAGSGraph();

	UAGSGraph* GetAGSGraph() const;

	virtual bool Modify(bool bAlwaysMarkDirty = true) override;
	virtual void PostEditUndo() override;

	UPROPERTY(Transient)
	TMap<UAGSGraphNode*, UEdNode_AGSGraphNode*> NodeMap;

	UPROPERTY(Transient)
	TMap<UAGSGraphEdge*, UEdNode_AGSGraphEdge*> EdgeMap;

protected:
	void Clear();

	void SortNodes(UAGSGraphNode* RootNode);
};
