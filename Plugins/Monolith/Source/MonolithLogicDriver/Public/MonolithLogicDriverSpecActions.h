#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverSpecActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Import/Export/Spec (Phase 2-3)
	static FMonolithActionResult HandleExportSMJson(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleImportSMJson(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBuildSMFromSpec(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleExportSMSpec(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCompareStateMachines(const TSharedPtr<FJsonObject>& Params);
};
