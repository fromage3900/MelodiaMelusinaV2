#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 1: Mesh Inspection Actions (12 read-only actions)
 * Provides mesh info, bounds, materials, LODs, collision, UVs,
 * quality analysis, comparison, vertex data, and catalog queries.
 */
class FMonolithMeshInspectionActions
{
public:
	/** Register all 12 inspection actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Individual mesh inspection ---
	static FMonolithActionResult GetMeshInfo(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetMeshBounds(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetMeshMaterials(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetMeshLods(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetMeshCollision(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetMeshUvs(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzeSkeletalMesh(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzeMeshQuality(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CompareMeshes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetVertexData(const TSharedPtr<FJsonObject>& Params);

	// --- Catalog queries (require MeshCatalogIndexer to have run) ---
	static FMonolithActionResult SearchMeshesBySize(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetMeshCatalogStats(const TSharedPtr<FJsonObject>& Params);
};
