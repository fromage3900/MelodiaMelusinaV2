#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes the project's C++ source files (.h/.cpp) for UE macro-decorated symbols.
 * Scans Source/ directory and uses regex to extract UCLASS, USTRUCT, UENUM,
 * UFUNCTION, and UPROPERTY declarations.
 * Uses special class name "__CppSymbols__" for dispatch.
 */
class FCppIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__CppSymbols__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("CppIndexer"); }
	virtual bool IsSentinel() const override { return true; }

private:
	/** Parse a single source file and insert discovered symbols */
	static int32 ParseSourceFile(const FString& FilePath, const FString& RelativePath, FMonolithIndexDatabase& DB);
};
