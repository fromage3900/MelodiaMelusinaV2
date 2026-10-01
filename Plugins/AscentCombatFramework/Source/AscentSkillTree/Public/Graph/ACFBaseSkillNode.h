// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFBaseSkill.h"
#include "ACFSkillTypes.h"
#include "AGSGraphNode.h"
#include "CoreMinimal.h"

#include "ACFBaseSkillNode.generated.h"

/**
 * Base Class for all Skill Tree Graph Nodes
 */
UCLASS(abstract)
class ASCENTSKILLTREE_API UACFBaseSkillNode : public UAGSGraphNode {
    GENERATED_BODY()

protected:

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    TObjectPtr<UACFBaseSkill> Skill;

public:

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFBaseSkill* GetSkill() const { return Skill; }

    UFUNCTION(BlueprintPure, Category = ACY)
    int32 GetMaxLevel() const { return Skill ? Skill->MaxLevel : 1; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FSkillConfig GetSkillToGrant() const { return Skill ? Skill->SkillToGrant : FSkillConfig(); }

    UFUNCTION(BlueprintPure, Category = ACF)
    FSkillUIConfig GetUISkillInfo() const { return Skill ? Skill->UISkillInfo : FSkillUIConfig(); }

#if WITH_EDITOR
    virtual FText GetNodeTitle() const override;
    virtual FText GetParagraphTitle() const override;

#endif
};
