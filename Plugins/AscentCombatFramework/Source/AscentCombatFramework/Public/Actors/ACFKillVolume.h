// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PhysicsVolume.h"

#include "ACFKillVolume.generated.h"


/**
 *
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API AACFKillVolume : public APhysicsVolume {
    GENERATED_BODY()

protected:
    virtual void ActorEnteredVolume(class AActor* Other) override;
};
