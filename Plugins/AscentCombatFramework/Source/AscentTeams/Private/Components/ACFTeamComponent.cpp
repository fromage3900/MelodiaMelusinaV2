// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFTeamComponent.h"
#include "ACFTeamManagerSubsystem.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include <GenericTeamAgentInterface.h>
#include <GameplayTagContainer.h>

UACFTeamComponent::UACFTeamComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UACFTeamComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(UACFTeamComponent, CurrentTeam);
}

void UACFTeamComponent::BeginPlay()
{
    Super::BeginPlay();
}

void UACFTeamComponent::SetTeam(const FGameplayTag& NewTeam)
{
    // SERVER ONLY
    if (!GetOwner()->HasAuthority()) {
        UE_LOG(LogTemp, Warning, TEXT("SetTeam called on client! Use ServerRequestTeamChange instead."));
        return;
    }

    Internal_SetTeam(NewTeam);
}

void UACFTeamComponent::ServerRequestTeamChange_Implementation(const FGameplayTag& NewTeam)
{

    Internal_SetTeam(NewTeam);
}

void UACFTeamComponent::Internal_SetTeam(const FGameplayTag& NewTeam)
{
    if (CurrentTeam == NewTeam) {
        return;
    }

    CurrentTeam = NewTeam;

    // Update subsystem (server only)
    if (GetOwner()->HasAuthority()) {
        if (UACFTeamManagerSubsystem* TeamManager = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
            TeamManager->NotifyTeamChanged(GetOwner(),  NewTeam);
        }
    }

    OnTeamChanged.Broadcast( NewTeam);
}

void UACFTeamComponent::OnRep_CurrentTeam()
{
    // Called on clients when team replicates
    OnTeamChanged.Broadcast( CurrentTeam);

    // Update local subsystem cache if needed
    if (UACFTeamManagerSubsystem* TeamManager = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
        TeamManager->NotifyTeamChanged(GetOwner(), CurrentTeam);
    }
}

ETeamAttitude::Type UACFTeamComponent::GetAttitudeTowards(const FGameplayTag& OtherTeam) const
{
    if (UACFTeamManagerSubsystem* TeamManager = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
        return TeamManager->GetTeamAttitudeTowards(CurrentTeam, OtherTeam);
    }
    return ETeamAttitude::Neutral;
}

ETeamAttitude::Type UACFTeamComponent::GetAttitudeTowardsActor(AActor* OtherActor) const
{
    if (UACFTeamManagerSubsystem* TeamManager = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
        return TeamManager->GetAttitudeBetweenActors(GetOwner(), OtherActor);
    }
    return ETeamAttitude::Neutral;
}


bool UACFTeamComponent::IsHostileTowards(const FGameplayTag& OtherTeam) const
{
    return GetAttitudeTowards(OtherTeam) == ETeamAttitude::Hostile;
}

bool UACFTeamComponent::IsFriendlyWith(const FGameplayTag& OtherTeam) const
{
    return GetAttitudeTowards(OtherTeam) == ETeamAttitude::Friendly;
}

bool UACFTeamComponent::CanDamageTeam(const FGameplayTag& OtherTeam) const
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>())
    {
        return TeamSubsystem->CanTeamDamageTeam(CurrentTeam, OtherTeam);
    }
    return true;
}




FGenericTeamId UACFTeamComponent::GetGenericTeamId() const
{
    // Use subsystem for proper conversion via DataAsset
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>())
    {
        return TeamSubsystem->FromTagToTeamId(CurrentTeam);
    }
    
    return FGenericTeamId::NoTeam;
}