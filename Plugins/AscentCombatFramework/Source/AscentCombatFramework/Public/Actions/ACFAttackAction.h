// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actions/ACFComboAction.h"
#include "CoreMinimal.h"
#include "Game/ACFTypes.h"
#include "RootMotionModifier.h"

#include "ACFAttackAction.generated.h"

/**
 * Executes a melee attack as part of an ability-based combo system.
 * Handles damage triggering, tracing, and optional warping toward the target.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFAttackAction : public UACFComboAction {
    GENERATED_BODY()

public:
    UACFAttackAction();

protected:

    /** Enables evaluation of warp conditions for this attack */
    UPROPERTY(EditDefaultsOnly, Category = "ACF| Warp")
    bool bCheckWarpConditions = true;

    /** Maximum distance allowed for warping to the target */
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bCheckWarpConditions), Category = "ACF| Warp")
    float maxWarpDistance = 500.f;

    /** Minimum distance required to trigger warp */
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bCheckWarpConditions), Category = "ACF| Warp")
    float minWarpDistance = 10.f;

    /** Maximum allowed angle for warp alignment toward the target */
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bCheckWarpConditions), Category = "ACF| Warp")
    float maxWarpAngle = 270.f;

    /** Strength of the magnetic pull effect during warp updates */
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bContinuousUpdate), Category = "ACF| Warp")
    float WarpMagnetismStrength = 1.0f;

    virtual void OnActionStarted_Implementation() override;

    virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData);

    void SetupAttack();

    virtual void OnActionEnded_Implementation() override;

    virtual FTransform GetWarpTransform_Implementation() override;

    virtual USceneComponent* GetWarpTargetComponent_Implementation() override;

    bool TryGetTransform(FTransform& outTranform) const;

private:
    FTransform warpTrans;
    TObjectPtr<USceneComponent> currentTargetComp;

    EMontageReproductionType storedReproType;
};
