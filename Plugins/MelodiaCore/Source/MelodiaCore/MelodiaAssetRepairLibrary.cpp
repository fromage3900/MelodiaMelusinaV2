#include "MelodiaAssetRepairLibrary.h"

#include "Engine/SkeletalMesh.h"
#include "Animation/Skeleton.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSequenceBase.h"
#if WITH_EDITOR
#include "Animation/AnimSequenceHelpers.h"
#endif

bool UMelodiaAssetRepairLibrary::SetSkeletalMeshSkeleton(USkeletalMesh* Mesh, USkeleton* Skeleton)
{
	if (!Mesh || !Skeleton)
	{
		return false;
	}
	Mesh->SetSkeleton(Skeleton);
	Mesh->MarkPackageDirty();
	return Mesh->GetSkeleton() == Skeleton;
}

bool UMelodiaAssetRepairLibrary::SetAnimSequenceSkeleton(UAnimSequenceBase* Sequence, USkeleton* Skeleton)
{
	if (!Sequence || !Skeleton)
	{
		return false;
	}
	Sequence->SetSkeleton(Skeleton);
	Sequence->MarkPackageDirty();
	return Sequence->GetSkeleton() == Skeleton;
}

bool UMelodiaAssetRepairLibrary::KeepAnimSequenceFrameRange(
	UAnimSequence* Sequence,
	const int32 FirstFrame,
	const int32 LastFrame)
{
#if WITH_EDITOR
	if (!Sequence)
	{
		return false;
	}

	const int32 OriginalKeyCount = Sequence->GetNumberOfSampledKeys();
	if (OriginalKeyCount <= 1 || FirstFrame < 0 || LastFrame < FirstFrame || LastFrame >= OriginalKeyCount)
	{
		return false;
	}

	Sequence->Modify();
	if (LastFrame + 1 < OriginalKeyCount)
	{
		const TRange<FFrameNumber> TailRange(
			TRangeBound<FFrameNumber>::Inclusive(LastFrame + 1),
			TRangeBound<FFrameNumber>::Exclusive(OriginalKeyCount));
		if (!UE::Anim::AnimationData::Trim(Sequence, TailRange))
		{
			return false;
		}
	}

	if (FirstFrame > 0)
	{
		const TRange<FFrameNumber> HeadRange(
			TRangeBound<FFrameNumber>::Inclusive(0),
			TRangeBound<FFrameNumber>::Exclusive(FirstFrame));
		if (!UE::Anim::AnimationData::Trim(Sequence, HeadRange))
		{
			return false;
		}
	}

	Sequence->MarkPackageDirty();
	return Sequence->GetNumberOfSampledKeys() == LastFrame - FirstFrame + 1;
#else
	return false;
#endif
}
