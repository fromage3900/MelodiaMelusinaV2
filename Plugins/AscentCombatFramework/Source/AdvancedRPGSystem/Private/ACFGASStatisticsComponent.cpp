// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFGASStatisticsComponent.h"
#include "ACFRPGFunctionLibrary.h"
#include "ACFRPGTypes.h"
#include "ARSFunctionLibrary.h"
#include "AbilitySystemComponent.h"

FActiveGameplayEffectHandle UACFGASStatisticsComponent::AddAttributeSetModifier(const FAttributesSetModifier& attModifier)
{

	FAttributesSetModifier convertedMod = attModifier;
	if (attModifier.GEModifierType == EGEType::ESetByCallerFromConfig) {
		if (attModifier.StatisticsMod.Num() == 0 && attModifier.PrimaryAttributesMod.Num() == 0 && attModifier.AttributesMod.Num() == 0) {
			return FActiveGameplayEffectHandle();
		}
		convertedMod.GEHandle = UARSFunctionLibrary::CreateAndApplyGameplayEffectFromAttributeModifier(attModifier, GetOwnerAbilityComponent());
		activeModifiers.AddUnique(convertedMod);
	}
	else {
		convertedMod.GEHandle = UACFRPGFunctionLibrary::AddGameplayEffectToActor(FGameplayEffectConfig(attModifier.GameplayEffectModifier, attModifier.GELevel), GetOwner());
	}
	activeModifiers.AddUnique(convertedMod);
	return convertedMod.GEHandle;
}

/*
void UACFGASStatisticsComponent::RemoveAttributeSetModifier(const FAttributesSetModifier& attModifier)
{
	FAttributesSetModifier* localmod = activeModifiers.FindByKey(attModifier);
	if (localmod) {

		UACFRPGFunctionLibrary::RemovesActiveGameplayEffectFromActor(localmod->GEHandle, GetOwner());
		activeModifiers.RemoveSingle(*(localmod));
	}
}*/

void UACFGASStatisticsComponent::RemoveAttributeSetModifier(const FActiveGameplayEffectHandle& modifier)
{
	UACFRPGFunctionLibrary::RemovesActiveGameplayEffectFromActor(modifier, GetOwner());
	activeModifiers.RemoveAll([&modifier](const FAttributesSetModifier& Modifier)
		{
			return Modifier.GEHandle == modifier;
		});
}

bool UACFGASStatisticsComponent::CheckCosts(const TArray<FStatisticValue>& Costs) const
{
	if (GetOwnerAbilityComponent()) {
		return UARSFunctionLibrary::VerifyCosts(Costs, GetOwnerAbilityComponent());
	}
	return true;
}

bool UACFGASStatisticsComponent::CheckCost(const FStatisticValue& Cost) const
{

	TArray<FStatisticValue> Costs;
	Costs.Add(Cost);
	return CheckCosts(Costs);
}

void UACFGASStatisticsComponent::ConsumeStatistics(const TArray<FStatisticValue>& Costs)
{

	UARSFunctionLibrary::CreateAndApplyGameplayEffectFromStatisticCost(StatModifierGE, Costs, GetOwnerAbilityComponent());
	OnAttributeSetModified.Broadcast();
}

void UACFGASStatisticsComponent::ModifyStatistic(FGameplayTag Stat, float value)
{

	// ADDING - since we are consuming those value
	TArray<FStatisticValue> Costs = { FStatisticValue(Stat, -value) };
	ConsumeStatistics(Costs);
}

void UACFGASStatisticsComponent::ModifyStat_Implementation(const FStatisticValue& StatMod)
{

	TArray<FStatisticValue> Costs = { FStatisticValue(StatMod.Statistic, -StatMod.Value) };
	ConsumeStatistics(Costs);
}

void UACFGASStatisticsComponent::AddTimedAttributeSetModifier(const FAttributesSetModifier& attModifier, float duration)
{

	// we are not returning the handle for timed modifiers are they are removed automatically
	if (attModifier.GEModifierType == EGEType::ESetByCallerFromConfig) {
		if (attModifier.StatisticsMod.Num() == 0 && attModifier.PrimaryAttributesMod.Num() == 0 && attModifier.AttributesMod.Num() == 0) {
			return;
		}
		UARSFunctionLibrary::CreateAndApplyGameplayEffectFromAttributeModifier(attModifier, GetOwnerAbilityComponent(), duration);
	}
	else {
		UACFRPGFunctionLibrary::AddGameplayEffectToActor(FGameplayEffectConfig(attModifier.GameplayEffectModifier, attModifier.GELevel), GetOwner());
	}
}

float UACFGASStatisticsComponent::GetCurrentValueForStatitstic(FGameplayTag stat) const
{

	FStatisticsConfig statConfig;
	if (UARSFunctionLibrary::TryGetStatisticFromSetByCallerTag(stat, statConfig) && GetOwnerAbilityComponent()) {
		bool bFound;
		return GetOwnerAbilityComponent()->GetGameplayAttributeValue(statConfig.CurrentStatAttribute, bFound);
	}

	return 0.f;
}

float UACFGASStatisticsComponent::GetMaxValueForStatitstic(FGameplayTag stat) const
{

	FStatisticsConfig statConfig;
	if (UARSFunctionLibrary::TryGetStatisticFromSetByCallerTag(stat, statConfig) && GetOwnerAbilityComponent()) {
		bool bFound;
		return GetOwnerAbilityComponent()->GetGameplayAttributeValue(statConfig.MaxStatAttribute, bFound);
	}

	return -1.f;
}

float UACFGASStatisticsComponent::GetCurrentPrimaryAttributeValue(FGameplayTag attributeTag) const
{
	return GetAttributeValue(attributeTag);
}

float UACFGASStatisticsComponent::GetAttributeValue(FGameplayTag attributeTag) const
{
	FGameplayAttribute statConfig;
	if (UARSFunctionLibrary::TryGetAttributeFromSetByCallerTag(attributeTag, statConfig) && GetOwnerAbilityComponent()) {
		bool bFound;
		return GetOwnerAbilityComponent()->GetGameplayAttributeValue(statConfig, bFound);
	}
	return -1.f;
}

float UACFGASStatisticsComponent::GetCurrentAttributeValue(FGameplayTag attributeTag) const
{
	return GetAttributeValue(attributeTag);
}

void UACFGASStatisticsComponent::BeginPlay()
{
	Super::BeginPlay();

	const FGameplayAttribute healthAttribute = UARSFunctionLibrary::GetDefaultHealthAttribute();
	if (GetOwnerAbilityComponent()) {
		GetOwnerAbilityComponent()->GetGameplayAttributeValueChangeDelegate(healthAttribute).AddUObject(this, &UACFGASStatisticsComponent::HandleHealthReachesZero);
	}
}

void UACFGASStatisticsComponent::HandleHealthReachesZero(const FOnAttributeChangeData& Data)
{
	if (Data.NewValue == 0.f) {
		OnDeath();
		OnHealthReachesZero.Broadcast();
	}
}

void UACFGASStatisticsComponent::OnDeath_Implementation()
{
}

void UACFGASStatisticsComponent::OnRevive_Implementation()
{
}
