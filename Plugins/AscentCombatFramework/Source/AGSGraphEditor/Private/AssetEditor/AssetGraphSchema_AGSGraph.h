// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#pragma once

#include "CoreMinimal.h"
#include "AGSGraph.h"
#include "AGSGraphNode.h"
#include "AGSGraphEdge.h"
#include "EdGraph/EdGraphSchema.h"
#include "AssetGraphSchema_AGSGraph.generated.h"

class UEdNode_AGSGraphNode;
class UEdNode_AGSGraphEdge;
class UAutoLayoutStrategy;

/** Action to add a node to the graph */
USTRUCT()
struct AGSGRAPHEDITOR_API FAssetSchemaAction_AGSGraph_NewNode : public FEdGraphSchemaAction {
	GENERATED_USTRUCT_BODY();

public:
	FAssetSchemaAction_AGSGraph_NewNode(): NodeTemplate(nullptr) {}

	FAssetSchemaAction_AGSGraph_NewNode(const FText& InNodeCategory, const FText& InMenuDesc, const FText& InToolTip, const int32 InGrouping)
		: FEdGraphSchemaAction(InNodeCategory, InMenuDesc, InToolTip, InGrouping), NodeTemplate(nullptr) {}

	virtual UEdGraphNode* PerformAction(class UEdGraph* ParentGraph, UEdGraphPin* FromPin, const FVector2D Location, bool bSelectNewNode = true) override;
	virtual void AddReferencedObjects(FReferenceCollector& Collector) override;

	TObjectPtr<UEdNode_AGSGraphNode> NodeTemplate;
};

USTRUCT()
struct AGSGRAPHEDITOR_API FAssetSchemaAction_AGSGraph_NewEdge : public FEdGraphSchemaAction {
	GENERATED_USTRUCT_BODY();

public:
	FAssetSchemaAction_AGSGraph_NewEdge(): NodeTemplate(nullptr){}

	FAssetSchemaAction_AGSGraph_NewEdge(const FText& InNodeCategory, const FText& InMenuDesc, const FText& InToolTip, const int32 InGrouping)
		: FEdGraphSchemaAction(InNodeCategory, InMenuDesc, InToolTip, InGrouping), NodeTemplate(nullptr) {}

	virtual UEdGraphNode* PerformAction(class UEdGraph* ParentGraph, UEdGraphPin* FromPin, const FVector2D Location, bool bSelectNewNode = true) override;
	virtual void AddReferencedObjects(FReferenceCollector& Collector) override;

	TObjectPtr <UEdNode_AGSGraphEdge> NodeTemplate;
};

UCLASS(MinimalAPI)
class UAssetGraphSchema_AGSGraph : public UEdGraphSchema {
	GENERATED_BODY()

public:
	void GetBreakLinkToSubMenuActions(UToolMenu* Menu, UEdGraphPin* InGraphPin);

	virtual EGraphType GetGraphType(const UEdGraph* TestEdGraph) const override;

 	virtual void GetGraphContextActions(FGraphContextMenuBuilder& ContextMenuBuilder) const override;

	virtual void GetContextMenuActions(class UToolMenu* Menu, class UGraphNodeContextMenuContext* Context) const override;

 	virtual const FPinConnectionResponse CanCreateConnection(const UEdGraphPin* A, const UEdGraphPin* B) const override;

	virtual bool CreateAutomaticConversionNodeAndConnections(UEdGraphPin* A, UEdGraphPin* B) const override;

	virtual class FConnectionDrawingPolicy* CreateConnectionDrawingPolicy(int32 InBackLayerID, int32 InFrontLayerID, float InZoomFactor, const FSlateRect& InClippingRect, class FSlateWindowElementList& InDrawElements, class UEdGraph* InGraphObj) const override;

 	virtual FLinearColor GetPinTypeColor(const FEdGraphPinType& PinType) const override;

 	virtual void BreakNodeLinks(UEdGraphNode& TargetNode) const override;

 	virtual void BreakPinLinks(UEdGraphPin& TargetPin, bool bSendsNodeNotifcation) const override;

	virtual void BreakSinglePinLink(UEdGraphPin* SourcePin, UEdGraphPin* TargetPin) const override;

	virtual UEdGraphPin* DropPinOnNode(UEdGraphNode* InTargetNode, const FName& InSourcePinName, const FEdGraphPinType& InSourcePinType, EEdGraphPinDirection InSourcePinDirection) const override;

	virtual bool SupportsDropPinOnNode(UEdGraphNode* InTargetNode, const FEdGraphPinType& InSourcePinType, EEdGraphPinDirection InSourcePinDirection, FText& OutErrorMessage) const override;

	virtual bool IsCacheVisualizationOutOfDate(int32 InVisualizationCacheID) const override;

	virtual int32 GetCurrentVisualizationCacheID() const override;

	virtual void ForceVisualizationCacheClear() const override;

private:
	static int32 CurrentCacheRefreshID;
};

