// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSStatisticsComponent.h"
#include "CoreMinimal.h"

#include "ACFLegacyStatisticsComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnStatValueChanged, FGameplayTag, Stat, const FStatistic&, value);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnStatisticValueChanged, const FGameplayTag&, Stat, float, OldValue, float, NewValue);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnStatisticReachesZero, FGameplayTag, Stat);

/**
 *
 */
UCLASS()
class ADVANCEDRPGSYSTEM_API UACFLegacyStatisticsComponent : public UARSStatisticsComponent {
    GENERATED_BODY()

public:
    /*Adds a Modifier for the current AttributeSet of the character*/
    virtual FActiveGameplayEffectHandle AddAttributeSetModifier(const FAttributesSetModifier& modifier) override;

    /*Adds a Modifier for the current AttributeSet of the character*/
    virtual void RemoveAttributeSetModifier(const FActiveGameplayEffectHandle& modifier) override;

    // called to add to subtract given value from statistics based on param stat
    virtual void ModifyStat_Implementation(const FStatisticValue& StatMod) override;

    /*Modifies the actual Statistic "stat" adding to it "value" to the CurrentValue
    Server Side*/
    virtual void ModifyStatistic(FGameplayTag Stat, float value) override;

    /*Checks if current Statistics are enough for apply those Costs*/
    virtual bool CheckCosts(const TArray<FStatisticValue>& Costs) const override;

    /*Checks if current Statistic is enough to apply this Cost*/
    virtual bool CheckCost(const FStatisticValue& Cost) const override;

    /*Adds a Modifier for the current AttributeSet of the character for a limited amount of time*/
    virtual void AddTimedAttributeSetModifier(const FAttributesSetModifier& modifier, float duration) override;

    /*Remove the Statistic modifier from the actual Statistic*/
    virtual void ConsumeStatistics(const TArray<FStatisticValue>& Costs) override;

    /*Getter Current value for Statistic*/
    virtual float GetCurrentValueForStatitstic(FGameplayTag stat) const override;

    /*Getter Max value for Statistic*/
    virtual float GetMaxValueForStatitstic(FGameplayTag stat) const override;

    virtual float GetCurrentPrimaryAttributeValue(FGameplayTag attributeTag) const override;

    virtual float GetCurrentAttributeValue(FGameplayTag attributeTag) const override;

    virtual void InitializeAttributeSet() override;

    virtual void OnComponentLoaded_Implementation() override;

    virtual void OnComponentSaved_Implementation() override;

    virtual void OnLevelChanged() override;

    void OnDeath_Implementation() override;

    void OnRevive_Implementation() override;

    // OVERRIDES END

    /*Starts to regenerate all the Statistics with a regeneration value != 0.f.
   Server Side*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
    void StartRegeneration();

    /*Stops to regenerate all the Statistics with a regeneration value != 0.f.
        Server Side*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
    void StopRegeneration();

    UPROPERTY(BlueprintAssignable, Category = ARS)
    FOnStatisticValueChanged OnStatisticChanged;

    UPROPERTY(BlueprintAssignable, Category = ARS)
    FOnStatisticReachesZero OnStatisiticReachesZero;

    /*Everytime the StatisticTag Statistic will be modified, the amount of
        modifier will be multiplied by this value*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
    void AddStatisticConsumptionMultiplier(FGameplayTag statisticTag, float multiplier = 1.0f);

    UFUNCTION(BlueprintCallable, Category = ARS)
    float GetConsumptionMultiplierByStatistic(FGameplayTag statisticTag) const;

    /*Checks if your current Attributes are higher of the one passed as an argument,
        returns true only if all the actual attributes of the character are higher then the one passed as
        parameter*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    bool CheckPrimaryAttributesRequirements(const TArray<FAttribute>& attributeRequirements) const;

    /*Indicates if there is a statistic with this tag in the AttributeSet*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    bool HasValidStatistic(FGameplayTag stat) const { return AttributeSet.Statistics.Contains(stat); };

    UFUNCTION(BlueprintCallable, Category = ARS)
    bool HasValidAttribute(FGameplayTag param) const { return AttributeSet.Parameters.Contains(param); };

    UFUNCTION(BlueprintCallable, Category = ARS)
    bool HasValidPrimaryAttribute(FGameplayTag att) const { return AttributeSet.Attributes.Contains(att); };

    /*Uses numPerks of perks to increment the Attribute attributeTag by numPerks amount.
    Does nothing you don't have enough perks*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
    virtual void AssignPerkToPrimaryAttribute(FGameplayTag attributeTag, int32 numPerks = 1);

    /*Getter full statistic Structure*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    FStatistic GetFullStatisticStructure(FGameplayTag stat) const;

    /*Getter for the entire AttributeSet */
    UFUNCTION(BlueprintPure, Category = ARS)
    FAttributesSet GetCurrentAttributeSet() const;

    /*Getter for the entire Base AttributeSet without Modifiers.
    WARNING: current values for statistics are NOT updated here*/
    UFUNCTION(BlueprintPure, Category = ARS)
    FAttributesSet GetBaseAttributeSetWithoutModifiers() const
    {
        return baseAttributeSet;
    };

    /*use this to  properly reinitialize your attributeset from a saved level*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
    void PermanentlyModifyPrimaryAttribute(FGameplayTag attribute, float deltaValue = 1.0f);

    /*use this to Load an attribute set from savegame and properly reinitialize your attributeset*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
    void ReinitializeAttributeSetFromNewDefault(const FAttributesSet& newDefault);

    /*Define how your Statistics and Attributes are generated:
       Default Without Generation: No generation is applied, Default value are used
       Generate From Default Attributes: Define your Attributes in DefaultAttributeSet, Attributes and Statistic will be generated following the rules
       defined in ProjectSettings - ARS Settings
       Load By Level From Curve: Define the level of the character and Generate stats from AttributesByLevelCurves */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARS")
    EStatsLoadMethod StatsLoadMethod = EStatsLoadMethod::EGenerateFromDefaultsPrimary;

    /*Implement Rules to generate your ATTRIBUTES starting from your Level.
        For each Curve on X you have the Level, on Y the actual value of the Attribute for that Level
        Is used when StatLoadMethod is set to LoadByLevel and your LevelingType is GenerateNewStatsFromCurves*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        meta = (EditCondition = "LevelingType == ELevelingType::EGenerateNewStatsFromCurves && StatsLoadMethod == EStatsLoadMethod::ELoadByLevel"),
        Category = "ARS")
    class UARSLevelingSystemDataAsset* AttributesByLevelConfig;

    /*Multiplier applied everytime you modify CurrentValue of the target Statistics.
        Could be useful to implement logics like: if your inventory is full, Stamina consumption is
        multiplied by 1.5 for every action*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARS")
    TMap<FGameplayTag, float> StatisticConsumptionMultiplier;

    /*Turn off regeneration for this Character for optimization*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARS")
    bool bCanRegenerateStatistics = true;

    /*Regeneration time interval, set high values for optimization*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARS")
    float RegenerationTimeInterval = 0.2f;

private:
    UPROPERTY(SaveGame, Replicated)
    FAttributesSet baseAttributeSet;

    void CalcualtePrimaryStats();
    void CalcualteSecondaryStats();

    void GenerateSecondaryStat();
    void GenerateSecondaryStatFromCurrentPrimaryStat();

    // Regenerate Stats
    UFUNCTION(BlueprintCallable, Category = ARS)
    void GenerateStats();

    UFUNCTION()
    TArray<FAttribute> GetPrimitiveAttributesForCurrentLevel();

    TMap<FGameplayTag, FDateTime> regenDelay;

    UPROPERTY(SaveGame, ReplicatedUsing = OnRep_AttributeSet)
    FAttributesSet AttributeSet;

    UPROPERTY()
    FTimerHandle RegenTimer;

    UPROPERTY()
    bool bIsRegenerationStarted = false;

    TArray<FAttribute> Internal_GetPrimitiveAttributesForCurrentLevel();

    void RegenerateStat();
    FAttributesSetModifier CreateAdditiveAttributeSetModifireFromPercentage(const FAttributesSetModifier& modifier);

    TArray<FAttributesSetModifier> storedUnactiveModifiers;

    UFUNCTION()
    void Internal_ModifyStat(const FStatisticValue& StatMod, bool bResetDelay = true);

    UFUNCTION()
    void Internal_AddModifier(const FAttributesSetModifier& modifier);

    UFUNCTION()
    void OnRep_AttributeSet();

    void Internal_InitializeStats();
};
