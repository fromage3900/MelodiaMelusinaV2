#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes project .ini config files into the configs table.
 * Enumerates Config/ directory, parses INI sections/keys,
 * and classifies each file by layer (Base/Default/Platform/User).
 * Uses special class name "__Configs__" for dispatch (like DependencyIndexer).
 */
class FConfigIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__Configs__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("ConfigIndexer"); }
	virtual bool IsSentinel() const override { return true; }

private:
	/** Determine the config layer from the file path/name */
	static FString ClassifyLayer(const FString& FilePath);

	/** Parse a single .ini file and insert its entries into the DB */
	static int32 ParseAndInsertIniFile(const FString& FilePath, FMonolithIndexDatabase& DB);
};
