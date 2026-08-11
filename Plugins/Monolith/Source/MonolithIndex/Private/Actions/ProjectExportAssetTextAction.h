#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FProjectExportAssetTextAction
{
public:
	static FMonolithActionResult Execute(const TSharedPtr<FJsonObject>& Params);
	static FString GetName() { return TEXT("export_asset_text"); }
	static FString GetDescription();
	static TSharedPtr<FJsonObject> GetSchema();
};
