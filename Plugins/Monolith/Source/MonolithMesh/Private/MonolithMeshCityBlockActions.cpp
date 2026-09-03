#if WITH_GEOMETRYSCRIPT

#include "MonolithMeshCityBlockActions.h"
#include "MonolithMeshFloorPlanGenerator.h"
#include "MonolithMeshProceduralActions.h"
#include "MonolithMeshHandlePool.h"
#include "MonolithMeshUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"
#include "MonolithAssetUtils.h"

#include "UDynamicMesh.h"
#include "DynamicMesh/DynamicMesh3.h"

#include "GeometryScript/MeshPrimitiveFunctions.h"
#include "GeometryScript/MeshNormalsFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "GeometryScript/MeshTransformFunctions.h"

#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Editor.h"
#include "Misc/FileHelper.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

using namespace UE::Geometry;

DECLARE_LOG_CATEGORY_EXTERN(LogMonolithCityBlock, Log, All);
DEFINE_LOG_CATEGORY(LogMonolithCityBlock);

UMonolithMeshHandlePool* FMonolithMeshCityBlockActions::Pool = nullptr;

void FMonolithMeshCityBlockActions::SetHandlePool(UMonolithMeshHandlePool* InPool)
{
	Pool = InPool;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshCityBlockActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. create_city_block — top-level orchestrator
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_city_block"),
		TEXT("Generate a complete city block: subdivide into lots, build each building (floor plan + walls + facades + roofs), "
			"create streets with sidewalks and curbs, place street furniture, apply horror decay, and register everything in the spatial registry. "
			"Each step is also available as a standalone action for finer control."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshCityBlockActions::CreateCityBlock),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("save_path_prefix"), TEXT("Base path for all generated assets (e.g. /Game/CityBlock/Block_01)"))
			.Optional(TEXT("buildings"), TEXT("integer"), TEXT("Number of buildings"), TEXT("4"))
			.Optional(TEXT("block_size"), TEXT("array"), TEXT("[width, height] in cm"), TEXT("[6000,4000]"))
			.Optional(TEXT("genre"), TEXT("string"), TEXT("horror, suburban, downtown"), TEXT("horror"))
			.Optional(TEXT("seed"), TEXT("integer"), TEXT("Random seed (default: random)"))
			.Optional(TEXT("decay"), TEXT("number"), TEXT("Horror decay level 0-1"), TEXT("0.3"))
			.Optional(TEXT("street_width"), TEXT("number"), TEXT("Street width in cm"), TEXT("600"))
			.Optional(TEXT("sidewalk_width"), TEXT("number"), TEXT("Sidewalk width in cm"), TEXT("200"))
			.Optional(TEXT("min_building_gap"), TEXT("number"), TEXT("Minimum gap between buildings in cm"), TEXT("100"))
			.Optional(TEXT("archetypes"), TEXT("array"), TEXT("Override building archetypes array"))
			.Optional(TEXT("hospice_mode"), TEXT("boolean"), TEXT("ADA-compliant buildings"), TEXT("false"))
			.Optional(TEXT("preset"), TEXT("string"), TEXT("Block preset name to load defaults from"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x,y,z] for block origin"))
			.OptionalAssetPathWithDefault(TEXT("folder"), TEXT("Outliner folder"), TEXT("CityBlock"))
			.Optional(TEXT("skip_facades"), TEXT("boolean"), TEXT("Skip facade generation"), TEXT("false"))
			.Optional(TEXT("skip_roofs"), TEXT("boolean"), TEXT("Skip roof generation"), TEXT("false"))
			.Optional(TEXT("skip_streets"), TEXT("boolean"), TEXT("Skip street generation"), TEXT("false"))
			.Optional(TEXT("skip_furniture"), TEXT("boolean"), TEXT("Skip street furniture"), TEXT("false"))
			.Optional(TEXT("skip_validation"), TEXT("boolean"), TEXT("Skip post-generation validation for faster iteration"), TEXT("false"))
			.Optional(TEXT("validate_and_retry"), TEXT("boolean"), TEXT("Retry buildings that fail validation (score < 0.5) with different seeds, max 2 retries"), TEXT("false"))
			.Optional(TEXT("skip_furnishing"), TEXT("boolean"), TEXT("Skip interior furnishing"), TEXT("false"))
			.Optional(TEXT("skip_volumes"), TEXT("boolean"), TEXT("Skip navmesh/audio volume generation"), TEXT("false"))
			.Optional(TEXT("use_templates"), TEXT("boolean"), TEXT("Use template-based floor plans when available (false = algorithmic treemap only)"), TEXT("true"))
			.Build());

	// 2. create_lot_layout — standalone subdivision
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_lot_layout"),
		TEXT("Subdivide a rectangular block into building lots using OBB recursive, grid, or organic subdivision. "
			"Returns lot positions and generated street segments. Does NOT generate buildings — use create_city_block for full pipeline."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshCityBlockActions::CreateLotLayout),
		FParamSchemaBuilder()
			.Required(TEXT("block_size"), TEXT("array"), TEXT("[width, height] in cm"))
			.Required(TEXT("lot_count"), TEXT("integer"), TEXT("Number of lots to subdivide into"))
			.Optional(TEXT("seed"), TEXT("integer"), TEXT("Random seed"))
			.Optional(TEXT("min_lot_size"), TEXT("array"), TEXT("[min_width, min_height] in cm"), TEXT("[800,600]"))
			.Optional(TEXT("street_width"), TEXT("number"), TEXT("Reserve width for streets between lots"), TEXT("600"))
			.Optional(TEXT("algorithm"), TEXT("string"), TEXT("obb_recursive, grid, organic"), TEXT("obb_recursive"))
			.Build());

	// 3. create_street — street geometry
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_street"),
		TEXT("Generate street geometry: road surface, sidewalks, and curbs as a single static mesh. "
			"Curbs are 15cm raised edges. Sidewalks are flat raised surfaces on each side."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshCityBlockActions::CreateStreet),
		FParamSchemaBuilder()
			.Required(TEXT("start"), TEXT("array"), TEXT("[x, y] start point"))
			.Required(TEXT("end"), TEXT("array"), TEXT("[x, y] end point"))
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path to save street mesh"))
			.Optional(TEXT("width"), TEXT("number"), TEXT("Road width in cm"), TEXT("600"))
			.Optional(TEXT("sidewalk_width"), TEXT("number"), TEXT("Per-side sidewalk width in cm"), TEXT("200"))
			.Optional(TEXT("curb_height"), TEXT("number"), TEXT("Curb height in cm"), TEXT("15"))
			.Optional(TEXT("has_sidewalk"), TEXT("boolean"), TEXT("Generate sidewalks"), TEXT("true"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x,y,z]"))
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder"))
			.Build());

	// 4. place_street_furniture — lamps, hydrants, benches etc.
	Registry.RegisterAction(TEXT("mesh"), TEXT("place_street_furniture"),
		TEXT("Place street furniture (lamps, hydrants, benches, mailboxes, trash cans) along a street segment. "
			"Items are spawned via create_parametric_mesh through the tool registry."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshCityBlockActions::PlaceStreetFurniture),
		FParamSchemaBuilder()
			.Required(TEXT("street_start"), TEXT("array"), TEXT("[x, y] start of street"))
			.Required(TEXT("street_end"), TEXT("array"), TEXT("[x, y] end of street"))
			.Optional(TEXT("types"), TEXT("array"), TEXT("Furniture types: lamp, hydrant, bench, mailbox, trash_can"), TEXT("[\"lamp\"]"))
			.Optional(TEXT("spacing"), TEXT("number"), TEXT("Distance between items in cm"), TEXT("800"))
			.Optional(TEXT("side"), TEXT("string"), TEXT("left, right, both"), TEXT("both"))
			.Optional(TEXT("offset"), TEXT("number"), TEXT("Offset from street center in cm"), TEXT("250"))
			.Optional(TEXT("seed"), TEXT("integer"), TEXT("Random seed"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder"))
			.OptionalAssetPath(TEXT("save_path_prefix"), TEXT("Base asset path for furniture meshes"))
			.Optional(TEXT("decay"), TEXT("number"), TEXT("Decay level 0-1 — broken/tilted furniture"), TEXT("0"))
			.Build());
}

// ============================================================================
// Helper: TryExecuteAction — call a downstream SP action via registry
// ============================================================================

bool FMonolithMeshCityBlockActions::TryExecuteAction(const FString& Action,
	const TSharedPtr<FJsonObject>& Params, TSharedPtr<FJsonObject>& OutResult, FString& OutError)
{
	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();
	FMonolithActionResult Result = Registry.ExecuteAction(TEXT("mesh"), Action, Params);
	if (Result.bSuccess)
	{
		OutResult = Result.Result;
		return true;
	}
	OutError = Result.ErrorMessage;
	UE_LOG(LogMonolithCityBlock, Warning, TEXT("Action '%s' failed or not available: %s"), *Action, *OutError);
	return false;
}

// ============================================================================
// Preset System
// ============================================================================

FString FMonolithMeshCityBlockActions::GetPresetsDirectory()
{
	return FPaths::Combine(FPaths::ProjectPluginsDir(), TEXT("Monolith"), TEXT("Saved"), TEXT("Monolith"), TEXT("BlockPresets"));
}

bool FMonolithMeshCityBlockActions::LoadPreset(const FString& PresetName, TSharedPtr<FJsonObject>& OutPreset, FString& OutError)
{
	FString FilePath;
	if (PresetName.EndsWith(TEXT(".json")))
	{
		FilePath = PresetName;
	}
	else
	{
		FilePath = FPaths::Combine(GetPresetsDirectory(), PresetName + TEXT(".json"));
	}

	FString JsonString;
	if (!FFileHelper::LoadFileToString(JsonString, *FilePath))
	{
		OutError = FString::Printf(TEXT("Could not load block preset: %s"), *FilePath);
		return false;
	}

	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
	if (!FJsonSerializer::Deserialize(Reader, OutPreset) || !OutPreset.IsValid())
	{
		OutError = FString::Printf(TEXT("Failed to parse block preset JSON: %s"), *FilePath);
		return false;
	}

	return true;
}

void FMonolithMeshCityBlockActions::ApplyPresetDefaults(const TSharedPtr<FJsonObject>& Preset, const TSharedPtr<FJsonObject>& Params)
{
	if (!Preset.IsValid() || !Params.IsValid()) return;

	// Apply preset fields as defaults only if not already specified in Params
	static const TArray<FString> NumberFields = {
		TEXT("buildings"), TEXT("street_width"), TEXT("sidewalk_width"),
		TEXT("min_building_gap"), TEXT("decay")
	};
	for (const FString& Field : NumberFields)
	{
		if (!Params->HasField(Field) && Preset->HasField(Field))
		{
			Params->SetNumberField(Field, Preset->GetNumberField(Field));
		}
	}

	static const TArray<FString> StringFields = {
		TEXT("genre"), TEXT("facade_style")
	};
	for (const FString& Field : StringFields)
	{
		if (!Params->HasField(Field) && Preset->HasField(Field))
		{
			Params->SetStringField(Field, Preset->GetStringField(Field));
		}
	}

	// block_size
	if (!Params->HasField(TEXT("block_size")) && Preset->HasField(TEXT("block_size")))
	{
		Params->SetArrayField(TEXT("block_size"), Preset->GetArrayField(TEXT("block_size")));
	}

	// archetypes
	if (!Params->HasField(TEXT("archetypes")) && Preset->HasField(TEXT("archetypes")))
	{
		Params->SetArrayField(TEXT("archetypes"), Preset->GetArrayField(TEXT("archetypes")));
	}

	// furniture
	if (!Params->HasField(TEXT("furniture")) && Preset->HasField(TEXT("furniture")))
	{
		Params->SetArrayField(TEXT("furniture"), Preset->GetArrayField(TEXT("furniture")));
	}
}

// ============================================================================
// Genre Defaults
// ============================================================================

TArray<FString> FMonolithMeshCityBlockActions::GetGenreArchetypes(const FString& Genre, int32 BuildingCount, FRandomStream& Rng)
{
	TArray<FString> Archetypes;
	Archetypes.Reserve(BuildingCount);

	if (Genre == TEXT("suburban"))
	{
		// suburban: mostly residential, small_house for variety (warehouse replaces non-existent garage)
		TArray<FString> ArchPool = { TEXT("residential_house"), TEXT("residential_house"), TEXT("small_house"), TEXT("residential_house") };
		for (int32 i = 0; i < BuildingCount; ++i)
		{
			Archetypes.Add(ArchPool[Rng.RandRange(0, ArchPool.Num() - 1)]);
		}
	}
	else if (Genre == TEXT("downtown"))
	{
		// downtown: commercial mix (restaurant replaces commercial_shop, office_building replaces office_small)
		TArray<FString> ArchPool = { TEXT("restaurant"), TEXT("office_building"), TEXT("apartment"), TEXT("warehouse") };
		for (int32 i = 0; i < BuildingCount; ++i)
		{
			Archetypes.Add(ArchPool[Rng.RandRange(0, ArchPool.Num() - 1)]);
		}
	}
	else // "horror" or default
	{
		// Horror: diverse archetypes matching horror templates
		TArray<FString> ArchPool = {
			TEXT("abandoned_hospital"), TEXT("motel"), TEXT("church"),
			TEXT("victorian_mansion"), TEXT("abandoned_school"),
			TEXT("residential_house"), TEXT("warehouse"), TEXT("underground_bunker")
		};
		// Fisher-Yates shuffle for unique picks
		TArray<FString> Shuffled = ArchPool;
		for (int32 i = Shuffled.Num() - 1; i > 0; --i)
		{
			int32 j = Rng.RandRange(0, i);
			Shuffled.Swap(i, j);
		}
		for (int32 i = 0; i < BuildingCount; ++i)
		{
			Archetypes.Add(Shuffled[i % Shuffled.Num()]);
		}
	}

	return Archetypes;
}

TArray<FString> FMonolithMeshCityBlockActions::GetGenreFurniture(const FString& Genre)
{
	if (Genre == TEXT("suburban"))
	{
		return { TEXT("lamp"), TEXT("mailbox"), TEXT("hydrant") };
	}
	else if (Genre == TEXT("downtown"))
	{
		return { TEXT("lamp"), TEXT("hydrant"), TEXT("bench"), TEXT("trash_can") };
	}
	else // horror
	{
		return { TEXT("lamp"), TEXT("hydrant"), TEXT("trash_can") };
	}
}

// ============================================================================
// Lot Subdivision — OBB Recursive
// ============================================================================

TArray<FMonolithMeshCityBlockActions::FBlockLot> FMonolithMeshCityBlockActions::SubdivideOBBRecursive(
	float OriginX, float OriginY, float Width, float Height,
	int32 TargetCount, float MinWidth, float MinHeight,
	float Irregularity, FRandomStream& Rng, int32& LotCounter)
{
	TArray<FBlockLot> Lots;

	// Base case: single lot
	if (TargetCount <= 1 || (Width < MinWidth * 2.0f && Height < MinHeight * 2.0f))
	{
		FBlockLot Lot;
		Lot.LotIndex = LotCounter++;
		Lot.X = OriginX;
		Lot.Y = OriginY;
		Lot.Width = Width;
		Lot.Height = Height;
		Lot.Rotation = 0.0f;
		Lots.Add(Lot);
		return Lots;
	}

	// Choose split axis: always split the longer axis
	const bool bSplitAlongX = (Width >= Height);

	// Split position: center +/- irregularity
	const float SplitT = 0.5f + Rng.FRandRange(-Irregularity, Irregularity);

	// Distribute target count roughly proportional to area
	const int32 CountA = FMath::Max(1, FMath::RoundToInt32(TargetCount * SplitT));
	const int32 CountB = FMath::Max(1, TargetCount - CountA);

	if (bSplitAlongX)
	{
		const float SplitX = Width * SplitT;

		// Check minimum sizes
		if (SplitX < MinWidth || (Width - SplitX) < MinWidth)
		{
			// Can't split — make single lot
			FBlockLot Lot;
			Lot.LotIndex = LotCounter++;
			Lot.X = OriginX;
			Lot.Y = OriginY;
			Lot.Width = Width;
			Lot.Height = Height;
			Lots.Add(Lot);
			return Lots;
		}

		// Left half
		Lots.Append(SubdivideOBBRecursive(
			OriginX, OriginY, SplitX, Height,
			CountA, MinWidth, MinHeight, Irregularity, Rng, LotCounter));

		// Right half
		Lots.Append(SubdivideOBBRecursive(
			OriginX + SplitX, OriginY, Width - SplitX, Height,
			CountB, MinWidth, MinHeight, Irregularity, Rng, LotCounter));
	}
	else
	{
		const float SplitY = Height * SplitT;

		if (SplitY < MinHeight || (Height - SplitY) < MinHeight)
		{
			FBlockLot Lot;
			Lot.LotIndex = LotCounter++;
			Lot.X = OriginX;
			Lot.Y = OriginY;
			Lot.Width = Width;
			Lot.Height = Height;
			Lots.Add(Lot);
			return Lots;
		}

		// Bottom half
		Lots.Append(SubdivideOBBRecursive(
			OriginX, OriginY, Width, SplitY,
			CountA, MinWidth, MinHeight, Irregularity, Rng, LotCounter));

		// Top half
		Lots.Append(SubdivideOBBRecursive(
			OriginX, OriginY + SplitY, Width, Height - SplitY,
			CountB, MinWidth, MinHeight, Irregularity, Rng, LotCounter));
	}

	return Lots;
}

// ============================================================================
// Lot Subdivision — Grid
// ============================================================================

TArray<FMonolithMeshCityBlockActions::FBlockLot> FMonolithMeshCityBlockActions::SubdivideGrid(
	float OriginX, float OriginY, float Width, float Height,
	int32 TargetCount, float MinWidth, float MinHeight,
	int32& LotCounter)
{
	TArray<FBlockLot> Lots;

	// Compute best grid dimensions
	int32 Cols = FMath::Max(1, FMath::RoundToInt32(FMath::Sqrt(static_cast<float>(TargetCount) * Width / Height)));
	int32 Rows = FMath::Max(1, FMath::CeilToInt32(static_cast<float>(TargetCount) / Cols));

	const float LotW = Width / Cols;
	const float LotH = Height / Rows;

	int32 Placed = 0;
	for (int32 R = 0; R < Rows && Placed < TargetCount; ++R)
	{
		for (int32 C = 0; C < Cols && Placed < TargetCount; ++C)
		{
			FBlockLot Lot;
			Lot.LotIndex = LotCounter++;
			Lot.X = OriginX + C * LotW;
			Lot.Y = OriginY + R * LotH;
			Lot.Width = LotW;
			Lot.Height = LotH;
			Lot.Rotation = 0.0f;
			Lots.Add(Lot);
			++Placed;
		}
	}

	return Lots;
}

// ============================================================================
// Lot Subdivision — Organic (Poisson-ish jittered grid)
// ============================================================================

TArray<FMonolithMeshCityBlockActions::FBlockLot> FMonolithMeshCityBlockActions::SubdivideOrganic(
	float OriginX, float OriginY, float Width, float Height,
	int32 TargetCount, float MinWidth, float MinHeight,
	FRandomStream& Rng, int32& LotCounter)
{
	// Start with grid, then jitter positions and sizes
	TArray<FBlockLot> Lots = SubdivideGrid(OriginX, OriginY, Width, Height, TargetCount, MinWidth, MinHeight, LotCounter);

	// Reset LotCounter since SubdivideGrid already advanced it — we re-assigned in place
	// Just jitter the positions and sizes
	for (FBlockLot& Lot : Lots)
	{
		const float JitterX = Rng.FRandRange(-Lot.Width * 0.1f, Lot.Width * 0.1f);
		const float JitterY = Rng.FRandRange(-Lot.Height * 0.1f, Lot.Height * 0.1f);
		const float ScaleW = Rng.FRandRange(0.85f, 1.15f);
		const float ScaleH = Rng.FRandRange(0.85f, 1.15f);

		Lot.X = FMath::Clamp(Lot.X + JitterX, OriginX, OriginX + Width - MinWidth);
		Lot.Y = FMath::Clamp(Lot.Y + JitterY, OriginY, OriginY + Height - MinHeight);
		Lot.Width = FMath::Max(MinWidth, Lot.Width * ScaleW);
		Lot.Height = FMath::Max(MinHeight, Lot.Height * ScaleH);

		// Slight rotation for organic feel
		Lot.Rotation = Rng.FRandRange(-3.0f, 3.0f);

		// Clamp to not exceed block bounds
		if (Lot.X + Lot.Width > OriginX + Width)
			Lot.Width = OriginX + Width - Lot.X;
		if (Lot.Y + Lot.Height > OriginY + Height)
			Lot.Height = OriginY + Height - Lot.Y;
	}

	return Lots;
}

// ============================================================================
// Building Footprint Generation
// ============================================================================

FString FMonolithMeshCityBlockActions::ChooseFootprintShape(const FString& Genre, FRandomStream& Rng)
{
	float Roll = Rng.FRandRange(0.0f, 1.0f);

	if (Genre == TEXT("downtown"))
	{
		// Commercial: mostly rectangles, some L-shapes
		if (Roll < 0.7f) return TEXT("rectangle");
		if (Roll < 0.9f) return TEXT("l_shape");
		return TEXT("t_shape");
	}
	else // residential / horror
	{
		// Based on research: rect 50%, L 30%, T 10%, complex 10%
		if (Roll < 0.5f) return TEXT("rectangle");
		if (Roll < 0.8f) return TEXT("l_shape");
		if (Roll < 0.9f) return TEXT("t_shape");
		return TEXT("rectangle"); // complex falls back to rectangle for now
	}
}

TArray<FVector2D> FMonolithMeshCityBlockActions::GenerateFootprint(
	const FBlockLot& Lot, const FString& ShapeType,
	float FillRatio, FRandomStream& Rng)
{
	// Building envelope inside lot (simple setbacks: 10% each side)
	const float SetbackFront = Lot.Height * 0.15f;
	const float SetbackRear = Lot.Height * 0.10f;
	const float SetbackSide = Lot.Width * 0.08f;

	const float EnvX = Lot.X + SetbackSide;
	const float EnvY = Lot.Y + SetbackFront;
	const float EnvW = FMath::Max(200.0f, Lot.Width - SetbackSide * 2.0f);
	const float EnvH = FMath::Max(200.0f, Lot.Height - SetbackFront - SetbackRear);

	TArray<FVector2D> Footprint;

	if (ShapeType == TEXT("l_shape"))
	{
		// Main body + wing
		const float MainW = EnvW * Rng.FRandRange(0.5f, 0.7f);
		const float WingD = EnvH * Rng.FRandRange(0.4f, 0.6f);

		Footprint.Add(FVector2D(EnvX, EnvY));
		Footprint.Add(FVector2D(EnvX + EnvW, EnvY));
		Footprint.Add(FVector2D(EnvX + EnvW, EnvY + WingD));
		Footprint.Add(FVector2D(EnvX + MainW, EnvY + WingD));
		Footprint.Add(FVector2D(EnvX + MainW, EnvY + EnvH));
		Footprint.Add(FVector2D(EnvX, EnvY + EnvH));
	}
	else if (ShapeType == TEXT("t_shape"))
	{
		// Cross bar + stem
		const float BarD = EnvH * Rng.FRandRange(0.3f, 0.4f);
		const float StemW = EnvW * Rng.FRandRange(0.3f, 0.5f);
		const float StemOffset = (EnvW - StemW) * 0.5f;

		Footprint.Add(FVector2D(EnvX, EnvY));
		Footprint.Add(FVector2D(EnvX + EnvW, EnvY));
		Footprint.Add(FVector2D(EnvX + EnvW, EnvY + BarD));
		Footprint.Add(FVector2D(EnvX + StemOffset + StemW, EnvY + BarD));
		Footprint.Add(FVector2D(EnvX + StemOffset + StemW, EnvY + EnvH));
		Footprint.Add(FVector2D(EnvX + StemOffset, EnvY + EnvH));
		Footprint.Add(FVector2D(EnvX + StemOffset, EnvY + BarD));
		Footprint.Add(FVector2D(EnvX, EnvY + BarD));
	}
	else // rectangle (default)
	{
		const float Shrink = FMath::Sqrt(FillRatio);
		const float FW = EnvW * Shrink;
		const float FH = EnvH * Shrink;
		const float FX = EnvX + (EnvW - FW) * 0.5f;
		const float FY = EnvY + (EnvH - FH) * 0.5f;

		Footprint.Add(FVector2D(FX, FY));
		Footprint.Add(FVector2D(FX + FW, FY));
		Footprint.Add(FVector2D(FX + FW, FY + FH));
		Footprint.Add(FVector2D(FX, FY + FH));
	}

	return Footprint;
}

// ============================================================================
// Decay System
// ============================================================================

void FMonolithMeshCityBlockActions::ApplyBuildingDecay(float DecayLevel, int32 BuildingIndex,
	const TSharedPtr<FJsonObject>& BuildingResult, FRandomStream& Rng,
	TArray<FString>& OutSkippedBuildings)
{
	if (DecayLevel <= 0.0f || !BuildingResult.IsValid()) return;

	// At higher decay, some buildings get destroyed (skipped)
	if (DecayLevel > 0.5f)
	{
		const float DestroyChance = (DecayLevel - 0.5f) * 0.4f; // 0-20% chance
		if (Rng.FRandRange(0.0f, 1.0f) < DestroyChance)
		{
			OutSkippedBuildings.Add(FString::Printf(TEXT("Building_%02d"), BuildingIndex));
		}
	}

	// Add decay metadata to the building result
	BuildingResult->SetNumberField(TEXT("decay_level"), DecayLevel);

	// Tilt: slight random rotation at higher decay
	if (DecayLevel > 0.3f)
	{
		const float MaxTilt = DecayLevel * 3.0f; // Up to 3 degrees at full decay
		BuildingResult->SetNumberField(TEXT("tilt_pitch"), Rng.FRandRange(-MaxTilt, MaxTilt));
		BuildingResult->SetNumberField(TEXT("tilt_roll"), Rng.FRandRange(-MaxTilt, MaxTilt));
	}

	// Boarded windows probability
	const float BoardedPct = FMath::Clamp(DecayLevel * 0.6f, 0.0f, 0.5f);
	BuildingResult->SetNumberField(TEXT("boarded_window_pct"), BoardedPct);
}

// ============================================================================
// Street Geometry Builders
// ============================================================================

void FMonolithMeshCityBlockActions::BuildRoadSurface(UDynamicMesh* Mesh,
	const FVector2D& Start, const FVector2D& End, float RoadWidth, float Z)
{
	if (!Mesh) return;

	const FVector2D Dir = (End - Start);
	const float Length = Dir.Size();
	if (Length < 1.0f) return;

	const FVector2D Forward = Dir.GetSafeNormal();
	const FVector2D Right(-Forward.Y, Forward.X);

	// Road is a flat box
	const FVector2D Center = (Start + End) * 0.5f;

	FGeometryScriptPrimitiveOptions PrimOpts;
	PrimOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	// Use AppendBox for the road surface
	FTransform BoxTransform;
	BoxTransform.SetLocation(FVector(Center.X, Center.Y, Z - 1.0f)); // Slightly below Z=0
	// Rotate to align with street direction
	const float Angle = FMath::Atan2(Forward.Y, Forward.X);
	BoxTransform.SetRotation(FQuat(FVector::UpVector, Angle));

	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
		Mesh, PrimOpts, BoxTransform,
		RoadWidth, Length, 2.0f, // 2cm thick slab
		0, 0, 0,
		EGeometryScriptPrimitiveOriginMode::Center);
}

void FMonolithMeshCityBlockActions::BuildSidewalk(UDynamicMesh* Mesh,
	const FVector2D& Start, const FVector2D& End,
	float SidewalkWidth, float CurbHeight, float OffsetFromCenter, bool bLeftSide, float Z)
{
	if (!Mesh) return;

	const FVector2D Dir = (End - Start);
	const float Length = Dir.Size();
	if (Length < 1.0f) return;

	const FVector2D Forward = Dir.GetSafeNormal();
	const FVector2D Right(-Forward.Y, Forward.X);

	const float Side = bLeftSide ? -1.0f : 1.0f;
	const FVector2D SidewalkCenter = ((Start + End) * 0.5f) + Right * Side * (OffsetFromCenter + SidewalkWidth * 0.5f);

	FGeometryScriptPrimitiveOptions PrimOpts;
	PrimOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	const float Angle = FMath::Atan2(Forward.Y, Forward.X);

	// Sidewalk slab (raised)
	{
		FTransform T;
		T.SetLocation(FVector(SidewalkCenter.X, SidewalkCenter.Y, Z + CurbHeight * 0.5f));
		T.SetRotation(FQuat(FVector::UpVector, Angle));

		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, PrimOpts, T,
			SidewalkWidth, Length, CurbHeight,
			0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);
	}

	// Curb face: thin vertical strip at the road-side edge of sidewalk
	{
		const FVector2D CurbCenter = ((Start + End) * 0.5f) + Right * Side * OffsetFromCenter;
		FTransform T;
		T.SetLocation(FVector(CurbCenter.X, CurbCenter.Y, Z + CurbHeight * 0.5f));
		T.SetRotation(FQuat(FVector::UpVector, Angle));

		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, PrimOpts, T,
			3.0f, Length, CurbHeight, // 3cm wide curb face
			0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);
	}
}

// ============================================================================
// Action: create_lot_layout
// ============================================================================

FMonolithActionResult FMonolithMeshCityBlockActions::CreateLotLayout(const TSharedPtr<FJsonObject>& Params)
{
	// Parse block_size
	const TArray<TSharedPtr<FJsonValue>>* BlockSizeArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("block_size"), BlockSizeArr) || !BlockSizeArr || BlockSizeArr->Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("block_size must be [width, height] array"));
	}

	const float BlockWidth = static_cast<float>((*BlockSizeArr)[0]->AsNumber());
	const float BlockHeight = static_cast<float>((*BlockSizeArr)[1]->AsNumber());

	if (BlockWidth < 100.0f || BlockHeight < 100.0f)
	{
		return FMonolithActionResult::Error(TEXT("block_size dimensions must be >= 100 cm"));
	}

	const int32 LotCount = static_cast<int32>(Params->GetNumberField(TEXT("lot_count")));
	if (LotCount < 1 || LotCount > 100)
	{
		return FMonolithActionResult::Error(TEXT("lot_count must be between 1 and 100"));
	}

	// Optional params
	int32 Seed = Params->HasField(TEXT("seed"))
		? static_cast<int32>(Params->GetNumberField(TEXT("seed")))
		: FMath::Rand();
	FRandomStream Rng(Seed);

	float MinW = 800.0f, MinH = 600.0f;
	const TArray<TSharedPtr<FJsonValue>>* MinSizeArr = nullptr;
	if (Params->TryGetArrayField(TEXT("min_lot_size"), MinSizeArr) && MinSizeArr && MinSizeArr->Num() >= 2)
	{
		MinW = static_cast<float>((*MinSizeArr)[0]->AsNumber());
		MinH = static_cast<float>((*MinSizeArr)[1]->AsNumber());
	}

	const float StreetWidth = Params->HasField(TEXT("street_width"))
		? static_cast<float>(Params->GetNumberField(TEXT("street_width")))
		: 600.0f;

	FString Algorithm = TEXT("obb_recursive");
	Params->TryGetStringField(TEXT("algorithm"), Algorithm);

	// Usable area after subtracting border streets
	const float UsableX = StreetWidth * 0.5f;
	const float UsableY = StreetWidth * 0.5f;
	const float UsableW = BlockWidth - StreetWidth;
	const float UsableH = BlockHeight - StreetWidth;

	int32 LotCounter = 0;
	TArray<FBlockLot> Lots;

	if (Algorithm == TEXT("grid"))
	{
		Lots = SubdivideGrid(UsableX, UsableY, UsableW, UsableH, LotCount, MinW, MinH, LotCounter);
	}
	else if (Algorithm == TEXT("organic"))
	{
		Lots = SubdivideOrganic(UsableX, UsableY, UsableW, UsableH, LotCount, MinW, MinH, Rng, LotCounter);
	}
	else // obb_recursive
	{
		const float Irregularity = 0.15f;
		Lots = SubdivideOBBRecursive(UsableX, UsableY, UsableW, UsableH, LotCount, MinW, MinH, Irregularity, Rng, LotCounter);
	}

	// Mark corner lots (lots touching two edges of usable area)
	for (FBlockLot& Lot : Lots)
	{
		const bool bTouchesLeft = (Lot.X <= UsableX + 1.0f);
		const bool bTouchesRight = (Lot.X + Lot.Width >= UsableX + UsableW - 1.0f);
		const bool bTouchesBottom = (Lot.Y <= UsableY + 1.0f);
		const bool bTouchesTop = (Lot.Y + Lot.Height >= UsableY + UsableH - 1.0f);
		Lot.bCornerLot = (bTouchesLeft || bTouchesRight) && (bTouchesBottom || bTouchesTop);
	}

	// Generate street segments at block edges
	TArray<FStreetSegment> Streets;

	// Bottom street
	FStreetSegment Bottom;
	Bottom.Start = FVector2D(0, 0);
	Bottom.End = FVector2D(BlockWidth, 0);
	Bottom.Width = StreetWidth;
	Streets.Add(Bottom);

	// Top street
	FStreetSegment Top;
	Top.Start = FVector2D(0, BlockHeight);
	Top.End = FVector2D(BlockWidth, BlockHeight);
	Top.Width = StreetWidth;
	Streets.Add(Top);

	// Left street
	FStreetSegment Left;
	Left.Start = FVector2D(0, 0);
	Left.End = FVector2D(0, BlockHeight);
	Left.Width = StreetWidth;
	Streets.Add(Left);

	// Right street
	FStreetSegment Right;
	Right.Start = FVector2D(BlockWidth, 0);
	Right.End = FVector2D(BlockWidth, BlockHeight);
	Right.Width = StreetWidth;
	Streets.Add(Right);

	// Build result
	auto Result = MakeShared<FJsonObject>();

	TArray<TSharedPtr<FJsonValue>> LotsArr;
	for (const FBlockLot& Lot : Lots)
	{
		LotsArr.Add(MakeShared<FJsonValueObject>(Lot.ToJson()));
	}
	Result->SetArrayField(TEXT("lots"), LotsArr);

	TArray<TSharedPtr<FJsonValue>> StreetsArr;
	for (const FStreetSegment& S : Streets)
	{
		StreetsArr.Add(MakeShared<FJsonValueObject>(S.ToJson()));
	}
	Result->SetArrayField(TEXT("streets"), StreetsArr);

	Result->SetNumberField(TEXT("seed"), Seed);
	Result->SetStringField(TEXT("algorithm"), Algorithm);
	Result->SetNumberField(TEXT("lot_count"), Lots.Num());

	TArray<TSharedPtr<FJsonValue>> BlockSizeOut;
	BlockSizeOut.Add(MakeShared<FJsonValueNumber>(BlockWidth));
	BlockSizeOut.Add(MakeShared<FJsonValueNumber>(BlockHeight));
	Result->SetArrayField(TEXT("block_size"), BlockSizeOut);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// Action: create_street
// ============================================================================

FMonolithActionResult FMonolithMeshCityBlockActions::CreateStreet(const TSharedPtr<FJsonObject>& Params)
{
	// Parse required fields
	const TArray<TSharedPtr<FJsonValue>>* StartArr = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* EndArr = nullptr;

	if (!Params->TryGetArrayField(TEXT("start"), StartArr) || !StartArr || StartArr->Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("start must be [x, y] array"));
	}
	if (!Params->TryGetArrayField(TEXT("end"), EndArr) || !EndArr || EndArr->Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("end must be [x, y] array"));
	}

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("save_path is required"));
	}

	const FVector2D Start((*StartArr)[0]->AsNumber(), (*StartArr)[1]->AsNumber());
	const FVector2D End((*EndArr)[0]->AsNumber(), (*EndArr)[1]->AsNumber());

	const float RoadWidth = Params->HasField(TEXT("width"))
		? static_cast<float>(Params->GetNumberField(TEXT("width"))) : 600.0f;
	const float SidewalkWidth = Params->HasField(TEXT("sidewalk_width"))
		? static_cast<float>(Params->GetNumberField(TEXT("sidewalk_width"))) : 200.0f;
	const float CurbHeight = Params->HasField(TEXT("curb_height"))
		? static_cast<float>(Params->GetNumberField(TEXT("curb_height"))) : 15.0f;

	bool bHasSidewalk = true;
	if (Params->HasField(TEXT("has_sidewalk")))
	{
		bHasSidewalk = Params->GetBoolField(TEXT("has_sidewalk"));
	}

	FVector Location = FVector::ZeroVector;
	MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location);

	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);

	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);

	// Create dynamic mesh
	UDynamicMesh* DynMesh = NewObject<UDynamicMesh>();

	// Build road surface
	BuildRoadSurface(DynMesh, Start, End, RoadWidth, 0.0f);

	// Build sidewalks
	if (bHasSidewalk)
	{
		const float SidewalkOffset = RoadWidth * 0.5f;
		BuildSidewalk(DynMesh, Start, End, SidewalkWidth, CurbHeight, SidewalkOffset, true, 0.0f);
		BuildSidewalk(DynMesh, Start, End, SidewalkWidth, CurbHeight, SidewalkOffset, false, 0.0f);
	}

	// Compute normals
	FGeometryScriptCalculateNormalsOptions NormOpts;
	UGeometryScriptLibrary_MeshNormalsFunctions::RecomputeNormals(DynMesh, NormOpts);

	// Save to asset
	FString SaveError;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(DynMesh, SavePath, true, SaveError))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to save street mesh: %s"), *SaveError));
	}

	// Optionally place in scene
	AActor* PlacedActor = nullptr;
	if (Label.IsEmpty())
	{
		Label = TEXT("Street");
	}
	PlacedActor = FMonolithMeshProceduralActions::PlaceMeshInScene(SavePath, Location, FRotator::ZeroRotator, Label, false, Folder);

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("save_path"), SavePath);
	Result->SetNumberField(TEXT("road_width"), RoadWidth);
	Result->SetNumberField(TEXT("sidewalk_width"), SidewalkWidth);
	Result->SetNumberField(TEXT("curb_height"), CurbHeight);
	Result->SetBoolField(TEXT("has_sidewalk"), bHasSidewalk);

	if (PlacedActor)
	{
		Result->SetStringField(TEXT("actor_name"), PlacedActor->GetActorNameOrLabel());
	}

	TArray<TSharedPtr<FJsonValue>> StartOut, EndOut;
	StartOut.Add(MakeShared<FJsonValueNumber>(Start.X));
	StartOut.Add(MakeShared<FJsonValueNumber>(Start.Y));
	EndOut.Add(MakeShared<FJsonValueNumber>(End.X));
	EndOut.Add(MakeShared<FJsonValueNumber>(End.Y));
	Result->SetArrayField(TEXT("start"), StartOut);
	Result->SetArrayField(TEXT("end"), EndOut);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// Action: place_street_furniture
// ============================================================================

FMonolithActionResult FMonolithMeshCityBlockActions::PlaceStreetFurniture(const TSharedPtr<FJsonObject>& Params)
{
	// Parse street segment
	const TArray<TSharedPtr<FJsonValue>>* StartArr = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* EndArr = nullptr;

	if (!Params->TryGetArrayField(TEXT("street_start"), StartArr) || !StartArr || StartArr->Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("street_start must be [x, y] array"));
	}
	if (!Params->TryGetArrayField(TEXT("street_end"), EndArr) || !EndArr || EndArr->Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("street_end must be [x, y] array"));
	}

	const FVector2D StreetStart((*StartArr)[0]->AsNumber(), (*StartArr)[1]->AsNumber());
	const FVector2D StreetEnd((*EndArr)[0]->AsNumber(), (*EndArr)[1]->AsNumber());

	const float Spacing = Params->HasField(TEXT("spacing"))
		? static_cast<float>(Params->GetNumberField(TEXT("spacing"))) : 800.0f;
	const float Offset = Params->HasField(TEXT("offset"))
		? static_cast<float>(Params->GetNumberField(TEXT("offset"))) : 250.0f;
	const float DecayLevel = Params->HasField(TEXT("decay"))
		? static_cast<float>(Params->GetNumberField(TEXT("decay"))) : 0.0f;

	int32 Seed = Params->HasField(TEXT("seed"))
		? static_cast<int32>(Params->GetNumberField(TEXT("seed")))
		: FMath::Rand();
	FRandomStream Rng(Seed);

	FString Side = TEXT("both");
	Params->TryGetStringField(TEXT("side"), Side);

	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);

	FString SavePathPrefix;
	Params->TryGetStringField(TEXT("save_path_prefix"), SavePathPrefix);

	// Parse furniture types
	TArray<FString> FurnitureTypes;
	const TArray<TSharedPtr<FJsonValue>>* TypesArr = nullptr;
	if (Params->TryGetArrayField(TEXT("types"), TypesArr) && TypesArr)
	{
		for (const auto& V : *TypesArr)
		{
			FurnitureTypes.Add(V->AsString());
		}
	}
	if (FurnitureTypes.Num() == 0)
	{
		FurnitureTypes.Add(TEXT("lamp"));
	}

	// Compute street direction and perpendicular
	const FVector2D Dir = (StreetEnd - StreetStart);
	const float StreetLength = Dir.Size();
	if (StreetLength < Spacing)
	{
		return FMonolithActionResult::Error(TEXT("Street segment too short for requested spacing"));
	}

	const FVector2D Forward = Dir.GetSafeNormal();
	const FVector2D Right(-Forward.Y, Forward.X);
	const float YawDeg = FMath::RadiansToDegrees(FMath::Atan2(Forward.Y, Forward.X));

	// Determine which sides to place on
	TArray<float> SideOffsets;
	if (Side == TEXT("left") || Side == TEXT("both"))
	{
		SideOffsets.Add(-Offset);
	}
	if (Side == TEXT("right") || Side == TEXT("both"))
	{
		SideOffsets.Add(Offset);
	}

	TArray<TSharedPtr<FJsonValue>> PlacedItems;
	int32 ItemIndex = 0;

	// Walk along street and place items
	const int32 NumPositions = FMath::FloorToInt32(StreetLength / Spacing);

	for (float SideOffset : SideOffsets)
	{
		for (int32 i = 0; i <= NumPositions; ++i)
		{
			const float T = (NumPositions > 0) ? static_cast<float>(i) / NumPositions : 0.5f;
			const FVector2D Pos = StreetStart + Dir * T + Right * SideOffset;

			// Pick furniture type (cycle through types)
			const FString& FType = FurnitureTypes[i % FurnitureTypes.Num()];

			// Map furniture type to parametric mesh spec
			FString MeshType;
			float MeshWidth = 30.0f, MeshHeight = 300.0f, MeshDepth = 30.0f;

			if (FType == TEXT("lamp"))
			{
				MeshType = TEXT("cylinder");
				MeshWidth = 15.0f;
				MeshHeight = 400.0f;
				MeshDepth = 15.0f;
			}
			else if (FType == TEXT("hydrant"))
			{
				MeshType = TEXT("cylinder");
				MeshWidth = 20.0f;
				MeshHeight = 60.0f;
				MeshDepth = 20.0f;
			}
			else if (FType == TEXT("bench"))
			{
				MeshType = TEXT("box");
				MeshWidth = 120.0f;
				MeshHeight = 45.0f;
				MeshDepth = 40.0f;
			}
			else if (FType == TEXT("mailbox"))
			{
				MeshType = TEXT("box");
				MeshWidth = 40.0f;
				MeshHeight = 100.0f;
				MeshDepth = 30.0f;
			}
			else if (FType == TEXT("trash_can"))
			{
				MeshType = TEXT("cylinder");
				MeshWidth = 30.0f;
				MeshHeight = 70.0f;
				MeshDepth = 30.0f;
			}
			else
			{
				MeshType = TEXT("box");
			}

			// Call create_parametric_mesh via registry
			auto MeshParams = MakeShared<FJsonObject>();
			MeshParams->SetStringField(TEXT("type"), MeshType);
			MeshParams->SetNumberField(TEXT("width"), MeshWidth);
			MeshParams->SetNumberField(TEXT("height"), MeshHeight);
			MeshParams->SetNumberField(TEXT("depth"), MeshDepth);

			FString ItemLabel = FString::Printf(TEXT("%s_%02d"), *FType, ItemIndex);

			if (!SavePathPrefix.IsEmpty())
			{
				MeshParams->SetStringField(TEXT("save_path"),
					FString::Printf(TEXT("%s/Furniture/%s"), *SavePathPrefix, *ItemLabel));
			}

			// Location — place at sidewalk height
			TArray<TSharedPtr<FJsonValue>> LocArr;
			LocArr.Add(MakeShared<FJsonValueNumber>(Pos.X));
			LocArr.Add(MakeShared<FJsonValueNumber>(Pos.Y));
			LocArr.Add(MakeShared<FJsonValueNumber>(15.0f)); // Curb height
			MeshParams->SetArrayField(TEXT("location"), LocArr);
			MeshParams->SetStringField(TEXT("label"), ItemLabel);

			if (!Folder.IsEmpty())
			{
				MeshParams->SetStringField(TEXT("folder"), Folder);
			}

			// Apply decay: tilt or skip some items
			float ItemYaw = YawDeg;
			bool bSkipped = false;
			if (DecayLevel > 0.0f)
			{
				// Skip chance
				if (Rng.FRandRange(0.0f, 1.0f) < DecayLevel * 0.3f)
				{
					bSkipped = true;
				}
				// Tilt
				if (!bSkipped && DecayLevel > 0.2f)
				{
					const float TiltRange = DecayLevel * 15.0f;
					ItemYaw += Rng.FRandRange(-TiltRange, TiltRange);
				}
			}

			if (!bSkipped)
			{
				TSharedPtr<FJsonObject> MeshResult;
				FString MeshError;
				bool bPlaced = TryExecuteAction(TEXT("create_parametric_mesh"), MeshParams, MeshResult, MeshError);

				auto ItemJson = MakeShared<FJsonObject>();
				ItemJson->SetStringField(TEXT("type"), FType);
				TArray<TSharedPtr<FJsonValue>> ItemLoc;
				ItemLoc.Add(MakeShared<FJsonValueNumber>(Pos.X));
				ItemLoc.Add(MakeShared<FJsonValueNumber>(Pos.Y));
				ItemLoc.Add(MakeShared<FJsonValueNumber>(15.0f));
				ItemJson->SetArrayField(TEXT("location"), ItemLoc);
				ItemJson->SetStringField(TEXT("label"), ItemLabel);
				ItemJson->SetBoolField(TEXT("placed"), bPlaced);

				if (bPlaced && MeshResult.IsValid())
				{
					FString ActorName;
					if (MeshResult->TryGetStringField(TEXT("actor_name"), ActorName))
					{
						ItemJson->SetStringField(TEXT("actor_name"), ActorName);
					}
				}

				PlacedItems.Add(MakeShared<FJsonValueObject>(ItemJson));
			}

			++ItemIndex;
		}
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("furniture"), PlacedItems);
	Result->SetNumberField(TEXT("total_placed"), PlacedItems.Num());
	Result->SetNumberField(TEXT("seed"), Seed);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// Action: create_city_block — THE ORCHESTRATOR
// ============================================================================

FMonolithActionResult FMonolithMeshCityBlockActions::CreateCityBlock(const TSharedPtr<FJsonObject>& Params)
{
	// ---- Step 0: Parse parameters + apply preset ----

	FString SavePathPrefix;
	if (!Params->TryGetStringField(TEXT("save_path_prefix"), SavePathPrefix) || SavePathPrefix.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("save_path_prefix is required"));
	}

	// Load and apply preset if specified
	FString PresetName;
	if (Params->TryGetStringField(TEXT("preset"), PresetName) && !PresetName.IsEmpty())
	{
		TSharedPtr<FJsonObject> Preset;
		FString PresetError;
		if (LoadPreset(PresetName, Preset, PresetError))
		{
			ApplyPresetDefaults(Preset, Params);
			UE_LOG(LogMonolithCityBlock, Log, TEXT("Applied block preset: %s"), *PresetName);
		}
		else
		{
			UE_LOG(LogMonolithCityBlock, Warning, TEXT("Could not load preset '%s': %s (using defaults)"), *PresetName, *PresetError);
		}
	}

	// Extract parameters with defaults
	const int32 BuildingCount = Params->HasField(TEXT("buildings"))
		? static_cast<int32>(Params->GetNumberField(TEXT("buildings"))) : 4;

	float BlockWidth = 6000.0f, BlockHeight = 4000.0f;
	const TArray<TSharedPtr<FJsonValue>>* BlockSizeArr = nullptr;
	if (Params->TryGetArrayField(TEXT("block_size"), BlockSizeArr) && BlockSizeArr && BlockSizeArr->Num() >= 2)
	{
		BlockWidth = static_cast<float>((*BlockSizeArr)[0]->AsNumber());
		BlockHeight = static_cast<float>((*BlockSizeArr)[1]->AsNumber());
	}

	FString Genre = TEXT("horror");
	Params->TryGetStringField(TEXT("genre"), Genre);

	int32 Seed = Params->HasField(TEXT("seed"))
		? static_cast<int32>(Params->GetNumberField(TEXT("seed")))
		: FMath::Rand();
	FRandomStream Rng(Seed);

	const float Decay = Params->HasField(TEXT("decay"))
		? FMath::Clamp(static_cast<float>(Params->GetNumberField(TEXT("decay"))), 0.0f, 1.0f) : 0.3f;
	const float StreetWidth = Params->HasField(TEXT("street_width"))
		? static_cast<float>(Params->GetNumberField(TEXT("street_width"))) : 600.0f;
	const float SidewalkWidth = Params->HasField(TEXT("sidewalk_width"))
		? static_cast<float>(Params->GetNumberField(TEXT("sidewalk_width"))) : 200.0f;

	const bool bHospiceMode = Params->HasField(TEXT("hospice_mode"))
		? Params->GetBoolField(TEXT("hospice_mode")) : false;
	const bool bSkipFacades = Params->HasField(TEXT("skip_facades"))
		? Params->GetBoolField(TEXT("skip_facades")) : false;

	// Facade style for integrated generation (v3)
	FString BlockFacadeStyle;
	Params->TryGetStringField(TEXT("facade_style"), BlockFacadeStyle);
	// Default facade style per genre if not specified
	if (BlockFacadeStyle.IsEmpty())
	{
		if (Genre == TEXT("horror")) BlockFacadeStyle = TEXT("abandoned");
		else if (Genre == TEXT("suburban")) BlockFacadeStyle = TEXT("colonial");
		else if (Genre == TEXT("downtown")) BlockFacadeStyle = TEXT("brutalist");
		else BlockFacadeStyle = TEXT("colonial"); // fallback
	}
	const bool bSkipRoofs = Params->HasField(TEXT("skip_roofs"))
		? Params->GetBoolField(TEXT("skip_roofs")) : false;
	const bool bSkipStreets = Params->HasField(TEXT("skip_streets"))
		? Params->GetBoolField(TEXT("skip_streets")) : false;
	const bool bSkipFurniture = Params->HasField(TEXT("skip_furniture"))
		? Params->GetBoolField(TEXT("skip_furniture")) : false;
	const bool bSkipValidation = Params->HasField(TEXT("skip_validation"))
		? Params->GetBoolField(TEXT("skip_validation")) : false;
	const bool bValidateAndRetry = Params->HasField(TEXT("validate_and_retry"))
		? Params->GetBoolField(TEXT("validate_and_retry")) : false;
	const bool bSkipFurnishing = Params->HasField(TEXT("skip_furnishing"))
		? Params->GetBoolField(TEXT("skip_furnishing")) : false;
	const bool bSkipVolumes = Params->HasField(TEXT("skip_volumes"))
		? Params->GetBoolField(TEXT("skip_volumes")) : false;
	const bool bUseTemplates = Params->HasField(TEXT("use_templates"))
		? Params->GetBoolField(TEXT("use_templates")) : true;

	FVector BlockOrigin = FVector::ZeroVector;
	MonolithMeshUtils::ParseVector(Params, TEXT("location"), BlockOrigin);

	FString Folder = TEXT("CityBlock");
	Params->TryGetStringField(TEXT("folder"), Folder);

	// Determine archetypes
	TArray<FString> Archetypes;
	const TArray<TSharedPtr<FJsonValue>>* ArchArr = nullptr;
	if (Params->TryGetArrayField(TEXT("archetypes"), ArchArr) && ArchArr)
	{
		for (const auto& V : *ArchArr)
		{
			Archetypes.Add(V->AsString());
		}
	}
	if (Archetypes.Num() < BuildingCount)
	{
		TArray<FString> GenreDefaults = GetGenreArchetypes(Genre, BuildingCount - Archetypes.Num(), Rng);
		Archetypes.Append(GenreDefaults);
	}

	TArray<FString> SkippedSteps;

	// ---- Step 1: Lot subdivision ----

	UE_LOG(LogMonolithCityBlock, Log, TEXT("=== create_city_block: %d buildings, genre=%s, seed=%d ==="), BuildingCount, *Genre, Seed);

	auto LotParams = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> BlockSizeOut;
	BlockSizeOut.Add(MakeShared<FJsonValueNumber>(BlockWidth));
	BlockSizeOut.Add(MakeShared<FJsonValueNumber>(BlockHeight));
	LotParams->SetArrayField(TEXT("block_size"), BlockSizeOut);
	LotParams->SetNumberField(TEXT("lot_count"), BuildingCount);
	LotParams->SetNumberField(TEXT("seed"), Seed);
	LotParams->SetNumberField(TEXT("street_width"), StreetWidth);

	FMonolithActionResult LotResult = CreateLotLayout(LotParams);
	if (!LotResult.bSuccess)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Lot subdivision failed: %s"), *LotResult.ErrorMessage));
	}

	// Parse lots from result
	const TArray<TSharedPtr<FJsonValue>>* LotsArr = nullptr;
	if (!LotResult.Result->TryGetArrayField(TEXT("lots"), LotsArr) || !LotsArr)
	{
		return FMonolithActionResult::Error(TEXT("Lot layout returned no lots"));
	}

	UE_LOG(LogMonolithCityBlock, Log, TEXT("  Subdivided into %d lots"), LotsArr->Num());

	// ---- Step 2-5: Buildings (one at a time) ----

	TArray<TSharedPtr<FJsonValue>> BuildingResults;
	TArray<FString> DestroyedBuildings;

	// Validation tracking
	int32 BuildingsValidated = 0;
	int32 BuildingsPassed = 0;
	double ValidationScoreSum = 0.0;

	// Template dedup tracking — avoid repeating the same template within a block
	TSet<FString> UsedTemplates;

	for (int32 i = 0; i < LotsArr->Num() && i < BuildingCount; ++i)
	{
		const TSharedPtr<FJsonObject>* LotObj = nullptr;
		if (!(*LotsArr)[i]->TryGetObject(LotObj) || !LotObj || !(*LotObj).IsValid())
		{
			continue;
		}

		const float LotX = static_cast<float>((*LotObj)->GetNumberField(TEXT("x")));
		const float LotY = static_cast<float>((*LotObj)->GetNumberField(TEXT("y")));
		const float LotW = static_cast<float>((*LotObj)->GetNumberField(TEXT("width")));
		const float LotH = static_cast<float>((*LotObj)->GetNumberField(TEXT("height")));

		// Build an FBlockLot for footprint generation
		FBlockLot Lot;
		Lot.LotIndex = i;
		Lot.X = LotX;
		Lot.Y = LotY;
		Lot.Width = LotW;
		Lot.Height = LotH;

		UE_LOG(LogMonolithCityBlock, Log, TEXT("  Building %d: lot at (%.0f, %.0f) size %.0f x %.0f, archetype=%s"),
			i, LotX, LotY, LotW, LotH, *Archetypes[i]);

		// Check if this building is destroyed by decay
		TArray<FString> SkippedBuildings;
		auto BuildingMeta = MakeShared<FJsonObject>();
		ApplyBuildingDecay(Decay, i, BuildingMeta, Rng, SkippedBuildings);

		if (SkippedBuildings.Contains(FString::Printf(TEXT("Building_%02d"), i)))
		{
			UE_LOG(LogMonolithCityBlock, Log, TEXT("    -> DESTROYED by decay (skipped)"));
			DestroyedBuildings.Add(FString::Printf(TEXT("Building_%02d"), i));

			auto SkipJson = MakeShared<FJsonObject>();
			SkipJson->SetStringField(TEXT("building_id"), FString::Printf(TEXT("Building_%02d"), i));
			SkipJson->SetBoolField(TEXT("destroyed"), true);
			BuildingResults.Add(MakeShared<FJsonValueObject>(SkipJson));
			continue;
		}

		// Step 2: Generate floor plan via SP2 (generate_floor_plan)
		auto FloorPlanParams = MakeShared<FJsonObject>();
		FloorPlanParams->SetStringField(TEXT("archetype"), Archetypes[i]);
		FloorPlanParams->SetNumberField(TEXT("footprint_width"), LotW * 0.7f); // Building fills ~70% of lot
		FloorPlanParams->SetNumberField(TEXT("footprint_height"), LotH * 0.7f);
		FloorPlanParams->SetNumberField(TEXT("seed"), Seed + i);
		if (bHospiceMode)
		{
			FloorPlanParams->SetBoolField(TEXT("hospice_mode"), true);
		}

		// Fix #2: Pass horror_level so floor plan generator can apply horror modifiers
		if (Decay > 0.0f)
		{
			FloorPlanParams->SetNumberField(TEXT("horror_level"), Decay);
		}

		// Fix #8: Pass use_templates flag through to floor plan generator
		if (!bUseTemplates)
		{
			FloorPlanParams->SetBoolField(TEXT("use_templates"), false);
		}

		// Fix #9: When genre is horror, hint the template system to prefer horror-category templates
		if (Genre == TEXT("horror"))
		{
			FloorPlanParams->SetStringField(TEXT("template_category"), TEXT("horror"));
		}

		// Inject exclude_templates for dedup within the city block
		if (UsedTemplates.Num() > 0)
		{
			TArray<TSharedPtr<FJsonValue>> ExcludeArr;
			for (const FString& T : UsedTemplates)
				ExcludeArr.Add(MakeShared<FJsonValueString>(T));
			FloorPlanParams->SetArrayField(TEXT("exclude_templates"), ExcludeArr);
		}

		TSharedPtr<FJsonObject> FloorPlanResult;
		FString FloorPlanError;
		bool bHasFloorPlan = TryExecuteAction(TEXT("generate_floor_plan"), FloorPlanParams, FloorPlanResult, FloorPlanError);

		// Track chosen template for dedup
		if (bHasFloorPlan && FloorPlanResult.IsValid())
		{
			FString ChosenTemplate;
			if (FloorPlanResult->TryGetStringField(TEXT("template_name"), ChosenTemplate))
				UsedTemplates.Add(ChosenTemplate);
			// Safety: if approaching template exhaustion, reset to avoid zero-candidate failures
			if (UsedTemplates.Num() >= 8)
				UsedTemplates.Reset();
		}

		if (!bHasFloorPlan)
		{
			UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Floor plan generation failed/unavailable: %s. Using simple box fallback."), *FloorPlanError);
		}

		// Step 3: Build geometry via SP1 (create_building_from_grid)
		TSharedPtr<FJsonObject> BuildingGridParams;
		FString BuildingAssetPath = FString::Printf(TEXT("%s/Building_%02d"), *SavePathPrefix, i);

		if (bHasFloorPlan && FloorPlanResult.IsValid())
		{
			// Floor plan result contains grid, rooms, doors — pass directly to create_building_from_grid
			BuildingGridParams = FloorPlanResult;
			BuildingGridParams->SetStringField(TEXT("save_path"), BuildingAssetPath);
			BuildingGridParams->SetStringField(TEXT("building_id"), FString::Printf(TEXT("Building_%02d"), i));

			// Set world location for this building
			TArray<TSharedPtr<FJsonValue>> BuildingLoc;
			BuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.X + LotX + LotW * 0.15f));
			BuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Y + LotY + LotH * 0.15f));
			BuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Z));
			BuildingGridParams->SetArrayField(TEXT("location"), BuildingLoc);
			BuildingGridParams->SetStringField(TEXT("folder"), Folder + TEXT("/Buildings"));
			BuildingGridParams->SetBoolField(TEXT("overwrite"), true);
			// omit_exterior_walls is now set automatically by facade_style in create_building_from_grid
		}
		else
		{
			// Fallback: create a simple 2-room grid
			BuildingGridParams = MakeShared<FJsonObject>();

			// Simple 2x2 grid: room 0 = left, room 1 = right
			const int32 GridW = FMath::Max(2, FMath::RoundToInt32(LotW * 0.7f / 50.0f));
			const int32 GridH = FMath::Max(2, FMath::RoundToInt32(LotH * 0.7f / 50.0f));
			const int32 HalfW = GridW / 2;

			TArray<TSharedPtr<FJsonValue>> GridRows;
			for (int32 Row = 0; Row < GridH; ++Row)
			{
				TArray<TSharedPtr<FJsonValue>> RowData;
				for (int32 Col = 0; Col < GridW; ++Col)
				{
					RowData.Add(MakeShared<FJsonValueNumber>(Col < HalfW ? 0 : 1));
				}
				GridRows.Add(MakeShared<FJsonValueArray>(RowData));
			}
			BuildingGridParams->SetArrayField(TEXT("grid"), GridRows);

			// Rooms
			TArray<TSharedPtr<FJsonValue>> RoomsArr;
			{
				auto R0 = MakeShared<FJsonObject>();
				R0->SetStringField(TEXT("room_id"), TEXT("room_a"));
				R0->SetStringField(TEXT("room_type"), TEXT("living_room"));
				TArray<TSharedPtr<FJsonValue>> Cells0;
				for (int32 Row = 0; Row < GridH; ++Row)
				{
					for (int32 Col = 0; Col < HalfW; ++Col)
					{
						TArray<TSharedPtr<FJsonValue>> Cell;
						Cell.Add(MakeShared<FJsonValueNumber>(Col));
						Cell.Add(MakeShared<FJsonValueNumber>(Row));
						Cells0.Add(MakeShared<FJsonValueArray>(Cell));
					}
				}
				R0->SetArrayField(TEXT("grid_cells"), Cells0);
				RoomsArr.Add(MakeShared<FJsonValueObject>(R0));

				auto R1 = MakeShared<FJsonObject>();
				R1->SetStringField(TEXT("room_id"), TEXT("room_b"));
				R1->SetStringField(TEXT("room_type"), TEXT("bedroom"));
				TArray<TSharedPtr<FJsonValue>> Cells1;
				for (int32 Row = 0; Row < GridH; ++Row)
				{
					for (int32 Col = HalfW; Col < GridW; ++Col)
					{
						TArray<TSharedPtr<FJsonValue>> Cell;
						Cell.Add(MakeShared<FJsonValueNumber>(Col));
						Cell.Add(MakeShared<FJsonValueNumber>(Row));
						Cells1.Add(MakeShared<FJsonValueArray>(Cell));
					}
				}
				R1->SetArrayField(TEXT("grid_cells"), Cells1);
				RoomsArr.Add(MakeShared<FJsonValueObject>(R1));
			}
			BuildingGridParams->SetArrayField(TEXT("rooms"), RoomsArr);

			// Door between rooms at the center
			TArray<TSharedPtr<FJsonValue>> DoorsArr;
			{
				auto D = MakeShared<FJsonObject>();
				D->SetStringField(TEXT("door_id"), TEXT("door_0"));
				D->SetStringField(TEXT("room_a"), TEXT("room_a"));
				D->SetStringField(TEXT("room_b"), TEXT("room_b"));
				TArray<TSharedPtr<FJsonValue>> ES, EE;
				ES.Add(MakeShared<FJsonValueNumber>(HalfW));
				ES.Add(MakeShared<FJsonValueNumber>(GridH / 2));
				EE.Add(MakeShared<FJsonValueNumber>(HalfW));
				EE.Add(MakeShared<FJsonValueNumber>(GridH / 2));
				D->SetArrayField(TEXT("edge_start"), ES);
				D->SetArrayField(TEXT("edge_end"), EE);
				DoorsArr.Add(MakeShared<FJsonValueObject>(D));
			}
			BuildingGridParams->SetArrayField(TEXT("doors"), DoorsArr);

			BuildingGridParams->SetStringField(TEXT("save_path"), BuildingAssetPath);
			BuildingGridParams->SetStringField(TEXT("building_id"), FString::Printf(TEXT("Building_%02d"), i));

			TArray<TSharedPtr<FJsonValue>> BuildingLoc;
			BuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.X + LotX + LotW * 0.15f));
			BuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Y + LotY + LotH * 0.15f));
			BuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Z));
			BuildingGridParams->SetArrayField(TEXT("location"), BuildingLoc);
			BuildingGridParams->SetStringField(TEXT("folder"), Folder + TEXT("/Buildings"));
			BuildingGridParams->SetBoolField(TEXT("overwrite"), true);
			// omit_exterior_walls is now set automatically by facade_style in create_building_from_grid
		}

		// Pass facade_style through to building generation (v3 integrated facade)
		if (!bSkipFacades && !BlockFacadeStyle.IsEmpty())
		{
			BuildingGridParams->SetStringField(TEXT("facade_style"), BlockFacadeStyle);
			BuildingGridParams->SetNumberField(TEXT("facade_seed"), Seed + i * 31);
		}

		// Fix #3: Transfer decay metadata from BuildingMeta to BuildingGridParams
		// Transfer decay metadata (BuildingMeta is always valid — it's a TSharedRef from MakeShared)
		{
			if (BuildingMeta->HasField(TEXT("decay_level")))
			{
				BuildingGridParams->SetNumberField(TEXT("decay_level"),
					BuildingMeta->GetNumberField(TEXT("decay_level")));
			}
			if (BuildingMeta->HasField(TEXT("tilt_pitch")))
			{
				BuildingGridParams->SetNumberField(TEXT("tilt_pitch"),
					BuildingMeta->GetNumberField(TEXT("tilt_pitch")));
			}
			if (BuildingMeta->HasField(TEXT("tilt_roll")))
			{
				BuildingGridParams->SetNumberField(TEXT("tilt_roll"),
					BuildingMeta->GetNumberField(TEXT("tilt_roll")));
			}
			if (BuildingMeta->HasField(TEXT("boarded_window_pct")))
			{
				BuildingGridParams->SetNumberField(TEXT("boarded_window_pct"),
					BuildingMeta->GetNumberField(TEXT("boarded_window_pct")));
			}
		}

		// Execute SP1: create_building_from_grid
		TSharedPtr<FJsonObject> BuildingResult;
		FString BuildingError;
		bool bBuilt = TryExecuteAction(TEXT("create_building_from_grid"), BuildingGridParams, BuildingResult, BuildingError);

		if (!bBuilt)
		{
			UE_LOG(LogMonolithCityBlock, Error, TEXT("    Building %d geometry generation FAILED: %s"), i, *BuildingError);
			auto FailJson = MakeShared<FJsonObject>();
			FailJson->SetStringField(TEXT("building_id"), FString::Printf(TEXT("Building_%02d"), i));
			FailJson->SetBoolField(TEXT("failed"), true);
			FailJson->SetStringField(TEXT("error"), BuildingError);
			BuildingResults.Add(MakeShared<FJsonValueObject>(FailJson));
			continue;
		}

		UE_LOG(LogMonolithCityBlock, Log, TEXT("    Building %d geometry: OK"), i);

		// Step 4: Facade — now integrated into create_building_from_grid (v3 single-pass)
		// When facade_style is passed to the building generator, it builds exterior walls
		// with window/door openings, frames, trim, and cornices in one mesh. No separate
		// facade actor needed. The old generate_facade action still works standalone.
		if (bSkipFacades || BlockFacadeStyle.IsEmpty())
		{
			SkippedSteps.AddUnique(TEXT("facades"));
		}
		else if (BuildingResult.IsValid() && BuildingResult->HasField(TEXT("integrated_facade")))
		{
			UE_LOG(LogMonolithCityBlock, Log, TEXT("    Facade %d: integrated (%d windows, %d doors)"),
				i,
				BuildingResult->HasField(TEXT("window_count")) ? static_cast<int32>(BuildingResult->GetNumberField(TEXT("window_count"))) : 0,
				BuildingResult->HasField(TEXT("entrance_door_count")) ? static_cast<int32>(BuildingResult->GetNumberField(TEXT("entrance_door_count"))) : 0);
		}
		else
		{
			UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Facade %d: integration failed, no facade generated"), i);
			SkippedSteps.AddUnique(TEXT("facades"));
		}

		// Step 5: Generate roof via SP4 (if not skipped)
		if (!bSkipRoofs)
		{
			auto RoofParams = MakeShared<FJsonObject>();

			// BuildingResult IS the descriptor — pass footprint_polygon and height info
			if (BuildingResult.IsValid())
			{
				if (BuildingResult->HasField(TEXT("footprint_polygon")))
				{
					RoofParams->SetArrayField(TEXT("footprint_polygon"), BuildingResult->GetArrayField(TEXT("footprint_polygon")));
				}

				// Compute roof height from top floor — MUST account for ceiling slab thickness
				// Building structure per floor: [floor_slab=FT] [walls=FH] [ceiling_slab=FT]
				// Roof sits on TOP of the ceiling slab of the top floor
				const TArray<TSharedPtr<FJsonValue>>* FloorsArr = nullptr;
				if (BuildingResult->TryGetArrayField(TEXT("floors"), FloorsArr) && FloorsArr && FloorsArr->Num() > 0)
				{
					const TSharedPtr<FJsonObject>* TopFloor = nullptr;
					if ((*FloorsArr).Last()->TryGetObject(TopFloor) && TopFloor && (*TopFloor).IsValid())
					{
						float ZOff = static_cast<float>((*TopFloor)->GetNumberField(TEXT("z_offset")));
						float FH = static_cast<float>((*TopFloor)->GetNumberField(TEXT("height")));

						// Get slab thickness from building result (WP-3 fix)
						// Each floor has: floor_slab(FT) + walls(FH) + ceiling_slab(FT)
						// ZOff is the base of the floor slab. Top of ceiling = ZOff + FT + FH + FT = ZOff + FH + 2*FT
						float FT = 3.0f; // default
						if (BuildingResult->HasField(TEXT("floor_thickness")))
							FT = static_cast<float>(BuildingResult->GetNumberField(TEXT("floor_thickness")));

						float RoofZ = ZOff + FH + 2.0f * FT;
						RoofParams->SetNumberField(TEXT("height_offset"), RoofZ);
					}
				}

				// Pass building location for roof placement
				if (BuildingResult->HasField(TEXT("world_origin")))
				{
					RoofParams->SetArrayField(TEXT("location"), BuildingResult->GetArrayField(TEXT("world_origin")));
				}
				if (BuildingResult->HasField(TEXT("building_id")))
				{
					RoofParams->SetStringField(TEXT("building_id"), BuildingResult->GetStringField(TEXT("building_id")));
				}
			}

			// Pass roof_type from floor plan result or load directly from archetype
			bool bHasRoofType = false;
			if (FloorPlanResult.IsValid() && FloorPlanResult->HasField(TEXT("roof_type")))
			{
				FString RT = FloorPlanResult->GetStringField(TEXT("roof_type"));
				if (!RT.IsEmpty())
				{
					RoofParams->SetStringField(TEXT("roof_type"), RT);
					bHasRoofType = true;
				}
			}
			if (!bHasRoofType && i < Archetypes.Num())
			{
				FString RoofType = FMonolithMeshFloorPlanGenerator::GetArchetypeRoofType(Archetypes[i]);
				RoofParams->SetStringField(TEXT("roof_type"), RoofType);
			}

			RoofParams->SetStringField(TEXT("save_path"), FString::Printf(TEXT("%s/Roof_%02d"), *SavePathPrefix, i));
			RoofParams->SetStringField(TEXT("folder"), Folder + TEXT("/Roofs"));
			RoofParams->SetNumberField(TEXT("seed"), Seed + i + 2000);
			RoofParams->SetBoolField(TEXT("overwrite"), true);

			TSharedPtr<FJsonObject> RoofResult;
			FString RoofError;
			if (TryExecuteAction(TEXT("generate_roof"), RoofParams, RoofResult, RoofError))
			{
				UE_LOG(LogMonolithCityBlock, Log, TEXT("    Roof %d: OK"), i);
				if (BuildingResult.IsValid() && RoofResult.IsValid())
				{
					BuildingResult->SetObjectField(TEXT("roof"), RoofResult);
				}
			}
			else
			{
				UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Roof %d skipped (SP4 not available): %s"), i, *RoofError);
				SkippedSteps.AddUnique(TEXT("roofs"));
			}
		}
		else
		{
			SkippedSteps.AddUnique(TEXT("roofs"));
		}

		// Register building in spatial registry via SP6
		{
			auto RegParams = MakeShared<FJsonObject>();
			RegParams->SetStringField(TEXT("building_id"), FString::Printf(TEXT("Building_%02d"), i));

			if (BuildingResult.IsValid())
			{
				RegParams->SetObjectField(TEXT("building_descriptor"), BuildingResult);
			}

			TSharedPtr<FJsonObject> RegResult;
			FString RegError;
			if (TryExecuteAction(TEXT("register_building"), RegParams, RegResult, RegError))
			{
				UE_LOG(LogMonolithCityBlock, Log, TEXT("    Registered building %d in spatial registry"), i);
			}
			else
			{
				UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Spatial registry skipped: %s"), *RegError);
				SkippedSteps.AddUnique(TEXT("spatial_registry"));
			}
		}

		// Fix #6: Wire furnish_building — furnish interior of each building
		if (!bSkipFurnishing)
		{
			const FString BuildingId = FString::Printf(TEXT("Building_%02d"), i);
			auto FurnishParams = MakeShared<FJsonObject>();
			FurnishParams->SetStringField(TEXT("building_id"), BuildingId);
			if (BuildingResult.IsValid())
			{
				FurnishParams->SetObjectField(TEXT("building_descriptor"), BuildingResult);
			}
			FurnishParams->SetStringField(TEXT("save_path_prefix"), SavePathPrefix + TEXT("/Furniture"));
			FurnishParams->SetStringField(TEXT("folder"), Folder + TEXT("/Furniture"));
			FurnishParams->SetNumberField(TEXT("seed"), Seed + i + 5000);
			if (Decay > 0.0f)
			{
				FurnishParams->SetNumberField(TEXT("decay"), Decay);
			}

			TSharedPtr<FJsonObject> FurnishResult;
			FString FurnishError;
			if (TryExecuteAction(TEXT("furnish_building"), FurnishParams, FurnishResult, FurnishError))
			{
				UE_LOG(LogMonolithCityBlock, Log, TEXT("    Furnish %d: OK"), i);
				if (BuildingResult.IsValid() && FurnishResult.IsValid())
				{
					BuildingResult->SetObjectField(TEXT("furnishing"), FurnishResult);
				}
			}
			else
			{
				UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Furnish %d skipped: %s"), i, *FurnishError);
				SkippedSteps.AddUnique(TEXT("furnishing"));
			}
		}
		else
		{
			SkippedSteps.AddUnique(TEXT("furnishing"));
		}

		// Fix #7: Wire auto_volumes_for_building — generate navmesh/audio volumes
		if (!bSkipVolumes)
		{
			const FString BuildingId = FString::Printf(TEXT("Building_%02d"), i);
			auto VolParams = MakeShared<FJsonObject>();
			VolParams->SetStringField(TEXT("building_id"), BuildingId);
			if (BuildingResult.IsValid())
			{
				VolParams->SetObjectField(TEXT("building_descriptor"), BuildingResult);
			}
			VolParams->SetStringField(TEXT("folder"), Folder + TEXT("/Volumes"));

			TSharedPtr<FJsonObject> VolResult;
			FString VolError;
			if (TryExecuteAction(TEXT("auto_volumes_for_building"), VolParams, VolResult, VolError))
			{
				UE_LOG(LogMonolithCityBlock, Log, TEXT("    Volumes %d: OK"), i);
				if (BuildingResult.IsValid() && VolResult.IsValid())
				{
					BuildingResult->SetObjectField(TEXT("volumes"), VolResult);
				}
			}
			else
			{
				UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Volumes %d skipped: %s"), i, *VolError);
				SkippedSteps.AddUnique(TEXT("volumes"));
			}
		}
		else
		{
			SkippedSteps.AddUnique(TEXT("volumes"));
		}

		// ---- Post-generation validation ----
		if (!bSkipValidation)
		{
			const FString BuildingId = FString::Printf(TEXT("Building_%02d"), i);

			auto ValParams = MakeShared<FJsonObject>();
			ValParams->SetStringField(TEXT("building_id"), BuildingId);
			ValParams->SetBoolField(TEXT("check_doors"), true);
			ValParams->SetBoolField(TEXT("check_connectivity"), true);
			ValParams->SetBoolField(TEXT("check_stairs"), true);

			TSharedPtr<FJsonObject> ValResult;
			FString ValError;
			if (TryExecuteAction(TEXT("validate_building"), ValParams, ValResult, ValError))
			{
				float ValScore = ValResult.IsValid() && ValResult->HasField(TEXT("score"))
					? static_cast<float>(ValResult->GetNumberField(TEXT("score"))) : 1.0f;

				UE_LOG(LogMonolithCityBlock, Log, TEXT("    Validation building %d: score=%.2f"), i, ValScore);

				// Retry logic: if score < 0.5 and validate_and_retry is enabled
				if (bValidateAndRetry && ValScore < 0.5f)
				{
					float BestScore = ValScore;
					TSharedPtr<FJsonObject> BestValResult = ValResult;
					TSharedPtr<FJsonObject> BestBuildingResult = BuildingResult;

					constexpr int32 MaxRetries = 2;
					for (int32 Retry = 1; Retry <= MaxRetries; ++Retry)
					{
						const int32 RetrySeed = Seed + i + Retry * 100;
						UE_LOG(LogMonolithCityBlock, Log, TEXT("    Retry %d/%d for building %d (score %.2f < 0.5), seed=%d"),
							Retry, MaxRetries, i, BestScore, RetrySeed);

						// Fix #4: Regenerate floor plan with new seed BEFORE rebuilding geometry
						FloorPlanParams->SetNumberField(TEXT("seed"), RetrySeed);
						TSharedPtr<FJsonObject> RetryFloorPlan;
						FString RetryFPError;
						if (TryExecuteAction(TEXT("generate_floor_plan"), FloorPlanParams, RetryFloorPlan, RetryFPError)
							&& RetryFloorPlan.IsValid())
						{
							// Use the new floor plan as the building grid params
							BuildingGridParams = RetryFloorPlan;
							// Re-apply building metadata that was on the original params
							BuildingGridParams->SetStringField(TEXT("save_path"), BuildingAssetPath);
							BuildingGridParams->SetStringField(TEXT("building_id"), FString::Printf(TEXT("Building_%02d"), i));

							TArray<TSharedPtr<FJsonValue>> RetryBuildingLoc;
							RetryBuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.X + LotX + LotW * 0.15f));
							RetryBuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Y + LotY + LotH * 0.15f));
							RetryBuildingLoc.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Z));
							BuildingGridParams->SetArrayField(TEXT("location"), RetryBuildingLoc);
							BuildingGridParams->SetStringField(TEXT("folder"), Folder + TEXT("/Buildings"));
							BuildingGridParams->SetBoolField(TEXT("overwrite"), true);

							if (!bSkipFacades && !BlockFacadeStyle.IsEmpty())
							{
								BuildingGridParams->SetStringField(TEXT("facade_style"), BlockFacadeStyle);
								BuildingGridParams->SetNumberField(TEXT("facade_seed"), RetrySeed + i * 31);
							}

							// Re-apply decay metadata
							// Re-apply decay metadata (BuildingMeta is TSharedRef, always valid)
							{
								if (BuildingMeta->HasField(TEXT("decay_level")))
									BuildingGridParams->SetNumberField(TEXT("decay_level"), BuildingMeta->GetNumberField(TEXT("decay_level")));
								if (BuildingMeta->HasField(TEXT("tilt_pitch")))
									BuildingGridParams->SetNumberField(TEXT("tilt_pitch"), BuildingMeta->GetNumberField(TEXT("tilt_pitch")));
								if (BuildingMeta->HasField(TEXT("tilt_roll")))
									BuildingGridParams->SetNumberField(TEXT("tilt_roll"), BuildingMeta->GetNumberField(TEXT("tilt_roll")));
								if (BuildingMeta->HasField(TEXT("boarded_window_pct")))
									BuildingGridParams->SetNumberField(TEXT("boarded_window_pct"), BuildingMeta->GetNumberField(TEXT("boarded_window_pct")));
							}
						}
						else
						{
							UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Retry %d floor plan regen failed: %s (using previous grid)"), Retry, *RetryFPError);
						}

						// Rebuild geometry with (possibly new) grid params
						BuildingGridParams->SetNumberField(TEXT("seed"), RetrySeed);
						BuildingGridParams->SetBoolField(TEXT("overwrite"), true);

						TSharedPtr<FJsonObject> RetryBuildResult;
						FString RetryBuildError;
						if (!TryExecuteAction(TEXT("create_building_from_grid"), BuildingGridParams, RetryBuildResult, RetryBuildError))
						{
							UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Retry %d build failed: %s"), Retry, *RetryBuildError);
							continue;
						}

						// Re-register in spatial registry
						auto RetryRegParams = MakeShared<FJsonObject>();
						RetryRegParams->SetStringField(TEXT("building_id"), BuildingId);
						if (RetryBuildResult.IsValid())
						{
							RetryRegParams->SetObjectField(TEXT("building_descriptor"), RetryBuildResult);
						}
						TSharedPtr<FJsonObject> RetryRegResult;
						FString RetryRegError;
						TryExecuteAction(TEXT("register_building"), RetryRegParams, RetryRegResult, RetryRegError);

						// Re-validate
						TSharedPtr<FJsonObject> RetryValResult;
						FString RetryValError;
						if (TryExecuteAction(TEXT("validate_building"), ValParams, RetryValResult, RetryValError))
						{
							float RetryScore = RetryValResult.IsValid() && RetryValResult->HasField(TEXT("score"))
								? static_cast<float>(RetryValResult->GetNumberField(TEXT("score"))) : 0.0f;

							UE_LOG(LogMonolithCityBlock, Log, TEXT("    Retry %d score: %.2f (best: %.2f)"), Retry, RetryScore, BestScore);

							if (RetryScore > BestScore)
							{
								BestScore = RetryScore;
								BestValResult = RetryValResult;
								BestBuildingResult = RetryBuildResult;
							}

							// Early out if we pass
							if (BestScore >= 0.5f)
							{
								break;
							}
						}
						else
						{
							UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Retry %d validation failed: %s"), Retry, *RetryValError);
						}
					}

					// Use the best attempt
					ValResult = BestValResult;
					ValScore = BestScore;
					BuildingResult = BestBuildingResult;

					UE_LOG(LogMonolithCityBlock, Log, TEXT("    Final score for building %d after retries: %.2f"), i, ValScore);
				}

				// Track validation stats
				BuildingsValidated++;
				ValidationScoreSum += ValScore;
				bool bPassed = ValResult.IsValid() && ValResult->HasField(TEXT("valid"))
					? ValResult->GetBoolField(TEXT("valid")) : (ValScore >= 0.5f);
				if (bPassed)
				{
					BuildingsPassed++;
				}

				// Attach validation to building result
				if (BuildingResult.IsValid())
				{
					BuildingResult->SetObjectField(TEXT("validation"), ValResult);
				}
			}
			else
			{
				UE_LOG(LogMonolithCityBlock, Warning, TEXT("    Validation skipped (action unavailable): %s"), *ValError);
				SkippedSteps.AddUnique(TEXT("validation"));
			}
		}
		else
		{
			SkippedSteps.AddUnique(TEXT("validation"));
		}

		// Add to results
		if (BuildingResult.IsValid())
		{
			BuildingResult->SetStringField(TEXT("building_id"), FString::Printf(TEXT("Building_%02d"), i));
			BuildingResult->SetNumberField(TEXT("lot_index"), i);
			BuildingResults.Add(MakeShared<FJsonValueObject>(BuildingResult));
		}
	}

	// ---- Step 6: Streets ----

	TArray<TSharedPtr<FJsonValue>> StreetResults;

	if (!bSkipStreets)
	{
		// Parse street segments from lot result
		const TArray<TSharedPtr<FJsonValue>>* StreetsArr = nullptr;
		if (LotResult.Result->TryGetArrayField(TEXT("streets"), StreetsArr) && StreetsArr)
		{
			int32 StreetIdx = 0;
			for (const auto& StreetVal : *StreetsArr)
			{
				const TSharedPtr<FJsonObject>* StreetObj = nullptr;
				if (!StreetVal->TryGetObject(StreetObj) || !StreetObj || !(*StreetObj).IsValid())
				{
					continue;
				}

				const TArray<TSharedPtr<FJsonValue>>* SArr = nullptr;
				const TArray<TSharedPtr<FJsonValue>>* EArr = nullptr;
				if (!(*StreetObj)->TryGetArrayField(TEXT("start"), SArr) || !SArr || SArr->Num() < 2) continue;
				if (!(*StreetObj)->TryGetArrayField(TEXT("end"), EArr) || !EArr || EArr->Num() < 2) continue;

				auto StreetParams = MakeShared<FJsonObject>();

				// Offset start/end to world coords
				TArray<TSharedPtr<FJsonValue>> WorldStart, WorldEnd;
				WorldStart.Add(MakeShared<FJsonValueNumber>(BlockOrigin.X + (*SArr)[0]->AsNumber()));
				WorldStart.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Y + (*SArr)[1]->AsNumber()));
				WorldEnd.Add(MakeShared<FJsonValueNumber>(BlockOrigin.X + (*EArr)[0]->AsNumber()));
				WorldEnd.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Y + (*EArr)[1]->AsNumber()));

				StreetParams->SetArrayField(TEXT("start"), WorldStart);
				StreetParams->SetArrayField(TEXT("end"), WorldEnd);
				StreetParams->SetStringField(TEXT("save_path"), FString::Printf(TEXT("%s/Street_%02d"), *SavePathPrefix, StreetIdx));
				StreetParams->SetNumberField(TEXT("width"), StreetWidth);
				StreetParams->SetNumberField(TEXT("sidewalk_width"), SidewalkWidth);
				StreetParams->SetStringField(TEXT("label"), FString::Printf(TEXT("Street_%02d"), StreetIdx));
				StreetParams->SetStringField(TEXT("folder"), Folder + TEXT("/Streets"));

				TSharedPtr<FJsonObject> StreetResult;
				FString StreetError;
				// Call our own CreateStreet directly — it's part of this class, no need to go through registry
				FMonolithActionResult SR = CreateStreet(StreetParams);
				if (SR.bSuccess)
				{
					UE_LOG(LogMonolithCityBlock, Log, TEXT("  Street %d: OK"), StreetIdx);
					StreetResults.Add(MakeShared<FJsonValueObject>(SR.Result));
				}
				else
				{
					UE_LOG(LogMonolithCityBlock, Warning, TEXT("  Street %d failed: %s"), StreetIdx, *SR.ErrorMessage);
				}

				++StreetIdx;
			}
		}
	}
	else
	{
		SkippedSteps.AddUnique(TEXT("streets"));
	}

	// ---- Step 7: Street furniture ----
	// Fix #5: Place furniture on ALL street segments, not just the south street

	TArray<TSharedPtr<FJsonValue>> FurnitureResults;

	if (!bSkipFurniture && !bSkipStreets)
	{
		TArray<FString> FurnitureTypes = GetGenreFurniture(Genre);

		// Build shared types array once
		TArray<TSharedPtr<FJsonValue>> TypesArr;
		for (const FString& FT : FurnitureTypes)
		{
			TypesArr.Add(MakeShared<FJsonValueString>(FT));
		}

		// Parse street segments from lot layout results
		const TArray<TSharedPtr<FJsonValue>>* FurnStreetsArr = nullptr;
		if (LotResult.Result->TryGetArrayField(TEXT("streets"), FurnStreetsArr) && FurnStreetsArr)
		{
			for (int32 FurnIdx = 0; FurnIdx < FurnStreetsArr->Num(); ++FurnIdx)
			{
				const TSharedPtr<FJsonObject>* StreetObj = nullptr;
				if (!(*FurnStreetsArr)[FurnIdx]->TryGetObject(StreetObj) || !StreetObj || !(*StreetObj).IsValid())
				{
					continue;
				}

				const TArray<TSharedPtr<FJsonValue>>* SArr = nullptr;
				const TArray<TSharedPtr<FJsonValue>>* EArr = nullptr;
				if (!(*StreetObj)->TryGetArrayField(TEXT("start"), SArr) || !SArr || SArr->Num() < 2) continue;
				if (!(*StreetObj)->TryGetArrayField(TEXT("end"), EArr) || !EArr || EArr->Num() < 2) continue;

				auto FurnParams = MakeShared<FJsonObject>();

				// Offset to world coords (same as street generation)
				TArray<TSharedPtr<FJsonValue>> WorldStart, WorldEnd;
				WorldStart.Add(MakeShared<FJsonValueNumber>(BlockOrigin.X + (*SArr)[0]->AsNumber()));
				WorldStart.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Y + (*SArr)[1]->AsNumber()));
				WorldEnd.Add(MakeShared<FJsonValueNumber>(BlockOrigin.X + (*EArr)[0]->AsNumber()));
				WorldEnd.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Y + (*EArr)[1]->AsNumber()));

				FurnParams->SetArrayField(TEXT("street_start"), WorldStart);
				FurnParams->SetArrayField(TEXT("street_end"), WorldEnd);
				FurnParams->SetArrayField(TEXT("types"), TypesArr);
				FurnParams->SetNumberField(TEXT("spacing"), 800.0);
				FurnParams->SetNumberField(TEXT("offset"), StreetWidth * 0.5f + SidewalkWidth * 0.5f);
				FurnParams->SetNumberField(TEXT("seed"), Seed + 5000 + FurnIdx);
				FurnParams->SetNumberField(TEXT("decay"), Decay);
				FurnParams->SetStringField(TEXT("folder"), Folder + TEXT("/Furniture"));
				FurnParams->SetStringField(TEXT("save_path_prefix"), SavePathPrefix);

				FMonolithActionResult FurnResult = PlaceStreetFurniture(FurnParams);
				if (FurnResult.bSuccess)
				{
					FurnitureResults.Add(MakeShared<FJsonValueObject>(FurnResult.Result));
					UE_LOG(LogMonolithCityBlock, Log, TEXT("  Street furniture %d: OK"), FurnIdx);
				}
				else
				{
					UE_LOG(LogMonolithCityBlock, Warning, TEXT("  Street furniture %d failed: %s"), FurnIdx, *FurnResult.ErrorMessage);
				}
			}
		}

		if (FurnitureResults.Num() > 0)
		{
			UE_LOG(LogMonolithCityBlock, Log, TEXT("  Street furniture: %d segments furnished"), FurnitureResults.Num());
		}
	}
	else
	{
		SkippedSteps.AddUnique(TEXT("furniture"));
	}

	// ---- Step 9: Build final result ----

	auto Result = MakeShared<FJsonObject>();

	// Block metadata
	Result->SetStringField(TEXT("save_path_prefix"), SavePathPrefix);
	Result->SetStringField(TEXT("genre"), Genre);
	Result->SetNumberField(TEXT("seed"), Seed);
	Result->SetNumberField(TEXT("decay"), Decay);

	TArray<TSharedPtr<FJsonValue>> BlockSizeFinal;
	BlockSizeFinal.Add(MakeShared<FJsonValueNumber>(BlockWidth));
	BlockSizeFinal.Add(MakeShared<FJsonValueNumber>(BlockHeight));
	Result->SetArrayField(TEXT("block_size"), BlockSizeFinal);

	TArray<TSharedPtr<FJsonValue>> OriginArr;
	OriginArr.Add(MakeShared<FJsonValueNumber>(BlockOrigin.X));
	OriginArr.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Y));
	OriginArr.Add(MakeShared<FJsonValueNumber>(BlockOrigin.Z));
	Result->SetArrayField(TEXT("origin"), OriginArr);

	// Lots
	Result->SetObjectField(TEXT("lot_layout"), LotResult.Result);

	// Buildings
	Result->SetArrayField(TEXT("buildings"), BuildingResults);
	Result->SetNumberField(TEXT("buildings_generated"), BuildingResults.Num());
	Result->SetNumberField(TEXT("buildings_destroyed"), DestroyedBuildings.Num());

	// Validation summary
	if (!bSkipValidation && BuildingsValidated > 0)
	{
		auto ValSummary = MakeShared<FJsonObject>();
		ValSummary->SetNumberField(TEXT("buildings_validated"), BuildingsValidated);
		ValSummary->SetNumberField(TEXT("buildings_passed"), BuildingsPassed);
		ValSummary->SetNumberField(TEXT("average_score"),
			FMath::RoundToFloat(static_cast<float>(ValidationScoreSum / BuildingsValidated) * 100.0f) / 100.0f);
		Result->SetObjectField(TEXT("validation_summary"), ValSummary);
	}

	// Streets
	Result->SetArrayField(TEXT("streets"), StreetResults);

	// Furniture
	if (FurnitureResults.Num() > 0)
	{
		Result->SetArrayField(TEXT("furniture"), FurnitureResults);
	}

	// Skipped steps
	if (SkippedSteps.Num() > 0)
	{
		TArray<TSharedPtr<FJsonValue>> SkippedArr;
		for (const FString& S : SkippedSteps)
		{
			SkippedArr.Add(MakeShared<FJsonValueString>(S));
		}
		Result->SetArrayField(TEXT("skipped_steps"), SkippedArr);
	}

	UE_LOG(LogMonolithCityBlock, Log, TEXT("=== create_city_block COMPLETE: %d buildings, %d streets, %d skipped steps ==="),
		BuildingResults.Num(), StreetResults.Num(), SkippedSteps.Num());

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_GEOMETRYSCRIPT
