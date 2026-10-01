// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFStatusTypes.h"
#include "StatusEffects/ACFBaseStatusEffect.h"

FStatusEffect::FStatusEffect(UACFBaseStatusEffect* inEffect)
{
    effectInstance = inEffect;
    StatusTag = inEffect->GetStatusEffectTag();
    StatusIcon = inEffect->GetStatusIcon();

}
