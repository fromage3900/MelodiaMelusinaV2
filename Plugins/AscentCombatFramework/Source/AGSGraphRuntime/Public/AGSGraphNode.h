// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Templates/SubclassOf.h"

#include "AGSGraphNode.generated.h"

UENUM()
enum class ENodeState : uint8 {
	/** Node is enabled. */
	Enabled,
	/** Node is disabled. */
	Disabled,
};

class UAGSGraph;
class UAGSGraphEdge;

/**
 * Represents a node within a generic graph system.
 * Nodes can be connected via edges and maintain references to their parent and child nodes.
 * They can be activated/deactivated and queried for state and structure.
 */
UCLASS(Blueprintable)
class AGSGRAPHRUNTIME_API UAGSGraphNode : public UObject {
	GENERATED_BODY()

public:
	/** Parent nodes that have directed edges pointing to this node */
	UPROPERTY(BlueprintReadOnly, Category = AGS)
	TArray<UAGSGraphNode*> ParentNodes;

	/** Child nodes that this node connects to */
	UPROPERTY(BlueprintReadOnly, Category = AGS)
	TArray<UAGSGraphNode*> ChildrenNodes;

	/** Edges connecting this node to its children */
	UPROPERTY(BlueprintReadOnly, Category = AGS)
	TMap<UAGSGraphNode*, UAGSGraphEdge*> Edges;

	/**
	 * Returns the edge that connects this node to the given child node.
	 *
	 * @param ChildNode The node connected as a child.
	 * @return The edge between this node and the child, or nullptr if not found.
	 */
	UFUNCTION(BlueprintCallable, Category = AGS)
	UAGSGraphEdge* GetEdge(UAGSGraphNode* ChildNode) const;

	/**
	 * Checks whether the node is a leaf (has no children).
	 *
	 * @return True if the node has no children.
	 */
	UFUNCTION(BlueprintCallable, Category = AGS)
	bool IsLeafNode() const;

	/**
	 * Checks whether the node is a root (has no parents).
	 *
	 * @return True if the node has no parents.
	 */
	UFUNCTION(BlueprintCallable, Category = AGS)
	bool IsRootNode() const;

	/**
	 * Checks whether the node is currently activated.
	 *
	 * @return True if the node is in the active state.
	 */
	UFUNCTION(BlueprintCallable, Category = AGS)
	bool IsNodeActivated() const;

	/**
	 * Returns the graph that owns this node.
	 *
	 * @return A pointer to the owning graph.
	 */
	UFUNCTION(BlueprintCallable, Category = AGS)
	UAGSGraph* GetGraph() const;

	/**
	 * Retrieves the description of this node. Can be overridden in Blueprints.
	 *
	 * @return A localized text describing the node.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = AGS)
	FText GetDescription() const;

	UFUNCTION(BlueprintPure, Category = AGS)
	FVector2D GetNodePosition() const { return NodePosition; }

	UFUNCTION(BlueprintPure, Category = AGS)
	FGuid GetNodeId() const { return NodeId; }

	void GenerateNewID();

	void SetNodePosition(FVector2D val) { NodePosition = val; }
	UWorld* GetWorld() const override;

	UPROPERTY()
	UAGSGraph* Graph;

	class APlayerController* GetPlayerController() const;

#if WITH_EDITORONLY_DATA
	// UPROPERTY(VisibleDefaultsOnly, Category = "AGSGraphNode_Editor")
	TSubclassOf<UAGSGraph> CompatibleGraphType;

	// UPROPERTY(EditDefaultsOnly, Category = "AGSGraphNode_Editor")
	FLinearColor BackgroundColor;

	// UPROPERTY(EditDefaultsOnly, Category = "AGSGraphNode_Editor")
	FText ContextMenuName;
#endif
	UAGSGraphNode();
	virtual ~UAGSGraphNode();

#if WITH_EDITOR
	virtual FLinearColor GetBackgroundColor() const;

	virtual bool CanCreateConnection(UAGSGraphNode* Other, FText& ErrorMessage);

	virtual FText GetNodeTitle() const;
	virtual FText GetParagraphTitle() const;

	virtual void InitializeNode();

	virtual void PostDuplicate(bool bDuplicateForPIE) override;


	void PostEditImport()
	{
		Super::PostEditImport();

		if (!NodeId.IsValid())
		{
			GenerateNewID();

		}
	}


	/*	void SetNodeTitle(const FText& NewTitle);*/
#endif

	friend class UAGSGraph;

protected:
	/** Activates this node. Override to define custom activation behavior. */
	virtual void ActivateNode();

	/** Deactivates this node. Override to define custom deactivation behavior. */
	virtual void DeactivateNode();

	/** Current state of the node (e.g., Enabled, Disabled, Active) */
	UPROPERTY(BlueprintReadOnly, Category = AGS)
	ENodeState NodeState = ENodeState::Disabled;

	/** Current state of the node (e.g., Enabled, Disabled, Active) */
	UPROPERTY(BlueprintReadOnly, Category = AGS)
	FVector2D NodePosition;

	/** Unique Node Identifier */
	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, SaveGame, Category = AGS)
	FGuid NodeId;

	void PostLoad()
	{
		Super::PostLoad();

		if (!NodeId.IsValid())
		{
			GenerateNewID();
		}
	}

};
