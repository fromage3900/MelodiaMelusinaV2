// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Game/ACFBaseDamageTypeCalculator.h"
#include "Game/ACFDamageCalculation.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFTypes.h"

#include "ACFGASDamageCalculator.generated.h"


struct FOnHitActionChances;

/**
 *
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFGASDamageCalculator : public UACFBaseDamageTypeCalculator {
    GENERATED_BODY()

public:
    virtual float CalculateFinalDamage_Implementation(const FACFDamageEvent& inDamageEvent, TArray<FAttributeData>& otherAffectedAttributes);

    virtual FGameplayTag EvaluateHitResponseAction_Implementation(const FACFDamageEvent& inDamageEvent, const TArray<FOnHitActionChances>& hitResponseActions);

    virtual bool IsCriticalDamage_Implementation(const FACFDamageEvent& inDamageEvent);

    float Internal_CalculateDamage(const FACFDamageEvent& inDamageEvent);

protected:
    /*Attribute used to reduce incoming damage when in Defense State*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    FGameplayAttribute BlockingDefenseAttribute;

    /*Attribute used to reduce incoming damage when in Defense State*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    FGameplayAttribute StaggerResistanceAttribute;

    /*Max Value Attribute used to reduce incoming damage when in Defense State*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    FGameplayAttribute MaxStaggerResistanceAttribute;

    /*Attribute used to reduce incoming damage when in Defense State*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    FGameplayAttribute CritChanceAttribute;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    FGameplayTag StaggerResistanceDataTag;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    FGameplayTag BlockDamagedDataTag;

private:
    bool EvaluetHitResponseAction(const FOnHitActionChances& action, const FACFDamageEvent& damageEvent);
};
