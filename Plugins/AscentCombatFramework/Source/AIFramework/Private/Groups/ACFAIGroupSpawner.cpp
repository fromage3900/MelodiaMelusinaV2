// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Groups/ACFAIGroupSpawner.h"
#include "ACFAIController.h"
#include "ACFAITypes.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFGroupAIComponent.h"
#include "Game/ACFTypes.h"
#include "Groups/ACFGroupAIController.h"
#include "TimerManager.h"
#include <Components/SplineComponent.h>
#include <Engine/World.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetSystemLibrary.h>
#include "ACFTeamManagerSubsystem.h"

// Sets default values
AACFAIGroupSpawner::AACFAIGroupSpawner()
{
    // Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = false;
    // initalize spline component

    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root Componnet"));
    AIGroupComponent = CreateDefaultSubobject<UACFGroupAIComponent>(TEXT("Group Componnet"));
    // SetRootComponent(AIGroupComponent);
    AIGroupComponent->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepRelativeTransform);
    AIControllerClass = AACFGroupAIController::StaticClass();
    TeamComponent = CreateDefaultSubobject<UACFTeamComponent>(TEXT("TeamComponent"));
}

// Called when the game starts or when spawned
void AACFAIGroupSpawner::BeginPlay()
{
    Super::BeginPlay();

    if (!AIGroupComponent->OnAgentsSpawned.IsAlreadyBound(this, &AACFAIGroupSpawner::StartUpdatePos)) {
        AIGroupComponent->OnAgentsSpawned.AddDynamic(this, &AACFAIGroupSpawner::StartUpdatePos);
    }
    if (!AIGroupComponent->OnAllAgentDeath.IsAlreadyBound(this, &AACFAIGroupSpawner::StopUpdatePos)) {
        AIGroupComponent->OnAllAgentDeath.AddDynamic(this, &AACFAIGroupSpawner::StopUpdatePos);
    }

    if (AIGroupComponent && GetOwner() && GetOwner()->HasAuthority()) {
        if (bSpawnOnBeginPlay) {
            AIGroupComponent->SpawnGroup();
        }
    }
}

int32 AACFAIGroupSpawner::GetGroupSize() const
{
    return GetAIGroupComponent()->GetGroupSize();
}

bool AACFAIGroupSpawner::GetAgentWithIndex(int32 index, FAIAgentsInfo& outAgent) const
{
    if (AIGroupComponent) {
        return AIGroupComponent->GetAgentByIndex(index, outAgent);
    }
    return false;
}

AACFCharacter* AACFAIGroupSpawner::GetAgentNearestTo(const FVector& location) const
{
    if (AIGroupComponent) {
        return AIGroupComponent->GetAgentNearestTo(location);
    }
    return nullptr;
}

void AACFAIGroupSpawner::StartUpdatePos()
{
    if (bCheckPos || !bUpdateSpawnerPosition) {
        return;
    }

    UWorld* world = GetWorld();
    if (world) {
        world->GetTimerManager().SetTimer(
            timerHandle, this, &AACFAIGroupSpawner::AdjustSpawnerPos,
            UpdateGroupPositionTimeInterval, true);
        bCheckPos = true;
    }
}

void AACFAIGroupSpawner::StopUpdatePos()
{
    timerHandle.Invalidate();
    bCheckPos = false;
}

void AACFAIGroupSpawner::AdjustSpawnerPos()
{
    if (AIGroupComponent->GetGroupSize() == 0) {
        StopUpdatePos();
        return;
    }

    FAIAgentsInfo agentInfo;

    if (AIGroupComponent->GetAgentByIndex(0, agentInfo) && agentInfo.AICharacter) {
        SetActorRotation(agentInfo.AICharacter->GetActorRotation());
    }

    SetActorLocation(AIGroupComponent->GetGroupCentroid());
}


FGameplayTag AACFAIGroupSpawner::GetEntityCombatTeam_Implementation() const
{
    return TeamComponent ? TeamComponent->GetTeam() : FGameplayTag();
}

void AACFAIGroupSpawner::AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam)
{
    if (UWorld* World = GetWorld()) {
        if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
            const FGenericTeamId GenericTeamId = TeamSubsystem->FromTagToTeamId(inCombatTeam);
            SetGenericTeamId(GenericTeamId);
        }
    }
}

FGenericTeamId AACFAIGroupSpawner::GetGenericTeamId() const
{
    return TeamComponent ? TeamComponent->GetGenericTeamId() : FGenericTeamId::NoTeam;
}

void AACFAIGroupSpawner::SetGenericTeamId(const FGenericTeamId& TeamID)
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
        const FGameplayTag TeamTag = TeamSubsystem->FromTeamIdToTag(TeamID);
        if (TeamComponent) {

            TeamComponent->ServerRequestTeamChange(TeamTag);
        }
    }
}

ETeamAttitude::Type AACFAIGroupSpawner::GetTeamAttitudeTowards(const AActor& OtherTeam) const
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {

        return TeamSubsystem->GetAttitudeBetweenActors(this, &OtherTeam);
    }
    return ETeamAttitude::Neutral;
}



/*
void AACFAIGroupSpawner::SetGenericTeamId(const FGenericTeamId& InTeamID)
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
        const FGameplayTag TeamTag = TeamSubsystem->FromTeamIdToTag(TeamID);
        if (TeamComponent) {

            TeamComponent->ServerRequestTeamChange(inCombatTeam);
        }
    }
}

FGenericTeamId AACFAIGroupSpawner::GetGenericTeamId() const
{
    return TeamComponent ? TeamComponent->GetGenericTeamId() : FGenericTeamId::NoTeam;
}

ETeamAttitude::Type AACFAIGroupSpawner::GetTeamAttitudeTowards(const AActor& OtherTeam) const
{
    if (TeamComponent && GetWorld()) {
        if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
            const FGameplayTag MyTeam = TeamComponent->GetTeam(); // Get tag from component
            const FGameplayTag OtherTeamTag = TeamSubsystem->FromTeamIdToTag(OtherTeam);
            return TeamSubsystem->GetTeamAttitudeTowards(MyTeam, OtherTeamTag);
        }
    }
    return ETeamAttitude::Neutral;
}*/

