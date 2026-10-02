// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSStatisticsComponent.h"
#include "AbilitySystemComponent.h"
#include "CoreMinimal.h"
#include "GameplayEffectTypes.h"

#include "ACFGASStatisticsComponent.generated.h"

/**
 *  Specification of the Stat component to manipulate GAS Attributes
 */
UCLASS()
class ADVANCEDRPGSYSTEM_API UACFGASStatisticsComponent : public UARSStatisticsComponent {
	GENERATED_BODY()

public:
	/*Adds a Modifier for the current AttributeSet of the character*/
	virtual FActiveGameplayEffectHandle AddAttributeSetModifier(const FAttributesSetModifier& modifier) override;

	/*Adds a Modifier for the current AttributeSet of the character*/
	//virtual void RemoveAttributeSetModifier(const FAttributesSetModifier& modifier) override;
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

	virtual float GetCurrentPrimaryAttributeValue(FGameplayTag attributeTag) const;

	virtual float GetCurrentAttributeValue(FGameplayTag attributeTag) const;

	virtual void BeginPlay() override;
	/*
	  virtual void InitializeAttributeSet() override;


	  virtual void OnComponentLoaded_Implementation() override;

	  virtual void OnComponentSaved_Implementation() override;

	  virtual void OnLevelChanged() override;*/

protected:
	void OnDeath_Implementation() override;

	void OnRevive_Implementation() override;

private:
	// UFUNCTION()
	void HandleHealthReachesZero(const FOnAttributeChangeData& ChangeData);

	float GetAttributeValue(FGameplayTag attributeTag) const;
};
