#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FProjectGetSavedAssetStateAction
{
public:
	static FMonolithActionResult Execute(const TSharedPtr<FJsonObject>& Params);
	static FString GetName() { return TEXT("get_saved_asset_state"); }
	static FString GetDescription() { return TEXT("Return disk-backed state for an asset -- class, package, disk path, file size, mtime, dependencies and referencers"); }
	static TSharedPtr<FJsonObject> GetSchema();
};
