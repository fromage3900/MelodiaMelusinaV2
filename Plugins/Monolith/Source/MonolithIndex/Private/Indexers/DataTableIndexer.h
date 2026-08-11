#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes DataTable assets: iterates all rows, serializes field values to JSON.
 * Runs as a post-processing step on the game thread (requires asset loading).
 * Uses sentinel class "__DataTables__" for dispatch.
 */
class FDataTableIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__DataTables__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("DataTableIndexer"); }
	virtual bool IsSentinel() const override { return true; }

private:
	/** Serialize a single row struct instance to a JSON string */
	static FString RowStructToJson(const UScriptStruct* RowStruct, const void* RowData);
};
