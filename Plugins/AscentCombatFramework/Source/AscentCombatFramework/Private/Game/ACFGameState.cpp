// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "Game/ACFGameState.h"
#include "ACFDifficultyManagerComponent.h"
#include "ACMEffectsDispatcherComponent.h"
#include "AIController.h"
#include "Components/ACFTeamManagerComponent.h"



AACFGameState::AACFGameState()
{
	EffectsComp = CreateDefaultSubobject<UACMEffectsDispatcherComponent>(TEXT("ACF Effects Component"));
	TeamManagerComponent = CreateDefaultSubobject<UACFTeamManagerComponent>(TEXT("ACF Team Manager"));
	DifficultyManagerComponent = CreateDefaultSubobject<UACFDifficultyManagerComponent>(TEXT("ACF Difficulty Manager"));
}

