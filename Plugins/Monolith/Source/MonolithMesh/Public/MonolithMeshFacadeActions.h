#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"
#include "MonolithMeshBuildingTypes.h"

#if WITH_GEOMETRYSCRIPT

class UMonolithMeshHandlePool;
class UDynamicMesh;

/**
 * SP3: Facade & Window Generation
 * Consumes the Building Descriptor's exterior_faces array to generate windows, doors,
 * trim, cornices, and storefronts. CGA-style vertical split (base/shaft/cap) with
 * even window placement and horror damage overlay.
 *
 * 3 actions: generate_facade, list_facade_styles, apply_horror_damage
 *
 * Public static utilities are shared with FMonolithMeshBuildingActions for integrated
 * facade generation (v3 single-pass architecture).
 */
class FMonolithMeshFacadeActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);
	static void SetHandlePool(UMonolithMeshHandlePool* InPool);

	// ---- Public types (shared with building generator) ----

	/** Facade style definition loaded from JSON presets */
	struct FFacadeStyle
	{
		FString Name;
		FString Description;

		// Window defaults
		float WindowWidth = 80.0f;
		float WindowHeight = 120.0f;
		float FrameWidth = 6.0f;
		float FrameDepth = 5.0f;
		float SillDepth = 10.0f;
		float SillHeight = 90.0f;
		float LintelHeight = 12.0f;
		bool bArch = false;

		// Trim
		float CornerWidth = 12.0f;
		float CornerDepth = 5.0f;
		float BeltCourseHeight = 10.0f;
		float BeltCourseDepth = 5.0f;

		// Cornice
		float CorniceHeight = 25.0f;
		float CorniceDepth = 20.0f;
		FString CorniceProfile = TEXT("classical");

		// Ground floor
		float GroundFloorHeightMultiplier = 1.3f;
		float StorefrontDepth = 5.0f;
		float DoorWidth = 100.0f;
		float DoorHeight = 240.0f;

		// Material slot mapping
		int32 WallMaterialId = 0;
		int32 TrimMaterialId = 3;
		int32 WindowFrameMaterialId = 4;
		int32 CorniceMaterialId = 5;
		int32 GlassMaterialId = 6;
		int32 DoorMaterialId = 7;
	};

	struct FWindowPlacement
	{
		float CenterX;      // Center X position along wall face (local to face)
		float SillZ;        // Z of window sill (local to face)
		float Width;
		float Height;
		int32 FloorIndex;
		bool bIsGroundFloor;
	};

	struct FDoorPlacement
	{
		float CenterX;
		float Width;
		float Height;
		bool bStorefront;
	};

	// ---- Public static utilities (callable from building generator) ----

	/** Load a facade style from JSON preset file. Returns false if not found. */
	static bool LoadFacadeStyle(const FString& StyleName, FFacadeStyle& OutStyle);

	/** Get the directory path for facade style JSON files */
	static FString GetFacadeStylesDir();

	/**
	 * Core window placement: evenly distribute N windows across a wall of given width.
	 * Returns center-X positions relative to wall center (i.e., -W/2 to +W/2 range).
	 */
	static TArray<float> ComputeWindowPositions(float WallWidth, float WindowWidth,
		float Margin, float MinSpacing);

	/** Build the base wall slab for a single exterior face */
	static void BuildWallSlab(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		float WallThickness, int32 MaterialId);

	/** Boolean-subtract all window and door openings from the wall mesh.
	 *  Pre-insets cut regions by 0.5cm to avoid coplanar faces.
	 *  LEGACY: Use CutOpeningsSelectionInset for the v3 pipeline. */
	static void CutOpenings(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		const TArray<FWindowPlacement>& Windows, const TArray<FDoorPlacement>& Doors,
		float WallThickness, bool& bHadBooleans);

	/**
	 * Selection+Inset window/door openings — replaces boolean subtract.
	 * Pre-subdivides the wall with plane cuts at window boundaries, then uses
	 * SelectMeshElementsInBox + SelectMeshElementsByNormalAngle + ApplyMeshInsetOutsetFaces
	 * + DeleteSelectedTrianglesFromMesh to create clean openings with frame geometry.
	 *
	 * ~20x faster than boolean subtract, no T-junctions or degenerate triangles.
	 *
	 * @param bUseSelectionInset  If false, falls back to CutOpenings (boolean subtract).
	 */
	static void CutOpeningsSelectionInset(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		const TArray<FWindowPlacement>& Windows, const TArray<FDoorPlacement>& Doors,
		float WallThickness, float FrameWidth, bool bUseSelectionInset, bool& bHadBooleans);

	/** Add window frame trim (jambs, lintel, sill) for all windows */
	static void AddWindowFrames(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		const TArray<FWindowPlacement>& Windows, const FFacadeStyle& Style, float WallThickness);

	/** Add door frame trim */
	static void AddDoorFrames(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		const TArray<FDoorPlacement>& Doors, const FFacadeStyle& Style, float WallThickness);

	/** Add cornice at the top of the building (runs along wall top edge) */
	static void AddCornice(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		float TotalBuildingHeight, const FFacadeStyle& Style);

	/** Add belt course between ground floor and upper floors */
	static void AddBeltCourse(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		float CourseZ, const FFacadeStyle& Style);

	/** Add glass pane geometry inside window openings */
	static void AddGlassPanes(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		const TArray<FWindowPlacement>& Windows, int32 GlassMaterialId);

	/** Get the horizontal axis for a face (perpendicular to normal, in XY plane) */
	static FVector GetFaceWidthAxis(const FExteriorFaceDef& Face);

	/** Compute the transform that maps from face-local (width along X, height along Z)
	 *  to world space, given the face's origin, normal, and wall direction. */
	static FTransform ComputeFaceTransform(const FExteriorFaceDef& Face);

private:
	static UMonolithMeshHandlePool* Pool;

	// ---- Action handlers ----
	static FMonolithActionResult GenerateFacade(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ListFacadeStyles(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ApplyHorrorDamage(const TSharedPtr<FJsonObject>& Params);

	// ---- Horror damage builders ----

	/** Add boarding planks across window openings */
	static void AddBoardedWindows(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		const TArray<FWindowPlacement>& Windows, const TArray<int32>& WindowIndices,
		int32 Seed);

	/** Add crack line geometry on wall surface */
	static void AddCrackGeometry(UDynamicMesh* Mesh, const FExteriorFaceDef& Face,
		float DamageLevel, int32 Seed);
};

#endif // WITH_GEOMETRYSCRIPT
