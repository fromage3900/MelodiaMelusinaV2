// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFMusicVolume.h"
#include "ACFMusicComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

AACFMusicVolume::AACFMusicVolume()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = false;
}

void AACFMusicVolume::BeginPlay()
{
    Super::BeginPlay();

    OnActorBeginOverlap.AddDynamic(this, &AACFMusicVolume::HandleBeginOverlap);
    OnActorEndOverlap.AddDynamic(this, &AACFMusicVolume::HandleEndOverlap);
}

void AACFMusicVolume::HandleBeginOverlap(AActor* OverlappedActor, AActor* OtherActor)
{
    APawn* Pawn = Cast<APawn>(OtherActor);
    if (!Pawn)
    {
        return;
    }

    APlayerController* PC = Cast<APlayerController>(Pawn->GetController());
    if (!PC)
    {
        return;
    }

    UACFMusicComponent* MusicComp = PC->FindComponentByClass<UACFMusicComponent>();
    if (MusicComp && MusicOverride)
    {
        MusicComp->StartMusicOverride(MusicOverride);
    }
}

void AACFMusicVolume::HandleEndOverlap(AActor* OverlappedActor, AActor* OtherActor)
{
    APawn* Pawn = Cast<APawn>(OtherActor);
    if (!Pawn)
    {
        return;
    }

    APlayerController* PC = Cast<APlayerController>(Pawn->GetController());
    if (!PC)
    {
        return;
    }

    UACFMusicComponent* MusicComp = PC->FindComponentByClass<UACFMusicComponent>();
    if (MusicComp)
    {
        MusicComp->StopMusicOverride();
    }
}
