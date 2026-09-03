#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverAssetActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Asset CRUD
	static FMonolithActionResult HandleCreateStateMachine(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetStateMachine(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListStateMachines(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDeleteStateMachine(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateStateMachine(const TSharedPtr<FJsonObject>& Params);

	// Node Blueprints (Phase 2)
	static FMonolithActionResult HandleCreateNodeBlueprint(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetNodeBlueprint(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListNodeBlueprints(const TSharedPtr<FJsonObject>& Params);
};
