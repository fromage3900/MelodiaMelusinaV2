// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Cues/ACFImpactGameplayCue.h"
#include "ACMCollisionsFunctionLibrary.h"
#include "ACMEffectsDispatcherComponent.h"
#include "ACMTypes.h"
#include "Logging.h"
#include <Engine/HitResult.h>


UACFImpactGameplayCue::UACFImpactGameplayCue()
{
}
bool UACFImpactGameplayCue::OnExecute_Implementation(AActor* Target, const FGameplayCueParameters& Parameters) const
{
    if (Parameters.EffectContext.IsValid()) {
        const FGameplayEffectContext* BaseContext = Parameters.EffectContext.Get();
        const FACFGameplayEffectContext* acfContext = static_cast<const FACFGameplayEffectContext*>(BaseContext);
        UACMEffectsDispatcherComponent* effComp = UACMCollisionsFunctionLibrary::GetEffectDispatcher(Target);
        UPhysicalMaterial* PhysMat = acfContext->GetHitResult()->PhysMaterial.Get();

        FBaseFX outFX;
       
        if (Parameters.GetInstigator() && effComp->TryGetImpactFX(acfContext->DamageTypeClass, PhysMat, outFX)) {
            FImpactFX effect = FImpactFX(outFX, acfContext->GetHitResult()->ImpactPoint);
            FComponentFX outComps;
            UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAtLocation(Target, effect,outComps);
            return true;
        }
    } else {
        UE_LOG(ACFCollisionsLog, Error, TEXT("Missing Effect Context! - UACFActionGameplayCue::OnExecute_Implementation"));
    }
    return false;
}
