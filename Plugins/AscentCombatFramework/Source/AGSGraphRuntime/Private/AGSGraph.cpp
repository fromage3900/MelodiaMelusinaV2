// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AGSGraph.h"
#include "AGSGraphRuntimePCH.h"
#include "Engine/Engine.h"
#include "AGSTypes.h"

#define LOCTEXT_NAMESPACE "AGSGraph"

UAGSGraph::UAGSGraph()
{
    NodeType = UAGSGraphNode::StaticClass();
    EdgeType = UAGSGraphEdge::StaticClass();
    GraphId = FGuid::NewGuid();
    bEdgeEnabled = true;

#if WITH_EDITORONLY_DATA
    EdGraph = nullptr;

    bCanRenameNode = true;
#endif
    ActivedNodes.Empty();
}

UAGSGraph::~UAGSGraph() { }

void UAGSGraph::Print(bool ToConsole /*= true*/, bool ToScreen /*= true*/)
{
    int32 Level = 0;
    TArray<UAGSGraphNode*> CurrLevelNodes = RootNodes;
    TArray<UAGSGraphNode*> NextLevelNodes;

    while (CurrLevelNodes.Num() != 0) {
        for (int32 i = 0; i < CurrLevelNodes.Num(); ++i) {
            UAGSGraphNode* Node = CurrLevelNodes[i];
            check(Node != nullptr);

            FString Message = FString::Printf(
                TEXT("%s, Level %d"), *Node->GetDescription().ToString(), Level);

            if (ToConsole) {
                LOG_INFO(TEXT("%s"), *Message);
            }

            if (ToScreen && GEngine != nullptr) {
                GEngine->AddOnScreenDebugMessage(-1, 15.f, FColor::Blue, Message);
            }

            for (int j = 0; j < Node->ChildrenNodes.Num(); ++j) {
                NextLevelNodes.Add(Node->ChildrenNodes[j]);
            }
        }

        CurrLevelNodes = NextLevelNodes;
        NextLevelNodes.Reset();
        ++Level;
    }
}

bool UAGSGraph::ActivateNode(UAGSGraphNode* node)
{
    if (node && AllNodes.Contains(node)) {
        ActivedNodes.AddUnique(node);
        node->ActivateNode();
        return true;
    }
    return false;
}

bool UAGSGraph::DeactivateNode(UAGSGraphNode* node)
{
    if (node && AllNodes.Contains(node)) {
        node->DeactivateNode();
        ActivedNodes.Remove(node);

        return true;
    }
    return false;
}

void UAGSGraph::DeactivateAllNodes()
{
    TArray<UAGSGraphNode*> copiedVect = GetActiveNodes();
    for (auto node : copiedVect) {
        DeactivateNode(node);
    }
}

bool UAGSGraph::IsNodeActive(class UAGSGraphNode* node)
{
    return ActivedNodes.Contains(node);
}

int UAGSGraph::GetLevelNum() const
{

    int32 Level = 0;
    TArray<UAGSGraphNode*> CurrLevelNodes = RootNodes;
    TArray<UAGSGraphNode*> NextLevelNodes;

    while (CurrLevelNodes.Num() != 0) {
        for (int32 i = 0; i < CurrLevelNodes.Num(); ++i) {
            UAGSGraphNode* Node = CurrLevelNodes[i];
            check(Node != nullptr);

            for (int32 j = 0; j < Node->ChildrenNodes.Num(); ++j) {
                NextLevelNodes.Add(Node->ChildrenNodes[j]);
            }
        }

        CurrLevelNodes = NextLevelNodes;
        NextLevelNodes.Reset();
        ++Level;
    }

    return Level;
}

void UAGSGraph::GetNodesByLevel(int32 Level, TArray<UAGSGraphNode*>& Nodes)
{
    int32 CurrLEvel = 0;
    TArray<UAGSGraphNode*> NextLevelNodes;

    Nodes = RootNodes;

    while (Nodes.Num() != 0) {
        if (CurrLEvel == Level)
            break;

        for (int32 i = 0; i < Nodes.Num(); ++i) {
            UAGSGraphNode* Node = Nodes[i];
            check(Node != nullptr);

            for (int32 j = 0; j < Node->ChildrenNodes.Num(); ++j) {
                NextLevelNodes.Add(Node->ChildrenNodes[j]);
            }
        }

        Nodes = NextLevelNodes;
        NextLevelNodes.Reset();
        ++CurrLEvel;
    }
}

void UAGSGraph::ClearGraph()
{
    for (int32 i = 0; i < AllNodes.Num(); ++i) {
        UAGSGraphNode* Node = AllNodes[i];

        Node->ParentNodes.Empty();
        Node->ChildrenNodes.Empty();
        Node->Edges.Empty();
    }

    AllNodes.Empty();
    RootNodes.Empty();
}

FAGSGraphRecord UAGSGraph::CreateGraphRecord()
{
    FAGSGraphRecord record;
    record.GraphID = GraphId;
    for (const UAGSGraphNode* node : AllNodes) {
        if (node->IsNodeActivated()) {
            record.ActiveNodeIds.Add(GraphId);
        }
    }
    return record;
}

void UAGSGraph::SynchWithGraphRecord(const FAGSGraphRecord& graphRecord)
{
    DeactivateAllNodes();
    for (const auto& nodeId : graphRecord.ActiveNodeIds) {
        UAGSGraphNode* node = GetNodeById(nodeId);
        if (node) {
            node->ActivateNode();
        }
    }
 
}

UAGSGraphNode* UAGSGraph::GetNodeById(const FGuid nodeId) const
{
    for (UAGSGraphNode* node : AllNodes) {
        if (node->GetNodeId() == nodeId) {
            return node;
        }
    }
    return nullptr;
}

#if WITH_EDITOR
#include "UObject/ObjectSaveContext.h"

void UAGSGraph::PreSave(FObjectPreSaveContext SaveContext)
{
    Super::PreSave(SaveContext);

    for (int32 i = ActivedNodes.Num() - 1; i >= 0; --i) {
        auto node = ActivedNodes[i];
        if (!AllNodes.Contains(node)) {
            ActivedNodes.Remove(node);
        }
    }
}
#endif

#undef LOCTEXT_NAMESPACE
