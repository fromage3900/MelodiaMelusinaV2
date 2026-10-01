// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "ACFGatherableSpawner.generated.h"

/**
 * Base C++ class for gatherable spawner actors.
 * Extend this in Blueprint to define world actors that spawn or manage gatherable resources.
 */
UCLASS(Blueprintable, BlueprintType)
class INVENTORYSYSTEM_API AACFGatherableSpawner : public AActor
{
    GENERATED_BODY()

public:
    AACFGatherableSpawner();
};
