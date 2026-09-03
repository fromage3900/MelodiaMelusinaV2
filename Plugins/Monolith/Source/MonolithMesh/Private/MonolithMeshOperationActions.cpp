#if WITH_GEOMETRYSCRIPT

#include "MonolithMeshOperationActions.h"
#include "MonolithMeshHandlePool.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"

#include "UDynamicMesh.h"
#include "DynamicMesh/DynamicMesh3.h"

#include "GeometryScript/MeshBooleanFunctions.h"
#include "GeometryScript/MeshSimplifyFunctions.h"
#include "GeometryScript/MeshRemeshFunctions.h"
#include "GeometryScript/MeshRepairFunctions.h"
#include "GeometryScript/MeshUVFunctions.h"
#include "GeometryScript/MeshTransformFunctions.h"
#include "GeometryScript/CollisionFunctions.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

using namespace UE::Geometry;

UMonolithMeshHandlePool* FMonolithMeshOperationActions::Pool = nullptr;

void FMonolithMeshOperationActions::SetHandlePool(UMonolithMeshHandlePool* InPool)
{
	Pool = InPool;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshOperationActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_handle"),
		TEXT("Create a mesh handle from a StaticMesh asset or primitive (box/sphere/cylinder/cone/torus/plane)"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::CreateHandle),
		FParamSchemaBuilder()
			.Required(TEXT("source"), TEXT("string"), TEXT("Asset path (e.g. /Game/Meshes/SM_Box) or primitive descriptor (e.g. primitive:box)"))
			.Required(TEXT("handle"), TEXT("string"), TEXT("Name for this handle"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("release_handle"),
		TEXT("Release a mesh handle, freeing memory"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::ReleaseHandle),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Handle name to release"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("list_handles"),
		TEXT("List all active mesh handles with source, triangle count, and idle time"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::ListHandles),
		FParamSchemaBuilder().Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("save_handle"),
		TEXT("Save a mesh handle as a new StaticMesh asset with auto-generated collision"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::SaveHandle),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Handle name to save"))
			.RequiredAssetPath(TEXT("target_path"), TEXT("Asset path for the new StaticMesh (e.g. /Game/Meshes/SM_Result)"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Allow overwriting existing asset"), TEXT("false"))
			.Optional(TEXT("collision"), TEXT("string"), TEXT("Collision mode: auto, box, convex, complex_as_simple, none"), TEXT("auto"))
			.Optional(TEXT("max_hulls"), TEXT("integer"), TEXT("Max convex hulls for decomposition (auto/convex modes)"), TEXT("4"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("mesh_boolean"),
		TEXT("Boolean operation (union/subtract/intersect) between two mesh handles"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::MeshBoolean),
		FParamSchemaBuilder()
			.Required(TEXT("handle_a"), TEXT("string"), TEXT("First mesh handle (target)"))
			.Required(TEXT("handle_b"), TEXT("string"), TEXT("Second mesh handle (tool)"))
			.Required(TEXT("operation"), TEXT("string"), TEXT("Boolean operation: union, subtract, or intersect"))
			.Required(TEXT("result_handle"), TEXT("string"), TEXT("Name for the result handle"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("mesh_simplify"),
		TEXT("Simplify a mesh to a target triangle count or percentage"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::MeshSimplify),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Handle to simplify"))
			.Optional(TEXT("target_triangles"), TEXT("integer"), TEXT("Target triangle count"))
			.Optional(TEXT("target_percentage"), TEXT("number"), TEXT("Target percentage (0.0-1.0) of current triangles"))
			.Optional(TEXT("max_deviation"), TEXT("number"), TEXT("Maximum geometric deviation tolerance"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("mesh_remesh"),
		TEXT("Isotropic remeshing to a target edge length"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::MeshRemesh),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Handle to remesh"))
			.Required(TEXT("target_edge_length"), TEXT("number"), TEXT("Target edge length in cm"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("generate_collision"),
		TEXT("Generate collision shapes for a mesh handle"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::GenerateCollision),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Handle to generate collision for"))
			.Optional(TEXT("method"), TEXT("string"), TEXT("Collision method: convex_decomp, auto_box, auto_sphere, auto_capsule, simplified"), TEXT("convex_decomp"))
			.Optional(TEXT("max_hulls"), TEXT("integer"), TEXT("Max convex hulls (for convex_decomp)"), TEXT("4"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("generate_lods"),
		TEXT("Generate LOD chain by repeated simplification"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::GenerateLods),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Source handle for LOD0"))
			.Required(TEXT("lod_count"), TEXT("integer"), TEXT("Number of LODs to generate (excluding LOD0)"))
			.Optional(TEXT("reduction_per_lod"), TEXT("number"), TEXT("Triangle reduction ratio per LOD (0.0-1.0)"), TEXT("0.5"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("fill_holes"),
		TEXT("Automatically detect and fill holes in a mesh"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::FillHoles),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Handle to repair"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("compute_uvs"),
		TEXT("Compute UVs using various projection methods"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::ComputeUvs),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Handle to compute UVs for"))
			.Optional(TEXT("method"), TEXT("string"), TEXT("UV method: auto_unwrap, box_project, planar_project, cylinder_project"), TEXT("auto_unwrap"))
			.Optional(TEXT("uv_channel"), TEXT("integer"), TEXT("UV channel index"), TEXT("0"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("mirror_mesh"),
		TEXT("Mirror a mesh across an axis"),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshOperationActions::MirrorMesh),
		FParamSchemaBuilder()
			.Required(TEXT("handle"), TEXT("string"), TEXT("Handle to mirror"))
			.Required(TEXT("axis"), TEXT("string"), TEXT("Mirror axis: X, Y, or Z"))
			.Optional(TEXT("weld"), TEXT("boolean"), TEXT("Weld vertices along mirror plane"), TEXT("true"))
			.Build());
}

// ============================================================================
// Handle Management Actions
// ============================================================================

FMonolithActionResult FMonolithMeshOperationActions::CreateHandle(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString Source = Params->GetStringField(TEXT("source"));
	FString HandleName = Params->GetStringField(TEXT("handle"));

	if (Source.IsEmpty() || HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Both 'source' and 'handle' are required"));
	}

	FString Error;
	if (!Pool->CreateHandle(HandleName, Source, Error))
	{
		return FMonolithActionResult::Error(Error);
	}

	// Return info about the created handle
	FString GetError;
	UDynamicMesh* Mesh = Pool->GetHandle(HandleName, GetError);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetStringField(TEXT("source"), Source);
	Result->SetNumberField(TEXT("triangle_count"), Mesh ? Mesh->GetTriangleCount() : 0);
	Result->SetStringField(TEXT("status"), TEXT("created"));

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::ReleaseHandle(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	if (HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'handle' is required"));
	}

	if (!Pool->ReleaseHandle(HandleName))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Handle '%s' not found"), *HandleName));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetStringField(TEXT("status"), TEXT("released"));

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::ListHandles(const TSharedPtr<FJsonObject>& /*Params*/)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	TSharedPtr<FJsonObject> Result = Pool->ListHandles();
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::SaveHandle(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	FString TargetPath = Params->GetStringField(TEXT("target_path"));
	bool bOverwrite = Params->HasField(TEXT("overwrite")) ? Params->GetBoolField(TEXT("overwrite")) : false;
	FString CollisionMode = Params->HasField(TEXT("collision")) ? Params->GetStringField(TEXT("collision")).ToLower() : TEXT("auto");
	int32 MaxHulls = Params->HasField(TEXT("max_hulls")) ? static_cast<int32>(Params->GetNumberField(TEXT("max_hulls"))) : 4;

	if (HandleName.IsEmpty() || TargetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Both 'handle' and 'target_path' are required"));
	}

	// Validate collision mode
	static const TSet<FString> ValidModes = { TEXT("auto"), TEXT("convex"), TEXT("box"), TEXT("complex_as_simple"), TEXT("none") };
	if (!ValidModes.Contains(CollisionMode))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Invalid collision mode '%s'. Valid: auto, convex, box, complex_as_simple, none"), *CollisionMode));
	}

	FString Error;
	if (!Pool->SaveHandle(HandleName, TargetPath, bOverwrite, Error, CollisionMode, MaxHulls))
	{
		return FMonolithActionResult::Error(Error);
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetStringField(TEXT("saved_to"), TargetPath);
	Result->SetStringField(TEXT("collision_mode"), CollisionMode);
	Result->SetNumberField(TEXT("max_hulls"), MaxHulls);
	Result->SetStringField(TEXT("status"), TEXT("saved"));

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// Mesh Operations
// ============================================================================

FMonolithActionResult FMonolithMeshOperationActions::MeshBoolean(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleA = Params->GetStringField(TEXT("handle_a"));
	FString HandleB = Params->GetStringField(TEXT("handle_b"));
	FString Operation = Params->GetStringField(TEXT("operation")).ToLower();
	FString ResultHandle = Params->GetStringField(TEXT("result_handle"));

	if (HandleA.IsEmpty() || HandleB.IsEmpty() || Operation.IsEmpty() || ResultHandle.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("handle_a, handle_b, operation, and result_handle are all required"));
	}

	FString ErrorA, ErrorB;
	UDynamicMesh* MeshA = Pool->GetHandle(HandleA, ErrorA);
	UDynamicMesh* MeshB = Pool->GetHandle(HandleB, ErrorB);

	if (!MeshA) return FMonolithActionResult::Error(ErrorA);
	if (!MeshB) return FMonolithActionResult::Error(ErrorB);

	// Map operation string to enum
	EGeometryScriptBooleanOperation BoolOp;
	if (Operation == TEXT("union"))
	{
		BoolOp = EGeometryScriptBooleanOperation::Union;
	}
	else if (Operation == TEXT("subtract"))
	{
		BoolOp = EGeometryScriptBooleanOperation::Subtract;
	}
	else if (Operation == TEXT("intersect"))
	{
		BoolOp = EGeometryScriptBooleanOperation::Intersection;
	}
	else
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown boolean operation '%s'. Valid: union, subtract, intersect"), *Operation));
	}

	// Create result handle first (to check name availability)
	FString CreateError;
	if (!Pool->CreateHandle(ResultHandle, FString::Printf(TEXT("internal:boolean:%s(%s,%s)"), *Operation, *HandleA, *HandleB), CreateError))
	{
		return FMonolithActionResult::Error(CreateError);
	}

	UDynamicMesh* ResultMesh = Pool->GetHandle(ResultHandle, CreateError);
	if (!ResultMesh)
	{
		return FMonolithActionResult::Error(TEXT("Failed to get newly created result handle"));
	}

	// Copy MeshA into result, then boolean with MeshB
	ResultMesh->SetMesh(MeshA->GetMeshRef());

	FGeometryScriptMeshBooleanOptions BoolOpts;
	UGeometryScriptLibrary_MeshBooleanFunctions::ApplyMeshBoolean(
		ResultMesh, FTransform::Identity,
		MeshB, FTransform::Identity,
		BoolOp, BoolOpts);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("result_handle"), ResultHandle);
	Result->SetStringField(TEXT("operation"), Operation);
	Result->SetNumberField(TEXT("triangle_count"), ResultMesh->GetTriangleCount());
	Result->SetStringField(TEXT("status"), TEXT("completed"));

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::MeshSimplify(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	if (HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'handle' is required"));
	}

	FString Error;
	UDynamicMesh* Mesh = Pool->GetHandle(HandleName, Error);
	if (!Mesh) return FMonolithActionResult::Error(Error);

	int32 OriginalTris = Mesh->GetTriangleCount();
	int32 TargetTris = 0;

	if (Params->HasField(TEXT("target_triangles")))
	{
		TargetTris = static_cast<int32>(Params->GetNumberField(TEXT("target_triangles")));
	}
	else if (Params->HasField(TEXT("target_percentage")))
	{
		double Pct = Params->GetNumberField(TEXT("target_percentage"));
		Pct = FMath::Clamp(Pct, 0.0, 1.0);
		TargetTris = FMath::Max(4, FMath::RoundToInt32(OriginalTris * Pct));
	}
	else
	{
		return FMonolithActionResult::Error(TEXT("Either 'target_triangles' or 'target_percentage' is required"));
	}

	if (Params->HasField(TEXT("max_deviation")))
	{
		float Tolerance = static_cast<float>(Params->GetNumberField(TEXT("max_deviation")));
		FGeometryScriptSimplifyMeshOptions Opts;
		UGeometryScriptLibrary_MeshSimplifyFunctions::ApplySimplifyToTolerance(Mesh, Tolerance, Opts);
	}
	else
	{
		FGeometryScriptSimplifyMeshOptions Opts;
		UGeometryScriptLibrary_MeshSimplifyFunctions::ApplySimplifyToTriangleCount(Mesh, TargetTris, Opts);
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetNumberField(TEXT("original_triangles"), OriginalTris);
	Result->SetNumberField(TEXT("result_triangles"), Mesh->GetTriangleCount());
	Result->SetNumberField(TEXT("reduction_ratio"), OriginalTris > 0 ? 1.0 - (double)Mesh->GetTriangleCount() / OriginalTris : 0.0);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::MeshRemesh(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	if (HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'handle' is required"));
	}

	double TargetEdgeLength = Params->GetNumberField(TEXT("target_edge_length"));
	if (TargetEdgeLength <= 0.0)
	{
		return FMonolithActionResult::Error(TEXT("'target_edge_length' must be positive"));
	}

	FString Error;
	UDynamicMesh* Mesh = Pool->GetHandle(HandleName, Error);
	if (!Mesh) return FMonolithActionResult::Error(Error);

	int32 OriginalTris = Mesh->GetTriangleCount();

	FGeometryScriptRemeshOptions RemeshOpts;
	FGeometryScriptUniformRemeshOptions UniformOpts;
	UniformOpts.TargetType = EGeometryScriptUniformRemeshTargetType::TargetEdgeLength;
	UniformOpts.TargetEdgeLength = static_cast<float>(TargetEdgeLength);

	UGeometryScriptLibrary_RemeshingFunctions::ApplyUniformRemesh(Mesh, RemeshOpts, UniformOpts);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetNumberField(TEXT("original_triangles"), OriginalTris);
	Result->SetNumberField(TEXT("result_triangles"), Mesh->GetTriangleCount());
	Result->SetNumberField(TEXT("target_edge_length"), TargetEdgeLength);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::GenerateCollision(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	if (HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'handle' is required"));
	}

	FString Method = Params->HasField(TEXT("method"))
		? Params->GetStringField(TEXT("method")).ToLower()
		: TEXT("convex_decomp");

	int32 MaxHulls = Params->HasField(TEXT("max_hulls"))
		? static_cast<int32>(Params->GetNumberField(TEXT("max_hulls")))
		: 4;

	FString Error;
	UDynamicMesh* Mesh = Pool->GetHandle(HandleName, Error);
	if (!Mesh) return FMonolithActionResult::Error(Error);

	FGeometryScriptCollisionFromMeshOptions CollisionOpts;
	CollisionOpts.bEmitTransaction = false;

	if (Method == TEXT("convex_decomp"))
	{
		CollisionOpts.Method = EGeometryScriptCollisionGenerationMethod::ConvexHulls;
		CollisionOpts.MaxConvexHullsPerMesh = MaxHulls;
	}
	else if (Method == TEXT("auto_box"))
	{
		CollisionOpts.Method = EGeometryScriptCollisionGenerationMethod::AlignedBoxes;
	}
	else if (Method == TEXT("auto_sphere"))
	{
		CollisionOpts.Method = EGeometryScriptCollisionGenerationMethod::MinimalSpheres;
	}
	else if (Method == TEXT("auto_capsule"))
	{
		CollisionOpts.Method = EGeometryScriptCollisionGenerationMethod::Capsules;
	}
	else if (Method == TEXT("simplified"))
	{
		CollisionOpts.Method = EGeometryScriptCollisionGenerationMethod::MinVolumeShapes;
	}
	else
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown collision method '%s'. Valid: convex_decomp, auto_box, auto_sphere, auto_capsule, simplified"), *Method));
	}

	FGeometryScriptSimpleCollision Collision = UGeometryScriptLibrary_CollisionFunctions::GenerateCollisionFromMesh(
		Mesh, CollisionOpts);

	// BUG (known): The collision data computed above is discarded after this function returns.
	// It is NOT stored on the handle or applied to any StaticMesh.
	// This is harmless in practice because save_handle now auto-generates collision
	// (added in Task 4 of the proc-geo overhaul). Users wanting custom collision can
	// use the collision/max_hulls params on save_handle instead.
	// TODO: Phase 2 fix — store collision in a TMap<FString, FGeometryScriptSimpleCollision>
	// on the pool so save_handle can use pre-generated collision instead of re-computing.

	// Report collision shape counts so the user gets useful feedback
	int32 ShapeCount = Collision.AggGeom.BoxElems.Num()
		+ Collision.AggGeom.SphereElems.Num()
		+ Collision.AggGeom.SphylElems.Num()
		+ Collision.AggGeom.ConvexElems.Num();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetStringField(TEXT("method"), Method);
	Result->SetNumberField(TEXT("shape_count"), ShapeCount);
	Result->SetNumberField(TEXT("box_elements"), Collision.AggGeom.BoxElems.Num());
	Result->SetNumberField(TEXT("sphere_elements"), Collision.AggGeom.SphereElems.Num());
	Result->SetNumberField(TEXT("capsule_elements"), Collision.AggGeom.SphylElems.Num());
	Result->SetNumberField(TEXT("convex_elements"), Collision.AggGeom.ConvexElems.Num());
	Result->SetStringField(TEXT("status"), TEXT("generated"));
	Result->SetStringField(TEXT("note"), TEXT("Collision shapes computed but not stored. Use save_handle with collision param to persist collision on the saved StaticMesh."));

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::GenerateLods(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	if (HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'handle' is required"));
	}

	int32 LodCount = static_cast<int32>(Params->GetNumberField(TEXT("lod_count")));
	if (LodCount <= 0 || LodCount > 8)
	{
		return FMonolithActionResult::Error(TEXT("'lod_count' must be between 1 and 8"));
	}

	double ReductionPerLod = Params->HasField(TEXT("reduction_per_lod"))
		? Params->GetNumberField(TEXT("reduction_per_lod"))
		: 0.5;
	ReductionPerLod = FMath::Clamp(ReductionPerLod, 0.1, 0.9);

	FString Error;
	UDynamicMesh* SourceMesh = Pool->GetHandle(HandleName, Error);
	if (!SourceMesh) return FMonolithActionResult::Error(Error);

	int32 BaseTris = SourceMesh->GetTriangleCount();
	TArray<TSharedPtr<FJsonValue>> LodArray;

	for (int32 Lod = 1; Lod <= LodCount; ++Lod)
	{
		FString LodHandleName = FString::Printf(TEXT("%s_LOD%d"), *HandleName, Lod);

		// Remove existing LOD handle if present
		Pool->ReleaseHandle(LodHandleName);

		// Create LOD handle as copy of source
		FString CreateError;
		if (!Pool->CreateHandle(LodHandleName, FString::Printf(TEXT("internal:lod:%s:%d"), *HandleName, Lod), CreateError))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to create LOD handle: %s"), *CreateError));
		}

		UDynamicMesh* LodMesh = Pool->GetHandle(LodHandleName, CreateError);
		if (!LodMesh)
		{
			return FMonolithActionResult::Error(TEXT("Failed to get LOD handle"));
		}

		// Copy source mesh data
		LodMesh->SetMesh(SourceMesh->GetMeshRef());

		// Simplify progressively
		int32 TargetTris = FMath::Max(4, FMath::RoundToInt32(BaseTris * FMath::Pow(ReductionPerLod, Lod)));

		FGeometryScriptSimplifyMeshOptions SimplifyOpts;
		UGeometryScriptLibrary_MeshSimplifyFunctions::ApplySimplifyToTriangleCount(LodMesh, TargetTris, SimplifyOpts);

		TSharedPtr<FJsonObject> LodInfo = MakeShared<FJsonObject>();
		LodInfo->SetStringField(TEXT("handle"), LodHandleName);
		LodInfo->SetNumberField(TEXT("lod_level"), Lod);
		LodInfo->SetNumberField(TEXT("target_triangles"), TargetTris);
		LodInfo->SetNumberField(TEXT("actual_triangles"), LodMesh->GetTriangleCount());
		LodArray.Add(MakeShared<FJsonValueObject>(LodInfo));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("source_handle"), HandleName);
	Result->SetNumberField(TEXT("source_triangles"), BaseTris);
	Result->SetNumberField(TEXT("lod_count"), LodCount);
	Result->SetNumberField(TEXT("reduction_per_lod"), ReductionPerLod);
	Result->SetArrayField(TEXT("lods"), LodArray);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::FillHoles(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	if (HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'handle' is required"));
	}

	FString Error;
	UDynamicMesh* Mesh = Pool->GetHandle(HandleName, Error);
	if (!Mesh) return FMonolithActionResult::Error(Error);

	int32 OriginalTris = Mesh->GetTriangleCount();

	FGeometryScriptFillHolesOptions FillOpts;
	FillOpts.FillMethod = EGeometryScriptFillHolesMethod::Automatic;
	int32 NumFilledHoles = 0;
	int32 NumFailedHoleFills = 0;

	UGeometryScriptLibrary_MeshRepairFunctions::FillAllMeshHoles(
		Mesh, FillOpts, NumFilledHoles, NumFailedHoleFills);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetNumberField(TEXT("holes_filled"), NumFilledHoles);
	Result->SetNumberField(TEXT("holes_failed"), NumFailedHoleFills);
	Result->SetNumberField(TEXT("original_triangles"), OriginalTris);
	Result->SetNumberField(TEXT("result_triangles"), Mesh->GetTriangleCount());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::ComputeUvs(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	if (HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'handle' is required"));
	}

	FString Method = Params->HasField(TEXT("method"))
		? Params->GetStringField(TEXT("method")).ToLower()
		: TEXT("auto_unwrap");

	int32 UVChannel = Params->HasField(TEXT("uv_channel"))
		? static_cast<int32>(Params->GetNumberField(TEXT("uv_channel")))
		: 0;

	FString Error;
	UDynamicMesh* Mesh = Pool->GetHandle(HandleName, Error);
	if (!Mesh) return FMonolithActionResult::Error(Error);

	FGeometryScriptMeshSelection EmptySelection; // No selection = operate on whole mesh

	if (Method == TEXT("auto_unwrap"))
	{
		FGeometryScriptXAtlasOptions XAtlasOpts;
		UGeometryScriptLibrary_MeshUVFunctions::AutoGenerateXAtlasMeshUVs(Mesh, UVChannel, XAtlasOpts);
	}
	else if (Method == TEXT("box_project"))
	{
		UGeometryScriptLibrary_MeshUVFunctions::SetMeshUVsFromBoxProjection(
			Mesh, UVChannel, FTransform::Identity, EmptySelection);
	}
	else if (Method == TEXT("planar_project"))
	{
		UGeometryScriptLibrary_MeshUVFunctions::SetMeshUVsFromPlanarProjection(
			Mesh, UVChannel, FTransform::Identity, EmptySelection);
	}
	else if (Method == TEXT("cylinder_project"))
	{
		UGeometryScriptLibrary_MeshUVFunctions::SetMeshUVsFromCylinderProjection(
			Mesh, UVChannel, FTransform::Identity, EmptySelection);
	}
	else
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown UV method '%s'. Valid: auto_unwrap, box_project, planar_project, cylinder_project"), *Method));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetStringField(TEXT("method"), Method);
	Result->SetNumberField(TEXT("uv_channel"), UVChannel);
	Result->SetStringField(TEXT("status"), TEXT("computed"));

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithMeshOperationActions::MirrorMesh(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(TEXT("Enable the GeometryScripting plugin in your .uproject to use mesh operations."));
	}

	FString HandleName = Params->GetStringField(TEXT("handle"));
	if (HandleName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'handle' is required"));
	}

	FString Axis = Params->GetStringField(TEXT("axis")).ToUpper();
	if (Axis != TEXT("X") && Axis != TEXT("Y") && Axis != TEXT("Z"))
	{
		return FMonolithActionResult::Error(TEXT("'axis' must be X, Y, or Z"));
	}

	bool bWeld = Params->HasField(TEXT("weld")) ? Params->GetBoolField(TEXT("weld")) : true;

	FString Error;
	UDynamicMesh* Mesh = Pool->GetHandle(HandleName, Error);
	if (!Mesh) return FMonolithActionResult::Error(Error);

	int32 OriginalTris = Mesh->GetTriangleCount();

	// Build mirror transform: mirror plane normal determines the mirror axis
	// ApplyMeshMirror mirrors across a plane defined by MirrorFrame
	// The plane normal is the local X axis of the frame by convention
	FTransform MirrorFrame = FTransform::Identity;
	if (Axis == TEXT("X"))
	{
		// Mirror plane has normal along X — identity frame works (X-axis is forward)
		MirrorFrame = FTransform::Identity;
	}
	else if (Axis == TEXT("Y"))
	{
		// Rotate so the plane normal (local X) points along world Y
		MirrorFrame.SetRotation(FQuat(FVector::UpVector, FMath::DegreesToRadians(90.0f)));
	}
	else if (Axis == TEXT("Z"))
	{
		// Rotate so the plane normal (local X) points along world Z
		MirrorFrame.SetRotation(FQuat(FVector::RightVector, FMath::DegreesToRadians(-90.0f)));
	}

	FGeometryScriptMeshMirrorOptions MirrorOpts;
	MirrorOpts.bApplyPlaneCut = true;
	MirrorOpts.bWeldAlongPlane = bWeld;

	UGeometryScriptLibrary_MeshBooleanFunctions::ApplyMeshMirror(
		Mesh, MirrorFrame, MirrorOpts);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("handle"), HandleName);
	Result->SetStringField(TEXT("axis"), Axis);
	Result->SetBoolField(TEXT("weld"), bWeld);
	Result->SetNumberField(TEXT("original_triangles"), OriginalTris);
	Result->SetNumberField(TEXT("result_triangles"), Mesh->GetTriangleCount());

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_GEOMETRYSCRIPT
