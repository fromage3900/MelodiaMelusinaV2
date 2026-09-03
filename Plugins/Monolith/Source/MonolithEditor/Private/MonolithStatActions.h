#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FJsonObject;

// Gap 10: programmatic stat-group readout (editor namespace).
//
//   get_stat_group_values — enable a stat group, settle one or more frames, and read back the
//                           group's counter values (int64 / double) and cycle-stat timings (ms)
//                           into a structured response.
//
// The entire readout path depends on the engine STATS system being compiled in (the STATS macro
// is defined in Development editor builds — our target — but NOT in Shipping/Test). The handler
// body is #if STATS gated and returns a clean "stats system not compiled in this build
// configuration" error off-gate.
class FMonolithStatActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleGetStatGroupValues(const TSharedPtr<FJsonObject>& Params);
};
