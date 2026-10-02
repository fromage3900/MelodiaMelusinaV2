// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "Cue/ACFHitEffectGameplayCue.h"
#include "ACMCollisionsFunctionLibrary.h"
#include "ACMTypes.h"
#include "Logging.h"
#include <Engine/HitResult.h>
#include "Components/ACFEffectsManagerComponent.h"
#include <GameFramework/Character.h>

bool UACFHitEffectGameplayCue::OnExecute_Implementation(AActor* Target, const FGameplayCueParameters& Parameters) const
{
    if (Parameters.EffectContext.IsValid()) {
        const FGameplayEffectContext* BaseContext = Parameters.EffectContext.Get();
        const FACFGameplayEffectContext* acfContext = static_cast<const FACFGameplayEffectContext*>(BaseContext);
        UPhysicalMaterial* PhysMat = acfContext->GetHitResult()->PhysMaterial.Get();
        ACharacter* instigator = Cast<ACharacter>(Parameters.GetInstigator());
        if (!instigator) {
            return false;
        }
        UACFEffectsManagerComponent* effComp = instigator->FindComponentByClass<UACFEffectsManagerComponent>();
        FImpactFX outFX;

        if (effComp && effComp->TryGetDamageFX(acfContext->ActionEffectTag, acfContext->DamageTypeClass,  outFX)) {
            FActionEffect effect(outFX, ESpawnFXLocation::ESpawnAttachedToSocketOrBone, acfContext->GetHitResult()->BoneName);
            UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAttached(effect, instigator);
            return true;
        }
    } else {
        UE_LOG(ACFLog, Error, TEXT("Missing Effect Context! - UACFActionGameplayCue::OnExecute_Implementation"));
    }
    return false;
}

UACFHitEffectGameplayCue::UACFHitEffectGameplayCue()
{
}
