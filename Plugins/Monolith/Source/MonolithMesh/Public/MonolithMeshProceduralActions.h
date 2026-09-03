#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

#if WITH_GEOMETRYSCRIPT

class UMonolithMeshHandlePool;
class UDynamicMesh;

/**
 * Phases 19A-D: Procedural Geometry Actions (GeometryScript)
 * 19A: Parametric furniture + horror prop generation via boolean ops on primitives.
 * 19B: Structures (rooms/corridors/junctions) + building shells + maze generation.
 * 19C: Pipe networks (swept polygon) + mesh fragmentation (plane slice).
 * 19D: Terrain patches (Perlin noise heightmap).
 * 8 actions total: create_parametric_mesh, create_horror_prop, create_structure,
 *   create_building_shell, create_maze, create_pipe_network, create_fragments, create_terrain_patch
 */
class FMonolithMeshProceduralActions
{
public:
	/** Register all procedural geometry actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

	/** Set the handle pool instance (called during module startup) */
	static void SetHandlePool(UMonolithMeshHandlePool* InPool);

	// ---- Shared helpers (public for cross-module use, e.g. FMonolithMeshBuildingActions) ----

	/** Optionally save the built mesh to a UStaticMesh asset. Returns save_path in result. */
	static bool SaveMeshToAsset(UDynamicMesh* Mesh, const FString& SavePath, bool bOverwrite, FString& OutError);

	/** Optionally place a StaticMesh actor in the scene */
	static AActor* PlaceMeshInScene(const FString& AssetPath, const FVector& Location, const FRotator& Rotation, const FString& Label, bool bSnapToFloor = true, const FString& Folder = TEXT(""));

	/** Apply final cleanup: SelfUnion (additive-only) or ComputeSplitNormals (post-boolean) */
	static void CleanupMesh(UDynamicMesh* Mesh, bool bHadBooleans);

private:
	static UMonolithMeshHandlePool* Pool;

	// Action handlers — Phase 19A
	static FMonolithActionResult CreateParametricMesh(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateHorrorProp(const TSharedPtr<FJsonObject>& Params);

	// Action handlers — Phase 19B (Structures + Mazes)
	static FMonolithActionResult CreateStructure(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateBuildingShell(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateMaze(const TSharedPtr<FJsonObject>& Params);

	// Action handlers — Phase 19C (Pipes + Fragments)
	static FMonolithActionResult CreatePipeNetwork(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateFragments(const TSharedPtr<FJsonObject>& Params);

	// Action handlers — Phase 19D (Terrain)
	static FMonolithActionResult CreateTerrainPatch(const TSharedPtr<FJsonObject>& Params);

	// ---- Parametric furniture builders ----
	// Each returns triangle count. Mesh is built in-place on TargetMesh.
	static bool BuildChair(UDynamicMesh* Mesh, float Width, float Depth, float Height, float SeatHeight, float BackHeight, float LegThickness, FString& OutError);
	static bool BuildTable(UDynamicMesh* Mesh, float Width, float Depth, float Height, float LegThickness, float TopThickness, FString& OutError);
	static bool BuildDesk(UDynamicMesh* Mesh, float Width, float Depth, float Height, float LegThickness, float TopThickness, bool bHasDrawer, FString& OutError);
	static bool BuildShelf(UDynamicMesh* Mesh, float Width, float Depth, float Height, int32 ShelfCount, float BoardThickness, FString& OutError);
	static bool BuildCabinet(UDynamicMesh* Mesh, float Width, float Depth, float Height, float WallThickness, float RecessDepth, FString& OutError);
	static bool BuildBed(UDynamicMesh* Mesh, float Width, float Depth, float Height, float MattressHeight, float HeadboardHeight, FString& OutError);
	static bool BuildDoorFrame(UDynamicMesh* Mesh, float Width, float Height, float FrameThickness, float FrameDepth, FString& OutError);
	static bool BuildWindowFrame(UDynamicMesh* Mesh, float Width, float Height, float FrameThickness, float FrameDepth, float SillHeight, FString& OutError);
	static bool BuildStairs(UDynamicMesh* Mesh, float Width, float StepHeight, float StepDepth, int32 StepCount, bool bFloating, FString& OutError);
	static bool BuildRamp(UDynamicMesh* Mesh, float Width, float Depth, float Height, FString& OutError);
	static bool BuildPillar(UDynamicMesh* Mesh, float Radius, float Height, int32 Sides, bool bRound, FString& OutError);
	static bool BuildCounter(UDynamicMesh* Mesh, float Width, float Depth, float Height, float TopThickness, FString& OutError);
	static bool BuildToilet(UDynamicMesh* Mesh, float Width, float Depth, float Height, float BowlDepth, FString& OutError);
	static bool BuildSink(UDynamicMesh* Mesh, float Width, float Depth, float Height, float BowlRadius, float BowlDepth, FString& OutError);
	static bool BuildBathtub(UDynamicMesh* Mesh, float Width, float Depth, float Height, float WallThickness, FString& OutError);

	// ---- Horror prop builders ----
	static bool BuildBarricade(UDynamicMesh* Mesh, float Width, float Height, float Depth, int32 BoardCount, float GapRatio, int32 Seed, FString& OutError);
	static bool BuildDebrisPile(UDynamicMesh* Mesh, float Radius, float Height, int32 PieceCount, int32 Seed, FString& OutError);
	static bool BuildCage(UDynamicMesh* Mesh, float Width, float Depth, float Height, int32 BarCount, float BarRadius, FString& OutError);
	static bool BuildCoffin(UDynamicMesh* Mesh, float Width, float Depth, float Height, float WallThickness, float LidGap, FString& OutError);
	static bool BuildGurney(UDynamicMesh* Mesh, float Width, float Depth, float Height, float LegRadius, FString& OutError);
	static bool BuildBrokenWall(UDynamicMesh* Mesh, float Width, float Height, float Thickness, float NoiseScale, float HoleRadius, int32 Seed, FString& OutError);
	static bool BuildVentGrate(UDynamicMesh* Mesh, float Width, float Height, float Depth, int32 SlotCount, float FrameThickness, FString& OutError);

	// ---- Shared helpers (private) ----

	/** Parse a "dimensions" sub-object, filling defaults from the provided values */
	static void ParseDimensions(const TSharedPtr<FJsonObject>& Params, float& Width, float& Depth, float& Height,
		float DefaultWidth = 100.0f, float DefaultDepth = 100.0f, float DefaultHeight = 100.0f);

	/** Parse a "params" sub-object, returning it (or empty object if absent) */
	static TSharedPtr<FJsonObject> ParseSubParams(const TSharedPtr<FJsonObject>& Params);

	/** Parse an array of [x,y,z] arrays from a JSON field */
	static bool ParseVectorArray(const TSharedPtr<FJsonObject>& Params, const FString& Key, TArray<FVector>& Out);

	/** Parse an array of [x,y] arrays from a JSON field (2D polygon points) */
	static bool ParseVector2DArray(const TSharedPtr<FJsonObject>& Params, const FString& Key, TArray<FVector2D>& Out);

	/** Generate a circle polygon (2D) for sweep profiles */
	static TArray<FVector2D> MakeCirclePolygon(float Radius, int32 Segments);

	/** Inset a 2D polygon by a fixed distance (simple per-edge inward offset) */
	static TArray<FVector2D> InsetPolygon2D(const TArray<FVector2D>& Polygon, float InsetDist);

	/** Common save/place/handle logic used by all procedural actions. Mutates Result JSON. Returns error or empty.
	 *  ActionName/Category are used for cache hash computation and auto-save path generation.
	 *  If MeshPtr is null on entry but Params has use_cache=true, checks cache and may skip generation. */
	static FString FinalizeProceduralMesh(UDynamicMesh* Mesh, const TSharedPtr<FJsonObject>& Params,
		const TSharedPtr<FJsonObject>& Result, const FString& HandleCategory,
		const FString& ActionName = TEXT(""), const FString& Category = TEXT(""));

	// ---- Cache management actions ----
	static FMonolithActionResult ListCachedMeshes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ClearCacheAction(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ValidateCacheAction(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetCacheStatsAction(const TSharedPtr<FJsonObject>& Params);

	static void RegisterCacheActions(FMonolithToolRegistry& Registry);

	// ---- Maze algorithms (pure logic, return wall segment list) ----
	struct FMazeWall { int32 X0, Y0, X1, Y1; }; // Grid coords of cells on either side
	static TArray<FMazeWall> GenerateMaze_RecursiveBacktracker(int32 GridW, int32 GridH, int32 Seed);
	static TArray<FMazeWall> GenerateMaze_Prims(int32 GridW, int32 GridH, int32 Seed);
	static TArray<FMazeWall> GenerateMaze_BinaryTree(int32 GridW, int32 GridH, int32 Seed);
};

#endif // WITH_GEOMETRYSCRIPT
