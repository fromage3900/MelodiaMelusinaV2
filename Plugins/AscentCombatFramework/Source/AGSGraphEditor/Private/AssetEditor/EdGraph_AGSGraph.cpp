// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "EdGraph_AGSGraph.h"
#include "AGSGraphEditorPCH.h"
#include "AGSGraph.h"
#include "EdNode_AGSGraphNode.h"
#include "EdNode_AGSGraphEdge.h"

UEdGraph_AGSGraph::UEdGraph_AGSGraph()
{

}

UEdGraph_AGSGraph::~UEdGraph_AGSGraph()
{

}

void UEdGraph_AGSGraph::RebuildAGSGraph()
{
	LOG_INFO(TEXT("UAGSGraphEdGraph::RebuildAGSGraph has been called"));

	UAGSGraph* Graph = GetAGSGraph();

	Clear();

	for (int i = 0; i < Nodes.Num(); ++i)
	{
		if (UEdNode_AGSGraphNode* EdNode = Cast<UEdNode_AGSGraphNode>(Nodes[i]))
		{
			if (EdNode->AGSGraphNode == nullptr)
				continue;

			UAGSGraphNode* AGSGraphNode = EdNode->AGSGraphNode;

			// Keep the runtime node position in sync with the editor layout so that
			// gameplay code (e.g. ordering of dialogue answers) can rely on the
			// authored left-to-right placement even when nodes are moved by drag.
			AGSGraphNode->SetNodePosition(FVector2D(EdNode->NodePosX, EdNode->NodePosY));

			NodeMap.Add(AGSGraphNode, EdNode);

			Graph->AllNodes.Add(AGSGraphNode);

			for (int PinIdx = 0; PinIdx < EdNode->Pins.Num(); ++PinIdx)
			{
				UEdGraphPin* Pin = EdNode->Pins[PinIdx];

				if (Pin->Direction != EEdGraphPinDirection::EGPD_Output)
					continue;

				for (int LinkToIdx = 0; LinkToIdx < Pin->LinkedTo.Num(); ++LinkToIdx)
				{
					UAGSGraphNode* ChildNode = nullptr;
					if (UEdNode_AGSGraphNode* EdNode_Child = Cast<UEdNode_AGSGraphNode>(Pin->LinkedTo[LinkToIdx]->GetOwningNode()))
					{
						ChildNode = EdNode_Child->AGSGraphNode;
					}
					else if (UEdNode_AGSGraphEdge* EdNode_Edge = Cast<UEdNode_AGSGraphEdge>(Pin->LinkedTo[LinkToIdx]->GetOwningNode()))
					{
						UEdNode_AGSGraphNode* Child = EdNode_Edge->GetEndNode();;
						if (Child != nullptr)
						{
							ChildNode = Child->AGSGraphNode;
						}
					}

					if (ChildNode != nullptr)
					{
						AGSGraphNode->ChildrenNodes.Add(ChildNode);

						ChildNode->ParentNodes.Add(AGSGraphNode);
					}
					else
					{
						LOG_ERROR(TEXT("UEdGraph_AGSGraph::RebuildAGSGraph can't find child node"));
					}
				}
			}
		}
		else if (UEdNode_AGSGraphEdge* EdgeNode = Cast<UEdNode_AGSGraphEdge>(Nodes[i]))
		{
			UEdNode_AGSGraphNode* StartNode = EdgeNode->GetStartNode();
			UEdNode_AGSGraphNode* EndNode = EdgeNode->GetEndNode();
			UAGSGraphEdge* Edge = EdgeNode->AGSGraphEdge;

			if (StartNode == nullptr || EndNode == nullptr || Edge == nullptr)
			{
				LOG_ERROR(TEXT("UEdGraph_AGSGraph::RebuildAGSGraph add edge failed."));
				continue;
			}

			EdgeMap.Add(Edge, EdgeNode);

			Edge->Graph = Graph;
			Edge->Rename(nullptr, Graph, REN_DontCreateRedirectors | REN_DoNotDirty);
			Edge->StartNode = StartNode->AGSGraphNode;
			Edge->EndNode = EndNode->AGSGraphNode;
			Edge->StartNode->Edges.Add(Edge->EndNode, Edge);
		}
	}

	for (int i = 0; i < Graph->AllNodes.Num(); ++i)
	{
		UAGSGraphNode* Node = Graph->AllNodes[i];
		if (Node->ParentNodes.Num() == 0)
		{
			Graph->RootNodes.Add(Node);

			if (!Graph->bAllowCycles) {
				SortNodes(Node);
			}
		}

		Node->Graph = Graph;
		Node->Rename(nullptr, Graph, REN_DontCreateRedirectors | REN_DoNotDirty);
	}

	Graph->RootNodes.Sort([&](const UAGSGraphNode& L, const UAGSGraphNode& R)
	{
		UEdNode_AGSGraphNode* EdNode_LNode = NodeMap[&L];
		UEdNode_AGSGraphNode* EdNode_RNode = NodeMap[&R];
		return EdNode_LNode->NodePosX < EdNode_RNode->NodePosX;
	});
}

UAGSGraph* UEdGraph_AGSGraph::GetAGSGraph() const
{
	return CastChecked<UAGSGraph>(GetOuter());
}

bool UEdGraph_AGSGraph::Modify(bool bAlwaysMarkDirty /*= true*/)
{
	bool Rtn = Super::Modify(bAlwaysMarkDirty);

	GetAGSGraph()->Modify();

	for (int32 i = 0; i < Nodes.Num(); ++i)
	{
		Nodes[i]->Modify();
	}

	return Rtn;
}

void UEdGraph_AGSGraph::Clear()
{
	UAGSGraph* Graph = GetAGSGraph();

	Graph->ClearGraph();
	NodeMap.Reset();
	EdgeMap.Reset();

	for (int i = 0; i < Nodes.Num(); ++i)
	{
		if (UEdNode_AGSGraphNode* EdNode = Cast<UEdNode_AGSGraphNode>(Nodes[i]))
		{
			UAGSGraphNode* AGSGraphNode = EdNode->AGSGraphNode;
			AGSGraphNode->ParentNodes.Reset();
			AGSGraphNode->ChildrenNodes.Reset();
			AGSGraphNode->Edges.Reset();
		}
	}
}

void UEdGraph_AGSGraph::SortNodes(UAGSGraphNode* RootNode)
{
	int Level = 0;
	TArray<UAGSGraphNode*> CurrLevelNodes = { RootNode };
	TArray<UAGSGraphNode*> NextLevelNodes;

	while (CurrLevelNodes.Num() != 0)
	{
		int32 LevelWidth = 0;
		for (int i = 0; i < CurrLevelNodes.Num(); ++i)
		{
			UAGSGraphNode* Node = CurrLevelNodes[i];

			auto Comp = [&](const UAGSGraphNode& L, const UAGSGraphNode& R)
			{
				UEdNode_AGSGraphNode* EdNode_LNode = NodeMap[&L];
				UEdNode_AGSGraphNode* EdNode_RNode = NodeMap[&R];
				return EdNode_LNode->NodePosX < EdNode_RNode->NodePosX;
			};

			Node->ChildrenNodes.Sort(Comp);
			Node->ParentNodes.Sort(Comp);

			for (int j = 0; j < Node->ChildrenNodes.Num(); ++j)
			{
				NextLevelNodes.Add(Node->ChildrenNodes[j]);
			}
		}

		CurrLevelNodes = NextLevelNodes;
		NextLevelNodes.Reset();
		++Level;
	}
}

void UEdGraph_AGSGraph::PostEditUndo()
{
	Super::PostEditUndo();

	NotifyGraphChanged();
}

