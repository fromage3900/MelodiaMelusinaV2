// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "ACFSkillTypes.h"

#include "ACFBaseSkill.generated.h"

/**
 *
 */
UCLASS(Blueprintable, BlueprintType, DefaultToInstanced, EditInlineNew)
class ASCENTSKILLTREE_API UACFBaseSkill : public UObject {
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF", meta = (ClampMin = 1))
    int32 MaxLevel = 1;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF")
    FSkillConfig SkillToGrant;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF")
    FSkillUIConfig UISkillInfo;
};
