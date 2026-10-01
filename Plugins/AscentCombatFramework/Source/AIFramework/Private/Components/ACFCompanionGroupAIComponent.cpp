// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFCompanionGroupAIComponent.h"
#include "ARSLevelingComponent.h"
#include "ARSStatisticsComponent.h"
#include "Actors/ACFCharacter.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFPlayerController.h"
#include "TimerManager.h"
#include <Engine/World.h>
#include <GameFramework/Controller.h>

void UACFCompanionGroupAIComponent::AddExpToTheGroup(int32 Exp)
{

    if (contr) {
        AACFCharacter* charGroupLead = Cast<AACFCharacter>(contr->GetPawn());
        if (charGroupLead) {
            UARSLevelingComponent* StatComp = charGroupLead->FindComponentByClass<UARSLevelingComponent>();
            if (StatComp) {
                StatComp->AddExp(Exp);
            }
        }
        for (auto& companion : AICharactersInfo) {
            if (companion.AICharacter) {
                UARSLevelingComponent* StatComp = companion.AICharacter->FindComponentByClass<UARSLevelingComponent>();
                if (StatComp) {
                    StatComp->AddExp(Exp);
                }
            }
        }
    }
}

void UACFCompanionGroupAIComponent::SetDespawnIfTooDistanceFromLead(bool bDespawn)
{
    bDespawnIfTooDistanceFromLead = bDespawn;
    if (bDespawnIfTooDistanceFromLead) {
        StartUpdateCentroid();
    } else {
        StopUpdateCentroid();
    }
}

void UACFCompanionGroupAIComponent::SetReferences()
{
    /*Super::SetReferences();*/
    contr = Cast<AController>(GetOwner());
    if (contr) {
        AACFCharacter* charGroupLead = Cast<AACFCharacter>(contr->GetPawn());
        if (charGroupLead) {
            charGroupLead->OnDamageInflicted.AddDynamic(this, &UACFCompanionGroupAIComponent::HandleLeadHits);
            charGroupLead->OnDamageReceived.AddDynamic(this, &UACFCompanionGroupAIComponent::HandleLeadGetHit);
        }
        groupLead = contr->GetPawn();
    }
}

void UACFCompanionGroupAIComponent::BeginPlay()
{
    Super::BeginPlay();
    contr = Cast<AController>(GetOwner());
    if (contr) {
        auto& eventNewPawn = contr->GetOnNewPawnNotifier();
        eventNewPawn.AddLambda([this](APawn* newPawn) {
            HandlePossessedCharacterChanged(Cast<AACFCharacter>(newPawn));
        });
    }

    if (bDespawnIfTooDistanceFromLead) {
        StartUpdateCentroid();
    }
}

void UACFCompanionGroupAIComponent::StartUpdateCentroid()
{
    UWorld* world = GetWorld();
    if (world) {
        world->GetTimerManager().SetTimer(UpdateTimer, this, &UACFCompanionGroupAIComponent::UpdateCentroid, GetUpdateTime(), true);
        bUpdating = true;
    }
}

void UACFCompanionGroupAIComponent::StopUpdateCentroid()
{
    if (bUpdating) {
        UWorld* world = GetWorld();
        world->GetTimerManager().ClearTimer(UpdateTimer);
        bUpdating = false;
    }
}

void UACFCompanionGroupAIComponent::HandleLeadGetHit(const FACFDamageEvent& damage)
{
    SetInBattle(true, damage.DamageDealer);
}

void UACFCompanionGroupAIComponent::HandleLeadHits(const FACFDamageEvent& damage)
{
    SetInBattle(true, damage.DamageReceiver);
}

void UACFCompanionGroupAIComponent::HandlePossessedCharacterChanged(const AACFCharacter* _char)
{
    if (contr && _char) {
        AACFCharacter* charLead = Cast<AACFCharacter>(groupLead);
        if (charLead) {
            charLead->OnDamageInflicted.RemoveDynamic(
                this, &UACFCompanionGroupAIComponent::HandleLeadHits);
            charLead->OnDamageReceived.RemoveDynamic(
                this, &UACFCompanionGroupAIComponent::HandleLeadGetHit);
            SetReferences();
        }
    }
}

void UACFCompanionGroupAIComponent::UpdateCentroid()
{
    if (IsGroupSpawned()) {
        const FVector centroid = GetGroupCentroid();
        if ((GetGroupLead()->GetActorLocation() - centroid).Size() > GetMaxDistanceFromLead()) {
            DespawnGroup(true);
        }
    }
}
