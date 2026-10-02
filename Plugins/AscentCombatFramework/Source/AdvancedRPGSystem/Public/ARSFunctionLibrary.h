// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSTypes.h"
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <GameplayEffect.h>
#include <GameplayTagContainer.h>
#include <AttributeSet.h>

#include "ARSFunctionLibrary.generated.h"

class UAbilitySystemComponent;

/**
 * Static utility functions for interacting with Attribute Sets and Gameplay Effects in ARS (Advanced RPG System).
 */
UCLASS()
class ADVANCEDRPGSYSTEM_API UARSFunctionLibrary : public UBlueprintFunctionLibrary {
	GENERATED_BODY()

public:
	/**
	 * Retrieves the default GameplayTag associated with the Health attribute.
	 *
	 * @return The GameplayTag used to represent Health.
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FGameplayTag GetHealthTag();

	/**
	 * Retrieves the default GameplayAttribute associated with the Health
	 *
	 * @return The GameplayAttribute used to represent Health.
	 */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FGameplayAttribute GetDefaultHealthAttribute();

	/**
	 * Returns the maximum character level defined in the RPG system settings.
	 *
	 * @return The maximum level as defined in the project settings.
	 */
	UFUNCTION(BlueprintCallable, Category = ARS)
	static uint8 GetMaxLevel();

	/**
	 * Converts an attribute GameplayTag to a human-readable string name.
	 *
	 * @param attributeTag The GameplayTag representing the attribute.
	 * @return A readable name corresponding to the attribute tag.
	 */
	UFUNCTION(BlueprintCallable, Category = ARS)
	static FString FromAttributeTagToReadableName(FGameplayTag attributeTag);

	/**
	 * Returns the DataTable used to resolve SetByCaller gameplay tags into attributes.
	 *
	 * @return The data table reference containing SetByCaller tag mapping.
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static UDataTable* GetAttributesToSetByCallerTagsDT();

	/**
	 * Returns the DataTable used to resolve SetByCaller gameplay tags into stats.
	 *
	 * @return The data table reference containing SetByCaller tag mapping.
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static UDataTable* GetStatsToSetByCallerTagsDT();

	/**
	 * Resolves a SetByCaller tag into the corresponding GameplayAttribute.
	 *
	 * @param setByCallerTag The gameplay tag used as SetByCaller key.
	 * @return The resolved GameplayAttribute.
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool TryGetAttributeFromSetByCallerTag(const FGameplayTag& setByCallerTag, FGameplayAttribute& outAttribute);

	/**
	 * Resolves a FGameplayAttribute tag into the corresponding UI Text.
	 *
	 * @param inAttribute the attribute
	 * @return The resolved text.
	    */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool TryGetAttributeUIName(const FGameplayAttribute& inAttribute, FText& outText);

	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool TryGetStatisticFromSetByCallerTag(const FGameplayTag& setByCallerTag, FStatisticsConfig& outStat);

	/**
	 * Creates and applies a GameplayEffect based on the values contained in an FAttributesSetModifier.
	 * Supports dynamic duration configuration.
	 *
	 * @param effectClass The class of the GameplayEffect to instantiate.
	 * @param modifier The modifier structure containing attributes and values.
	 * @param abilityComp The target Ability System Component.
	 * @param effectLevel Optional level of the effect (default is 1).
	 * @param modifierDuration Duration in seconds (0 for default (infinite), or a positive value to enforce it).
	 * @return A handle to the active GameplayEffect applied.
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FActiveGameplayEffectHandle CreateAndApplyGameplayEffectFromAttributeModifier(const FAttributesSetModifier& modifier,
		UAbilitySystemComponent* abilityComp, int32 effectLevel = 1, float modifierDuration = -1.f);

	/**
	 * Creates and applies a GameplayEffect that consumes a list of statistics as cost.
	 *
	 * @param effectClass The class of the GameplayEffect to instantiate.
	 * @param Costs A list of statistic values used as cost.
	 * @param abilityComp The target Ability System Component.
	 * @param effectLevel Optional level of the effect (default is 1).
	 * @return A handle to the active GameplayEffect applied.
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FActiveGameplayEffectHandle CreateAndApplyGameplayEffectFromStatisticCost(const TSubclassOf<UGameplayEffect>& effectClass, const TArray<FStatisticValue>& Costs,
		UAbilitySystemComponent* abilityComp, int32 effectLevel = 1);

	/**
	 * Verifies that the provided Ability System Component has enough resources to cover the given costs.
	 *
	 * @param Costs A list of statistics representing the resource costs.
	 * @param abilityComp The Ability System Component to verify against.
	 * @return True if the component has sufficient resources, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool VerifyCosts(const TArray<FStatisticValue>& Costs, UAbilitySystemComponent* abilityComp);

	/**
	 * Recalculates a current value based on a change in the corresponding max value,
	 * preserving the same percentage.
	 *
	 * @param oldCurrentValue The current value before the max changed.
	 * @param oldMaxValue The old max value.
	 * @param newMaxValue The new max value.
	 * @return The new current value that maintains the same percentage.
	 */
	UFUNCTION(BlueprintCallable, Category = ARS)
	static float GetNewCurrentValueForNewMaxValue(float oldCurrentValue, float oldMaxValue, float newMaxValue)
	{
		const float multiplier = oldCurrentValue / oldMaxValue;
		return newMaxValue * multiplier;
	}

	/*Gets the root GameplayTag for Attributes, the one specified in RPGSettings*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	static FGameplayTag GetAttributesTagRoot();

	/*Gets the root GameplayTag for Parameters, the one specified in RPGSettings*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	static FGameplayTag GetParametersTagRoot();

	/*Gets the root GameplayTag for Statistics, the one specified in RPGSettings*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	static FGameplayTag GetStatisticsTagRoot();

	/*Tries to find an attribute with the provided tag in the given array*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	static bool TryGetAttributeFromArray(FGameplayTag attributeTag, const TArray<FAttribute>& attributesArray, FAttribute& outAttribute);

	/*Tries to find a Statistic with the provided tag in the given array*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	static bool TryGetStatisticFromArray(FGameplayTag statTag, const TArray<FStatistic>& statsArray, FStatistic& outStat);

	/*Returns true if TagToCheck is a ChildTag of StatisticTag Root*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	static bool IsValidStatisticTag(FGameplayTag TagToCheck);

	/*Returns true if TagToCheck is a ChildTag of AttributeTag Root*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	static bool IsValidAttributeTag(FGameplayTag TagToCheck);

	/*Returns true if TagToCheck is a ChildTag of ParameterTag Root*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	static bool IsValidParameterTag(FGameplayTag TagToCheck);
};
