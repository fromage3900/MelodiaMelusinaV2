#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes Niagara particle systems: emitter names, sim targets (CPU/GPU),
 * fixed bounds, compile status, and renderer info.
 * Runs as a post-processing step on the game thread (requires asset loading).
 * Uses sentinel class "__Niagara__" for dispatch.
 */
class FNiagaraIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__Niagara__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("NiagaraIndexer"); }
	virtual bool IsSentinel() const override { return true; }

private:
	void IndexNiagaraSystem(class UNiagaraSystem* System, FMonolithIndexDatabase& DB, int64 AssetId);
};
