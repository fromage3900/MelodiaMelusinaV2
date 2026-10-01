// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFLegacyStatisticsComponent.h"
#include "ARSFunctionLibrary.h"
#include "ARSTypes.h"
#include <Net/UnrealNetwork.h>
#include "ARSLevelingSystemDataAsset.h"
#include <TimerManager.h>
#include <Engine/World.h>
#include <AbilitySystemComponent.h>

FActiveGameplayEffectHandle UACFLegacyStatisticsComponent::AddAttributeSetModifier(const FAttributesSetModifier& attModifier)
{
	if (attModifier.StatisticsMod.Num() == 0 && attModifier.PrimaryAttributesMod.Num() == 0 && attModifier.AttributesMod.Num() == 0) {
		return FActiveGameplayEffectHandle();
	}

	if (!bIsInitialized) {
		storedUnactiveModifiers.Add(attModifier);
		return FActiveGameplayEffectHandle();
	}

	const FAttributesSetModifier convertedMod = CreateAdditiveAttributeSetModifireFromPercentage(attModifier);
	Internal_AddModifier(convertedMod);

	return convertedMod.GEHandle;
}

void UACFLegacyStatisticsComponent::RemoveAttributeSetModifier(const FActiveGameplayEffectHandle& attModifier)
{
	// Find the index of the modifier by comparing the GEHandle
	int32 Index = activeModifiers.IndexOfByPredicate([&attModifier](const FAttributesSetModifier& Mod)
		{
			return Mod.GEHandle == attModifier; // Compare the handle stored in the modifier
		});

	if (Index != INDEX_NONE)
	{
		activeModifiers.RemoveAt(Index);
		GenerateStats();
	}
}

void UACFLegacyStatisticsComponent::InitializeAttributeSet()
{
	Super::InitializeAttributeSet();
	if (GetOwner()->HasAuthority()) {
		Internal_InitializeStats();
		StartRegeneration();
	}
}

FAttributesSet UACFLegacyStatisticsComponent::GetCurrentAttributeSet() const
{
	return AttributeSet;
}

bool UACFLegacyStatisticsComponent::CheckCosts(const TArray<FStatisticValue>& Costs) const
{
	for (const FStatisticValue& cost : Costs) {
		if (!CheckCost(cost))
			return false;
	}
	return true;
}

bool UACFLegacyStatisticsComponent::CheckCost(const FStatisticValue& Cost) const
{
	const FStatistic* stat = AttributeSet.Statistics.FindByKey(Cost.Statistic);
	if (stat) {
		return stat->CurrentValue > (Cost.Value * GetConsumptionMultiplierByStatistic(stat->StatType));
	}
	else {
		UE_LOG(LogTemp, Warning, TEXT("Missing Statistic! - ARSStatistic Component"));
	}
	return false;
}

void UACFLegacyStatisticsComponent::ConsumeStatistics(const TArray<FStatisticValue>& Costs)
{

	for (const FStatisticValue& cost : Costs) {
		FStatisticValue modifier = cost;
		modifier.Value *= -1;
		ModifyStat(modifier);
	}
}

void UACFLegacyStatisticsComponent::ModifyStatistic(FGameplayTag Stat, float value)
{

	FStatisticValue mod = FStatisticValue(Stat, value);
	ModifyStat(mod);
}

void UACFLegacyStatisticsComponent::ModifyStat_Implementation(const FStatisticValue& StatMod)
{
	Internal_ModifyStat(StatMod);
}

FAttributesSetModifier UACFLegacyStatisticsComponent::CreateAdditiveAttributeSetModifireFromPercentage(const FAttributesSetModifier& attModifier)
{
	FAttributesSetModifier newatt;
	UAbilitySystemComponent* ASC = GetOwner()->FindComponentByClass<UAbilitySystemComponent>();
	if (ASC)
	{
		newatt.GEHandle = FActiveGameplayEffectHandle::GenerateNewHandle(ASC);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Cannot generate handle - AbilitySystemComponent not found on owner"));
	}

	for (const auto& att : attModifier.PrimaryAttributesMod) {
		if (att.ModType == EModifierType::EPercentage) {
			const FAttribute* originalatt = AttributeSet.Attributes.FindByKey(att);
			if (originalatt) {
				const float newval = originalatt->Value * att.Value / 100.f;
				const FAttributeModifier newMod(att.AttributeType, EModifierType::EAdditive, newval);
				newatt.PrimaryAttributesMod.AddUnique(newMod);
			}
		}
		else if (att.ModType == EModifierType::EAdditive) {
			const FAttributeModifier newMod(att.AttributeType, EModifierType::EAdditive, att.Value);
			newatt.PrimaryAttributesMod.AddUnique(newMod);
		}
	}
	for (const auto& att : attModifier.AttributesMod) {
		if (att.ModType == EModifierType::EPercentage) {
			const FAttribute* originalatt = AttributeSet.Parameters.FindByKey(att);
			if (originalatt) {
				const float newval = originalatt->Value * att.Value / 100.f;
				const FAttributeModifier newMod(att.AttributeType, EModifierType::EAdditive, newval);
				newatt.AttributesMod.AddUnique(newMod);
			}
		}
		else if (att.ModType == EModifierType::EAdditive) {
			const FAttributeModifier newMod(att.AttributeType, EModifierType::EAdditive, att.Value);
			newatt.AttributesMod.AddUnique(newMod);
		}
	}
	for (const auto& stat : attModifier.StatisticsMod) {
		const FStatistic* originalatt = AttributeSet.Statistics.FindByKey(stat);
		if (stat.ModType == EModifierType::EPercentage) {
			if (originalatt) {

				const float newval = originalatt->MaxValue * stat.MaxValue / 100.f;
				const float newregenval = originalatt->RegenValue * stat.RegenValue / 100.f;
				const FStatisticsModifier newMod(stat.AttributeType, EModifierType::EAdditive, newval, newregenval);
				newatt.StatisticsMod.AddUnique(newMod);
			}
		}
		else if (stat.ModType == EModifierType::EAdditive) {
			const FStatisticsModifier newMod(stat.AttributeType, EModifierType::EAdditive, stat.MaxValue, stat.RegenValue);
			newatt.StatisticsMod.AddUnique(newMod);
		}
	}
	return newatt;
}

void UACFLegacyStatisticsComponent::AddTimedAttributeSetModifier(const FAttributesSetModifier& attModifier, float duration)
{

	if (duration == 0.f)
		return;

	if (!attModifier.AttributesMod.IsValidIndex(0) && !attModifier.PrimaryAttributesMod.IsValidIndex(0) && !attModifier.StatisticsMod.IsValidIndex(0)) {
		return;
	}

	Internal_AddModifier(attModifier);

	FTimerDelegate TimerDel;
	FTimerHandle TimerHandle;
	TimerDel.BindUFunction(this, FName("RemoveAttributeSetModifier"), attModifier);

	UWorld* world = GetWorld();
	if (world) {
		world->GetTimerManager().SetTimer(TimerHandle, TimerDel, duration, false);
	}
}

float UACFLegacyStatisticsComponent::GetCurrentValueForStatitstic(FGameplayTag stat) const
{

	if (!UARSFunctionLibrary::IsValidStatisticTag(stat)) {
		UE_LOG(LogTemp, Warning, TEXT("INVALID STATISTIC TAG -  -  ARSStatistic Component"));
		return 0.f;
	}

	const FStatistic* intStat = AttributeSet.Statistics.FindByKey(stat);

	if (intStat) {
		return intStat->CurrentValue;
	}

	return 0.f;
}

float UACFLegacyStatisticsComponent::GetMaxValueForStatitstic(FGameplayTag stat) const
{

	if (!UARSFunctionLibrary::IsValidStatisticTag(stat)) {
		UE_LOG(LogTemp, Warning, TEXT("INVALID STATISTIC TAG -  -  ARSStatistic Component"));
		return 0.f;
	}

	const FStatistic* intStat = AttributeSet.Statistics.FindByKey(stat);

	if (intStat) {
		return intStat->MaxValue;
	}

	return 0.f;
}

void UACFLegacyStatisticsComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UACFLegacyStatisticsComponent, AttributeSet);
	DOREPLIFETIME(UACFLegacyStatisticsComponent, baseAttributeSet);
}

void UACFLegacyStatisticsComponent::RegenerateStat()
{
	for (const auto& elem : AttributeSet.Statistics) {
		if (elem.HasRegeneration) {
			if (regenDelay.Contains(elem.StatType)) {
				FDateTime* before = regenDelay.Find(elem.StatType);
				if (before) {
					const FTimespan delay = FDateTime::Now() - *before;
					if (delay.GetSeconds() > elem.RegenDelay) {
						regenDelay.Remove(elem.StatType);
					}
					else if (elem.RegenValue != 0.f) {
						continue;
					}
				}
			}
			FStatisticValue modifier;
			modifier.Statistic = elem.StatType;
			modifier.Value = elem.RegenValue * RegenerationTimeInterval;
			Internal_ModifyStat(modifier, false);
		}
	}
}

void UACFLegacyStatisticsComponent::Internal_AddModifier(const FAttributesSetModifier& attModifier)
{

	activeModifiers.AddUnique(attModifier);

	GenerateStats();
}

void UACFLegacyStatisticsComponent::GenerateStats()
{

	TArray<FStatistic> currentValuesCopy;
	for (const FStatistic& stat : AttributeSet.Statistics) {
		currentValuesCopy.Add(stat);
	}

	CalcualtePrimaryStats();
	GenerateSecondaryStat();

	for (FStatistic& stat : AttributeSet.Statistics) {
		FStatistic* oldStat = currentValuesCopy.FindByKey(stat);
		if (oldStat) {
			stat.CurrentValue = UARSFunctionLibrary::GetNewCurrentValueForNewMaxValue(oldStat->CurrentValue, oldStat->MaxValue, stat.MaxValue);
		}
	}
	AttributeSet.Sort();
	OnAttributeSetModified.Broadcast();
}

void UACFLegacyStatisticsComponent::Internal_ModifyStat(const FStatisticValue& StatMod, bool bResetDelay)
{
	if (!bIsInitialized)
		return;

	FStatistic* stat = AttributeSet.Statistics.FindByKey(StatMod.Statistic);

	if (stat) {
		const float oldValue = stat->CurrentValue;
		stat->CurrentValue += StatMod.Value; // *GetConsumptionMultiplierByStatistic(stat->StatType);

		if (stat->bClampToZero) {
			stat->CurrentValue = FMath::Clamp(stat->CurrentValue, 0.f, stat->MaxValue);
		}
		else {
			stat->CurrentValue = FMath::Clamp(stat->CurrentValue, -BIG_NUMBER, stat->MaxValue);
		}

		if (bResetDelay && stat->HasRegeneration && stat->RegenDelay > 0.f) {
			regenDelay.Add(stat->StatType, FDateTime::Now());
		}
		// AttributeSet.Sort();
		if (oldValue != stat->CurrentValue) {
			OnAttributeSetModified.Broadcast();
			OnStatisticChanged.Broadcast(stat->StatType, oldValue, stat->CurrentValue);
			if (FMath::IsNearlyZero(stat->CurrentValue)) {
				OnStatisiticReachesZero.Broadcast(stat->StatType);
				if (StatMod.Statistic == UARSFunctionLibrary::GetHealthTag()) {
					OnDeath();
					OnHealthReachesZero.Broadcast();

				}
			}
		}
	}
}

void UACFLegacyStatisticsComponent::CalcualtePrimaryStats()
{
	AttributeSet.Attributes = baseAttributeSet.Attributes;

	for (const FAttributesSetModifier& attModifier : activeModifiers) {

		for (const auto& att : attModifier.PrimaryAttributesMod) {
			ensure(UARSFunctionLibrary::IsValidAttributeTag(att.AttributeType));
			if (UARSFunctionLibrary::IsValidAttributeTag(att.AttributeType)) {
				FAttribute* originalatt = AttributeSet.Attributes.FindByKey(att);
				if (originalatt) {
					*(originalatt) = *(originalatt)+att;
				}
				else {
					AttributeSet.Attributes.Add(FAttribute(att.AttributeType, att.Value));
				}
			}
		}
	}
}

void UACFLegacyStatisticsComponent::CalcualteSecondaryStats()
{
	for (const FAttributesSetModifier& attModifier : activeModifiers) {
		for (const auto& att : attModifier.AttributesMod) {

			ensure(UARSFunctionLibrary::IsValidParameterTag(att.AttributeType));
			if (UARSFunctionLibrary::IsValidParameterTag(att.AttributeType)) {
				FAttribute* originalatt = AttributeSet.Parameters.FindByKey(att);
				if (originalatt) {
					*(originalatt) = *(originalatt)+att;
				}
				else {
					AttributeSet.Parameters.Add(FAttribute(att.AttributeType, att.Value));
				}
			}
		}

		for (const auto& att : attModifier.StatisticsMod) {
			ensure(UARSFunctionLibrary::IsValidStatisticTag(att.AttributeType));
			if (UARSFunctionLibrary::IsValidStatisticTag(att.AttributeType)) {
				FStatistic* originalatt = AttributeSet.Statistics.FindByKey(att);
				if (originalatt) {
					*(originalatt) = *(originalatt)+att;
				}
				else {

					AttributeSet.Statistics.Add(FStatistic(att.AttributeType, att.MaxValue, att.RegenValue));
				}
			}
		}
	}
}

void UACFLegacyStatisticsComponent::Internal_InitializeStats()
{
	bIsInitialized = false;

	AttributeSet.Statistics.Empty();
	AttributeSet.Attributes.Empty();
	AttributeSet.Parameters.Empty();

	TArray<FStatistic> currentValues;
	switch (StatsLoadMethod) {
	case EStatsLoadMethod::EUseDefaultsWithoutGeneration:
		baseAttributeSet = DefaultAttributeSet;
		AttributeSet = baseAttributeSet;
		break;
	case EStatsLoadMethod::EGenerateFromDefaultsPrimary:
		baseAttributeSet = DefaultAttributeSet;
		break;
	case EStatsLoadMethod::ELoadByLevel:
		baseAttributeSet.Attributes = GetPrimitiveAttributesForCurrentLevel();
		AttributeSet = baseAttributeSet;
		break;
	default:
		break;
	}

	if (StatsLoadMethod != EStatsLoadMethod::EUseDefaultsWithoutGeneration) {
		GenerateStats();
	}

	for (auto& statistic : AttributeSet.Statistics) {
		statistic.CurrentValue = statistic.bStartFromZero ? 0.f : statistic.MaxValue;
	}

	bIsInitialized = true;

	for (const FAttributesSetModifier& modifier : storedUnactiveModifiers) {
		AddAttributeSetModifier(modifier);
	}
	storedUnactiveModifiers.Empty();
}

TArray<FAttribute> UACFLegacyStatisticsComponent::Internal_GetPrimitiveAttributesForCurrentLevel()
{
	TArray<FAttribute> attributes;

	if (AttributesByLevelConfig) {
		AttributesByLevelConfig->GetAllAttributesValueByLevel(GetCurrentLevel(), attributes);
	}

	return attributes;
}

void UACFLegacyStatisticsComponent::ReinitializeAttributeSetFromNewDefault_Implementation(const FAttributesSet& newDefault)
{
	DefaultAttributeSet = newDefault;

	InitializeAttributeSet();
}

TArray<FAttribute> UACFLegacyStatisticsComponent::GetPrimitiveAttributesForCurrentLevel()
{
	return Internal_GetPrimitiveAttributesForCurrentLevel();
}

void UACFLegacyStatisticsComponent::PermanentlyModifyPrimaryAttribute_Implementation(FGameplayTag attribute, float deltaValue /*= 1.0f*/)
{
	const FAttribute* currValue = DefaultAttributeSet.Attributes.FindByKey(attribute);
	if (currValue) {
		FAttribute newValue(currValue->AttributeType, currValue->Value + deltaValue);
		DefaultAttributeSet.Attributes.Remove(newValue);
		DefaultAttributeSet.Attributes.AddUnique(newValue);
		InitializeAttributeSet();
	}
}

void UACFLegacyStatisticsComponent::OnRep_AttributeSet()
{
	OnAttributeSetModified.Broadcast();
}

void UACFLegacyStatisticsComponent::OnComponentLoaded_Implementation()
{
	if (StatsLoadMethod != EStatsLoadMethod::EUseDefaultsWithoutGeneration) {
		GenerateStats();
	}
}

void UACFLegacyStatisticsComponent::OnComponentSaved_Implementation()
{
}

float UACFLegacyStatisticsComponent::GetCurrentPrimaryAttributeValue(FGameplayTag attributeTag) const
{
	if (!UARSFunctionLibrary::IsValidAttributeTag(attributeTag)) {
		UE_LOG(LogTemp, Warning, TEXT("INVALID PRIMARY ATTRIBUTE TAG -  -  ARSStatistic Component"));
		return 0.f;
	}

	const FAttribute* intStat = AttributeSet.Attributes.FindByKey(attributeTag);

	if (intStat) {
		return intStat->Value;
	}

	UE_LOG(LogTemp, Warning, TEXT("Missing  Primary Attribute '%s'! -  -  ARSStatistic Component"), *attributeTag.GetTagName().ToString());

	return 0.f;
}

float UACFLegacyStatisticsComponent::GetCurrentAttributeValue(FGameplayTag attributeTag) const
{
	if (!UARSFunctionLibrary::IsValidParameterTag(attributeTag)) {
		UE_LOG(LogTemp, Warning, TEXT("INVALID SECONDARY ATTRIBUTE TAG -  -  ARSStatistic Component"));
		return 0.f;
	}

	const FAttribute* intStat = AttributeSet.Parameters.FindByKey(attributeTag);

	if (intStat) {
		return intStat->Value;
	}

	UE_LOG(LogTemp, Warning, TEXT("Missing  Secondary Attribute '%s! - ARSStatistic Component"), *attributeTag.GetTagName().ToString());

	return 0.f;
}

FStatistic UACFLegacyStatisticsComponent::GetFullStatisticStructure(FGameplayTag stat) const
{
	if (!UARSFunctionLibrary::IsValidStatisticTag(stat)) {
		UE_LOG(LogTemp, Warning, TEXT("INVALID STATISTIC TAG - %s - ARSStatisticsComponent::GetFullStatisticStructure"), *stat.ToString());
		return FStatistic();
	}
	if (AttributeSet.Statistics.Contains(stat)) {
		return *AttributeSet.Statistics.FindByKey(stat);
	}

	UE_LOG(LogTemp, Warning, TEXT("INVALID STATISTIC TAG - %s - ARSStatisticsComponent::GetFullStatisticStructure"), *stat.ToString());
	return FStatistic();
}

void UACFLegacyStatisticsComponent::AssignPerkToPrimaryAttribute_Implementation(FGameplayTag attributeTag, int32 numPerks /*= 1*/)
{
	if (numPerks > GetAvailablePerks()) {
		UE_LOG(LogTemp, Warning, TEXT("You don't have enough perks!"));
		return;
	}
}

void UACFLegacyStatisticsComponent::GenerateSecondaryStat()
{
	AttributeSet.Parameters = DefaultAttributeSet.Parameters;
	AttributeSet.Statistics = DefaultAttributeSet.Statistics;

	if (StatsLoadMethod != EStatsLoadMethod::EUseDefaultsWithoutGeneration) {
		GenerateSecondaryStatFromCurrentPrimaryStat();
	}
	CalcualteSecondaryStats();
}

void UACFLegacyStatisticsComponent::GenerateSecondaryStatFromCurrentPrimaryStat()
{
}

void UACFLegacyStatisticsComponent::OnRevive_Implementation()
{
	StartRegeneration();
}

void UACFLegacyStatisticsComponent::StartRegeneration_Implementation()
{
	if (!bIsRegenerationStarted && bCanRegenerateStatistics) {
		UWorld* world = GetWorld();
		if (world) {
			world->GetTimerManager().SetTimer(RegenTimer, this, &UACFLegacyStatisticsComponent::RegenerateStat, RegenerationTimeInterval, true);
			bIsRegenerationStarted = true;
		}
	}
}

void UACFLegacyStatisticsComponent::StopRegeneration_Implementation()
{
	if (bIsRegenerationStarted && RegenTimer.IsValid()) {
		UWorld* world = GetWorld();
		// Calling MyUsefulFunction after 5 seconds without looping
		world->GetTimerManager().ClearTimer(RegenTimer);
		bIsRegenerationStarted = false;
	}
}

void UACFLegacyStatisticsComponent::AddStatisticConsumptionMultiplier_Implementation(FGameplayTag statisticTag, float multiplier /*= 1.0f*/)
{
	if (UARSFunctionLibrary::IsValidStatisticTag(statisticTag)) {
		StatisticConsumptionMultiplier.Add(statisticTag, multiplier);
	}
}

float UACFLegacyStatisticsComponent::GetConsumptionMultiplierByStatistic(FGameplayTag statisticTag) const
{
	if (UARSFunctionLibrary::IsValidStatisticTag(statisticTag)) {
		const float* _mult = StatisticConsumptionMultiplier.Find(statisticTag);
		if (_mult) {
			return *(_mult);
		}
	}
	return 1.0f;
}

bool UACFLegacyStatisticsComponent::CheckPrimaryAttributesRequirements(const TArray<FAttribute>& Requirements) const
{
	for (const FAttribute& att : Requirements) {
		if (!UARSFunctionLibrary::IsValidAttributeTag(att.AttributeType)) {
			UE_LOG(LogTemp, Log,
				TEXT("Invalid Primary Attribute Tag!!! - "
					"CheckPrimaryAttributeRequirements"));
			return false;
		}
		const FAttribute* localatt = AttributeSet.Attributes.FindByKey(att.AttributeType);
		if (localatt && localatt->Value < att.Value)
			return false;
	}
	return true;
}

void UACFLegacyStatisticsComponent::OnLevelChanged()
{
	switch (GetLevelingType()) {
	case ELevelingType::EGenerateNewStatsFromCurves:
		Internal_InitializeStats();
		break;
	case ELevelingType::EAssignPerksManually:
		break;
	default:
		UE_LOG(LogTemp, Error, TEXT("A character that cannot level, just leveled! ARSStatisticsComponent"));
		break;
	}
}

void UACFLegacyStatisticsComponent::OnDeath_Implementation()
{
	StopRegeneration();
}
