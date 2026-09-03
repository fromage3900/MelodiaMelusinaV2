#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverRuntimeActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Runtime inspection/control (Phase 3)
	static FMonolithActionResult HandleRuntimeGetSMState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeStartSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeStopSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeRestartSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeSwitchState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeEvaluateTransitions(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeGetStateHistory(const TSharedPtr<FJsonObject>& Params);
};
