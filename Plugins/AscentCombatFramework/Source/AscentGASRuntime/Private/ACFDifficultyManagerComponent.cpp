// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFDifficultyManagerComponent.h"
#include "Net/UnrealNetwork.h"

UACFDifficultyManagerComponent::UACFDifficultyManagerComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void UACFDifficultyManagerComponent::SetDifficultyLevel(const FGameplayTag& NewDifficultyLevel)
{
	if (CurrentDifficultyLevel != NewDifficultyLevel) {
		CurrentDifficultyLevel = NewDifficultyLevel;
		OnDifficultyChanged.Broadcast(CurrentDifficultyLevel);
	}
}

void UACFDifficultyManagerComponent::BroadcastCurrentDifficulty()
{
	OnDifficultyChanged.Broadcast(CurrentDifficultyLevel);
}

void UACFDifficultyManagerComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFDifficultyManagerComponent, CurrentDifficultyLevel);
}

void UACFDifficultyManagerComponent::OnRep_DifficultyLevel()
{
	OnDifficultyChanged.Broadcast(CurrentDifficultyLevel);
}

void UACFDifficultyManagerComponent::OnComponentLoaded_Implementation()
{
	BroadcastCurrentDifficulty();
}
