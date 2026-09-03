#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * ABP graph node wiring actions for Monolith — Wave 7.
 * 3 core actions: add_anim_graph_node, connect_anim_graph_pins, set_state_animation.
 * Places animation nodes inside state graphs or the main AnimGraph and wires them.
 */
class MONOLITHANIMATION_API FMonolithAbpWriteActions
{
public:
	/** Register all ABP graph wiring actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleAddAnimGraphNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConnectAnimGraphPins(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetStateAnimation(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddVariableGet(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAnimGraphNodeProperty(const TSharedPtr<FJsonObject>& Params);

	// Sprint 4 — Motion Matching AnimBP graph authoring.
	static FMonolithActionResult HandleConfigurePoseHistoryNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureMotionMatchingNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBuildMotionMatchingNode(const TSharedPtr<FJsonObject>& Params);

	// READ-ONLY — report whether the AnimGraph's Output Pose (UAnimGraphNode_Root 'Result'
	// input) is driven, and by which node/pin. Verifies the graph actually produces a pose.
	static FMonolithActionResult HandleGetAnimGraphOutputConnection(const TSharedPtr<FJsonObject>& Params);

	// Pack C — foot IK composite + post-process anim rig assignment.
	// build_foot_ik_pass        : insert a lightweight foot IK pass (2x TwoBoneIK + pelvis ModifyBone)
	//                             into the post-MM pose chain, spliced before Output Pose.
	// assign_post_process_anim_rig: set USkeletalMesh::PostProcessAnimBlueprint (post-process anim
	//                             instance class) on a mesh asset.
	static FMonolithActionResult HandleBuildFootIkPass(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAssignPostProcessAnimRig(const TSharedPtr<FJsonObject>& Params);

	// AnimGraph authoring (Group 1) — node spawn + single-input wiring wrappers over the shared
	// SpawnAndWirePoseInput helper, plus the Output-Pose write half of the existing reader.
	// add_apply_additive / add_apply_mesh_space_additive : ApplyAdditive / mesh-space sibling
	//   (shared impl, bMeshSpace flag) — wire Base/Additive, optional Alpha.
	// add_slot_node            : UAnimGraphNode_Slot, set SlotName (validated via USkeleton::ContainsSlotName).
	// add_save_cached_pose     : UAnimGraphNode_SaveCachedPose, set public CacheName, wire pose-in.
	// add_use_cached_pose      : UAnimGraphNode_UseCachedPose, reflection-write private NameOfCache.
	// set_output_pose_source   : drive the UAnimGraphNode_Root 'Result' input from an arbitrary node.
	static FMonolithActionResult HandleAddApplyAdditive(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddApplyMeshSpaceAdditive(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddSlotNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddSaveCachedPose(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddUseCachedPose(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetOutputPoseSource(const TSharedPtr<FJsonObject>& Params);

	// AnimGraph authoring (Group 2) — state-result wiring, dynamic blend-list pins, sync-group
	// settings, and per-bone layered-blend configuration.
	// set_state_result_source  : wire any node's pose-out into a state's result pin
	//   (UAnimStateNode::GetPoseSinkPinInsideState).
	// add_blend_by_int          : UAnimGraphNode_BlendListByInt grown to num_poses pose pins via
	//   the ANIMGRAPH_API AddPinToBlendList().
	// add_blend_by_enum         : UAnimGraphNode_BlendListByEnum bound to an enum, with one pose pin
	//   exposed per chosen enumerator (plus the always-present index-0 Default pin). The editor node's
	//   ExposeEnumElementAsPin / AddPinToBlendList are protected/Int-only, so the same effect is
	//   replicated externally: reflection-set the protected BoundEnum + reflection-Add each enumerator
	//   FName into the protected VisibleEnumEntries (TArray<FName>), and call the public header-inline
	//   inner Node.AddPose() per entry, then ReconstructNode(). BakeDataDuringCompilation auto-builds
	//   EnumToPoseIndex from VisibleEnumEntries; unexposed values fall through to Default (pose 0).
	// set_sync_group            : write GroupName/GroupRole/Method on an asset-player node via the
	//   inner FAnimNode_SequencePlayer/BlendSpacePlayer ENGINE_API setters (NOT FoldProperty reflection).
	// set_layered_blend_bones   : grow UAnimGraphNode_LayeredBoneBlend pins (AddPinToBlendByFilter)
	//   then write each layer's FBranchFilter{BoneName,BlendDepth} into the editfixedsize LayerSetup.
	static FMonolithActionResult HandleSetStateResultSource(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddBlendByInt(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddBlendByEnum(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetSyncGroup(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetLayeredBlendBones(const TSharedPtr<FJsonObject>& Params);

	// AnimGraph authoring (Group 3) — reflection-heavy Tier-2 nodes whose editor setters are not
	// DLL-exported (UAnimGraphNode_ControlRig / UAnimGraphNode_LinkedAnimLayer are MinimalAPI).
	// add_anim_control_rig_node : spawn UAnimGraphNode_ControlRig, reflection-write the inner
	//   FAnimNode_ControlRig::ControlRigClass (private EditAnywhere UPROPERTY) then ReconstructNode()
	//   to regenerate the rig's IO pins via CreateCustomPins(). Distinct from add_control_rig_node
	//   (the RigVM-graph action) — this is the AnimGraph-side wrapper.
	// add_linked_anim_layer     : spawn UAnimGraphNode_LinkedAnimLayer via FGraphNodeCreator, reflection-
	//   write inner Node.Layer (FName) / Node.Interface (TSubclassOf) / Node.InstanceClass, resolve and
	//   reflection-set the editor-node InterfaceGuid from the implemented anim-layer interface graph
	//   (mirrors UAnimGraphNode_LinkedAnimLayer::GetGuidForLayer), then ReconstructNode().
	static FMonolithActionResult HandleAddAnimControlRigNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddLinkedAnimLayer(const TSharedPtr<FJsonObject>& Params);
};
