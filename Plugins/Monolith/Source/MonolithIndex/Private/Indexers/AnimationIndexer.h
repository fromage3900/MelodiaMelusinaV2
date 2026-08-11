#pragma once

#include "MonolithIndexer.h"

/**
 * Indexes animation assets: AnimSequence, AnimMontage, BlendSpace, and PoseAsset.
 * Runs as a post-processing step on the game thread (requires asset loading).
 * Uses sentinel class "__Animations__" for dispatch.
 */
class FAnimationIndexer : public IMonolithIndexer
{
public:
	virtual TArray<FString> GetSupportedClasses() const override
	{
		return { TEXT("__Animations__") };
	}

	virtual bool IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId) override;
	virtual FString GetName() const override { return TEXT("AnimationIndexer"); }
	virtual bool IsSentinel() const override { return true; }

	// Public wrappers for SEH-safe dispatch (called from free function via void* context)
	void IndexAnimSequencePublic(class UAnimSequence* A, FMonolithIndexDatabase& DB, int64 Id) { IndexAnimSequence(A, DB, Id); }
	void IndexAnimMontagePublic(class UAnimMontage* A, FMonolithIndexDatabase& DB, int64 Id) { IndexAnimMontage(A, DB, Id); }
	void IndexBlendSpacePublic(class UBlendSpace* A, FMonolithIndexDatabase& DB, int64 Id) { IndexBlendSpace(A, DB, Id); }
	void IndexPoseAssetPublic(class UPoseAsset* A, FMonolithIndexDatabase& DB, int64 Id) { IndexPoseAsset(A, DB, Id); }

private:
	void IndexAnimSequence(class UAnimSequence* AnimSeq, FMonolithIndexDatabase& DB, int64 AssetId);
	void IndexAnimMontage(class UAnimMontage* Montage, FMonolithIndexDatabase& DB, int64 AssetId);
	void IndexBlendSpace(class UBlendSpace* BlendSpace, FMonolithIndexDatabase& DB, int64 AssetId);
	void IndexPoseAsset(class UPoseAsset* PoseAsset, FMonolithIndexDatabase& DB, int64 AssetId);
	static FString NotifiesToJson(const TArray<struct FAnimNotifyEvent>& Notifies);
};
