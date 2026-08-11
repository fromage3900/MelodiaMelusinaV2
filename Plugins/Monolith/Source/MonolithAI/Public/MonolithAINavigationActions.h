#pragma once

#include "MonolithAIInternal.h"

class UNavigationSystemV1;

class FMonolithAINavigationActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// 143-150: NavSystem / NavMesh config & build
	static FMonolithActionResult HandleGetNavSystemConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetNavMeshConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetNavMeshConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetNavMeshStats(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddNavBoundsVolume(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListNavBoundsVolumes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBuildNavigation(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetNavBuildStatus(const TSharedPtr<FJsonObject>& Params);

	// 151-156: Nav areas, modifiers, links
	static FMonolithActionResult HandleListNavAreas(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCreateNavArea(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddNavModifierVolume(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddNavLinkProxy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureNavLink(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListNavLinks(const TSharedPtr<FJsonObject>& Params);

	// 157-161: Path queries
	static FMonolithActionResult HandleFindPath(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleTestPath(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleProjectPointToNavigation(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetRandomNavigablePoint(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleNavigationRaycast(const TSharedPtr<FJsonObject>& Params);

	// 162-166: Agent config, invokers, crowd, analysis
	static FMonolithActionResult HandleConfigureNavAgent(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddNavInvokerComponent(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetCrowdManagerConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetCrowdManagerConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAnalyzeNavigationCoverage(const TSharedPtr<FJsonObject>& Params);

	// 167-168: Harness support — rebuild + validation
	static FMonolithActionResult HandleRebuildNavigation(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateNavPoints(const TSharedPtr<FJsonObject>& Params);

	// Helpers
	static UWorld* GetNavWorld();
	static FVector ParseVector(const TSharedPtr<FJsonObject>& Params, const FString& FieldName, bool& bOutFound);
	static TArray<TSharedPtr<FJsonValue>> VectorToJsonArray(const FVector& V);

	// Pump the editor world tick in a bounded loop until navmesh generation
	// completes (no remaining build tasks and not in progress) or the deadline
	// elapses. Returns true if generation finished within the budget.
	// Game-thread only; drives async tile generation to completion without a busy-loop.
	static bool WaitForNavGenerationComplete(UWorld* World, UNavigationSystemV1* NavSys, double TimeoutSeconds, int32& OutTicks);
};
