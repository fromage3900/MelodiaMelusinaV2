// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFMusicComponent.h"
#include "Components/ACFAIManagerComponent.h"
#include <Components/AudioComponent.h>
#include <GameFramework/GameState.h>
#include <Kismet/GameplayStatics.h>
#include <Sound/SoundCue.h>

// Sets default values for this component's properties
UACFMusicComponent::UACFMusicComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
}

void UACFMusicComponent::SetMusicCueByState(USoundCue* musicCue, EBattleState battleState)
{
    MusicCueByState.Add(battleState, musicCue);
}

void UACFMusicComponent::PlayMusicCueByState(EBattleState battleState)
{
    if (!IsLocallyControlled()) {
        return;
	}
    USoundCue* musicToPlay = GetMusicCueByState(battleState);
    if (musicToPlay) {
        StopCurrentMusic();
        StartMusicInternal(musicToPlay);

    } else {
        UE_LOG(LogTemp, Warning, TEXT("Missing music cue! - UACFMusicComponent "));
    }
}

void UACFMusicComponent::StartMusicInternal(USoundCue* musicToPlay)
{
    UAudioComponent* audioComp = UGameplayStatics::SpawnSound2D(this, musicToPlay, VolumeMult, 1.0f, 0.f);
    if (audioComp) {
        audioComp->FadeIn(FadeTime, VolumeMult);
        currentComponent = audioComp;
        currentlyPlayingMusic = musicToPlay;
    }
}

void UACFMusicComponent::StopCurrentMusic()
{
    if (IsValid(currentComponent)) {
        currentComponent->FadeOut(FadeTime, 0.f);
    }
}

void UACFMusicComponent::StartMusicOverride(USoundCue* newMusic)
{
    StopMusic();
    StartMusicInternal(newMusic);
}

void UACFMusicComponent::StopMusicOverride()
{
    StopCurrentMusic();
    StartMusic();
}

class USoundCue* UACFMusicComponent::GetMusicCueByState(EBattleState battleState) const
{
    if (MusicCueByState.Contains(battleState)) {
        return *MusicCueByState.Find(battleState);
    }
    return nullptr;
}

// Called when the game starts
void UACFMusicComponent::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoStart && IsLocallyControlled()) {
        StartMusic();
    }
}

void UACFMusicComponent::EndPlay(EEndPlayReason::Type reason)
{
    TObjectPtr<AGameStateBase> gameState = UGameplayStatics::GetGameState(this);
    if (gameState) {
        TObjectPtr<UACFAIManagerComponent> aiManager = gameState->FindComponentByClass<UACFAIManagerComponent>();
        if (aiManager) {
            aiManager->OnBattleStateChanged.RemoveDynamic(this, &UACFMusicComponent::HandleStateChanged);
        }
    }
    Super::EndPlay(reason);
}

void UACFMusicComponent::StartMusic()
{
    if (!IsLocallyControlled()) {
        return;
	}
    TObjectPtr<AGameStateBase> gameState = UGameplayStatics::GetGameState(this);
    if (gameState) {
        TObjectPtr<UACFAIManagerComponent> aiManager = gameState->FindComponentByClass<UACFAIManagerComponent>();
        if (aiManager) {
            if (!aiManager->OnBattleStateChanged.IsAlreadyBound(this, &UACFMusicComponent::HandleStateChanged)) {
                aiManager->OnBattleStateChanged.AddDynamic(this, &UACFMusicComponent::HandleStateChanged);
            }
            PlayMusicCueByState(aiManager->GetBattleState());
            bIsStarted = true;
        }
    } else {
        UE_LOG(LogTemp, Warning, TEXT("Missing ACFGameState! - UACFMusicComponent "));
    }
}

bool UACFMusicComponent::IsLocallyControlled() const
{
    // Get the owning player controller
    APlayerController* ownerPC = Cast<APlayerController>(GetOwner());
    if (!ownerPC)
    {
        UE_LOG(LogTemp, Warning, TEXT("MusicComponent owner is not a PlayerController!"));
        return false;
    }

    // Only play audio on the local player controller
    // This prevents other players' controllers from playing music
    return ownerPC->IsLocalPlayerController();
}

void UACFMusicComponent::StopMusic()
{
    StopCurrentMusic();
    bIsStarted = false;
}

void UACFMusicComponent::HandleStateChanged(const EBattleState& battleState)
{
    if (bIsStarted) {
        PlayMusicCueByState(battleState);
    }
}
