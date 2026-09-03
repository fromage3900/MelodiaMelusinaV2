#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * SP6: Spatial Registry — Hierarchical spatial model for procedurally generated city blocks.
 *
 * Maintains an in-memory registry of blocks → buildings → floors → rooms → openings,
 * with an adjacency graph for BFS pathfinding through doors and stairwells.
 * Persists to JSON files in Saved/Monolith/SpatialRegistry/.
 *
 * 10 actions:
 *   register_building, register_room, register_street_furniture,
 *   query_room_at, query_adjacent_rooms, query_rooms_by_filter,
 *   query_building_exits, path_between_rooms,
 *   save_block_descriptor, load_block_descriptor
 */

// ============================================================================
// Data Structures
// ============================================================================

/** A room in the spatial registry */
struct FSpatialRoom
{
	FString RoomId;
	FString RoomType;
	FString BuildingId;
	int32 FloorIndex = 0;
	FBox WorldBounds = FBox(ForceInit);
	TArray<FString> AdjacentRoomIds;
	TArray<FString> DoorIds;
	TMap<FString, FString> Tags;
};

/** A building in the spatial registry */
struct FSpatialBuilding
{
	FString BuildingId;
	FString AssetPath;
	FVector WorldOrigin = FVector::ZeroVector;
	TArray<FVector2D> FootprintPolygon;
	TMap<int32, TArray<FString>> FloorToRoomIds;
	TArray<FString> ExteriorDoorIds;
};

/** A street furniture item */
struct FSpatialStreetFurniture
{
	FString FurnitureId;
	FString FurnitureType;
	FVector WorldPosition = FVector::ZeroVector;
	FString ActorName;
};

/** An adjacency edge: connected room + the door/stairwell that connects them */
struct FSpatialAdjacencyEdge
{
	FString ConnectedRoomId;
	FString DoorId;
};

/** A door with its spatial context (for building exit queries) */
struct FSpatialDoor
{
	FString DoorId;
	FString Wall;
	FVector WorldPosition = FVector::ZeroVector;
	FString RoomA;
	FString RoomB;
	bool bExterior = false;
	float Width = 90.0f;
	float Height = 220.0f;
};

/** The top-level block containing everything */
struct FSpatialBlock
{
	FString BlockId;
	TMap<FString, FSpatialBuilding> Buildings;
	TMap<FString, FSpatialRoom> Rooms;
	TMap<FString, FSpatialStreetFurniture> Furniture;
	TMap<FString, FSpatialDoor> Doors;

	/** Adjacency graph: room_id -> list of {connected_room_id, door_id} */
	TMap<FString, TArray<FSpatialAdjacencyEdge>> AdjacencyGraph;

	TSharedPtr<FJsonObject> ToJson() const;
	static FSpatialBlock FromJson(const TSharedPtr<FJsonObject>& Json);
};

// ============================================================================
// Action Class
// ============================================================================

class FMonolithMeshSpatialRegistry
{
public:
	/** Register all 10 spatial registry actions */
	static void RegisterActions(FMonolithToolRegistry& Registry);

	/** Access the current in-memory block (session-scoped) */
	static FSpatialBlock& GetBlock(const FString& BlockId = TEXT("default"));

	/** Check if a block exists in memory */
	static bool HasBlock(const FString& BlockId);

	/** Clear a specific block or all blocks */
	static void ClearBlock(const FString& BlockId);
	static void ClearAll();

	/** Get all loaded block IDs */
	static TArray<FString> GetLoadedBlockIds();

	/** Room to compact JSON for query results (public — used by FSpatialBlock::ToJson) */
	static TSharedPtr<FJsonObject> RoomToJson(const FSpatialRoom& Room);

	/** Door to compact JSON for query results (public — used by FSpatialBlock::ToJson) */
	static TSharedPtr<FJsonObject> DoorToJson(const FSpatialDoor& Door);

	/** Create a JSON array from FVector (public — used by FSpatialBlock::ToJson) */
	static TArray<TSharedPtr<FJsonValue>> VecToJsonArray(const FVector& V);

private:
	/** In-memory block storage */
	static TMap<FString, FSpatialBlock>& GetBlockMap();

	/** Get the save directory path */
	static FString GetSaveDirectory();

	/** Ensure the save directory exists */
	static bool EnsureSaveDirectory();

	// ---- Action Handlers ----

	static FMonolithActionResult RegisterBuilding(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult RegisterRoom(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult RegisterStreetFurniture(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult QueryRoomAt(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult QueryAdjacentRooms(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult QueryRoomsByFilter(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult QueryBuildingExits(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult PathBetweenRooms(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SaveBlockDescriptor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult LoadBlockDescriptor(const TSharedPtr<FJsonObject>& Params);

	// ---- Helpers ----

	/** Build adjacency graph edges from a building's doors and stairwells */
	static void BuildAdjacencyFromBuilding(FSpatialBlock& Block, const FString& BuildingId,
		const TSharedPtr<FJsonObject>& BuildingJson, const FVector& BuildingOrigin);

	/** BFS shortest path between two rooms */
	static TArray<FString> BFS(const FSpatialBlock& Block, const FString& StartRoom,
		const FString& EndRoom, const TSet<FString>& AvoidRooms);

	/** Parse a [x,y,z] array from JSON */
	static bool ParseVector(const TSharedPtr<FJsonObject>& Obj, const FString& FieldName, FVector& OutVec);

	/** Parse world_bounds {min: [x,y,z], max: [x,y,z]} from JSON */
	static bool ParseBounds(const TSharedPtr<FJsonObject>& Obj, FBox& OutBox);

};
