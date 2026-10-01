// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ARSStatisticsComponent.h"
#include "ACFRPGFunctionLibrary.h"
#include "ACFRPGTypes.h"
#include "ARSFunctionLibrary.h"
#include "ARSLevelingSystemDataAsset.h"
#include "ARSTypes.h"
#include "Net/UnrealNetwork.h"
#include <Curves/CurveFloat.h>
#include <Engine/World.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetSystemLibrary.h>
#include <TimerManager.h>

// Sets default values for this component's properties
UARSStatisticsComponent::UARSStatisticsComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked
	// every frame.  You can turn these features off to improve performance if you
	// don't need them.
	PrimaryComponentTick.bCanEverTick = false;

	SetIsReplicatedByDefault(true);
}

void UARSStatisticsComponent::InitializeAttributeSet()
{
	Super::InitializeAttributeSet();
}

// Called when the game starts
void UARSStatisticsComponent::BeginPlay()
{
	Super::BeginPlay();
}

FActiveGameplayEffectHandle UARSStatisticsComponent::AddAttributeSetModifier(const FAttributesSetModifier& attModifier)
{
	ensure(false);
	return FActiveGameplayEffectHandle();
}

void UARSStatisticsComponent::RemoveAttributeSetModifier(const FActiveGameplayEffectHandle& attModifier)
{

	ensure(false);
}



bool UARSStatisticsComponent::CheckCosts(const TArray<FStatisticValue>& Costs) const
{
	ensure(false);
	return true;
}

bool UARSStatisticsComponent::CheckCost(const FStatisticValue& Cost) const
{
	ensure(false);
	return false;
}

void UARSStatisticsComponent::ConsumeStatistics(const TArray<FStatisticValue>& Costs)
{
	ensure(false);
}

void UARSStatisticsComponent::ModifyStatistic(FGameplayTag Stat, float value)
{
	ensure(false);
}

void UARSStatisticsComponent::ModifyStat_Implementation(const FStatisticValue& StatMod)
{
	ensure(false);
}

void UARSStatisticsComponent::AddTimedAttributeSetModifier(const FAttributesSetModifier& attModifier, float duration)
{
	ensure(false);
}

float UARSStatisticsComponent::GetCurrentValueForStatitstic(FGameplayTag stat) const
{
	ensure(false);
	return -1.f;
}

float UARSStatisticsComponent::GetMaxValueForStatitstic(FGameplayTag stat) const
{
	ensure(false);
	return -1.f;
}

float UARSStatisticsComponent::GetNormalizedValueForStatitstic(FGameplayTag statTag) const
{
	const float max = GetMaxValueForStatitstic(statTag);
	const float value = GetCurrentValueForStatitstic(statTag);

	if (max != 0.f) {
		return value / max;
	}
	return 0.f;
}

float UARSStatisticsComponent::GetCurrentPrimaryAttributeValue(FGameplayTag attributeTag) const
{
	ensure(false);
	return -1.f;
}

float UARSStatisticsComponent::GetCurrentAttributeValue(FGameplayTag attributeTag) const
{
	ensure(false);
	return -1.f;
}

void UARSStatisticsComponent::OnDeath_Implementation()
{
}

void UARSStatisticsComponent::OnRevive_Implementation()
{
}

void UARSStatisticsComponent::RefillStat(FGameplayTag Stat)
{
	if (UARSFunctionLibrary::IsValidStatisticTag(Stat)) {
		ModifyStatistic(Stat, GetMaxValueForStatitstic(Stat));
	}
}

void UARSStatisticsComponent::SetNewLevelAndReinitialize_Implementation(int32 newLevel)
{
	ForceSetLevel(newLevel);
	InitializeAttributeSet();
}
