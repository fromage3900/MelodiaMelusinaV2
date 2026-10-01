// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayCueNotify_Static.h"

#include "ACFImpactGameplayCue.generated.h"


struct FComponentFX;
/**
 *
 */
UCLASS()
class COLLISIONSMANAGER_API UACFImpactGameplayCue : public UGameplayCueNotify_Static {
    GENERATED_BODY()
public:
    UACFImpactGameplayCue();

protected:
    // This function is called when the gameplay cue is executed
    virtual bool OnExecute_Implementation(AActor* Target, const FGameplayCueParameters& Parameters) const override;
};
