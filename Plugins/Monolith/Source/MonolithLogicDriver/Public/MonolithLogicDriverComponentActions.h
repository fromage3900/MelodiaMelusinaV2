#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverComponentActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Component management (Phase 1 read, Phase 2-3 write)
	static FMonolithActionResult HandleGetSMComponentConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddSMComponent(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureSMComponent(const TSharedPtr<FJsonObject>& Params);
};
