#if WITH_GEOMETRYSCRIPT

#include "MonolithMeshFacadeActions.h"
#include "MonolithMeshProceduralActions.h"
#include "MonolithMeshHandlePool.h"
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
#include "GeometryScript/MeshUVFunctions.h"
#include "GeometryScript/MeshSelectionFunctions.h"
#include "GeometryScript/MeshModelingFunctions.h"

#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Editor.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

using namespace UE::Geometry;

static const FString GS_ERROR_FACADE = TEXT("Enable the GeometryScripting plugin in your .uproject to use facade generation.");

UMonolithMeshHandlePool* FMonolithMeshFacadeActions::Pool = nullptr;

void FMonolithMeshFacadeActions::SetHandlePool(UMonolithMeshHandlePool* InPool)
{
	Pool = InPool;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshFacadeActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("mesh"), TEXT("generate_facade"),
		TEXT("Generate a building facade with windows, doors, trim, and cornices from a Building Descriptor's exterior faces. "
			"CGA-style vertical split (base/shaft/cap) with even window placement. Returns facade mesh + element metadata."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshFacadeActions::GenerateFacade),
		FParamSchemaBuilder()
			.Required(TEXT("building_descriptor"), TEXT("object"), TEXT("Full Building Descriptor JSON from create_building_from_grid"))
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the facade mesh (e.g. /Game/CityBlock/Mesh/SM_Facade_01)"))
			.Optional(TEXT("style"), TEXT("string"), TEXT("Facade style name (loads from FacadeStyles/ presets)"), TEXT("colonial"))
			.Optional(TEXT("seed"), TEXT("integer"), TEXT("Random seed for variation"), TEXT("0"))
			.Optional(TEXT("window_width"), TEXT("number"), TEXT("Window width in cm (overrides style)"), TEXT("80"))
			.Optional(TEXT("window_height"), TEXT("number"), TEXT("Window height in cm (overrides style)"), TEXT("120"))
			.Optional(TEXT("sill_height"), TEXT("number"), TEXT("Height from floor to window sill in cm (overrides style)"), TEXT("90"))
			.Optional(TEXT("has_cornice"), TEXT("boolean"), TEXT("Add cornice at roofline"), TEXT("true"))
			.Optional(TEXT("ground_floor_style"), TEXT("string"), TEXT("Ground floor treatment: residential, storefront, entrance"), TEXT("residential"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x, y, z]"))
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Allow overwriting existing asset at save_path"), TEXT("false"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("list_facade_styles"),
		TEXT("List available facade style JSON presets from the FacadeStyles/ directory."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshFacadeActions::ListFacadeStyles),
		FParamSchemaBuilder().Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("apply_horror_damage"),
		TEXT("Apply procedural horror damage to a building facade: boarded windows, broken glass, cracks. "
			"Operates on an existing facade actor by generating damage overlay geometry."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshFacadeActions::ApplyHorrorDamage),
		FParamSchemaBuilder()
			.Required(TEXT("target_actor"), TEXT("string"), TEXT("Actor name of the facade to damage"))
			.Optional(TEXT("damage_level"), TEXT("number"), TEXT("0.0 (pristine) to 1.0 (destroyed)"), TEXT("0.5"))
			.Optional(TEXT("seed"), TEXT("integer"), TEXT("Random seed for deterministic damage"), TEXT("42"))
			.Optional(TEXT("boarded_windows"), TEXT("number"), TEXT("Fraction of windows to board up (0-1)"), TEXT("0.3"))
			.Optional(TEXT("broken_glass"), TEXT("number"), TEXT("Fraction of windows with broken glass geometry"), TEXT("0.2"))
			.Optional(TEXT("rust_stains"), TEXT("boolean"), TEXT("Add rust streak marker geometry below windows"), TEXT("true"))
			.Optional(TEXT("cracks"), TEXT("boolean"), TEXT("Add crack line geometry on wall surface"), TEXT("true"))
			.OptionalAssetPath(TEXT("save_path"), TEXT("Asset path for the damage overlay mesh"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Allow overwriting existing asset"), TEXT("false"))
			.Build());
}

// ============================================================================
// Facade Style Loading
// ============================================================================

FString FMonolithMeshFacadeActions::GetFacadeStylesDir()
{
	return FPaths::Combine(FPaths::ProjectPluginsDir(), TEXT("Monolith"), TEXT("Saved"), TEXT("Monolith"), TEXT("FacadeStyles"));
}

bool FMonolithMeshFacadeActions::LoadFacadeStyle(const FString& StyleName, FFacadeStyle& OutStyle)
{
	FString FilePath = FPaths::Combine(GetFacadeStylesDir(), StyleName + TEXT(".json"));

	FString JsonStr;
	if (!FFileHelper::LoadFileToString(JsonStr, *FilePath))
	{
		return false;
	}

	TSharedPtr<FJsonObject> Json;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonStr);
	if (!FJsonSerializer::Deserialize(Reader, Json) || !Json.IsValid())
	{
		return false;
	}

	OutStyle.Name = StyleName;
	Json->TryGetStringField(TEXT("description"), OutStyle.Description);

	// Window
	const TSharedPtr<FJsonObject>* WinObj = nullptr;
	if (Json->TryGetObjectField(TEXT("window"), WinObj) && WinObj && (*WinObj).IsValid())
	{
		auto& W = *(*WinObj);
		if (W.HasField(TEXT("width")))       OutStyle.WindowWidth = static_cast<float>(W.GetNumberField(TEXT("width")));
		if (W.HasField(TEXT("height")))      OutStyle.WindowHeight = static_cast<float>(W.GetNumberField(TEXT("height")));
		if (W.HasField(TEXT("frame_width"))) OutStyle.FrameWidth = static_cast<float>(W.GetNumberField(TEXT("frame_width")));
		if (W.HasField(TEXT("frame_depth"))) OutStyle.FrameDepth = static_cast<float>(W.GetNumberField(TEXT("frame_depth")));
		if (W.HasField(TEXT("sill_depth")))  OutStyle.SillDepth = static_cast<float>(W.GetNumberField(TEXT("sill_depth")));
		if (W.HasField(TEXT("sill_height"))) OutStyle.SillHeight = static_cast<float>(W.GetNumberField(TEXT("sill_height")));
		if (W.HasField(TEXT("lintel_height"))) OutStyle.LintelHeight = static_cast<float>(W.GetNumberField(TEXT("lintel_height")));
		if (W.HasField(TEXT("arch")))        OutStyle.bArch = W.GetBoolField(TEXT("arch"));
	}

	// Trim
	const TSharedPtr<FJsonObject>* TrimObj = nullptr;
	if (Json->TryGetObjectField(TEXT("trim"), TrimObj) && TrimObj && (*TrimObj).IsValid())
	{
		auto& T = *(*TrimObj);
		if (T.HasField(TEXT("corner_width")))       OutStyle.CornerWidth = static_cast<float>(T.GetNumberField(TEXT("corner_width")));
		if (T.HasField(TEXT("corner_depth")))        OutStyle.CornerDepth = static_cast<float>(T.GetNumberField(TEXT("corner_depth")));
		if (T.HasField(TEXT("belt_course_height")))  OutStyle.BeltCourseHeight = static_cast<float>(T.GetNumberField(TEXT("belt_course_height")));
		if (T.HasField(TEXT("belt_course_depth")))   OutStyle.BeltCourseDepth = static_cast<float>(T.GetNumberField(TEXT("belt_course_depth")));
	}

	// Cornice
	const TSharedPtr<FJsonObject>* CorniceObj = nullptr;
	if (Json->TryGetObjectField(TEXT("cornice"), CorniceObj) && CorniceObj && (*CorniceObj).IsValid())
	{
		auto& C = *(*CorniceObj);
		if (C.HasField(TEXT("height")))  OutStyle.CorniceHeight = static_cast<float>(C.GetNumberField(TEXT("height")));
		if (C.HasField(TEXT("depth")))   OutStyle.CorniceDepth = static_cast<float>(C.GetNumberField(TEXT("depth")));
		C.TryGetStringField(TEXT("profile"), OutStyle.CorniceProfile);
	}

	// Ground floor
	const TSharedPtr<FJsonObject>* GfObj = nullptr;
	if (Json->TryGetObjectField(TEXT("ground_floor"), GfObj) && GfObj && (*GfObj).IsValid())
	{
		auto& G = *(*GfObj);
		if (G.HasField(TEXT("height_multiplier"))) OutStyle.GroundFloorHeightMultiplier = static_cast<float>(G.GetNumberField(TEXT("height_multiplier")));
		if (G.HasField(TEXT("storefront_depth")))  OutStyle.StorefrontDepth = static_cast<float>(G.GetNumberField(TEXT("storefront_depth")));
		if (G.HasField(TEXT("door_width")))         OutStyle.DoorWidth = static_cast<float>(G.GetNumberField(TEXT("door_width")));
		if (G.HasField(TEXT("door_height")))        OutStyle.DoorHeight = static_cast<float>(G.GetNumberField(TEXT("door_height")));
	}

	// Material slots
	const TSharedPtr<FJsonObject>* MatObj = nullptr;
	if (Json->TryGetObjectField(TEXT("material_slots"), MatObj) && MatObj && (*MatObj).IsValid())
	{
		auto& M = *(*MatObj);
		if (M.HasField(TEXT("wall")))          OutStyle.WallMaterialId = static_cast<int32>(M.GetNumberField(TEXT("wall")));
		if (M.HasField(TEXT("trim")))          OutStyle.TrimMaterialId = static_cast<int32>(M.GetNumberField(TEXT("trim")));
		if (M.HasField(TEXT("window_frame")))  OutStyle.WindowFrameMaterialId = static_cast<int32>(M.GetNumberField(TEXT("window_frame")));
		if (M.HasField(TEXT("cornice")))       OutStyle.CorniceMaterialId = static_cast<int32>(M.GetNumberField(TEXT("cornice")));
		if (M.HasField(TEXT("glass")))         OutStyle.GlassMaterialId = static_cast<int32>(M.GetNumberField(TEXT("glass")));
		if (M.HasField(TEXT("door")))          OutStyle.DoorMaterialId = static_cast<int32>(M.GetNumberField(TEXT("door")));
	}

	return true;
}

// ============================================================================
// Coordinate Helpers
// ============================================================================

FVector FMonolithMeshFacadeActions::GetFaceWidthAxis(const FExteriorFaceDef& Face)
{
	// The width axis is perpendicular to the normal in the XY plane
	// For north-facing (normal 0,-1,0) -> width axis is (1,0,0)
	// For south-facing (normal 0,1,0)  -> width axis is (-1,0,0)
	// For east-facing  (normal 1,0,0)  -> width axis is (0,1,0)
	// For west-facing  (normal -1,0,0) -> width axis is (0,-1,0)
	FVector N = Face.Normal.GetSafeNormal();
	FVector Up(0.0f, 0.0f, 1.0f);
	FVector WidthAxis = FVector::CrossProduct(Up, N).GetSafeNormal();

	// If normal is vertical (unlikely for walls but safe), fall back
	if (WidthAxis.IsNearlyZero())
	{
		WidthAxis = FVector(1.0f, 0.0f, 0.0f);
	}

	return WidthAxis;
}

FTransform FMonolithMeshFacadeActions::ComputeFaceTransform(const FExteriorFaceDef& Face)
{
	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Up(0.0f, 0.0f, 1.0f);
	FVector Normal = Face.Normal.GetSafeNormal();

	// Build rotation from axes: X = width axis, Y = normal (outward), Z = up
	FMatrix RotMat = FMatrix::Identity;
	RotMat.SetAxis(0, WidthAxis);
	RotMat.SetAxis(1, Normal);
	RotMat.SetAxis(2, Up);

	return FTransform(RotMat.Rotator(), Face.WorldOrigin);
}

// ============================================================================
// Window Placement Algorithm
// ============================================================================

TArray<float> FMonolithMeshFacadeActions::ComputeWindowPositions(
	float WallWidth, float WindowWidth, float Margin, float MinSpacing)
{
	TArray<float> Positions;

	float Available = WallWidth - 2.0f * Margin;
	if (Available <= 0.0f || WindowWidth <= 0.0f)
	{
		return Positions;
	}

	// Max windows that fit with minimum spacing
	int32 N = FMath::FloorToInt32((Available + MinSpacing) / (WindowWidth + MinSpacing));
	N = FMath::Max(N, 0);

	if (N == 0) return Positions;

	float TotalWindowWidth = N * WindowWidth;
	float TotalGap = Available - TotalWindowWidth;
	float Gap = TotalGap / static_cast<float>(N + 1);

	Positions.Reserve(N);
	for (int32 i = 0; i < N; ++i)
	{
		// Position relative to wall center (-WallWidth/2 to +WallWidth/2)
		float X = -WallWidth / 2.0f + Margin + Gap + static_cast<float>(i) * (WindowWidth + Gap) + WindowWidth / 2.0f;
		Positions.Add(X);
	}

	return Positions;
}

// ============================================================================
// Geometry Builders
// ============================================================================

void FMonolithMeshFacadeActions::BuildWallSlab(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, float WallThickness, int32 MaterialId)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	Opts.bFlipOrientation = false;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();

	// Wall straddles the grid boundary (no Normal offset).
	// WorldOrigin is at the grid line; the wall extends WallThickness/2 on each side.
	FVector Center = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	// Determine box dimensions based on face orientation
	// AppendBox takes (DimX, DimY, DimZ) in world-aligned coords
	float BoxX, BoxY;
	if (FMath::Abs(Normal.X) > FMath::Abs(Normal.Y))
	{
		// East/West facing: thin in X, wide in Y
		BoxX = WallThickness;
		BoxY = Face.Width;
	}
	else
	{
		// North/South facing: wide in X, thin in Y
		BoxX = Face.Width;
		BoxY = WallThickness;
	}

	FTransform WallXf(FRotator::ZeroRotator, FVector(Center.X, Center.Y, Face.WorldOrigin.Z), FVector::OneVector);

	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
		Mesh, Opts, WallXf,
		BoxX, BoxY, Face.Height,
		0, 0, 0,
		EGeometryScriptPrimitiveOriginMode::Base);
}

void FMonolithMeshFacadeActions::CutOpenings(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, const TArray<FWindowPlacement>& Windows,
	const TArray<FDoorPlacement>& Doors, float WallThickness, bool& bHadBooleans)
{
	if (Windows.Num() == 0 && Doors.Num() == 0) return;

	// Merge all cutters into one mesh for a single boolean op (optimization)
	UDynamicMesh* AllCutters = NewObject<UDynamicMesh>(Pool);
	FGeometryScriptPrimitiveOptions Opts;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	// Cutter depth: thicker than wall + 0.5cm inset on each side to avoid coplanar
	float CutterDepth = WallThickness + 10.0f;

	for (const FWindowPlacement& Win : Windows)
	{
		// CenterX is relative to face center along width axis
		FVector WinCenter = FaceCenter + WidthAxis * Win.CenterX;
		WinCenter.Z = Face.WorldOrigin.Z + Win.SillZ;

		float CutW, CutD;
		if (FMath::Abs(Normal.X) > FMath::Abs(Normal.Y))
		{
			CutW = CutterDepth;
			CutD = Win.Width - 1.0f; // 0.5cm inset on each side
		}
		else
		{
			CutW = Win.Width - 1.0f;
			CutD = CutterDepth;
		}

		FTransform CutXf(FRotator::ZeroRotator, WinCenter, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			AllCutters, Opts, CutXf,
			CutW, CutD, Win.Height - 1.0f, // 0.5cm inset top/bottom
			0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Base);
	}

	for (const FDoorPlacement& Door : Doors)
	{
		FVector DoorCenter = FaceCenter + WidthAxis * Door.CenterX;
		DoorCenter.Z = Face.WorldOrigin.Z;

		float CutW, CutD;
		if (FMath::Abs(Normal.X) > FMath::Abs(Normal.Y))
		{
			CutW = CutterDepth;
			CutD = Door.Width - 1.0f;
		}
		else
		{
			CutW = Door.Width - 1.0f;
			CutD = CutterDepth;
		}

		FTransform CutXf(FRotator::ZeroRotator, DoorCenter, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			AllCutters, Opts, CutXf,
			CutW, CutD, Door.Height - 0.5f,
			0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Base);
	}

	if (AllCutters->GetTriangleCount() > 0)
	{
		FGeometryScriptMeshBooleanOptions BoolOpts;
		UGeometryScriptLibrary_MeshBooleanFunctions::ApplyMeshBoolean(
			Mesh, FTransform::Identity, AllCutters, FTransform::Identity,
			EGeometryScriptBooleanOperation::Subtract, BoolOpts);
		bHadBooleans = true;
	}
}

// ============================================================================
// Selection+Inset Window Cutting — v3 Boolean Replacement
// ============================================================================

void FMonolithMeshFacadeActions::CutOpeningsSelectionInset(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, const TArray<FWindowPlacement>& Windows,
	const TArray<FDoorPlacement>& Doors, float WallThickness, float FrameWidth,
	bool bUseSelectionInset, bool& bHadBooleans)
{
	if (Windows.Num() == 0 && Doors.Num() == 0)
	{
		// No openings — just build a solid wall slab on the main mesh
		BuildWallSlab(Mesh, Face, WallThickness, 0);
		return;
	}

	// Fallback to boolean subtract — isolate wall in temp mesh for clean boolean
	if (!bUseSelectionInset)
	{
		UDynamicMesh* WallMesh = NewObject<UDynamicMesh>(GetTransientPackage());
		BuildWallSlab(WallMesh, Face, WallThickness, 0);
		CutOpenings(WallMesh, Face, Windows, Doors, WallThickness, bHadBooleans);
		// Append the cleanly-cut wall to the main mesh
		UGeometryScriptLibrary_MeshBasicEditFunctions::AppendMesh(
			Mesh, WallMesh, FTransform::Identity, true);
		WallMesh->MarkAsGarbage(); // Ensure GC cleanup
		return;
	}

	// ---- CRITICAL: Build wall slab in an ISOLATED temp mesh ----
	// PlaneSlice operates on ALL geometry in a mesh. Since the main building mesh
	// already contains interior walls, floors, stairs, etc., we must isolate the
	// wall slab so plane cuts only subdivide THIS wall, not the whole building.
	// After all cuts + insets + deletions, AppendMesh merges it into the main mesh.
	UDynamicMesh* WallMesh = NewObject<UDynamicMesh>(Pool);

	BuildWallSlab(WallMesh, Face, WallThickness, 0);

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);
	bool bNorthSouth = FMath::Abs(Normal.Y) > FMath::Abs(Normal.X);
	FVector WallCenter = FaceCenter + Normal * (WallThickness * 0.5f);

	// ---- Step 0: Pre-subdivide wall with PlaneSlice at opening boundaries ----
	// AppendBox with 0 subdivisions produces 12 tris (2 per face).
	// SelectMeshElementsInBox CANNOT isolate a window sub-region from a 2-tri face.
	// PlaneSlice inserts edge loops at cut boundaries, creating the face subdivisions
	// needed for Selection+Inset to target specific window regions.

	FGeometryScriptMeshPlaneSliceOptions SliceOpts;
	SliceOpts.bFillHoles = false;
	SliceOpts.bFillSpans = false;

	// Collect all cut lines from openings
	TArray<float> VerticalCuts;
	TArray<float> HorizontalCuts;

	auto AddOpeningCuts = [&](float CenterX, float Width, float BottomZ, float Height)
	{
		VerticalCuts.AddUnique(CenterX - Width * 0.5f);
		VerticalCuts.AddUnique(CenterX + Width * 0.5f);
		// Don't slice at exact wall base (Z=0) — produces degenerate zero-height triangles
		if (BottomZ > KINDA_SMALL_NUMBER)
		{
			HorizontalCuts.AddUnique(BottomZ);
		}
		HorizontalCuts.AddUnique(BottomZ + Height);
	};

	for (const FWindowPlacement& Win : Windows)
	{
		AddOpeningCuts(Win.CenterX, Win.Width, Win.SillZ, Win.Height);
	}
	for (const FDoorPlacement& Door : Doors)
	{
		AddOpeningCuts(Door.CenterX, Door.Width, 0.0f, Door.Height);
	}

	// Helper: build a CutFrame where the Z axis = PlaneNormal, located at CutPoint
	auto MakeCutFrame = [](const FVector& CutPoint, const FVector& PlaneNormal) -> FTransform
	{
		// Build rotation that aligns Z with PlaneNormal
		FQuat Rot = FQuat::FindBetweenNormals(FVector::UpVector, PlaneNormal);
		return FTransform(Rot, CutPoint);
	};

	// Vertical plane cuts (perpendicular to wall width axis)
	for (float CutX : VerticalCuts)
	{
		FVector CutPoint = FaceCenter + WidthAxis * CutX;
		CutPoint.Z = Face.WorldOrigin.Z + Face.Height * 0.5f;

		UGeometryScriptLibrary_MeshBooleanFunctions::ApplyMeshPlaneSlice(
			WallMesh, MakeCutFrame(CutPoint, WidthAxis), SliceOpts);
	}

	// Horizontal plane cuts
	for (float CutZ : HorizontalCuts)
	{
		FVector CutPoint = WallCenter;
		CutPoint.Z = Face.WorldOrigin.Z + CutZ;

		UGeometryScriptLibrary_MeshBooleanFunctions::ApplyMeshPlaneSlice(
			WallMesh, MakeCutFrame(CutPoint, FVector::UpVector), SliceOpts);
	}

	// ---- Step 1: For each opening, select + inset + delete ----
	auto CutOneOpening = [&](float CenterX, float Width, float BottomZ, float Height)
	{
		float HalfW = Width * 0.5f;
		FVector OpeningCenter = FaceCenter + WidthAxis * CenterX;

		// Build selection box tightly around the opening region of the wall
		FVector BoxMin, BoxMax;
		if (bNorthSouth)
		{
			BoxMin = FVector(
				OpeningCenter.X - HalfW - 0.5f,
				WallCenter.Y - WallThickness,
				Face.WorldOrigin.Z + BottomZ - 0.5f);
			BoxMax = FVector(
				OpeningCenter.X + HalfW + 0.5f,
				WallCenter.Y + WallThickness,
				Face.WorldOrigin.Z + BottomZ + Height + 0.5f);
		}
		else
		{
			BoxMin = FVector(
				WallCenter.X - WallThickness,
				OpeningCenter.Y - HalfW - 0.5f,
				Face.WorldOrigin.Z + BottomZ - 0.5f);
			BoxMax = FVector(
				WallCenter.X + WallThickness,
				OpeningCenter.Y + HalfW + 0.5f,
				Face.WorldOrigin.Z + BottomZ + Height + 0.5f);
		}
		FBox WindowBox(BoxMin, BoxMax);

		// Select outward-facing tris in window region
		FGeometryScriptMeshSelection BoxSel;
		UGeometryScriptLibrary_MeshSelectionFunctions::SelectMeshElementsInBox(
			WallMesh, BoxSel, WindowBox,
			EGeometryScriptMeshSelectionType::Triangles, false, 2);

		FGeometryScriptMeshSelection NormSel;
		UGeometryScriptLibrary_MeshSelectionFunctions::SelectMeshElementsByNormalAngle(
			WallMesh, NormSel, Normal, 30.0,
			EGeometryScriptMeshSelectionType::Triangles, false, 1);

		FGeometryScriptMeshSelection FrontSel;
		UGeometryScriptLibrary_MeshSelectionFunctions::CombineMeshSelections(
			BoxSel, NormSel, FrontSel,
			EGeometryScriptCombineSelectionMode::Intersection);

		// CRITICAL: Guard against empty selection — InsetOutsetFaces with empty selection
		// insets ALL mesh triangles, which crashes GeometryCore with array index out of bounds.
		// Empty selection can happen when plane slicing at wall boundaries produces degenerate
		// triangles with unpredictable normals, or floating-point precision misses vertices.
		if (FrontSel.GetNumSelected() == 0)
		{
			UE_LOG(LogTemp, Warning, TEXT("CutOpeningsSelectionInset: Empty selection for opening — skipping (likely degenerate geometry from plane slice)"));
			return;
		}

		// Inset to create frame border geometry
		FGeometryScriptMeshInsetOutsetFacesOptions InsetOpts;
		InsetOpts.Distance = FrameWidth;
		InsetOpts.bReproject = true;
		InsetOpts.bBoundaryOnly = false;
		InsetOpts.Softness = 0.0f;

		UGeometryScriptLibrary_MeshModelingFunctions::ApplyMeshInsetOutsetFaces(
			WallMesh, InsetOpts, FrontSel);

		// Select INNER faces (shrunk by inset distance) for deletion
		float ShrinkDist = FrameWidth + 0.5f;
		FBox ShrunkBox = WindowBox.ExpandBy(-ShrinkDist);

		// Delete front-facing inner faces
		FGeometryScriptMeshSelection InnerBoxSel;
		UGeometryScriptLibrary_MeshSelectionFunctions::SelectMeshElementsInBox(
			WallMesh, InnerBoxSel, ShrunkBox,
			EGeometryScriptMeshSelectionType::Triangles, false, 3);

		FGeometryScriptMeshSelection InnerNormSel;
		UGeometryScriptLibrary_MeshSelectionFunctions::SelectMeshElementsByNormalAngle(
			WallMesh, InnerNormSel, Normal, 30.0,
			EGeometryScriptMeshSelectionType::Triangles, false, 1);

		FGeometryScriptMeshSelection DeleteFrontSel;
		UGeometryScriptLibrary_MeshSelectionFunctions::CombineMeshSelections(
			InnerBoxSel, InnerNormSel, DeleteFrontSel,
			EGeometryScriptCombineSelectionMode::Intersection);

		int32 NumFrontDeleted = 0;
		UGeometryScriptLibrary_MeshBasicEditFunctions::DeleteSelectedTrianglesFromMesh(
			WallMesh, DeleteFrontSel, NumFrontDeleted);

		// Delete back-facing inner faces (punch fully through the wall)
		FGeometryScriptMeshSelection InnerBoxSel2;
		UGeometryScriptLibrary_MeshSelectionFunctions::SelectMeshElementsInBox(
			WallMesh, InnerBoxSel2, ShrunkBox,
			EGeometryScriptMeshSelectionType::Triangles, false, 3);

		FGeometryScriptMeshSelection BackNormSel;
		UGeometryScriptLibrary_MeshSelectionFunctions::SelectMeshElementsByNormalAngle(
			WallMesh, BackNormSel, -Normal, 30.0,
			EGeometryScriptMeshSelectionType::Triangles, false, 1);

		FGeometryScriptMeshSelection DeleteBackSel;
		UGeometryScriptLibrary_MeshSelectionFunctions::CombineMeshSelections(
			InnerBoxSel2, BackNormSel, DeleteBackSel,
			EGeometryScriptCombineSelectionMode::Intersection);

		int32 NumBackDeleted = 0;
		UGeometryScriptLibrary_MeshBasicEditFunctions::DeleteSelectedTrianglesFromMesh(
			WallMesh, DeleteBackSel, NumBackDeleted);
	};

	// Process all openings
	for (const FWindowPlacement& Win : Windows)
	{
		CutOneOpening(Win.CenterX, Win.Width, Win.SillZ, Win.Height);
	}
	for (const FDoorPlacement& Door : Doors)
	{
		CutOneOpening(Door.CenterX, Door.Width, 0.0f, Door.Height);
	}

	// Merge the processed wall into the main building mesh
	UGeometryScriptLibrary_MeshBasicEditFunctions::AppendMesh(
		Mesh, WallMesh, FTransform::Identity);
}

void FMonolithMeshFacadeActions::AddWindowFrames(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, const TArray<FWindowPlacement>& Windows,
	const FFacadeStyle& Style, float WallThickness)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	float FW = Style.FrameWidth;
	float FD = Style.FrameDepth;

	for (const FWindowPlacement& Win : Windows)
	{
		FVector WinCenter = FaceCenter + WidthAxis * Win.CenterX;
		float WinBaseZ = Face.WorldOrigin.Z + Win.SillZ;

		// Frame sits on the wall surface (offset outward by normal)
		FVector FrameOrigin = WinCenter + Normal * WallThickness;

		bool bNorthSouth = FMath::Abs(Normal.Y) > FMath::Abs(Normal.X);

		// Left jamb
		{
			FVector Pos = FrameOrigin + WidthAxis * (-Win.Width * 0.5f - FW * 0.5f);
			Pos.Z = WinBaseZ;
			float JambW = bNorthSouth ? FW : FD;
			float JambD = bNorthSouth ? FD : FW;
			FTransform Xf(FRotator::ZeroRotator, Pos, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, Xf, JambW, JambD, Win.Height + FW * 2.0f, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}

		// Right jamb
		{
			FVector Pos = FrameOrigin + WidthAxis * (Win.Width * 0.5f + FW * 0.5f);
			Pos.Z = WinBaseZ;
			float JambW = bNorthSouth ? FW : FD;
			float JambD = bNorthSouth ? FD : FW;
			FTransform Xf(FRotator::ZeroRotator, Pos, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, Xf, JambW, JambD, Win.Height + FW * 2.0f, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}

		// Lintel (top)
		{
			FVector Pos = FrameOrigin;
			Pos.Z = WinBaseZ + Win.Height;
			float LintelW = bNorthSouth ? (Win.Width + FW * 2.0f) : FD;
			float LintelD = bNorthSouth ? FD : (Win.Width + FW * 2.0f);
			FTransform Xf(FRotator::ZeroRotator, Pos, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, Xf, LintelW, LintelD, Style.LintelHeight, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}

		// Sill (bottom, projects outward)
		{
			FVector Pos = FrameOrigin + Normal * (Style.SillDepth * 0.5f);
			Pos.Z = WinBaseZ - 4.0f; // sill sits just below window
			float SillExtension = 4.0f; // extends past frame on each side
			float SillW, SillD;
			if (bNorthSouth)
			{
				SillW = Win.Width + FW * 2.0f + SillExtension * 2.0f;
				SillD = FD + Style.SillDepth;
			}
			else
			{
				SillW = FD + Style.SillDepth;
				SillD = Win.Width + FW * 2.0f + SillExtension * 2.0f;
			}
			FTransform Xf(FRotator::ZeroRotator, Pos, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, Xf, SillW, SillD, 4.0f, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}
	}
}

void FMonolithMeshFacadeActions::AddDoorFrames(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, const TArray<FDoorPlacement>& Doors,
	const FFacadeStyle& Style, float WallThickness)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	float FW = Style.FrameWidth;
	float FD = Style.FrameDepth;
	bool bNorthSouth = FMath::Abs(Normal.Y) > FMath::Abs(Normal.X);

	for (const FDoorPlacement& Door : Doors)
	{
		FVector DoorCenter = FaceCenter + WidthAxis * Door.CenterX;
		FVector FrameOrigin = DoorCenter + Normal * WallThickness;
		float DoorBaseZ = Face.WorldOrigin.Z;

		// Left jamb
		{
			FVector Pos = FrameOrigin + WidthAxis * (-Door.Width * 0.5f - FW * 0.5f);
			Pos.Z = DoorBaseZ;
			float JambW = bNorthSouth ? FW : FD;
			float JambD = bNorthSouth ? FD : FW;
			FTransform Xf(FRotator::ZeroRotator, Pos, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, Xf, JambW, JambD, Door.Height, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}

		// Right jamb
		{
			FVector Pos = FrameOrigin + WidthAxis * (Door.Width * 0.5f + FW * 0.5f);
			Pos.Z = DoorBaseZ;
			float JambW = bNorthSouth ? FW : FD;
			float JambD = bNorthSouth ? FD : FW;
			FTransform Xf(FRotator::ZeroRotator, Pos, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, Xf, JambW, JambD, Door.Height, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}

		// Header
		{
			FVector Pos = FrameOrigin;
			Pos.Z = DoorBaseZ + Door.Height;
			float HeaderW = bNorthSouth ? (Door.Width + FW * 2.0f) : FD;
			float HeaderD = bNorthSouth ? FD : (Door.Width + FW * 2.0f);
			FTransform Xf(FRotator::ZeroRotator, Pos, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, Xf, HeaderW, HeaderD, Style.LintelHeight, 0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}
	}
}

void FMonolithMeshFacadeActions::AddCornice(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, float TotalBuildingHeight, const FFacadeStyle& Style)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	bool bNorthSouth = FMath::Abs(Normal.Y) > FMath::Abs(Normal.X);

	// Main cornice body: projects outward from wall top
	FVector CornicePos = FaceCenter + Normal * (Style.CorniceDepth * 0.5f);
	CornicePos.Z = Face.WorldOrigin.Z + TotalBuildingHeight;

	float CornW, CornD;
	if (bNorthSouth)
	{
		CornW = Face.Width + 4.0f; // slight overhang at corners
		CornD = Style.CorniceDepth;
	}
	else
	{
		CornW = Style.CorniceDepth;
		CornD = Face.Width + 4.0f;
	}

	FTransform CornXf(FRotator::ZeroRotator, CornicePos, FVector::OneVector);
	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
		Mesh, Opts, CornXf,
		CornW, CornD, Style.CorniceHeight,
		0, 0, 0,
		EGeometryScriptPrimitiveOriginMode::Base);

	// Soffit (underside projection strip, thinner)
	float SoffitThick = 3.0f;
	FVector SoffitPos = FaceCenter + Normal * (Style.CorniceDepth * 0.75f);
	SoffitPos.Z = Face.WorldOrigin.Z + TotalBuildingHeight - SoffitThick;

	float SoftW, SoftD;
	if (bNorthSouth)
	{
		SoftW = Face.Width;
		SoftD = Style.CorniceDepth * 0.5f;
	}
	else
	{
		SoftW = Style.CorniceDepth * 0.5f;
		SoftD = Face.Width;
	}

	FTransform SoftXf(FRotator::ZeroRotator, SoffitPos, FVector::OneVector);
	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
		Mesh, Opts, SoftXf,
		SoftW, SoftD, SoffitThick,
		0, 0, 0,
		EGeometryScriptPrimitiveOriginMode::Base);
}

void FMonolithMeshFacadeActions::AddBeltCourse(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, float CourseZ, const FFacadeStyle& Style)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	bool bNorthSouth = FMath::Abs(Normal.Y) > FMath::Abs(Normal.X);

	FVector BeltPos = FaceCenter + Normal * (Style.BeltCourseDepth * 0.5f);
	BeltPos.Z = Face.WorldOrigin.Z + CourseZ;

	float BeltW, BeltD;
	if (bNorthSouth)
	{
		BeltW = Face.Width;
		BeltD = Style.BeltCourseDepth;
	}
	else
	{
		BeltW = Style.BeltCourseDepth;
		BeltD = Face.Width;
	}

	FTransform BeltXf(FRotator::ZeroRotator, BeltPos, FVector::OneVector);
	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
		Mesh, Opts, BeltXf,
		BeltW, BeltD, Style.BeltCourseHeight,
		0, 0, 0,
		EGeometryScriptPrimitiveOriginMode::Base);
}

void FMonolithMeshFacadeActions::AddGlassPanes(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, const TArray<FWindowPlacement>& Windows,
	int32 GlassMaterialId)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	bool bNorthSouth = FMath::Abs(Normal.Y) > FMath::Abs(Normal.X);

	for (const FWindowPlacement& Win : Windows)
	{
		FVector PaneCenter = FaceCenter + WidthAxis * Win.CenterX;
		PaneCenter.Z = Face.WorldOrigin.Z + Win.SillZ;

		// Glass pane: very thin, sits at wall center plane
		float PaneW, PaneD;
		if (bNorthSouth)
		{
			PaneW = Win.Width - 2.0f;
			PaneD = 1.0f; // 1cm thick glass
		}
		else
		{
			PaneW = 1.0f;
			PaneD = Win.Width - 2.0f;
		}

		FTransform PaneXf(FRotator::ZeroRotator, PaneCenter, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, PaneXf,
			PaneW, PaneD, Win.Height - 2.0f,
			0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Base);
	}
}

// ============================================================================
// Horror Damage Builders
// ============================================================================

void FMonolithMeshFacadeActions::AddBoardedWindows(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, const TArray<FWindowPlacement>& Windows,
	const TArray<int32>& WindowIndices, int32 Seed)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	bool bNorthSouth = FMath::Abs(Normal.Y) > FMath::Abs(Normal.X);

	const float BoardHeight = 18.0f;     // standard plank width
	const float BoardThickness = 2.5f;   // plank depth
	const float BoardGap = 3.0f;         // gap between planks

	for (int32 WinIdx : WindowIndices)
	{
		if (!Windows.IsValidIndex(WinIdx)) continue;
		const FWindowPlacement& Win = Windows[WinIdx];

		FVector WinCenter = FaceCenter + WidthAxis * Win.CenterX + Normal * (Face.Width > 0 ? 0.5f : -0.5f);

		// Number of boards to cover the window
		int32 NumBoards = FMath::CeilToInt32(Win.Height / (BoardHeight + BoardGap));
		FRandomStream Rng(Seed + WinIdx * 137);

		for (int32 b = 0; b < NumBoards; ++b)
		{
			float BoardZ = Face.WorldOrigin.Z + Win.SillZ + static_cast<float>(b) * (BoardHeight + BoardGap) + BoardHeight * 0.5f;
			if (BoardZ > Face.WorldOrigin.Z + Win.SillZ + Win.Height) break;

			// Slight random offset and rotation for realism
			float OffsetX = Rng.FRandRange(-3.0f, 3.0f);
			float RotAngle = Rng.FRandRange(-3.0f, 3.0f); // degrees

			FVector BoardPos = WinCenter + WidthAxis * OffsetX + Normal * BoardThickness;
			BoardPos.Z = BoardZ;

			float PlankW, PlankD;
			if (bNorthSouth)
			{
				PlankW = Win.Width + 8.0f; // slightly wider than window
				PlankD = BoardThickness;
			}
			else
			{
				PlankW = BoardThickness;
				PlankD = Win.Width + 8.0f;
			}

			// Rotation around the normal axis
			FRotator BoardRot = FRotator::ZeroRotator;
			if (bNorthSouth)
			{
				BoardRot.Roll = RotAngle;
			}
			else
			{
				BoardRot.Pitch = RotAngle;
			}

			FTransform BoardXf(BoardRot, BoardPos, FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, BoardXf,
				PlankW, PlankD, BoardHeight,
				0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Center);
		}
	}
}

void FMonolithMeshFacadeActions::AddCrackGeometry(UDynamicMesh* Mesh,
	const FExteriorFaceDef& Face, float DamageLevel, int32 Seed)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;

	FVector WidthAxis = GetFaceWidthAxis(Face);
	FVector Normal = Face.Normal.GetSafeNormal();
	FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

	bool bNorthSouth = FMath::Abs(Normal.Y) > FMath::Abs(Normal.X);

	// Number of cracks scales with damage level
	int32 NumCracks = FMath::Clamp(FMath::RoundToInt32(DamageLevel * 8.0f), 1, 12);
	FRandomStream Rng(Seed + 7919);

	for (int32 i = 0; i < NumCracks; ++i)
	{
		// Random position on wall face
		float RelX = Rng.FRandRange(-Face.Width * 0.4f, Face.Width * 0.4f);
		float RelZ = Rng.FRandRange(Face.Height * 0.1f, Face.Height * 0.85f);

		FVector CrackPos = FaceCenter + WidthAxis * RelX + Normal * 0.5f;
		CrackPos.Z = Face.WorldOrigin.Z + RelZ;

		// Crack: thin wedge on the wall surface
		float CrackLength = Rng.FRandRange(30.0f, 120.0f) * DamageLevel;
		float CrackWidth = Rng.FRandRange(0.5f, 2.0f);
		float CrackDepth = 1.0f;

		float Angle = Rng.FRandRange(-45.0f, 45.0f);
		FRotator CrackRot = FRotator::ZeroRotator;

		float CrW, CrD;
		if (bNorthSouth)
		{
			CrW = CrackLength;
			CrD = CrackDepth;
			CrackRot.Roll = Angle;
		}
		else
		{
			CrW = CrackDepth;
			CrD = CrackLength;
			CrackRot.Pitch = Angle;
		}

		FTransform CrackXf(CrackRot, CrackPos, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Mesh, Opts, CrackXf,
			CrW, CrD, CrackWidth,
			0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Center);
	}
}

// ============================================================================
// generate_facade — Main Action
// ============================================================================

FMonolithActionResult FMonolithMeshFacadeActions::GenerateFacade(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(GS_ERROR_FACADE);
	}

	// ---- Parse building descriptor ----
	const TSharedPtr<FJsonObject>* DescObj = nullptr;
	if (!Params->TryGetObjectField(TEXT("building_descriptor"), DescObj) || !DescObj || !(*DescObj).IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing 'building_descriptor' object"));
	}

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing 'save_path'"));
	}

	// Parse exterior faces from descriptor
	const TArray<TSharedPtr<FJsonValue>>* FacesArr = nullptr;
	if (!(*DescObj)->TryGetArrayField(TEXT("exterior_faces"), FacesArr) || !FacesArr || FacesArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Building descriptor has no 'exterior_faces' array"));
	}

	TArray<FExteriorFaceDef> ExteriorFaces;
	for (const auto& FaceVal : *FacesArr)
	{
		const TSharedPtr<FJsonObject>* FaceObj = nullptr;
		if (!FaceVal->TryGetObject(FaceObj) || !FaceObj || !(*FaceObj).IsValid()) continue;

		FExteriorFaceDef F;
		(*FaceObj)->TryGetStringField(TEXT("wall"), F.Wall);
		if ((*FaceObj)->HasField(TEXT("floor_index")))
			F.FloorIndex = static_cast<int32>((*FaceObj)->GetNumberField(TEXT("floor_index")));
		if ((*FaceObj)->HasField(TEXT("width")))
			F.Width = static_cast<float>((*FaceObj)->GetNumberField(TEXT("width")));
		if ((*FaceObj)->HasField(TEXT("height")))
			F.Height = static_cast<float>((*FaceObj)->GetNumberField(TEXT("height")));

		const TArray<TSharedPtr<FJsonValue>>* OriginArr = nullptr;
		if ((*FaceObj)->TryGetArrayField(TEXT("world_origin"), OriginArr) && OriginArr && OriginArr->Num() >= 3)
		{
			F.WorldOrigin = FVector(
				(*OriginArr)[0]->AsNumber(),
				(*OriginArr)[1]->AsNumber(),
				(*OriginArr)[2]->AsNumber());
		}
		const TArray<TSharedPtr<FJsonValue>>* NormArr = nullptr;
		if ((*FaceObj)->TryGetArrayField(TEXT("normal"), NormArr) && NormArr && NormArr->Num() >= 3)
		{
			F.Normal = FVector(
				(*NormArr)[0]->AsNumber(),
				(*NormArr)[1]->AsNumber(),
				(*NormArr)[2]->AsNumber());
		}

		ExteriorFaces.Add(F);
	}

	if (ExteriorFaces.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("No valid exterior faces parsed from building descriptor"));
	}

	// ---- Load style ----
	FString StyleName = TEXT("colonial");
	Params->TryGetStringField(TEXT("style"), StyleName);

	FFacadeStyle Style;
	if (!LoadFacadeStyle(StyleName, Style))
	{
		// Fall back to defaults if style file not found
		Style.Name = StyleName;
		Style.Description = TEXT("Default (no preset file found)");
	}

	// ---- Override style with explicit params ----
	if (Params->HasField(TEXT("window_width")))
		Style.WindowWidth = static_cast<float>(Params->GetNumberField(TEXT("window_width")));
	if (Params->HasField(TEXT("window_height")))
		Style.WindowHeight = static_cast<float>(Params->GetNumberField(TEXT("window_height")));
	if (Params->HasField(TEXT("sill_height")))
		Style.SillHeight = static_cast<float>(Params->GetNumberField(TEXT("sill_height")));

	bool bHasCornice = !Params->HasField(TEXT("has_cornice")) || Params->GetBoolField(TEXT("has_cornice"));
	FString GroundFloorStyle = TEXT("residential");
	Params->TryGetStringField(TEXT("ground_floor_style"), GroundFloorStyle);
	int32 Seed = Params->HasField(TEXT("seed")) ? static_cast<int32>(Params->GetNumberField(TEXT("seed"))) : 0;

	// ---- Determine building height (max floor Z + height) ----
	float TotalBuildingHeight = 0.0f;
	int32 MaxFloorIndex = 0;
	for (const FExteriorFaceDef& Face : ExteriorFaces)
	{
		float FaceTop = (Face.WorldOrigin.Z - ExteriorFaces[0].WorldOrigin.Z) + Face.Height;
		if (FaceTop > TotalBuildingHeight)
		{
			TotalBuildingHeight = FaceTop;
		}
		if (Face.FloorIndex > MaxFloorIndex)
		{
			MaxFloorIndex = Face.FloorIndex;
		}
	}

	// Get building origin Z (lowest face)
	float BuildingBaseZ = ExteriorFaces[0].WorldOrigin.Z;
	for (const FExteriorFaceDef& Face : ExteriorFaces)
	{
		if (Face.WorldOrigin.Z < BuildingBaseZ)
			BuildingBaseZ = Face.WorldOrigin.Z;
	}

	// ---- Get wall thickness from descriptor ----
	float WallThickness = 15.0f;
	const TSharedPtr<FJsonObject>* WallThickObj = nullptr;
	if ((*DescObj)->TryGetObjectField(TEXT("wall_thickness"), WallThickObj) && WallThickObj && (*WallThickObj).IsValid())
	{
		if ((*WallThickObj)->HasField(TEXT("exterior")))
			WallThickness = static_cast<float>((*WallThickObj)->GetNumberField(TEXT("exterior")));
	}

	// ---- Create mesh ----
	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	bool bHadBooleans = false;

	// Group faces by wall direction + floor for window alignment
	// First: compute ground floor window positions per wall direction for vertical alignment
	TMap<FString, TArray<float>> GroundFloorWindowX; // wall -> X positions

	// ---- Process all faces ----
	int32 TotalWindows = 0;
	int32 TotalDoors = 0;

	TArray<TSharedPtr<FJsonValue>> WindowMetadataArr;
	TArray<TSharedPtr<FJsonValue>> DoorMetadataArr;

	for (const FExteriorFaceDef& Face : ExteriorFaces)
	{
		bool bIsGroundFloor = (Face.FloorIndex == 0);
		float MinSpacing = Style.WindowWidth * 0.6f; // min gap = 60% of window width
		float Margin = Style.FrameWidth + Style.CornerWidth;

		// 1. Build wall slab
		BuildWallSlab(Mesh, Face, WallThickness, Style.WallMaterialId);

		// 2. Compute window positions
		TArray<float> WinXPositions;

		if (bIsGroundFloor && GroundFloorStyle == TEXT("storefront"))
		{
			// Storefront: fewer, wider openings
			WinXPositions = ComputeWindowPositions(Face.Width, Style.WindowWidth * 2.0f, Margin, MinSpacing);
		}
		else if (bIsGroundFloor)
		{
			// Ground floor: compute and store for alignment
			WinXPositions = ComputeWindowPositions(Face.Width, Style.WindowWidth, Margin, MinSpacing);
			GroundFloorWindowX.FindOrAdd(Face.Wall) = WinXPositions;
		}
		else
		{
			// Upper floors: try to align with ground floor
			const TArray<float>* GroundPositions = GroundFloorWindowX.Find(Face.Wall);
			if (GroundPositions && GroundPositions->Num() > 0)
			{
				// Reuse ground floor positions (if wall width matches)
				WinXPositions = *GroundPositions;
			}
			else
			{
				WinXPositions = ComputeWindowPositions(Face.Width, Style.WindowWidth, Margin, MinSpacing);
			}
		}

		// 3. Build window placements
		TArray<FWindowPlacement> Windows;
		for (float XPos : WinXPositions)
		{
			FWindowPlacement Win;
			Win.CenterX = XPos;
			Win.Width = (bIsGroundFloor && GroundFloorStyle == TEXT("storefront")) ? Style.WindowWidth * 2.0f : Style.WindowWidth;
			Win.Height = (bIsGroundFloor && GroundFloorStyle == TEXT("storefront")) ? Face.Height * 0.65f : Style.WindowHeight;
			Win.SillZ = (bIsGroundFloor && GroundFloorStyle == TEXT("storefront")) ? 35.0f : Style.SillHeight;
			Win.FloorIndex = Face.FloorIndex;
			Win.bIsGroundFloor = bIsGroundFloor;
			Windows.Add(Win);
		}

		// 4. Build door placements (one door per ground-floor face that's wide enough)
		TArray<FDoorPlacement> Doors;
		if (bIsGroundFloor && Face.Width >= Style.DoorWidth + 2.0f * Margin)
		{
			// Only place a door on the first ground-floor face per wall direction
			// Use seed to pick which face gets a door
			FRandomStream DoorRng(Seed + FCrc::StrCrc32(*Face.Wall));
			if (DoorRng.FRand() < 0.4f || GroundFloorStyle == TEXT("entrance"))
			{
				FDoorPlacement Door;
				Door.CenterX = 0.0f; // Center of face
				Door.Width = Style.DoorWidth;
				Door.Height = Style.DoorHeight;
				Door.bStorefront = (GroundFloorStyle == TEXT("storefront"));
				Doors.Add(Door);

				// Remove any window that overlaps the door
				float DoorHalfW = Style.DoorWidth * 0.5f + Style.FrameWidth;
				Windows.RemoveAll([DoorHalfW](const FWindowPlacement& W)
				{
					return FMath::Abs(W.CenterX) < DoorHalfW;
				});
			}
		}

		// 5. Boolean-subtract all openings
		CutOpenings(Mesh, Face, Windows, Doors, WallThickness, bHadBooleans);

		// 6. Add window frames
		AddWindowFrames(Mesh, Face, Windows, Style, WallThickness);

		// 7. Add door frames
		AddDoorFrames(Mesh, Face, Doors, Style, WallThickness);

		// 8. Add glass panes
		AddGlassPanes(Mesh, Face, Windows, Style.GlassMaterialId);

		// 9. Add belt course at floor transition (above ground floor only)
		if (bIsGroundFloor && MaxFloorIndex > 0)
		{
			AddBeltCourse(Mesh, Face, Face.Height, Style);
		}

		// 10. Add cornice (only on top floor faces)
		if (bHasCornice && Face.FloorIndex == MaxFloorIndex)
		{
			// Cornice Z is relative to face — it sits at the top of this face
			AddCornice(Mesh, Face, Face.Height, Style);
		}

		// Collect metadata
		TotalWindows += Windows.Num();
		TotalDoors += Doors.Num();

		FVector WidthAxis = GetFaceWidthAxis(Face);
		FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

		for (const FWindowPlacement& W : Windows)
		{
			auto WMeta = MakeShared<FJsonObject>();
			WMeta->SetStringField(TEXT("wall"), Face.Wall);
			WMeta->SetNumberField(TEXT("floor_index"), Face.FloorIndex);
			WMeta->SetNumberField(TEXT("center_x"), W.CenterX);
			WMeta->SetNumberField(TEXT("sill_z"), W.SillZ);
			WMeta->SetNumberField(TEXT("width"), W.Width);
			WMeta->SetNumberField(TEXT("height"), W.Height);

			FVector WorldPos = FaceCenter + WidthAxis * W.CenterX;
			WorldPos.Z = Face.WorldOrigin.Z + W.SillZ + W.Height * 0.5f;
			TArray<TSharedPtr<FJsonValue>> PosArr;
			PosArr.Add(MakeShared<FJsonValueNumber>(WorldPos.X));
			PosArr.Add(MakeShared<FJsonValueNumber>(WorldPos.Y));
			PosArr.Add(MakeShared<FJsonValueNumber>(WorldPos.Z));
			WMeta->SetArrayField(TEXT("world_center"), PosArr);

			WindowMetadataArr.Add(MakeShared<FJsonValueObject>(WMeta));
		}

		for (const FDoorPlacement& D : Doors)
		{
			auto DMeta = MakeShared<FJsonObject>();
			DMeta->SetStringField(TEXT("wall"), Face.Wall);
			DMeta->SetNumberField(TEXT("floor_index"), Face.FloorIndex);
			DMeta->SetNumberField(TEXT("center_x"), D.CenterX);
			DMeta->SetNumberField(TEXT("width"), D.Width);
			DMeta->SetNumberField(TEXT("height"), D.Height);
			DMeta->SetBoolField(TEXT("storefront"), D.bStorefront);

			FVector WorldPos = FaceCenter + WidthAxis * D.CenterX;
			WorldPos.Z = Face.WorldOrigin.Z + D.Height * 0.5f;
			TArray<TSharedPtr<FJsonValue>> PosArr;
			PosArr.Add(MakeShared<FJsonValueNumber>(WorldPos.X));
			PosArr.Add(MakeShared<FJsonValueNumber>(WorldPos.Y));
			PosArr.Add(MakeShared<FJsonValueNumber>(WorldPos.Z));
			DMeta->SetArrayField(TEXT("world_center"), PosArr);

			DoorMetadataArr.Add(MakeShared<FJsonValueObject>(DMeta));
		}
	}

	// ---- Cleanup mesh ----
	FMonolithMeshProceduralActions::CleanupMesh(Mesh, bHadBooleans);

	// ---- Box UV projection ----
	{
		FGeometryScriptMeshSelection EmptySelection;
		FTransform UVBox = FTransform::Identity;
		UVBox.SetScale3D(FVector(100.0f));
		UGeometryScriptLibrary_MeshUVFunctions::SetMeshUVsFromBoxProjection(
			Mesh, 0, UVBox, EmptySelection, 2);
	}

	int32 TriCount = Mesh->GetTriangleCount();

	// ---- Save mesh ----
	bool bOverwrite = Params->HasField(TEXT("overwrite")) ? Params->GetBoolField(TEXT("overwrite")) : false;
	FString SaveErr;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(Mesh, SavePath, bOverwrite, SaveErr))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Facade generated (%d tris, %d windows, %d doors) but save failed: %s"),
			TriCount, TotalWindows, TotalDoors, *SaveErr));
	}

	// ---- Place in scene ----
	FVector Location = FVector::ZeroVector;
	const TArray<TSharedPtr<FJsonValue>>* LocArr = nullptr;
	if (Params->TryGetArrayField(TEXT("location"), LocArr) && LocArr && LocArr->Num() >= 3)
	{
		Location = FVector(
			(*LocArr)[0]->AsNumber(),
			(*LocArr)[1]->AsNumber(),
			(*LocArr)[2]->AsNumber());
	}

	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);
	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);

	AActor* Actor = FMonolithMeshProceduralActions::PlaceMeshInScene(SavePath, Location, FRotator::ZeroRotator, Label, false, Folder);

	// ---- Build result ----
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("save_path"), SavePath);
	Result->SetStringField(TEXT("style"), Style.Name);
	Result->SetNumberField(TEXT("triangle_count"), TriCount);
	Result->SetNumberField(TEXT("window_count"), TotalWindows);
	Result->SetNumberField(TEXT("door_count"), TotalDoors);
	Result->SetNumberField(TEXT("exterior_face_count"), ExteriorFaces.Num());
	Result->SetBoolField(TEXT("has_cornice"), bHasCornice);
	Result->SetStringField(TEXT("ground_floor_style"), GroundFloorStyle);
	Result->SetBoolField(TEXT("had_booleans"), bHadBooleans);

	Result->SetArrayField(TEXT("windows"), WindowMetadataArr);
	Result->SetArrayField(TEXT("doors"), DoorMetadataArr);

	// Material slot summary
	auto MatSlots = MakeShared<FJsonObject>();
	MatSlots->SetNumberField(TEXT("wall"), Style.WallMaterialId);
	MatSlots->SetNumberField(TEXT("trim"), Style.TrimMaterialId);
	MatSlots->SetNumberField(TEXT("window_frame"), Style.WindowFrameMaterialId);
	MatSlots->SetNumberField(TEXT("cornice"), Style.CorniceMaterialId);
	MatSlots->SetNumberField(TEXT("glass"), Style.GlassMaterialId);
	MatSlots->SetNumberField(TEXT("door"), Style.DoorMaterialId);
	Result->SetObjectField(TEXT("material_slots"), MatSlots);

	if (Actor)
	{
		Result->SetStringField(TEXT("actor_name"), Actor->GetActorNameOrLabel());
		Result->SetBoolField(TEXT("placed_in_scene"), true);

		// Tag the actor
		Actor->Tags.Add(FName(TEXT("BuildingFacade")));
		Actor->Tags.Add(FName(TEXT("Monolith.Procedural")));
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// list_facade_styles
// ============================================================================

FMonolithActionResult FMonolithMeshFacadeActions::ListFacadeStyles(const TSharedPtr<FJsonObject>& Params)
{
	FString StylesDir = GetFacadeStylesDir();

	TArray<FString> Files;
	IFileManager::Get().FindFiles(Files, *(StylesDir / TEXT("*.json")), true, false);

	TArray<TSharedPtr<FJsonValue>> StylesArr;
	for (const FString& File : Files)
	{
		FString StyleName = FPaths::GetBaseFilename(File);
		FFacadeStyle Style;

		auto StyleObj = MakeShared<FJsonObject>();
		StyleObj->SetStringField(TEXT("name"), StyleName);

		if (LoadFacadeStyle(StyleName, Style))
		{
			StyleObj->SetStringField(TEXT("description"), Style.Description);
			StyleObj->SetNumberField(TEXT("window_width"), Style.WindowWidth);
			StyleObj->SetNumberField(TEXT("window_height"), Style.WindowHeight);
			StyleObj->SetNumberField(TEXT("cornice_height"), Style.CorniceHeight);
			StyleObj->SetNumberField(TEXT("door_width"), Style.DoorWidth);
			StyleObj->SetNumberField(TEXT("door_height"), Style.DoorHeight);
		}

		StylesArr.Add(MakeShared<FJsonValueObject>(StyleObj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("styles"), StylesArr);
	Result->SetNumberField(TEXT("count"), StylesArr.Num());
	Result->SetStringField(TEXT("styles_directory"), StylesDir);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// apply_horror_damage
// ============================================================================

FMonolithActionResult FMonolithMeshFacadeActions::ApplyHorrorDamage(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(GS_ERROR_FACADE);
	}

	FString TargetActorName;
	if (!Params->TryGetStringField(TEXT("target_actor"), TargetActorName) || TargetActorName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing 'target_actor'"));
	}

	// Find the actor
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	AActor* TargetActor = nullptr;
	for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
	{
		if (It->GetActorNameOrLabel() == TargetActorName)
		{
			TargetActor = *It;
			break;
		}
	}

	if (!TargetActor)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Actor '%s' not found"), *TargetActorName));
	}

	// Parse params
	float DamageLevel = Params->HasField(TEXT("damage_level")) ? static_cast<float>(Params->GetNumberField(TEXT("damage_level"))) : 0.5f;
	DamageLevel = FMath::Clamp(DamageLevel, 0.0f, 1.0f);
	int32 Seed = Params->HasField(TEXT("seed")) ? static_cast<int32>(Params->GetNumberField(TEXT("seed"))) : 42;
	float BoardedFraction = Params->HasField(TEXT("boarded_windows")) ? static_cast<float>(Params->GetNumberField(TEXT("boarded_windows"))) : 0.3f;
	float BrokenFraction = Params->HasField(TEXT("broken_glass")) ? static_cast<float>(Params->GetNumberField(TEXT("broken_glass"))) : 0.2f;
	bool bRustStains = !Params->HasField(TEXT("rust_stains")) || Params->GetBoolField(TEXT("rust_stains"));
	bool bCracks = !Params->HasField(TEXT("cracks")) || Params->GetBoolField(TEXT("cracks"));

	// Get the actor's bounds to estimate facade dimensions
	FBox ActorBounds = TargetActor->GetComponentsBoundingBox();
	FVector BoundsSize = ActorBounds.GetSize();
	FVector BoundsCenter = ActorBounds.GetCenter();

	// Build synthetic exterior faces from bounding box (4 sides)
	TArray<FExteriorFaceDef> SyntheticFaces;

	auto AddFace = [&](const FString& Wall, const FVector& Origin, const FVector& Normal, float Width, float Height)
	{
		FExteriorFaceDef F;
		F.Wall = Wall;
		F.FloorIndex = 0;
		F.WorldOrigin = Origin;
		F.Normal = Normal;
		F.Width = Width;
		F.Height = Height;
		SyntheticFaces.Add(F);
	};

	// Four cardinal faces from bounding box
	AddFace(TEXT("north"), FVector(ActorBounds.Min.X, ActorBounds.Min.Y, ActorBounds.Min.Z),
		FVector(0, -1, 0), BoundsSize.X, BoundsSize.Z);
	AddFace(TEXT("south"), FVector(ActorBounds.Max.X, ActorBounds.Max.Y, ActorBounds.Min.Z),
		FVector(0, 1, 0), BoundsSize.X, BoundsSize.Z);
	AddFace(TEXT("east"), FVector(ActorBounds.Max.X, ActorBounds.Min.Y, ActorBounds.Min.Z),
		FVector(1, 0, 0), BoundsSize.Y, BoundsSize.Z);
	AddFace(TEXT("west"), FVector(ActorBounds.Min.X, ActorBounds.Max.Y, ActorBounds.Min.Z),
		FVector(-1, 0, 0), BoundsSize.Y, BoundsSize.Z);

	// Create damage overlay mesh
	UDynamicMesh* DamageMesh = NewObject<UDynamicMesh>(Pool);
	FRandomStream Rng(Seed);

	int32 BoardedCount = 0;
	int32 CrackCount = 0;
	TArray<TSharedPtr<FJsonValue>> RustStainPositions;

	for (const FExteriorFaceDef& Face : SyntheticFaces)
	{
		// Estimate window positions (using typical defaults since we don't have the original metadata)
		float WinWidth = 80.0f;
		float WinHeight = 120.0f;
		float SillHeight = 90.0f;
		float Margin = 30.0f;
		float MinSpacing = 50.0f;

		TArray<float> WinXPositions = ComputeWindowPositions(Face.Width, WinWidth, Margin, MinSpacing);

		TArray<FWindowPlacement> Windows;
		for (float XPos : WinXPositions)
		{
			FWindowPlacement Win;
			Win.CenterX = XPos;
			Win.Width = WinWidth;
			Win.Height = WinHeight;
			Win.SillZ = SillHeight;
			Win.FloorIndex = 0;
			Win.bIsGroundFloor = true;
			Windows.Add(Win);
		}

		// Boarded windows
		if (BoardedFraction > 0.0f && Windows.Num() > 0)
		{
			TArray<int32> BoardedIndices;
			for (int32 i = 0; i < Windows.Num(); ++i)
			{
				if (Rng.FRand() < BoardedFraction * DamageLevel)
				{
					BoardedIndices.Add(i);
				}
			}
			if (BoardedIndices.Num() > 0)
			{
				AddBoardedWindows(DamageMesh, Face, Windows, BoardedIndices, Seed);
				BoardedCount += BoardedIndices.Num();
			}
		}

		// Rust stain markers (small geometry patches below windows)
		if (bRustStains)
		{
			FVector WidthAxis = GetFaceWidthAxis(Face);
			FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

			for (int32 i = 0; i < Windows.Num(); ++i)
			{
				if (Rng.FRand() < DamageLevel * 0.5f)
				{
					FVector StainPos = FaceCenter + WidthAxis * Windows[i].CenterX + Face.Normal * 0.3f;
					StainPos.Z = Face.WorldOrigin.Z + Windows[i].SillZ - 5.0f;

					auto PosObj = MakeShared<FJsonObject>();
					TArray<TSharedPtr<FJsonValue>> PosArr;
					PosArr.Add(MakeShared<FJsonValueNumber>(StainPos.X));
					PosArr.Add(MakeShared<FJsonValueNumber>(StainPos.Y));
					PosArr.Add(MakeShared<FJsonValueNumber>(StainPos.Z));
					PosObj->SetArrayField(TEXT("position"), PosArr);
					PosObj->SetStringField(TEXT("wall"), Face.Wall);
					PosObj->SetNumberField(TEXT("streak_length"), Rng.FRandRange(20.0f, 80.0f) * DamageLevel);
					RustStainPositions.Add(MakeShared<FJsonValueObject>(PosObj));
				}
			}
		}

		// Crack geometry
		if (bCracks && DamageLevel > 0.2f)
		{
			AddCrackGeometry(DamageMesh, Face, DamageLevel, Seed);
			CrackCount += FMath::Clamp(FMath::RoundToInt32(DamageLevel * 8.0f), 1, 12);
		}
	}

	if (DamageMesh->GetTriangleCount() == 0)
	{
		return FMonolithActionResult::Error(TEXT("No damage geometry generated (damage_level may be too low or actor too small)"));
	}

	// Cleanup
	FMonolithMeshProceduralActions::CleanupMesh(DamageMesh, false);

	// UV projection
	{
		FGeometryScriptMeshSelection EmptySelection;
		FTransform UVBox = FTransform::Identity;
		UVBox.SetScale3D(FVector(50.0f));
		UGeometryScriptLibrary_MeshUVFunctions::SetMeshUVsFromBoxProjection(
			DamageMesh, 0, UVBox, EmptySelection, 2);
	}

	int32 TriCount = DamageMesh->GetTriangleCount();

	// Save
	FString DamageSavePath;
	Params->TryGetStringField(TEXT("save_path"), DamageSavePath);
	if (DamageSavePath.IsEmpty())
	{
		DamageSavePath = FString::Printf(TEXT("/Game/Procedural/Damage/%s_Damage"), *TargetActorName);
	}

	bool bOverwrite = Params->HasField(TEXT("overwrite")) ? Params->GetBoolField(TEXT("overwrite")) : false;
	FString SaveErr;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(DamageMesh, DamageSavePath, bOverwrite, SaveErr))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Damage mesh generated (%d tris) but save failed: %s"), TriCount, *SaveErr));
	}

	// Place near the target actor
	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);
	if (Folder.IsEmpty())
	{
		// Use target actor's folder
		Folder = TargetActor->GetFolderPath().ToString();
	}

	FString DamageLabel = FString::Printf(TEXT("%s_Damage"), *TargetActorName);
	AActor* DamageActor = FMonolithMeshProceduralActions::PlaceMeshInScene(
		DamageSavePath, TargetActor->GetActorLocation(), FRotator::ZeroRotator, DamageLabel, false, Folder);

	// Build result
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("save_path"), DamageSavePath);
	Result->SetStringField(TEXT("target_actor"), TargetActorName);
	Result->SetNumberField(TEXT("triangle_count"), TriCount);
	Result->SetNumberField(TEXT("damage_level"), DamageLevel);
	Result->SetNumberField(TEXT("boarded_windows"), BoardedCount);
	Result->SetNumberField(TEXT("crack_count"), CrackCount);
	Result->SetArrayField(TEXT("rust_stain_positions"), RustStainPositions);
	Result->SetBoolField(TEXT("had_cracks"), bCracks && DamageLevel > 0.2f);

	if (DamageActor)
	{
		Result->SetStringField(TEXT("actor_name"), DamageActor->GetActorNameOrLabel());
		Result->SetBoolField(TEXT("placed_in_scene"), true);

		DamageActor->Tags.Add(FName(TEXT("HorrorDamage")));
		DamageActor->Tags.Add(FName(TEXT("Monolith.Procedural")));
	}

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_GEOMETRYSCRIPT
