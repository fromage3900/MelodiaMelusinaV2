#include "MonolithMelusinaClipGuard.h"

#include "Animation/AnimSequence.h"
#include "Animation/AnimData/IAnimationDataModel.h"
#include "Animation/BlendSpace.h"
#include "Animation/Skeleton.h"
#include "AnimPose.h"
#include "Engine/SkeletalMesh.h"

bool MonolithMelusinaClipGuard::IsCanonicalSkeleton(const USkeleton* Skeleton)
{
	return Skeleton && Skeleton->GetPathName() == TEXT("/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton");
}

bool MonolithMelusinaClipGuard::Validate(const UAnimationAsset* Asset, const USkeleton* TargetSkeleton, FString& Error)
{
	if (!IsCanonicalSkeleton(TargetSkeleton)) return true;
	auto Reject = [&](const FString& Reason)
	{
		Error = FString::Printf(TEXT("Melusina clip preflight rejected %s: %s. Existing binding unchanged; repair a duplicate and revalidate, preserving authored rotations and frozen originals."),
			*GetPathNameSafe(Asset), *Reason);
		return false;
	};
	if (!Asset || Asset->GetSkeleton() != TargetSkeleton)
		return Reject(TEXT("canonical skeleton mismatch or missing animation"));
	if (const UBlendSpace* Blend = Cast<UBlendSpace>(Asset))
	{
		if (Blend->GetBlendSamples().IsEmpty()) return Reject(TEXT("blend space has no animation samples"));
		for (const FBlendSample& Sample : Blend->GetBlendSamples())
		{
			if (!Validate(Sample.Animation, TargetSkeleton, Error)) return false;
		}
		return true;
	}
	const UAnimSequence* Sequence = Cast<UAnimSequence>(Asset);
	if (!Sequence) return Reject(TEXT("unsupported animation type for checked state assignment"));
	const IAnimationDataModel* Model = Sequence->GetDataModel();
	if (!Model || Model->GetNumberOfKeys() <= 0) return Reject(TEXT("missing animation key data"));
	for (FName Bone : { FName(TEXT("arm_stretch_l")), FName(TEXT("forearm_stretch_l")), FName(TEXT("arm_stretch_r")), FName(TEXT("forearm_stretch_r")) })
		if (!Model->IsValidBoneTrackName(Bone)) return Reject(FString::Printf(TEXT("missing authored arm track %s; reference-pose fallback is unsafe"), *Bone.ToString()));
	FAnimPoseEvaluationOptions Options;
	// Skeleton-only evaluation can accept translations that the actual body
	// redistributes back to the rejected 34.789/9.520 cm shoulder convention.
	USkeletalMesh* Body = LoadObject<USkeletalMesh>(nullptr,
		TEXT("/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body.SK_Melusina_V2_Body"));
	if (!Body || Body->GetSkeleton() != TargetSkeleton)
		return Reject(TEXT("canonical body missing or skeleton mismatch; no skeleton-only fallback"));
	Options.OptionalSkeletalMesh = Body;
	Options.EvaluationType = EAnimDataEvalType::Raw;
	Options.bShouldRetarget = true;
	Options.bExtractRootMotion = false;
	Options.bIncorporateRootMotionIntoPose = true;
	Options.bRetrieveAdditiveAsFullPose = true;
	Options.bEvaluateCurves = false;
	const FName Bones[] = { TEXT("root"), TEXT("shoulder_l"), TEXT("arm_stretch_l"), TEXT("forearm_stretch_l"), TEXT("hand_l"),
		TEXT("shoulder_r"), TEXT("arm_stretch_r"), TEXT("forearm_stretch_r"), TEXT("hand_r") };
	const double Expected[] = { 15.774, 28.561, 28.615 };
	for (int32 Frame = 0; Frame < Model->GetNumberOfKeys(); ++Frame)
	{
		FAnimPose Pose;
		UAnimPoseExtensions::GetAnimPoseAtFrame(Sequence, Frame, Options, Pose);
		if (!Pose.IsValid()) return Reject(FString::Printf(TEXT("invalid evaluated pose at key %d"), Frame));
		TArray<FName> Present;
		UAnimPoseExtensions::GetBoneNames(Pose, Present);
		for (FName Bone : Bones)
			if (!Present.Contains(Bone)) return Reject(FString::Printf(TEXT("missing bone %s at key %d"), *Bone.ToString(), Frame));
		for (FName RootBone : { FName(TEXT("root")), FName(TEXT("root_x")) })
		{
			if (!Present.Contains(RootBone)) return Reject(FString::Printf(TEXT("missing bone %s"), *RootBone.ToString()));
			const FTransform Root = UAnimPoseExtensions::GetBonePose(Pose, RootBone, EAnimPoseSpaces::Local);
			if (Root.ContainsNaN() || !Root.GetScale3D().Equals(FVector::OneVector, 0.01))
				return Reject(FString::Printf(TEXT("%s scale %s at key %d; require unit scale"), *RootBone.ToString(), *Root.GetScale3D().ToString(), Frame));
		}
		for (int32 Side = 0; Side < 2; ++Side)
		{
			for (int32 Segment = 0; Segment < 3; ++Segment)
			{
				const FTransform A = UAnimPoseExtensions::GetBonePose(Pose, Bones[1 + Side * 4 + Segment], EAnimPoseSpaces::World);
				const FTransform B = UAnimPoseExtensions::GetBonePose(Pose, Bones[2 + Side * 4 + Segment], EAnimPoseSpaces::World);
				const double Length = FVector::Distance(A.GetTranslation(), B.GetTranslation());
				if (A.ContainsNaN() || B.ContainsNaN() || !FMath::IsFinite(Length) || FMath::Abs(Length - Expected[Segment]) > 1.0)
					return Reject(FString::Printf(TEXT("%s arm segment %d = %.3f cm at key %d; require %.3f +/- 1 cm"),
						Side == 0 ? TEXT("left") : TEXT("right"), Segment, Length, Frame, Expected[Segment]));
			}
		}
	}
	return true;
}
