#pragma once

#if WITH_METASOUND

#include "MonolithIndexer.h"

class UMetaSoundSource;
class UMetaSoundPatch;

/**
 * Indexes MetaSound assets (UMetaSoundSource + UMetaSoundPatch): graph nodes,
 * edges (connections), variables, dependencies, and class metadata.
 *
 * Walks the read-only FMetasoundFrontendDocument exposed by
 * IMetaSoundDocumentInterface::GetConstDocument() — does NOT mutate asset
 * state (the writer-side actions in MonolithAudio use the builder subsystem
 * for that). Iterates the root graph's pages via
 * FMetasoundFrontendGraphClass::IterateGraphPages.
 *
 * Sentinel-class registration mirrors FNiagaraIndexer — it owns its own
 * AssetRegistry enumeration in IndexAsset, runs as a post-pass on the game
 * thread, and uses FMonolithMemoryHelper for batched GC + editor yielding.
 */
class FMetaSoundIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__MetaSound__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("MetaSoundIndexer"); }
	virtual bool IsSentinel() const override { return true; }

private:
	/**
	 * Index one MetaSound asset (Source or Patch). Resolves the document via
	 * IMetaSoundDocumentInterface and walks the root graph pages.
	 */
	void IndexMetaSoundAsset(UObject* MetaSoundAsset, const FString& AssetClassLabel, FMonolithIndexDatabase& DB, int64 AssetId);
};

#endif // WITH_METASOUND
