#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes Blueprints: graphs, nodes, pins, connections, variables.
 * Walks every UEdGraph in the Blueprint, extracts node topology,
 * pin connections, and variable declarations.
 */
class FBlueprintIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("Blueprint"), TEXT("WidgetBlueprint"), TEXT("AnimBlueprint") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("BlueprintIndexer"); }

private:
	void IndexGraph(class UEdGraph* Graph, FMonolithIndexDatabase& DB, int64 AssetId);
	void IndexVariables(class UBlueprint* Blueprint, FMonolithIndexDatabase& DB, int64 AssetId);
};
