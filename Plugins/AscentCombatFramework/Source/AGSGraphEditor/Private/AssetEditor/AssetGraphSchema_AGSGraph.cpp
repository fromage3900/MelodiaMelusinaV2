// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AssetGraphSchema_AGSGraph.h"
#include "AGSGraphEditorPCH.h"
#include "ConnectionDrawingPolicy_AGSGraph.h"
#include "EdNode_AGSGraphEdge.h"
#include "EdNode_AGSGraphNode.h"
#include "Framework/Commands/GenericCommands.h"
#include "GraphEditorActions.h"
#include "ScopedTransaction.h"
#include "ToolMenus.h"
#include "UObject/UObjectIterator.h"

#define LOCTEXT_NAMESPACE "AssetSchema_AGSGraph"

int32 UAssetGraphSchema_AGSGraph::CurrentCacheRefreshID = 0;

class FNodeVisitorCycleChecker {
public:
    /** Check whether a loop in the graph would be caused by linking the passed-in nodes */
    bool CheckForLoop(UEdGraphNode* StartNode, UEdGraphNode* EndNode)
    {
        VisitedNodes.Add(StartNode);

        return TraverseInputNodesToRoot(EndNode);
    }

private:
    bool TraverseInputNodesToRoot(UEdGraphNode* Node)
    {
        VisitedNodes.Add(Node);

        for (int32 PinIndex = 0; PinIndex < Node->Pins.Num(); ++PinIndex) {
            UEdGraphPin* MyPin = Node->Pins[PinIndex];

            if (MyPin->Direction == EGPD_Output) {
                for (int32 LinkedPinIndex = 0; LinkedPinIndex < MyPin->LinkedTo.Num(); ++LinkedPinIndex) {
                    UEdGraphPin* OtherPin = MyPin->LinkedTo[LinkedPinIndex];
                    if (OtherPin) {
                        UEdGraphNode* OtherNode = OtherPin->GetOwningNode();
                        if (VisitedNodes.Contains(OtherNode)) {
                            return false;
                        } else {
                            return TraverseInputNodesToRoot(OtherNode);
                        }
                    }
                }
            }
        }

        return true;
    }

    TSet<UEdGraphNode*> VisitedNodes;
};

UEdGraphNode* FAssetSchemaAction_AGSGraph_NewNode::PerformAction(class UEdGraph* ParentGraph, UEdGraphPin* FromPin, const FVector2D Location, bool bSelectNewNode /*= true*/)
{
    UEdGraphNode* ResultNode = nullptr;

    if (NodeTemplate != nullptr) {
        const FScopedTransaction Transaction(LOCTEXT("AGSGraphEditorNewNode", "Generic Graph Editor: New Node"));
        ParentGraph->Modify();
        if (FromPin != nullptr)
            FromPin->Modify();

        NodeTemplate->Rename(nullptr, ParentGraph);
        ParentGraph->AddNode(NodeTemplate, true, bSelectNewNode);

        NodeTemplate->CreateNewGuid();
        NodeTemplate->PostPlacedNewNode();
        NodeTemplate->AllocateDefaultPins();
        NodeTemplate->AutowireNewNode(FromPin);

        NodeTemplate->NodePosX = Location.X;
        NodeTemplate->NodePosY = Location.Y;

        NodeTemplate->AGSGraphNode->SetFlags(RF_Transactional);
        NodeTemplate->SetFlags(RF_Transactional);

        ResultNode = NodeTemplate;
    }

    return ResultNode;
}

void FAssetSchemaAction_AGSGraph_NewNode::AddReferencedObjects(FReferenceCollector& Collector)
{
    FEdGraphSchemaAction::AddReferencedObjects(Collector);
    Collector.AddReferencedObject(NodeTemplate);
}

UEdGraphNode* FAssetSchemaAction_AGSGraph_NewEdge::PerformAction(class UEdGraph* ParentGraph, UEdGraphPin* FromPin, const FVector2D Location, bool bSelectNewNode /*= true*/)
{
    UEdGraphNode* ResultNode = nullptr;

    if (NodeTemplate != nullptr) {
        const FScopedTransaction Transaction(LOCTEXT("AGSGraphEditorNewEdge", "Generic Graph Editor: New Edge"));
        ParentGraph->Modify();
        if (FromPin != nullptr)
            FromPin->Modify();

        NodeTemplate->Rename(nullptr, ParentGraph);
        ParentGraph->AddNode(NodeTemplate, true, bSelectNewNode);

        NodeTemplate->CreateNewGuid();
        NodeTemplate->PostPlacedNewNode();
        NodeTemplate->AllocateDefaultPins();
        NodeTemplate->AutowireNewNode(FromPin);

        NodeTemplate->NodePosX = Location.X;
        NodeTemplate->NodePosY = Location.Y;

        NodeTemplate->AGSGraphEdge->SetFlags(RF_Transactional);
        NodeTemplate->SetFlags(RF_Transactional);

        ResultNode = NodeTemplate;
    }

    return ResultNode;
}

void FAssetSchemaAction_AGSGraph_NewEdge::AddReferencedObjects(FReferenceCollector& Collector)
{
    FEdGraphSchemaAction::AddReferencedObjects(Collector);
    Collector.AddReferencedObject(NodeTemplate);
}

void UAssetGraphSchema_AGSGraph::GetBreakLinkToSubMenuActions(UToolMenu* Menu, UEdGraphPin* InGraphPin)
{
    // Make sure we have a unique name for every entry in the list
    TMap<FString, uint32> LinkTitleCount;

    FToolMenuSection& Section = Menu->FindOrAddSection("GenericGraph0PinActions");

    // Add all the links we could break from
    for (TArray<class UEdGraphPin*>::TConstIterator Links(InGraphPin->LinkedTo); Links; ++Links) {
        UEdGraphPin* Pin = *Links;
        FString TitleString = Pin->GetOwningNode()->GetNodeTitle(ENodeTitleType::ListView).ToString();
        FText Title = FText::FromString(TitleString);
        if (Pin->PinName != TEXT("")) {
            TitleString = FString::Printf(TEXT("%s (%s)"), *TitleString, *Pin->PinName.ToString());

            // Add name of connection if possible
            FFormatNamedArguments Args;
            Args.Add(TEXT("NodeTitle"), Title);
            Args.Add(TEXT("PinName"), Pin->GetDisplayName());
            Title = FText::Format(LOCTEXT("BreakDescPin", "{NodeTitle} ({PinName})"), Args);
        }

        uint32& Count = LinkTitleCount.FindOrAdd(TitleString);

        FText Description;
        FFormatNamedArguments Args;
        Args.Add(TEXT("NodeTitle"), Title);
        Args.Add(TEXT("NumberOfNodes"), Count);

        if (Count == 0) {
            Description = FText::Format(LOCTEXT("BreakDesc", "Break link to {NodeTitle}"), Args);
        } else {
            Description = FText::Format(LOCTEXT("BreakDescMulti", "Break link to {NodeTitle} ({NumberOfNodes})"), Args);
        }
        ++Count;

        Section.AddMenuEntry(NAME_None, Description, Description, FSlateIcon(), FUIAction(FExecuteAction::CreateUObject(this, &UAssetGraphSchema_AGSGraph::BreakSinglePinLink, const_cast<UEdGraphPin*>(InGraphPin), *Links)));
    }
}

EGraphType UAssetGraphSchema_AGSGraph::GetGraphType(const UEdGraph* TestEdGraph) const
{
    return GT_StateMachine;
}

void UAssetGraphSchema_AGSGraph::GetGraphContextActions(FGraphContextMenuBuilder& ContextMenuBuilder) const
{
    UAGSGraph* Graph = CastChecked<UAGSGraph>(ContextMenuBuilder.CurrentGraph->GetOuter());

    if (Graph->NodeType == nullptr) {
        return;
    }

    const bool bNoParent = (ContextMenuBuilder.FromPin == NULL);

    const FText AddToolTip = LOCTEXT("NewAGSGraphNodeTooltip", "Add node here");

    TSet<TSubclassOf<UAGSGraphNode>> Visited;

    FText Desc = Graph->NodeType.GetDefaultObject()->ContextMenuName;

    if (Desc.IsEmpty()) {
        FString Title = Graph->NodeType->GetName();
        Title.RemoveFromEnd("_C");
        Desc = FText::FromString(Title);
    }

    if (!Graph->NodeType->HasAnyClassFlags(CLASS_Abstract)) {
        TSharedPtr<FAssetSchemaAction_AGSGraph_NewNode> NewNodeAction(new FAssetSchemaAction_AGSGraph_NewNode(LOCTEXT("AGSGraphNodeAction", "Generic Graph Node"), Desc, AddToolTip, 0));
        NewNodeAction->NodeTemplate = NewObject<UEdNode_AGSGraphNode>(ContextMenuBuilder.OwnerOfTemporaries);
        NewNodeAction->NodeTemplate->AGSGraphNode = NewObject<UAGSGraphNode>(NewNodeAction->NodeTemplate, Graph->NodeType);
        NewNodeAction->NodeTemplate->AGSGraphNode->Graph = Graph;
    
        ContextMenuBuilder.AddAction(NewNodeAction);

        Visited.Add(Graph->NodeType);
    }

    for (TObjectIterator<UClass> It; It; ++It) {
        if (It->IsChildOf(Graph->NodeType) && !It->HasAnyClassFlags(CLASS_Abstract) && !Visited.Contains(*It)) {
            TSubclassOf<UAGSGraphNode> NodeType = *It;

            if (It->GetName().StartsWith("REINST") || It->GetName().StartsWith("SKEL"))
                continue;

            if (!Graph->GetClass()->IsChildOf(NodeType.GetDefaultObject()->CompatibleGraphType))
                continue;

            Desc = NodeType.GetDefaultObject()->ContextMenuName;

            if (Desc.IsEmpty()) {
                FString Title = NodeType->GetName();
                Title.RemoveFromEnd("_C");
                Desc = FText::FromString(Title);
            }

            TSharedPtr<FAssetSchemaAction_AGSGraph_NewNode> Action(new FAssetSchemaAction_AGSGraph_NewNode(LOCTEXT("AGSGraphNodeAction", "Generic Graph Node"), Desc, AddToolTip, 0));
            Action->NodeTemplate = NewObject<UEdNode_AGSGraphNode>(ContextMenuBuilder.OwnerOfTemporaries);
            Action->NodeTemplate->AGSGraphNode = NewObject<UAGSGraphNode>(Action->NodeTemplate, NodeType);
            Action->NodeTemplate->AGSGraphNode->Graph = Graph;
           Action->NodeTemplate->AGSGraphNode->InitializeNode();
            ContextMenuBuilder.AddAction(Action);

            Visited.Add(NodeType);
        }
    }
}

void UAssetGraphSchema_AGSGraph::GetContextMenuActions(class UToolMenu* Menu, class UGraphNodeContextMenuContext* Context) const
{
    if (Context && Context->Pin && Menu) {
        FToolMenuSection& Section = Menu->AddSection("AGSAssetGraphSchemaNodeActions", LOCTEXT("PinActionsMenuHeader", "Pin Actions"));
        {
            // Only display the 'Break Link' option if there is a link to break!
            if (Context->Pin->LinkedTo.Num() > 0) {
                Section.AddMenuEntry(FGraphEditorCommands::Get().BreakPinLinks);

                // add sub menu for break link to
                if (Context->Pin->LinkedTo.Num() > 1) {
                    Section.AddSubMenu(
                        "BreakLinkTo",
                        LOCTEXT("BreakLinkTo", "Break Link To..."),
                        LOCTEXT("BreakSpecificLinks", "Break a specific link..."),
                        FNewToolMenuDelegate::CreateUObject((UAssetGraphSchema_AGSGraph* const)this, &UAssetGraphSchema_AGSGraph::GetBreakLinkToSubMenuActions, const_cast<UEdGraphPin*>(Context->Pin)));
                } else {
                    ((UAssetGraphSchema_AGSGraph* const)this)->GetBreakLinkToSubMenuActions(Menu, const_cast<UEdGraphPin*>(Context->Pin));
                }
            }
        }

    } else if (Context->Node) {
        FToolMenuSection& Section = Menu->AddSection("GenericGraphAssetGraphSchemaNodeActions", LOCTEXT("ClassActionsMenuHeader", "Node Actions"));
        Section.AddMenuEntry(FGenericCommands::Get().Delete);
        Section.AddMenuEntry(FGenericCommands::Get().Cut);
        Section.AddMenuEntry(FGenericCommands::Get().Copy);
        Section.AddMenuEntry(FGenericCommands::Get().Duplicate);

        Section.AddMenuEntry(FGraphEditorCommands::Get().BreakNodeLinks);
    }

    Super::GetContextMenuActions(Menu, Context);
}

const FPinConnectionResponse UAssetGraphSchema_AGSGraph::CanCreateConnection(const UEdGraphPin* A, const UEdGraphPin* B) const
{
    // Make sure the pins are not on the same node
    if (A->GetOwningNode() == B->GetOwningNode()) {
        return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW, LOCTEXT("PinErrorSameNode", "Both are on the same node"));
    }

    // Compare the directions
    if ((A->Direction == EGPD_Input) && (B->Direction == EGPD_Input)) {
        return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW, LOCTEXT("PinErrorInput", "Can't connect input node to input node"));
    } else if ((A->Direction == EGPD_Output) && (B->Direction == EGPD_Output)) {
        return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW, LOCTEXT("PinErrorOutput", "Can't connect output node to output node"));
    }

    UEdNode_AGSGraphNode* EdNode_A = Cast<UEdNode_AGSGraphNode>(A->GetOwningNode());
    UEdNode_AGSGraphNode* EdNode_B = Cast<UEdNode_AGSGraphNode>(B->GetOwningNode());

    if (EdNode_A == nullptr || EdNode_B == nullptr) {
        return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW, LOCTEXT("PinError", "Not a valid UAGSGraphEdNode"));
    }

    // check for cycles
    FNodeVisitorCycleChecker CycleChecker;
    if (!EdNode_A->AGSGraphNode->GetGraph()->bAllowCycles) //&& !CycleChecker.CheckForLoop(A->GetOwningNode(), B->GetOwningNode()))
    {
        return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW, LOCTEXT("PinErrorCycle", "Can't create a graph cycle"));
    }

    FText ErrorMessage;
    if (A->Direction == EGPD_Input) {
        if (!EdNode_A->AGSGraphNode->CanCreateConnection(EdNode_B->AGSGraphNode, ErrorMessage)) {
            return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW, ErrorMessage);
        }
    } else {
        if (!EdNode_B->AGSGraphNode->CanCreateConnection(EdNode_A->AGSGraphNode, ErrorMessage)) {
            return FPinConnectionResponse(CONNECT_RESPONSE_DISALLOW, ErrorMessage);
        }
    }

    if (EdNode_A->AGSGraphNode->GetGraph()->bEdgeEnabled) {
        return FPinConnectionResponse(CONNECT_RESPONSE_MAKE_WITH_CONVERSION_NODE, LOCTEXT("PinConnect", "Connect nodes with edge"));
    } else {
        return FPinConnectionResponse(CONNECT_RESPONSE_MAKE, LOCTEXT("PinConnect", "Connect nodes"));
    }
}

bool UAssetGraphSchema_AGSGraph::CreateAutomaticConversionNodeAndConnections(UEdGraphPin* A, UEdGraphPin* B) const
{
    UEdNode_AGSGraphNode* NodeA = Cast<UEdNode_AGSGraphNode>(A->GetOwningNode());
    UEdNode_AGSGraphNode* NodeB = Cast<UEdNode_AGSGraphNode>(B->GetOwningNode());

    if (NodeA == nullptr || NodeB == nullptr)
        return false;

    if (NodeA->GetInputPin() == nullptr || NodeA->GetOutputPin() == nullptr || NodeB->GetInputPin() == nullptr || NodeB->GetOutputPin() == nullptr)
        return false;

    UAGSGraph* Graph = NodeA->AGSGraphNode->GetGraph();

    FVector2D InitPos((NodeA->NodePosX + NodeB->NodePosX) / 2, (NodeA->NodePosY + NodeB->NodePosY) / 2);

    FAssetSchemaAction_AGSGraph_NewEdge Action;
    Action.NodeTemplate = NewObject<UEdNode_AGSGraphEdge>(NodeA->GetGraph());
    Action.NodeTemplate->SetEdge(NewObject<UAGSGraphEdge>(Action.NodeTemplate, Graph->EdgeType));
    UEdNode_AGSGraphEdge* EdgeNode = Cast<UEdNode_AGSGraphEdge>(Action.PerformAction(NodeA->GetGraph(), nullptr, InitPos, false));

    if (A->Direction == EGPD_Output) {
        EdgeNode->CreateConnections(NodeA, NodeB);
    } else {
        EdgeNode->CreateConnections(NodeB, NodeA);
    }

    return true;
}

class FConnectionDrawingPolicy* UAssetGraphSchema_AGSGraph::CreateConnectionDrawingPolicy(int32 InBackLayerID, int32 InFrontLayerID, float InZoomFactor, const FSlateRect& InClippingRect, class FSlateWindowElementList& InDrawElements, class UEdGraph* InGraphObj) const
{
    return new FConnectionDrawingPolicy_AGSGraph(InBackLayerID, InFrontLayerID, InZoomFactor, InClippingRect, InDrawElements, InGraphObj);
}

FLinearColor UAssetGraphSchema_AGSGraph::GetPinTypeColor(const FEdGraphPinType& PinType) const
{
    return FColor::White;
}

void UAssetGraphSchema_AGSGraph::BreakNodeLinks(UEdGraphNode& TargetNode) const
{
    const FScopedTransaction Transaction(NSLOCTEXT("UnrealEd", "GraphEd_BreakNodeLinks", "Break Node Links"));

    Super::BreakNodeLinks(TargetNode);
}

void UAssetGraphSchema_AGSGraph::BreakPinLinks(UEdGraphPin& TargetPin, bool bSendsNodeNotifcation) const
{
    const FScopedTransaction Transaction(NSLOCTEXT("UnrealEd", "GraphEd_BreakPinLinks", "Break Pin Links"));

    Super::BreakPinLinks(TargetPin, bSendsNodeNotifcation);
}

void UAssetGraphSchema_AGSGraph::BreakSinglePinLink(UEdGraphPin* SourcePin, UEdGraphPin* TargetPin) const
{
    const FScopedTransaction Transaction(NSLOCTEXT("UnrealEd", "GraphEd_BreakSinglePinLink", "Break Pin Link"));

    Super::BreakSinglePinLink(SourcePin, TargetPin);
}

UEdGraphPin* UAssetGraphSchema_AGSGraph::DropPinOnNode(UEdGraphNode* InTargetNode, const FName& InSourcePinName, const FEdGraphPinType& InSourcePinType, EEdGraphPinDirection InSourcePinDirection) const
{
    UEdNode_AGSGraphNode* EdNode = Cast<UEdNode_AGSGraphNode>(InTargetNode);
    switch (InSourcePinDirection) {
    case EGPD_Input:
        return EdNode->GetOutputPin();
    case EGPD_Output:
        return EdNode->GetInputPin();
    default:
        return nullptr;
    }
}

bool UAssetGraphSchema_AGSGraph::SupportsDropPinOnNode(UEdGraphNode* InTargetNode, const FEdGraphPinType& InSourcePinType, EEdGraphPinDirection InSourcePinDirection, FText& OutErrorMessage) const
{
    return Cast<UEdNode_AGSGraphNode>(InTargetNode) != nullptr;
}

bool UAssetGraphSchema_AGSGraph::IsCacheVisualizationOutOfDate(int32 InVisualizationCacheID) const
{
    return CurrentCacheRefreshID != InVisualizationCacheID;
}

int32 UAssetGraphSchema_AGSGraph::GetCurrentVisualizationCacheID() const
{
    return CurrentCacheRefreshID;
}

void UAssetGraphSchema_AGSGraph::ForceVisualizationCacheClear() const
{
    ++CurrentCacheRefreshID;
}

#undef LOCTEXT_NAMESPACE
