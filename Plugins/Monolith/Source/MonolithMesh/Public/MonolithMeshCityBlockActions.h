#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

#if WITH_GEOMETRYSCRIPT

class UMonolithMeshHandlePool;
class UDynamicMesh;

/**
 * SP5: City Block Layout — orchestrates SP1-SP6 to generate a complete city block.
 *
 * 4 actions:
 *   - create_city_block:     Top-level orchestrator — subdivide, build, facades, roofs, streets, furniture
 *   - create_lot_layout:     Standalone lot subdivision (OBB recursive, grid, or organic)
 *   - create_street:         Generate street geometry (sidewalks, road surface, curbs)
 *   - place_street_furniture: Place lamps, hydrants, benches, etc. along streets
 *
 * All downstream SP calls go through FMonolithToolRegistry::ExecuteAction so SP5 stays
 * decoupled from SP1/SP2/SP3/SP4/SP6 — graceful skip when actions don't exist.
 */
class FMonolithMeshCityBlockActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);
	static void SetHandlePool(UMonolithMeshHandlePool* InPool);

private:
	static UMonolithMeshHandlePool* Pool;

	// ---- Action handlers ----
	static FMonolithActionResult CreateCityBlock(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateLotLayout(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateStreet(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult PlaceStreetFurniture(const TSharedPtr<FJsonObject>& Params);

	// ============================================================================
	// Lot Subdivision
	// ============================================================================

	/** A single lot within a block */
	struct FBlockLot
	{
		int32 LotIndex = 0;
		float X = 0.0f;        // Block-local X
		float Y = 0.0f;        // Block-local Y
		float Width = 0.0f;
		float Height = 0.0f;
		float Rotation = 0.0f; // Degrees
		bool bCornerLot = false;

		TSharedPtr<FJsonObject> ToJson() const
		{
			auto J = MakeShared<FJsonObject>();
			J->SetNumberField(TEXT("index"), LotIndex);
			J->SetNumberField(TEXT("x"), X);
			J->SetNumberField(TEXT("y"), Y);
			J->SetNumberField(TEXT("width"), Width);
			J->SetNumberField(TEXT("height"), Height);
			J->SetNumberField(TEXT("rotation"), Rotation);
			J->SetBoolField(TEXT("corner_lot"), bCornerLot);
			return J;
		}
	};

	/** A street segment between lots or at block edges */
	struct FStreetSegment
	{
		FVector2D Start = FVector2D::ZeroVector;
		FVector2D End = FVector2D::ZeroVector;
		float Width = 600.0f;

		TSharedPtr<FJsonObject> ToJson() const
		{
			auto J = MakeShared<FJsonObject>();
			TArray<TSharedPtr<FJsonValue>> S, E;
			S.Add(MakeShared<FJsonValueNumber>(Start.X));
			S.Add(MakeShared<FJsonValueNumber>(Start.Y));
			E.Add(MakeShared<FJsonValueNumber>(End.X));
			E.Add(MakeShared<FJsonValueNumber>(End.Y));
			J->SetArrayField(TEXT("start"), S);
			J->SetArrayField(TEXT("end"), E);
			J->SetNumberField(TEXT("width"), Width);
			return J;
		}
	};

	/** OBB recursive subdivision: split a rect into N lots */
	static TArray<FBlockLot> SubdivideOBBRecursive(
		float OriginX, float OriginY, float Width, float Height,
		int32 TargetCount, float MinWidth, float MinHeight,
		float Irregularity, FRandomStream& Rng, int32& LotCounter);

	/** Grid subdivision: uniform grid of lots */
	static TArray<FBlockLot> SubdivideGrid(
		float OriginX, float OriginY, float Width, float Height,
		int32 TargetCount, float MinWidth, float MinHeight,
		int32& LotCounter);

	/** Organic subdivision: Poisson-disk sampled, irregular lots */
	static TArray<FBlockLot> SubdivideOrganic(
		float OriginX, float OriginY, float Width, float Height,
		int32 TargetCount, float MinWidth, float MinHeight,
		FRandomStream& Rng, int32& LotCounter);

	// ============================================================================
	// Building Footprint Generation
	// ============================================================================

	/** Generate a building footprint polygon within a lot (respecting setbacks) */
	static TArray<FVector2D> GenerateFootprint(
		const FBlockLot& Lot, const FString& ShapeType,
		float FillRatio, FRandomStream& Rng);

	/** Choose a random footprint shape based on genre-weighted probabilities */
	static FString ChooseFootprintShape(const FString& Genre, FRandomStream& Rng);

	// ============================================================================
	// Street Geometry
	// ============================================================================

	/** Build a road surface mesh (flat plane between curbs) */
	static void BuildRoadSurface(UDynamicMesh* Mesh, const FVector2D& Start, const FVector2D& End,
		float RoadWidth, float Z);

	/** Build sidewalk + curb geometry along one side of a street */
	static void BuildSidewalk(UDynamicMesh* Mesh, const FVector2D& Start, const FVector2D& End,
		float SidewalkWidth, float CurbHeight, float OffsetFromCenter, bool bLeftSide, float Z);

	// ============================================================================
	// Preset Loading
	// ============================================================================

	/** Get the block presets directory */
	static FString GetPresetsDirectory();

	/** Load a block preset JSON by name. Returns false on failure. */
	static bool LoadPreset(const FString& PresetName, TSharedPtr<FJsonObject>& OutPreset, FString& OutError);

	/** Apply preset values as defaults to a params object (doesn't overwrite user-specified values) */
	static void ApplyPresetDefaults(const TSharedPtr<FJsonObject>& Preset, const TSharedPtr<FJsonObject>& Params);

	// ============================================================================
	// Decay System
	// ============================================================================

	/** Apply horror decay to a building (tilt, skip walls, board windows) */
	static void ApplyBuildingDecay(float DecayLevel, int32 BuildingIndex,
		const TSharedPtr<FJsonObject>& BuildingResult, FRandomStream& Rng,
		TArray<FString>& OutSkippedBuildings);

	// ============================================================================
	// Genre Archetype Mapping
	// ============================================================================

	/** Get default building archetypes for a genre */
	static TArray<FString> GetGenreArchetypes(const FString& Genre, int32 BuildingCount, FRandomStream& Rng);

	/** Get default furniture types for a genre */
	static TArray<FString> GetGenreFurniture(const FString& Genre);

	// ============================================================================
	// Helper: Call downstream SP action via registry (returns success + result or logs skip)
	// ============================================================================

	static bool TryExecuteAction(const FString& Action, const TSharedPtr<FJsonObject>& Params,
		TSharedPtr<FJsonObject>& OutResult, FString& OutError);
};

#endif // WITH_GEOMETRYSCRIPT
