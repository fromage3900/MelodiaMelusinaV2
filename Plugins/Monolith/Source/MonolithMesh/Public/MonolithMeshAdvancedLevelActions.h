#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 17: Advanced Level Design (8 actions)
 * Sublevels, BP actor spawning, splines, prefabs (Level Instances),
 * randomize transforms, filtered actor enumeration, distance measurement.
 *
 * set_collision_preset already exists in Phase 14 (VolumeActions) -- skipped here.
 */
class FMonolithMeshAdvancedLevelActions
{
public:
	/** Register all advanced level design actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	/** Create/load/unload sublevels, move actors between levels */
	static FMonolithActionResult ManageSublevel(const TSharedPtr<FJsonObject>& Params);

	/** Spawn a Blueprint actor with exposed property configuration */
	static FMonolithActionResult PlaceBlueprintActor(const TSharedPtr<FJsonObject>& Params);

	/** Spawn an actor with a USplineComponent + optional USplineMeshComponents per segment */
	static FMonolithActionResult PlaceSpline(const TSharedPtr<FJsonObject>& Params);

	/** Create a Level Instance (prefab) from selected actors */
	static FMonolithActionResult CreatePrefab(const TSharedPtr<FJsonObject>& Params);

	/** Create a Blueprint prefab from world actors (dialog-free, MCP-safe) */
	static FMonolithActionResult CreateBlueprintPrefab(const TSharedPtr<FJsonObject>& Params);

	/** Spawn a copy of a saved Level Instance prefab */
	static FMonolithActionResult SpawnPrefab(const TSharedPtr<FJsonObject>& Params);

	/** Apply random offset/rotation/scale variation to actors */
	static FMonolithActionResult RandomizeTransforms(const TSharedPtr<FJsonObject>& Params);

	/** Filtered enumeration of actors in the editor world */
	static FMonolithActionResult GetLevelActors(const TSharedPtr<FJsonObject>& Params);

	/** Measure distance between two actors or world points */
	static FMonolithActionResult MeasureDistance(const TSharedPtr<FJsonObject>& Params);
};
