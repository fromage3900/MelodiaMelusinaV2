#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"
#include "MonolithMeshBuildingTypes.h"

#if WITH_GEOMETRYSCRIPT

class UMonolithMeshHandlePool;
class UDynamicMesh;

/**
 * SP8b: Architectural Feature Actions
 * Standalone procedural geometry for balconies, porches, fire escapes, ADA ramps, and railings.
 * All actions produce static mesh assets via GeometryScript primitives (AppendBox/AppendCylinder).
 * 5 actions: create_balcony, create_porch, create_fire_escape, create_ramp_connector, create_railing.
 *
 * Supports optional `building_context` parameter for auto-orientation to a building wall face.
 * When provided, features auto-orient to the wall normal and emit wall_openings in the result JSON.
 */
class FMonolithMeshArchFeatureActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);
	static void SetHandlePool(UMonolithMeshHandlePool* InPool);

private:
	static UMonolithMeshHandlePool* Pool;

	// Action handlers
	static FMonolithActionResult CreateBalcony(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreatePorch(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateFireEscape(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateRampConnector(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateRailing(const TSharedPtr<FJsonObject>& Params);

	// ---- Attachment context helpers ----

	/** Parse building_context from Params. Returns FAttachmentContext with bValid=true if present and valid. */
	static FAttachmentContext ParseBuildingContext(const TSharedPtr<FJsonObject>& Params);

	/** Compute yaw rotation from a wall normal vector */
	static FRotator ComputeWallRotation(const FVector& WallNormal);

	/** Compute world-space attachment position for a feature centered on a wall face.
	 *  Places the feature at WallOrigin + offset along the wall to center it, pushed out by FeatureDepth/2. */
	static FVector ComputeAttachmentPosition(const FVector& WallOrigin, const FVector& WallNormal,
		const FVector& WallRight, float FeatureWidth, float FeatureDepth, float WallWidth);

	/** Emit wall_openings JSON array on the result object */
	static void EmitWallOpenings(const TSharedPtr<FJsonObject>& Result, const TArray<FWallOpeningRequest>& Openings);

	// ---- Internal geometry builders ----

	/** Build railing geometry along an edge. Posts + top rail + style-dependent infill.
	 *  Path is an array of 3D points defining the railing baseline.
	 *  All geometry is appended to Mesh in-place. */
	static void BuildRailingGeometry(UDynamicMesh* Mesh, const TArray<FVector>& Path,
		float Height, const FString& Style, float PostSpacing, float PostWidth,
		float RailWidth, float BarSpacing, float BarWidth, float PanelThickness,
		bool bClosedLoop);

	/** Apply box UV projection + compute split normals (standard finalization for additive geometry) */
	static void FinalizeGeometry(UDynamicMesh* Mesh);

	/** Save mesh to asset, optionally place in scene. Uses public helpers from FMonolithMeshProceduralActions.
	 *  Populates Result with save_path, actor_name, etc. Returns empty string on success, error message on failure.
	 *  When AttachCtx is valid, overrides location/rotation with computed wall-relative placement. */
	static FString SaveAndPlace(UDynamicMesh* Mesh, const TSharedPtr<FJsonObject>& Params,
		const TSharedPtr<FJsonObject>& Result,
		const FAttachmentContext& AttachCtx = FAttachmentContext(),
		float FeatureWidth = 0.0f, float FeatureDepth = 0.0f);

	/** Helper: parse a float from Params, returning Default if absent */
	static float GetFloat(const TSharedPtr<FJsonObject>& P, const FString& Key, float Default);

	/** Helper: parse an int from Params, returning Default if absent */
	static int32 GetInt(const TSharedPtr<FJsonObject>& P, const FString& Key, int32 Default);

	/** Helper: parse a string from Params, returning Default if absent */
	static FString GetString(const TSharedPtr<FJsonObject>& P, const FString& Key, const FString& Default);

	/** Helper: parse a bool from Params, returning Default if absent */
	static bool GetBool(const TSharedPtr<FJsonObject>& P, const FString& Key, bool Default);
};

#endif // WITH_GEOMETRYSCRIPT
