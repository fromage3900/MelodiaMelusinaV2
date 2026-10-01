// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Game/ACFDamageCalculation.h"
#include "ACFBaseDamageTypeCalculator.generated.h"

/**
 * Base class for calculating custom damage logic.
 * Extend this class to implement specific damage formulas and critical hit rules.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFBaseDamageTypeCalculator : public UACFDamageCalculation
{
	GENERATED_BODY()


protected: 
	/*For every hitresponse you can define a multiplier to be applied to the final damage*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Hit Responses")
    TMap<FGameplayTag, float> HitResponseActionMultiplier;

	  /*Multiplier applied when an hit is Critical*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF| Critical Damage Config")
    float critMultiplier = 1.5f;

	 /*Actions to be triggered when the stagger resistance of the character is heavily damaged*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Hit Responses|Heavy Hit")
    FGameplayTag HeavyHitReaction;

    /*Heavy Hit Action will be triggered when StaggerResistanceStastistic will be below this value.
    To be intended as a negative scaling factor for your Stagger Resistance statistic: the higher, 
    the more difficult to trigger an Heavy Hit Reaction*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Hit Responses|Heavy Hit")
    float StaggerResistanceForHeavyHitMultiplier = 4.f;

        /*Random deviation in percentage added to final damage. % means that final damage will be randomized
    in the range -5% , +5%*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    float DefaultRandomDamageDeviationPercentage = 5.0f;

    /*Multiplier applied depending on the damaged zone of the receiver*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    TMap<EDamageZone, float> DamageZoneToDamageMultiplier;

      
    bool EvaluetHitResponseAction(const FOnHitActionChances& action, const FACFDamageEvent& damageEvent);

	virtual float Internal_CalculateDamage(const FACFDamageEvent& inDamageEvent);
};
