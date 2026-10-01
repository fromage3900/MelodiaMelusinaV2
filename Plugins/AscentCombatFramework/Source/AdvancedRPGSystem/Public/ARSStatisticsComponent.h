// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFGASAttributesComponent.h"
#include "ARSLevelingComponent.h"
#include "ARSTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>

#include "ARSStatisticsComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnHealthReachesZero);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAttributeSetModified);


UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ADVANCEDRPGSYSTEM_API UARSStatisticsComponent : public UACFGASAttributesComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UARSStatisticsComponent();

    /*Adds a Modifier for the current AttributeSet of the character*/
    UFUNCTION(BlueprintAuthorityOnly, BlueprintCallable, Category = ACF)
    virtual FActiveGameplayEffectHandle AddAttributeSetModifier(const FAttributesSetModifier& modifier);

    /*Removes a Modifier for the current AttributeSet of the character*/
   
    UFUNCTION(BlueprintAuthorityOnly, BlueprintCallable, Category = ACF)
    virtual void RemoveAttributeSetModifier(const FActiveGameplayEffectHandle& modifier);


    // called to add to subtract given value from statistics based on param stat
    UFUNCTION(Server, Reliable, Category = ACF)
    virtual void ModifyStat(const FStatisticValue& StatMod);

    /*Modifies the actual Statistic "stat" adding to it "value" to the CurrentValue
    Server Side*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual void ModifyStatistic(FGameplayTag Stat, float value);

    /*Checks if current Statistics are enough for apply those Costs*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual bool CheckCosts(const TArray<FStatisticValue>& Costs) const;

    /*Checks if current Statistic is enough to apply this Cost*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual bool CheckCost(const FStatisticValue& Cost) const;

    /*Adds a Modifier for the current AttributeSet of the character for a limited amount of time*/
    UFUNCTION(BlueprintAuthorityOnly, BlueprintCallable, Category = ACF)
    virtual void AddTimedAttributeSetModifier(const FAttributesSetModifier& modifier, float duration);

    /*Remove the Statistic modifier from the actual Statistic*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    virtual void ConsumeStatistics(const TArray<FStatisticValue>& Costs);

    /*Modifies the actual Statistic "stat" setting his CurrentValue to  "value" */
    UFUNCTION(BlueprintCallable, Category = ARS)
    virtual void RefillStat(FGameplayTag Stat);

    /*Getter Current value for Statistic*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    virtual float GetCurrentValueForStatitstic(FGameplayTag stat) const;

    /*Getter Max value for Statistic*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    virtual float GetMaxValueForStatitstic(FGameplayTag stat) const;

    /*Getter Current value/ Max Value for Statistic*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    virtual float GetNormalizedValueForStatitstic(FGameplayTag statTag) const;

    /*Getter for current Primary Attribute Value*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    virtual float GetCurrentPrimaryAttributeValue(FGameplayTag attributeTag) const;

    /*Getter for current Attribute Value*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    virtual float GetCurrentAttributeValue(FGameplayTag attributeTag) const;

    UPROPERTY(BlueprintAssignable, Category = ARS)
    FOnHealthReachesZero OnHealthReachesZero;

    UPROPERTY(BlueprintAssignable, Category = ARS)
    FOnAttributeSetModified OnAttributeSetModified;

    UFUNCTION(BlueprintNativeEvent, Category = ARS)
    void OnDeath();

    UFUNCTION(BlueprintNativeEvent, Category = ARS)
    void OnRevive();
    // LEVEL

    /*use this to  properly reinitialize your attributeset from a saved level*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
    virtual void SetNewLevelAndReinitialize(int32 newLevel);

    virtual void InitializeAttributeSet() override;

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|Set By Caller GEs")
    TSubclassOf<UGameplayEffect> StatModifierGE;

    /*Attribute set used if you select No Generation or Generate From Default Values
    In the first case it is used as is, in the second one, your Attribute will be
    used to generate your Statistics and Attributes following your ARS Settings.*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "ARS| DEPRECATED")
    FAttributesSet DefaultAttributeSet;

    UPROPERTY()
    bool bIsInitialized = false;

    UPROPERTY()
    TArray<FAttributesSetModifier> activeModifiers;
};
