#if WITH_GEOMETRYSCRIPT

#include "MonolithMeshTerrainActions.h"
#include "MonolithMeshBuildingTypes.h"
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
#include "GeometryScript/MeshBooleanFunctions.h"
#include "GeometryScript/MeshNormalsFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "GeometryScript/MeshTransformFunctions.h"

#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Editor.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

using namespace UE::Geometry;

static const FString GS_ERROR_TERRAIN = TEXT("Enable the GeometryScripting plugin in your .uproject to use terrain/foundation actions.");

UMonolithMeshHandlePool* FMonolithMeshTerrainActions::Pool = nullptr;

void FMonolithMeshTerrainActions::SetHandlePool(UMonolithMeshHandlePool* InPool)
{
	Pool = InPool;
}

// ============================================================================
// Strategy helpers
// ============================================================================

FString FMonolithMeshTerrainActions::StrategyToString(EFoundationStrategy S)
{
	switch (S)
	{
	case EFoundationStrategy::Flat:             return TEXT("flat");
	case EFoundationStrategy::CutAndFill:       return TEXT("cut_and_fill");
	case EFoundationStrategy::Stepped:          return TEXT("stepped");
	case EFoundationStrategy::Piers:            return TEXT("piers");
	case EFoundationStrategy::WalkoutBasement:  return TEXT("walkout_basement");
	}
	return TEXT("flat");
}

FMonolithMeshTerrainActions::EFoundationStrategy FMonolithMeshTerrainActions::StringToStrategy(const FString& S)
{
	if (S == TEXT("cut_and_fill"))       return EFoundationStrategy::CutAndFill;
	if (S == TEXT("stepped"))            return EFoundationStrategy::Stepped;
	if (S == TEXT("piers"))              return EFoundationStrategy::Piers;
	if (S == TEXT("walkout_basement"))   return EFoundationStrategy::WalkoutBasement;
	return EFoundationStrategy::Flat;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshTerrainActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ---- sample_terrain_grid ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("sample_terrain_grid"),
		TEXT("Sample an NxM grid of terrain heights via downward line traces. "
			"Returns a 2D height grid, min/max/avg Z, slope analysis, and roughness. "
			"Output feeds into analyze_building_site and create_foundation."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTerrainActions::SampleTerrainGrid),
		FParamSchemaBuilder()
			.Required(TEXT("center"), TEXT("array"), TEXT("Center of the sample area [x, y, z]"))
			.Required(TEXT("size"), TEXT("array"), TEXT("Sample area dimensions [width, height] in cm"))
			.Optional(TEXT("grid_resolution"), TEXT("integer"), TEXT("NxN sample points per axis"), TEXT("8"))
			.Optional(TEXT("trace_height"), TEXT("number"), TEXT("Start height above center for traces"), TEXT("5000"))
			.Optional(TEXT("trace_depth"), TEXT("number"), TEXT("How far below center to trace"), TEXT("10000"))
			.Optional(TEXT("channel"), TEXT("string"), TEXT("Trace channel name"), TEXT("Visibility"))
			.Build());

	// ---- analyze_building_site ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_building_site"),
		TEXT("Given a building footprint polygon and terrain samples, determine the optimal foundation strategy "
			"(flat, cut_and_fill, stepped, piers, walkout_basement). Returns strategy, slope, pad Z, and ramp specs if hospice mode."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTerrainActions::AnalyzeBuildingSite),
		FParamSchemaBuilder()
			.Required(TEXT("footprint_polygon"), TEXT("array"), TEXT("Building footprint as [[x,y], ...] points in world space"))
			.Required(TEXT("terrain_samples"), TEXT("object"), TEXT("Output from sample_terrain_grid"))
			.Optional(TEXT("floor_height"), TEXT("number"), TEXT("Building floor height in cm"), TEXT("270"))
			.Optional(TEXT("hospice_mode"), TEXT("boolean"), TEXT("Require ADA-compliant ramps"), TEXT("false"))
			.Build());

	// ---- create_foundation ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_foundation"),
		TEXT("Generate foundation geometry for a building on terrain. Supports flat pad, cut-and-fill, stepped, "
			"pier, and walkout basement strategies. Saves to StaticMesh and optionally places in scene."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTerrainActions::CreateFoundation),
		FParamSchemaBuilder()
			.Required(TEXT("strategy"), TEXT("string"), TEXT("Foundation type: flat, cut_and_fill, stepped, piers, walkout_basement"))
			.Required(TEXT("footprint_polygon"), TEXT("array"), TEXT("Building footprint [[x,y], ...] in world space"))
			.Required(TEXT("terrain_samples"), TEXT("object"), TEXT("Output from sample_terrain_grid"))
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the foundation mesh"))
			.Optional(TEXT("pad_z"), TEXT("number"), TEXT("Target Z for the building pad (auto-computed if omitted)"))
			.Optional(TEXT("floor_height"), TEXT("number"), TEXT("Building floor height in cm"), TEXT("270"))
			.Optional(TEXT("pier_diameter"), TEXT("number"), TEXT("Pier column diameter (pier strategy)"), TEXT("30"))
			.Optional(TEXT("pier_spacing"), TEXT("number"), TEXT("Spacing between piers"), TEXT("200"))
			.Optional(TEXT("material_foundation"), TEXT("string"), TEXT("Material asset path for foundation"))
			.Optional(TEXT("material_pier"), TEXT("string"), TEXT("Material asset path for pier columns"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x, y, z]"))
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Allow overwriting existing asset"), TEXT("false"))
			.Build());

	// ---- create_retaining_wall ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_retaining_wall"),
		TEXT("Generate a retaining wall along a terrain cut edge. Wall height varies along its length "
			"based on terrain samples. Tapered profile (thicker at base)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTerrainActions::CreateRetainingWall),
		FParamSchemaBuilder()
			.Required(TEXT("start"), TEXT("array"), TEXT("Wall start point [x, y, z]"))
			.Required(TEXT("end"), TEXT("array"), TEXT("Wall end point [x, y, z]"))
			.Required(TEXT("terrain_samples"), TEXT("object"), TEXT("Output from sample_terrain_grid"))
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the retaining wall mesh"))
			.Optional(TEXT("thickness"), TEXT("number"), TEXT("Wall base thickness in cm"), TEXT("20"))
			.Optional(TEXT("cap_height"), TEXT("number"), TEXT("Height above terrain at the cap"), TEXT("10"))
			.Optional(TEXT("material"), TEXT("string"), TEXT("Material asset path"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x, y, z]"))
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Build());

	// ---- place_building_on_terrain ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("place_building_on_terrain"),
		TEXT("Full pipeline: sample terrain under building footprint, analyze site, generate foundation, "
			"and adjust building Z. Optionally creates retaining walls and ADA ramps (hospice mode)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTerrainActions::PlaceBuildingOnTerrain),
		FParamSchemaBuilder()
			.Required(TEXT("building_descriptor"), TEXT("object"), TEXT("Full Building Descriptor JSON from create_building_from_grid"))
			.RequiredAssetPath(TEXT("save_path_prefix"), TEXT("Base asset path for generated foundation/retaining wall meshes"))
			.Optional(TEXT("terrain_samples"), TEXT("object"), TEXT("Pre-computed terrain samples (auto-sampled if omitted)"))
			.Optional(TEXT("hospice_mode"), TEXT("boolean"), TEXT("Generate ADA-compliant ramps"), TEXT("false"))
			.Optional(TEXT("create_retaining_walls"), TEXT("boolean"), TEXT("Auto-create retaining walls for cut sites"), TEXT("true"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("seed"), TEXT("integer"), TEXT("Random seed for any procedural variation"))
			.Build());
}

// ============================================================================
// Polygon / Math Helpers
// ============================================================================

FBox2D FMonolithMeshTerrainActions::ComputePolygonBounds(const TArray<FVector2D>& Polygon)
{
	FBox2D Bounds(ForceInit);
	for (const FVector2D& P : Polygon)
	{
		Bounds += P;
	}
	return Bounds;
}

bool FMonolithMeshTerrainActions::IsPointInPolygon(const FVector2D& Point, const TArray<FVector2D>& Polygon)
{
	int32 N = Polygon.Num();
	if (N < 3) return false;

	bool bInside = false;
	for (int32 I = 0, J = N - 1; I < N; J = I++)
	{
		const FVector2D& A = Polygon[I];
		const FVector2D& B = Polygon[J];
		if (((A.Y > Point.Y) != (B.Y > Point.Y)) &&
			(Point.X < (B.X - A.X) * (Point.Y - A.Y) / (B.Y - A.Y) + A.X))
		{
			bInside = !bInside;
		}
	}
	return bInside;
}

float FMonolithMeshTerrainActions::InterpolateTerrainZ(const FTerrainSample& Terrain, float WorldX, float WorldY)
{
	if (Terrain.GridResX < 2 || Terrain.GridResY < 2)
	{
		return Terrain.AvgZ;
	}

	// Convert world XY to grid UV [0,1]
	float HalfW = Terrain.SampleSize.X * 0.5f;
	float HalfH = Terrain.SampleSize.Y * 0.5f;
	float U = (WorldX - (Terrain.Center.X - HalfW)) / Terrain.SampleSize.X;
	float V = (WorldY - (Terrain.Center.Y - HalfH)) / Terrain.SampleSize.Y;

	U = FMath::Clamp(U, 0.0f, 1.0f);
	V = FMath::Clamp(V, 0.0f, 1.0f);

	// Map to grid indices
	float GX = U * (Terrain.GridResX - 1);
	float GY = V * (Terrain.GridResY - 1);
	int32 X0 = FMath::FloorToInt32(GX);
	int32 Y0 = FMath::FloorToInt32(GY);
	int32 X1 = FMath::Min(X0 + 1, Terrain.GridResX - 1);
	int32 Y1 = FMath::Min(Y0 + 1, Terrain.GridResY - 1);
	float FX = GX - X0;
	float FY = GY - Y0;

	float Z00 = Terrain.Heights[Y0][X0];
	float Z10 = Terrain.Heights[Y0][X1];
	float Z01 = Terrain.Heights[Y1][X0];
	float Z11 = Terrain.Heights[Y1][X1];

	// Bilinear interpolation
	float ZTop = FMath::Lerp(Z00, Z10, FX);
	float ZBot = FMath::Lerp(Z01, Z11, FX);
	return FMath::Lerp(ZTop, ZBot, FY);
}

bool FMonolithMeshTerrainActions::ParsePolygon(const TSharedPtr<FJsonObject>& Params, const FString& Key,
	TArray<FVector2D>& Out, FString& OutError)
{
	const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
	if (!Params->TryGetArrayField(Key, Arr) || !Arr || Arr->Num() < 3)
	{
		OutError = FString::Printf(TEXT("'%s' must be an array of at least 3 [x,y] points"), *Key);
		return false;
	}

	for (const TSharedPtr<FJsonValue>& Val : *Arr)
	{
		const TArray<TSharedPtr<FJsonValue>>* Inner = nullptr;
		if (!Val->TryGetArray(Inner) || !Inner || Inner->Num() < 2)
		{
			OutError = FString::Printf(TEXT("Each point in '%s' must be [x, y]"), *Key);
			return false;
		}
		Out.Add(FVector2D((*Inner)[0]->AsNumber(), (*Inner)[1]->AsNumber()));
	}
	return true;
}

// ============================================================================
// Terrain Sampling
// ============================================================================

bool FMonolithMeshTerrainActions::SampleTerrain(UWorld* World, const FVector& Center, const FVector2D& Size,
	int32 ResX, int32 ResY, float TraceHeight, float TraceDepth,
	ECollisionChannel Channel, FTerrainSample& OutSample, FString& OutError)
{
	if (!World)
	{
		OutError = TEXT("No editor world available");
		return false;
	}

	if (ResX < 2 || ResY < 2)
	{
		OutError = TEXT("grid_resolution must be >= 2");
		return false;
	}

	if (Size.X <= 0.0f || Size.Y <= 0.0f)
	{
		OutError = TEXT("size must have positive width and height");
		return false;
	}

	OutSample = FTerrainSample();
	OutSample.Center = Center;
	OutSample.SampleSize = Size;
	OutSample.GridResX = ResX;
	OutSample.GridResY = ResY;

	float HalfW = Size.X * 0.5f;
	float HalfH = Size.Y * 0.5f;
	float StartX = Center.X - HalfW;
	float StartY = Center.Y - HalfH;
	float StepX = Size.X / (ResX - 1);
	float StepY = Size.Y / (ResY - 1);

	FCollisionQueryParams QP(SCENE_QUERY_STAT(MonolithTerrainSample), true);
	QP.bReturnPhysicalMaterial = false;

	OutSample.Heights.SetNum(ResY);
	OutSample.Normals.SetNum(ResY);

	double SumZ = 0.0;
	FVector SumNormal = FVector::ZeroVector;
	int32 HitCount = 0;

	for (int32 Row = 0; Row < ResY; ++Row)
	{
		OutSample.Heights[Row].SetNum(ResX);
		OutSample.Normals[Row].SetNum(ResX);

		for (int32 Col = 0; Col < ResX; ++Col)
		{
			float X = StartX + Col * StepX;
			float Y = StartY + Row * StepY;

			FVector TraceStart(X, Y, Center.Z + TraceHeight);
			FVector TraceEnd(X, Y, Center.Z - TraceDepth);

			FHitResult Hit;
			bool bHit = World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, Channel, QP);

			if (bHit)
			{
				float Z = Hit.ImpactPoint.Z;
				OutSample.Heights[Row][Col] = Z;
				OutSample.Normals[Row][Col] = Hit.ImpactNormal;
				OutSample.MinZ = FMath::Min(OutSample.MinZ, Z);
				OutSample.MaxZ = FMath::Max(OutSample.MaxZ, Z);
				SumZ += Z;
				SumNormal += Hit.ImpactNormal;
				++HitCount;
			}
			else
			{
				// No hit — use center Z as fallback
				OutSample.Heights[Row][Col] = Center.Z;
				OutSample.Normals[Row][Col] = FVector::UpVector;
				OutSample.bAllHit = false;
			}
		}
	}

	if (HitCount == 0)
	{
		OutSample.MinZ = Center.Z;
		OutSample.MaxZ = Center.Z;
		OutSample.AvgZ = Center.Z;
		return true; // Valid but empty — no geometry below
	}

	OutSample.AvgZ = static_cast<float>(SumZ / HitCount);
	OutSample.HeightDiff = OutSample.MaxZ - OutSample.MinZ;
	OutSample.AvgNormal = SumNormal.GetSafeNormal();
	if (OutSample.AvgNormal.IsNearlyZero())
	{
		OutSample.AvgNormal = FVector::UpVector;
	}

	// Slope from average normal
	OutSample.AvgSlopeDegrees = FMath::RadiansToDegrees(
		FMath::Acos(FMath::Clamp(FVector::DotProduct(OutSample.AvgNormal, FVector::UpVector), -1.0f, 1.0f)));

	// Slope direction: project average normal onto XY plane
	FVector SlopeDir2D = FVector(OutSample.AvgNormal.X, OutSample.AvgNormal.Y, 0.0f);
	if (!SlopeDir2D.IsNearlyZero())
	{
		OutSample.SlopeDirection = SlopeDir2D.GetSafeNormal();
	}

	// Roughness: standard deviation of heights
	double SumSqDev = 0.0;
	for (int32 Row = 0; Row < ResY; ++Row)
	{
		for (int32 Col = 0; Col < ResX; ++Col)
		{
			double Dev = OutSample.Heights[Row][Col] - OutSample.AvgZ;
			SumSqDev += Dev * Dev;
		}
	}
	OutSample.Roughness = static_cast<float>(FMath::Sqrt(SumSqDev / (ResX * ResY)));

	return true;
}

TSharedPtr<FJsonObject> FMonolithMeshTerrainActions::TerrainSampleToJson(const FTerrainSample& Sample)
{
	auto J = MakeShared<FJsonObject>();

	// Heights 2D array
	TArray<TSharedPtr<FJsonValue>> RowsArr;
	for (int32 Row = 0; Row < Sample.GridResY; ++Row)
	{
		TArray<TSharedPtr<FJsonValue>> ColArr;
		for (int32 Col = 0; Col < Sample.GridResX; ++Col)
		{
			ColArr.Add(MakeShared<FJsonValueNumber>(Sample.Heights[Row][Col]));
		}
		RowsArr.Add(MakeShared<FJsonValueArray>(ColArr));
	}
	J->SetArrayField(TEXT("samples"), RowsArr);

	J->SetNumberField(TEXT("min_z"), Sample.MinZ);
	J->SetNumberField(TEXT("max_z"), Sample.MaxZ);
	J->SetNumberField(TEXT("avg_z"), Sample.AvgZ);
	J->SetNumberField(TEXT("height_diff"), Sample.HeightDiff);
	J->SetNumberField(TEXT("avg_slope_degrees"), Sample.AvgSlopeDegrees);
	J->SetNumberField(TEXT("roughness"), Sample.Roughness);
	J->SetBoolField(TEXT("all_hit"), Sample.bAllHit);

	// Center
	TArray<TSharedPtr<FJsonValue>> CArr;
	CArr.Add(MakeShared<FJsonValueNumber>(Sample.Center.X));
	CArr.Add(MakeShared<FJsonValueNumber>(Sample.Center.Y));
	CArr.Add(MakeShared<FJsonValueNumber>(Sample.Center.Z));
	J->SetArrayField(TEXT("center"), CArr);

	// Average normal
	TArray<TSharedPtr<FJsonValue>> NArr;
	NArr.Add(MakeShared<FJsonValueNumber>(Sample.AvgNormal.X));
	NArr.Add(MakeShared<FJsonValueNumber>(Sample.AvgNormal.Y));
	NArr.Add(MakeShared<FJsonValueNumber>(Sample.AvgNormal.Z));
	J->SetArrayField(TEXT("avg_normal"), NArr);

	// Slope direction
	TArray<TSharedPtr<FJsonValue>> SArr;
	SArr.Add(MakeShared<FJsonValueNumber>(Sample.SlopeDirection.X));
	SArr.Add(MakeShared<FJsonValueNumber>(Sample.SlopeDirection.Y));
	SArr.Add(MakeShared<FJsonValueNumber>(Sample.SlopeDirection.Z));
	J->SetArrayField(TEXT("slope_direction"), SArr);

	// Size
	TArray<TSharedPtr<FJsonValue>> SzArr;
	SzArr.Add(MakeShared<FJsonValueNumber>(Sample.SampleSize.X));
	SzArr.Add(MakeShared<FJsonValueNumber>(Sample.SampleSize.Y));
	J->SetArrayField(TEXT("size"), SzArr);

	// Grid resolution
	J->SetNumberField(TEXT("grid_res_x"), Sample.GridResX);
	J->SetNumberField(TEXT("grid_res_y"), Sample.GridResY);

	return J;
}

bool FMonolithMeshTerrainActions::ParseTerrainSample(const TSharedPtr<FJsonObject>& Json,
	FTerrainSample& OutSample, FString& OutError)
{
	if (!Json.IsValid())
	{
		OutError = TEXT("terrain_samples is null");
		return false;
	}

	OutSample = FTerrainSample();

	// Parse 2D samples array
	const TArray<TSharedPtr<FJsonValue>>* RowsArr = nullptr;
	if (!Json->TryGetArrayField(TEXT("samples"), RowsArr) || !RowsArr || RowsArr->Num() == 0)
	{
		OutError = TEXT("terrain_samples missing 'samples' array");
		return false;
	}

	OutSample.GridResY = RowsArr->Num();
	for (int32 Row = 0; Row < OutSample.GridResY; ++Row)
	{
		const TArray<TSharedPtr<FJsonValue>>* ColArr = nullptr;
		if (!(*RowsArr)[Row]->TryGetArray(ColArr) || !ColArr)
		{
			OutError = FString::Printf(TEXT("terrain_samples row %d is not an array"), Row);
			return false;
		}

		if (Row == 0)
		{
			OutSample.GridResX = ColArr->Num();
		}

		TArray<float> RowHeights;
		TArray<FVector> RowNormals;
		RowHeights.Reserve(ColArr->Num());
		RowNormals.Reserve(ColArr->Num());

		for (const TSharedPtr<FJsonValue>& V : *ColArr)
		{
			RowHeights.Add(static_cast<float>(V->AsNumber()));
			RowNormals.Add(FVector::UpVector); // Normals not preserved in JSON round-trip
		}
		OutSample.Heights.Add(MoveTemp(RowHeights));
		OutSample.Normals.Add(MoveTemp(RowNormals));
	}

	// Scalar fields
	if (Json->HasField(TEXT("min_z")))  OutSample.MinZ = static_cast<float>(Json->GetNumberField(TEXT("min_z")));
	if (Json->HasField(TEXT("max_z")))  OutSample.MaxZ = static_cast<float>(Json->GetNumberField(TEXT("max_z")));
	if (Json->HasField(TEXT("avg_z")))  OutSample.AvgZ = static_cast<float>(Json->GetNumberField(TEXT("avg_z")));
	if (Json->HasField(TEXT("height_diff")))       OutSample.HeightDiff = static_cast<float>(Json->GetNumberField(TEXT("height_diff")));
	if (Json->HasField(TEXT("avg_slope_degrees")))  OutSample.AvgSlopeDegrees = static_cast<float>(Json->GetNumberField(TEXT("avg_slope_degrees")));
	if (Json->HasField(TEXT("roughness")))          OutSample.Roughness = static_cast<float>(Json->GetNumberField(TEXT("roughness")));
	if (Json->HasField(TEXT("all_hit")))            OutSample.bAllHit = Json->GetBoolField(TEXT("all_hit"));

	// Center
	MonolithMeshUtils::ParseVector(Json, TEXT("center"), OutSample.Center);

	// Size
	const TArray<TSharedPtr<FJsonValue>>* SzArr = nullptr;
	if (Json->TryGetArrayField(TEXT("size"), SzArr) && SzArr && SzArr->Num() >= 2)
	{
		OutSample.SampleSize.X = static_cast<float>((*SzArr)[0]->AsNumber());
		OutSample.SampleSize.Y = static_cast<float>((*SzArr)[1]->AsNumber());
	}

	// Average normal
	MonolithMeshUtils::ParseVector(Json, TEXT("avg_normal"), OutSample.AvgNormal);

	// Slope direction
	MonolithMeshUtils::ParseVector(Json, TEXT("slope_direction"), OutSample.SlopeDirection);

	// Grid resolution
	if (Json->HasField(TEXT("grid_res_x"))) OutSample.GridResX = static_cast<int32>(Json->GetNumberField(TEXT("grid_res_x")));
	if (Json->HasField(TEXT("grid_res_y"))) OutSample.GridResY = static_cast<int32>(Json->GetNumberField(TEXT("grid_res_y")));

	return true;
}

// ============================================================================
// Site Analysis
// ============================================================================

FMonolithMeshTerrainActions::FSiteAnalysis FMonolithMeshTerrainActions::AnalyzeSite(
	const TArray<FVector2D>& Footprint, const FTerrainSample& Terrain,
	float FloorHeight, bool bHospiceMode)
{
	FSiteAnalysis A;
	A.SlopeDegrees = Terrain.AvgSlopeDegrees;
	A.HeightDiff = Terrain.HeightDiff;

	// Compute pad Z: average terrain height within the footprint
	double SumZ = 0.0;
	int32 Count = 0;
	float FootprintMinZ = MAX_FLT;
	float FootprintMaxZ = -MAX_FLT;

	FBox2D FootBounds = ComputePolygonBounds(Footprint);

	for (int32 Row = 0; Row < Terrain.GridResY; ++Row)
	{
		for (int32 Col = 0; Col < Terrain.GridResX; ++Col)
		{
			// Map grid index to world XY
			float U = (Terrain.GridResX > 1) ? (float)Col / (Terrain.GridResX - 1) : 0.5f;
			float V = (Terrain.GridResY > 1) ? (float)Row / (Terrain.GridResY - 1) : 0.5f;
			float WX = Terrain.Center.X - Terrain.SampleSize.X * 0.5f + U * Terrain.SampleSize.X;
			float WY = Terrain.Center.Y - Terrain.SampleSize.Y * 0.5f + V * Terrain.SampleSize.Y;

			FVector2D Pt(WX, WY);

			// Only count samples within (or near) the footprint
			if (IsPointInPolygon(Pt, Footprint) || FootBounds.IsInside(Pt))
			{
				float Z = Terrain.Heights[Row][Col];
				SumZ += Z;
				FootprintMinZ = FMath::Min(FootprintMinZ, Z);
				FootprintMaxZ = FMath::Max(FootprintMaxZ, Z);
				++Count;
			}
		}
	}

	if (Count > 0)
	{
		A.PadZ = static_cast<float>(SumZ / Count);
		A.HeightDiff = FootprintMaxZ - FootprintMinZ;
	}
	else
	{
		// Fallback: use terrain average
		A.PadZ = Terrain.AvgZ;
	}

	// Select strategy based on slope and height differential
	if (A.HeightDiff < 30.0f)
	{
		A.Strategy = EFoundationStrategy::Flat;
	}
	else if (A.SlopeDegrees < 10.0f)
	{
		A.Strategy = EFoundationStrategy::CutAndFill;
	}
	else if (A.SlopeDegrees < 25.0f)
	{
		// Check if walkout basement makes sense (height diff > 70% of floor height)
		if (A.HeightDiff > FloorHeight * 0.7f)
		{
			A.Strategy = EFoundationStrategy::WalkoutBasement;
		}
		else
		{
			A.Strategy = EFoundationStrategy::Stepped;
		}
	}
	else
	{
		// Steep slope
		if (A.HeightDiff > FloorHeight * 0.7f)
		{
			A.Strategy = EFoundationStrategy::WalkoutBasement;
		}
		else
		{
			A.Strategy = EFoundationStrategy::Piers;
		}
	}

	// ADA ramp analysis (hospice mode)
	if (bHospiceMode)
	{
		// Rise = difference between pad Z and lowest terrain Z at building perimeter
		float PerimeterMinZ = FootprintMinZ < MAX_FLT ? FootprintMinZ : Terrain.MinZ;
		A.RampRise = FMath::Max(0.0f, A.PadZ - PerimeterMinZ);
		A.bNeedsRamp = A.RampRise > 2.0f; // Only need ramp if >2cm rise

		if (A.bNeedsRamp)
		{
			constexpr float ADA_SLOPE = 1.0f / 12.0f;
			constexpr float ADA_MAX_RISE_PER_RUN = 76.0f;
			constexpr float ADA_LANDING_LENGTH = 150.0f;
			constexpr float ADA_RAMP_WIDTH = 100.0f;

			A.RampWidth = ADA_RAMP_WIDTH;
			A.RampSegments = FMath::CeilToInt32(A.RampRise / ADA_MAX_RISE_PER_RUN);
			float SegmentRise = A.RampRise / A.RampSegments;
			float SegmentRun = SegmentRise / ADA_SLOPE;
			A.RampRun = SegmentRun * A.RampSegments + ADA_LANDING_LENGTH * FMath::Max(0, A.RampSegments - 1);
		}
	}

	return A;
}

// ============================================================================
// Foundation Geometry Builders
// ============================================================================

bool FMonolithMeshTerrainActions::BuildFlatPad(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
	float PadZ, float PadThickness, int32 MaterialID, FString& OutError)
{
	if (!Mesh)
	{
		OutError = TEXT("Null mesh");
		return false;
	}

	// Compute footprint AABB and add margin
	FBox2D Bounds = ComputePolygonBounds(Footprint);
	float Margin = 20.0f;
	float PadW = (Bounds.Max.X - Bounds.Min.X) + Margin * 2.0f;
	float PadD = (Bounds.Max.Y - Bounds.Min.Y) + Margin * 2.0f;
	FVector2D PadCenter = (Bounds.Min + Bounds.Max) * 0.5f;

	FGeometryScriptPrimitiveOptions Opts;
	FTransform PadXf(FRotator::ZeroRotator, FVector(PadCenter.X, PadCenter.Y, PadZ - PadThickness), FVector::OneVector);

	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
		Mesh, Opts, PadXf, PadW, PadD, PadThickness,
		0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

	return true;
}

bool FMonolithMeshTerrainActions::BuildCutAndFill(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
	const FTerrainSample& Terrain, float PadZ, float PadThickness, int32 MaterialID, FString& OutError)
{
	if (!Mesh)
	{
		OutError = TEXT("Null mesh");
		return false;
	}

	// Build the main pad
	if (!BuildFlatPad(Mesh, Footprint, PadZ, PadThickness, MaterialID, OutError))
	{
		return false;
	}

	// Add fill geometry on the low side: boxes from terrain up to pad Z
	FBox2D Bounds = ComputePolygonBounds(Footprint);
	float Margin = 20.0f;
	float PadW = (Bounds.Max.X - Bounds.Min.X) + Margin * 2.0f;
	float PadD = (Bounds.Max.Y - Bounds.Min.Y) + Margin * 2.0f;
	FVector2D PadCenter = (Bounds.Min + Bounds.Max) * 0.5f;

	// Sample a few points along the footprint to build fill columns
	int32 FillRes = 4;
	float StepX = PadW / FillRes;
	float StepY = PadD / FillRes;

	FGeometryScriptPrimitiveOptions Opts;

	for (int32 IX = 0; IX < FillRes; ++IX)
	{
		for (int32 IY = 0; IY < FillRes; ++IY)
		{
			float WX = (Bounds.Min.X - Margin) + (IX + 0.5f) * StepX;
			float WY = (Bounds.Min.Y - Margin) + (IY + 0.5f) * StepY;
			float TerrZ = InterpolateTerrainZ(Terrain, WX, WY);

			if (TerrZ < PadZ - PadThickness)
			{
				// Fill from terrain up to pad bottom
				float FillH = (PadZ - PadThickness) - TerrZ;
				if (FillH > 1.0f)
				{
					FTransform FillXf(FRotator::ZeroRotator, FVector(WX, WY, TerrZ), FVector::OneVector);
					UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
						Mesh, Opts, FillXf, StepX, StepY, FillH,
						0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
				}
			}
		}
	}

	return true;
}

bool FMonolithMeshTerrainActions::BuildStepped(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
	const FTerrainSample& Terrain, float PadZ, float StepHeight, int32 MaterialID,
	int32& OutStepCount, FString& OutError)
{
	if (!Mesh)
	{
		OutError = TEXT("Null mesh");
		return false;
	}

	// Determine step quantization
	if (StepHeight < 10.0f) StepHeight = 100.0f; // Default: 100cm steps

	FBox2D Bounds = ComputePolygonBounds(Footprint);
	float Margin = 10.0f;

	// Determine slope direction to divide footprint into strips
	FVector2D SlopeDir2D(Terrain.SlopeDirection.X, Terrain.SlopeDirection.Y);
	if (SlopeDir2D.IsNearlyZero())
	{
		SlopeDir2D = FVector2D(1.0f, 0.0f); // Default: slope along X
	}
	SlopeDir2D.Normalize();

	// Project footprint extents along slope direction
	float MinProj = MAX_FLT, MaxProj = -MAX_FLT;
	for (const FVector2D& P : Footprint)
	{
		float Proj = FVector2D::DotProduct(P, SlopeDir2D);
		MinProj = FMath::Min(MinProj, Proj);
		MaxProj = FMath::Max(MaxProj, Proj);
	}

	float TotalSpan = MaxProj - MinProj;
	OutStepCount = FMath::Max(1, FMath::CeilToInt32(Terrain.HeightDiff / StepHeight));
	float StripWidth = TotalSpan / OutStepCount;

	FGeometryScriptPrimitiveOptions Opts;
	FVector2D PerpDir(-SlopeDir2D.Y, SlopeDir2D.X);

	// Compute perpendicular extent
	float MinPerp = MAX_FLT, MaxPerp = -MAX_FLT;
	for (const FVector2D& P : Footprint)
	{
		float Proj = FVector2D::DotProduct(P, PerpDir);
		MinPerp = FMath::Min(MinPerp, Proj);
		MaxPerp = FMath::Max(MaxPerp, Proj);
	}
	float PerpSpan = MaxPerp - MinPerp;

	// Build each step pad
	for (int32 S = 0; S < OutStepCount; ++S)
	{
		float Frac = (OutStepCount > 1) ? (float)S / (OutStepCount - 1) : 0.5f;
		float StripCenter = MinProj + (S + 0.5f) * StripWidth;

		// World XY of strip center
		FVector2D StripCenterXY = SlopeDir2D * StripCenter + PerpDir * ((MinPerp + MaxPerp) * 0.5f);

		// Z for this step: interpolate terrain Z at this strip and quantize
		float TerrZ = InterpolateTerrainZ(Terrain, StripCenterXY.X, StripCenterXY.Y);
		float QuantizedZ = FMath::RoundToFloat(TerrZ / StepHeight) * StepHeight;

		float PadThickness = 15.0f;
		FTransform StepXf(
			FRotator::ZeroRotator,
			FVector(StripCenterXY.X, StripCenterXY.Y, QuantizedZ - PadThickness),
			FVector::OneVector);

		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, StepXf,
			StripWidth + Margin, PerpSpan + Margin, PadThickness,
			0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

		// Connecting wall between steps (vertical face)
		if (S > 0)
		{
			// Get previous step Z
			float PrevStripCenter = MinProj + (S - 0.5f) * StripWidth;
			FVector2D PrevXY = SlopeDir2D * PrevStripCenter + PerpDir * ((MinPerp + MaxPerp) * 0.5f);
			float PrevTerrZ = InterpolateTerrainZ(Terrain, PrevXY.X, PrevXY.Y);
			float PrevZ = FMath::RoundToFloat(PrevTerrZ / StepHeight) * StepHeight;

			float WallH = FMath::Abs(QuantizedZ - PrevZ);
			if (WallH > 1.0f)
			{
				float WallZ = FMath::Min(QuantizedZ, PrevZ);
				FVector2D WallXY = SlopeDir2D * (MinProj + S * StripWidth) + PerpDir * ((MinPerp + MaxPerp) * 0.5f);
				FTransform WallXf(FRotator::ZeroRotator, FVector(WallXY.X, WallXY.Y, WallZ), FVector::OneVector);
				float WallThickness = 10.0f;
				UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
					Mesh, Opts, WallXf,
					WallThickness, PerpSpan + Margin, WallH,
					0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
			}
		}
	}

	return true;
}

bool FMonolithMeshTerrainActions::BuildPiers(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
	const FTerrainSample& Terrain, float PadZ, float PierDiameter, float PierSpacing,
	float PadThickness, int32 MatFoundation, int32 MatPier,
	int32& OutPierCount, FString& OutError)
{
	if (!Mesh)
	{
		OutError = TEXT("Null mesh");
		return false;
	}

	// Build the raised pad first
	if (!BuildFlatPad(Mesh, Footprint, PadZ, PadThickness, MatFoundation, OutError))
	{
		return false;
	}

	// Generate pier grid within the footprint bounds
	FBox2D Bounds = ComputePolygonBounds(Footprint);
	float StartX = Bounds.Min.X;
	float StartY = Bounds.Min.Y;

	FGeometryScriptPrimitiveOptions Opts;
	float PierRadius = PierDiameter * 0.5f;
	OutPierCount = 0;
	constexpr float MIN_GAP = 30.0f; // Minimum gap before placing a pier

	for (float X = StartX; X <= Bounds.Max.X; X += PierSpacing)
	{
		for (float Y = StartY; Y <= Bounds.Max.Y; Y += PierSpacing)
		{
			// Check if pier is inside the footprint
			if (!IsPointInPolygon(FVector2D(X, Y), Footprint))
			{
				continue;
			}

			float TerrZ = InterpolateTerrainZ(Terrain, X, Y);
			float Gap = (PadZ - PadThickness) - TerrZ;

			if (Gap > MIN_GAP)
			{
				FTransform PierXf(FRotator::ZeroRotator, FVector(X, Y, TerrZ), FVector::OneVector);
				UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendCylinder(
					Mesh, Opts, PierXf,
					PierRadius, Gap, 8, 0, true,
					EGeometryScriptPrimitiveOriginMode::Base);
				++OutPierCount;
			}
		}
	}

	return true;
}

bool FMonolithMeshTerrainActions::BuildWalkoutBasement(UDynamicMesh* Mesh, const TArray<FVector2D>& Footprint,
	const FTerrainSample& Terrain, float PadZ, float FloorHeight,
	float WallThickness, int32 MaterialID, FString& OutError)
{
	if (!Mesh)
	{
		OutError = TEXT("Null mesh");
		return false;
	}

	// Walkout basement: building floor at uphill side terrain level.
	// Basement extends one floor height below. Downhill side is exposed.
	FBox2D Bounds = ComputePolygonBounds(Footprint);
	float Margin = 5.0f;
	float W = (Bounds.Max.X - Bounds.Min.X) + Margin * 2.0f;
	float D = (Bounds.Max.Y - Bounds.Min.Y) + Margin * 2.0f;
	FVector2D Center = (Bounds.Min + Bounds.Max) * 0.5f;

	float BasementFloorZ = PadZ - FloorHeight;

	FGeometryScriptPrimitiveOptions Opts;

	// Basement floor slab
	float SlabT = 15.0f;
	FTransform FloorXf(FRotator::ZeroRotator, FVector(Center.X, Center.Y, BasementFloorZ - SlabT), FVector::OneVector);
	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
		Mesh, Opts, FloorXf, W, D, SlabT,
		0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

	// Basement walls on 3 sides (buried sides). The walkout side (lowest terrain) is left open.
	// Determine which side is the walkout (lowest average terrain along that edge)
	struct FEdge { float FixedCoord; bool bVertical; FString Side; float AvgTerrZ; };
	TArray<FEdge> Edges;
	Edges.Add({static_cast<float>(Bounds.Min.Y - Margin), false, TEXT("south"), 0.0f});
	Edges.Add({static_cast<float>(Bounds.Max.Y + Margin), false, TEXT("north"), 0.0f});
	Edges.Add({static_cast<float>(Bounds.Min.X - Margin), true, TEXT("west"), 0.0f});
	Edges.Add({static_cast<float>(Bounds.Max.X + Margin), true, TEXT("east"), 0.0f});

	// Sample terrain Z along each edge
	for (FEdge& E : Edges)
	{
		float SumZ = 0.0f;
		int32 N = 5;
		for (int32 I = 0; I < N; ++I)
		{
			float T = (float)I / (N - 1);
			float X, Y;
			if (E.bVertical)
			{
				X = E.FixedCoord;
				Y = (Bounds.Min.Y - Margin) + T * D;
			}
			else
			{
				X = (Bounds.Min.X - Margin) + T * W;
				Y = E.FixedCoord;
			}
			SumZ += InterpolateTerrainZ(Terrain, X, Y);
		}
		E.AvgTerrZ = SumZ / N;
	}

	// Find lowest edge (walkout side)
	int32 WalkoutIdx = 0;
	float LowestZ = Edges[0].AvgTerrZ;
	for (int32 I = 1; I < Edges.Num(); ++I)
	{
		if (Edges[I].AvgTerrZ < LowestZ)
		{
			LowestZ = Edges[I].AvgTerrZ;
			WalkoutIdx = I;
		}
	}

	// Build walls on all sides except walkout
	for (int32 I = 0; I < Edges.Num(); ++I)
	{
		if (I == WalkoutIdx) continue;

		const FEdge& E = Edges[I];
		float WallH = PadZ - BasementFloorZ;
		FVector WallPos;
		float WallW, WallD;

		if (E.bVertical)
		{
			WallPos = FVector(E.FixedCoord, Center.Y, BasementFloorZ);
			WallW = WallThickness;
			WallD = D;
		}
		else
		{
			WallPos = FVector(Center.X, E.FixedCoord, BasementFloorZ);
			WallW = W;
			WallD = WallThickness;
		}

		FTransform WallXf(FRotator::ZeroRotator, WallPos, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, WallXf, WallW, WallD, WallH,
			0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
	}

	// Main floor slab (at pad Z)
	FTransform MainFloorXf(FRotator::ZeroRotator, FVector(Center.X, Center.Y, PadZ - SlabT), FVector::OneVector);
	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
		Mesh, Opts, MainFloorXf, W, D, SlabT,
		0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

	return true;
}

bool FMonolithMeshTerrainActions::BuildADARamp(UDynamicMesh* Mesh, float Rise, float Width,
	const FVector& StartPos, const FVector& Direction, int32 MaterialID, FString& OutError)
{
	if (!Mesh)
	{
		OutError = TEXT("Null mesh");
		return false;
	}

	if (Rise < 0.1f)
	{
		return true; // Nothing to build
	}

	constexpr float ADA_SLOPE = 1.0f / 12.0f;
	constexpr float ADA_MAX_RISE_PER_RUN = 76.0f;
	constexpr float ADA_LANDING_LENGTH = 150.0f;
	constexpr float HANDRAIL_HEIGHT = 90.0f;
	constexpr float HANDRAIL_POST_SPACING = 120.0f;
	constexpr float HANDRAIL_POST_WIDTH = 5.0f;
	constexpr float HANDRAIL_RAIL_HEIGHT = 3.0f;

	int32 Segments = FMath::CeilToInt32(Rise / ADA_MAX_RISE_PER_RUN);
	float SegmentRise = Rise / Segments;
	float SegmentRun = SegmentRise / ADA_SLOPE;

	FVector Dir = Direction.GetSafeNormal2D();
	if (Dir.IsNearlyZero()) Dir = FVector(1, 0, 0);
	FVector RightVec = FVector::CrossProduct(FVector::UpVector, Dir).GetSafeNormal();

	// Lateral gap between parallel runs: ramp width + 30cm for inner handrails (ADA 505.3)
	const float LateralGap = Width + 30.0f;
	constexpr float RAMP_THICKNESS = 10.0f;
	const float RampAngle = FMath::RadiansToDegrees(FMath::Atan(ADA_SLOPE));
	const float RampLength = FMath::Sqrt(SegmentRun * SegmentRun + SegmentRise * SegmentRise);

	FGeometryScriptPrimitiveOptions Opts;

	// Switchback layout: runs are SIDE BY SIDE in plan view (offset perpendicular),
	// NOT stacked vertically. Each segment alternates direction along the run axis,
	// and each is offset laterally by LateralGap.

	for (int32 Seg = 0; Seg < Segments; ++Seg)
	{
		float SegStartZ = StartPos.Z + SegmentRise * Seg;
		float SegEndZ = SegStartZ + SegmentRise;

		// Alternate direction: even segments go forward, odd go backward
		FVector SegDir = (Seg % 2 == 0) ? Dir : -Dir;

		// Perpendicular offset: each segment shifts laterally
		FVector LateralOffset = RightVec * (Seg * LateralGap);

		// Segment start position (at the beginning of this run)
		FVector SegStart = StartPos + LateralOffset;
		SegStart.Z = SegStartZ;

		// Ramp slab: box at angle
		FVector RampCenter = SegStart + SegDir * (SegmentRun * 0.5f) + FVector(0, 0, SegmentRise * 0.5f);
		FRotator RampRot = SegDir.Rotation();
		RampRot.Pitch = -RampAngle; // Tilt upward along run direction

		FTransform RampXf(RampRot, RampCenter, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, RampXf, RampLength, Width, RAMP_THICKNESS,
			0, 0, 0, EGeometryScriptPrimitiveOriginMode::Center);

		// Handrail posts on both sides
		FVector RampRight = FVector::CrossProduct(FVector::UpVector, SegDir).GetSafeNormal();
		float NumPosts = FMath::Max(2.0f, FMath::CeilToFloat(SegmentRun / HANDRAIL_POST_SPACING) + 1.0f);

		for (int32 Side = 0; Side < 2; ++Side)
		{
			float SideSign = (Side == 0) ? -1.0f : 1.0f;
			FVector SideOffset = RampRight * SideSign * (Width * 0.5f + HANDRAIL_POST_WIDTH * 0.5f);

			for (int32 P = 0; P < static_cast<int32>(NumPosts); ++P)
			{
				float T = (NumPosts > 1) ? (float)P / (NumPosts - 1) : 0.5f;
				FVector PostBase = SegStart + SegDir * (T * SegmentRun) +
					FVector(0, 0, T * SegmentRise) + SideOffset;

				FTransform PostXf(FRotator::ZeroRotator, PostBase, FVector::OneVector);
				UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
					Mesh, Opts, PostXf,
					HANDRAIL_POST_WIDTH, HANDRAIL_POST_WIDTH, HANDRAIL_HEIGHT,
					0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
			}

			// Top rail
			FVector RailStart = SegStart + SideOffset + FVector(0, 0, HANDRAIL_HEIGHT);
			FVector RailEnd = SegStart + SegDir * SegmentRun + SideOffset + FVector(0, 0, SegmentRise + HANDRAIL_HEIGHT);
			FVector RailCenter = (RailStart + RailEnd) * 0.5f;
			float RailLen = (RailEnd - RailStart).Size();
			FVector RailDir2 = (RailEnd - RailStart).GetSafeNormal();
			FRotator RailRot = RailDir2.Rotation();

			FTransform RailXf(RailRot, RailCenter, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, RailXf,
				RailLen, HANDRAIL_POST_WIDTH, HANDRAIL_RAIL_HEIGHT,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Center);
		}

		// 180-degree landing connecting this segment's end to the next segment's start
		if (Seg < Segments - 1)
		{
			// Landing spans laterally from this run's end to next run's start
			FVector ThisEnd = SegStart + SegDir * SegmentRun + FVector(0, 0, SegmentRise);
			FVector NextLateral = RightVec * ((Seg + 1) * LateralGap);
			FVector NextStart = StartPos + NextLateral;
			NextStart.Z = SegEndZ;

			FVector LandingCenter = (ThisEnd + NextStart) * 0.5f;
			// Landing width spans from this run to next run (perpendicular to run direction)
			float LandingSpanPerp = LateralGap + Width;

			// Rotate landing to align perpendicular span with the right vector
			FRotator LandingRot = RightVec.Rotation();
			FTransform LandingXf(LandingRot, LandingCenter, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, LandingXf,
				LandingSpanPerp, ADA_LANDING_LENGTH, RAMP_THICKNESS,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Center);
		}
	}

	// Top landing pad at the end of the last segment
	{
		int32 LastSeg = Segments - 1;
		FVector LastSegDir = (LastSeg % 2 == 0) ? Dir : -Dir;
		FVector LastLateral = RightVec * (LastSeg * LateralGap);
		FVector LastSegStart = StartPos + LastLateral;
		LastSegStart.Z = StartPos.Z + SegmentRise * LastSeg;
		FVector TopPos = LastSegStart + LastSegDir * SegmentRun + FVector(0, 0, SegmentRise);

		FTransform TopLandingXf(FRotator::ZeroRotator, TopPos, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, TopLandingXf,
			ADA_LANDING_LENGTH, Width, RAMP_THICKNESS,
			0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
	}

	return true;
}

// ============================================================================
// Retaining Wall Helper
// ============================================================================

bool FMonolithMeshTerrainActions::BuildRetainingWallGeometry(UDynamicMesh* Mesh,
	const FVector& Start, const FVector& End, const FTerrainSample& Terrain,
	float Thickness, float CapHeight, int32 MaterialID, FString& OutError)
{
	if (!Mesh)
	{
		OutError = TEXT("Null mesh");
		return false;
	}

	FVector WallDir = (End - Start);
	float WallLength = WallDir.Size2D();
	if (WallLength < 1.0f)
	{
		OutError = TEXT("Wall start and end are too close");
		return false;
	}

	WallDir.Normalize();

	// Segment the wall into sections and vary height based on terrain
	int32 NumSections = FMath::Max(1, FMath::CeilToInt32(WallLength / 100.0f));
	float SectionLength = WallLength / NumSections;

	FGeometryScriptPrimitiveOptions Opts;

	for (int32 I = 0; I < NumSections; ++I)
	{
		float T0 = (float)I / NumSections;
		float T1 = (float)(I + 1) / NumSections;
		float TMid = (T0 + T1) * 0.5f;

		FVector SectionCenter2D = Start + WallDir * (TMid * WallLength);
		float TerrZ = InterpolateTerrainZ(Terrain, SectionCenter2D.X, SectionCenter2D.Y);

		// Wall goes from the lower of Start.Z/End.Z up to terrain + cap
		float BaseZ = FMath::Lerp(Start.Z, End.Z, TMid);
		float TopZ = TerrZ + CapHeight;
		float WallH = TopZ - BaseZ;

		if (WallH < 1.0f) continue; // No wall needed here

		// Tapered wall: thicker at base
		float BaseThick = Thickness;
		float TopThick = Thickness * 0.6f;

		// Build as a simple box (tapered profile would need AppendSimpleExtrudePolygon, keeping it simple)
		float AvgThick = (BaseThick + TopThick) * 0.5f;
		FTransform SectionXf(
			WallDir.Rotation(),
			FVector(SectionCenter2D.X, SectionCenter2D.Y, BaseZ),
			FVector::OneVector);

		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, SectionXf,
			SectionLength, AvgThick, WallH,
			0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
	}

	return true;
}

// ============================================================================
// Action Handlers
// ============================================================================

FMonolithActionResult FMonolithMeshTerrainActions::SampleTerrainGrid(const TSharedPtr<FJsonObject>& Params)
{
	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world"));
	}

	// Parse center
	FVector Center;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("center"), Center))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid 'center' array [x, y, z]"));
	}

	// Parse size
	const TArray<TSharedPtr<FJsonValue>>* SizeArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("size"), SizeArr) || !SizeArr || SizeArr->Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid 'size' array [width, height]"));
	}
	FVector2D Size(
		static_cast<float>((*SizeArr)[0]->AsNumber()),
		static_cast<float>((*SizeArr)[1]->AsNumber()));

	// Optional params
	int32 Res = Params->HasField(TEXT("grid_resolution")) ?
		static_cast<int32>(Params->GetNumberField(TEXT("grid_resolution"))) : 8;
	float TraceHeight = Params->HasField(TEXT("trace_height")) ?
		static_cast<float>(Params->GetNumberField(TEXT("trace_height"))) : 5000.0f;
	float TraceDepth = Params->HasField(TEXT("trace_depth")) ?
		static_cast<float>(Params->GetNumberField(TEXT("trace_depth"))) : 10000.0f;

	// Trace channel
	ECollisionChannel Channel = ECC_Visibility;
	FString ChannelStr;
	if (Params->TryGetStringField(TEXT("channel"), ChannelStr))
	{
		if (ChannelStr == TEXT("WorldStatic"))       Channel = ECC_WorldStatic;
		else if (ChannelStr == TEXT("WorldDynamic")) Channel = ECC_WorldDynamic;
		// Default: Visibility
	}

	FTerrainSample Sample;
	FString SampleError;
	if (!SampleTerrain(World, Center, Size, Res, Res, TraceHeight, TraceDepth, Channel, Sample, SampleError))
	{
		return FMonolithActionResult::Error(SampleError);
	}

	auto Result = TerrainSampleToJson(Sample);
	Result->SetNumberField(TEXT("sample_count"), Res * Res);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshTerrainActions::AnalyzeBuildingSite(const TSharedPtr<FJsonObject>& Params)
{
	// Parse footprint polygon
	TArray<FVector2D> Footprint;
	FString PolyError;
	if (!ParsePolygon(Params, TEXT("footprint_polygon"), Footprint, PolyError))
	{
		return FMonolithActionResult::Error(PolyError);
	}

	// Parse terrain samples
	const TSharedPtr<FJsonObject>* TerrainObj = nullptr;
	if (!Params->TryGetObjectField(TEXT("terrain_samples"), TerrainObj) || !TerrainObj || !(*TerrainObj).IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing 'terrain_samples' object"));
	}
	FTerrainSample Terrain;
	FString TerrainError;
	if (!ParseTerrainSample(*TerrainObj, Terrain, TerrainError))
	{
		return FMonolithActionResult::Error(TerrainError);
	}

	float FloorHeight = Params->HasField(TEXT("floor_height")) ?
		static_cast<float>(Params->GetNumberField(TEXT("floor_height"))) : 270.0f;
	bool bHospice = Params->HasField(TEXT("hospice_mode")) ?
		Params->GetBoolField(TEXT("hospice_mode")) : false;

	FSiteAnalysis Analysis = AnalyzeSite(Footprint, Terrain, FloorHeight, bHospice);

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("strategy"), StrategyToString(Analysis.Strategy));
	Result->SetNumberField(TEXT("slope_degrees"), Analysis.SlopeDegrees);
	Result->SetNumberField(TEXT("height_diff"), Analysis.HeightDiff);
	Result->SetNumberField(TEXT("pad_z"), Analysis.PadZ);
	Result->SetBoolField(TEXT("needs_ramp"), Analysis.bNeedsRamp);

	if (Analysis.bNeedsRamp)
	{
		auto RampSpec = MakeShared<FJsonObject>();
		RampSpec->SetNumberField(TEXT("rise"), Analysis.RampRise);
		RampSpec->SetNumberField(TEXT("run"), Analysis.RampRun);
		RampSpec->SetNumberField(TEXT("segments"), Analysis.RampSegments);
		RampSpec->SetNumberField(TEXT("width"), Analysis.RampWidth);
		RampSpec->SetStringField(TEXT("slope_ratio"), TEXT("1:12"));
		Result->SetObjectField(TEXT("ramp_specs"), RampSpec);
	}

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshTerrainActions::CreateFoundation(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(GS_ERROR_TERRAIN);
	}

	// Parse strategy
	FString StrategyStr;
	if (!Params->TryGetStringField(TEXT("strategy"), StrategyStr))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: strategy"));
	}
	EFoundationStrategy Strategy = StringToStrategy(StrategyStr);

	// Parse footprint
	TArray<FVector2D> Footprint;
	FString PolyError;
	if (!ParsePolygon(Params, TEXT("footprint_polygon"), Footprint, PolyError))
	{
		return FMonolithActionResult::Error(PolyError);
	}

	// Parse terrain samples
	const TSharedPtr<FJsonObject>* TerrainObj = nullptr;
	if (!Params->TryGetObjectField(TEXT("terrain_samples"), TerrainObj) || !TerrainObj || !(*TerrainObj).IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing 'terrain_samples' object"));
	}
	FTerrainSample Terrain;
	FString TerrainError;
	if (!ParseTerrainSample(*TerrainObj, Terrain, TerrainError))
	{
		return FMonolithActionResult::Error(TerrainError);
	}

	// Save path
	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
	}

	// Optional params
	float FloorHeight = Params->HasField(TEXT("floor_height")) ?
		static_cast<float>(Params->GetNumberField(TEXT("floor_height"))) : 270.0f;
	float PierDiameter = Params->HasField(TEXT("pier_diameter")) ?
		static_cast<float>(Params->GetNumberField(TEXT("pier_diameter"))) : 30.0f;
	float PierSpacing = Params->HasField(TEXT("pier_spacing")) ?
		static_cast<float>(Params->GetNumberField(TEXT("pier_spacing"))) : 200.0f;

	// Compute pad Z (or use provided)
	float PadZ;
	if (Params->HasField(TEXT("pad_z")))
	{
		PadZ = static_cast<float>(Params->GetNumberField(TEXT("pad_z")));
	}
	else
	{
		// Auto-compute from site analysis
		FSiteAnalysis Quick = AnalyzeSite(Footprint, Terrain, FloorHeight, false);
		PadZ = Quick.PadZ;
	}

	// Create mesh
	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh)
	{
		return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));
	}

	FString BuildError;
	int32 PierCount = 0;
	int32 StepCount = 0;
	float PadThickness = 15.0f;

	switch (Strategy)
	{
	case EFoundationStrategy::Flat:
		if (!BuildFlatPad(Mesh, Footprint, PadZ, PadThickness, 0, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;

	case EFoundationStrategy::CutAndFill:
		if (!BuildCutAndFill(Mesh, Footprint, Terrain, PadZ, PadThickness, 0, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;

	case EFoundationStrategy::Stepped:
		if (!BuildStepped(Mesh, Footprint, Terrain, PadZ, 100.0f, 0, StepCount, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;

	case EFoundationStrategy::Piers:
		if (!BuildPiers(Mesh, Footprint, Terrain, PadZ, PierDiameter, PierSpacing,
			PadThickness, 0, 1, PierCount, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;

	case EFoundationStrategy::WalkoutBasement:
		if (!BuildWalkoutBasement(Mesh, Footprint, Terrain, PadZ, FloorHeight, 15.0f, 0, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;
	}

	// Cleanup normals
	FMonolithMeshProceduralActions::CleanupMesh(Mesh, false);

	// Save to asset
	bool bOverwrite = Params->HasField(TEXT("overwrite")) ? Params->GetBoolField(TEXT("overwrite")) : false;
	FString SaveErr;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(Mesh, SavePath, bOverwrite, SaveErr))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Foundation built but save failed: %s"), *SaveErr));
	}

	// Optionally place in scene
	AActor* PlacedActor = nullptr;
	FVector Location = FVector::ZeroVector;
	bool bHasLocation = MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location);

	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);
	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);
	if (Folder.IsEmpty()) Folder = TEXT("Procedural/Terrain");

	if (bHasLocation || !Label.IsEmpty())
	{
		PlacedActor = FMonolithMeshProceduralActions::PlaceMeshInScene(
			SavePath, Location, FRotator::ZeroRotator, Label, false, Folder);
	}

	// Build result
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("strategy"), StrategyToString(Strategy));
	Result->SetNumberField(TEXT("pad_z"), PadZ);
	Result->SetStringField(TEXT("asset_path"), SavePath);
	Result->SetNumberField(TEXT("triangle_count"), Mesh->GetTriangleCount());

	if (PlacedActor)
	{
		Result->SetStringField(TEXT("actor_name"), PlacedActor->GetActorNameOrLabel());
	}

	if (Strategy == EFoundationStrategy::Piers)
	{
		Result->SetNumberField(TEXT("pier_count"), PierCount);
	}
	if (Strategy == EFoundationStrategy::Stepped)
	{
		Result->SetNumberField(TEXT("step_count"), StepCount);
	}

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshTerrainActions::CreateRetainingWall(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(GS_ERROR_TERRAIN);
	}

	// Parse start/end
	FVector Start, End;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("start"), Start))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid 'start' [x, y, z]"));
	}
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("end"), End))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid 'end' [x, y, z]"));
	}

	// Parse terrain
	const TSharedPtr<FJsonObject>* TerrainObj = nullptr;
	if (!Params->TryGetObjectField(TEXT("terrain_samples"), TerrainObj) || !TerrainObj || !(*TerrainObj).IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing 'terrain_samples' object"));
	}
	FTerrainSample Terrain;
	FString TerrainError;
	if (!ParseTerrainSample(*TerrainObj, Terrain, TerrainError))
	{
		return FMonolithActionResult::Error(TerrainError);
	}

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
	}

	float Thickness = Params->HasField(TEXT("thickness")) ?
		static_cast<float>(Params->GetNumberField(TEXT("thickness"))) : 20.0f;
	float CapHeight = Params->HasField(TEXT("cap_height")) ?
		static_cast<float>(Params->GetNumberField(TEXT("cap_height"))) : 10.0f;

	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh)
	{
		return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));
	}

	FString BuildError;
	if (!BuildRetainingWallGeometry(Mesh, Start, End, Terrain, Thickness, CapHeight, 0, BuildError))
	{
		return FMonolithActionResult::Error(BuildError);
	}

	FMonolithMeshProceduralActions::CleanupMesh(Mesh, false);

	// Save
	FString SaveErr;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(Mesh, SavePath, false, SaveErr))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Retaining wall built but save failed: %s"), *SaveErr));
	}

	// Place
	AActor* PlacedActor = nullptr;
	FVector Location = FVector::ZeroVector;
	bool bHasLocation = MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location);
	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);
	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);
	if (Folder.IsEmpty()) Folder = TEXT("Procedural/Terrain");

	if (bHasLocation || !Label.IsEmpty())
	{
		PlacedActor = FMonolithMeshProceduralActions::PlaceMeshInScene(
			SavePath, Location, FRotator::ZeroRotator, Label, false, Folder);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), SavePath);
	Result->SetNumberField(TEXT("triangle_count"), Mesh->GetTriangleCount());
	Result->SetNumberField(TEXT("wall_length"), (End - Start).Size2D());
	if (PlacedActor)
	{
		Result->SetStringField(TEXT("actor_name"), PlacedActor->GetActorNameOrLabel());
	}

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshTerrainActions::PlaceBuildingOnTerrain(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(GS_ERROR_TERRAIN);
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world"));
	}

	// Parse building descriptor
	const TSharedPtr<FJsonObject>* DescObj = nullptr;
	if (!Params->TryGetObjectField(TEXT("building_descriptor"), DescObj) || !DescObj || !(*DescObj).IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing 'building_descriptor' object"));
	}
	FBuildingDescriptor Building = FBuildingDescriptor::FromJson(*DescObj);

	FString SavePathPrefix;
	if (!Params->TryGetStringField(TEXT("save_path_prefix"), SavePathPrefix) || SavePathPrefix.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path_prefix"));
	}

	bool bHospice = Params->HasField(TEXT("hospice_mode")) ?
		Params->GetBoolField(TEXT("hospice_mode")) : false;
	bool bCreateRetainingWalls = Params->HasField(TEXT("create_retaining_walls")) ?
		Params->GetBoolField(TEXT("create_retaining_walls")) : true;
	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);
	if (Folder.IsEmpty()) Folder = TEXT("Procedural/Terrain");

	// Step 1: Get footprint polygon from descriptor
	TArray<FVector2D> Footprint;
	if (Building.FootprintPolygon.Num() >= 3)
	{
		Footprint = Building.FootprintPolygon;
	}
	else
	{
		// Fallback: compute from grid dimensions of first floor
		// Use the world origin and grid cell size to build a rectangle
		float W = 500.0f; // Default fallback
		float D = 500.0f;
		if (Building.Floors.Num() > 0 && Building.Floors[0].Grid.Num() > 0)
		{
			int32 GridH = Building.Floors[0].Grid.Num();
			int32 GridW = Building.Floors[0].Grid[0].Num();
			W = GridW * Building.GridCellSize;
			D = GridH * Building.GridCellSize;
		}
		Footprint.Add(FVector2D(Building.WorldOrigin.X, Building.WorldOrigin.Y));
		Footprint.Add(FVector2D(Building.WorldOrigin.X + W, Building.WorldOrigin.Y));
		Footprint.Add(FVector2D(Building.WorldOrigin.X + W, Building.WorldOrigin.Y + D));
		Footprint.Add(FVector2D(Building.WorldOrigin.X, Building.WorldOrigin.Y + D));
	}

	// Step 2: Sample terrain (or use pre-computed)
	FTerrainSample Terrain;
	const TSharedPtr<FJsonObject>* PrecomputedTerrain = nullptr;
	if (Params->TryGetObjectField(TEXT("terrain_samples"), PrecomputedTerrain) &&
		PrecomputedTerrain && (*PrecomputedTerrain).IsValid())
	{
		FString TerrainError;
		if (!ParseTerrainSample(*PrecomputedTerrain, Terrain, TerrainError))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Invalid terrain_samples: %s"), *TerrainError));
		}
	}
	else
	{
		// Auto-sample
		FBox2D FootBounds = ComputePolygonBounds(Footprint);
		FVector2D FootCenter = (FootBounds.Min + FootBounds.Max) * 0.5f;
		FVector2D FootSize = FootBounds.Max - FootBounds.Min;
		// Add 20% margin for sampling
		FootSize *= 1.2f;

		FString SampleError;
		if (!SampleTerrain(World,
			FVector(FootCenter.X, FootCenter.Y, Building.WorldOrigin.Z),
			FootSize, 8, 8, 5000.0f, 10000.0f, ECC_Visibility,
			Terrain, SampleError))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Terrain sampling failed: %s"), *SampleError));
		}
	}

	// Step 3: Analyze site
	float FloorHeight = 270.0f;
	if (Building.Floors.Num() > 0)
	{
		FloorHeight = Building.Floors[0].Height;
	}
	FSiteAnalysis Analysis = AnalyzeSite(Footprint, Terrain, FloorHeight, bHospice);

	// Step 4: Create foundation
	FString FoundationPath = SavePathPrefix + TEXT("_Foundation");
	UDynamicMesh* FoundationMesh = NewObject<UDynamicMesh>(Pool);
	if (!FoundationMesh)
	{
		return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh for foundation"));
	}

	FString BuildError;
	int32 PierCount = 0;
	int32 StepCount = 0;
	float PadThickness = 15.0f;

	switch (Analysis.Strategy)
	{
	case EFoundationStrategy::Flat:
		if (!BuildFlatPad(FoundationMesh, Footprint, Analysis.PadZ, PadThickness, 0, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;
	case EFoundationStrategy::CutAndFill:
		if (!BuildCutAndFill(FoundationMesh, Footprint, Terrain, Analysis.PadZ, PadThickness, 0, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;
	case EFoundationStrategy::Stepped:
		if (!BuildStepped(FoundationMesh, Footprint, Terrain, Analysis.PadZ, 100.0f, 0, StepCount, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;
	case EFoundationStrategy::Piers:
		if (!BuildPiers(FoundationMesh, Footprint, Terrain, Analysis.PadZ, 30.0f, 200.0f,
			PadThickness, 0, 1, PierCount, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;
	case EFoundationStrategy::WalkoutBasement:
		if (!BuildWalkoutBasement(FoundationMesh, Footprint, Terrain, Analysis.PadZ, FloorHeight, 15.0f, 0, BuildError))
			return FMonolithActionResult::Error(BuildError);
		break;
	}

	FMonolithMeshProceduralActions::CleanupMesh(FoundationMesh, false);

	FString SaveErr;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(FoundationMesh, FoundationPath, true, SaveErr))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Foundation save failed: %s"), *SaveErr));
	}

	AActor* FoundationActor = FMonolithMeshProceduralActions::PlaceMeshInScene(
		FoundationPath, FVector::ZeroVector, FRotator::ZeroRotator,
		FString::Printf(TEXT("%s_Foundation"), *Building.BuildingId), false, Folder);

	// Step 5: Retaining walls (for cut-and-fill or walkout basement)
	TArray<TSharedPtr<FJsonValue>> RetainingWallsArr;
	if (bCreateRetainingWalls &&
		(Analysis.Strategy == EFoundationStrategy::CutAndFill ||
		 Analysis.Strategy == EFoundationStrategy::WalkoutBasement))
	{
		// Create retaining walls on the uphill edges of the footprint
		FBox2D Bounds = ComputePolygonBounds(Footprint);
		float HighZ = Terrain.MaxZ;

		// Simple approach: place retaining wall along the two edges closest to the uphill side
		FVector SlopeDir3D = Terrain.SlopeDirection;
		FVector2D SlopeDir2D(SlopeDir3D.X, SlopeDir3D.Y);

		// Determine which edges face uphill
		struct FPolyEdge { FVector2D A, B; float DotUphill; };
		TArray<FPolyEdge> PolyEdges;
		for (int32 I = 0; I < Footprint.Num(); ++I)
		{
			int32 J = (I + 1) % Footprint.Num();
			FVector2D EdgeDir = (Footprint[J] - Footprint[I]).GetSafeNormal();
			FVector2D EdgeNormal(-EdgeDir.Y, EdgeDir.X);
			float Dot = FVector2D::DotProduct(EdgeNormal, SlopeDir2D);
			PolyEdges.Add({Footprint[I], Footprint[J], Dot});
		}

		// Build retaining walls on edges that face uphill (positive dot product)
		int32 WallIdx = 0;
		for (const FPolyEdge& Edge : PolyEdges)
		{
			if (Edge.DotUphill > 0.1f)
			{
				FString WallPath = FString::Printf(TEXT("%s_RetWall_%d"), *SavePathPrefix, WallIdx);
				UDynamicMesh* WallMesh = NewObject<UDynamicMesh>(Pool);
				if (WallMesh)
				{
					FString WallError;
					FVector WallStart(Edge.A.X, Edge.A.Y, Analysis.PadZ);
					FVector WallEnd(Edge.B.X, Edge.B.Y, Analysis.PadZ);

					if (BuildRetainingWallGeometry(WallMesh, WallStart, WallEnd, Terrain, 20.0f, 10.0f, 0, WallError))
					{
						FMonolithMeshProceduralActions::CleanupMesh(WallMesh, false);
						FString WallSaveErr;
						if (FMonolithMeshProceduralActions::SaveMeshToAsset(WallMesh, WallPath, true, WallSaveErr))
						{
							AActor* WallActor = FMonolithMeshProceduralActions::PlaceMeshInScene(
								WallPath, FVector::ZeroVector, FRotator::ZeroRotator,
								Building.BuildingId + FString::Printf(TEXT("_RetWall_%d"), WallIdx),
								false, Folder);

							auto WallJson = MakeShared<FJsonObject>();
							WallJson->SetStringField(TEXT("asset_path"), WallPath);
							if (WallActor)
							{
								WallJson->SetStringField(TEXT("actor_name"), WallActor->GetActorNameOrLabel());
							}
							RetainingWallsArr.Add(MakeShared<FJsonValueObject>(WallJson));
						}
					}
				}
				++WallIdx;
			}
		}
	}

	// Step 6: ADA Ramp (hospice mode)
	AActor* RampActor = nullptr;
	if (bHospice && Analysis.bNeedsRamp)
	{
		FString RampPath = SavePathPrefix + TEXT("_Ramp");
		UDynamicMesh* RampMesh = NewObject<UDynamicMesh>(Pool);
		if (RampMesh)
		{
			// Place ramp starting at the lowest perimeter point, facing away from building
			FVector RampStart(Footprint[0].X, Footprint[0].Y, Terrain.MinZ);
			float LowestZ = MAX_FLT;
			for (const FVector2D& P : Footprint)
			{
				float TZ = InterpolateTerrainZ(Terrain, P.X, P.Y);
				if (TZ < LowestZ)
				{
					LowestZ = TZ;
					RampStart = FVector(P.X, P.Y, TZ);
				}
			}

			// Direction: away from building center
			FBox2D FootBounds = ComputePolygonBounds(Footprint);
			FVector2D FootCenter = (FootBounds.Min + FootBounds.Max) * 0.5f;
			FVector RampDir = FVector(RampStart.X - FootCenter.X, RampStart.Y - FootCenter.Y, 0).GetSafeNormal();
			if (RampDir.IsNearlyZero()) RampDir = FVector(1, 0, 0);

			FString RampError;
			if (BuildADARamp(RampMesh, Analysis.RampRise, Analysis.RampWidth, RampStart, RampDir, 3, RampError))
			{
				FMonolithMeshProceduralActions::CleanupMesh(RampMesh, false);
				FString RampSaveErr;
				if (FMonolithMeshProceduralActions::SaveMeshToAsset(RampMesh, RampPath, true, RampSaveErr))
				{
					RampActor = FMonolithMeshProceduralActions::PlaceMeshInScene(
						RampPath, FVector::ZeroVector, FRotator::ZeroRotator,
						Building.BuildingId + TEXT("_ADA_Ramp"),
						false, Folder);
				}
			}
		}
	}

	// Step 7: Adjust building Z — move all building actors to pad Z
	for (const FString& ActorName : Building.ActorNames)
	{
		FString FindErr;
		AActor* Actor = MonolithMeshUtils::FindActorByName(ActorName, FindErr);
		if (Actor)
		{
			FVector ActorLoc = Actor->GetActorLocation();
			float OriginalZ = ActorLoc.Z;
			ActorLoc.Z = Analysis.PadZ;
			Actor->SetActorLocation(ActorLoc);
		}
	}

	// Build result
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("building_id"), Building.BuildingId);
	Result->SetStringField(TEXT("strategy"), StrategyToString(Analysis.Strategy));
	Result->SetNumberField(TEXT("pad_z"), Analysis.PadZ);
	Result->SetNumberField(TEXT("slope_degrees"), Analysis.SlopeDegrees);
	Result->SetNumberField(TEXT("height_diff"), Analysis.HeightDiff);
	Result->SetStringField(TEXT("foundation_asset"), FoundationPath);

	if (FoundationActor)
	{
		Result->SetStringField(TEXT("foundation_actor"), FoundationActor->GetActorNameOrLabel());
	}

	if (RetainingWallsArr.Num() > 0)
	{
		Result->SetArrayField(TEXT("retaining_walls"), RetainingWallsArr);
	}

	if (RampActor)
	{
		Result->SetStringField(TEXT("ramp_actor"), RampActor->GetActorNameOrLabel());
	}

	// Terrain samples in result for downstream use
	Result->SetObjectField(TEXT("terrain_samples"), TerrainSampleToJson(Terrain));

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_GEOMETRYSCRIPT
