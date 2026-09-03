#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 6: Horror Analysis Actions (8 actions)
 * Spatial analysis for survival horror level design:
 * sightlines, hiding spots, ambush points, choke points,
 * escape routes, tension classification, pacing curves, dead ends.
 */
class FMonolithMeshHorrorActions
{
public:
	/** Register all 8 horror analysis actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult AnalyzeSightlines(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindHidingSpots(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindAmbushPoints(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzeChokePoints(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzeEscapeRoutes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ClassifyZoneTension(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzePacingCurve(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindDeadEnds(const TSharedPtr<FJsonObject>& Params);
};
