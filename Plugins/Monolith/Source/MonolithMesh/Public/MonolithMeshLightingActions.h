#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 7: Lighting Analysis Actions (5 actions)
 * Hybrid scene capture + analytic lighting analysis.
 * Measures actual illumination including Lumen GI via scene capture,
 * with analytic fallback for light attribution (which light dominates a point).
 */
class FMonolithMeshLightingActions
{
public:
	/** Register all 5 lighting analysis actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	/** Sample light levels at specified points (capture/analytic/both) */
	static FMonolithActionResult SampleLightLevels(const TSharedPtr<FJsonObject>& Params);

	/** Find contiguous dark regions in a volume */
	static FMonolithActionResult FindDarkCorners(const TSharedPtr<FJsonObject>& Params);

	/** Analyze light transitions along a path, flag harsh changes */
	static FMonolithActionResult AnalyzeLightTransitions(const TSharedPtr<FJsonObject>& Params);

	/** Room-level lighting coverage audit */
	static FMonolithActionResult GetLightCoverage(const TSharedPtr<FJsonObject>& Params);

	/** Suggest light placements for a given mood */
	static FMonolithActionResult SuggestLightPlacement(const TSharedPtr<FJsonObject>& Params);
};
