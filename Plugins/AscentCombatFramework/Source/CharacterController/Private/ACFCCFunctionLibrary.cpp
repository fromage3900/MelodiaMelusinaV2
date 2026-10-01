// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFCCFunctionLibrary.h"
#include "ACFCCTypes.h"
#include <GameplayTagContainer.h>
#include <GameplayTagsManager.h>

FGameplayTag UACFCCFunctionLibrary::GetMovesetTypeTagRoot()
{
    return UGameplayTagsManager::Get().RequestGameplayTag(FName("Moveset"));
}

FGameplayTag UACFCCFunctionLibrary::GetAnimationOverlayTagRoot()
{
    return UGameplayTagsManager::Get().RequestGameplayTag(FName("Moveset"));
}

bool UACFCCFunctionLibrary::IsValidMovesetTypeTag(FGameplayTag TagToCheck)
{
    const FGameplayTag root = GetMovesetTypeTagRoot();
    return UGameplayTagsManager::Get().RequestGameplayTagChildren(root).HasTag(TagToCheck);
}

bool UACFCCFunctionLibrary::IsValidAnimOverlayTag(FGameplayTag TagToCheck)
{
    const FGameplayTag root = GetAnimationOverlayTagRoot();
    return UGameplayTagsManager::Get().RequestGameplayTagChildren(root).HasTag(TagToCheck);
}

EACFDirection UACFCCFunctionLibrary::GetDirectionFromAngle(const float angle)
{
    if (angle >= -45 && angle <= 45) {
        return EACFDirection::Front;
    } else if (angle >= 135 || angle <= -135) {
        return EACFDirection::Back;
    } else if (angle >= 45 && angle <= 135) {
        return EACFDirection::Right;
    } else if (angle >= -135 && angle <= -45) {
        return EACFDirection::Left;
    }

    return EACFDirection::Front;
}

EACFDirection UACFCCFunctionLibrary::GetOppositeDirection(EACFDirection direction)
{
    switch (direction) {
    case EACFDirection::Front:
        return EACFDirection::Back;
    case EACFDirection::Back:
        return EACFDirection::Front;
    case EACFDirection::Left:
        return EACFDirection::Right;
    case EACFDirection::Right:
        return EACFDirection::Left;
    }

    return EACFDirection::Front;
}

EACFDirection UACFCCFunctionLibrary::GetOppositeDirectionFromAngle(float angle)
{
    const EACFDirection dir = GetDirectionFromAngle(angle);
    return GetOppositeDirection(dir);
}
