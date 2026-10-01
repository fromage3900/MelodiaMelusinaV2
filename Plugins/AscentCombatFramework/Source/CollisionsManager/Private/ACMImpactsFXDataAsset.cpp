// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACMImpactsFXDataAsset.h"
#include "ACMTypes.h"



bool UACMImpactsFXDataAsset::TryGetImpactFX(const TSubclassOf<class UDamageType>& damageImpacting, class UPhysicalMaterial* materialImpacted, FBaseFX& outFXtoPlay) const
{
    if (ImpactFXsByDamageType.Contains(damageImpacting)) {
        const FImpactsArray& impacts = ImpactFXsByDamageType.FindChecked(damageImpacting);

        if (impacts.ImpactsFX.Contains(materialImpacted)) {
            const FMaterialImpactFX* matfx = impacts.ImpactsFX.FindByKey(materialImpacted);
            outFXtoPlay = FBaseFX(matfx->ActionSound, matfx->NiagaraParticle, matfx->ActionParticle);
            return true;
        }
    } else {
        // IF WE DON'T FIND THAT DAMAGE TYPE, WE TRY HIS CHILD CLASSES
        for (auto& impfx : ImpactFXsByDamageType) {
            if (damageImpacting->IsChildOf(impfx.Key)) {
                const FImpactsArray& impacts = ImpactFXsByDamageType.FindChecked(impfx.Key);
                const FMaterialImpactFX* matfx = impacts.ImpactsFX.FindByKey(materialImpacted);
                outFXtoPlay = FBaseFX(matfx->ActionSound, matfx->NiagaraParticle, matfx->ActionParticle);
                return true;
            }
        }
    }
    return false;
}
