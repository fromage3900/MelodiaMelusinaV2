#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 13: Level Design Quick Wins (9 actions)
 * Lights, materials, mesh swap, LOD, instancing, component property reflection.
 * High-frequency actions for level design sessions.
 */
class FMonolithMeshLevelDesignActions
{
public:
	/** Register all 9 level design actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	/** Spawn point/spot/rect/directional light with full properties */
	static FMonolithActionResult PlaceLight(const TSharedPtr<FJsonObject>& Params);

	/** Modify properties on an existing light actor */
	static FMonolithActionResult SetLightProperties(const TSharedPtr<FJsonObject>& Params);

	/** Assign a material to an actor's mesh component by slot index or name */
	static FMonolithActionResult SetActorMaterial(const TSharedPtr<FJsonObject>& Params);

	/** Bulk replace material X with Y across actors or entire level */
	static FMonolithActionResult SwapMaterialInLevel(const TSharedPtr<FJsonObject>& Params);

	/** Swap all instances of static mesh X with mesh Y */
	static FMonolithActionResult FindReplaceMesh(const TSharedPtr<FJsonObject>& Params);

	/** Set per-LOD screen size thresholds on a static mesh asset */
	static FMonolithActionResult SetLodScreenSizes(const TSharedPtr<FJsonObject>& Params);

	/** Identify meshes used many times that could be HISM-converted */
	static FMonolithActionResult FindInstancingCandidates(const TSharedPtr<FJsonObject>& Params);

	/** Convert grouped StaticMeshActors into a single HISM actor */
	static FMonolithActionResult ConvertToHism(const TSharedPtr<FJsonObject>& Params);

	/** Read arbitrary component properties via FProperty reflection */
	static FMonolithActionResult GetActorComponentProperties(const TSharedPtr<FJsonObject>& Params);

	// --- Helpers ---

	/** Apply light properties from JSON to a light component. Returns list of properties set. */
	static TArray<FString> ApplyLightProperties(class ULightComponent* LightComp, const TSharedPtr<FJsonObject>& Params);
};
