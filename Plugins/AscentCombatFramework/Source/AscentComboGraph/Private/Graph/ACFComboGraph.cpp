// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Graph/ACFComboGraph.h"

#include "ACFComboComponent.h"
#include "Actions/ACFActionAbility.h"
#include "Engine/Engine.h"
#include "Graph/ACFBaseComboNode.h"
#include "Graph/ACFComboNode.h"
#include "Graph/ACFRerouteNode.h"
#include "Graph/ACFStartComboNode.h"
#include "Graph/ACFTransition.h"

bool UACFComboGraph::ActivateNode(class UAGSGraphNode* node)
{
    return Super::ActivateNode(node);
}

UACFComboGraph::UACFComboGraph()
{
    NodeType = UACFBaseComboNode::StaticClass();
    EdgeType = UACFTransition::StaticClass();
    Enabled = EComboState::NotStarted;
    bIsAI = false;
}

void UACFComboGraph::StartCombo(const FGameplayTag& inStartAction)
{
    DeactivateAllNodes();
    triggeringAction = inStartAction;
  
    for (UAGSGraphNode* root : RootNodes) {
        UACFStartComboNode* startNode = Cast<UACFStartComboNode>(root);
        if (startNode && startNode->GetTriggeringAction() == inStartAction) {
            Enabled = EComboState::Started;
            ActivateNode(startNode);
            return;
        }
    }
}

void UACFComboGraph::StopCombo()
{
    DeactivateAllNodes();
    Enabled = EComboState::NotStarted;
}



bool UACFComboGraph::PerformTransition(const FGameplayTag& inputTag, const ACharacter* Character)
{
    for (auto node : GetActiveNodes()) {
        UACFBaseComboNode* comboNode = Cast<UACFBaseComboNode>(node);
        if (comboNode) {
            if (HandleRerouteNode(comboNode)) {
                return true;
            }

            // Collect and sort edges
            TArray<TPair<UAGSGraphNode*, UACFTransition*>> SortedTransitions = GetSortedTransitions(comboNode);
            // Check if AI and delegate logic
            if (IsAI()) {
                if (HandleAITransitions(SortedTransitions, inputTag, Character, comboNode)) {
                    return true;
                }
            } else {
                if (HandlePlayerTransitions(SortedTransitions, inputTag, Character, comboNode)) {
                    return true;
                }
            }
        }
    }
    StopCombo(); // Gracefully terminate the combo if no valid transitions are found
    return false; // No valid transition found
}

bool UACFComboGraph::HandleRerouteNode(UACFBaseComboNode* comboNode)
{
    UACFRerouteNode* rerouteNode = Cast<UACFRerouteNode>(comboNode);
    if (rerouteNode) {
        if (rerouteNode->TargetRerouteNode && rerouteNode->bIsProxyNode) {
            DeactivateNode(rerouteNode);
            ActivateNode(rerouteNode->TargetRerouteNode);
            return true;
        }
    }

    return false;
}

TArray<TPair<UAGSGraphNode*, UACFTransition*>> UACFComboGraph::GetSortedTransitions(UACFBaseComboNode* comboNode)
{
    TArray<TPair<UAGSGraphNode*, UACFTransition*>> SortedTransitions;

    for (auto edge : comboNode->Edges) {
        UAGSGraphNode* TargetNode = Cast<UAGSGraphNode>(edge.Key);
        UACFTransition* Transition = Cast<UACFTransition>(edge.Value);

        if (TargetNode && Transition) {
            SortedTransitions.Add(TPair<UAGSGraphNode*, UACFTransition*>(TargetNode, Transition));
        }
    }

    SortedTransitions.Sort([](const TPair<UAGSGraphNode*, UACFTransition*>& A, const TPair<UAGSGraphNode*, UACFTransition*>& B) {
        if (A.Value->bUseWeightedPriorities && B.Value->bUseWeightedPriorities) {
            float TotalWeight = A.Value->Weight + B.Value->Weight;
            float ProbabilityA = A.Value->Weight / TotalWeight;
            return FMath::FRand() < ProbabilityA;
        } else if (A.Value->bUseWeightedPriorities) {
            return false;
        } else if (B.Value->bUseWeightedPriorities) {
            return true;
        }
        return A.Value->Priority > B.Value->Priority;
    });

    // Filter sorted transitions by valid pair.key
    SortedTransitions = SortedTransitions.FilterByPredicate([](const TPair<UAGSGraphNode*, UACFTransition*>& Pair) {
        return Pair.Key != nullptr;
    });

    return SortedTransitions;
}

bool UACFComboGraph::HandleAITransitions(
    const TArray<TPair<UAGSGraphNode*, UACFTransition*>>& Transitions,
    const FGameplayTag& currentInput,
    const ACharacter* Character,
    UACFBaseComboNode* CurrentNode)
{

    // Evaluate transitions based on the simulated input
    for (const auto& Pair : Transitions) {
        UAGSGraphNode* TargetNode = Pair.Key;
        UACFTransition* Transition = Pair.Value;

        if (Transition->GetTransitionInputTag() == currentInput && Transition->AreConditionsMet(Character)) {
            UACFBaseComboNode* newNode = Cast<UACFBaseComboNode>(TargetNode);
            ensure(newNode);

            DeactivateNode(CurrentNode);
            ActivateNode(newNode);

            return true;
        }
    }

    return false; // No valid transition found
}

void UACFComboGraph::SetIsAI(bool bInIsAI)
{
    bIsAI = bInIsAI;
}

bool UACFComboGraph::IsAI() const
{
    return bIsAI;
}

TArray<FGameplayTag> UACFComboGraph::GetValidInputsForCurrentNode() const
{
    TArray<FGameplayTag> ValidInputs;

    for (UAGSGraphNode* Node : GetActiveNodes()) {
        UACFBaseComboNode* ComboNode = Cast<UACFBaseComboNode>(Node);
        if (ComboNode) {
            for (const auto& Edge : ComboNode->Edges) {
                UACFTransition* Transition = Cast<UACFTransition>(Edge.Value);
                if (Transition ) {
                    ValidInputs.AddUnique(Transition->GetTransitionInputTag());
                }
            }
        }
    }

    return ValidInputs;
}

bool UACFComboGraph::HandlePlayerTransitions(
    const TArray<TPair<UAGSGraphNode*, UACFTransition*>>& Transitions,
    const FGameplayTag& currentInput,
    const ACharacter* Character,
    UACFBaseComboNode* CurrentNode)
{
    for (const auto& Pair : Transitions) {
        UAGSGraphNode* TargetNode = Pair.Key;
        UACFTransition* Transition = Pair.Value;

        if (Transition->GetTransitionInputTag() == currentInput && Transition->AreConditionsMet(Character)) {
            UACFBaseComboNode* newNode = Cast<UACFBaseComboNode>(TargetNode);
            ensure(newNode);

            DeactivateNode(CurrentNode);
            ActivateNode(newNode);

            return true;
        }
    }
    return false;
}

FGameplayTag UACFComboGraph::GetTriggeringAction() const
{
    return triggeringAction;
}

UACFComboNode* UACFComboGraph::GetCurrentComboNode() const
{
    if (IsActive() && GetActiveNodes().IsValidIndex(0) && IsValid(GetActiveNodes()[0])) {
        // only one combo anim can be reproduced at time
        return Cast<UACFComboNode>(GetActiveNodes()[0]);
    }
    return nullptr;
}

UACFComboComponent* UACFComboGraph::GetOwningComponent() const
{
    return characterOwner ? characterOwner->FindComponentByClass<UACFComboComponent>() : nullptr;
}

UAnimMontage* UACFComboGraph::GetCurrentComboMontage() const
{
    UACFComboNode* currentNode = GetCurrentComboNode();
    if (currentNode) {
        return currentNode->GetMontage();
    }
    return nullptr;
}

bool UACFComboGraph::GetCurrentComboModifier(FAttributesSetModifier& outModifier) const
{
    UACFComboNode* currentNode = GetCurrentComboNode();
    if (currentNode) {
        outModifier = currentNode->GetComboNodeModifier();
        return true;
    }
    return false;
}
