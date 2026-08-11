#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes the Gameplay Tag hierarchy and tag references across assets.
 * Runs as a post-pass (like DependencyIndexer) using special class "__GameplayTags__".
 * Enumerates all registered tags via UGameplayTagsManager, then scans
 * asset registry tag metadata for GameplayTagContainer references.
 */
class FGameplayTagIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__GameplayTags__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("GameplayTagIndexer"); }
	virtual bool IsSentinel() const override { return true; }

private:
	/** Recursively index a tag node and its children, returns the DB id */
	int64 IndexTagNode(const struct FGameplayTagNode& Node, FMonolithIndexDatabase& DB);

	/** Scan all indexed assets for gameplay tag references in their asset registry tags */
	void ScanAssetTagReferences(FMonolithIndexDatabase& DB);
};
