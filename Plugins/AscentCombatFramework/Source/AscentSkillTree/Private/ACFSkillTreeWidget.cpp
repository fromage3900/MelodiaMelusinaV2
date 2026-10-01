// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFSkillTreeWidget.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/CanvasPanelSlot.h"
#include "Graph/ACFBaseSkillNode.h"
#include "Slate/SlateBrushAsset.h"
#include "SlateOptMacros.h"
#include <Rendering/DrawElementTypes.h>
#include <Components/PanelWidget.h>
#include "ACFSkillNodeWidget.h"



void UACFSkillTreeWidget::BuildFromNodes(const TArray<UAGSGraphNode*>& RootNodes)
{
    if (!SkillsConnections || !CanvasPanel) {
        return;
    }

    // Clear existing widgets and connections
    SkillsConnections->EmptyConnections();
    for (auto Pair : NodeToWidgetMap) {
        CanvasPanel->RemoveChild(Pair.Value);
    }
    NodeToWidgetMap.Empty();

    if (RootNodes.Num() == 0) {
        return;
    }


    const float HorizontalSpacing = BaseNodeDistance;
    const float VerticalSpacing = BaseNodeDistance * 0.75f;

    // Create all widgets
    TSet<UACFBaseSkillNode*> Visited;

    const float HorizontalRootSpacing = BaseNodeDistance * 3.f;
    const int32 NumRoots = RootNodes.Num();

    const float TotalRootWidth = (NumRoots > 0) ? (NumRoots - 1) * HorizontalRootSpacing : 0.f;
    const float StartX = -(TotalRootWidth * 0.5f);

    for (int32 i = 0; i < NumRoots; i++)
    {
        UACFBaseSkillNode* RootNode = Cast<UACFBaseSkillNode>(RootNodes[i]);
        if (RootNode)
        {
            FVector2D RootPosition = FVector2D(StartX + (i * HorizontalRootSpacing), TreeStartPosition.Y);
            RecursivelyBuildNode(RootNode, RootPosition, HorizontalSpacing, VerticalSpacing, Visited);
        }
    }

    //Center nodes
    if (NodeToWidgetMap.Num() > 0)
    {
        float MinTreeX = FLT_MAX;
        float MaxTreeX = -FLT_MAX;

        for (auto& Pair : NodeToWidgetMap)
        {
            UACFSkillNodeWidget* Widget = Pair.Value;
            if (UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(Widget->Slot))
            {
                float NodeX = CanvasSlot->GetPosition().X;
                if (NodeX < MinTreeX) MinTreeX = NodeX;
                if (NodeX > MaxTreeX) MaxTreeX = NodeX;
            }
        }


        float CanvasWidth = CanvasPanel->GetCachedGeometry().GetLocalSize().X;

        if (CanvasWidth <= 0.f)
        {
            const FVector2D ViewportSize = UWidgetLayoutLibrary::GetViewportSize(GetWorld());
            CanvasWidth = ViewportSize.X;
        }

        const float CanvasCenter = CanvasWidth * 0.5f;
        const float TreeCenter = (MinTreeX + MaxTreeX) * 0.5f;
        const float CenterOffset = CanvasCenter - TreeCenter;

        for (auto& Pair : NodeToWidgetMap)
        {
            UACFSkillNodeWidget* Widget = Pair.Value;
            if (UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(Widget->Slot))
            {
                FVector2D CurrentPos = CanvasSlot->GetPosition();
                CanvasSlot->SetPosition(FVector2D(CurrentPos.X + CenterOffset, CurrentPos.Y));
            }
        }
    }

    // Create connections
    for (auto& Pair : NodeToWidgetMap)
    {
        UACFBaseSkillNode* ParentNode = Pair.Key;
        UACFSkillNodeWidget* ParentWidget = Pair.Value;

        for (UAGSGraphNode* ChildNode : ParentNode->ChildrenNodes)
        {
            UACFBaseSkillNode* ChildSkillNode = Cast<UACFBaseSkillNode>(ChildNode);
            if (ChildSkillNode && NodeToWidgetMap.Contains(ChildSkillNode))
            {
                SkillsConnections->AddConnection(
                    ParentWidget,
                    NodeToWidgetMap[ChildSkillNode],
                    ConnectionColor,
                    ConnectionThickness);
            }
        }
    }

    CanvasPanel->InvalidateLayoutAndVolatility();
}

void UACFSkillTreeWidget::RecursivelyBuildNode(
    UACFBaseSkillNode* Node,
    const FVector2D& ParentPosition,
    float HorizontalSpacing,
    float VerticalSpacing,
    TSet<UACFBaseSkillNode*>& Visited)
{
    if (!Node || Visited.Contains(Node)) {
        return;
    }

    Visited.Add(Node);

    UACFSkillNodeWidget* NodeWidget = CreateWidget<UACFSkillNodeWidget>(GetWorld(), SkillNodeWidgetClass);
    if (!NodeWidget) {
        return;
    }

    NodeWidget->SetupWithNode(Node);
    CanvasPanel->AddChild(NodeWidget);

    // Calcola posizione basata sulla gerarchia
    FVector2D NodePosition;
    
    if (Node->IsRootNode())
    {
        // Nodi radice usano la posizione del genitore direttamente
        NodePosition = ParentPosition;
    }
    else
    {
        // Nodi figli: posiziona sotto il genitore con spaziatura orizzontale distribuita
        UACFBaseSkillNode* ParentSkillNode = Cast<UACFBaseSkillNode>(Node->ParentNodes[0]);
        if (ParentSkillNode && NodeToWidgetMap.Contains(ParentSkillNode))
        {
            int32 SiblingIndex = ParentSkillNode->ChildrenNodes.IndexOfByKey(Node);
            int32 SiblingCount = ParentSkillNode->ChildrenNodes.Num();
            
            // Distribuzione orizzontale centrata
            float XOffset = (SiblingIndex - (SiblingCount - 1) * 0.5f) * HorizontalSpacing;
            NodePosition = ParentPosition + FVector2D(XOffset, VerticalSpacing);
        }
        else
        {
            // Fallback se non trova il genitore
            NodePosition = ParentPosition + FVector2D(0, VerticalSpacing);
        }
    }

    if (UCanvasPanelSlot* PanelSlot = Cast<UCanvasPanelSlot>(NodeWidget->Slot))
    {
        PanelSlot->SetPosition(NodePosition);
        PanelSlot->SetAlignment(FVector2D(0.5f, 0.5f));
        PanelSlot->SetSize(SkillWidgetSize);
    }

    NodeToWidgetMap.Add(Node, NodeWidget);

    // Process children
    for (UAGSGraphNode* Child : Node->ChildrenNodes)
    {
        UACFBaseSkillNode* ChildSkillNode = Cast<UACFBaseSkillNode>(Child);
        if (ChildSkillNode)
        {
            RecursivelyBuildNode(ChildSkillNode, NodePosition, HorizontalSpacing, VerticalSpacing, Visited);
        }
    }
}

UWidget* UACFSkillTreeWidget::GetFirstSkillWidget() const
{
    return CanvasPanel->GetChildAt(0);
}