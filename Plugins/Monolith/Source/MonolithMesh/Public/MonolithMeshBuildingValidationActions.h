#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * WP-3a: Post-Generation Building Validation
 *
 * Validates that a procedurally generated building is actually playable:
 *   - Door passability (capsule sweeps through openings)
 *   - Room connectivity (BFS over adjacency graph from entrance)
 *   - Window openings (raycasts through expected window positions)
 *   - Stair angle validation (max walkable gradient)
 *
 * Reads from the SP6 Spatial Registry (no mesh generation, no HandlePool).
 *
 * 1 action:
 *   validate_building  -- Full playability validation with per-check breakdown and score
 */
class FMonolithMeshBuildingValidationActions
{
public:
	/** Register all building validation actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// ---- Action Handlers ----
	static FMonolithActionResult ValidateBuilding(const TSharedPtr<FJsonObject>& Params);

	// ---- Sub-Validators ----

	/** Check door passability via capsule sweeps. Returns JSON object with results. */
	static TSharedPtr<FJsonObject> ValidateDoors(
		const struct FSpatialBlock& Block,
		const FString& BuildingId,
		float CapsuleRadius,
		float CapsuleHalfHeight,
		float MinDoorWidth,
		class UWorld* World);

	/** Check room connectivity via BFS from entrance. Returns JSON object with results. */
	static TSharedPtr<FJsonObject> ValidateConnectivity(
		const struct FSpatialBlock& Block,
		const FString& BuildingId);

	/** Check window openings via raycasts. Returns JSON object with results. */
	static TSharedPtr<FJsonObject> ValidateWindows(
		const struct FSpatialBlock& Block,
		const FString& BuildingId,
		class UWorld* World);

	/** Check stair angles. Returns JSON object with results. */
	static TSharedPtr<FJsonObject> ValidateStairs(
		const struct FSpatialBlock& Block,
		const FString& BuildingId,
		float MaxStairAngle);

	// ---- Helpers ----

	/** BFS over the block's adjacency graph from a start room. Returns set of reachable room IDs. */
	static TSet<FString> BFSReachable(
		const struct FSpatialBlock& Block,
		const FString& StartRoomId);

	/** Find the entrance room for a building (first room with an exterior door). */
	static FString FindEntranceRoom(
		const struct FSpatialBlock& Block,
		const FString& BuildingId);

	/** Get all room IDs belonging to a building. */
	static TArray<FString> GetBuildingRoomIds(
		const struct FSpatialBlock& Block,
		const FString& BuildingId);
};
