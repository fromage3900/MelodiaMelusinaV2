// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFTeamManagerSubsystem.h"
#include "ACFTeamsConfigDataAsset.h"
#include "Components/ACFTeamComponent.h"
#include "Components/ACFTeamManagerComponent.h"
#include "GameFramework/GameStateBase.h"
#include "Logging.h"
#include <GameFramework/Controller.h>
#include <GameFramework/Pawn.h>
#include <GenericTeamAgentInterface.h>
#include <Engine/World.h>

void UACFTeamManagerSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    // Clear cached reference
    CachedTeamsManager.Reset();
}

UACFTeamManagerComponent* UACFTeamManagerSubsystem::GetTeamsManagerComponent() const
{
    // Use cached reference if valid
    if (CachedTeamsManager.IsValid()) {
        return CachedTeamsManager.Get();
    }

    // Find and cache the teams manager component
    if (const AGameStateBase* GameState = GetWorld()->GetGameState()) {
        if (UACFTeamManagerComponent* TeamsManager = GameState->FindComponentByClass<UACFTeamManagerComponent>()) {
            CachedTeamsManager = TeamsManager;
            return TeamsManager;
        }
    }

    return nullptr;
}



FGameplayTag UACFTeamManagerSubsystem::GetActorTeam(const AActor* Actor) const
{
    if (!Actor) {
        return FGameplayTag();
    }

    // Try team component first
    if (const UACFTeamComponent* TeamComp = Actor->FindComponentByClass<UACFTeamComponent>()) {
        return TeamComp->GetTeam();
    }

    // 2. If it's a Pawn, check the Controller for TeamComponent
    if (const APawn* Pawn = Cast<APawn>(Actor)) {
        if (AController* Controller = Pawn->GetController()) {
            if (UACFTeamComponent* ControllerTeamComp = Controller->FindComponentByClass<UACFTeamComponent>()) {
                return ControllerTeamComp->GetTeam();
            }
        }
    }
    // 3. Try Unreal's GenericTeamAgent interface
    if (const IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(Actor)) {
       const FGenericTeamId GenericTeamId = TeamAgent->GetGenericTeamId();
        return FromTeamIdToTag(GenericTeamId);
    }

    // 4. If it's a Pawn, try interface on Controller
    if (const APawn* Pawn = Cast<APawn>(Actor)) {
        if (const AController* Controller = Pawn->GetController()) {
            if (const IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(Controller)) {
                const FGenericTeamId GenericTeamId = TeamAgent->GetGenericTeamId();
                return FromTeamIdToTag(GenericTeamId);
            }
        }
    }
    return FGameplayTag();
}

ETeamAttitude::Type UACFTeamManagerSubsystem::GetAttitudeBetweenActors(const AActor* ActorA, const AActor* ActorB) const
{
    if (!ActorA || !ActorB) {
        return ETeamAttitude::Neutral;
    }

    const FGameplayTag TeamA = GetActorTeam(ActorA);
    const FGameplayTag TeamB = GetActorTeam(ActorB);

    return GetTeamAttitudeTowards(TeamA, TeamB);
}

FGenericTeamId UACFTeamManagerSubsystem::FromTagToTeamId(const FGameplayTag& TeamTag) const
{
    UACFTeamsConfigDataAsset* TeamConfig = GetTeamConfigDataAsset();

    if (!TeamConfig) {
        UE_LOG(ACFLog, Error, TEXT("Missing Team Config - UACFTeamManagerComponent "));

        return FGenericTeamId();
    }
    for (const auto& TeamPair : TeamConfig->TeamsConfig) {
        if (TeamPair.Value.TeamTag == TeamTag) {
            return TeamPair.Key;
        }
    }
    return FGenericTeamId();
}

FGameplayTag UACFTeamManagerSubsystem::FromTeamIdToTag(const FGenericTeamId& TeamId) const
{
    UACFTeamsConfigDataAsset* TeamConfig = GetTeamConfigDataAsset();

    if (!TeamConfig) {
        UE_LOG(ACFLog, Error, TEXT("Missing Team Config - UACFTeamManagerComponent "));
        return FGameplayTag();
    }
    if (TeamConfig->TeamsConfig.Contains(TeamId)) {
        return TeamConfig->TeamsConfig.Find(TeamId)->TeamTag;
    }

    return FGameplayTag();
}

bool UACFTeamManagerSubsystem::AreActorsHostile(const AActor* ActorA, const AActor* ActorB) const
{
    return GetAttitudeBetweenActors(ActorA, ActorB) == ETeamAttitude::Hostile;
}

bool UACFTeamManagerSubsystem::CanActorDamageActor(const AActor* Attacker, const AActor* Victim) const
{
    if (!Attacker || !Victim) {
        return false;
    }

    const FGameplayTag AttackerTeam = GetActorTeam(Attacker);
    const FGameplayTag VictimTeam = GetActorTeam(Victim);

    return CanTeamDamageTeam(AttackerTeam, VictimTeam);
}

bool UACFTeamManagerSubsystem::IsFriendlyFireEnabled() const
{
    if (const UACFTeamManagerComponent* TeamsManager = GetTeamsManagerComponent()) {
        return TeamsManager->IsFriendlyFireEnabled();
    }
    return false;
}

EBattleType UACFTeamManagerSubsystem::GetBattleType() const
{
    if (const UACFTeamManagerComponent* TeamsManager = GetTeamsManagerComponent()) {
        return TeamsManager->GetBattleType();
    }
    return EBattleType::ETeamBased;
}

ETeamAttitude::Type UACFTeamManagerSubsystem::GetDefaultAttitude() const
{
    if (const UACFTeamManagerComponent* TeamsManager = GetTeamsManagerComponent()) {
        return TeamsManager->GetDefaultAttitude();
    }
    return ETeamAttitude::Neutral;
}


UACFTeamsConfigDataAsset* UACFTeamManagerSubsystem::GetTeamConfigDataAsset() const
{
    if (UACFTeamManagerComponent* TeamsManager = GetTeamsManagerComponent()) {
        return TeamsManager->GetTeamConfigDataAsset();
    }
    return nullptr;
}

ETeamAttitude::Type UACFTeamManagerSubsystem::GetTeamAttitudeTowards(const FGameplayTag& TeamA, const FGameplayTag& TeamB) const
{
    if (TeamA == TeamB) {
        return GetDefaultAttitude();
    }

    // Read directly from data asset - NO caching, NO duplication
    const UACFTeamsConfigDataAsset* TeamConfig = GetTeamConfigDataAsset();
    if (!TeamConfig) {
        return GetDefaultAttitude();
    }

    // Find TeamA's relationships
    for (const auto& TeamEntry : TeamConfig->TeamsConfig) {
        const FTeamConfig& TeamConfigEntry = TeamEntry.Value;
        if (TeamConfigEntry.TeamTag == TeamA) {
            if (const auto* AttitudePtr = TeamConfigEntry.Relationship.Find(TeamB)) {
                return AttitudePtr->GetValue();
            }
            break;
        }
    }

    return GetDefaultAttitude();
}

bool UACFTeamManagerSubsystem::AreTeamsHostile(const FGameplayTag& TeamA, const FGameplayTag& TeamB) const
{
    return GetTeamAttitudeTowards(TeamA, TeamB) == ETeamAttitude::Hostile || GetBattleType() == EBattleType::EEveryoneAgainstEveryone;
}

bool UACFTeamManagerSubsystem::AreTeamsFriendly(const FGameplayTag& TeamA, const FGameplayTag& TeamB) const
{
    return GetTeamAttitudeTowards(TeamA, TeamB) == ETeamAttitude::Friendly;
}

bool UACFTeamManagerSubsystem::CanTeamDamageTeam(const FGameplayTag& AttackerTeam, const FGameplayTag& VictimTeam) const
{
    // Same team: allow only if friendly fire is enabled or FFA
    if (AttackerTeam == VictimTeam) {
        return IsFriendlyFireEnabled() || GetBattleType() == EBattleType::EEveryoneAgainstEveryone;
    }

    const ETeamAttitude::Type Attitude = GetTeamAttitudeTowards(AttackerTeam, VictimTeam);

    // Always can damage hostile teams
    if (Attitude == ETeamAttitude::Hostile) {
        return true;
    }

    // Can damage friendly-attitude (different) teams only if friendly fire is enabled
    if (Attitude == ETeamAttitude::Friendly) {
        return IsFriendlyFireEnabled() || GetBattleType() == EBattleType::EEveryoneAgainstEveryone;
    }

    // Neutral teams cant be damaged
    return false;
}

TArray<TEnumAsByte<ECollisionChannel>> UACFTeamManagerSubsystem::GetHostileCollisionChannels(const FGameplayTag& Team) const
{
    if (IsFriendlyFireEnabled()) {
        return GetAllDamageCollisionChannels();
    }
    TSet<ECollisionChannel> UniqueChannels; // Use TSet to avoid duplicates

    UACFTeamsConfigDataAsset* TeamConfig = GetTeamConfigDataAsset();
    if (!TeamConfig) {
        return TArray<TEnumAsByte<ECollisionChannel>>();
    }

    // Read directly from data asset
    for (const auto& TeamEntry : TeamConfig->TeamsConfig) {
        const FTeamConfig& TeamConfigEntry = TeamEntry.Value;
        if (AreTeamsHostile(Team, TeamConfigEntry.TeamTag)) {
            // Add to set - automatically handles duplicates
            for (const auto& Channel : TeamConfigEntry.DamageCollisionsChannel) {
                UniqueChannels.Add(Channel.GetValue());
            }
        }
    }

    // Convert TSet to TArray manually
    TArray<TEnumAsByte<ECollisionChannel>> Result;
    for (const ECollisionChannel& Channel : UniqueChannels) {
        Result.Add(Channel);
    }
    return Result;
}

TArray<TEnumAsByte<ECollisionChannel>> UACFTeamManagerSubsystem::GetAllDamageCollisionChannels() const
{
    TSet<ECollisionChannel> UniqueChannels;

    UACFTeamsConfigDataAsset* TeamConfig = GetTeamConfigDataAsset();
    if (!TeamConfig) {
        return TArray<TEnumAsByte<ECollisionChannel>>();
    }

    // Collect all channels from all teams
    for (const auto& TeamEntry : TeamConfig->TeamsConfig) {
        const FTeamConfig& TeamConfigEntry = TeamEntry.Value;
        for (const auto& Channel : TeamConfigEntry.DamageCollisionsChannel) {
            UniqueChannels.Add(Channel.GetValue());
        }
    }

    // Convert TSet to TArray manually
    TArray<TEnumAsByte<ECollisionChannel>> Result;
    for (const ECollisionChannel& Channel : UniqueChannels) {
        Result.Add(Channel);
    }
    return Result;
}

TArray<TEnumAsByte<ECollisionChannel>> UACFTeamManagerSubsystem::GetCollisionChannelsByTeam(const FGameplayTag& Team) const
{
    UACFTeamsConfigDataAsset* TeamConfig = GetTeamConfigDataAsset();
    if (!TeamConfig)
    {
        return TArray<TEnumAsByte<ECollisionChannel>>();
    }

    // Find the specific team and return its collision channels
    for (const auto& TeamEntry : TeamConfig->TeamsConfig)
    {
        const FTeamConfig& TeamConfigEntry = TeamEntry.Value;
        if (TeamConfigEntry.TeamTag == Team)
        {
            return TeamConfigEntry.DamageCollisionsChannel;
        }
    }

    return TArray<TEnumAsByte<ECollisionChannel>>();
}
void UACFTeamManagerSubsystem::NotifyTeamChanged(AActor* Actor, const FGameplayTag& NewTeam)
{
    OnTeamChanged.Broadcast(Actor, NewTeam);
}

void UACFTeamManagerSubsystem::NotifyFriendlyFireChanged(bool bEnabled)
{
    OnFriendlyFireChanged.Broadcast(bEnabled);
}

void UACFTeamManagerSubsystem::NotifyBattleTypeChanged(EBattleType NewBattleType)
{
    OnBattleTypeChanged.Broadcast(NewBattleType);
}
