// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ANSNavWidget.h"
#include "CoreMinimal.h"


#include "ACFSkillNodeWidget.generated.h"


class UACFBaseSkillNode;

/**
 * Single skill node widget in the skill tree. Implement SetupWithNode in Blueprint to display
 * the skill name, icon, state (locked/unlocked), and handle selection.
 */
UCLASS()
class ASCENTSKILLTREE_API UACFSkillNodeWidget : public UANSNavWidget {
    GENERATED_BODY()

public:
    /** Called to initialize the widget with the logical skill node; implement in Blueprint. */
    UFUNCTION(BlueprintImplementableEvent, Category = ACF)
    void SetupWithNode(UACFBaseSkillNode* skillNode);
};
