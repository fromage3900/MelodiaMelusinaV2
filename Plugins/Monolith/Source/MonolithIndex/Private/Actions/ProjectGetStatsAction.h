#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FProjectGetStatsAction
{
public:
	static FMonolithActionResult Execute(const TSharedPtr<FJsonObject>& Params);
	static FString GetName() { return TEXT("get_stats"); }
	static FString GetDescription() { return TEXT("Get project index statistics -- total counts by table and asset class breakdown"); }
	static TSharedPtr<FJsonObject> GetSchema();
};
