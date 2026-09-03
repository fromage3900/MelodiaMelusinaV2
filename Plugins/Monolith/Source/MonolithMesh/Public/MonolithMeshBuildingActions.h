#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"
#include "MonolithMeshBuildingTypes.h"

#if WITH_GEOMETRYSCRIPT

class UMonolithMeshHandlePool;
class UDynamicMesh;

/**
 * SP1: Grid-Based Building Construction
 * Takes a 2D grid of room IDs + door edge positions → generates geometry AND a Building Descriptor JSON.
 * The descriptor is the interface contract for all downstream sub-projects (SP2-SP10).
 */
class FMonolithMeshBuildingActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);
	static void SetHandlePool(UMonolithMeshHandlePool* InPool);

private:
	static UMonolithMeshHandlePool* Pool;

	// Action handlers
	static FMonolithActionResult CreateBuildingFromGrid(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateGridFromRooms(const TSharedPtr<FJsonObject>& Params);

	// ---- Internal helpers ----

	/** Wall segment: a merged run of grid edges between two different room IDs */
	struct FWallSegment
	{
		int32 FixedAxis;       // The grid coordinate on the fixed axis (X for vertical, Y for horizontal)
		int32 RunStart;        // Start position on the run axis
		int32 RunEnd;          // End position on the run axis (exclusive)
		int32 LeftId;          // Room ID on left/top side
		int32 RightId;         // Room ID on right/bottom side
		bool bVertical;        // true = wall runs along Y (fixed X), false = runs along X (fixed Y)
		bool bExterior;        // One side is empty (-1)
	};

	/** Parse the 2D grid from JSON array-of-arrays */
	static bool ParseGrid(const TSharedPtr<FJsonObject>& Params, TArray<TArray<int32>>& OutGrid,
		int32& OutGridW, int32& OutGridH, FString& OutError);

	/** Parse rooms array from JSON */
	static bool ParseRooms(const TArray<TSharedPtr<FJsonValue>>& RoomsArr, TArray<FRoomDef>& OutRooms, FString& OutError);

	/** Parse doors array from JSON */
	static bool ParseDoors(const TArray<TSharedPtr<FJsonValue>>& DoorsArr, TArray<FDoorDef>& OutDoors, FString& OutError);

	/** Parse stairwells array from JSON */
	static bool ParseStairwells(const TArray<TSharedPtr<FJsonValue>>& StairArr, TArray<FStairwellDef>& OutStairwells, FString& OutError);

	/** Walk grid edges and produce merged wall segments. Skips edges covered by doors. */
	static TArray<FWallSegment> BuildWallSegments(const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH,
		const TArray<FDoorDef>& Doors);

	/** Check if a specific grid edge is covered by a door */
	static bool IsDoorEdge(int32 FixedAxis, int32 RunPos, bool bVertical, const TArray<FDoorDef>& Doors);

	/** Generate wall geometry for all segments on one floor */
	static void GenerateWallGeometry(UDynamicMesh* Mesh, const TArray<FWallSegment>& Segments,
		float CellSize, float FloorHeight, float FloorZ, float ExteriorT, float InteriorT,
		TArray<FExteriorFaceDef>& OutExteriorFaces, int32 FloorIndex,
		const TArray<FRoomDef>& Rooms, bool bOmitExteriorWalls = false);

	/** Generate floor/ceiling slabs per room, skipping stairwell cells */
	static void GenerateSlabs(UDynamicMesh* Mesh, const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH,
		float CellSize, float SlabThickness, float ZPosition, int32 MaterialId, bool bSkipStairwells);

	/** Boolean-subtract door openings from wall geometry */
	static void CutDoorOpenings(UDynamicMesh* Mesh, const TArray<FDoorDef>& Doors,
		float CellSize, float FloorZ, float ExteriorT, float InteriorT,
		const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH, bool& bHadBooleans);

	/** Add trim frames around door openings */
	static void AddDoorTrim(UDynamicMesh* Mesh, const TArray<FDoorDef>& Doors,
		float CellSize, float FloorZ, float ExteriorT, float InteriorT,
		const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH);

	/** Generate stair geometry for stairwells (skips elevator-type shafts) */
	static void GenerateStairGeometry(UDynamicMesh* Mesh, const TArray<FStairwellDef>& Stairwells,
		float CellSize, float FloorHeight, float FloorZ, float StairWidth);

	/** Generate entrance door frame geometry for exterior doors (WP-3) */
	static void GenerateEntranceDoorFrames(UDynamicMesh* Mesh, const TArray<FDoorDef>& Doors,
		float CellSize, float FloorZ, float ExteriorT,
		const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH);

	/** Compute world bounds for all rooms based on grid cell positions */
	static void ComputeRoomBounds(TArray<FRoomDef>& Rooms, float CellSize, float FloorHeight, float FloorZ, const FVector& WorldOrigin);

	/** Compute world positions for all doors */
	static void ComputeDoorPositions(TArray<FDoorDef>& Doors, float CellSize, float FloorZ, const FVector& WorldOrigin,
		const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH);

	/** Build footprint polygon from the outermost grid edges */
	static TArray<FVector2D> ComputeFootprint(const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH, float CellSize);

	/** Generate integrated facade (walls + windows) for one floor's exterior faces.
	 *  Called from CreateBuildingFromGrid when facade_style is provided. */
	static void GenerateIntegratedFacade(UDynamicMesh* Mesh,
		const TArray<FExteriorFaceDef>& ExteriorFaces, float WallThickness,
		const FString& FacadeStyleName, int32 Seed, int32 MaxFloorIndex,
		FBuildingDescriptor& Descriptor, bool& bHadBooleans);
};

#endif // WITH_GEOMETRYSCRIPT
