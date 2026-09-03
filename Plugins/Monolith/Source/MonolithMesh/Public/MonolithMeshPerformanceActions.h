#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 9: Performance Analysis (5 actions)
 * Budget-aware placement analysis with conservative estimates.
 * No occlusion culling assumed — all estimates trend HIGH for safe budgeting.
 */
class FMonolithMeshPerformanceActions
{
public:
	/** Register all 5 performance analysis actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Region analysis ---
	static FMonolithActionResult GetRegionPerformance(const TSharedPtr<FJsonObject>& Params);

	// --- Pre-placement budgeting ---
	static FMonolithActionResult EstimatePlacementCost(const TSharedPtr<FJsonObject>& Params);

	// --- Overdraw detection ---
	static FMonolithActionResult FindOverdrawHotspots(const TSharedPtr<FJsonObject>& Params);

	// --- Shadow cost audit ---
	static FMonolithActionResult AnalyzeShadowCost(const TSharedPtr<FJsonObject>& Params);

	// --- Triangle budget ---
	static FMonolithActionResult GetTriangleBudget(const TSharedPtr<FJsonObject>& Params);

	// --- Helpers ---
	static TArray<TSharedPtr<FJsonValue>> VectorToJsonArray(const FVector& V);
};
