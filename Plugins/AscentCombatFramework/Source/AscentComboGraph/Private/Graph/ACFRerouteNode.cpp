#include "Graph/ACFRerouteNode.h"
#include "Graph/ACFComboGraph.h"
#include "ACFComboComponent.h"
#include "Logging.h"


UACFRerouteNode::UACFRerouteNode()
{
    NodeName = "Reroute Node";
    NodeParagraph = "...";

#if WITH_EDITOR
    // Assign a custom background color for the editor
    BackgroundColor = FLinearColor(0.2f, 0.6f, 1.0f, 1.0f); // Blue
#endif
}

void UACFRerouteNode::ActivateNode()
{
    UE_LOG(ACFLog, Log, TEXT("ACFRerouteNode::ActivateNode - Activated [%s]."), *NodeName);

    UACFComboGraph* CurrentGraph = Cast<UACFComboGraph>(Graph);
    // If this is a proxy node, forward activation to the target reroute node
    if (CurrentGraph && bIsProxyNode && TargetRerouteNode && TargetRerouteNode->GetOuter() == GetOuter()) {
        UE_LOG(ACFLog, Warning, TEXT("ACFRerouteNode::ActivateNode - Forwarding to TargetRerouteNode [%s]."), *TargetRerouteNode->NodeName);

        UACFComboComponent* comboComp = CurrentGraph->GetOwningComponent();
        if (comboComp) {
            pendingInput = comboComp->GetLastTagInput();
            comboComp->SendInputReceived(pendingInput);
            TargetRerouteNode->ActivateNode();
            return;
        }

    } else {
        UE_LOG(ACFLog, Error, TEXT("ACFRerouteNode::ActivateNode - TargetRerouteNode [%s] is not part of the same graph."), *TargetRerouteNode->NodeName);
    }

    // Perform default behavior for non-proxy nodes
    Super::ActivateNode();

    if (Graph) {
        UACFComboGraph* OwningGraph = Cast<UACFComboGraph>(Graph);
        if (OwningGraph) {
            const bool bTransitioned = OwningGraph->PerformTransition(pendingInput, OwningGraph->GetCharacterOwner());
            if (!bTransitioned) {
                UE_LOG(ACFLog, Warning, TEXT("ACFRerouteNode::ActivateNode - No valid transition from [%s]."), *NodeName);
            } else {
                UE_LOG(ACFLog, Log, TEXT("ACFRerouteNode::ActivateNode - Transition succeeded from [%s]."), *NodeName);
            }
        }
    }
}

#if WITH_EDITOR

FText UACFRerouteNode::GetNodeTitle() const
{
    // If this is a proxy node, show the reference target in parentheses
    if (TargetRerouteNode) {
        return FText::Format(FText::FromString("{0} (Proxy to: {1})"),
            FText::FromString(NodeName.IsEmpty() ? TEXT("Reroute Node") : NodeName),
            FText::FromString(TargetRerouteNode->NodeName.IsEmpty() ? TEXT("Reroute Node") : TargetRerouteNode->NodeName));
    }

    // Otherwise, just show the node name
    return FText::FromString(NodeName.IsEmpty() ? TEXT("Reroute Node") : NodeName);
}

FText UACFRerouteNode::GetParagraphTitle() const
{
    return FText::FromString(NodeParagraph.IsEmpty() ? TEXT("No additional details.") : NodeParagraph);
}

void UACFRerouteNode::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
    Super::PostEditChangeProperty(PropertyChangedEvent);

    if (PropertyChangedEvent.Property && PropertyChangedEvent.Property->GetFName() == GET_MEMBER_NAME_CHECKED(UACFRerouteNode, bIsProxyNode)) {
        // Clear TargetRerouteNode if this is no longer a proxy node
        if (!bIsProxyNode) {
            TargetRerouteNode = nullptr;
        }
    }
}

#endif
