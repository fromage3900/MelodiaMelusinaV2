// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "ACFAITypes.h"
#include "Game/ACFTypes.h"
#include "Data/ACFBaseCombatBehaviorDataAsset.h"

#include "ACFCombatBehaviorDataAsset.generated.h"

/**
 * Data Asset describing how this AI should behave in Combat
 */
UCLASS()
class AIFRAMEWORK_API UACFCombatBehaviorDataAsset : public UACFBaseCombatBehaviorDataAsset {
    GENERATED_BODY()

public:
    UACFCombatBehaviorDataAsset();

    /* If this ai needs an equipped weapon to start fighting*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    bool bNeedsWeapon = true;

    /*The default combat behavior (melee/ranged) for this AI. Could change during combat if multiple
    behaviors have been defined in Allowed Behaviors*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    ECombatBehaviorType DefaultCombatBehaviorType;

    /*The default combat state  for this AI, triggered once no other states are available*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    EAICombatState DefaultCombatState = EAICombatState::EMeleeCombat;

    /*Configuration of each Combat State*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    TArray<FAICombatStateConfig> CombatStatesConfig;

    /*The actions that should be performed by the AI for every combat state */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    TMap<EAICombatState, FActionsChances> ActionByCombatState;

};
