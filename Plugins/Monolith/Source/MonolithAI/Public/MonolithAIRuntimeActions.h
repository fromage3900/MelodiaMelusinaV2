#pragma once

#include "MonolithAIInternal.h"

class FMonolithAIRuntimeActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Blackboard (167-169)
	static FMonolithActionResult HandleRuntimeGetBBValue(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeSetBBValue(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeClearBBValue(const TSharedPtr<FJsonObject>& Params);

	// Behavior Tree (170-173)
	static FMonolithActionResult HandleRuntimeGetBTState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeStartBT(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeStopBT(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeGetBTExecutionPath(const TSharedPtr<FJsonObject>& Params);

	// Perception (174-176)
	static FMonolithActionResult HandleRuntimeGetPerceivedActors(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeCheckPerception(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeReportNoise(const TSharedPtr<FJsonObject>& Params);

	// StateTree (177-178)
	static FMonolithActionResult HandleRuntimeGetSTActiveStates(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRuntimeSendSTEvent(const TSharedPtr<FJsonObject>& Params);

	// Smart Objects (179)
	static FMonolithActionResult HandleRuntimeFindSmartObjects(const TSharedPtr<FJsonObject>& Params);

	// EQS (180)
	static FMonolithActionResult HandleRuntimeRunEQSQuery(const TSharedPtr<FJsonObject>& Params);
};
