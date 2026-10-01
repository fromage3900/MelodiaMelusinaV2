// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AGSGraphEdge.h"

#include "ACFSkillTransition.generated.h"


/**
 * Represents a directional connection (edge) between two skill nodes in the skill tree.
 * Can be extended to store conditions or cost for unlocking transitions.
 */
UCLASS()
class ASCENTSKILLTREE_API UACFSkillTransition : public UAGSGraphEdge {
    GENERATED_BODY()

};
