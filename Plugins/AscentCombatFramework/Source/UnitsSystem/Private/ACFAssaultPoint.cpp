// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAssaultPoint.h"
#include "ACFConqueringComponent.h"
#include "ACFUnitTypes.h"
#include "Components/ACFAIWavesMasterComponent.h"
#include "Net/UnrealNetwork.h"
#include "Kismet/GameplayStatics.h"


void AACFAssaultPoint::SetConqueringState_Implementation(APlayerController* player, EConqueredState newState)
{
    conqueringState = newState;
    if (player) {
        UACFConqueringComponent* conqComp = GetLocalPlayerConqueringComponent(player);
        if (conqComp) {
            conqComp->SetConqueringState(AssaultPointTag, conqueringState);
        }
    }
    OnConquerStateChanged.Broadcast(conqueringState);
}

void AACFAssaultPoint::StartConquering_Implementation(APlayerController* player)
{
    SetConqueringState(player, EConqueredState::EConquerInProgress);

    OnConquestStarted();
}

void AACFAssaultPoint::CompleteConquering_Implementation(APlayerController* player)
{
    SetConqueringState(player, EConqueredState::EConquered);
    OnConquestCompleted();
}

void AACFAssaultPoint::InterruptConquering_Implementation(APlayerController* player)
{
    SetConqueringState(player, EConqueredState::ENotConquered);

    OnConquestInterrupted();
}

class UACFConqueringComponent* AACFAssaultPoint::GetLocalPlayerConqueringComponent(APlayerController* player) const
{
    return player->FindComponentByClass<UACFConqueringComponent>();
}

void AACFAssaultPoint::BeginPlay()
{
    Super::BeginPlay();
}

void AACFAssaultPoint::OnConquestStarted_Implementation()
{
}

void AACFAssaultPoint::OnConquestCompleted_Implementation()
{
}

void AACFAssaultPoint::OnConquestInterrupted_Implementation()
{
}

void AACFAssaultPoint::OnLoaded_Implementation()
{
   
    SetConqueringState( UGameplayStatics::GetPlayerController(this, 0), conqueringState);
}

void AACFAssaultPoint::OnRep_ConqueringState()
{
    OnConquerStateChanged.Broadcast(conqueringState);
}

void AACFAssaultPoint::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AACFAssaultPoint, conqueringState);
}
