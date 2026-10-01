// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AGSGraphNode.h"
#include "CoreMinimal.h"
#include "ACFBaseComboNode.h"
#include <../../../../../../../Source/Runtime/GameplayTags/Classes/GameplayTagContainer.h>
#include "ACFRerouteNode.generated.h"

/**
 * Reroute Node - Dummy node for branching transitions
 */
UCLASS()
class ASCENTCOMBOGRAPH_API UACFRerouteNode : public UACFBaseComboNode
{
    GENERATED_BODY()

public:
    UACFRerouteNode();

    // Override ActivateNode to handle rerouting logic
    virtual void ActivateNode() override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combo Graph")
    FString NodeName = "Reroute Node";

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combo Graph")
    FString NodeParagraph = "";

    // The target reroute node that this node will proxy to, allowing the flow to redirect to another reroute node.
    // This property is only valid and editable if the node is marked as a Proxy Node (bIsProxyNode = true).
    // Use this to define the rerouting behavior for branching transitions in the Combo Graph.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combo Graph", meta = (EditCondition = "bIsProxyNode"))
    TObjectPtr<UACFRerouteNode> TargetRerouteNode;

    // Determines whether this reroute node acts as a proxy, redirecting the flow to a specified Target Reroute Node.
    // If true, this node serves as a reference to another reroute node (TargetRerouteNode), enabling branching transitions. Adding further transitions currently not supported if true.
    // If false, this node behaves as a standard reroute node with no proxy behavior. You can add further transitions here
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combo Graph")
    bool bIsProxyNode = false;

    UPROPERTY()
    FGameplayTag pendingInput;

#if WITH_EDITOR
    virtual FText GetNodeTitle() const override;
    virtual FText GetParagraphTitle() const override;
    virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif
};
