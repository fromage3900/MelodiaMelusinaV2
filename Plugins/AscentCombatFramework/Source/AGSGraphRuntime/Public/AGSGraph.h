// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AGSGraphEdge.h"
#include "AGSGraphNode.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include <GameFramework/PlayerController.h>

#include "AGSGraph.generated.h"

class UEdGraph;
class UAGSGraphNode;

/**
 * A generic, blueprintable class to represent a graph
 */
UCLASS(Blueprintable)
class AGSGRAPHRUNTIME_API UAGSGraph : public UObject {
    GENERATED_BODY()

public:
    /* Returns all nodes in the graph */
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    const TArray<UAGSGraphNode*> GetAllNodes() const
    {
        return AllNodes;
    }

    /* Returns the currently active nodes in the graph */
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    const TArray<UAGSGraphNode*> GetActiveNodes() const
    {
        return ActivedNodes;
    }

    /* Prints a textual representation of the graph to console and/or screen */
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    void Print(bool ToConsole = true, bool ToScreen = true);

    /* Activates the given node. Returns true if successful */
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    virtual bool ActivateNode(class UAGSGraphNode* node);

    /* Deactivates the given node. Returns true if successful */
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    virtual bool DeactivateNode(class UAGSGraphNode* node);

    /* Deactivates all currently active nodes in the graph */
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    void DeactivateAllNodes();

    /* Checks if the provided node is active*/
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    bool IsNodeActive(class UAGSGraphNode* node);

    /* Returns the total number of levels (layers) in the graph */
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    int32 GetLevelNum() const;

    /* Fills the given array with all nodes at the specified level */
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    void GetNodesByLevel(int32 Level, TArray<UAGSGraphNode*>& Nodes);

    /* Clears the graph, removing all nodes and connections */
    void ClearGraph();

    /* Returns the player controller associated with this graph instance */
    UFUNCTION(BlueprintPure, Category = "AGSGraph")
    class APlayerController* GetPlayerController() const
    {
        return controller;
    }

    /**
     * Traverses the outer chain to find the actor that owns this graph instance.
     * Works for dialogue graphs (outer chain: Graph → Dialogue → ParticipantComponent → NPC Actor)
     * and for any graph instanced inside an actor or actor component.
     * Returns nullptr if no actor is found in the chain.
     */
    UFUNCTION(BlueprintPure, Category = "AGSGraph")
    AActor* GetOwnerActor() const
    {
        UObject* Outer = GetOuter();
        while (Outer)
        {
            if (AActor* Actor = Cast<AActor>(Outer))
            {
                return Actor;
            }
            if (UActorComponent* Comp = Cast<UActorComponent>(Outer))
            {
                return Comp->GetOwner();
            }
            Outer = Outer->GetOuter();
        }
        return nullptr;
    }

    /* Root nodes of the graph (no incoming connections) */
    UPROPERTY(BlueprintReadOnly, Category = "AGSGraph")
    TArray<UAGSGraphNode*> RootNodes;

    /* All nodes that belong to this graph */
    UPROPERTY(BlueprintReadOnly, Category = "AGSGraph")
    TArray<UAGSGraphNode*> AllNodes;

    // Save, Load, Replication
    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    FAGSGraphRecord CreateGraphRecord();

    UFUNCTION(BlueprintCallable, Category = "AGSGraph")
    void SynchWithGraphRecord(const FAGSGraphRecord& graphRecord);

    UFUNCTION(BlueprintPure, Category = "AGSGraph")
    UAGSGraphNode* GetNodeById(const FGuid nodeId) const;


#if WITH_EDITORONLY_DATA
    UPROPERTY()
    TObjectPtr<UEdGraph> EdGraph;

    UPROPERTY()
    bool bCanRenameNode = false;
#endif

protected:
    TObjectPtr<APlayerController> controller;

    /** Unique Node Identifier */
    UPROPERTY(BlueprintReadOnly, VisibleAnywhere, Category = AGS)
    FGuid GraphId;

#if WITH_EDITOR
    virtual void PreSave(FObjectPreSaveContext SaveContext) override;

    virtual void PostDuplicate(bool bDuplicateForPIE) override
    {
        Super::PostDuplicate(bDuplicateForPIE);
        GraphId = FGuid::NewGuid();
    }
#endif

public:
    UAGSGraph();
    virtual ~UAGSGraph();

    // UPROPERTY(EditDefaultsOnly, Category = "AGSGraph")
    FString Name;

    // UPROPERTY(EditDefaultsOnly, Category = "AGSGraph")
    TSubclassOf<UAGSGraphNode> NodeType;

    // UPROPERTY(EditDefaultsOnly, Category = "AGSGraph")
    TSubclassOf<UAGSGraphEdge> EdgeType;

    UWorld* GetWorld() const override { return controller ? controller->GetWorld() : nullptr; }

    //	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AGSGraph")
    bool bEdgeEnabled;

    bool bAllowCycles = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AGSGraph")
    FGameplayTagContainer GraphTags;

    UPROPERTY()
    TArray<UAGSGraphNode*> ActivedNodes;
};
