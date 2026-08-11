#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes Materials and Material Instances: expression nodes,
 * connections, parameters (scalar, vector, texture).
 */
class FMaterialIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return {
			TEXT("Material"),
			TEXT("MaterialInstanceConstant"),
			TEXT("MaterialFunction")
		};
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("MaterialIndexer"); }

private:
	void IndexMaterialExpressions(class UMaterial* Material, FMonolithIndexDatabase& DB, int64 AssetId);
	void IndexMaterialInstance(class UMaterialInstanceConstant* MIC, FMonolithIndexDatabase& DB, int64 AssetId);
};
