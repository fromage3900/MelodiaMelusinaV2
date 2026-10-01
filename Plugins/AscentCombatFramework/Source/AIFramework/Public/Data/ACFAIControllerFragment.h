// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCCTypes.h"
#include "CoreMinimal.h"
#include "Data/ACFCharacterFragment.h"
#include <GameplayTagContainer.h>

#include "ACFAIControllerFragment.generated.h"

class UBehaviorTree;

/**
 * Character fragment that overrides AI controller settings directly from the
 * UACFCharacterDataAsset. Add it to UACFCharacterDataAsset::Fragments to configure
 * per-character AI behaviour without subclassing AACFAIController.
 *
 * Each group of settings has its own override toggle so you can mix-and-match only
 * the properties you want to change, leaving the rest at controller defaults.
 */
UCLASS(Blueprintable, EditInlineNew, DefaultToInstanced)
class AIFRAMEWORK_API UACFAIControllerFragment : public UACFCharacterFragment
{
    GENERATED_BODY()

public:
    // -----------------------------------------------------------------------
    // Behavior Tree
    // -----------------------------------------------------------------------

    // When true, replaces the behavior tree asset on the AI controller with BehaviorTree below.
    // The running tree is stopped and restarted with the new asset.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI|BehaviorTree")
    bool bOverrideBehaviorTree = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideBehaviorTree", EditConditionHides), Category = "ACF|AI|BehaviorTree")
    TObjectPtr<UBehaviorTree> BehaviorTree;

    // -----------------------------------------------------------------------
    // AI State
    // -----------------------------------------------------------------------

    // When true, overrides the default AI state (e.g. Idle, Patrol, Combat).
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI|State")
    bool bOverrideDefaultState = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideDefaultState", EditConditionHides, Categories = "AIState"), Category = "ACF|AI|State")
    FGameplayTag DefaultState;

    // When true, replaces the entire locomotion-state-per-AI-state map.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI|State")
    bool bOverrideLocomotionStates = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideLocomotionStates", EditConditionHides), Category = "ACF|AI|State")
    TMap<FGameplayTag, ELocomotionState> LocomotionStateByAIState;

    // -----------------------------------------------------------------------
    // Home
    // -----------------------------------------------------------------------

    // When true, overrides the home-distance settings on the AI controller.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI|Home")
    bool bOverrideHomeSettings = false;

    // Whether the AI should return to home when outside MaxDistanceFromHome
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideHomeSettings", EditConditionHides), Category = "ACF|AI|Home")
    bool bBoundToHome = true;

    // Maximum distance from home before the AI turns back
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideHomeSettings", EditConditionHides, ClampMin = "0.0", ForceUnits = "cm"), Category = "ACF|AI|Home")
    float MaxDistanceFromHome = 8500.f;

    // -----------------------------------------------------------------------
    // Teleport to Lead
    // -----------------------------------------------------------------------

    // When true, overrides teleport-to-lead settings on the AI controller.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI|Teleport")
    bool bOverrideTeleportSettings = false;

    // Whether the AI should teleport near its lead when too far away
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideTeleportSettings", EditConditionHides), Category = "ACF|AI|Teleport")
    bool bTeleportToLead = false;

    // Distance that triggers the teleport
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideTeleportSettings", EditConditionHides, ClampMin = "0.0", ForceUnits = "cm"), Category = "ACF|AI|Teleport")
    float TeleportToLeadTriggerDistance = 8500.f;

    // Spawn radius around the lead position after teleporting
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideTeleportSettings", EditConditionHides, ClampMin = "0.0", ForceUnits = "cm"), Category = "ACF|AI|Teleport")
    float TeleportNearLeadRadius = 2500.f;

    // -----------------------------------------------------------------------
    // Combat
    // -----------------------------------------------------------------------

    // When true, overrides combat-related settings on the AI controller.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI|Combat")
    bool bOverrideCombatSettings = false;

    // Distance at which the AI stops pursuing and drops its current target
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideCombatSettings", EditConditionHides, ClampMin = "0.0", ForceUnits = "cm"), Category = "ACF|AI|Combat")
    float LoseTargetDistance = 3500.f;

    // Whether this AI automatically attacks enemies it perceives
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideCombatSettings", EditConditionHides), Category = "ACF|AI|Combat")
    bool bIsAggressive = true;

    // Whether this AI reacts (adds threat, switches target) when it takes damage
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bOverrideCombatSettings", EditConditionHides), Category = "ACF|AI|Combat")
    bool bShouldReactOnHit = true;

    virtual void ApplyFragment_Implementation(APawn* pawnOwner) override;
};
