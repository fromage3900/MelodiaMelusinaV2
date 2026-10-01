// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFAIWavesMasterComponent.h"
#include "ACFAITypes.h"
#include "Components/ACFGroupAIComponent.h"
#include "Groups/ACFAIGroupSpawner.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"
#include <Engine/World.h>

// Sets default values for this component's properties
UACFAIWavesMasterComponent::UACFAIWavesMasterComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    // ...
}

// Called when the game starts
void UACFAIWavesMasterComponent::BeginPlay()
{
    Super::BeginPlay();

    // ...
}

void UACFAIWavesMasterComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFAIWavesMasterComponent, currentWaveIndex);
    DOREPLIFETIME(UACFAIWavesMasterComponent, bAreWavesStarted);
}

void UACFAIWavesMasterComponent::StartWave()
{
    if (Internal_StartWave(0)) {
        bAreWavesStarted = true;
    }
}

bool UACFAIWavesMasterComponent::Internal_StartWave(int32 waveIndex)
{
    if (Waves.IsValidIndex(waveIndex)) {
        if (Waves[waveIndex].GroupSpawner) {
            UACFGroupAIComponent* groupComp = Waves[waveIndex].GroupSpawner->GetAIGroupComponent();
            groupComp->ReplaceAIToSpawn(Waves[waveIndex].WaveAgentsOverride);
            groupComp->SetCanSpawnMultitpleTimes(true);
            groupComp->SpawnGroup();
            groupComp->OnAllAgentDeath.AddDynamic(this, &UACFAIWavesMasterComponent::HandleWaveFinished);
            OnWaveStarted.Broadcast(waveIndex);
            return true;
        }
    }
    return false;
}

void UACFAIWavesMasterComponent::HandleWaveFinished()
{
    TerminateCurrentWave();

    if (Waves.IsValidIndex(currentWaveIndex) && Waves[currentWaveIndex].secondsDelayToNextWave > 0.f) {
        FTimerDelegate nextWaveDelegate;
        nextWaveDelegate.BindUObject(this, &UACFAIWavesMasterComponent::ProceedToNextWave);

        GetWorld()->GetTimerManager().SetTimer(nextWaveHandle, nextWaveDelegate,
            Waves[currentWaveIndex].secondsDelayToNextWave, false);
    } else {
        ProceedToNextWave();
    }
}

void UACFAIWavesMasterComponent::TerminateCurrentWave()
{
    if (Waves.IsValidIndex(currentWaveIndex)) {
        if (Waves[currentWaveIndex].GroupSpawner) {
            UACFGroupAIComponent* groupComp = Waves[currentWaveIndex].GroupSpawner->GetAIGroupComponent();
            groupComp->OnAllAgentDeath.RemoveDynamic(this, &UACFAIWavesMasterComponent::HandleWaveFinished);
            OnWaveEnded.Broadcast(currentWaveIndex);
        }
    }
}

void UACFAIWavesMasterComponent::AddAgentToWave_Implementation(int32 waveIndex, TSubclassOf<AACFCharacter> agentClass, int32 count)
{
    if (Waves.IsValidIndex(waveIndex)) {
        Waves[waveIndex].AddAIToSpawn(agentClass, count);
    }
}

void UACFAIWavesMasterComponent::RemoveAgentFromWave_Implementation(int32 waveIndex, TSubclassOf<AACFCharacter> agentClass, int32 count)
{
    if (Waves.IsValidIndex(waveIndex)) {
        Waves[waveIndex].RemoveAIToSpawn(agentClass, count);
    }
}

void UACFAIWavesMasterComponent::ProceedToNextWave_Implementation()
{
    currentWaveIndex++;
    if (bAreWavesStarted && !Internal_StartWave(currentWaveIndex)) {
        OnAllWavesEnded.Broadcast();
        currentWaveIndex = 0;
        bAreWavesStarted = false;
    } else {
        OnWaveProgressed.Broadcast(currentWaveIndex);
    }
}

bool UACFAIWavesMasterComponent::TryGetWaveConfigAtIndex(int32 waveIndex, FWaveConfig& outWaveConfig)
{
    if (Waves.IsValidIndex(waveIndex)) {
        outWaveConfig = Waves[waveIndex];
        return true;
    }
    return false;
}
