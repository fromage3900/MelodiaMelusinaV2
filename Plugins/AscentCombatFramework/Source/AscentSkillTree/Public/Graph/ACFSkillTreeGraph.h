// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.
#pragma once
#include "AGSGraph.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>
#include "ACFSkillTreeGraph.generated.h"

class UACFBaseSkillNode;

/**
 * A specialized graph that represents a skill tree structure.
 * Supports nodes as skills identified by unique GUIDs.
 */
UCLASS()
class ASCENTSKILLTREE_API UACFSkillTreeGraph : public UAGSGraph {
    GENERATED_BODY()

public:
    UACFSkillTreeGraph();

    /**
     * Returns the gameplay tag associated with this skill tree.
     *
     * @return The skill tree tag.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetSkillTreeTag() const { return SkillTreeTag; }

    /**
     * Returns the UI Display name associated with this skill tree.
     *
     * @return The UI Display name.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FText GetSkillTreeName() const { return SkillTreeName; }

    /**
     * Retrieves a skill node within the graph by its unique GUID.
     *
     * @param SkillId The GUID identifying the skill.
     * @return A pointer to the matching skill node, or nullptr if not found.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UACFBaseSkillNode* GetSkillNodeById(const FGuid& SkillId) const;

    /**
     * Activates the skill node identified by the given GUID.
     *
     * @param SkillId The GUID of the skill to activate.
     * @return True if the skill was successfully activated.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool ActivateSkillNode(const FGuid& SkillId);

    /**
     * Checks if the skill node identified by the given GUID is active.
     *
     * @param SkillId The GUID of the skill to check.
     * @return True if the skill node is active.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool IsSkillNodeActive(const FGuid& SkillId);

    /**
     * Checks if all parent nodes of the specified skill are active.
     *
     * @param SkillId The GUID of the skill to check.
     * @return True if all parent nodes are active.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool AreAllParentsActive(const FGuid& SkillId) const;

    // They can be different instances, but they are the same graph
    FORCEINLINE bool operator==(const UACFSkillTreeGraph* Other) const { return this->GetClass() == Other->GetClass(); }
    FORCEINLINE bool operator!=(const UACFSkillTreeGraph* Other) const { return this->GetClass() != Other->GetClass(); }

    bool ActivateNode(class UAGSGraphNode* Node);

protected:
    /**
     * Tag identifying the skill tree this object belongs to.
     */
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACF)
    FGameplayTag SkillTreeTag;

    /**
     * Display name of the skill tree, shown in UI and editor.
     */
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACF)
    FText SkillTreeName;

    UWorld* GetWorld() const override { return controller ? controller->GetWorld() : nullptr; }
};
