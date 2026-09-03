#if WITH_GEOMETRYSCRIPT

#include "MonolithMeshArchFeatureActions.h"
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
#include "GeometryScript/MeshNormalsFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "GeometryScript/MeshTransformFunctions.h"
#include "GeometryScript/MeshUVFunctions.h"

#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Editor.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

using namespace UE::Geometry;

static const FString GS_ERROR_ARCH = TEXT("Enable the GeometryScripting plugin in your .uproject to use architectural feature generation.");

UMonolithMeshHandlePool* FMonolithMeshArchFeatureActions::Pool = nullptr;

void FMonolithMeshArchFeatureActions::SetHandlePool(UMonolithMeshHandlePool* InPool)
{
	Pool = InPool;
}

// ============================================================================
// Helpers
// ============================================================================

float FMonolithMeshArchFeatureActions::GetFloat(const TSharedPtr<FJsonObject>& P, const FString& Key, float Default)
{
	return P->HasField(Key) ? static_cast<float>(P->GetNumberField(Key)) : Default;
}

int32 FMonolithMeshArchFeatureActions::GetInt(const TSharedPtr<FJsonObject>& P, const FString& Key, int32 Default)
{
	return P->HasField(Key) ? static_cast<int32>(P->GetNumberField(Key)) : Default;
}

FString FMonolithMeshArchFeatureActions::GetString(const TSharedPtr<FJsonObject>& P, const FString& Key, const FString& Default)
{
	FString Val;
	return P->TryGetStringField(Key, Val) ? Val : Default;
}

bool FMonolithMeshArchFeatureActions::GetBool(const TSharedPtr<FJsonObject>& P, const FString& Key, bool Default)
{
	return P->HasField(Key) ? P->GetBoolField(Key) : Default;
}

// ============================================================================
// Attachment Context Helpers
// ============================================================================

FAttachmentContext FMonolithMeshArchFeatureActions::ParseBuildingContext(const TSharedPtr<FJsonObject>& Params)
{
	FAttachmentContext Ctx;

	const TSharedPtr<FJsonObject>* CtxObj = nullptr;
	if (!Params->TryGetObjectField(TEXT("building_context"), CtxObj) || !CtxObj || !(*CtxObj).IsValid())
	{
		return Ctx; // bValid = false, caller falls back to location+rotation
	}

	const TSharedPtr<FJsonObject>& BC = *CtxObj;

	// Parse wall normal
	const TArray<TSharedPtr<FJsonValue>>* NormalArr = nullptr;
	if (BC->TryGetArrayField(TEXT("normal"), NormalArr) && NormalArr && NormalArr->Num() >= 3)
	{
		Ctx.WallNormal.X = (*NormalArr)[0]->AsNumber();
		Ctx.WallNormal.Y = (*NormalArr)[1]->AsNumber();
		Ctx.WallNormal.Z = (*NormalArr)[2]->AsNumber();
		Ctx.WallNormal.Normalize();
	}

	// Parse world_origin
	const TArray<TSharedPtr<FJsonValue>>* OriginArr = nullptr;
	if (BC->TryGetArrayField(TEXT("world_origin"), OriginArr) && OriginArr && OriginArr->Num() >= 3)
	{
		Ctx.WallOrigin.X = (*OriginArr)[0]->AsNumber();
		Ctx.WallOrigin.Y = (*OriginArr)[1]->AsNumber();
		Ctx.WallOrigin.Z = (*OriginArr)[2]->AsNumber();
	}

	// Parse scalar fields
	if (BC->HasField(TEXT("width")))
		Ctx.WallWidth = static_cast<float>(BC->GetNumberField(TEXT("width")));
	if (BC->HasField(TEXT("height")))
		Ctx.WallHeight = static_cast<float>(BC->GetNumberField(TEXT("height")));
	if (BC->HasField(TEXT("wall_thickness")))
		Ctx.WallThickness = static_cast<float>(BC->GetNumberField(TEXT("wall_thickness")));
	if (BC->HasField(TEXT("floor_height")))
		Ctx.FloorHeight = static_cast<float>(BC->GetNumberField(TEXT("floor_height")));
	if (BC->HasField(TEXT("floor_index")))
		Ctx.FloorIndex = static_cast<int32>(BC->GetNumberField(TEXT("floor_index")));

	// Parse string fields
	FString WallStr;
	if (BC->TryGetStringField(TEXT("wall"), WallStr))
		Ctx.Wall = WallStr;

	FString BldgId;
	if (BC->TryGetStringField(TEXT("building_id"), BldgId))
		Ctx.BuildingId = BldgId;

	// Compute derived transform
	Ctx.ComputeDerived();

	return Ctx;
}

FRotator FMonolithMeshArchFeatureActions::ComputeWallRotation(const FVector& WallNormal)
{
	// Yaw rotation from wall normal: features are built facing +Y (local outward).
	// We need the yaw that rotates +Y to align with WallNormal (in the XY plane).
	float YawRad = FMath::Atan2(WallNormal.Y, WallNormal.X);
	// +Y in UE is the 90-degree direction, so subtract 90 degrees to align local +Y with the normal
	float YawDeg = FMath::RadiansToDegrees(YawRad) - 90.0f;
	return FRotator(0.0f, YawDeg, 0.0f);
}

FVector FMonolithMeshArchFeatureActions::ComputeAttachmentPosition(
	const FVector& WallOrigin, const FVector& WallNormal, const FVector& WallRight,
	float FeatureWidth, float FeatureDepth, float WallWidth)
{
	// Center the feature along the wall face
	FVector Pos = WallOrigin + WallRight * (WallWidth * 0.5f);
	// Push the feature outward from the wall by half its depth (features are built centered on Y)
	// Actually features extend from Y=0 (wall face) outward, so no depth offset needed for the origin.
	// The rotation handles making +Y point outward.
	return Pos;
}

void FMonolithMeshArchFeatureActions::EmitWallOpenings(
	const TSharedPtr<FJsonObject>& Result, const TArray<FWallOpeningRequest>& Openings)
{
	if (Openings.Num() == 0) return;

	TArray<TSharedPtr<FJsonValue>> OpeningsArr;
	for (const FWallOpeningRequest& O : Openings)
	{
		OpeningsArr.Add(MakeShared<FJsonValueObject>(O.ToJson()));
	}
	Result->SetArrayField(TEXT("wall_openings"), OpeningsArr);
}

// ============================================================================
// Finalize + Save
// ============================================================================

void FMonolithMeshArchFeatureActions::FinalizeGeometry(UDynamicMesh* Mesh)
{
	if (!Mesh) return;

	// Box UV projection
	{
		FGeometryScriptMeshSelection EmptySelection;
		FTransform UVBox = FTransform::Identity;
		UVBox.SetScale3D(FVector(100.0f));
		UGeometryScriptLibrary_MeshUVFunctions::SetMeshUVsFromBoxProjection(
			Mesh, 0, UVBox, EmptySelection, 2);
	}

	// Compute normals (additive-only geometry, no booleans)
	FMonolithMeshProceduralActions::CleanupMesh(Mesh, /*bHadBooleans=*/false);
}

FString FMonolithMeshArchFeatureActions::SaveAndPlace(UDynamicMesh* Mesh, const TSharedPtr<FJsonObject>& Params,
	const TSharedPtr<FJsonObject>& Result,
	const FAttachmentContext& AttachCtx, float FeatureWidth, float FeatureDepth)
{
	FString SavePath;
	Params->TryGetStringField(TEXT("save_path"), SavePath);
	if (SavePath.IsEmpty())
	{
		return TEXT("save_path is required");
	}

	bool bOverwrite = Params->HasField(TEXT("overwrite")) ? Params->GetBoolField(TEXT("overwrite")) : false;
	FString SaveErr;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(Mesh, SavePath, bOverwrite, SaveErr))
	{
		int32 TriCount = Mesh->GetTriangleCount();
		return FString::Printf(TEXT("Mesh generated (%d tris) but save failed: %s"), TriCount, *SaveErr);
	}
	Result->SetStringField(TEXT("asset_path"), SavePath);

	// Determine placement: attachment context overrides manual location/rotation
	FVector Location = FVector::ZeroVector;
	FRotator Rotation = FRotator::ZeroRotator;

	if (AttachCtx.bValid)
	{
		// Auto-orient from wall normal
		Rotation = ComputeWallRotation(AttachCtx.WallNormal);
		Location = ComputeAttachmentPosition(
			AttachCtx.WallOrigin, AttachCtx.WallNormal, AttachCtx.WallRight,
			FeatureWidth, FeatureDepth, AttachCtx.WallWidth);

		Result->SetBoolField(TEXT("auto_oriented"), true);
	}
	else
	{
		// Fall back to explicit location + rotation params
		MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location);
		float YawDeg = GetFloat(Params, TEXT("rotation"), 0.0f);
		Rotation = FRotator(0.0f, YawDeg, 0.0f);
	}

	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);

	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);
	if (Folder.IsEmpty())
	{
		Folder = TEXT("Procedural/ArchFeatures");
	}

	AActor* Actor = FMonolithMeshProceduralActions::PlaceMeshInScene(
		SavePath, Location, Rotation, Label, /*bSnapToFloor=*/false, Folder);
	if (Actor)
	{
		Result->SetStringField(TEXT("actor_name"), Actor->GetActorNameOrLabel());
	}

	return FString(); // success
}

// ============================================================================
// Railing Builder (shared by balcony, porch, fire escape, ramp, create_railing)
// ============================================================================

void FMonolithMeshArchFeatureActions::BuildRailingGeometry(UDynamicMesh* Mesh, const TArray<FVector>& Path,
	float Height, const FString& Style, float PostSpacing, float PostWidth,
	float RailWidth, float BarSpacing, float BarWidth, float PanelThickness,
	bool bClosedLoop)
{
	if (Path.Num() < 2) return;

	FGeometryScriptPrimitiveOptions Opts;
	const float TopRailThickness = RailWidth;

	// Build segment list (pairs of points)
	int32 SegCount = bClosedLoop ? Path.Num() : Path.Num() - 1;

	for (int32 Seg = 0; Seg < SegCount; ++Seg)
	{
		const FVector& A = Path[Seg];
		const FVector& B = Path[(Seg + 1) % Path.Num()];
		FVector Dir = B - A;
		float SegLen = Dir.Size();
		if (SegLen < 1.0f) continue;
		Dir /= SegLen;

		// Compute rotation from X-axis to segment direction
		FRotator SegRot = Dir.Rotation();

		// Top rail along this segment
		FVector RailCenter = (A + B) * 0.5f + FVector(0, 0, Height - TopRailThickness * 0.5f);
		FTransform RailXf(SegRot, RailCenter, FVector::OneVector);
		// AppendBox: DimX = along segment direction, DimY = width, DimZ = height
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, RailXf, SegLen, TopRailThickness, TopRailThickness, 0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);

		// Posts along this segment
		int32 NumPosts = FMath::Max(2, FMath::CeilToInt32(SegLen / PostSpacing) + 1);
		for (int32 Pi = 0; Pi < NumPosts; ++Pi)
		{
			float T = (NumPosts > 1) ? static_cast<float>(Pi) / static_cast<float>(NumPosts - 1) : 0.0f;
			FVector PostBase = FMath::Lerp(A, B, T);
			FTransform PostXf(FRotator::ZeroRotator, PostBase, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, PostXf, PostWidth, PostWidth, Height, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}

		// Style-specific infill
		if (Style == TEXT("bars"))
		{
			// Vertical bars between posts
			float FillHeight = Height - TopRailThickness;
			int32 NumBars = FMath::Max(0, FMath::FloorToInt32(SegLen / BarSpacing) - 1);
			for (int32 Bi = 1; Bi <= NumBars; ++Bi)
			{
				float BT = static_cast<float>(Bi) * BarSpacing / SegLen;
				if (BT >= 1.0f) break;
				FVector BarBase = FMath::Lerp(A, B, BT);
				FTransform BarXf(FRotator::ZeroRotator, BarBase, FVector::OneVector);
				UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
					Mesh, Opts, BarXf, BarWidth, BarWidth, FillHeight, 0, 0, 0,
					EGeometryScriptPrimitiveOriginMode::Base);
			}
		}
		else if (Style == TEXT("solid"))
		{
			// Solid panel
			float PanelHeight = Height - TopRailThickness;
			FVector PanelCenter = (A + B) * 0.5f + FVector(0, 0, PanelHeight * 0.5f);
			FTransform PanelXf(SegRot, PanelCenter, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, PanelXf, SegLen, PanelThickness, PanelHeight, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Center);
		}
		// "simple" style = posts + top rail only (no infill)
	}
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshArchFeatureActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// Schema description for the building_context param (shared across all 5 actions)
	static const FString BuildingContextDesc = TEXT(
		"Optional building context for auto-orientation. Object with: "
		"wall (string: north/south/east/west), floor_index (int), "
		"world_origin ([x,y,z]), normal ([x,y,z] outward), "
		"width (wall width cm), height (wall height cm), "
		"building_id (string). When provided, overrides location/rotation "
		"and emits wall_openings in the result.");

	// ---- create_balcony ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_balcony"),
		TEXT("Generate a balcony: floor slab + railing extending from an upper floor wall face. "
			"Styles: simple (posts + top rail), bars (vertical balusters), solid (solid panel). "
			"With building_context: auto-orients to wall normal and emits wall_openings (french_door)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshArchFeatureActions::CreateBalcony),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path (e.g. /Game/Town/SM_Balcony_01)"))
			.Required(TEXT("width"), TEXT("number"), TEXT("Balcony width along the wall (cm)"))
			.Required(TEXT("depth"), TEXT("number"), TEXT("How far it extends from the wall (cm)"))
			.Optional(TEXT("floor_thickness"), TEXT("number"), TEXT("Slab thickness (cm)"), TEXT("15"))
			.Optional(TEXT("railing_height"), TEXT("number"), TEXT("Railing height (cm)"), TEXT("100"))
			.Optional(TEXT("railing_style"), TEXT("string"), TEXT("simple, bars, or solid"), TEXT("bars"))
			.Optional(TEXT("bar_spacing"), TEXT("number"), TEXT("Space between railing bars (cm)"), TEXT("12"))
			.Optional(TEXT("bar_diameter"), TEXT("number"), TEXT("Bar thickness (cm)"), TEXT("2"))
			.Optional(TEXT("has_floor_drain"), TEXT("boolean"), TEXT("Slight slope for drainage"), TEXT("true"))
			.Optional(TEXT("material_slab"), TEXT("string"), TEXT("Material for slab (slot 0)"))
			.Optional(TEXT("material_railing"), TEXT("string"), TEXT("Material for railing (slot 1)"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x,y,z] — bottom of slab at wall face"))
			.Optional(TEXT("rotation"), TEXT("number"), TEXT("Yaw rotation in degrees"))
			.Optional(TEXT("building_context"), TEXT("object"), BuildingContextDesc)
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing asset"), TEXT("false"))
			.Build());

	// ---- create_porch ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_porch"),
		TEXT("Generate a covered porch: floor platform, support columns, roof slab, and optional entry steps with railings. "
			"Configurable column count, step geometry, roof overhang. "
			"With building_context: auto-orients, aligns porch floor to building floor, emits wall_openings (door)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshArchFeatureActions::CreatePorch),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path (e.g. /Game/Town/SM_Porch_01)"))
			.Required(TEXT("width"), TEXT("number"), TEXT("Porch width (cm)"))
			.Required(TEXT("depth"), TEXT("number"), TEXT("Porch depth (cm)"))
			.Optional(TEXT("height"), TEXT("number"), TEXT("Porch roof height from ground (cm)"), TEXT("270"))
			.Optional(TEXT("column_count"), TEXT("number"), TEXT("Number of support columns"), TEXT("2"))
			.Optional(TEXT("column_diameter"), TEXT("number"), TEXT("Column diameter (cm)"), TEXT("20"))
			.Optional(TEXT("has_roof"), TEXT("boolean"), TEXT("Generate roof slab"), TEXT("true"))
			.Optional(TEXT("roof_overhang"), TEXT("number"), TEXT("Roof extends beyond columns (cm)"), TEXT("15"))
			.Optional(TEXT("has_steps"), TEXT("boolean"), TEXT("Generate entry steps"), TEXT("true"))
			.Optional(TEXT("step_count"), TEXT("number"), TEXT("Number of steps (auto from height if 0)"), TEXT("3"))
			.Optional(TEXT("step_depth"), TEXT("number"), TEXT("Each step depth (cm)"), TEXT("30"))
			.Optional(TEXT("step_height"), TEXT("number"), TEXT("Each step height (cm)"), TEXT("18"))
			.Optional(TEXT("railing_height"), TEXT("number"), TEXT("Step railing height (0 = no railing)"), TEXT("90"))
			.Optional(TEXT("material_floor"), TEXT("string"), TEXT("Floor material (slot 0)"))
			.Optional(TEXT("material_column"), TEXT("string"), TEXT("Column material (slot 1)"))
			.Optional(TEXT("material_roof"), TEXT("string"), TEXT("Roof material (slot 2)"))
			.Optional(TEXT("material_steps"), TEXT("string"), TEXT("Steps material (slot 3)"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x,y,z]"))
			.Optional(TEXT("rotation"), TEXT("number"), TEXT("Yaw rotation in degrees"))
			.Optional(TEXT("building_context"), TEXT("object"), BuildingContextDesc)
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing asset"), TEXT("false"))
			.Build());

	// ---- create_fire_escape ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_fire_escape"),
		TEXT("Generate a multi-story fire escape: zigzag exterior stairs between floor landings. "
			"Each floor gets a landing platform. Stairs alternate left/right. Optional roof ladder. "
			"With building_context: auto-orients to wall, aligns landings to floor heights, emits wall_openings (windows)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshArchFeatureActions::CreateFireEscape),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path (e.g. /Game/Town/SM_FireEscape_01)"))
			.Required(TEXT("floor_count"), TEXT("number"), TEXT("Number of floors to span"))
			.Required(TEXT("floor_height"), TEXT("number"), TEXT("Height per floor (cm)"))
			.Optional(TEXT("landing_width"), TEXT("number"), TEXT("Landing platform width (cm)"), TEXT("150"))
			.Optional(TEXT("landing_depth"), TEXT("number"), TEXT("Landing platform depth (cm)"), TEXT("120"))
			.Optional(TEXT("stair_width"), TEXT("number"), TEXT("Stair run width (cm)"), TEXT("90"))
			.Optional(TEXT("railing_height"), TEXT("number"), TEXT("Railing height (cm)"), TEXT("100"))
			.Optional(TEXT("has_ladder"), TEXT("boolean"), TEXT("Top floor ladder to roof"), TEXT("true"))
			.Optional(TEXT("ladder_height"), TEXT("number"), TEXT("Ladder extension above top landing (cm)"), TEXT("150"))
			.Optional(TEXT("material_platform"), TEXT("string"), TEXT("Platform material (slot 0)"))
			.Optional(TEXT("material_railing"), TEXT("string"), TEXT("Railing material (slot 1)"))
			.Optional(TEXT("material_stairs"), TEXT("string"), TEXT("Stairs material (slot 2)"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x,y,z] — base attachment point"))
			.Optional(TEXT("rotation"), TEXT("number"), TEXT("Yaw rotation in degrees"))
			.Optional(TEXT("building_context"), TEXT("object"), BuildingContextDesc)
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing asset"), TEXT("false"))
			.Build());

	// ---- create_ramp_connector ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_ramp_connector"),
		TEXT("Generate an ADA-compliant ramp between two heights. Auto-computes run length from rise and slope ratio. "
			"Adds intermediate switchback landings if rise exceeds max_rise_per_run. "
			"With building_context: auto-orients to wall and emits wall_openings (door at top)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshArchFeatureActions::CreateRampConnector),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path (e.g. /Game/Town/SM_Ramp_01)"))
			.Required(TEXT("rise"), TEXT("number"), TEXT("Total height change (cm)"))
			.Optional(TEXT("width"), TEXT("number"), TEXT("Ramp width (cm)"), TEXT("120"))
			.Optional(TEXT("slope_ratio"), TEXT("number"), TEXT("Rise-to-run ratio (1/12 for ADA)"), TEXT("0.0833"))
			.Optional(TEXT("max_rise_per_run"), TEXT("number"), TEXT("Max rise before landing (cm, 76 for ADA)"), TEXT("76"))
			.Optional(TEXT("landing_length"), TEXT("number"), TEXT("Landing pad length (cm)"), TEXT("150"))
			.Optional(TEXT("railing_height"), TEXT("number"), TEXT("Railing height (cm)"), TEXT("90"))
			.Optional(TEXT("railing_style"), TEXT("string"), TEXT("simple or bars"), TEXT("simple"))
			.Optional(TEXT("material_ramp"), TEXT("string"), TEXT("Ramp material (slot 0)"))
			.Optional(TEXT("material_railing"), TEXT("string"), TEXT("Railing material (slot 1)"))
			.Optional(TEXT("material_landing"), TEXT("string"), TEXT("Landing material (slot 2)"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x,y,z] — base of ramp"))
			.Optional(TEXT("rotation"), TEXT("number"), TEXT("Yaw rotation in degrees"))
			.Optional(TEXT("building_context"), TEXT("object"), BuildingContextDesc)
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing asset"), TEXT("false"))
			.Build());

	// ---- create_railing ----
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_railing"),
		TEXT("Generate a railing along an arbitrary path defined by 3D points. "
			"Styles: simple (posts + top rail), bars (+ vertical balusters), solid (+ panel infill). "
			"With building_context: auto-orients to wall normal for placement."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshArchFeatureActions::CreateRailing),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path (e.g. /Game/Town/SM_Railing_01)"))
			.Required(TEXT("points"), TEXT("array"), TEXT("Array of [x,y,z] points defining the railing path"))
			.Optional(TEXT("height"), TEXT("number"), TEXT("Railing height (cm)"), TEXT("100"))
			.Optional(TEXT("style"), TEXT("string"), TEXT("simple, bars, or solid"), TEXT("bars"))
			.Optional(TEXT("post_spacing"), TEXT("number"), TEXT("Distance between posts (cm)"), TEXT("120"))
			.Optional(TEXT("post_width"), TEXT("number"), TEXT("Post cross-section (cm)"), TEXT("4"))
			.Optional(TEXT("rail_width"), TEXT("number"), TEXT("Top rail cross-section (cm)"), TEXT("5"))
			.Optional(TEXT("bar_spacing"), TEXT("number"), TEXT("Vertical bar spacing for bars style (cm)"), TEXT("12"))
			.Optional(TEXT("bar_width"), TEXT("number"), TEXT("Bar cross-section (cm)"), TEXT("2"))
			.Optional(TEXT("panel_thickness"), TEXT("number"), TEXT("Panel thickness for solid style (cm)"), TEXT("3"))
			.Optional(TEXT("closed_loop"), TEXT("boolean"), TEXT("Connect last point to first"), TEXT("false"))
			.Optional(TEXT("material"), TEXT("string"), TEXT("Material path (slot 0)"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x,y,z]"))
			.Optional(TEXT("building_context"), TEXT("object"), BuildingContextDesc)
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing asset"), TEXT("false"))
			.Build());
}

// ============================================================================
// create_balcony
// ============================================================================

FMonolithActionResult FMonolithMeshArchFeatureActions::CreateBalcony(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool) return FMonolithActionResult::Error(GS_ERROR_ARCH);

	// Required params
	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));

	float Width = 0.0f, Depth = 0.0f;
	if (!Params->HasField(TEXT("width")))
		return FMonolithActionResult::Error(TEXT("Missing required param: width"));
	if (!Params->HasField(TEXT("depth")))
		return FMonolithActionResult::Error(TEXT("Missing required param: depth"));

	Width = static_cast<float>(Params->GetNumberField(TEXT("width")));
	Depth = static_cast<float>(Params->GetNumberField(TEXT("depth")));

	if (Width <= 0.0f || Depth <= 0.0f)
		return FMonolithActionResult::Error(TEXT("width and depth must be positive"));

	// Optional params
	const float FloorThick   = GetFloat(Params, TEXT("floor_thickness"), 15.0f);
	const float RailHeight   = GetFloat(Params, TEXT("railing_height"), 100.0f);
	const FString RailStyle  = GetString(Params, TEXT("railing_style"), TEXT("bars")).ToLower();
	const float BarSpacing   = GetFloat(Params, TEXT("bar_spacing"), 12.0f);
	const float BarDiam      = GetFloat(Params, TEXT("bar_diameter"), 2.0f);
	const bool bFloorDrain   = GetBool(Params, TEXT("has_floor_drain"), true);

	// Parse attachment context (optional)
	FAttachmentContext AttachCtx = ParseBuildingContext(Params);

	// Validate railing style
	if (RailStyle != TEXT("simple") && RailStyle != TEXT("bars") && RailStyle != TEXT("solid"))
		return FMonolithActionResult::Error(FString::Printf(TEXT("Invalid railing_style '%s'. Valid: simple, bars, solid"), *RailStyle));

	// Create mesh
	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh) return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));

	FGeometryScriptPrimitiveOptions Opts;

	// ---- Floor slab ----
	// Slab sits at Z=0 (bottom), extends in +Y direction (away from wall)
	// Origin mode Base: Z=0 is bottom of the box
	{
		FVector SlabCenter(0.0f, Depth * 0.5f, 0.0f);
		FTransform SlabXf(FRotator::ZeroRotator, SlabCenter, FVector::OneVector);

		float SlabThick = FloorThick;
		if (bFloorDrain)
		{
			// Slight slope: make the slab slightly thinner at the outer edge.
			// Since AppendBox can't do tapered geometry, we just use the slab as-is.
			// The "drain" is represented by a tiny wedge — for blockout fidelity, flat slab is fine.
			SlabThick = FloorThick;
		}

		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, SlabXf, Width, Depth, SlabThick, 0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);
	}

	// ---- Railing ----
	// Three-sided railing: left edge, front edge, right edge (not against wall)
	if (RailHeight > 0.0f)
	{
		const float HalfW = Width * 0.5f;
		const float RailZ = FloorThick * 0.5f; // top of slab

		TArray<FVector> RailPath;
		RailPath.Add(FVector(-HalfW, 0.0f, RailZ));        // left-wall corner
		RailPath.Add(FVector(-HalfW, Depth, RailZ));        // left-front corner
		RailPath.Add(FVector(HalfW, Depth, RailZ));          // right-front corner
		RailPath.Add(FVector(HalfW, 0.0f, RailZ));          // right-wall corner

		const float PostWidth = 4.0f;
		const float RailWidth = 5.0f;
		const float PanelThick = 3.0f;

		BuildRailingGeometry(Mesh, RailPath, RailHeight, RailStyle,
			/*PostSpacing=*/FMath::Max(BarSpacing * 10.0f, 100.0f), PostWidth, RailWidth,
			BarSpacing, BarDiam, PanelThick, /*bClosedLoop=*/false);
	}

	// Finalize
	FinalizeGeometry(Mesh);

	int32 TriCount = Mesh->GetTriangleCount();

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("type"), TEXT("balcony"));
	Result->SetNumberField(TEXT("width"), Width);
	Result->SetNumberField(TEXT("depth"), Depth);
	Result->SetStringField(TEXT("railing_style"), RailStyle);
	Result->SetNumberField(TEXT("triangle_count"), TriCount);

	// Emit wall openings when attachment context is provided (Fix #9: balcony door access)
	if (AttachCtx.bValid)
	{
		TArray<FWallOpeningRequest> Openings;
		FWallOpeningRequest DoorOpening;
		DoorOpening.BuildingId = AttachCtx.BuildingId;
		DoorOpening.Wall = AttachCtx.Wall;
		DoorOpening.FloorIndex = AttachCtx.FloorIndex;
		DoorOpening.PositionAlongWall = AttachCtx.WallWidth * 0.5f; // centered on wall
		DoorOpening.Width = 110.0f;    // door opening width (cm)
		DoorOpening.Height = 230.0f;   // door opening height (cm)
		DoorOpening.SillHeight = 0.0f; // floor-level access
		DoorOpening.Type = TEXT("door");
		DoorOpening.Purpose = TEXT("balcony_access");
		Openings.Add(DoorOpening);
		EmitWallOpenings(Result, Openings);
	}

	FString FinalErr = SaveAndPlace(Mesh, Params, Result, AttachCtx, Width, Depth);
	if (!FinalErr.IsEmpty())
		return FMonolithActionResult::Error(FinalErr);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// create_porch
// ============================================================================

FMonolithActionResult FMonolithMeshArchFeatureActions::CreatePorch(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool) return FMonolithActionResult::Error(GS_ERROR_ARCH);

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));

	if (!Params->HasField(TEXT("width")))
		return FMonolithActionResult::Error(TEXT("Missing required param: width"));
	if (!Params->HasField(TEXT("depth")))
		return FMonolithActionResult::Error(TEXT("Missing required param: depth"));

	const float Width   = static_cast<float>(Params->GetNumberField(TEXT("width")));
	const float Depth   = static_cast<float>(Params->GetNumberField(TEXT("depth")));

	if (Width <= 0.0f || Depth <= 0.0f)
		return FMonolithActionResult::Error(TEXT("width and depth must be positive"));

	const float Height     = GetFloat(Params, TEXT("height"), 270.0f);
	const int32 ColCount   = GetInt(Params, TEXT("column_count"), 2);
	const float ColDiam    = GetFloat(Params, TEXT("column_diameter"), 20.0f);
	const bool bHasRoof    = GetBool(Params, TEXT("has_roof"), true);
	const float RoofOver   = GetFloat(Params, TEXT("roof_overhang"), 15.0f);
	const bool bHasSteps   = GetBool(Params, TEXT("has_steps"), true);
	const float StepDepth  = GetFloat(Params, TEXT("step_depth"), 30.0f);
	const float StepHeight = GetFloat(Params, TEXT("step_height"), 18.0f);
	const float RailHeight = GetFloat(Params, TEXT("railing_height"), 90.0f);

	// Parse attachment context (optional)
	FAttachmentContext AttachCtx = ParseBuildingContext(Params);

	// Floor height: if building context is provided, derive porch floor from building floor level.
	// Otherwise fall back to step_count * step_height.
	int32 StepCount = GetInt(Params, TEXT("step_count"), 3);
	float PorchFloorZ = 0.0f;

	if (AttachCtx.bValid)
	{
		// Porch floor should match the building's floor level.
		// world_origin.Z gives the base of the wall face on this floor.
		// For a ground floor porch, PorchFloorZ = world_origin.Z (relative to the mesh origin).
		// Steps count is computed from porch floor height down to ground (Z=0).
		PorchFloorZ = AttachCtx.WallOrigin.Z;

		if (bHasSteps && PorchFloorZ > StepHeight * 0.5f)
		{
			// Auto-compute steps from porch floor to ground
			StepCount = FMath::Max(1, FMath::RoundToInt32(PorchFloorZ / StepHeight));
			// The porch floor Z is defined by the building, steps adapt to reach it
		}
		else if (!bHasSteps || PorchFloorZ < StepHeight * 0.5f)
		{
			StepCount = 0;
			// Floor is at or near ground level; no steps needed
		}

		// Zero out the PorchFloorZ for geometry generation since we use it relative to mesh origin.
		// The attachment system handles world positioning.
		// Geometry is still built starting from Z=0 in local space; we store the computed Z offset.
	}
	else
	{
		if (StepCount <= 0 && bHasSteps)
		{
			// Auto-compute step count from a reasonable porch floor height
			float PorchFloorH = 54.0f; // 3 steps * 18cm default
			StepCount = FMath::Max(1, FMath::RoundToInt32(PorchFloorH / StepHeight));
		}
		PorchFloorZ = bHasSteps ? (StepCount * StepHeight) : 0.0f;
	}
	const float FloorThick = 10.0f;

	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh) return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));

	FGeometryScriptPrimitiveOptions Opts;

	// ---- Floor platform ----
	{
		FVector FloorPos(0.0f, Depth * 0.5f, PorchFloorZ);
		FTransform FloorXf(FRotator::ZeroRotator, FloorPos, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, FloorXf, Width, Depth, FloorThick, 0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);
	}

	// ---- Columns ----
	if (ColCount > 0)
	{
		const float ColRadius = ColDiam * 0.5f;
		const float ColHeight = Height - PorchFloorZ - FloorThick * 0.5f;
		const float ColZ = PorchFloorZ + FloorThick * 0.5f;

		// Distribute columns evenly along the front edge
		for (int32 Ci = 0; Ci < ColCount; ++Ci)
		{
			float T = (ColCount > 1) ? static_cast<float>(Ci) / static_cast<float>(ColCount - 1) : 0.5f;
			float X = FMath::Lerp(-Width * 0.5f + ColRadius + 5.0f, Width * 0.5f - ColRadius - 5.0f, T);

			FTransform ColXf(FRotator::ZeroRotator, FVector(X, Depth - ColRadius - 5.0f, ColZ), FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendCylinder(
				Mesh, Opts, ColXf, ColRadius, ColHeight, 12, 0, true,
				EGeometryScriptPrimitiveOriginMode::Base);
		}
	}

	// ---- Roof ----
	if (bHasRoof)
	{
		const float RoofThick = 8.0f;
		const float RoofW = Width + RoofOver * 2.0f;
		const float RoofD = Depth + RoofOver * 2.0f;

		FVector RoofPos(0.0f, Depth * 0.5f, Height - RoofThick * 0.5f);
		FTransform RoofXf(FRotator::ZeroRotator, RoofPos, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, RoofXf, RoofW, RoofD, RoofThick, 0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);
	}

	// ---- Steps ----
	if (bHasSteps && StepCount > 0)
	{
		for (int32 Si = 0; Si < StepCount; ++Si)
		{
			float SZ = Si * StepHeight;
			float SY = -(Si + 1) * StepDepth + StepDepth * 0.5f; // steps extend in -Y (towards viewer)

			// Each step is full-width
			FVector StepPos(0.0f, Depth + (Si + 1) * StepDepth - StepDepth * 0.5f, SZ + StepHeight * 0.5f);
			// Actually, steps descend from the porch front edge outward (in +Y direction from origin)
			// Recalculate: step 0 is the lowest (farthest from porch), step N-1 is at porch floor
			float StepZ = (Si) * StepHeight;
			float StepY = Depth + (StepCount - Si) * StepDepth - StepDepth * 0.5f;

			FTransform StepXf(FRotator::ZeroRotator, FVector(0.0f, StepY, StepZ + StepHeight * 0.5f), FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, StepXf, Width, StepDepth, StepHeight, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Center);
		}

		// ---- Step railings ----
		if (RailHeight > 0.0f)
		{
			const float HalfW = Width * 0.5f;
			const float TotalStepRun = StepCount * StepDepth;

			// Left side railing (following the step diagonal)
			for (int32 Side = 0; Side < 2; ++Side)
			{
				float X = (Side == 0) ? -HalfW : HalfW;
				TArray<FVector> StepRailPath;

				// Bottom of stairs
				StepRailPath.Add(FVector(X, Depth + TotalStepRun, 0.0f));
				// Top of stairs (porch floor level)
				StepRailPath.Add(FVector(X, Depth, PorchFloorZ));

				BuildRailingGeometry(Mesh, StepRailPath, RailHeight, TEXT("simple"),
					/*PostSpacing=*/100.0f, /*PostWidth=*/4.0f, /*RailWidth=*/5.0f,
					/*BarSpacing=*/12.0f, /*BarWidth=*/2.0f, /*PanelThick=*/3.0f,
					/*bClosedLoop=*/false);
			}
		}
	}

	// Finalize
	FinalizeGeometry(Mesh);

	int32 TriCount = Mesh->GetTriangleCount();

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("type"), TEXT("porch"));
	Result->SetNumberField(TEXT("width"), Width);
	Result->SetNumberField(TEXT("depth"), Depth);
	Result->SetNumberField(TEXT("height"), Height);
	Result->SetNumberField(TEXT("column_count"), ColCount);
	Result->SetNumberField(TEXT("step_count"), StepCount);
	Result->SetNumberField(TEXT("porch_floor_z"), PorchFloorZ);
	Result->SetNumberField(TEXT("triangle_count"), TriCount);

	// Emit wall openings when attachment context is provided (Fix #10: porch entry door)
	if (AttachCtx.bValid)
	{
		TArray<FWallOpeningRequest> Openings;
		FWallOpeningRequest DoorOpening;
		DoorOpening.BuildingId = AttachCtx.BuildingId;
		DoorOpening.Wall = AttachCtx.Wall;
		DoorOpening.FloorIndex = AttachCtx.FloorIndex;
		DoorOpening.PositionAlongWall = AttachCtx.WallWidth * 0.5f; // centered on wall
		DoorOpening.Width = 110.0f;    // 110cm for momentum-based FPS movement (R2-I2)
		DoorOpening.Height = 230.0f;   // standard door height
		DoorOpening.SillHeight = 0.0f; // floor-level entry
		DoorOpening.Type = TEXT("door");
		DoorOpening.Purpose = TEXT("porch_entry");
		Openings.Add(DoorOpening);
		EmitWallOpenings(Result, Openings);
	}

	FString FinalErr = SaveAndPlace(Mesh, Params, Result, AttachCtx, Width, Depth);
	if (!FinalErr.IsEmpty())
		return FMonolithActionResult::Error(FinalErr);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// create_fire_escape
// ============================================================================

FMonolithActionResult FMonolithMeshArchFeatureActions::CreateFireEscape(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool) return FMonolithActionResult::Error(GS_ERROR_ARCH);

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));

	if (!Params->HasField(TEXT("floor_count")))
		return FMonolithActionResult::Error(TEXT("Missing required param: floor_count"));
	if (!Params->HasField(TEXT("floor_height")))
		return FMonolithActionResult::Error(TEXT("Missing required param: floor_height"));

	const int32 FloorCount   = GetInt(Params, TEXT("floor_count"), 2);
	const float FloorHeight  = static_cast<float>(Params->GetNumberField(TEXT("floor_height")));

	if (FloorCount < 1) return FMonolithActionResult::Error(TEXT("floor_count must be >= 1"));
	if (FloorHeight <= 0.0f) return FMonolithActionResult::Error(TEXT("floor_height must be positive"));

	const float LandingW    = GetFloat(Params, TEXT("landing_width"), 150.0f);
	const float LandingD    = GetFloat(Params, TEXT("landing_depth"), 120.0f);
	const float StairW      = GetFloat(Params, TEXT("stair_width"), 90.0f);
	const float RailHeight  = GetFloat(Params, TEXT("railing_height"), 100.0f);
	const bool bHasLadder   = GetBool(Params, TEXT("has_ladder"), true);
	const float LadderH     = GetFloat(Params, TEXT("ladder_height"), 150.0f);

	// Parse attachment context (optional)
	FAttachmentContext AttachCtx = ParseBuildingContext(Params);

	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh) return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));

	FGeometryScriptPrimitiveOptions Opts;
	const float PlatformThick = 5.0f;
	const float TreadThick = 3.0f;
	const float StringerW = 4.0f;

	// Stair geometry constants — IBC fire escape: 20cm tread / 20cm riser = 45 deg max
	const float StepDepth   = GetFloat(Params, TEXT("step_depth"), 20.0f);  // IBC fire escape minimum 8"
	const float TargetRiser = GetFloat(Params, TEXT("step_rise"), 20.0f);   // IBC fire escape maximum 8"
	const int32 StepsPerFlight = FMath::Max(2, FMath::RoundToInt32(FloorHeight / TargetRiser));
	const float ActualStepH = FloorHeight / static_cast<float>(StepsPerFlight);

	// Stair run extends BEYOND the landing — this is the correct fire escape layout
	const float StairRunLength = StepDepth * StepsPerFlight;

	// Validate angle
	const float StairAngleDeg = FMath::RadiansToDegrees(FMath::Atan2(ActualStepH, StepDepth));
	if (StairAngleDeg > 50.0f)
	{
		UE_LOG(LogTemp, Warning, TEXT("Fire escape stair angle %.1f deg exceeds 45 deg IBC max. "
			"Consider increasing step_depth or decreasing step_rise."), StairAngleDeg);
	}

	// Fire escape layout: landings at each floor level, attached to the building wall (Y=0 side).
	// Stairs extend outward from landings in +Y. Flights zigzag: even floors descend to the left (-X),
	// odd floors descend to the right (+X). Mid-level landings at half-floor height connect flights.

	// Helper lambda: build a single flight of treads + stringers + railings
	auto BuildFlight = [&](float FlightBottomZ, float FlightTopZ, float FlightStartY,
		float FlightEndY, float FlightX, int32 NumSteps)
	{
		float FlightRun = FMath::Abs(FlightEndY - FlightStartY);
		float FlightRise = FlightTopZ - FlightBottomZ;
		float YDir = (FlightEndY > FlightStartY) ? 1.0f : -1.0f;

		// Treads
		for (int32 Si = 0; Si < NumSteps; ++Si)
		{
			float T = static_cast<float>(Si) / static_cast<float>(NumSteps);
			float TreadZ = FMath::Lerp(FlightBottomZ, FlightTopZ, T);
			float TreadY = FlightStartY + YDir * StepDepth * Si;

			FTransform TreadXf(FRotator::ZeroRotator,
				FVector(FlightX, TreadY, TreadZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, TreadXf, StairW, StepDepth, TreadThick, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Center);
		}

		// Stringers (left and right side beams)
		{
			float StringerLen = FMath::Sqrt(FMath::Square(FlightRun) + FMath::Square(FlightRise));
			FVector StringerDir = FVector(0.0f, YDir * FlightRun, FlightRise);
			StringerDir.Normalize();
			FRotator StringerRot = StringerDir.Rotation();

			for (int32 Side = 0; Side < 2; ++Side)
			{
				float SX = FlightX + (Side == 0 ? -StairW * 0.5f : StairW * 0.5f);
				FTransform StrXf(StringerRot,
					FVector(SX, (FlightStartY + FlightEndY) * 0.5f, (FlightBottomZ + FlightTopZ) * 0.5f),
					FVector::OneVector);
				UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
					Mesh, Opts, StrXf, StringerLen, StringerW, StringerW, 0, 0, 0,
					EGeometryScriptPrimitiveOriginMode::Center);
			}
		}

		// Railings
		if (RailHeight > 0.0f)
		{
			for (int32 Side = 0; Side < 2; ++Side)
			{
				float SX = FlightX + (Side == 0 ? -StairW * 0.5f : StairW * 0.5f);
				TArray<FVector> StairRailPath;
				StairRailPath.Add(FVector(SX, FlightStartY, FlightBottomZ + TreadThick * 0.5f));
				StairRailPath.Add(FVector(SX, FlightEndY, FlightTopZ + TreadThick * 0.5f));

				BuildRailingGeometry(Mesh, StairRailPath, RailHeight, TEXT("bars"),
					/*PostSpacing=*/80.0f, /*PostWidth=*/3.0f, /*RailWidth=*/4.0f,
					/*BarSpacing=*/12.0f, /*BarWidth=*/2.0f, /*PanelThick=*/3.0f,
					/*bClosedLoop=*/false);
			}
		}
	};

	// Helper lambda: build a landing platform with three-sided railing
	auto BuildLanding = [&](FVector LandingCenter, float LandW, float LandD)
	{
		FTransform PlatXf(FRotator::ZeroRotator, LandingCenter, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, PlatXf, LandW, LandD, PlatformThick, 0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);

		if (RailHeight > 0.0f)
		{
			const float HalfW = LandW * 0.5f;
			const float HalfD = LandD * 0.5f;
			const float RailZ = LandingCenter.Z + PlatformThick * 0.5f;

			TArray<FVector> RailPath;
			RailPath.Add(FVector(LandingCenter.X - HalfW, LandingCenter.Y - HalfD, RailZ));
			RailPath.Add(FVector(LandingCenter.X - HalfW, LandingCenter.Y + HalfD, RailZ));
			RailPath.Add(FVector(LandingCenter.X + HalfW, LandingCenter.Y + HalfD, RailZ));
			RailPath.Add(FVector(LandingCenter.X + HalfW, LandingCenter.Y - HalfD, RailZ));

			BuildRailingGeometry(Mesh, RailPath, RailHeight, TEXT("bars"),
				/*PostSpacing=*/100.0f, /*PostWidth=*/3.0f, /*RailWidth=*/4.0f,
				/*BarSpacing=*/12.0f, /*BarWidth=*/2.0f, /*PanelThick=*/3.0f,
				/*bClosedLoop=*/false);
		}
	};

	// Build floor-level landings and inter-floor flights.
	// For each floor gap (Fi to Fi+1), we use two half-flights with a mid-level landing.
	// Half-flight steps
	const int32 HalfSteps = StepsPerFlight / 2;
	const int32 RemainderSteps = StepsPerFlight - HalfSteps;
	const float HalfRise = ActualStepH * HalfSteps;

	for (int32 Fi = 0; Fi < FloorCount; ++Fi)
	{
		float FloorZ = static_cast<float>(Fi + 1) * FloorHeight;

		// Floor-level landing at Y=0 (against the building wall)
		BuildLanding(FVector(0.0f, LandingD * 0.5f, FloorZ), LandingW, LandingD);
	}

	// Now build stair flights between floors. Each floor gap gets two half-flights + a mid-landing.
	// Flight 1: from lower floor landing, extends in +Y
	// Mid-landing: at half-floor height, offset in X from floor landings
	// Flight 2: from mid-landing back toward the building in -Y, arriving at upper floor landing

	// Ground-to-first-floor flight
	{
		float BottomZ = PlatformThick * 0.5f; // ground level
		float TopZ = FloorHeight;              // first floor landing

		// Flight direction alternation: ground flight always goes left
		float MidLandingX = -(LandingW * 0.5f + StairW * 0.5f);

		// Flight 1 (lower half): from ground at Y=0, extending outward in +Y
		float Flight1StartY = LandingD * 0.5f;
		float Flight1EndY = Flight1StartY + StepDepth * HalfSteps;
		float Flight1TopZ = BottomZ + HalfRise;

		BuildFlight(BottomZ, Flight1TopZ, Flight1StartY, Flight1EndY, MidLandingX, HalfSteps);

		// Mid-level landing
		float MidZ = Flight1TopZ;
		BuildLanding(FVector(MidLandingX, Flight1EndY + LandingD * 0.5f, MidZ), StairW, LandingD);

		// Flight 2 (upper half): from mid-landing back toward building in -Y
		float Flight2StartY = Flight1EndY + LandingD;
		float Flight2EndY = Flight2StartY - StepDepth * RemainderSteps;
		float Flight2TopZ = TopZ - PlatformThick * 0.5f;

		BuildFlight(MidZ, Flight2TopZ, Flight2StartY, Flight2EndY, MidLandingX, RemainderSteps);
	}

	// Inter-floor flights (floor 1→2, 2→3, etc.)
	for (int32 Fi = 1; Fi < FloorCount; ++Fi)
	{
		float BottomZ = static_cast<float>(Fi) * FloorHeight + PlatformThick * 0.5f;
		float TopZ = static_cast<float>(Fi + 1) * FloorHeight - PlatformThick * 0.5f;

		// Zigzag: even floor indices go left (-X), odd go right (+X)
		float StairOffsetX = (Fi % 2 == 0) ? -(LandingW * 0.5f + StairW * 0.5f) : (LandingW * 0.5f + StairW * 0.5f);

		// Flight 1: from floor landing outward in +Y
		float Flight1StartY = LandingD * 0.5f;
		float Flight1EndY = Flight1StartY + StepDepth * HalfSteps;
		float Flight1TopZ = BottomZ + HalfRise;

		BuildFlight(BottomZ, Flight1TopZ, Flight1StartY, Flight1EndY, StairOffsetX, HalfSteps);

		// Mid-level landing
		float MidZ = Flight1TopZ;
		BuildLanding(FVector(StairOffsetX, Flight1EndY + LandingD * 0.5f, MidZ), StairW, LandingD);

		// Flight 2: from mid-landing back toward building in -Y
		float Flight2StartY = Flight1EndY + LandingD;
		float Flight2EndY = Flight2StartY - StepDepth * RemainderSteps;

		BuildFlight(MidZ, TopZ, Flight2StartY, Flight2EndY, StairOffsetX, RemainderSteps);
	}

	// ---- Roof ladder ----
	if (bHasLadder && FloorCount > 0)
	{
		float TopLandingZ = static_cast<float>(FloorCount) * FloorHeight + PlatformThick * 0.5f;
		float LadderW = 40.0f; // ladder width
		float RungSpacing = 30.0f;
		float RungDiam = 2.5f;
		float RailDiam = 3.0f;

		int32 RungCount = FMath::Max(2, FMath::FloorToInt32(LadderH / RungSpacing));

		// Side rails
		for (int32 Side = 0; Side < 2; ++Side)
		{
			float X = (Side == 0) ? -LadderW * 0.5f : LadderW * 0.5f;
			FTransform RailXf(FRotator::ZeroRotator,
				FVector(X, LandingD * 0.5f, TopLandingZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, RailXf, RailDiam, RailDiam, LadderH, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}

		// Rungs
		for (int32 Ri = 0; Ri < RungCount; ++Ri)
		{
			float RungZ = TopLandingZ + RungSpacing * (Ri + 1);
			if (RungZ > TopLandingZ + LadderH) break;

			FTransform RungXf(FRotator(0, 0, 90), FVector(0.0f, LandingD * 0.5f, RungZ), FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, RungXf, LadderW, RungDiam, RungDiam, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Center);
		}
	}

	// Finalize
	FinalizeGeometry(Mesh);

	int32 TriCount = Mesh->GetTriangleCount();

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("type"), TEXT("fire_escape"));
	Result->SetNumberField(TEXT("floor_count"), FloorCount);
	Result->SetNumberField(TEXT("floor_height"), FloorHeight);
	Result->SetNumberField(TEXT("landing_width"), LandingW);
	Result->SetNumberField(TEXT("landing_depth"), LandingD);
	Result->SetNumberField(TEXT("stair_run_length"), StairRunLength);
	Result->SetNumberField(TEXT("stair_angle_deg"), StairAngleDeg);
	Result->SetNumberField(TEXT("steps_per_flight"), StepsPerFlight);
	Result->SetNumberField(TEXT("step_depth"), StepDepth);
	Result->SetNumberField(TEXT("step_rise"), ActualStepH);
	Result->SetNumberField(TEXT("triangle_count"), TriCount);
	Result->SetBoolField(TEXT("has_ladder"), bHasLadder);

	// Emit wall openings when attachment context is provided (Fix #11: fire escape egress windows)
	if (AttachCtx.bValid)
	{
		TArray<FWallOpeningRequest> Openings;
		for (int32 Fi = 0; Fi < FloorCount; ++Fi)
		{
			FWallOpeningRequest WindowOpening;
			WindowOpening.BuildingId = AttachCtx.BuildingId;
			WindowOpening.Wall = AttachCtx.Wall;
			WindowOpening.FloorIndex = AttachCtx.FloorIndex + Fi + 1; // each landing is one floor up
			WindowOpening.PositionAlongWall = AttachCtx.WallWidth * 0.5f; // centered
			WindowOpening.Width = 70.0f;     // fire escape egress window width (cm)
			WindowOpening.Height = 100.0f;   // fire escape egress window height (cm)
			WindowOpening.SillHeight = 60.0f; // window sill at 60cm above floor
			WindowOpening.Type = TEXT("window");
			WindowOpening.Purpose = TEXT("fire_escape_egress");
			Openings.Add(WindowOpening);
		}
		EmitWallOpenings(Result, Openings);
	}

	FString FinalErr = SaveAndPlace(Mesh, Params, Result, AttachCtx, LandingW, LandingD);
	if (!FinalErr.IsEmpty())
		return FMonolithActionResult::Error(FinalErr);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// create_ramp_connector
// ============================================================================

FMonolithActionResult FMonolithMeshArchFeatureActions::CreateRampConnector(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool) return FMonolithActionResult::Error(GS_ERROR_ARCH);

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));

	if (!Params->HasField(TEXT("rise")))
		return FMonolithActionResult::Error(TEXT("Missing required param: rise"));

	const float Rise = static_cast<float>(Params->GetNumberField(TEXT("rise")));
	if (Rise <= 0.0f) return FMonolithActionResult::Error(TEXT("rise must be positive"));

	const float Width         = GetFloat(Params, TEXT("width"), 120.0f);
	const float SlopeRatio    = GetFloat(Params, TEXT("slope_ratio"), 1.0f / 12.0f);
	const float MaxRisePerRun = GetFloat(Params, TEXT("max_rise_per_run"), 76.0f);
	const float LandingLen    = GetFloat(Params, TEXT("landing_length"), 150.0f);
	const float RailHeight    = GetFloat(Params, TEXT("railing_height"), 90.0f);
	const FString RailStyle   = GetString(Params, TEXT("railing_style"), TEXT("simple")).ToLower();

	// Parse attachment context (optional)
	FAttachmentContext AttachCtx = ParseBuildingContext(Params);

	if (SlopeRatio <= 0.0f || SlopeRatio > 1.0f)
		return FMonolithActionResult::Error(TEXT("slope_ratio must be between 0 and 1 (exclusive)"));

	// Compute number of ramp segments
	int32 NumSegments = FMath::Max(1, FMath::CeilToInt32(Rise / MaxRisePerRun));
	float RisePerSeg = Rise / static_cast<float>(NumSegments);
	float RunPerSeg = RisePerSeg / SlopeRatio;

	const float RampThick = 10.0f;
	const float LandingThick = 10.0f;

	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh) return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));

	FGeometryScriptPrimitiveOptions Opts;

	// Layout: switchback ramp with runs SIDE BY SIDE in plan view (not stacked vertically).
	// Each segment offsets perpendicular (in X) so all runs have full headroom clearance.
	// Run direction alternates in Y; lateral position steps in X for each segment.

	const float LateralGap = Width + 30.0f; // 30cm gap between parallel runs for handrails (ADA 505.3)

	// Bottom landing
	{
		FTransform LandXf(FRotator::ZeroRotator,
			FVector(0.0f, -LandingLen * 0.5f, LandingThick * 0.5f),
			FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, LandXf, Width, LandingLen, LandingThick, 0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);
	}

	for (int32 Seg = 0; Seg < NumSegments; ++Seg)
	{
		float SegStartZ = RisePerSeg * Seg;
		float SegEndZ = SegStartZ + RisePerSeg;

		// Alternate direction: even segments go +Y, odd go -Y
		int32 Direction = (Seg % 2 == 0) ? 1 : -1;

		// Lateral offset: each segment shifts in +X
		float LateralX = Seg * LateralGap;

		// Y positions: all runs span the same Y range (0 to RunPerSeg)
		float SegStartY = (Direction > 0) ? 0.0f : RunPerSeg;
		float SegEndY = (Direction > 0) ? RunPerSeg : 0.0f;

		// Ramp surface: a tilted box
		float RampLen = FMath::Sqrt(FMath::Square(RunPerSeg) + FMath::Square(RisePerSeg));
		float Angle = FMath::Atan2(RisePerSeg, RunPerSeg);
		float AngleDeg = FMath::RadiansToDegrees(Angle);

		float PitchDeg = (Direction > 0) ? -AngleDeg : AngleDeg;

		FVector RampCenter(LateralX, RunPerSeg * 0.5f, (SegStartZ + SegEndZ) * 0.5f);
		FRotator RampRot(PitchDeg, (Direction > 0) ? 0.0f : 180.0f, 0.0f);
		FTransform RampXf(RampRot, RampCenter, FVector::OneVector);

		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, RampXf, Width, RampLen, RampThick, 0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);

		// Railings on both sides of the ramp
		if (RailHeight > 0.0f)
		{
			const float HalfW = Width * 0.5f;
			for (int32 Side = 0; Side < 2; ++Side)
			{
				float X = LateralX + ((Side == 0) ? -HalfW : HalfW);
				TArray<FVector> RailPath;
				RailPath.Add(FVector(X, SegStartY, SegStartZ + RampThick * 0.5f));
				RailPath.Add(FVector(X, SegEndY, SegEndZ + RampThick * 0.5f));

				BuildRailingGeometry(Mesh, RailPath, RailHeight, RailStyle,
					/*PostSpacing=*/100.0f, /*PostWidth=*/4.0f, /*RailWidth=*/5.0f,
					/*BarSpacing=*/12.0f, /*BarWidth=*/2.0f, /*PanelThick=*/3.0f,
					/*bClosedLoop=*/false);
			}
		}

		// 180-degree landing connecting this segment's end to the next segment's start
		if (Seg < NumSegments - 1)
		{
			// Landing spans laterally from this run's end X to next run's start X
			float ThisEndX = LateralX;
			float NextStartX = (Seg + 1) * LateralGap;
			float LandingCenterX = (ThisEndX + NextStartX) * 0.5f;
			float LandingSpanX = NextStartX - ThisEndX + Width; // spans both run widths + gap

			// Landing sits at the Y-end of the current segment
			float LandingY = SegEndY;
			float LandingZ = SegEndZ;

			FTransform LandXf(FRotator::ZeroRotator,
				FVector(LandingCenterX, LandingY, LandingZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, LandXf, LandingSpanX, LandingLen, LandingThick, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Center);

			// Landing railing on the far edge (perpendicular to run direction)
			if (RailHeight > 0.0f)
			{
				float LandZ = LandingZ + LandingThick * 0.5f;
				float FarY = LandingY + Direction * LandingLen * 0.5f;
				TArray<FVector> FrontRail;
				FrontRail.Add(FVector(LandingCenterX - LandingSpanX * 0.5f, FarY, LandZ));
				FrontRail.Add(FVector(LandingCenterX + LandingSpanX * 0.5f, FarY, LandZ));

				BuildRailingGeometry(Mesh, FrontRail, RailHeight, RailStyle,
					/*PostSpacing=*/100.0f, /*PostWidth=*/4.0f, /*RailWidth=*/5.0f,
					/*BarSpacing=*/12.0f, /*BarWidth=*/2.0f, /*PanelThick=*/3.0f,
					/*bClosedLoop=*/false);
			}
		}
	}

	// Top landing (at the end of the last segment)
	{
		int32 LastDir = ((NumSegments - 1) % 2 == 0) ? 1 : -1;
		float TopLandingX = (NumSegments - 1) * LateralGap;
		float TopLandingY = (LastDir > 0) ? RunPerSeg : 0.0f;
		float TopLandingZ = Rise;

		FTransform LandXf(FRotator::ZeroRotator,
			FVector(TopLandingX, TopLandingY, TopLandingZ),
			FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, LandXf, Width, LandingLen, LandingThick, 0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);
	}

	// Finalize
	FinalizeGeometry(Mesh);

	int32 TriCount = Mesh->GetTriangleCount();

	// Compute footprint: runs are side-by-side, not end-to-end
	float FootprintY = RunPerSeg + LandingLen; // single run length + landing overhang
	float FootprintX = (NumSegments > 1) ? (NumSegments - 1) * LateralGap + Width : Width;

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("type"), TEXT("ramp_connector"));
	Result->SetNumberField(TEXT("rise"), Rise);
	Result->SetNumberField(TEXT("run_per_segment"), RunPerSeg);
	Result->SetNumberField(TEXT("segments"), NumSegments);
	Result->SetNumberField(TEXT("slope_ratio"), SlopeRatio);
	Result->SetNumberField(TEXT("width"), Width);
	Result->SetNumberField(TEXT("lateral_gap"), LateralGap);
	Result->SetNumberField(TEXT("footprint_x"), FootprintX);
	Result->SetNumberField(TEXT("footprint_y"), FootprintY);
	Result->SetBoolField(TEXT("ada_compliant"), SlopeRatio <= (1.0f / 12.0f) + 0.001f);
	Result->SetNumberField(TEXT("triangle_count"), TriCount);

	// Emit wall openings when attachment context is provided (ramp door at top)
	if (AttachCtx.bValid)
	{
		TArray<FWallOpeningRequest> Openings;
		FWallOpeningRequest DoorOpening;
		DoorOpening.BuildingId = AttachCtx.BuildingId;
		DoorOpening.Wall = AttachCtx.Wall;
		DoorOpening.FloorIndex = AttachCtx.FloorIndex;
		DoorOpening.PositionAlongWall = AttachCtx.WallWidth * 0.5f; // centered
		DoorOpening.Width = 110.0f;    // 110cm for accessibility
		DoorOpening.Height = 230.0f;   // standard door
		DoorOpening.SillHeight = 0.0f;
		DoorOpening.Type = TEXT("door");
		DoorOpening.Purpose = TEXT("ramp_entry");
		Openings.Add(DoorOpening);
		EmitWallOpenings(Result, Openings);
	}

	FString FinalErr = SaveAndPlace(Mesh, Params, Result, AttachCtx, Width, FootprintY);
	if (!FinalErr.IsEmpty())
		return FMonolithActionResult::Error(FinalErr);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// create_railing
// ============================================================================

FMonolithActionResult FMonolithMeshArchFeatureActions::CreateRailing(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool) return FMonolithActionResult::Error(GS_ERROR_ARCH);

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));

	// Parse points array
	const TArray<TSharedPtr<FJsonValue>>* PointsArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("points"), PointsArr) || !PointsArr || PointsArr->Num() < 2)
		return FMonolithActionResult::Error(TEXT("Missing or invalid 'points' array (need at least 2 points as [x,y,z])"));

	TArray<FVector> Points;
	Points.Reserve(PointsArr->Num());
	for (int32 Pi = 0; Pi < PointsArr->Num(); ++Pi)
	{
		const TArray<TSharedPtr<FJsonValue>>* PtArr = nullptr;
		if (!(*PointsArr)[Pi]->TryGetArray(PtArr) || !PtArr || PtArr->Num() < 3)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Point %d must be an array of [x,y,z]"), Pi));
		}
		FVector Pt(
			(*PtArr)[0]->AsNumber(),
			(*PtArr)[1]->AsNumber(),
			(*PtArr)[2]->AsNumber()
		);
		Points.Add(Pt);
	}

	const float Height       = GetFloat(Params, TEXT("height"), 100.0f);
	const FString Style      = GetString(Params, TEXT("style"), TEXT("bars")).ToLower();
	const float PostSpacing  = GetFloat(Params, TEXT("post_spacing"), 120.0f);
	const float PostWidth    = GetFloat(Params, TEXT("post_width"), 4.0f);
	const float RailWidth    = GetFloat(Params, TEXT("rail_width"), 5.0f);
	const float BarSpacing   = GetFloat(Params, TEXT("bar_spacing"), 12.0f);
	const float BarWidth     = GetFloat(Params, TEXT("bar_width"), 2.0f);
	const float PanelThick   = GetFloat(Params, TEXT("panel_thickness"), 3.0f);
	const bool bClosedLoop   = GetBool(Params, TEXT("closed_loop"), false);

	if (Style != TEXT("simple") && Style != TEXT("bars") && Style != TEXT("solid"))
		return FMonolithActionResult::Error(FString::Printf(TEXT("Invalid style '%s'. Valid: simple, bars, solid"), *Style));

	// Parse attachment context (optional — for railing, only affects placement, no wall openings)
	FAttachmentContext AttachCtx = ParseBuildingContext(Params);

	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh) return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));

	BuildRailingGeometry(Mesh, Points, Height, Style, PostSpacing, PostWidth, RailWidth,
		BarSpacing, BarWidth, PanelThick, bClosedLoop);

	// Finalize
	FinalizeGeometry(Mesh);

	int32 TriCount = Mesh->GetTriangleCount();

	// Compute total path length
	float PathLen = 0.0f;
	for (int32 Pi = 1; Pi < Points.Num(); ++Pi)
	{
		PathLen += FVector::Dist(Points[Pi - 1], Points[Pi]);
	}
	if (bClosedLoop && Points.Num() > 1)
	{
		PathLen += FVector::Dist(Points.Last(), Points[0]);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("type"), TEXT("railing"));
	Result->SetStringField(TEXT("style"), Style);
	Result->SetNumberField(TEXT("point_count"), Points.Num());
	Result->SetNumberField(TEXT("path_length"), PathLen);
	Result->SetNumberField(TEXT("height"), Height);
	Result->SetBoolField(TEXT("closed_loop"), bClosedLoop);
	Result->SetNumberField(TEXT("triangle_count"), TriCount);

	// Railing has no wall openings — just pass attachment context for auto-placement
	FString FinalErr = SaveAndPlace(Mesh, Params, Result, AttachCtx, PathLen, 0.0f);
	if (!FinalErr.IsEmpty())
		return FMonolithActionResult::Error(FinalErr);

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_GEOMETRYSCRIPT
