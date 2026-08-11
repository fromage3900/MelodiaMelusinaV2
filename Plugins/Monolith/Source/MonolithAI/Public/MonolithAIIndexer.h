#pragma once

#include "MonolithIndexer.h"

/**
 * Sentinel deep indexer for AI assets: BehaviorTrees, BlackboardData,
 * and AIController Blueprints. Registers itself into MonolithIndex at startup.
 * Lives in MonolithAI to avoid polluting the core index with optional AI deps.
 *
 * Skeleton version -- BT, BB, Controller indexing only.
 * StateTree, EQS, SmartObject, Perception indexing added in later phases.
 */
class FAIIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__AI__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("AI"); }
	virtual bool IsSentinel() const override { return true; }

private:
	// ── Per-type indexing ──

	/** Index a single BehaviorTree asset */
	void IndexBehaviorTree(class UBehaviorTree* BT, const FString& AssetPath, FMonolithIndexDatabase& DB);

	/** Index a single BlackboardData asset */
	void IndexBlackboard(class UBlackboardData* BB, const FString& AssetPath, FMonolithIndexDatabase& DB);

	/** Index an AIController Blueprint (CDO inspection) */
	void IndexAIController(class UBlueprint* BP, const FString& AssetPath, FMonolithIndexDatabase& DB);

	// ── Helpers ──

	/** Count nodes in a BT recursively */
	static int32 CountBTNodes(const class UBTCompositeNode* RootNode);

	/** Ensure custom AI tables exist in the database */
	void EnsureTablesExist(FMonolithIndexDatabase& DB);

	bool bTablesCreated = false;
};
