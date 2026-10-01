// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFCombatBehaviorDataAsset.h"

UACFCombatBehaviorDataAsset::UACFCombatBehaviorDataAsset()
{
    FAICombatStateConfig melee = FAICombatStateConfig(EAICombatState::EMeleeCombat, 100.f, ELocomotionState::EWalk);
    UACFDistanceActionCondition* distanceCond = melee.GetDistanceBasedCondition();
    if (distanceCond) {
        distanceCond->SetContidionConfig(EConditionType::EBelow, 120.f);
    }
    CombatStatesConfig.Add(melee);

    FAICombatStateConfig studyTarget = FAICombatStateConfig(EAICombatState::EStudyTarget, 50.f, ELocomotionState::EWalk);
    UACFDistanceActionCondition* studyDistanceCond = studyTarget.GetDistanceBasedCondition();
    if (studyDistanceCond) {
        studyDistanceCond->SetContidionConfig(EConditionType::EEqual, 300.f, 100.f);
    }
    CombatStatesConfig.Add(studyTarget);

    FAICombatStateConfig chase = FAICombatStateConfig(EAICombatState::EChaseTarget, 100.f, ELocomotionState::EJog);
    UACFDistanceActionCondition* chaseCond = chase.GetDistanceBasedCondition();
    if (chaseCond) {
        chaseCond->SetContidionConfig(EConditionType::EBelow, 800.f);
    }
    CombatStatesConfig.Add(chase);

    FAICombatStateConfig ranged = FAICombatStateConfig(EAICombatState::ERangedCombat, 100.f, ELocomotionState::EWalk);
    UACFDistanceActionCondition* rangedCond = ranged.GetDistanceBasedCondition();
    if (rangedCond) {
        rangedCond->SetContidionConfig(EConditionType::EAbove, 500.f);
    }
    CombatStatesConfig.Add(ranged);
}
