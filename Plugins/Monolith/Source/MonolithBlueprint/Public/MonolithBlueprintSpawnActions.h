// Copyright Monolith. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithBlueprintSpawnActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleSpawnBlueprintActor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBatchSpawnBlueprintActors(const TSharedPtr<FJsonObject>& Params);
};
