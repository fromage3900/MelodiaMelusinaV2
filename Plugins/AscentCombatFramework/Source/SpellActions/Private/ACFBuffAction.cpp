// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFBuffAction.h"
#include "ARSStatisticsComponent.h"
#include "Actions/ACFActionAbility.h"
#include "Game/ACFFunctionLibrary.h"

void UACFBuffAction::OnNotablePointReached_Implementation()
{
    Super::OnNotablePointReached_Implementation();
    UARSStatisticsComponent* statComp = GetCharacterOwner()->FindComponentByClass<UARSStatisticsComponent>();
    if (statComp) {
        statComp->AddTimedAttributeSetModifier(BuffToApply.modifier, BuffToApply.duration);
        FComponentFX compFX;
        UACFFunctionLibrary::PlayActionEffectLocally(ActionConfig.ActionEffect, GetCharacterOwner(), this,compFX);
    }
}
