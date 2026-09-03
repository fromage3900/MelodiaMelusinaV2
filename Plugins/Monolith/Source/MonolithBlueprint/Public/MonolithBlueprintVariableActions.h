#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithBlueprintVariableActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleAddVariable(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveVariable(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRenameVariable(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetVariableType(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetVariableDefaults(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddLocalVariable(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveLocalVariable(const TSharedPtr<FJsonObject>& Params);

	// Wave 7 — Advanced
	static FMonolithActionResult HandleAddReplicatedVariable(const TSharedPtr<FJsonObject>& Params);
};
