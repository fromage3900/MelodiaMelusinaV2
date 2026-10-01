// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ARSFunctionLibrary.h"
#include "ACFGASDeveloperSettings.h"
#include "ARSTypes.h"
#include <AbilitySystemComponent.h>
#include <GameplayEffect.h>
#include <GameplayTagsManager.h>

FGameplayTag UARSFunctionLibrary::GetAttributesTagRoot()
{
	return UGameplayTagsManager::Get().RequestGameplayTag(ARS::PrimaryAtt);
}

FGameplayTag UARSFunctionLibrary::GetParametersTagRoot()
{
	return UGameplayTagsManager::Get().RequestGameplayTag(ARS::Attribute);
}

FGameplayTag UARSFunctionLibrary::GetStatisticsTagRoot()
{
	return UGameplayTagsManager::Get().RequestGameplayTag(ARS::Stat);
}

bool UARSFunctionLibrary::TryGetAttributeFromArray(FGameplayTag attributeTag,
	const TArray<FAttribute>& attributesArray, FAttribute& outAttribute)
{
	if (attributesArray.Contains(attributeTag)) {
		outAttribute = *attributesArray.FindByKey(attributeTag);
		return true;
	}
	return false;
}

bool UARSFunctionLibrary::TryGetStatisticFromArray(FGameplayTag statTag,
	const TArray<FStatistic>& statsArray, FStatistic& outStat)
{
	if (statsArray.Contains(statTag)) {
		outStat = *statsArray.FindByKey(statTag);
		return true;
	}
	return false;
}

uint8 UARSFunctionLibrary::GetMaxLevel()
{
	UACFGASDeveloperSettings* settings = GetMutableDefault<UACFGASDeveloperSettings>();

	if (settings) {
		return settings->GetMaxLevel();
	}
	UE_LOG(LogTemp, Warning, TEXT("Missing MaxLevel! - ARSFUNCTION LIBRARY"));

	return 0;
}

FString UARSFunctionLibrary::FromAttributeTagToReadableName(FGameplayTag attributeTag)
{
	FString left, secondleft, right, right2;

	attributeTag.GetTagName().ToString().Split(".", &left, &right);
	right.Split(".", &secondleft, &right2);

	return right2;
}

FActiveGameplayEffectHandle UARSFunctionLibrary::CreateAndApplyGameplayEffectFromAttributeModifier(const FAttributesSetModifier& modifier,
	UAbilitySystemComponent* abilityComp, int32 effectLevel /*= 1*/, float modifierDuration)
{

	if (!abilityComp) {
		return FActiveGameplayEffectHandle();
	}

	if (!modifier.GameplayEffectModifier) {
		UE_LOG(LogTemp, Warning, TEXT("Missing GameplayEffect in AttributeSetModifier! - UARSFunctionLibrary"));

		return FActiveGameplayEffectHandle();
	}
	FGameplayEffectContextHandle EffectContext = abilityComp->MakeEffectContext();
	FGameplayTagContainer changedTags;

	FGameplayEffectSpecHandle SpecHandle = abilityComp->MakeOutgoingSpec(modifier.GameplayEffectModifier, effectLevel, EffectContext);
	if (SpecHandle.IsValid()) {
		FGameplayEffectSpec* Spec = SpecHandle.Data.Get();

		//let's add primary attributes first
		for (const FAttributeModifier& primary : modifier.PrimaryAttributesMod) {
			changedTags.AddTag(primary.AttributeType);

			if (primary.ModType == EModifierType::EAdditive) {
				Spec->SetSetByCallerMagnitude(primary.AttributeType, primary.Value);
			}
			else {
				FGameplayAttribute attribute;

				if (!UARSFunctionLibrary::TryGetAttributeFromSetByCallerTag(primary.AttributeType, attribute)) {
					continue;
				}
				const float baseValue = abilityComp->GetNumericAttribute(attribute);
				if (baseValue > 0.f) {
					const float modValue = baseValue * primary.Value / 100.f;
					Spec->SetSetByCallerMagnitude(primary.AttributeType, modValue);
				}
			}
		}
		// then attributes
		for (const FAttributeModifier& secondary : modifier.AttributesMod) {
			changedTags.AddTag(secondary.AttributeType);
			if (secondary.ModType == EModifierType::EAdditive) {
				Spec->SetSetByCallerMagnitude(secondary.AttributeType, secondary.Value);
			}
			else {
				FGameplayAttribute attribute;

				if (!UARSFunctionLibrary::TryGetAttributeFromSetByCallerTag(secondary.AttributeType, attribute)) {
					continue;
				}
				const float baseValue = abilityComp->GetNumericAttribute(attribute);
				if (baseValue > 0.f) {
					const float modValue = baseValue * secondary.Value / 100.f;
					Spec->SetSetByCallerMagnitude(secondary.AttributeType, modValue);
				}
			}
		}

		//then stats
		for (const FStatisticsModifier& stat : modifier.StatisticsMod) {
			changedTags.AddTag(stat.AttributeType);
			if (stat.ModType == EModifierType::EAdditive) {
				Spec->SetSetByCallerMagnitude(stat.AttributeType, stat.MaxValue);
			}
			else {
				FGameplayAttribute attribute;

				if (!UARSFunctionLibrary::TryGetAttributeFromSetByCallerTag(stat.AttributeType, attribute)) {
					continue;
				}
				const float baseValue = abilityComp->GetNumericAttribute(attribute);
				if (baseValue > 0.f) {
					const float modValue = baseValue * stat.MaxValue / 100.f;
					Spec->SetSetByCallerMagnitude(stat.AttributeType, modValue);
				}
			}
		}
		// Fallback: making sure no errors for missing tags are triggered

		for (const FGameplayModifierInfo& ModInfo : Spec->Def->Modifiers) {
			if (ModInfo.ModifierMagnitude.GetMagnitudeCalculationType() == EGameplayEffectMagnitudeCalculation::SetByCaller) {
				const FGameplayTag& Tag = ModInfo.ModifierMagnitude.GetSetByCallerFloat().DataTag;
				if (!changedTags.HasTagExact(Tag)) {
					Spec->SetSetByCallerMagnitude(Tag, 0.f);
				}
			}
		}

		if (modifierDuration > 0.f) {
			Spec->SetDuration(modifierDuration, true);
		}

		return abilityComp->ApplyGameplayEffectSpecToSelf(*Spec);
	}
	return FActiveGameplayEffectHandle();
}

FActiveGameplayEffectHandle UARSFunctionLibrary::CreateAndApplyGameplayEffectFromStatisticCost(const TSubclassOf<UGameplayEffect>& effectClass, const TArray<FStatisticValue>& Costs,
	UAbilitySystemComponent* abilityComp, int32 effectLevel /*= 1*/)
{

	FACFStatModifierContext* StatContext = new FACFStatModifierContext();
	StatContext->Costs = Costs;
	FGameplayEffectContextHandle ContextHandle = FGameplayEffectContextHandle(StatContext);
	if (abilityComp) {
		FGameplayEffectSpecHandle SpecHandle = abilityComp->MakeOutgoingSpec(
			effectClass,
			effectLevel, // Effect level
			ContextHandle
		);

		if (SpecHandle.IsValid()) {
			return abilityComp->ApplyGameplayEffectSpecToSelf(*SpecHandle.Data.Get());
		}
	}
	return FActiveGameplayEffectHandle();
}

bool UARSFunctionLibrary::VerifyCosts(const TArray<FStatisticValue>& Costs, UAbilitySystemComponent* abilityComp)
{
	for (const auto& stat : Costs) {
		FStatisticsConfig StatConf;

		if (!UARSFunctionLibrary::TryGetStatisticFromSetByCallerTag(stat.Statistic, StatConf)) {
			continue;
		}
		if (!StatConf.CurrentStatAttribute.IsValid()) {
			UE_LOG(LogTemp, Warning, TEXT("CurrentStatAttribute is not valid! - ARSFUNCTION LIBRARY"));
			continue;
		}
		const float attValue = abilityComp->GetNumericAttribute(StatConf.CurrentStatAttribute);
		if (attValue > 0.f && attValue >= stat.Value) {
			continue;
		}
		else {
			return false;
		}
	}
	return true;
}


UDataTable* UARSFunctionLibrary::GetAttributesToSetByCallerTagsDT()
{
	UACFGASDeveloperSettings* settings = GetMutableDefault<UACFGASDeveloperSettings>();

	if (settings) {
		return settings->GetAttributesToSetByCallerTagsDT();
	}

	return nullptr;
}

UDataTable* UARSFunctionLibrary::GetStatsToSetByCallerTagsDT()
{
	UACFGASDeveloperSettings* settings = GetMutableDefault<UACFGASDeveloperSettings>();

	if (settings) {
		return settings->GetStatsToSetByCallerTagsDT();
	}

	return nullptr;
}

bool UARSFunctionLibrary::TryGetAttributeFromSetByCallerTag(const FGameplayTag& setByCallerTag, FGameplayAttribute& outAttribute)
{
	UDataTable* AttributeMap = UARSFunctionLibrary::GetAttributesToSetByCallerTagsDT();

	if (!AttributeMap) {
		return false;
	}
	TArray<FAttributesConfig*> AllRows;
	AttributeMap->GetAllRows("", AllRows);

	for (const FAttributesConfig* Row : AllRows) {
		if (Row && Row->SetByCallerTag == setByCallerTag) {
			outAttribute = Row->Attribute;
			return true;
		}
	}
	return false;
}

bool UARSFunctionLibrary::TryGetAttributeUIName(const FGameplayAttribute& inAttribute, FText& outText)
{
	if (!inAttribute.IsValid()) {
		UE_LOG(LogTemp, Warning, TEXT("Invalid Attribute! - ARSFUNCTION LIBRARY - TryGetAttributeUIName"));
		return false;
	}
	UDataTable* AttributeMap = UARSFunctionLibrary::GetAttributesToSetByCallerTagsDT();

	if (!AttributeMap) {
		UE_LOG(LogTemp, Warning, TEXT("Missing Attribute Map! - ARSFUNCTION LIBRARY - TryGetAttributeUIName"));
		return false;
	}
	TArray<FAttributesConfig*> AllRows;
	AttributeMap->GetAllRows("", AllRows);

	for (const FAttributesConfig* Row : AllRows) {
		if (Row && Row->Attribute == inAttribute) {
			outText = Row->UIName;
			return true;
		}
	}

	UDataTable* StatsMap = UARSFunctionLibrary::GetStatsToSetByCallerTagsDT();
	if (!StatsMap) {
		UE_LOG(LogTemp, Warning, TEXT("Missing Stats Map! - ARSFUNCTION LIBRARY - TryGetAttributeUIName"));
		return false;
	}
	TArray<FStatisticsConfig*> AllStatRows;
	StatsMap->GetAllRows("", AllStatRows);

	for (const FStatisticsConfig* Row : AllStatRows) {
		if (Row && (Row->CurrentStatAttribute == inAttribute ||
			Row->MaxStatAttribute == inAttribute ||
			Row->RegenStatAttribute == inAttribute)) {
			outText = Row->UIName;
			return true;
		}
	}
	return false;

}

bool UARSFunctionLibrary::TryGetStatisticFromSetByCallerTag(const FGameplayTag& setByCallerTag, FStatisticsConfig& outStat)
{
	UDataTable* StatsMap = UARSFunctionLibrary::GetStatsToSetByCallerTagsDT();

	if (!setByCallerTag.IsValid()) {
		UE_LOG(LogTemp, Warning, TEXT("Missing Set By Caller Tag  - ARSFUNCTION LIBRARY- TryGetStatisticFromSetByCallerTag"));
		return false;
	}
	if (!StatsMap) {
		return false;
	}
	TArray<FStatisticsConfig*> AllRows;
	StatsMap->GetAllRows("", AllRows);

	for (const FStatisticsConfig* Row : AllRows) {
		if (Row && Row->SetByCallerTag == setByCallerTag) {
			outStat = *Row;
			return true;
		}
	}
	return false;
}

bool UARSFunctionLibrary::IsValidStatisticTag(FGameplayTag TagToCheck)
{
	const FGameplayTag root = GetStatisticsTagRoot();

	return UGameplayTagsManager::Get().RequestGameplayTagChildren(root).HasTag(TagToCheck);
}

bool UARSFunctionLibrary::IsValidAttributeTag(FGameplayTag TagToCheck)
{
	const FGameplayTag root = GetAttributesTagRoot();

	return UGameplayTagsManager::Get().RequestGameplayTagChildren(root).HasTag(TagToCheck);
}

bool UARSFunctionLibrary::IsValidParameterTag(FGameplayTag TagToCheck)
{
	const FGameplayTag root = GetParametersTagRoot();

	return UGameplayTagsManager::Get().RequestGameplayTagChildren(root).HasTag(TagToCheck);
}

FGameplayTag UARSFunctionLibrary::GetHealthTag()
{
	const UACFGASDeveloperSettings* settings = GetDefault<UACFGASDeveloperSettings>();

	if (settings) {
		return settings->GetHealthTag();
	}

	return FGameplayTag();
}

FGameplayAttribute UARSFunctionLibrary::GetDefaultHealthAttribute()
{
	UACFGASDeveloperSettings* settings = GetMutableDefault<UACFGASDeveloperSettings>();

	if (settings) {
		return settings->GetHealthAttribute();
	}
	return FGameplayAttribute();
}