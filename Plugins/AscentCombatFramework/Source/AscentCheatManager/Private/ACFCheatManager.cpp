// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFCheatManager.h"
#include "AMSMapSubsystem.h"
#include "AQSQuestManagerComponent.h"
#include "ARSLevelingComponent.h"
#include "Components/ACFCurrencyComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include <Engine/GameInstance.h>
#include <Kismet/GameplayStatics.h>
#include <GameFramework/Pawn.h>


void UACFCheatManager::DiscoverAllLocations()
{
    UAMSMapSubsystem* mapSubsystem = UGameplayStatics::GetGameInstance(GetOuterAPlayerController())->GetSubsystem<UAMSMapSubsystem>();
    mapSubsystem->DiscoverAllLocation();
}



void UACFCheatManager::AddExp(float Exps)
{
    UARSLevelingComponent* levelComp = GetOuterAPlayerController()->GetPawn()->FindComponentByClass<UARSLevelingComponent>();

    if (levelComp) {
        levelComp->AddExp(Exps);
    }
}

void UACFCheatManager::AddCurrency(float Coins)
{
    UACFCurrencyComponent* coinComp = GetOuterAPlayerController()->GetPawn()->FindComponentByClass<UACFCurrencyComponent>();

    if (coinComp) {
        coinComp->AddCurrency(Coins);
    }
}

void UACFCheatManager::ProceedInTrackedQuest()
{
    UAQSQuestManagerComponent* questComp = GetOuterAPlayerController()->FindComponentByClass<UAQSQuestManagerComponent>();
    if (questComp) {
        questComp->DEBUG_ProceedTrackedQuest();
    }
}

void UACFCheatManager::StartQuests()
{
    UAQSQuestManagerComponent* questComp = GetOuterAPlayerController()->FindComponentByClass<UAQSQuestManagerComponent>();
    if (questComp) {
        for (const FGameplayTag& questTag : QuestsToStart) {
            questComp->StartQuest(questTag);
        }
    }
}

void UACFCheatManager::AddItemsToInventory()
{
    UACFEquipmentComponent* equipComp = GetOuterAPlayerController()->GetPawn()->FindComponentByClass<UACFEquipmentComponent>();

    if (equipComp) {
        for (const FBaseItem& item : ItemsToAdd) {
            equipComp->AddItemToInventory(item);
        }
    }
}

