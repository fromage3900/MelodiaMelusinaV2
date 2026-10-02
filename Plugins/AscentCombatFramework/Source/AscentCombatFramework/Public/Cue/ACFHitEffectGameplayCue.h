// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayCueNotify_Static.h"

#include "ACFHitEffectGameplayCue.generated.h"

/**
 *
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFHitEffectGameplayCue : public UGameplayCueNotify_Static {
    GENERATED_BODY()

public:
    UACFHitEffectGameplayCue();

protected:
    bool OnExecute_Implementation(AActor* Target, const FGameplayCueParameters& Parameters) const;
};
