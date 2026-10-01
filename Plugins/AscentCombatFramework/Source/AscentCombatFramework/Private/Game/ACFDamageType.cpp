// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Game/ACFDamageType.h"

UACFDamageType::UACFDamageType()
{
    StaggerMutliplier = 1.f;
    bAffectedByImmortality = false;
}

USpellDamageType::USpellDamageType()
{
    bAffectedByImmortality = true;
}
