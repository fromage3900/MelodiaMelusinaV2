// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Groups/ACFAIWaveMaster.h"
#include "Components/ACFGroupAIComponent.h"
#include "Components/ACFAIWavesMasterComponent.h"

// Sets default values
AACFAIWaveMaster::AACFAIWaveMaster()
{
    // Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    wavesComp = CreateDefaultSubobject<UACFAIWavesMasterComponent>(TEXT("Waves Master"));
}

// Called when the game starts or when spawned
void AACFAIWaveMaster::BeginPlay()
{
    Super::BeginPlay();
}
