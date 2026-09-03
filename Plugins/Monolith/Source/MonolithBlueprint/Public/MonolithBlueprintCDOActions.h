#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithBlueprintCDOActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleGetCDOProperties(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetCDOProperty(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetPropertyAtPath(const TSharedPtr<FJsonObject>& Params);
};
