#pragma once

#include "MonolithIndexer.h"

/**
 * Post-pass indexer that builds the mesh_catalog table.
 * Uses sentinel class __MeshCatalog__ so it runs as a dispatch block
 * AFTER the generic asset pass (StaticMesh assets already in DB).
 * Iterates all StaticMesh assets via Asset Registry, loads each,
 * extracts bounds/tri count/collision/LODs, and inserts into mesh_catalog.
 */
class FMeshCatalogIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__MeshCatalog__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("MeshCatalogIndexer"); }
	virtual bool IsSentinel() const override { return true; }

	/** Set the content root paths to scan (e.g. /Game, /PluginName). */
	void SetIndexedPaths(const TArray<FName>& InPaths) { IndexedPaths = InPaths; }

private:
	TArray<FName> IndexedPaths;
};
