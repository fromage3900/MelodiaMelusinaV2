// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFActionsFunctionLibrary.h"
#include "ACFActionTypes.h"
#include "ARSFunctionLibrary.h"
#include "ARSTypes.h"
#include "ActiveGameplayEffectHandle.h"
#include "GameplayTagsManager.h"
#include "Logging.h"
#include <AbilitySystemComponent.h>

bool UACFActionsFunctionLibrary::IsValidMovesetActionsTag(FGameplayTag TagToCheck)
{
    const FGameplayTag root = GetMovesetActionsTagRoot();
    return UGameplayTagsManager::Get().RequestGameplayTagChildren(root).HasTag(TagToCheck);
}

FGameplayTag UACFActionsFunctionLibrary::GetDefaultActionsState()
{
    // Hardcoded default actions state tag,
    //  in this case hardcoding is better as we can enforce a category and  and filter in the editor
    return UGameplayTagsManager::Get().RequestGameplayTag(FName("Actions"));
}

FGameplayTag UACFActionsFunctionLibrary::GetMovesetActionsTagRoot()
{
    // Hardcoded root tag for all moveset-related actions
    //  in this case hardcoding is better as we can enforce a category and  and filter in the editor

    return UGameplayTagsManager::Get().RequestGameplayTag(FName("Moveset"));
}