// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Graph/ACFSkillTreeGraph.h"
#include "Graph/ACFBaseSkillNode.h"
#include "Graph/ACFSkillTransition.h"

UACFSkillTreeGraph::UACFSkillTreeGraph()
{
    NodeType = UACFBaseSkillNode::StaticClass();
    EdgeType = UACFSkillTransition::StaticClass();
}

bool UACFSkillTreeGraph::ActivateNode(class UAGSGraphNode* Node)
{
    return Super::ActivateNode(Node);
}

UACFBaseSkillNode* UACFSkillTreeGraph::GetSkillNodeById(const FGuid& SkillId) const
{
    for (UAGSGraphNode* Node : AllNodes) {
        UACFBaseSkillNode* SkillNode = Cast<UACFBaseSkillNode>(Node);
        if (SkillNode && SkillNode->GetNodeId() == SkillId) {
            return SkillNode;
        }
    }
    return nullptr;
}

bool UACFSkillTreeGraph::ActivateSkillNode(const FGuid& SkillId)
{
    UACFBaseSkillNode* SkillNode = GetSkillNodeById(SkillId);
    if (SkillNode) {
        return ActivateNode(SkillNode);
    }
    return false;
}

bool UACFSkillTreeGraph::IsSkillNodeActive(const FGuid& SkillId)
{
    UACFBaseSkillNode* SkillNode = GetSkillNodeById(SkillId);
    if (SkillNode) {
        return IsNodeActive(SkillNode);
    }
    return false;
}

bool UACFSkillTreeGraph::AreAllParentsActive(const FGuid& SkillId) const
{
    UACFBaseSkillNode* SkillNode = GetSkillNodeById(SkillId);
    if (SkillNode) {
        for (const UAGSGraphNode* ParentNode : SkillNode->ParentNodes) {
            if (!ParentNode->IsNodeActivated()) {
                return false;
            }
        }
        return true;
    }
    return false;
}