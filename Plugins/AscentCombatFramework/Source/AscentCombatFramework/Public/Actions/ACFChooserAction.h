// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Chooser.h"
#include "Actions/ACFActionAbility.h"
#include "ACFChooserAction.generated.h"

class UACFAbilitySystemComponent;
class UAnimMontage;

/**
 * A child action class that uses a Chooser Table to dynamically select a montage.
 */
UCLASS(Blueprintable, BlueprintType, DefaultToInstanced, EditInlineNew)
class ASCENTCOMBATFRAMEWORK_API UACFChooserAction : public UACFActionAbility
{
    GENERATED_BODY()

public:
    UACFChooserAction();

    /** Reference to the Chooser Table */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chooser")
    UChooserTable* ChooserTable;

    /**
     * Weight binding for Output Float column in chooser table.
     *
     * IMPORTANT: The Output Float column bound to this property MUST be at the same index as WeightColumnIndex.
     * Example: If WeightColumnIndex = 0, then the FIRST column in your chooser must be the Output Float column
     *          bound to "Randomize". If WeightColumnIndex = 1, it must be the SECOND column, etc.
     *
     * Setup in Chooser Table:
     * 1. Add an Output Float column at the correct index position
     * 2. Bind it to this "Randomize" property
     * 3. Set weight values for each row (higher = more likely to be selected)
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chooser")
    float Randomize = 1.0f;

    /** Function to set parameters dynamically in Blueprint */
    UFUNCTION(BlueprintNativeEvent, Category = "Chooser")
    void SetChooserParams();

    /**
     * Index of the Output Float column to use for weights (defaults to 0 = first column).
     * The column's float values will be used as selection weights.
     * Higher weight = more likely to be selected.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chooser")
    int32 WeightColumnIndex = 0;

    /**
     * Multiplier for weight of previously selected montage (0.0 = never repeat, 1.0 = no penalty).
     * Prevents repetitive animations by reducing probability of same montage twice in a row.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chooser", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float RepeatProbabilityMultiplier = 0.5f;

protected:
    virtual void SetChooserParams_Implementation();

    virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData) override;

private:
    /**
     * Performs deterministic weighted random selection from filtered montages.
     * Uses GAS prediction key as seed to ensure client and server pick same montage.
     * Weights are looked up from the pre-built weight map.
     */
    UAnimMontage* SelectMontageWithDeterministicWeightedRandom(
        const TArray<UAnimMontage*>& Montages,
        const TMap<UAnimMontage*, float>& WeightMap,
        const FGameplayAbilityActivationInfo& ActivationInfo);

    /** Last selected montage (for anti-repeat penalty) */
    UPROPERTY(Transient)
    TObjectPtr<UAnimMontage> LastSelectedMontage;
};