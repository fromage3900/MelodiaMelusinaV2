#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes the Asset Registry dependency graph.
 * Runs after all other indexers (needs all assets in DB).
 * Uses special class name "__Dependencies__" for dispatch.
 */
class FDependencyIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__Dependencies__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("DependencyIndexer"); }
	virtual bool IsSentinel() const override { return true; }

	/** Set of valid path prefixes for indexing */
	TArray<FName> IndexedPaths;

	/** Set indexed paths. Called before IndexAsset. */
	void SetIndexedPaths(const TArray<FName>& InPaths) { IndexedPaths = InPaths; }
};
