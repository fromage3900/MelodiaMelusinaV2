// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFSkillTreeConnectionsWidget.h"
#include "ANSNavWidget.h"
#include "CommonUserWidget.h"
#include "CoreMinimal.h"
#include <Components/CanvasPanel.h>
#include "ACFSkillTreeConnectionsWidget.h"

#include "ACFSkillTreeWidget.generated.h"

class UCanvasPanel;
class UACFSkillNodeWidget;
class UACFSkillTreeConnectionsWidget;

/**
 * Skill tree container widget: builds a tree of UACFSkillNodeWidget from graph root nodes,
 * places them on a canvas, and uses UACFSkillTreeConnectionsWidget to draw lines between nodes.
 */
UCLASS()
class ASCENTSKILLTREE_API UACFSkillTreeWidget : public UANSNavWidget {
    GENERATED_BODY()

public:
    /**
     * Builds the widget tree recursively from root logical nodes.
     * @param RootNodes The list of entry points for the skill tree
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void BuildFromNodes(const TArray<UAGSGraphNode*>& RootNodes);

    UFUNCTION(BlueprintPure, Category = ACF)
    UWidget* GetFirstSkillWidget() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    TMap<UACFBaseSkillNode*, UACFSkillNodeWidget*> GetNodeToWidgetMap() const { return NodeToWidgetMap; }

protected:
    /** Reference to the canvas panel used to place nodes */
    UPROPERTY(meta = (BindWidget), BlueprintReadOnly, Category = ACF)
    UCanvasPanel* CanvasPanel;

    /** Reference to the canvas panel used to place nodes */
    UPROPERTY(meta = (BindWidget), BlueprintReadOnly, Category = ACF)
    UACFSkillTreeConnectionsWidget* SkillsConnections;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FLinearColor ConnectionColor = FLinearColor::White;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float ConnectionThickness = 2.f;

    /** Base vertical offset for root node placement (Y axis) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FVector2D TreeStartPosition = FVector2D(100.0f, 100.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float BaseNodeDistance = 80.0f;

    /** List of connections to draw */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FVector2D ConnectionsLengthReductionFactor = FVector2D(2.f, 3.f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FVector2D SkillWidgetSize = FVector2D(84.f);

    /** Class used to instantiate skill node widgets */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TSubclassOf<UACFSkillNodeWidget> SkillNodeWidgetClass;

    void RecursivelyBuildNode(
        UACFBaseSkillNode* Node,
        const FVector2D& ParentPosition,
        float HorizontalSpacing,
        float VerticalSpacing,
        TSet<UACFBaseSkillNode*>& Visited);

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    TMap<UACFBaseSkillNode*, UACFSkillNodeWidget*> NodeToWidgetMap;
};
