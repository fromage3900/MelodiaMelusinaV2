// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Cues/ACFItemUsedGameplayCue.h"
#include "Items/ACFConsumable.h"
#include "Logging.h"
#include <GameFramework/Character.h>
#include <ACMCollisionsFunctionLibrary.h>

UACFItemUsedGameplayCue::UACFItemUsedGameplayCue()
{
}

bool UACFItemUsedGameplayCue::OnExecute_Implementation(AActor* Target, const FGameplayCueParameters& Parameters) const
{
    if (Parameters.EffectContext.IsValid()) {
        const FGameplayEffectContext* BaseContext = Parameters.EffectContext.Get();
        const FItemUseEffectContext* acfContext = static_cast<const FItemUseEffectContext*>(BaseContext);
        TSubclassOf<UACFConsumable> ItemClass = acfContext->ConsumedItemClass;
        ACharacter* instigator = Cast<ACharacter>(Parameters.GetInstigator());
        if (!instigator) {
            return false;
        }
        if (!ItemClass) {
            return false;
        }

        const UACFConsumable* cons = Cast < UACFConsumable>(ItemClass->GetDefaultObject(true));
        if (cons) {
            FActionEffect effect = cons->GetOnUsedEffect();
            UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAttached(effect, instigator);
            return true;
        }


    } else {
        UE_LOG(ACFInventoryLog, Error, TEXT("Missing Effect Context! - UACFActionGameplayCue::OnExecute_Implementation"));
    }
    return false;
}
