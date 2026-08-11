#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASInspectActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 3: export_gas_manifest (moved from Phase 4 — operates on assets, not runtime)
	static FMonolithActionResult HandleExportGASManifest(const TSharedPtr<FJsonObject>& Params);
	// Phase 4: Runtime Debug
	static FMonolithActionResult HandleSnapshotGASState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetTagState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetCooldownState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleTraceAbilityActivation(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCompareGASStates(const TSharedPtr<FJsonObject>& Params);
};
