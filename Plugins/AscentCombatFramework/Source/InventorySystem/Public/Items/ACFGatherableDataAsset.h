// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFGatherableDataAsset.generated.h"

/**
 * Base C++ class for gatherable resource data assets.
 * Extend this in Blueprint (PDA_Gathereable) to define the properties
 * of resources that can be gathered from the world.
 */
UCLASS(Blueprintable, BlueprintType)
class INVENTORYSYSTEM_API UACFGatherableDataAsset : public UPrimaryDataAsset
{
    GENERATED_BODY()
};
