// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFDamageType.h"
#include "CoreMinimal.h"

#include "ACFDamageCalculation.generated.h"

struct FACFDamageEvent;

/**
 * Base class for calculating custom damage logic.
 * Extend this class to implement specific damage formulas and critical hit rules.
 */
UCLASS(Blueprintable, Abstract, BlueprintType, DefaultToInstanced, EditInlineNew)
class ASCENTCOMBATFRAMEWORK_API UACFDamageCalculation : public UObject {
    GENERATED_BODY()

public:
    /**
     * Virtual function to Calculate final damage and fills secondary attribute modifications like stamina, posture etc.
     * Implement this in child classes
     *
     * @param inDamageEvent           Main damage input event.
     * @param otherAffectedAttributes    Output array of secondary attributes to modify.
     *                                       Example: reduce stamina on block, posture on hit, etc.
     * @return Final float damage to apply to health.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    float CalculateFinalDamage(const FACFDamageEvent& inDamageEvent, TArray<FAttributeData>& otherAffectedAttributes);
    virtual float CalculateFinalDamage_Implementation(const FACFDamageEvent& inDamageEvent, TArray<FAttributeData>& otherAffectedAttributes);

    /**
     * Evaluates which gameplay action should be triggered as a response to the hit
     * based on probabilities and damage context.
     * @param inDamageEvent The incoming damage event
     * @param hitResponseActions Array of candidate hit response actions with weights
     * @return GameplayTag representing the action to execute (e.g., hit, knockback)
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    FGameplayTag EvaluateHitResponseAction(const FACFDamageEvent& inDamageEvent, const TArray<FOnHitActionChances>& hitResponseActions);
    virtual FGameplayTag EvaluateHitResponseAction_Implementation(const FACFDamageEvent& inDamageEvent, const TArray<FOnHitActionChances>& hitResponseActions);

    /**
     * Determines whether the incoming hit qualifies as a critical strike
     * @param inDamageEvent The damage event used to evaluate the hit
     * @return True if the hit is critical, false otherwise
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    bool IsCriticalDamage(const FACFDamageEvent& inDamageEvent);
    virtual bool IsCriticalDamage_Implementation(const FACFDamageEvent& inDamageEvent);

    /**
     * Returns the UACFDamageType object from the given damage event
     * @param inDamageEvent The damage event containing the damage class
     * @return Pointer to the resolved UACFDamageType, or nullptr if invalid
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UACFDamageType* GetDamageType(const FACFDamageEvent& inDamageEvent);
};
