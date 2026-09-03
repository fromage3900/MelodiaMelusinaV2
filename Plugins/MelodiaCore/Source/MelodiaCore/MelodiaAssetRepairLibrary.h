// Asset-repair helpers exposed to Python/Blueprint for operations the scripting API cannot do.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaAssetRepairLibrary.generated.h"

class USkeletalMesh;
class USkeleton;
class UAnimSequenceBase;
class UAnimSequence;

UCLASS()
class MELODIACORE_API UMelodiaAssetRepairLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Rebind a skeletal mesh's Skeleton reference. USkeletalMesh::Skeleton is read-only to the
	 * Python property system, so a mesh whose skeleton ref was lost (e.g. during an asset move)
	 * cannot be healed from scripting without this. Marks the package dirty; caller saves.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|AssetRepair")
	static bool SetSkeletalMeshSkeleton(USkeletalMesh* Mesh, USkeleton* Skeleton);

	/**
	 * Rebind an AnimSequence's Skeleton reference. Same read-only wall as above ΓÇö UAnimSequenceBase
	 * exposes GetSkeleton() to Python but not a setter. Keyframe data is untouched by this call; it
	 * only repoints which USkeleton the sequence considers itself compatible with. Does NOT retarget
	 * bone data ΓÇö only use this when the sequence's keys were already authored against (or are
	 * numerically compatible with) the target skeleton and the reference itself is simply broken/null.
	 * Marks the package dirty; caller saves.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|AssetRepair")
	static bool SetAnimSequenceSkeleton(UAnimSequenceBase* Sequence, USkeleton* Skeleton);

	/**
	 * Keep an inclusive frame window and remove all keys outside it. This exposes the engine's
	 * animation-data trim operation to editor automation without altering the source sequence.
	 * Callers should duplicate the source asset first.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|AssetRepair")
	static bool KeepAnimSequenceFrameRange(UAnimSequence* Sequence, int32 FirstFrame, int32 LastFrame);
};
