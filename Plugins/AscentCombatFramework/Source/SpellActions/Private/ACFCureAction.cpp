// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFCureAction.h"
#include "ARSStatisticsComponent.h"
#include "Actions/ACFActionAbility.h"
#include "Actors/ACFCharacter.h"
#include "Game/ACFFunctionLibrary.h"
#include "Game/ACFTypes.h"

void UACFCureAction::OnNotablePointReached_Implementation()
{
    Super::OnNotablePointReached_Implementation();

    AACFCharacter* acfCharacter = Cast<AACFCharacter>(GetCharacterOwner());
    if (acfCharacter && acfCharacter->GetStatisticsComponent()) {
        acfCharacter->GetStatisticsComponent()->ModifyStat(StatModifier);
    }
        PlayEffects();
}

