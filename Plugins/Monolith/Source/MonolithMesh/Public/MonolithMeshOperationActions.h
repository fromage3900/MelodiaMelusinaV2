#if WITH_GEOMETRYSCRIPT

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class UMonolithMeshHandlePool;

/**
 * Phase 5: Mesh Operation Actions (12 actions, GeometryScript)
 * Handle pool-based mesh editing: create, release, list, save handles,
 * boolean, simplify, remesh, collision, LODs, fill holes, UVs, mirror.
 */
class FMonolithMeshOperationActions
{
public:
	/** Register all 12 operation actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

	/** Set the handle pool instance (called during module startup) */
	static void SetHandlePool(UMonolithMeshHandlePool* InPool);

private:
	static UMonolithMeshHandlePool* Pool;

	// Handle management
	static FMonolithActionResult CreateHandle(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ReleaseHandle(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ListHandles(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SaveHandle(const TSharedPtr<FJsonObject>& Params);

	// Mesh operations
	static FMonolithActionResult MeshBoolean(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult MeshSimplify(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult MeshRemesh(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GenerateCollision(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GenerateLods(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FillHoles(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ComputeUvs(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult MirrorMesh(const TSharedPtr<FJsonObject>& Params);
};

#endif // WITH_GEOMETRYSCRIPT
