#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FProjectFindReferencesAction
{
public:
	static FMonolithActionResult Execute(const TSharedPtr<FJsonObject>& Params);
	static FString GetName() { return TEXT("find_references"); }
	static FString GetDescription() { return TEXT("Find all assets that reference or are referenced by the given asset"); }
	static TSharedPtr<FJsonObject> GetSchema();
};
