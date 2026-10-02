// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "CASAnimCondition.h"
#include "CASAnimSlaveComponent.h"
#include <GameFramework/Character.h>
#include "CASTypes.h"
#include <GameplayTagsManager.h>
#include "ACFCombinedAnimSlaveComponent.h"

bool UCASAnimCondition::Internal_VerifyCondition(UACFCombinedAnimSlaveComponent* ownerComp, const FCombinedAnimConfig& contextualAnim, const ACharacter* animMaster)
{
    ownerCompoment = ownerComp;
    if (UGameplayTagsManager::Get().RequestGameplayTagChildren(AnimRootTag).HasTag(contextualAnim.AnimTag) || AnimRootTag.MatchesTagExact(contextualAnim.AnimTag)) {
        return VerifyCondition(contextualAnim, animMaster);
    }
    return true;
};

bool UCASAnimCondition::VerifyCondition_Implementation(const struct FCombinedAnimConfig& contextAnim, const ACharacter* animMaster)
{
    return true; // Default implementation, can be overridden in derived classes                                                    
}

UWorld* UCASAnimCondition::GetWorld() const
{
    
    return ownerCompoment ? ownerCompoment->GetWorld() : nullptr;
}

bool UCASORCondition::VerifyCondition_Implementation(const FCombinedAnimConfig& animTag, const class ACharacter* animMaster)
{
    for (auto& cond : OrConditions) {
        if (cond->Internal_VerifyCondition(ownerCompoment, animTag, animMaster)) {
            return true;
        }
    }
    return false;
}
