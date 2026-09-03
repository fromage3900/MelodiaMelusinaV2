#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes generic asset types that don't need deep graph inspection:
 * StaticMesh, SkeletalMesh, Texture2D, SoundWave, etc.
 * Captures metadata (poly count, texture size, audio duration, etc.)
 */
class FGenericAssetIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return {
			TEXT("StaticMesh"),
			TEXT("SkeletalMesh"),
			TEXT("Texture2D"),
			TEXT("TextureCube"),
			TEXT("SoundWave"),
			TEXT("SoundCue"),
			TEXT("PhysicsAsset"),
			TEXT("Skeleton")
		};
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("GenericAssetIndexer"); }
};
