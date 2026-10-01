// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AGSGraphNode.h"
#include "AGSGraph.h"

#define LOCTEXT_NAMESPACE "AGSGraphNode"

UAGSGraphNode::UAGSGraphNode()
{
#if WITH_EDITORONLY_DATA
	CompatibleGraphType = UAGSGraph::StaticClass();

	//	BackgroundColor = FLinearColor::Black;
#endif

}

UAGSGraphNode::~UAGSGraphNode()
{
	NodeState = ENodeState::Disabled;
}

UAGSGraphEdge* UAGSGraphNode::GetEdge(UAGSGraphNode* ChildNode) const
{
	return Edges.Contains(ChildNode) ? Edges.FindChecked(ChildNode) : nullptr;
}

FText UAGSGraphNode::GetDescription_Implementation() const
{
	return LOCTEXT("NodeDesc", "Default Node Name");
}

UWorld* UAGSGraphNode::GetWorld() const
{
	return IsValid(Graph) ? Graph->GetWorld() : nullptr;
}

class APlayerController* UAGSGraphNode::GetPlayerController() const
{
	return Graph ? Graph->GetPlayerController() : nullptr;
}

void UAGSGraphNode::ActivateNode()
{
	NodeState = ENodeState::Enabled;
}

void UAGSGraphNode::DeactivateNode()
{
	NodeState = ENodeState::Disabled;
}

void UAGSGraphNode::GenerateNewID()
{
	NodeId = FGuid::NewGuid();
}

#if WITH_EDITOR

FLinearColor UAGSGraphNode::GetBackgroundColor() const
{
	return BackgroundColor;
}

FText UAGSGraphNode::GetNodeTitle() const
{
	return GetDescription();
}

FText UAGSGraphNode::GetParagraphTitle() const
{
	return GetDescription();
}

void UAGSGraphNode::InitializeNode()
{
	if (!NodeId.IsValid())
	{
		GenerateNewID();
	}
}

void UAGSGraphNode::PostDuplicate(bool bDuplicateForPIE)
{
	Super::PostDuplicate(bDuplicateForPIE);
	if (bDuplicateForPIE)
	{
		NodeId = FGuid::NewGuid();
	}
}



// void UAGSGraphNode::SetNodeTitle(const FText& NewTitle)
// {
// 	Text = NewTitle;
// }

bool UAGSGraphNode::CanCreateConnection(UAGSGraphNode* Other, FText& ErrorMessage)
{
	return true;
}

#endif

bool UAGSGraphNode::IsLeafNode() const
{
	return ChildrenNodes.Num() == 0;
}

bool UAGSGraphNode::IsRootNode() const
{
	return ParentNodes.Num() == 0;
}

bool UAGSGraphNode::IsNodeActivated() const
{
	return NodeState == ENodeState::Enabled;
}

UAGSGraph* UAGSGraphNode::GetGraph() const
{
	return Graph;
}

#undef LOCTEXT_NAMESPACE
