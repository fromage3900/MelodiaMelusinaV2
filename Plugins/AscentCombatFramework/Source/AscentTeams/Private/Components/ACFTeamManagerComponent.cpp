// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFTeamManagerComponent.h"
#include "Engine/CollisionProfile.h"
#include "ACFTeamsConfigDataAsset.h"
#include "Net/UnrealNetwork.h"
#include "ACFTeamManagerSubsystem.h"
#include <Engine/World.h>

UACFTeamManagerComponent::UACFTeamManagerComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void UACFTeamManagerComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UACFTeamManagerComponent, bFriendlyFireEnabled);
}

void UACFTeamManagerComponent::SetFriendlyFireEnabled(bool bEnabled)
{
	if (!GetOwner()->HasAuthority())
	{
		return;
	}

	if (bFriendlyFireEnabled != bEnabled)
	{
		bFriendlyFireEnabled = bEnabled;
		OnFriendlyFireChanged.Broadcast(bFriendlyFireEnabled);
	}
}

void UACFTeamManagerComponent::SetBattleType(EBattleType NewBattleType)
{
	if (!GetOwner()->HasAuthority())
	{
		return;
	}

	if (CurrentBattleType != NewBattleType)
	{
		CurrentBattleType = NewBattleType;
		OnBattleTypeChanged.Broadcast(CurrentBattleType);

		// Notify subsystem
		if (UWorld* World = GetWorld())
		{
			if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>())
			{
				TeamSubsystem->NotifyBattleTypeChanged(CurrentBattleType);
			}
		}
	}
}

void UACFTeamManagerComponent::OnRep_BattleType()
{
	OnBattleTypeChanged.Broadcast(CurrentBattleType);
	// Notify subsystem
	if (UWorld* World = GetWorld())
	{
		if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>())
		{
			TeamSubsystem->NotifyBattleTypeChanged(CurrentBattleType);
		}
	}
}

void UACFTeamManagerComponent::SetTeamConfigDataAsset(UACFTeamsConfigDataAsset* InTeamConfig)
{
	if (!GetOwner()->HasAuthority())
	{
		return;
	}

	TeamConfigDataAsset = InTeamConfig;
}



void UACFTeamManagerComponent::OnRep_FriendlyFireEnabled()
{
	OnFriendlyFireChanged.Broadcast(bFriendlyFireEnabled);

	// Notify subsystem
	if (UWorld* World = GetWorld())
	{
		if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>())
		{
			TeamSubsystem->NotifyFriendlyFireChanged(bFriendlyFireEnabled);
		}
	}
}