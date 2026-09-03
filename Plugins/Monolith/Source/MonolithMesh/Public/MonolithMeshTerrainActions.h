#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

#if WITH_GEOMETRYSCRIPT

class UMonolithMeshHandlePool;
class UDynamicMesh;

/**
 * SP8a: Terrain + Foundations
 * 5 actions for placing buildings on uneven terrain:
 *   sample_terrain_grid     — Grid of downward line traces for height sampling
 *   analyze_building_site   — Slope analysis → foundation strategy selection
 *   create_foundation       — Generate foundation geometry (flat, cut-and-fill, stepped, piers, walkout basement)
 *   create_retaining_wall   — Retaining wall along a terrain cut edge
 *   place_building_on_terrain — Full pipeline: sample → analyze → foundation → adjust building Z
 *
 * Hospice mode: ADA-compliant ramp generation (1:12 slope, 76cm max rise per run, landings, handrails).
 */
class FMonolithMeshTerrainActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);
	static void SetHandlePool(UMonolithMeshHandlePool* InPool);

private:
	static UMonolithMeshHandlePool* Pool;

	// ---- Action handlers ----
	static FMonolithActionResult SampleTerrainGrid(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzeBuildingSite(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateFoundation(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateRetainingWall(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult PlaceBuildingOnTerrain(const TSharedPtr<FJsonObject>& Params);

	// ---- Foundation strategy enum ----
	enum class EFoundationStrategy : uint8
	{
		Flat,
		CutAndFill,
		Stepped,
		Piers,
		WalkoutBasement
	};

	static FString StrategyToString(EFoundationStrategy S);
	static EFoundationStrategy StringToStrategy(const FString& S);

	// ---- Terrain sampling helpers ----
	struct FTerrainSample
	{
		TArray<TArray<float>> Heights;       // [row][col] Z values
		TArray<TArray<FVector>> Normals;     // [row][col] surface normals
		float MinZ = MAX_FLT;
		float MaxZ = -MAX_FLT;
		float AvgZ = 0.0f;
		float HeightDiff = 0.0f;
		float AvgSlopeDegrees = 0.0f;
		FVector AvgNormal = FVector::UpVector;
		FVector SlopeDirection = FVector::ZeroVector;
		float Roughness = 0.0f;
		FVector Center = FVector::ZeroVector;
		int32 GridResX = 0;
		int32 GridResY = 0;
		FVector2D SampleSize = FVector2D::ZeroVector;
		bool bAllHit = true;
	};

	/** Fire an NxM grid of downward traces and accumulate stats */
	static bool SampleTerrain(UWorld* World, const FVector& Center, const FVector2D& Size,
		int32 ResX, int32 ResY, float TraceHeight, float TraceDepth,
		ECollisionChannel Channel, FTerrainSample& OutSample, FString& OutError);

	/** Convert FTerrainSample to JSON */
	static TSharedPtr<FJsonObject> TerrainSampleToJson(const FTerrainSample& Sample);

	/** Parse FTerrainSample from JSON (e.g. from a previous sample_terrain_grid call) */
	static bool ParseTerrainSample(const TSharedPtr<FJsonObject>& Json, FTerrainSample& OutSample, FString& OutError);

	// ---- Site analysis helpers ----
	struct FSiteAnalysis
	{
		EFoundationStrategy Strategy = EFoundationStrategy::Flat;
		float SlopeDegrees = 0.0f;
		float HeightDiff = 0.0f;
		float PadZ = 0.0f;
		bool bNeedsRamp = false;
		float RampRise = 0.0f;
		float RampRun = 0.0f;
		int32 RampSegments = 1;
		float RampWidth = 100.0f;
	};

	/** Analyze terrain samples for a building footprint and select foundation strategy */
	static FSiteAnalysis AnalyzeSite(const TArray<FVector2D>& Footprint,
		const FTerrainSample& Terrain, float FloorHeight, bool bHospiceMode);

	// ---- Foundation geometry builders ----

	/** Generate flat pad foundation */
	static bool BuildFlatPad(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
		float PadZ, float PadThickness, int32 MaterialID, FString& OutError);

	/** Generate cut-and-fill foundation with fill slope on low side */
	static bool BuildCutAndFill(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
		const FTerrainSample& Terrain, float PadZ, float PadThickness, int32 MaterialID, FString& OutError);

	/** Generate stepped foundation (multiple pads at different Z) */
	static bool BuildStepped(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
		const FTerrainSample& Terrain, float PadZ, float StepHeight, int32 MaterialID,
		int32& OutStepCount, FString& OutError);

	/** Generate pier/stilt foundation */
	static bool BuildPiers(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
		const FTerrainSample& Terrain, float PadZ, float PierDiameter, float PierSpacing,
		float PadThickness, int32 MatFoundation, int32 MatPier,
		int32& OutPierCount, FString& OutError);

	/** Generate walkout basement foundation */
	static bool BuildWalkoutBasement(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
		const FTerrainSample& Terrain, float PadZ, float FloorHeight,
		float WallThickness, int32 MaterialID, FString& OutError);

	/** Generate ADA-compliant ramp geometry */
	static bool BuildADARamp(UDynamicMesh* Mesh, float Rise, float Width,
		const FVector& StartPos, const FVector& Direction, int32 MaterialID,
		FString& OutError);

	// ---- Retaining wall helper ----
	static bool BuildRetainingWallGeometry(UDynamicMesh* Mesh, const FVector& Start, const FVector& End,
		const FTerrainSample& Terrain, float Thickness, float CapHeight, int32 MaterialID, FString& OutError);

	// ---- Polygon / math helpers ----

	/** Compute axis-aligned bounding box of a 2D polygon */
	static FBox2D ComputePolygonBounds(const TArray<FVector2D>& Polygon);

	/** Point-in-polygon test (ray casting) */
	static bool IsPointInPolygon(const FVector2D& Point, const TArray<FVector2D>& Polygon);

	/** Get terrain Z at a world XY by bilinear interpolation of sample grid */
	static float InterpolateTerrainZ(const FTerrainSample& Terrain, float WorldX, float WorldY);

	/** Parse a 2D polygon array from JSON */
	static bool ParsePolygon(const TSharedPtr<FJsonObject>& Params, const FString& Key,
		TArray<FVector2D>& Out, FString& OutError);
};

#endif // WITH_GEOMETRYSCRIPT
