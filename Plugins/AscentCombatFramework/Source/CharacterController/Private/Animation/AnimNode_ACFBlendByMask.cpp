// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/AnimNode_ACFBlendByMask.h"

#include "Animation/ACFBoneBlendMask.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimTypes.h"
#include "Animation/AttributesRuntime.h"
#include "AnimationRuntime.h"
#include "BonePose.h"
#include "Math/ScalarRegister.h"
#include "Misc/MemStack.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(AnimNode_ACFBlendByMask)

void FAnimNode_ACFBlendByMask::Initialize_AnyThread(const FAnimationInitializeContext& Context)
{
	DECLARE_SCOPE_HIERARCHICAL_COUNTER_ANIMNODE(Initialize_AnyThread)
	FAnimNode_Base::Initialize_AnyThread(Context);

	BasePose.Initialize(Context);
	BlendPose.Initialize(Context);

	bSnapWeights = true;
}

void FAnimNode_ACFBlendByMask::CacheBones_AnyThread(const FAnimationCacheBonesContext& Context)
{
	DECLARE_SCOPE_HIERARCHICAL_COUNTER_ANIMNODE(CacheBones_AnyThread)
	BasePose.CacheBones(Context);
	BlendPose.CacheBones(Context);
}

void FAnimNode_ACFBlendByMask::RebuildTargetBoneWeights(const FBoneContainer& RequiredBones)
{
	const int32 NumBones = RequiredBones.GetCompactPoseNumBones();

	// On LOD changes the compact pose indices are remapped, so interpolating from
	// the previous weights would blend unrelated bones: snap instead
	if (RequiredBones.GetSerialNumber() != RequiredBonesSerialNumber)
	{
		RequiredBonesSerialNumber = RequiredBones.GetSerialNumber();
		bSnapWeights = true;
	}

	TargetBoneWeights.Reset(NumBones);
	TargetBoneWeights.AddZeroed(NumBones);
	TargetBlendSpaces.Reset(NumBones);
	TargetBlendSpaces.AddDefaulted(NumBones);

	const UACFBoneBlendMask* Mask = BlendMask;
	if (!Mask || Mask->Branches.IsEmpty())
	{
		return;
	}

	TMap<FName, float> BranchAlphas;
	BranchAlphas.Reserve(Mask->Branches.Num());
	TMap<FName, EACFMaskBlendSpace> BranchSpaces;
	BranchSpaces.Reserve(Mask->Branches.Num());
	for (const FACFBoneBlendBranch& Branch : Mask->Branches)
	{
		if (Branch.Bone.BoneName != NAME_None)
		{
			BranchAlphas.Add(Branch.Bone.BoneName, FMath::Clamp(Branch.Alpha, 0.f, 1.f));
			BranchSpaces.Add(Branch.Bone.BoneName, Branch.BlendSpace);
		}
	}

	const FReferenceSkeleton& RefSkeleton = RequiredBones.GetReferenceSkeleton();

	// Compact pose bones are sorted parents-first, so each bone can inherit the
	// weight of its parent unless it is a branch point itself. This gives deeper
	// branch points priority over parent ones.
	for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
	{
		const FCompactPoseBoneIndex CompactIndex(BoneIndex);
		const FName BoneName = RefSkeleton.GetBoneName(RequiredBones.MakeMeshPoseIndex(CompactIndex).GetInt());

		if (const float* BranchAlpha = BranchAlphas.Find(BoneName))
		{
			TargetBoneWeights[BoneIndex] = *BranchAlpha;
			TargetBlendSpaces[BoneIndex] = BranchSpaces.FindRef(BoneName);
		}
		else
		{
			const FCompactPoseBoneIndex ParentIndex = RequiredBones.GetParentBoneIndex(CompactIndex);
			if (ParentIndex != INDEX_NONE)
			{
				TargetBoneWeights[BoneIndex] = TargetBoneWeights[ParentIndex.GetInt()];
				TargetBlendSpaces[BoneIndex] = TargetBlendSpaces[ParentIndex.GetInt()];
			}
		}
	}
}

void FAnimNode_ACFBlendByMask::Update_AnyThread(const FAnimationUpdateContext& Context)
{
	DECLARE_SCOPE_HIERARCHICAL_COUNTER_ANIMNODE(Update_AnyThread)

	bBlendPoseRelevant = false;
	float RootMotionWeight = 0.f;

	if (IsLODEnabled(Context.AnimInstanceProxy))
	{
		GetEvaluateGraphExposedInputs().Execute(Context);

		// Rebuilt every update so both mask swaps (pin) and value changes inside the
		// same asset are picked up; the interpolation below smooths any change
		RebuildTargetBoneWeights(Context.AnimInstanceProxy->GetRequiredBones());

		const int32 NumBones = TargetBoneWeights.Num();
		if (bSnapWeights || BlendTime <= UE_KINDA_SMALL_NUMBER)
		{
			CurrentBoneWeights = TargetBoneWeights;
			bSnapWeights = false;
		}
		else
		{
			CurrentBoneWeights.SetNumZeroed(NumBones);
			const float DeltaTime = Context.GetDeltaTime();
			const float InterpSpeed = 1.f / BlendTime;
			for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
			{
				CurrentBoneWeights[BoneIndex] = FMath::FInterpConstantTo(CurrentBoneWeights[BoneIndex], TargetBoneWeights[BoneIndex], DeltaTime, InterpSpeed);
			}
		}

		MaxCurrentWeight = 0.f;
		for (const float Weight : CurrentBoneWeights)
		{
			MaxCurrentWeight = FMath::Max(MaxCurrentWeight, Weight);
		}

		bBlendPoseRelevant = FAnimWeight::IsRelevant(MaxCurrentWeight);
		if (bBlendPoseRelevant)
		{
			// In Override mode the blend pose takes over root motion in proportion to the
			// root bone weight; in Additive mode root motion is left to the base pose
			if (BlendMode == EACFMaskBlendMode::Override && CurrentBoneWeights.Num() > 0)
			{
				RootMotionWeight = CurrentBoneWeights[0];
			}

			BlendPose.Update(Context.FractionalWeightAndRootMotion(MaxCurrentWeight, RootMotionWeight));
		}
	}

	const float BaseRootMotionWeight = 1.f - RootMotionWeight;
	if (BaseRootMotionWeight < 1.f - ZERO_ANIMWEIGHT_THRESH)
	{
		BasePose.Update(Context.FractionalWeightAndRootMotion(1.f, BaseRootMotionWeight));
	}
	else
	{
		BasePose.Update(Context);
	}
}

void FAnimNode_ACFBlendByMask::Evaluate_AnyThread(FPoseContext& Output)
{
	DECLARE_SCOPE_HIERARCHICAL_COUNTER_ANIMNODE(Evaluate_AnyThread)

	BasePose.Evaluate(Output);

	const int32 NumBones = Output.Pose.GetNumBones();
	if (!bBlendPoseRelevant || CurrentBoneWeights.Num() != NumBones)
	{
		return;
	}

	// Only a pre-authored additive input expects an additive pose; Override and DynamicAdditive take a normal full pose.
	const bool bPreAuthoredAdditive = (BlendMode == EACFMaskBlendMode::Additive);
	const bool bDynamicAdditive = (BlendMode == EACFMaskBlendMode::DynamicAdditive);

	FPoseContext BlendPoseContext(Output, bPreAuthoredAdditive);
	BlendPose.Evaluate(BlendPoseContext);

	// DynamicAdditive extracts the blend pose's additive delta relative to a neutral reference pose,
	// chosen via ReferencePoseSource (editor setting, no pin), then layers it on top of the live base.
	FPoseContext RefPoseContext(Output);
	if (bDynamicAdditive)
	{
		switch (ReferencePoseSource)
		{
		case EACFMaskReferencePose::CurrentBasePose:
			RefPoseContext.Pose.CopyBonesFrom(Output.Pose);
			RefPoseContext.Curve.CopyFrom(Output.Curve);
			break;

		case EACFMaskReferencePose::AnimSequenceFirstFrame:
			if (ReferencePoseAnimation)
			{
				FAnimationPoseData RefPoseData(RefPoseContext);
				ReferencePoseAnimation->GetAnimationPose(RefPoseData, FAnimExtractContext(0.0, false));
			}
			else
			{
				RefPoseContext.ResetToRefPose();
			}
			break;

		case EACFMaskReferencePose::SkeletonReferencePose:
		default:
			RefPoseContext.ResetToRefPose();
			break;
		}
	}

	const bool bNeedsMeshSpaceBlend = !bPreAuthoredAdditive && TargetBlendSpaces.Contains(EACFMaskBlendSpace::MeshSpace);

	// Local-space pass: all bones for additive modes, only local-space branches for the others.
	for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
	{
		const float BoneWeight = CurrentBoneWeights[BoneIndex];
		if (BoneWeight <= ZERO_ANIMWEIGHT_THRESH)
		{
			continue;
		}

		// Mesh-space branches are handled in the component-space pass below.
		if (!bPreAuthoredAdditive && TargetBlendSpaces.IsValidIndex(BoneIndex) && TargetBlendSpaces[BoneIndex] == EACFMaskBlendSpace::MeshSpace)
		{
			continue;
		}

		const FCompactPoseBoneIndex CompactIndex(BoneIndex);
		FTransform& OutBone = Output.Pose[CompactIndex];
		const FTransform& LayerBone = BlendPoseContext.Pose[CompactIndex];

		if (bPreAuthoredAdditive)
		{
			FTransform::BlendFromIdentityAndAccumulate(OutBone, LayerBone, ScalarRegister(BoneWeight));
		}
		else if (bDynamicAdditive)
		{
			// Build the additive delta on the fly: blend pose relative to the neutral reference pose,
			// then accumulate a fraction of it on top of the live base. Preserves base motion -> no stiffness.
			FTransform AdditiveDelta = LayerBone;
			FAnimationRuntime::ConvertTransformToAdditive(AdditiveDelta, RefPoseContext.Pose[CompactIndex]);
			FTransform::BlendFromIdentityAndAccumulate(OutBone, AdditiveDelta, ScalarRegister(BoneWeight));
		}
		else
		{
			OutBone.BlendWith(LayerBone, BoneWeight);
		}
	}

	if (bNeedsMeshSpaceBlend)
	{
		FCSPose<FCompactPose> OutputCSPose;
		FCSPose<FCompactPose> BlendCSPose;
		OutputCSPose.InitPose(Output.Pose);
		BlendCSPose.InitPose(BlendPoseContext.Pose);

		FCSPose<FCompactPose> RefCSPose;
		if (bDynamicAdditive)
		{
			RefCSPose.InitPose(RefPoseContext.Pose);
		}

		for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
		{
			const float BoneWeight = CurrentBoneWeights[BoneIndex];
			if (BoneWeight <= ZERO_ANIMWEIGHT_THRESH || !TargetBlendSpaces.IsValidIndex(BoneIndex) || TargetBlendSpaces[BoneIndex] != EACFMaskBlendSpace::MeshSpace)
			{
				continue;
			}

			const FCompactPoseBoneIndex CompactIndex(BoneIndex);
			const FTransform BaseCS = OutputCSPose.GetComponentSpaceTransform(CompactIndex);
			const FTransform BlendCS = BlendCSPose.GetComponentSpaceTransform(CompactIndex);

			FTransform NewCS = BaseCS;
			if (bDynamicAdditive)
			{
				// Mesh-space rotation additive: add a fraction of the blend pose's rotation offset
				// relative to the neutral reference, on top of the live base (like ApplyMeshSpaceAdditive).
				const FQuat RefRot = RefCSPose.GetComponentSpaceTransform(CompactIndex).GetRotation();
				const FQuat DeltaRot = BlendCS.GetRotation() * RefRot.Inverse();
				const FQuat ScaledDelta = FQuat::Slerp(FQuat::Identity, DeltaRot, BoneWeight);
				NewCS.SetRotation((ScaledDelta * BaseCS.GetRotation()).GetNormalized());
			}
			else
			{
				NewCS.BlendWith(BlendCS, BoneWeight);
			}
			OutputCSPose.SetComponentSpaceTransform(CompactIndex, NewCS);
		}

		FCSPose<FCompactPose>::ConvertComponentPosesToLocalPosesSafe(OutputCSPose, Output.Pose);
	}

	// Curves
	if (bPreAuthoredAdditive)
	{
		Output.Curve.Accumulate(BlendPoseContext.Curve, MaxCurrentWeight);
	}
	else
	{
		Output.Curve.LerpTo(BlendPoseContext.Curve, MaxCurrentWeight);
	}

	// Attributes
	if (BlendPoseContext.CustomAttributes.ContainsData())
	{
		if (bPreAuthoredAdditive)
		{
			UE::Anim::Attributes::AccumulateAttributes(BlendPoseContext.CustomAttributes, Output.CustomAttributes, MaxCurrentWeight, AAT_LocalSpaceBase);
		}
		else
		{
			UE::Anim::FStackAttributeContainer BaseAttributes;
			BaseAttributes.MoveFrom(Output.CustomAttributes);
			UE::Anim::Attributes::BlendAttributesPerBone(BaseAttributes, BlendPoseContext.CustomAttributes, CurrentBoneWeights, Output.CustomAttributes);
		}
	}

	Output.Pose.NormalizeRotations();
}

void FAnimNode_ACFBlendByMask::GatherDebugData(FNodeDebugData& DebugData)
{
	DECLARE_SCOPE_HIERARCHICAL_COUNTER_ANIMNODE(GatherDebugData)

	FString DebugLine = DebugData.GetNodeName(this);
	DebugLine += FString::Printf(TEXT("(Mask: %s, Max Weight: %.2f)"), BlendMask ? *BlendMask->GetName() : TEXT("None"), MaxCurrentWeight);
	DebugData.AddDebugItem(DebugLine);

	BasePose.GatherDebugData(DebugData.BranchFlow(1.f));
	BlendPose.GatherDebugData(DebugData.BranchFlow(MaxCurrentWeight));
}
