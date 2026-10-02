// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actions/ACFActionAbility.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageType.h"

#include "ACFAdvancedHitAction.generated.h"

/**
 * Advanced hit reaction action that plays a different montage section based on hit direction and bone impact.
 * Supports directional logic and optional warp distance toward the attacker.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFAdvancedHitAction : public UACFActionAbility {
    GENERATED_BODY()

    UACFAdvancedHitAction();

protected:
    /** Maps hit directions to montage section names */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ACF)
    TMap<EHitDirection, FName> HitDirectionToMontageSectionMap;

    /** List of bone names and their associated front-facing montage sections */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ACF)
    TArray<FBoneSections> FrontDetailsSectionByBoneNames;

    /** Distance to warp toward the attacker when hit, used if bSnapToTarget is true */
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bSnapToTarget), Category = "ACF| Warp")
    float hitWarpDistance = 200.f;

    virtual void OnActionStarted_Implementation() override;
    virtual void OnActionEnded_Implementation() override;

    virtual FTransform GetWarpTransform_Implementation() override;
    virtual FName GetMontageSectionName_Implementation() override;

private:
    FName GetMontageSectionFromHitDirectionSafe(const EHitDirection hitDir) const;

    FName GetMontageSectionFromFront(const FHitResult& damageReceived) const;
};
