#include "MonolithAbpWriteActions.h"
#include "MonolithAssetUtils.h"
#include "MonolithParamSchema.h"

#include "Animation/AnimBlueprint.h"
#include "Animation/AnimInstance.h"
#include "Animation/Skeleton.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace.h"
#include "Animation/AnimationAsset.h"
#include "AnimGraphNode_Base.h"
#include "AnimGraphNode_AssetPlayerBase.h"
#include "AnimGraphNode_SequencePlayer.h"
#include "AnimGraphNode_BlendSpacePlayer.h"
#include "AnimGraphNode_TwoWayBlend.h"
#include "AnimGraphNode_BlendListByBool.h"
#include "AnimGraphNode_LayeredBoneBlend.h"
#include "AnimGraphNode_StateMachine.h"
#include "AnimGraphNode_StateResult.h"
#include "AnimGraphNode_Root.h"
#include "AnimGraphNode_TwoBoneIK.h"
#include "AnimGraphNode_ModifyBone.h"
#include "AnimGraphNode_LocalToComponentSpace.h"
#include "AnimGraphNode_ComponentToLocalSpace.h"
// AnimGraph authoring (Group 1) — additive blend / slot / cached-pose node classes.
#include "AnimGraphNode_ApplyAdditive.h"
#include "AnimGraphNode_ApplyMeshSpaceAdditive.h"
#include "AnimGraphNode_Slot.h"
#include "AnimGraphNode_SaveCachedPose.h"
#include "AnimGraphNode_UseCachedPose.h"
// AnimGraph authoring (Group 2) — blend-by-int dynamic pins, layered-bone-blend layer setup.
#include "AnimGraphNode_BlendListByInt.h"
// add_blend_by_enum — the BlendListByEnum editor node. Its inner FAnimNode_BlendListByEnum (public
// Node UPROPERTY) exposes the header-inline FAnimNode_BlendListBase::AddPose(); BoundEnum /
// VisibleEnumEntries are protected UPROPERTYs written by reflection.
#include "AnimGraphNode_BlendListByEnum.h"
// AnimGraph authoring (Group 3) — Control Rig anim node + linked anim layer.
// FAnimNode_ControlRig::ControlRigClass is a private EditAnywhere UPROPERTY — written via the inner
// ImportTextOntoStruct path (the unexported SetControlRigClass / MinimalAPI LinkedAnimLayer setters are
// avoided to dodge LNK2019 across the module boundary).
#include "AnimGraphNode_ControlRig.h"
#include "AnimGraphNode_LinkedAnimLayer.h"
#include "Animation/AnimLayerInterface.h"
#include "Engine/Blueprint.h"
// Sync-group setters live on the inner runtime structs — typed casts need these.
// FAnimNode_SequencePlayer is in Engine (Animation/...); FAnimNode_BlendSpacePlayer is in
// AnimGraphRuntime (AnimNodes/...) — NOT the editor AnimGraphNode_BlendSpacePlayer.h.
#include "Animation/AnimNode_SequencePlayer.h"
#include "AnimNodes/AnimNode_BlendSpacePlayer.h"
// FInputBlendPose / FBranchFilter for set_layered_blend_bones LayerSetup writes.
#include "Animation/AnimData/BoneMaskFilter.h"
#include "K2Node_VariableGet.h"
#include "BoneControllers/AnimNode_SkeletalControlBase.h"
#include "Engine/MemberReference.h"
#include "AnimationGraph.h"
#include "AnimationStateGraph.h"
#include "AnimationStateMachineGraph.h"
#include "AnimationGraphSchema.h"
#include "AnimStateNode.h"
#include "EdGraphSchema_K2_Actions.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"
#include "UObject/SoftObjectPath.h"
#include "UObject/UObjectIterator.h"

// PoseSearchEditor module — provides UAnimGraphNode_MotionMatching
#include "AnimGraphNode_MotionMatching.h"
// PoseSearchEditor module — provides UAnimGraphNode_PoseSearchHistoryCollector (Sprint 4 MM graph)
#include "AnimGraphNode_PoseSearchHistoryCollector.h"
// AnimGraph module — provides UAnimGraphNode_Inertialization (Sprint 4 alias)
#include "AnimGraphNode_Inertialization.h"
// PoseSearch runtime — UPoseSearchDatabase (build_motion_matching_node Database write)
#include "PoseSearch/PoseSearchDatabase.h"
#include "Animation/BoneReference.h"
// BlendStackEditor module — UAnimGraphNode_BlendStack_Base (BoundGraph-node spawn fix)
#include "AnimGraphNode_BlendStack.h"
// FGraphNodeCreator — pristine node spawn for BoundGraph-owning nodes
#include "EdGraph/EdGraph.h"

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

void FMonolithAbpWriteActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// --- add_anim_graph_node ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_anim_graph_node"),
		TEXT("Place an animation graph node in a state or the main AnimGraph. node_type accepts built-in aliases; node_class accepts any loaded non-abstract UAnimGraphNode_Base subclass by path or name."),
		FMonolithActionHandler::CreateStatic(&HandleAddAnimGraphNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Optional(TEXT("node_type"), TEXT("string"), TEXT("Alias or UAnimGraphNode_Base class path/name. Aliases: SequencePlayer, BlendSpacePlayer, TwoWayBlend, BlendListByBool, LayeredBoneBlend, MotionMatching, TwoBoneIK, ModifyBone, LocalToComponentSpace, ComponentToLocalSpace"))
			.Optional(TEXT("node_class"), TEXT("string"), TEXT("UAnimGraphNode_Base subclass path or name, e.g. /Script/AnimGraph.AnimGraphNode_TwoBoneIK. Use this instead of node_type when not using an alias."))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name — 'AnimGraph' for top-level, or a state name for state inner graphs (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — if set, node is placed inside this state's inner graph (searched within the state machine found via graph_name if graph_name is a SM name, otherwise searches all SMs)"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Optional(TEXT("anim_asset"), TEXT("string"), TEXT("Animation/BlendSpace asset path — for SequencePlayer and BlendSpacePlayer nodes"))
			.Optional(TEXT("ik_bone"), TEXT("string"), TEXT("TwoBoneIK only: end-of-chain bone name (e.g. 'hand_l')"))
			.Optional(TEXT("effector_space"), TEXT("string"), TEXT("TwoBoneIK only: EffectorLocationSpace — WorldSpace, ComponentSpace (default), ParentBoneSpace, BoneSpace"))
			.Optional(TEXT("joint_target_space"), TEXT("string"), TEXT("TwoBoneIK only: JointTargetLocationSpace — WorldSpace, ComponentSpace (default), ParentBoneSpace, BoneSpace"))
			.Optional(TEXT("bone_to_modify"), TEXT("string"), TEXT("ModifyBone only: bone to modify (e.g. 'spine_01')"))
			.Optional(TEXT("expose_pins"), TEXT("array"), TEXT("Names of optional properties to expose as input pins (e.g. ['EffectorLocation','JointTargetLocation','Alpha']). TwoBoneIK exposes these three by default."))
			.Build());

	// --- connect_anim_graph_pins ---
	Registry.RegisterAction(TEXT("animation"), TEXT("connect_anim_graph_pins"),
		TEXT("Wire two node pins together in an ABP anim graph. Use after add_anim_graph_node to connect pose outputs to inputs."),
		FMonolithActionHandler::CreateStatic(&HandleConnectAnimGraphPins),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("source_node"), TEXT("string"), TEXT("Source node name (UObject name from add_anim_graph_node response, or class-based like AnimGraphNode_SequencePlayer_0)"))
			.Required(TEXT("source_pin"), TEXT("string"), TEXT("Source pin name, e.g. 'Pose' (output pin)"))
			.Required(TEXT("target_node"), TEXT("string"), TEXT("Target node name"))
			.Required(TEXT("target_pin"), TEXT("string"), TEXT("Target pin name, e.g. 'Result', 'A', 'B', 'BlendPose_0'"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Graph name to search in (default: searches all graphs)"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name to search in — narrows to a specific state's inner graph"))
			.Optional(TEXT("compile"), TEXT("bool"), TEXT("Compile ABP after wiring (default: true)"), TEXT("true"))
			.Build());

	// --- set_state_animation ---
	Registry.RegisterAction(TEXT("animation"), TEXT("set_state_animation"),
		TEXT("High-level shortcut: set which animation a state plays by spawning the right player node and wiring it to the state result. Handles SequencePlayer vs BlendSpacePlayer automatically."),
		FMonolithActionHandler::CreateStatic(&HandleSetStateAnimation),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("machine_name"), TEXT("string"), TEXT("State machine name (as shown in get_state_machines)"))
			.Required(TEXT("state_name"), TEXT("string"), TEXT("State name to set animation for"))
			.RequiredAssetPath(TEXT("anim_asset_path"), TEXT("AnimSequence or BlendSpace asset path"))
			.Optional(TEXT("loop"), TEXT("bool"), TEXT("Set loop flag on the player node"), TEXT("false"))
			.Optional(TEXT("clear_existing"), TEXT("bool"), TEXT("Remove existing animation nodes wired to the state result (default: true)"), TEXT("true"))
			.Build());

	// --- add_variable_get ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_variable_get"),
		TEXT("Place a variable Get node (K2Node_VariableGet) in the AnimGraph — used to drive AnimGraph pins from AnimInstance members."),
		FMonolithActionHandler::CreateStatic(&HandleAddVariableGet),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("variable_name"), TEXT("string"), TEXT("Variable name as exposed on the AnimInstance (C++ UPROPERTY or BP variable)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("Optional state name to scope the search to a state inner graph"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 0)"), TEXT("0"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- set_anim_graph_node_property ---
	// Mutates a property on the *source* UAnimGraphNode's inner FAnimNode struct.
	// Writing via blueprint.set_cdo_property is wiped on compile because the AnimBP's
	// CDO is regenerated from the graph nodes — this action edits the authoritative
	// source so the change persists.
	Registry.RegisterAction(TEXT("animation"), TEXT("set_anim_graph_node_property"),
		TEXT("Mutate a property on an existing anim graph node's internal FAnimNode struct (e.g. ModifyBone.BoneToModify.BoneName, ModifyBone.RotationMode, TwoBoneIK.EffectorLocationSpace). Persists across compile — writes to the source UAnimGraphNode, not the CDO."),
		FMonolithActionHandler::CreateStatic(&HandleSetAnimGraphNodeProperty),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("node_id"), TEXT("string"), TEXT("Node UObject name (e.g. 'AnimGraphNode_ModifyBone_7') — same id surfaced by get_graph_summary / add_anim_graph_node response"))
			.Required(TEXT("property_path"), TEXT("string"), TEXT("Dotted property path inside the node's inner FAnimNode struct (e.g. 'BoneToModify.BoneName', 'RotationMode', 'EffectorLocationSpace', 'Alpha'). Do NOT prefix with 'Node.'."))
			.Required(TEXT("value"), TEXT("string"), TEXT("Value as text — same format as ImportText in the Details panel. Enums: bare name (e.g. 'BMM_Additive', 'BCS_ComponentSpace'). FName: bare name. Struct: '(Field=Value,...)'."))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Graph name to scope the search (default: searches all graphs)"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name to narrow the search to a specific state's inner graph"))
			.Build());

	// --- configure_pose_history_node (Sprint 4.2) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("configure_pose_history_node"),
		TEXT("Configure a Pose History (PoseSearchHistoryCollector) anim graph node's FAnimNode_PoseSearchHistoryCollector_Base properties for Motion Matching. Trajectory is generated via bGenerateTrajectory (UE 5.7 has no CharacterTrajectoryComponent)."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleConfigurePoseHistoryNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("node_id"), TEXT("string"), TEXT("Pose History node UObject name (from add_anim_graph_node / get_graph_summary)"))
			.Optional(TEXT("generate_trajectory"), TEXT("bool"), TEXT("bGenerateTrajectory — node generates trajectory from TrajectoryData instead of an input trajectory"))
			.Optional(TEXT("pose_count"), TEXT("number"), TEXT("PoseCount — max stored poses (ClampMin 2)"))
			.Optional(TEXT("sampling_interval"), TEXT("number"), TEXT("SamplingInterval — seconds between collected poses (0 = every update)"))
			.Optional(TEXT("collected_bones"), TEXT("array"), TEXT("CollectedBones — bone names to collect (written as FBoneReference array)"))
			.Optional(TEXT("trajectory_history_count"), TEXT("number"), TEXT("TrajectoryHistoryCount — past trajectory samples (ClampMin 2; used when generate_trajectory)"))
			.Optional(TEXT("trajectory_prediction_count"), TEXT("number"), TEXT("TrajectoryPredictionCount — future trajectory samples (ClampMin 2; used when generate_trajectory)"))
			.Build());

	// --- configure_motion_matching_node (Sprint 4.3) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("configure_motion_matching_node"),
		TEXT("Configure a Motion Matching anim graph node's FAnimNode_MotionMatching + FAnimNode_BlendStack_Standalone base properties. PoseJumpThresholdTime is an FFloatInterval (min/max)."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleConfigureMotionMatchingNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("node_id"), TEXT("string"), TEXT("Motion Matching node UObject name (from add_anim_graph_node / get_graph_summary)"))
			.Optional(TEXT("blend_time"), TEXT("number"), TEXT("BlendTime — seconds to blend out to the new pose"))
			.Optional(TEXT("pose_jump_threshold_min"), TEXT("number"), TEXT("PoseJumpThresholdTime.Min (FFloatInterval)"))
			.Optional(TEXT("pose_jump_threshold_max"), TEXT("number"), TEXT("PoseJumpThresholdTime.Max (FFloatInterval)"))
			.Optional(TEXT("search_throttle"), TEXT("number"), TEXT("SearchThrottleTime — min seconds between searches"))
			.Optional(TEXT("use_inertial_blend"), TEXT("bool"), TEXT("bUseInertialBlend — requires an Inertialization node downstream"))
			.Optional(TEXT("should_filter_notifies"), TEXT("bool"), TEXT("bShouldFilterNotifies — on the BlendStack base struct"))
			.Optional(TEXT("notify_recency_timeout"), TEXT("number"), TEXT("NotifyRecencyTimeOut — on the BlendStack base struct"))
			.Optional(TEXT("max_active_blends"), TEXT("number"), TEXT("MaxActiveBlends — on the BlendStack base struct (0 = inertialization-only)"))
			.Build());

	// --- build_motion_matching_node (Sprint 4.4 — COMPOSITE) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("build_motion_matching_node"),
		TEXT("Composite: spawn a Pose History + Motion Matching node in the AnimGraph, wire History pose-out -> MM pose-in, assign the MM Database, apply sensible MM/history defaults, and compile. Optionally set chooser-driven DB selection."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleBuildMotionMatchingNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.RequiredAssetPath(TEXT("database_path"), TEXT("UPoseSearchDatabase asset path assigned to the MM node's Database"))
			.Optional(TEXT("chooser_path"), TEXT("string"), TEXT("Optional UChooserTable asset path for chooser-driven database selection (best-effort; Database is always set as fallback)"))
			.Build());

	Registry.RegisterAction(TEXT("animation"), TEXT("get_anim_graph_output_connection"),
		TEXT("READ-ONLY: report whether the AnimGraph's Output Pose (UAnimGraphNode_Root 'Result' input) "
			 "is driven, and by which node/pin. Verifies the graph actually produces a final pose — the "
			 "check that would have caught an unwired Motion Matching graph."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleGetAnimGraphOutputConnection),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Graph to inspect (default the main AnimGraph)"), TEXT("AnimGraph"))
			.Build());

	// --- build_foot_ik_pass (Pack C — COMPOSITE) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("build_foot_ik_pass"),
		TEXT("Composite: insert a lightweight foot IK pass (two TwoBoneIK nodes on the foot IK bones + a pelvis ModifyBone vertical offset) into the post-MM pose chain. Splices between whatever currently drives the Output Pose (e.g. Inertialization) and the Output Pose node. Foot IK alphas are gated by the contact_l/contact_r curves where supplied. Returns entry/exit node names for further splicing."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleBuildFootIkPass),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("left_foot_bone"), TEXT("string"), TEXT("Left foot IK end-of-chain bone (e.g. 'ik_foot_l')"))
			.Required(TEXT("right_foot_bone"), TEXT("string"), TEXT("Right foot IK end-of-chain bone (e.g. 'ik_foot_r')"))
			.Required(TEXT("pelvis_bone"), TEXT("string"), TEXT("Pelvis bone for the vertical (Z) root/pelvis offset (e.g. 'pelvis')"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("left_contact_curve"), TEXT("string"), TEXT("Anim curve gating left-foot IK alpha (default: contact_l)"), TEXT("contact_l"))
			.Optional(TEXT("right_contact_curve"), TEXT("string"), TEXT("Anim curve gating right-foot IK alpha (default: contact_r)"), TEXT("contact_r"))
			.Build());

	// --- assign_post_process_anim_rig (Pack C) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("assign_post_process_anim_rig"),
		TEXT("Set a skeletal mesh asset's PostProcessAnimBlueprint (post-process anim instance class) — runs after the main anim instance, before physics. Use to attach a post-process IK/Control-Rig ABP as an alternative to in-graph foot IK. Writes via USkeletalMesh::SetPostProcessAnimBlueprint."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAssignPostProcessAnimRig),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("mesh_path"), TEXT("USkeletalMesh asset path to assign the post-process ABP on"))
			.RequiredAssetPath(TEXT("post_process_abp_path"), TEXT("Post-process Animation Blueprint asset (its generated UAnimInstance class is assigned). Empty/None clears the assignment."))
			.Build());

	// --- add_apply_additive (AnimGraph authoring) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_apply_additive"),
		TEXT("Place an Apply Additive node (UAnimGraphNode_ApplyAdditive) and optionally wire a base pose into 'Base' and an additive pose into 'Additive'. The additive input must be authored as an additive animation (not detectable at author time). Set alpha to scale the additive contribution."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddApplyAdditive),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Optional(TEXT("base_node"), TEXT("string"), TEXT("Node whose pose output drives the Base input (must be in the same graph)"))
			.Optional(TEXT("additive_node"), TEXT("string"), TEXT("Node whose pose output drives the Additive input (must be in the same graph)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — place inside this state's inner graph"))
			.Optional(TEXT("alpha"), TEXT("number"), TEXT("Additive blend alpha 0..1 (default: 1.0)"), TEXT("1.0"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- add_apply_mesh_space_additive (AnimGraph authoring) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_apply_mesh_space_additive"),
		TEXT("Place an Apply Mesh-Space Additive node (UAnimGraphNode_ApplyMeshSpaceAdditive) — same Base/Additive/Alpha shape as add_apply_additive, but the additive input must be authored mesh-space (e.g. mesh-space aim offsets)."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddApplyMeshSpaceAdditive),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Optional(TEXT("base_node"), TEXT("string"), TEXT("Node whose pose output drives the Base input (must be in the same graph)"))
			.Optional(TEXT("additive_node"), TEXT("string"), TEXT("Node whose pose output drives the Additive input — must be a mesh-space additive pose"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — place inside this state's inner graph"))
			.Optional(TEXT("alpha"), TEXT("number"), TEXT("Additive blend alpha 0..1 (default: 1.0)"), TEXT("1.0"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- add_slot_node (AnimGraph authoring) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_slot_node"),
		TEXT("Place an Anim Slot node (UAnimGraphNode_Slot) that lets montages play into the graph at slot_name. Optionally wire a source pose into 'Source' (passed through when no montage plays). slot_name is validated against the skeleton's registered slots (non-fatal warning if absent — montage slots are often registered later)."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddSlotNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("slot_name"), TEXT("string"), TEXT("Montage slot name (e.g. 'DefaultSlot')"))
			.Optional(TEXT("source_node"), TEXT("string"), TEXT("Node whose pose output drives the Source input (must be in the same graph)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — place inside this state's inner graph"))
			.Optional(TEXT("validate_slot"), TEXT("bool"), TEXT("Validate slot_name against the skeleton's registered slots (default: true)"), TEXT("true"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- add_save_cached_pose (AnimGraph authoring) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_save_cached_pose"),
		TEXT("Place a Save Cached Pose node (UAnimGraphNode_SaveCachedPose) that caches a pose under cache_name for reuse by add_use_cached_pose. Save nodes are sinks restricted to the main AnimGraph (not state inner graphs). Optionally wire the pose to cache into 'Pose'. Cache scope is per-graph."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddSaveCachedPose),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("cache_name"), TEXT("string"), TEXT("Cache key — the authoritative name add_use_cached_pose binds to"))
			.Optional(TEXT("source_node"), TEXT("string"), TEXT("Node whose pose output is cached (drives the Pose input; must be in the same graph)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- add_use_cached_pose (AnimGraph authoring) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_use_cached_pose"),
		TEXT("Place a Use Cached Pose node (UAnimGraphNode_UseCachedPose) that outputs the pose cached by a Save Cached Pose node with the matching cache_name. By default errors if no Save node with that name exists in the graph (validate_pair) — guards the classic mismatched-name silent-wrong-compile failure."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddUseCachedPose),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("cache_name"), TEXT("string"), TEXT("Cache key — must match an existing Save Cached Pose node's cache_name in the graph"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("validate_pair"), TEXT("bool"), TEXT("Error if no Save node with this cache_name exists in the graph (default: true)"), TEXT("true"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- set_output_pose_source (AnimGraph authoring) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("set_output_pose_source"),
		TEXT("Drive the AnimGraph's Output Pose: wire an arbitrary node's pose output into the UAnimGraphNode_Root 'Result' input. The write half of get_anim_graph_output_connection — closes the 'compiles but A-poses' failure when the Output Pose is left unwired."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleSetOutputPoseSource),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("source_node"), TEXT("string"), TEXT("Node whose pose output drives the Output Pose (must be in the target graph)"))
			.Optional(TEXT("source_pin"), TEXT("string"), TEXT("Source pose output pin name (default: the node's first pose output)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("break_existing"), TEXT("bool"), TEXT("Break any existing link on the Output Pose before connecting (default: true)"), TEXT("true"))
			.Build());

	// --- set_state_result_source (AnimGraph authoring, Group 2) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("set_state_result_source"),
		TEXT("Drive a state's output pose: wire an arbitrary node (already inside the state's inner graph) into the state result sink pin (UAnimStateNode pose sink). The per-state analogue of set_output_pose_source — closes the 'state compiles but A-poses' failure when a state's result is left unwired. source_node must live inside this state's inner graph."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleSetStateResultSource),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("machine_name"), TEXT("string"), TEXT("State machine name containing the state"))
			.Required(TEXT("state_name"), TEXT("string"), TEXT("State whose result pose is being driven"))
			.Required(TEXT("source_node"), TEXT("string"), TEXT("Node inside the state's inner graph whose pose output drives the state result"))
			.Optional(TEXT("source_pin"), TEXT("string"), TEXT("Source pose output pin name (default: the node's first pose output)"))
			.Optional(TEXT("break_existing"), TEXT("bool"), TEXT("Break any existing link on the state result pin before connecting (default: true)"), TEXT("true"))
			.Build());

	// --- add_blend_by_int (AnimGraph authoring, Group 2) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_blend_by_int"),
		TEXT("Place a Blend Poses by int node (UAnimGraphNode_BlendListByInt) with num_poses BlendPose_* input pins, selected by an integer 'Active Child Index' input. The node ships with 2 pose pins; this grows it to num_poses via AddPinToBlendList(). Wire each BlendPose_0..N-1 pin to a candidate pose afterward."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddBlendByInt),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("num_poses"), TEXT("number"), TEXT("Total number of blend-pose input pins (2..32)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — place inside this state's inner graph"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- add_blend_by_enum (AnimGraph authoring, Group 2) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_blend_by_enum"),
		TEXT("Place a Blend Poses by enum node (UAnimGraphNode_BlendListByEnum) bound to the enum at enum_path, with one BlendPose_* input pin exposed per chosen enumerator plus the always-present index-0 'Default' pin (which catches every enum value not given its own pin). By default every non-Hidden, non-_MAX enumerator is exposed; pass 'enumerators' to expose an explicit subset. The active enum value selects which pose plays; wire each exposed BlendPose pin to a candidate pose afterward."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddBlendByEnum),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("enum_path"), TEXT("string"), TEXT("UEnum object path or name to bind (e.g. /Game/Enums/E_Locomotion.E_Locomotion, or a C++ enum like EAnimGroupRole)"))
			.Optional(TEXT("enumerators"), TEXT("array"), TEXT("Explicit subset of enumerator names to expose as pins (default: all non-Hidden, non-_MAX enumerators). Names may be short (e.g. 'Walk') or fully-qualified (e.g. 'E_Locomotion::Walk')."))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — place inside this state's inner graph"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- set_sync_group (AnimGraph authoring, Group 2) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("set_sync_group"),
		TEXT("Set the sync-group settings (GroupName/GroupRole/Method) on an asset-player node (Sequence Player or BlendSpace Player) so it synchronizes playback with other players in the same named group — e.g. so a start clip and a looping blendspace share phase with no foot-slide at the transition. Errors on node types that do not support sync groups."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleSetSyncGroup),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("node_id"), TEXT("string"), TEXT("Asset-player node id (Sequence Player / BlendSpace Player)"))
			.Required(TEXT("group_name"), TEXT("string"), TEXT("Sync group name (empty string clears the group)"))
			.Optional(TEXT("group_role"), TEXT("string"), TEXT("Role in the group: CanBeLeader / AlwaysLeader / AlwaysFollower / TransitionLeader / TransitionFollower / ExclusiveAlwaysLeader (default: CanBeLeader)"), TEXT("CanBeLeader"))
			.Optional(TEXT("sync_method"), TEXT("string"), TEXT("Sync method: DoNotSync / SyncGroup / Graph (default: SyncGroup)"), TEXT("SyncGroup"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: search all graphs)"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — scope the node lookup to this state's inner graph"))
			.Build());

	// --- set_layered_blend_bones (AnimGraph authoring, Group 2) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("set_layered_blend_bones"),
		TEXT("Configure the per-layer bone branch filters on a Layered Blend Per Bone node (UAnimGraphNode_LayeredBoneBlend). Each layer entry grows a BlendPose input pin (AddPinToBlendByFilter) and a LayerSetup branch-filter list. For each bone in a layer, 'depth' maps to the struct BlendDepth: 0 = blend exactly that bone, >0 = include descendants down that many levels, <0 = exclude. The node starts with 1 layer; this grows to layers.Num()."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleSetLayeredBlendBones),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("node_id"), TEXT("string"), TEXT("Layered Blend Per Bone node id"))
			.Required(TEXT("layers"), TEXT("array"), TEXT("Array of layers, one per blend-pose pin: [{ \"bones\": [{ \"bone\": \"spine_01\", \"depth\": 1 }] }]. 'depth' is the per-bone BlendDepth."))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: search all graphs)"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — scope the node lookup to this state's inner graph"))
			.Build());

	// --- add_anim_control_rig_node (AnimGraph authoring, Group 3) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_anim_control_rig_node"),
		TEXT("Place a Control Rig anim node (UAnimGraphNode_ControlRig) in the AnimGraph and set its Control Rig class. Writes the inner FAnimNode_ControlRig.ControlRigClass (a private EditAnywhere UPROPERTY) by reflection, then ReconstructNode() regenerates the rig's input/output pins from its exposed variables (via CreateCustomPins). Distinct from add_control_rig_node, which authors a RigVM control-rig graph — this is the AnimGraph-side node that runs a rig inside an Animation Blueprint."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddAnimControlRigNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("control_rig_class"), TEXT("string"), TEXT("UControlRig subclass to run — a Control Rig blueprint-generated class path or name (e.g. /Game/Rigs/CR_Foo.CR_Foo_C)"))
			.Optional(TEXT("source_node"), TEXT("string"), TEXT("Node whose pose output drives the Control Rig node's pose input (intra-graph)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("state_name"), TEXT("string"), TEXT("State name — place inside this state's inner graph"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- add_linked_anim_layer (AnimGraph authoring, Group 3) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_linked_anim_layer"),
		TEXT("Place a Linked Anim Layer node (UAnimGraphNode_LinkedAnimLayer) that runs a named animation layer declared on an implemented anim-layer interface. Spawns the node, reflection-writes the inner Layer name / Interface class / InstanceClass, and resolves the editor-node InterfaceGuid from the implemented interface graph whose name matches layer_name (mirrors the engine's GetGuidForLayer lookup), then ReconstructNode() regenerates the layer's IO pins. The ABP must implement at least one UAnimLayerInterface declaring the layer."),
		FMonolithActionHandler::CreateStatic(&FMonolithAbpWriteActions::HandleAddLinkedAnimLayer),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("layer_name"), TEXT("string"), TEXT("Layer/function name as declared on the implemented anim-layer interface graph"))
			.Optional(TEXT("interface_class"), TEXT("string"), TEXT("UAnimLayerInterface class declaring the layer (path or name) — required only when the ABP implements multiple anim-layer interfaces; otherwise resolved automatically from layer_name"))
			.Optional(TEXT("instance_class"), TEXT("string"), TEXT("External UAnimInstance class to run this layer (path or name); omit for a self/Default layer (only valid for non-self interface layers)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (default: AnimGraph)"), TEXT("AnimGraph"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 200)"), TEXT("200"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

namespace
{

/** Map a user-facing node type alias to UClass. Returns nullptr on unknown type. */
UClass* ResolveNodeTypeAlias(const FString& NodeType)
{
	if (NodeType.Equals(TEXT("SequencePlayer"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_SequencePlayer::StaticClass();
	if (NodeType.Equals(TEXT("BlendSpacePlayer"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_BlendSpacePlayer::StaticClass();
	if (NodeType.Equals(TEXT("TwoWayBlend"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_TwoWayBlend::StaticClass();
	if (NodeType.Equals(TEXT("BlendListByBool"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_BlendListByBool::StaticClass();
	if (NodeType.Equals(TEXT("LayeredBoneBlend"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_LayeredBoneBlend::StaticClass();
	if (NodeType.Equals(TEXT("MotionMatching"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_MotionMatching::StaticClass();
	// Sprint 4 (4.1): PoseHistory node — UE 5.7 class is UAnimGraphNode_PoseSearchHistoryCollector,
	// NOT the old UAnimGraphNode_PoseHistory (gotcha #2).
	if (NodeType.Equals(TEXT("pose_history"), ESearchCase::IgnoreCase)
		|| NodeType.Equals(TEXT("PoseHistory"), ESearchCase::IgnoreCase)
		|| NodeType.Equals(TEXT("PoseSearchHistoryCollector"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_PoseSearchHistoryCollector::StaticClass();
	if (NodeType.Equals(TEXT("inertialization"), ESearchCase::IgnoreCase)
		|| NodeType.Equals(TEXT("Inertialization"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_Inertialization::StaticClass();
	if (NodeType.Equals(TEXT("TwoBoneIK"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_TwoBoneIK::StaticClass();
	if (NodeType.Equals(TEXT("ModifyBone"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_ModifyBone::StaticClass();
	if (NodeType.Equals(TEXT("LocalToComponentSpace"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_LocalToComponentSpace::StaticClass();
	if (NodeType.Equals(TEXT("ComponentToLocalSpace"), ESearchCase::IgnoreCase))
		return UAnimGraphNode_ComponentToLocalSpace::StaticClass();
	return nullptr;
}

FString CleanClassSpecifier(FString ClassSpecifier)
{
	ClassSpecifier.TrimStartAndEndInline();

	const TCHAR* Prefixes[] =
	{
		TEXT("Class'"),
		TEXT("BlueprintGeneratedClass'")
	};

	for (const TCHAR* Prefix : Prefixes)
	{
		if (ClassSpecifier.StartsWith(Prefix) && ClassSpecifier.EndsWith(TEXT("'")))
		{
			const int32 PrefixLen = FCString::Strlen(Prefix);
			ClassSpecifier = ClassSpecifier.Mid(PrefixLen, ClassSpecifier.Len() - PrefixLen - 1);
			ClassSpecifier.TrimStartAndEndInline();
			break;
		}
	}

	return ClassSpecifier;
}

void AddUniqueClassLookupCandidate(TArray<FString>& Candidates, const FString& Candidate)
{
	const FString CleanCandidate = CleanClassSpecifier(Candidate);
	if (!CleanCandidate.IsEmpty())
	{
		Candidates.AddUnique(CleanCandidate);
	}
}

TArray<FString> BuildClassLookupCandidates(const FString& RawClassSpecifier)
{
	TArray<FString> Candidates;
	const FString ClassSpecifier = CleanClassSpecifier(RawClassSpecifier);
	AddUniqueClassLookupCandidate(Candidates, ClassSpecifier);

	if (ClassSpecifier.StartsWith(TEXT("/Script/")))
	{
		int32 DotIndex = INDEX_NONE;
		if (ClassSpecifier.FindLastChar(TEXT('.'), DotIndex)
			&& DotIndex + 2 < ClassSpecifier.Len()
			&& ClassSpecifier[DotIndex + 1] == TEXT('U'))
		{
			AddUniqueClassLookupCandidate(Candidates, ClassSpecifier.Left(DotIndex + 1) + ClassSpecifier.Mid(DotIndex + 2));
		}
	}
	else if (!ClassSpecifier.Contains(TEXT("/")) && ClassSpecifier.Contains(TEXT(".")))
	{
		AddUniqueClassLookupCandidate(Candidates, TEXT("/Script/") + ClassSpecifier);
		int32 DotIndex = INDEX_NONE;
		if (ClassSpecifier.FindLastChar(TEXT('.'), DotIndex)
			&& DotIndex + 2 < ClassSpecifier.Len()
			&& ClassSpecifier[DotIndex + 1] == TEXT('U'))
		{
			AddUniqueClassLookupCandidate(Candidates, TEXT("/Script/") + ClassSpecifier.Left(DotIndex + 1) + ClassSpecifier.Mid(DotIndex + 2));
		}
	}
	else if (!ClassSpecifier.Contains(TEXT("/")) && !ClassSpecifier.Contains(TEXT(".")))
	{
		if ((ClassSpecifier.StartsWith(TEXT("U")) || ClassSpecifier.StartsWith(TEXT("A"))) && ClassSpecifier.Len() > 1)
		{
			AddUniqueClassLookupCandidate(Candidates, ClassSpecifier.Mid(1));
		}
		else
		{
			AddUniqueClassLookupCandidate(Candidates, TEXT("U") + ClassSpecifier);
			AddUniqueClassLookupCandidate(Candidates, TEXT("A") + ClassSpecifier);
		}
	}

	return Candidates;
}

void AddUniqueClassMatch(TArray<UClass*>& Matches, UClass* Match)
{
	if (Match)
	{
		Matches.AddUnique(Match);
	}
}

TArray<UClass*> FindLoadedClassesBySpecifier(const TArray<FString>& Candidates)
{
	TArray<UClass*> Matches;
	for (TObjectIterator<UClass> It; It; ++It)
	{
		UClass* CandidateClass = *It;
		if (!CandidateClass)
		{
			continue;
		}

		const FString ClassName = CandidateClass->GetName();
		const FString PathName = CandidateClass->GetPathName();
		const FString FullName = CandidateClass->GetFullName();
		for (const FString& Candidate : Candidates)
		{
			if (ClassName.Equals(Candidate, ESearchCase::IgnoreCase)
				|| PathName.Equals(Candidate, ESearchCase::IgnoreCase)
				|| FullName.Equals(Candidate, ESearchCase::IgnoreCase))
			{
				AddUniqueClassMatch(Matches, CandidateClass);
			}
		}
	}

	return Matches;
}

TArray<UClass*> ResolveClassSpecifier(const FString& RawClassSpecifier)
{
	TArray<UClass*> Matches;
	const TArray<FString> Candidates = BuildClassLookupCandidates(RawClassSpecifier);

	for (const FString& Candidate : Candidates)
	{
		if (Candidate.Contains(TEXT("/")) || Candidate.Contains(TEXT(".")))
		{
			if (UClass* LoadedClass = LoadClass<UObject>(nullptr, *Candidate))
			{
				AddUniqueClassMatch(Matches, LoadedClass);
			}

			const FSoftClassPath SoftClassPath(Candidate);
			if (UClass* ResolvedClass = SoftClassPath.ResolveClass())
			{
				AddUniqueClassMatch(Matches, ResolvedClass);
			}
		}
	}

	if (Matches.Num() == 0)
	{
		Matches = FindLoadedClassesBySpecifier(Candidates);
	}

	return Matches;
}

FString DescribeClassMatches(const TArray<UClass*>& Matches)
{
	TArray<FString> Paths;
	for (const UClass* Match : Matches)
	{
		if (Match)
		{
			Paths.Add(Match->GetPathName());
		}
	}
	return FString::Join(Paths, TEXT(", "));
}

UClass* ResolveAnimGraphNodeClass(const FString& NodeType, const FString& NodeClassSpecifier, FString& OutError)
{
	const FString CleanNodeType = CleanClassSpecifier(NodeType);
	const FString CleanNodeClassSpecifier = CleanClassSpecifier(NodeClassSpecifier);

	if (!CleanNodeType.IsEmpty() && !CleanNodeClassSpecifier.IsEmpty())
	{
		OutError = TEXT("Specify either node_type or node_class, not both. node_type is for built-in aliases or legacy class strings; node_class is for explicit UAnimGraphNode_Base class paths/names.");
		return nullptr;
	}

	if (CleanNodeType.IsEmpty() && CleanNodeClassSpecifier.IsEmpty())
	{
		OutError = TEXT("Missing required parameter: provide node_type alias or node_class UAnimGraphNode_Base class path/name.");
		return nullptr;
	}

	const FString RequestedClass = !CleanNodeClassSpecifier.IsEmpty() ? CleanNodeClassSpecifier : CleanNodeType;
	UClass* NodeClass = CleanNodeClassSpecifier.IsEmpty() ? ResolveNodeTypeAlias(CleanNodeType) : nullptr;
	if (!NodeClass)
	{
		TArray<UClass*> ClassMatches = ResolveClassSpecifier(RequestedClass);
		TArray<UClass*> SpawnableMatches;
		for (UClass* ClassMatch : ClassMatches)
		{
			if (ClassMatch
				&& ClassMatch->IsChildOf(UAnimGraphNode_Base::StaticClass())
				&& !ClassMatch->HasAnyClassFlags(CLASS_Abstract))
			{
				SpawnableMatches.AddUnique(ClassMatch);
			}
		}

		if (SpawnableMatches.Num() > 1)
		{
			OutError = FString::Printf(
				TEXT("Ambiguous anim graph node class '%s'. Matches: %s. Use a full class path such as '/Script/Module.AnimGraphNode_Name'."),
				*RequestedClass,
				*DescribeClassMatches(SpawnableMatches));
			return nullptr;
		}

		if (SpawnableMatches.Num() == 1)
		{
			NodeClass = SpawnableMatches[0];
		}
		else if (ClassMatches.Num() == 1)
		{
			NodeClass = ClassMatches[0];
		}
	}

	if (!NodeClass)
	{
		OutError = FString::Printf(
			TEXT("Anim graph node class not found for '%s'. Use an alias [%s], a loaded class name like 'AnimGraphNode_TwoBoneIK', or a full class path like '/Script/AnimGraph.AnimGraphNode_TwoBoneIK'. If this is a plugin node, make sure its editor module is loaded."),
			*RequestedClass,
			TEXT("SequencePlayer, BlendSpacePlayer, TwoWayBlend, BlendListByBool, LayeredBoneBlend, MotionMatching, TwoBoneIK, ModifyBone, LocalToComponentSpace, ComponentToLocalSpace"));
		return nullptr;
	}

	if (!NodeClass->IsChildOf(UAnimGraphNode_Base::StaticClass()))
	{
		OutError = FString::Printf(
			TEXT("Resolved class '%s' (%s) is not a child of UAnimGraphNode_Base; add_anim_graph_node can only spawn editor AnimGraph node classes."),
			*NodeClass->GetName(),
			*NodeClass->GetPathName());
		return nullptr;
	}

	if (NodeClass->HasAnyClassFlags(CLASS_Abstract))
	{
		OutError = FString::Printf(
			TEXT("Resolved class '%s' (%s) is abstract and cannot be spawned. Use a concrete UAnimGraphNode_Base subclass."),
			*NodeClass->GetName(),
			*NodeClass->GetPathName());
		return nullptr;
	}

	return NodeClass;
}

/** Parse a bone-control-space string. Defaults to ComponentSpace when missing/unrecognized. */
EBoneControlSpace ParseBoneControlSpace(const FString& Str, EBoneControlSpace Default = BCS_ComponentSpace)
{
	if (Str.Equals(TEXT("WorldSpace"), ESearchCase::IgnoreCase))      return BCS_WorldSpace;
	if (Str.Equals(TEXT("ComponentSpace"), ESearchCase::IgnoreCase))  return BCS_ComponentSpace;
	if (Str.Equals(TEXT("ParentBoneSpace"), ESearchCase::IgnoreCase)) return BCS_ParentBoneSpace;
	if (Str.Equals(TEXT("BoneSpace"), ESearchCase::IgnoreCase))       return BCS_BoneSpace;
	return Default;
}

/** Find a state machine graph by its display title (same lookup as Wave 10 add_state_to_machine). */
UAnimationStateMachineGraph* FindSMGraphByName(UAnimBlueprint* ABP, const FString& MachineName)
{
	for (UEdGraph* Graph : ABP->FunctionGraphs)
	{
		if (!Graph) continue;
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			UAnimGraphNode_StateMachine* SMNode = Cast<UAnimGraphNode_StateMachine>(Node);
			if (!SMNode) continue;

			FString SMTitle = SMNode->GetNodeTitle(ENodeTitleType::FullTitle).ToString();
			int32 NewlineIdx = INDEX_NONE;
			if (SMTitle.FindChar(TEXT('\n'), NewlineIdx))
			{
				SMTitle.LeftInline(NewlineIdx);
			}
			if (SMTitle == MachineName)
			{
				return Cast<UAnimationStateMachineGraph>(SMNode->EditorStateMachineGraph);
			}
		}
	}
	return nullptr;
}

/** Find a state node by name within a state machine graph. */
UAnimStateNode* FindStateByName(UAnimationStateMachineGraph* SMGraph, const FString& StateName)
{
	for (UEdGraphNode* Node : SMGraph->Nodes)
	{
		UAnimStateNode* StateNode = Cast<UAnimStateNode>(Node);
		if (StateNode && StateNode->GetStateName() == StateName)
		{
			return StateNode;
		}
	}
	return nullptr;
}

/**
 * Resolve the target graph from graph_name and state_name parameters.
 * - If state_name is provided, searches all state machines for that state and returns its inner graph.
 * - If graph_name is "AnimGraph", returns the top-level AnimGraph.
 * - Otherwise treats graph_name as a state machine name and looks for state_name within it.
 */
UEdGraph* ResolveTargetGraph(UAnimBlueprint* ABP, const FString& GraphName, const FString& StateName, FString& OutError)
{
	// If state_name is specified, find the state and return its inner graph
	if (!StateName.IsEmpty())
	{
		// Search all state machines for this state
		for (UEdGraph* Graph : ABP->FunctionGraphs)
		{
			if (!Graph) continue;
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				UAnimGraphNode_StateMachine* SMNode = Cast<UAnimGraphNode_StateMachine>(Node);
				if (!SMNode) continue;

				UAnimationStateMachineGraph* SMGraph = Cast<UAnimationStateMachineGraph>(SMNode->EditorStateMachineGraph);
				if (!SMGraph) continue;

				UAnimStateNode* StateNode = FindStateByName(SMGraph, StateName);
				if (StateNode)
				{
					UAnimationStateGraph* StateGraph = Cast<UAnimationStateGraph>(StateNode->BoundGraph);
					if (!StateGraph)
					{
						OutError = FString::Printf(TEXT("State '%s' has no inner animation graph (BoundGraph is null)"), *StateName);
						return nullptr;
					}
					return StateGraph;
				}
			}
		}
		OutError = FString::Printf(TEXT("State '%s' not found in any state machine"), *StateName);
		return nullptr;
	}

	// No state_name — use graph_name
	if (GraphName.Equals(TEXT("AnimGraph"), ESearchCase::IgnoreCase) || GraphName.IsEmpty())
	{
		// Find the main AnimGraph (first UAnimationGraph in FunctionGraphs)
		for (UEdGraph* Graph : ABP->FunctionGraphs)
		{
			if (UAnimationGraph* AG = Cast<UAnimationGraph>(Graph))
			{
				return AG;
			}
		}
		OutError = TEXT("No AnimGraph found in this Animation Blueprint");
		return nullptr;
	}

	// Treat graph_name as a named function graph
	for (UEdGraph* Graph : ABP->FunctionGraphs)
	{
		if (Graph && Graph->GetName() == GraphName)
		{
			return Graph;
		}
	}
	OutError = FString::Printf(TEXT("Graph '%s' not found. Use 'AnimGraph' for the main graph, or provide state_name to target a state's inner graph."), *GraphName);
	return nullptr;
}

/** Find a node by UObject name across all graphs in an ABP, or within a specific graph. */
UEdGraphNode* FindNodeByName(UAnimBlueprint* ABP, const FString& NodeName, UEdGraph* InGraph = nullptr)
{
	auto SearchGraph = [&](UEdGraph* Graph) -> UEdGraphNode*
	{
		if (!Graph) return nullptr;
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (Node && Node->GetName() == NodeName)
			{
				return Node;
			}
		}
		return nullptr;
	};

	if (InGraph)
	{
		return SearchGraph(InGraph);
	}

	// Search all function graphs and their subgraphs
	for (UEdGraph* Graph : ABP->FunctionGraphs)
	{
		if (UEdGraphNode* Found = SearchGraph(Graph))
			return Found;

		// Search inside state machine graphs
		if (!Graph) continue;
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			UAnimGraphNode_StateMachine* SMNode = Cast<UAnimGraphNode_StateMachine>(Node);
			if (!SMNode) continue;

			UAnimationStateMachineGraph* SMGraph = Cast<UAnimationStateMachineGraph>(SMNode->EditorStateMachineGraph);
			if (!SMGraph) continue;

			if (UEdGraphNode* Found = SearchGraph(SMGraph))
				return Found;

			// Search inside each state's inner graph
			for (UEdGraphNode* SMChild : SMGraph->Nodes)
			{
				UAnimStateNode* StateNode = Cast<UAnimStateNode>(SMChild);
				if (!StateNode || !StateNode->BoundGraph) continue;

				if (UEdGraphNode* Found = SearchGraph(StateNode->BoundGraph))
					return Found;
			}
		}
	}
	return nullptr;
}

/** Build a JSON array describing a node's pins. */
TArray<TSharedPtr<FJsonValue>> BuildPinList(UEdGraphNode* Node)
{
	TArray<TSharedPtr<FJsonValue>> PinsArr;
	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (!Pin) continue;

		TSharedPtr<FJsonObject> PinObj = MakeShared<FJsonObject>();
		PinObj->SetStringField(TEXT("name"), Pin->PinName.ToString());
		PinObj->SetStringField(TEXT("direction"), Pin->Direction == EGPD_Input ? TEXT("Input") : TEXT("Output"));
		PinObj->SetBoolField(TEXT("is_pose"), UAnimationGraphSchema::IsPosePin(Pin->PinType));
		PinObj->SetBoolField(TEXT("is_connected"), Pin->LinkedTo.Num() > 0);
		PinObj->SetStringField(TEXT("type"), Pin->PinType.PinCategory.ToString());

		PinsArr.Add(MakeShared<FJsonValueObject>(PinObj));
	}
	return PinsArr;
}

/**
 * Find a node's pose output pin. If PreferredName is non-empty, looks for that
 * exact output pin first; otherwise (or on miss) returns the node's first pose
 * output pin. Returns nullptr if the node has no pose output.
 */
UEdGraphPin* FindPoseOutputPin(UEdGraphNode* Node, const FString& PreferredName)
{
	if (!Node) return nullptr;

	if (!PreferredName.IsEmpty())
	{
		if (UEdGraphPin* Named = Node->FindPin(FName(*PreferredName), EGPD_Output))
		{
			if (UAnimationGraphSchema::IsPosePin(Named->PinType))
			{
				return Named;
			}
		}
	}

	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Output && UAnimationGraphSchema::IsPosePin(Pin->PinType))
		{
			return Pin;
		}
	}
	return nullptr;
}

/** Comma-joined list of a node's output pin names (for error messages). */
FString ListOutputPins(UEdGraphNode* Node)
{
	FString Out;
	if (!Node) return Out;
	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Output)
		{
			if (!Out.IsEmpty()) Out += TEXT(", ");
			Out += Pin->PinName.ToString();
		}
	}
	return Out;
}

/**
 * Spawn an AnimGraph node of NodeClass into Graph at (X,Y) using the correct
 * path — FGraphNodeCreator for BoundGraph-owning classes (which assert in
 * PostPlacedNewNode when template-duplicated), template + PerformAction
 * otherwise — and optionally wire SourceNode's pose output into the new node's
 * TargetInputPin. Opens/closes its own transaction. Returns the spawned node,
 * or nullptr with OutError set. Consolidates the spawn fork from
 * HandleAddAnimGraphNode and the TryCreateConnection boilerplate.
 */
UAnimGraphNode_Base* SpawnAndWirePoseInput(
	UEdGraph* Graph, UClass* NodeClass, float X, float Y,
	UEdGraphNode* SourceNode, const FName& TargetInputPin, FString& OutError)
{
	if (!Graph || !NodeClass)
	{
		OutError = TEXT("SpawnAndWirePoseInput: null graph or node class");
		return nullptr;
	}

	UAnimGraphNode_Base* SpawnedAnim = nullptr;

	GEditor->BeginTransaction(FText::FromString(TEXT("Add Anim Graph Node")));
	Graph->Modify();

	// BoundGraph-owning classes (BlendStack family, LinkedAnimLayer, etc.) assert in
	// PostPlacedNewNode if duplicated from a template, so spawn them pristine via
	// FGraphNodeCreator. All other classes use the editor's template/PerformAction path.
	if (NodeClass->IsChildOf(UAnimGraphNode_BlendStack_Base::StaticClass()))
	{
		FGraphNodeCreator<UAnimGraphNode_Base> Creator(*Graph);
		UAnimGraphNode_Base* NewNode = Creator.CreateNode(/*bSelectNewNode=*/false, NodeClass);
		if (!NewNode)
		{
			GEditor->EndTransaction();
			OutError = FString::Printf(TEXT("FGraphNodeCreator failed to create node for class '%s'"), *NodeClass->GetPathName());
			return nullptr;
		}
		NewNode->NodePosX = static_cast<int32>(X);
		NewNode->NodePosY = static_cast<int32>(Y);
		Creator.Finalize();
		SpawnedAnim = NewNode;
	}
	else
	{
		UAnimGraphNode_Base* Template = Cast<UAnimGraphNode_Base>(NewObject<UObject>(GetTransientPackage(), NodeClass));
		if (!Template)
		{
			GEditor->EndTransaction();
			OutError = FString::Printf(TEXT("Failed to create node template for class '%s'"), *NodeClass->GetPathName());
			return nullptr;
		}

		const UEdGraphSchema* TargetSchema = Graph->GetSchema();
		if (!TargetSchema || !Template->CanCreateUnderSpecifiedSchema(TargetSchema))
		{
			GEditor->EndTransaction();
			OutError = FString::Printf(
				TEXT("Class '%s' cannot be created under graph '%s' with schema '%s'. Use an AnimGraph or animation state graph."),
				*NodeClass->GetPathName(), *Graph->GetName(),
				TargetSchema ? *TargetSchema->GetClass()->GetName() : TEXT("<null>"));
			return nullptr;
		}

		FEdGraphSchemaAction_K2NewNode Action;
		Action.NodeTemplate = Template;
		UEdGraphNode* SpawnedNode = Action.PerformAction(Graph, /*FromPin=*/nullptr, FVector2f(X, Y), /*bSelectNewNode=*/false);
		SpawnedAnim = Cast<UAnimGraphNode_Base>(SpawnedNode);
		if (!SpawnedAnim)
		{
			GEditor->EndTransaction();
			OutError = TEXT("PerformAction failed — node was not spawned. Check that the target graph supports this node type.");
			return nullptr;
		}
	}

	// Optional single pose-input wiring: SourceNode pose-out -> SpawnedAnim.TargetInputPin.
	if (SourceNode && !TargetInputPin.IsNone())
	{
		UEdGraphPin* InPin = SpawnedAnim->FindPin(TargetInputPin, EGPD_Input);
		if (!InPin)
		{
			GEditor->EndTransaction();
			OutError = FString::Printf(TEXT("Input pin '%s' not found on spawned node '%s'"),
				*TargetInputPin.ToString(), *SpawnedAnim->GetName());
			return nullptr;
		}
		UEdGraphPin* OutPin = FindPoseOutputPin(SourceNode, FString());
		if (!OutPin)
		{
			GEditor->EndTransaction();
			OutError = FString::Printf(TEXT("Source node '%s' has no pose output pin. Available outputs: [%s]"),
				*SourceNode->GetName(), *ListOutputPins(SourceNode));
			return nullptr;
		}
		if (SourceNode->GetGraph() != SpawnedAnim->GetGraph())
		{
			GEditor->EndTransaction();
			OutError = FString::Printf(
				TEXT("Source node '%s' is in a different graph than the spawned node — connections must be intra-graph"),
				*SourceNode->GetName());
			return nullptr;
		}
		const UEdGraphSchema* Schema = SpawnedAnim->GetGraph()->GetSchema();
		if (!Schema->TryCreateConnection(OutPin, InPin))
		{
			GEditor->EndTransaction();
			OutError = FString::Printf(TEXT("TryCreateConnection failed: '%s.%s' -> '%s.%s'. Pin types may be incompatible."),
				*SourceNode->GetName(), *OutPin->PinName.ToString(),
				*SpawnedAnim->GetName(), *TargetInputPin.ToString());
			return nullptr;
		}
	}

	GEditor->EndTransaction();
	return SpawnedAnim;
}

} // anonymous namespace

// ---------------------------------------------------------------------------
// Action: add_anim_graph_node
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddAnimGraphNode(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeType;
	Params->TryGetStringField(TEXT("node_type"), NodeType);
	FString NodeClassSpecifier;
	Params->TryGetStringField(TEXT("node_class"), NodeClassSpecifier);
	FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");
	FString AnimAsset = Params->HasField(TEXT("anim_asset")) ? Params->GetStringField(TEXT("anim_asset")) : TEXT("");

	double TempVal;
	float PosX = 200.f;
	float PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	// Resolve the node class
	FString ClassError;
	UClass* NodeClass = ResolveAnimGraphNodeClass(NodeType, NodeClassSpecifier, ClassError);
	if (!NodeClass)
	{
		return FMonolithActionResult::Error(ClassError);
	}

	// Resolve the target graph
	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	// ---- BlendStack-derived nodes (MotionMatching, MotionMatchingInteraction) ----
	// These own a UPROPERTY BoundGraph and CreateGraph() does check(BoundGraph == nullptr)
	// inside PostPlacedNewNode (AnimGraphNode_BlendStack.cpp:261). The default template
	// path (NewObject template -> FEdGraphSchemaAction_K2NewNode::PerformAction) duplicates
	// the template via DuplicateObject, which copies the BoundGraph UPROPERTY, so the
	// duplicated node already carries a non-null BoundGraph and PostPlacedNewNode asserts.
	// Spawn these via FGraphNodeCreator instead: it builds a PRISTINE node (no template
	// duplication, BoundGraph stays null) and runs PostPlacedNewNode exactly once in
	// Finalize(). All other node classes keep the existing template/PerformAction path.
	if (NodeClass->IsChildOf(UAnimGraphNode_BlendStack_Base::StaticClass()))
	{
		GEditor->BeginTransaction(FText::FromString(TEXT("Add Anim Graph Node")));
		TargetGraph->Modify();

		FGraphNodeCreator<UAnimGraphNode_Base> Creator(*TargetGraph);
		UAnimGraphNode_Base* NewNode = Creator.CreateNode(/*bSelectNewNode=*/false, NodeClass);
		if (!NewNode)
		{
			GEditor->EndTransaction();
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("FGraphNodeCreator failed to create node for class '%s'"), *NodeClass->GetPathName()));
		}
		NewNode->NodePosX = static_cast<int32>(PosX);
		NewNode->NodePosY = static_cast<int32>(PosY);
		Creator.Finalize(); // runs PostPlacedNewNode (CreateGraph) once on the pristine node

		GEditor->EndTransaction();

		// Do NOT ReconstructNode() here — the node is already fully formed by Finalize().
		ABP->MarkPackageDirty();

		TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
		Root->SetStringField(TEXT("node_name"), NewNode->GetName());
		Root->SetStringField(TEXT("node_class"), NewNode->GetClass()->GetName());
		Root->SetStringField(TEXT("node_class_path"), NewNode->GetClass()->GetPathName());
		Root->SetStringField(TEXT("node_guid"), NewNode->NodeGuid.ToString());
		Root->SetNumberField(TEXT("position_x"), NewNode->NodePosX);
		Root->SetNumberField(TEXT("position_y"), NewNode->NodePosY);
		Root->SetArrayField(TEXT("pins"), BuildPinList(NewNode));
		return FMonolithActionResult::Success(Root);
	}

	// Create the template node on the transient package (will be duplicated by PerformAction)
	UAnimGraphNode_Base* Template = Cast<UAnimGraphNode_Base>(NewObject<UObject>(GetTransientPackage(), NodeClass));
	if (!Template)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to create node template for class '%s'"), *NodeClass->GetPathName()));
	}

	const UEdGraphSchema* TargetSchema = TargetGraph->GetSchema();
	if (!TargetSchema || !Template->CanCreateUnderSpecifiedSchema(TargetSchema))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Class '%s' cannot be created under target graph '%s' with schema '%s'. Use an AnimGraph or animation state graph."),
			*NodeClass->GetPathName(),
			*TargetGraph->GetName(),
			TargetSchema ? *TargetSchema->GetClass()->GetName() : TEXT("<null>")));
	}

	// Set animation asset before spawning (gets duplicated with the node)
	if (!AnimAsset.IsEmpty())
	{
		UAnimGraphNode_AssetPlayerBase* AssetPlayer = Cast<UAnimGraphNode_AssetPlayerBase>(Template);
		if (AssetPlayer)
		{
			UAnimationAsset* Asset = FMonolithAssetUtils::LoadAssetByPath<UAnimationAsset>(AnimAsset);
			if (!Asset)
			{
				return FMonolithActionResult::Error(FString::Printf(TEXT("Animation asset not found: %s"), *AnimAsset));
			}
			AssetPlayer->SetAnimationAsset(Asset);
		}
		else
		{
			// Non-asset-player node doesn't support anim_asset — just warn via log, don't fail
			UE_LOG(LogTemp, Warning, TEXT("Monolith: Node type '%s' does not support anim_asset parameter — ignored"), *NodeType);
		}
	}

	// Skeletal control node configuration (set on template before spawn)
	if (UAnimGraphNode_TwoBoneIK* IKTemplate = Cast<UAnimGraphNode_TwoBoneIK>(Template))
	{
		FString IKBone;
		if (Params->TryGetStringField(TEXT("ik_bone"), IKBone) && !IKBone.IsEmpty())
		{
			IKTemplate->Node.IKBone.BoneName = FName(*IKBone);
		}
		FString EffectorSpace;
		if (Params->TryGetStringField(TEXT("effector_space"), EffectorSpace))
		{
			IKTemplate->Node.EffectorLocationSpace = ParseBoneControlSpace(EffectorSpace);
		}
		FString JointTargetSpace;
		if (Params->TryGetStringField(TEXT("joint_target_space"), JointTargetSpace))
		{
			IKTemplate->Node.JointTargetLocationSpace = ParseBoneControlSpace(JointTargetSpace);
		}
	}
	else if (UAnimGraphNode_ModifyBone* ModifyTemplate = Cast<UAnimGraphNode_ModifyBone>(Template))
	{
		FString ModifyBoneName;
		if (Params->TryGetStringField(TEXT("bone_to_modify"), ModifyBoneName) && !ModifyBoneName.IsEmpty())
		{
			ModifyTemplate->Node.BoneToModify.BoneName = FName(*ModifyBoneName);
		}
	}

	GEditor->BeginTransaction(FText::FromString(TEXT("Add Anim Graph Node")));
	TargetGraph->Modify();

	// Spawn via FEdGraphSchemaAction_K2NewNode — same path as the editor
	FEdGraphSchemaAction_K2NewNode Action;
	Action.NodeTemplate = Template;
	UEdGraphNode* SpawnedNode = Action.PerformAction(TargetGraph, /*FromPin=*/nullptr, FVector2f(PosX, PosY), /*bSelectNewNode=*/false);

	GEditor->EndTransaction();

	if (!SpawnedNode)
	{
		return FMonolithActionResult::Error(TEXT("PerformAction failed — node was not spawned. Check that the target graph supports this node type."));
	}

	// Expose optional-pin properties (e.g. EffectorLocation, JointTargetLocation, Alpha on TwoBoneIK)
	{
		UAnimGraphNode_Base* SpawnedAnim = Cast<UAnimGraphNode_Base>(SpawnedNode);
		if (SpawnedAnim)
		{
			TArray<FName> PinsToExpose;

			const TArray<TSharedPtr<FJsonValue>>* ExposePinsArr = nullptr;
			if (Params->TryGetArrayField(TEXT("expose_pins"), ExposePinsArr) && ExposePinsArr)
			{
				for (const TSharedPtr<FJsonValue>& V : *ExposePinsArr)
				{
					if (V.IsValid()) PinsToExpose.AddUnique(FName(*V->AsString()));
				}
			}

			// TwoBoneIK defaults: auto-expose common input pins
			if (Cast<UAnimGraphNode_TwoBoneIK>(SpawnedAnim) && PinsToExpose.Num() == 0)
			{
				PinsToExpose.Add(TEXT("EffectorLocation"));
				PinsToExpose.Add(TEXT("JointTargetLocation"));
				PinsToExpose.Add(TEXT("Alpha"));
			}

			bool bAnyExposed = false;
			for (FOptionalPinFromProperty& OptPin : SpawnedAnim->ShowPinForProperties)
			{
				if (PinsToExpose.Contains(OptPin.PropertyName) && !OptPin.bShowPin)
				{
					OptPin.bShowPin = true;
					bAnyExposed = true;
				}
			}
			if (bAnyExposed)
			{
				SpawnedAnim->ReconstructNode();
			}
		}
	}

	// Do NOT compile here — caller should batch node adds then wire, then compile once.
	// Just mark dirty.
	ABP->MarkPackageDirty();

	// Build response
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("node_name"), SpawnedNode->GetName());
	Root->SetStringField(TEXT("node_class"), SpawnedNode->GetClass()->GetName());
	Root->SetStringField(TEXT("node_class_path"), SpawnedNode->GetClass()->GetPathName());
	Root->SetStringField(TEXT("node_guid"), SpawnedNode->NodeGuid.ToString());
	Root->SetNumberField(TEXT("position_x"), SpawnedNode->NodePosX);
	Root->SetNumberField(TEXT("position_y"), SpawnedNode->NodePosY);
	Root->SetArrayField(TEXT("pins"), BuildPinList(SpawnedNode));
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: connect_anim_graph_pins
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleConnectAnimGraphPins(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath  = Params->GetStringField(TEXT("asset_path"));
	FString SourceNode = Params->GetStringField(TEXT("source_node"));
	FString SourcePin  = Params->GetStringField(TEXT("source_pin"));
	FString TargetNode = Params->GetStringField(TEXT("target_node"));
	FString TargetPin  = Params->GetStringField(TEXT("target_pin"));
	FString GraphName  = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("");
	FString StateName  = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	bool bCompile = true;
	if (Params->HasField(TEXT("compile")))
	{
		bCompile = Params->GetBoolField(TEXT("compile"));
	}

	if (SourceNode.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: source_node"));
	if (SourcePin.IsEmpty())  return FMonolithActionResult::Error(TEXT("Missing required parameter: source_pin"));
	if (TargetNode.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: target_node"));
	if (TargetPin.IsEmpty())  return FMonolithActionResult::Error(TEXT("Missing required parameter: target_pin"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	// Optionally resolve to a specific graph for scoping the search
	UEdGraph* ScopeGraph = nullptr;
	if (!StateName.IsEmpty() || (!GraphName.IsEmpty() && !GraphName.Equals(TEXT("AnimGraph"), ESearchCase::IgnoreCase)))
	{
		FString GraphError;
		ScopeGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
		// If scope resolution fails, we still search globally as fallback
	}

	// Find source and target nodes
	UEdGraphNode* SrcNode = FindNodeByName(ABP, SourceNode, ScopeGraph);
	if (!SrcNode)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Source node '%s' not found in ABP"), *SourceNode));
	}

	UEdGraphNode* DstNode = FindNodeByName(ABP, TargetNode, ScopeGraph);
	if (!DstNode)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Target node '%s' not found in ABP"), *TargetNode));
	}

	// Find output pin on source
	UEdGraphPin* OutPin = SrcNode->FindPin(FName(*SourcePin), EGPD_Output);
	if (!OutPin)
	{
		// List available output pins for debugging
		FString AvailPins;
		for (UEdGraphPin* P : SrcNode->Pins)
		{
			if (P && P->Direction == EGPD_Output)
			{
				if (!AvailPins.IsEmpty()) AvailPins += TEXT(", ");
				AvailPins += P->PinName.ToString();
			}
		}
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Output pin '%s' not found on node '%s'. Available output pins: [%s]"),
			*SourcePin, *SourceNode, *AvailPins));
	}

	// Find input pin on target
	UEdGraphPin* InPin = DstNode->FindPin(FName(*TargetPin), EGPD_Input);
	if (!InPin)
	{
		FString AvailPins;
		for (UEdGraphPin* P : DstNode->Pins)
		{
			if (P && P->Direction == EGPD_Input)
			{
				if (!AvailPins.IsEmpty()) AvailPins += TEXT(", ");
				AvailPins += P->PinName.ToString();
			}
		}
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Input pin '%s' not found on node '%s'. Available input pins: [%s]"),
			*TargetPin, *TargetNode, *AvailPins));
	}

	// Verify both nodes are in the same graph
	if (SrcNode->GetGraph() != DstNode->GetGraph())
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Source node '%s' and target node '%s' are in different graphs — connections must be within the same graph"),
			*SourceNode, *TargetNode));
	}

	GEditor->BeginTransaction(FText::FromString(TEXT("Connect Anim Graph Pins")));
	SrcNode->GetGraph()->Modify();

	// Use the graph's own schema for the connection (UAnimationGraphSchema or UAnimationStateGraphSchema)
	const UEdGraphSchema* Schema = SrcNode->GetGraph()->GetSchema();
	const bool bConnected = Schema->TryCreateConnection(OutPin, InPin);

	GEditor->EndTransaction();

	if (!bConnected)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("TryCreateConnection failed: '%s.%s' -> '%s.%s'. Pin types may be incompatible."),
			*SourceNode, *SourcePin, *TargetNode, *TargetPin));
	}

	if (bCompile)
	{
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
		FKismetEditorUtilities::CompileBlueprint(ABP);
	}

	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("source_node"), SourceNode);
	Root->SetStringField(TEXT("source_pin"), SourcePin);
	Root->SetStringField(TEXT("target_node"), TargetNode);
	Root->SetStringField(TEXT("target_pin"), TargetPin);
	Root->SetBoolField(TEXT("compiled"), bCompile);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: set_state_animation
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleSetStateAnimation(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath    = Params->GetStringField(TEXT("asset_path"));
	FString MachineName  = Params->GetStringField(TEXT("machine_name"));
	FString StateName    = Params->GetStringField(TEXT("state_name"));
	FString AnimAssetPath = Params->GetStringField(TEXT("anim_asset_path"));

	bool bLoop = false;
	if (Params->HasField(TEXT("loop")))
	{
		bLoop = Params->GetBoolField(TEXT("loop"));
	}

	bool bClearExisting = true;
	if (Params->HasField(TEXT("clear_existing")))
	{
		bClearExisting = Params->GetBoolField(TEXT("clear_existing"));
	}

	if (MachineName.IsEmpty())  return FMonolithActionResult::Error(TEXT("Missing required parameter: machine_name"));
	if (StateName.IsEmpty())    return FMonolithActionResult::Error(TEXT("Missing required parameter: state_name"));
	if (AnimAssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: anim_asset_path"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	// Find the state machine and state
	UAnimationStateMachineGraph* SMGraph = FindSMGraphByName(ABP, MachineName);
	if (!SMGraph) return FMonolithActionResult::Error(FString::Printf(TEXT("State machine '%s' not found in ABP"), *MachineName));

	UAnimStateNode* StateNode = FindStateByName(SMGraph, StateName);
	if (!StateNode) return FMonolithActionResult::Error(FString::Printf(TEXT("State '%s' not found in machine '%s'"), *StateName, *MachineName));

	UAnimationStateGraph* StateGraph = Cast<UAnimationStateGraph>(StateNode->BoundGraph);
	if (!StateGraph) return FMonolithActionResult::Error(FString::Printf(TEXT("State '%s' has no inner animation graph"), *StateName));

	UAnimGraphNode_StateResult* ResultNode = StateGraph->MyResultNode;
	if (!ResultNode) return FMonolithActionResult::Error(FString::Printf(TEXT("State '%s' has no result node — state graph may be corrupt"), *StateName));

	// Load the animation asset
	UAnimationAsset* AnimAsset = FMonolithAssetUtils::LoadAssetByPath<UAnimationAsset>(AnimAssetPath);
	if (!AnimAsset) return FMonolithActionResult::Error(FString::Printf(TEXT("Animation asset not found: %s"), *AnimAssetPath));

	// Determine node class using the engine's own mapping
	UClass* NodeClass = GetNodeClassForAsset(AnimAsset->GetClass());
	if (!NodeClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("No animation player node type for asset class '%s'. Supported: AnimSequence, BlendSpace."),
			*AnimAsset->GetClass()->GetName()));
	}

	GEditor->BeginTransaction(FText::FromString(TEXT("Set State Animation")));
	StateGraph->Modify();

	// Find the Result input pin
	UEdGraphPin* ResultInputPin = ResultNode->FindPin(TEXT("Result"), EGPD_Input);
	if (!ResultInputPin)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("Could not find 'Result' input pin on state result node"));
	}

	// Optionally clear existing nodes wired to the result
	if (bClearExisting)
	{
		// Collect nodes currently connected to the result pin
		TArray<UEdGraphNode*> NodesToRemove;
		for (UEdGraphPin* LinkedPin : ResultInputPin->LinkedTo)
		{
			if (LinkedPin && LinkedPin->GetOwningNode())
			{
				NodesToRemove.Add(LinkedPin->GetOwningNode());
			}
		}

		// Break all connections to the result pin
		ResultInputPin->BreakAllPinLinks();

		// Remove the previously-wired nodes (but not the result node itself)
		for (UEdGraphNode* OldNode : NodesToRemove)
		{
			if (OldNode && OldNode != ResultNode)
			{
				OldNode->BreakAllNodeLinks();
				StateGraph->RemoveNode(OldNode);
			}
		}
	}

	// Create template node on transient package
	UAnimGraphNode_AssetPlayerBase* Template = Cast<UAnimGraphNode_AssetPlayerBase>(
		NewObject<UObject>(GetTransientPackage(), NodeClass));
	if (!Template)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("Failed to create animation player node template"));
	}

	Template->SetAnimationAsset(AnimAsset);
	Template->CopySettingsFromAnimationAsset(AnimAsset);

	// Set loop flag if requested — need to access the FAnimNode struct via reflection
	if (bLoop)
	{
		// Try to set bLoopAnimation via the runtime node struct
		FStructProperty* NodeProp = Template->GetFNodeProperty();
		if (NodeProp)
		{
			void* NodePtr = NodeProp->ContainerPtrToValuePtr<void>(Template);
			FProperty* LoopProp = NodeProp->Struct->FindPropertyByName(FName(TEXT("bLoopAnimation")));
			if (LoopProp)
			{
				FBoolProperty* BoolProp = CastField<FBoolProperty>(LoopProp);
				if (BoolProp)
				{
					BoolProp->SetPropertyValue(BoolProp->ContainerPtrToValuePtr<void>(NodePtr), true);
				}
			}
		}
	}

	// Spawn into the state graph, positioned to the left of the result node
	float SpawnX = static_cast<float>(ResultNode->NodePosX - 300);
	float SpawnY = static_cast<float>(ResultNode->NodePosY);

	FEdGraphSchemaAction_K2NewNode Action;
	Action.NodeTemplate = Template;
	UEdGraphNode* SpawnedNode = Action.PerformAction(StateGraph, /*FromPin=*/nullptr, FVector2f(SpawnX, SpawnY), /*bSelectNewNode=*/false);

	if (!SpawnedNode)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("PerformAction failed — animation player node was not spawned"));
	}

	// Wire the pose output to the result input
	UEdGraphPin* PoseOutput = SpawnedNode->FindPin(TEXT("Pose"), EGPD_Output);
	if (!PoseOutput)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("Spawned node has no 'Pose' output pin — cannot wire to state result"));
	}

	const UEdGraphSchema* Schema = StateGraph->GetSchema();
	const bool bWired = Schema->TryCreateConnection(PoseOutput, ResultInputPin);

	GEditor->EndTransaction();

	if (!bWired)
	{
		return FMonolithActionResult::Error(TEXT("TryCreateConnection failed wiring Pose -> Result. The node was spawned but not connected."));
	}

	// Compile
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	// Build response
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("machine_name"), MachineName);
	Root->SetStringField(TEXT("state_name"), StateName);
	Root->SetStringField(TEXT("anim_asset_path"), AnimAssetPath);
	Root->SetStringField(TEXT("node_name"), SpawnedNode->GetName());
	Root->SetStringField(TEXT("node_class"), SpawnedNode->GetClass()->GetName());
	Root->SetBoolField(TEXT("loop"), bLoop);
	Root->SetBoolField(TEXT("cleared_existing"), bClearExisting);
	Root->SetArrayField(TEXT("pins"), BuildPinList(SpawnedNode));
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: add_variable_get
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddVariableGet(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString VarName   = Params->GetStringField(TEXT("variable_name"));
	FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	double TempVal;
	float PosX = 0.f;
	float PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	if (VarName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: variable_name"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	// Validate variable exists on skeleton class (BP-declared or C++ UPROPERTY)
	const FName VarFName(*VarName);
	UClass* SkeletonClass = ABP->SkeletonGeneratedClass ? ABP->SkeletonGeneratedClass : ABP->GeneratedClass;
	if (SkeletonClass && !SkeletonClass->FindPropertyByName(VarFName))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Variable '%s' not found on %s — check spelling and BlueprintReadOnly/ReadWrite on the UPROPERTY."),
			*VarName, *SkeletonClass->GetName()));
	}

	UK2Node_VariableGet* Template = NewObject<UK2Node_VariableGet>(GetTransientPackage());
	Template->VariableReference.SetSelfMember(VarFName);

	GEditor->BeginTransaction(FText::FromString(TEXT("Add Variable Get")));
	TargetGraph->Modify();

	FEdGraphSchemaAction_K2NewNode Action;
	Action.NodeTemplate = Template;
	UEdGraphNode* SpawnedNode = Action.PerformAction(TargetGraph, /*FromPin=*/nullptr, FVector2f(PosX, PosY), /*bSelectNewNode=*/false);

	GEditor->EndTransaction();

	if (!SpawnedNode)
	{
		return FMonolithActionResult::Error(TEXT("PerformAction failed for K2Node_VariableGet."));
	}

	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("node_name"), SpawnedNode->GetName());
	Root->SetStringField(TEXT("node_class"), SpawnedNode->GetClass()->GetName());
	Root->SetStringField(TEXT("node_guid"), SpawnedNode->NodeGuid.ToString());
	Root->SetStringField(TEXT("variable_name"), VarName);
	Root->SetNumberField(TEXT("position_x"), SpawnedNode->NodePosX);
	Root->SetNumberField(TEXT("position_y"), SpawnedNode->NodePosY);
	Root->SetArrayField(TEXT("pins"), BuildPinList(SpawnedNode));
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: set_anim_graph_node_property
// ---------------------------------------------------------------------------

namespace
{
/**
 * Resolve a dotted property path inside a container (struct value).
 * On success, `OutProperty` is the final property, `OutContainer` is the
 * address of the immediately-enclosing struct/object where that property lives.
 *
 *   path="BoneToModify.BoneName"  →  Prop=FNameProperty, Container=&Node.BoneToModify
 *   path="RotationMode"            →  Prop=FEnumProperty,  Container=&Node
 */
bool ResolvePropertyPath(UStruct* StructType, void* StructAddr, const FString& Path,
                         FProperty*& OutProperty, void*& OutContainer, FString& OutError)
{
	TArray<FString> Tokens;
	Path.ParseIntoArray(Tokens, TEXT("."));
	if (Tokens.Num() == 0)
	{
		OutError = TEXT("property_path is empty");
		return false;
	}

	UStruct* Cursor = StructType;
	void*    Addr   = StructAddr;

	for (int32 i = 0; i < Tokens.Num(); ++i)
	{
		const FString& Tok = Tokens[i];
		FProperty* Prop = Cursor ? Cursor->FindPropertyByName(FName(*Tok)) : nullptr;
		if (!Prop)
		{
			OutError = FString::Printf(TEXT("Property '%s' not found on %s"),
				*Tok, Cursor ? *Cursor->GetName() : TEXT("<null>"));
			return false;
		}

		if (i == Tokens.Num() - 1)
		{
			OutProperty  = Prop;
			OutContainer = Addr;
			return true;
		}

		// Descend into nested structs.
		FStructProperty* StructProp = CastField<FStructProperty>(Prop);
		if (!StructProp)
		{
			OutError = FString::Printf(TEXT("Cannot descend into '%s' — not a struct property"), *Tok);
			return false;
		}
		Cursor = StructProp->Struct;
		Addr   = StructProp->ContainerPtrToValuePtr<void>(Addr);
	}

	OutError = TEXT("unreachable");
	return false;
}

// ---------------------------------------------------------------------------
// Shared FAnimNode reflection helpers (Sprint 4 — reused by the MM graph
// configure/build handlers; mirror the resolution path in
// HandleSetAnimGraphNodeProperty).
// ---------------------------------------------------------------------------

/**
 * Resolve the inner FAnimNode struct (its UStruct + value address) on an
 * editor UAnimGraphNode_Base. Every UAnimGraphNode_X holds a UPROPERTY-tagged
 * FAnimNode_X member; we scan for the first FStructProperty derived from
 * FAnimNode_Base (same heuristic as HandleSetAnimGraphNodeProperty).
 */
bool ResolveInnerAnimNode(UAnimGraphNode_Base* AnimNode, UScriptStruct*& OutStruct,
                          void*& OutAddr, FString& OutError)
{
	OutStruct = nullptr;
	OutAddr = nullptr;
	for (TFieldIterator<FStructProperty> It(AnimNode->GetClass()); It; ++It)
	{
		FStructProperty* P = *It;
		if (!P || !P->Struct) continue;
		if (P->Struct->IsChildOf(FAnimNode_Base::StaticStruct()))
		{
			OutStruct = P->Struct;
			OutAddr   = P->ContainerPtrToValuePtr<void>(AnimNode);
			return true;
		}
	}
	OutError = FString::Printf(
		TEXT("Could not locate FAnimNode struct on '%s' — does the class inherit from FAnimNode_Base?"),
		*AnimNode->GetClass()->GetName());
	return false;
}

/** Write a named property on a struct via ImportText (the Details-panel parser). Searches superstructs. */
bool ImportTextOntoStruct(UScriptStruct* Struct, void* StructAddr, const FName& PropName,
                          const FString& Value, UObject* Owner, FString& OutError)
{
	FProperty* Prop = Struct ? Struct->FindPropertyByName(PropName) : nullptr;
	if (!Prop)
	{
		OutError = FString::Printf(TEXT("Property '%s' not found on %s"),
			*PropName.ToString(), Struct ? *Struct->GetName() : TEXT("<null>"));
		return false;
	}
	void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(StructAddr);
	const TCHAR* Result = Prop->ImportText_Direct(*Value, ValuePtr, Owner, PPF_None);
	if (!Result)
	{
		OutError = FString::Printf(TEXT("ImportText failed for '%s' with value '%s'"),
			*PropName.ToString(), *Value);
		return false;
	}
	return true;
}

/**
 * Write a TArray<FBoneReference> property from an array of bone-name strings.
 * Builds the array element-by-element via reflection so we never depend on
 * the typed FBoneReference header layout beyond its `BoneName` FName field.
 */
bool WriteBoneReferenceArray(UScriptStruct* Struct, void* StructAddr, const FName& PropName,
                             const TArray<FString>& BoneNames, FString& OutError)
{
	FProperty* Prop = Struct ? Struct->FindPropertyByName(PropName) : nullptr;
	FArrayProperty* ArrayProp = CastField<FArrayProperty>(Prop);
	if (!ArrayProp)
	{
		OutError = FString::Printf(TEXT("Property '%s' is not an array property"), *PropName.ToString());
		return false;
	}
	FStructProperty* ElemStructProp = CastField<FStructProperty>(ArrayProp->Inner);
	if (!ElemStructProp || !ElemStructProp->Struct)
	{
		OutError = FString::Printf(TEXT("Array '%s' inner is not a struct"), *PropName.ToString());
		return false;
	}
	FProperty* BoneNameProp = ElemStructProp->Struct->FindPropertyByName(TEXT("BoneName"));
	FNameProperty* NameProp = CastField<FNameProperty>(BoneNameProp);
	if (!NameProp)
	{
		OutError = FString::Printf(TEXT("Element struct of '%s' has no FName 'BoneName' field"), *PropName.ToString());
		return false;
	}

	void* ArrayValuePtr = ArrayProp->ContainerPtrToValuePtr<void>(StructAddr);
	FScriptArrayHelper Helper(ArrayProp, ArrayValuePtr);
	Helper.EmptyValues();
	for (const FString& BoneName : BoneNames)
	{
		const int32 Index = Helper.AddValue();
		void* ElemPtr = Helper.GetRawPtr(Index);
		void* NamePtr = NameProp->ContainerPtrToValuePtr<void>(ElemPtr);
		NameProp->SetPropertyValue(NamePtr, FName(*BoneName));
	}
	return true;
}

} // anonymous namespace

FMonolithActionResult FMonolithAbpWriteActions::HandleSetAnimGraphNodeProperty(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath    = Params->GetStringField(TEXT("asset_path"));
	FString NodeId       = Params->GetStringField(TEXT("node_id"));
	FString PropertyPath = Params->GetStringField(TEXT("property_path"));
	FString Value        = Params->GetStringField(TEXT("value"));
	FString GraphName    = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("");
	FString StateName    = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	if (NodeId.IsEmpty())       return FMonolithActionResult::Error(TEXT("Missing required parameter: node_id"));
	if (PropertyPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: property_path"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	// Optional graph scope — same resolution as connect_anim_graph_pins.
	UEdGraph* ScopeGraph = nullptr;
	if (!StateName.IsEmpty() || (!GraphName.IsEmpty() && !GraphName.Equals(TEXT("AnimGraph"), ESearchCase::IgnoreCase)))
	{
		FString GraphError;
		ScopeGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	}

	UEdGraphNode* FoundNode = FindNodeByName(ABP, NodeId, ScopeGraph);
	if (!FoundNode)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node '%s' not found"), *NodeId));
	}

	UAnimGraphNode_Base* AnimNode = Cast<UAnimGraphNode_Base>(FoundNode);
	if (!AnimNode)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Node '%s' is not a UAnimGraphNode_Base (class: %s) — this action only mutates anim graph nodes"),
			*NodeId, *FoundNode->GetClass()->GetName()));
	}

	// Find the inner `Node` FStructProperty on the UAnimGraphNode subclass. Every
	// UAnimGraphNode_X has a UPROPERTY-tagged FAnimNode_X field — conventionally
	// named "Node", but some subclasses rename it, so we scan for any FStructProperty
	// whose struct inherits from FAnimNode_Base.
	FStructProperty* NodeStructProp = nullptr;
	for (TFieldIterator<FStructProperty> It(AnimNode->GetClass()); It; ++It)
	{
		FStructProperty* P = *It;
		if (!P || !P->Struct) continue;
		// Heuristic: accept any struct derived from FAnimNode_Base.
		if (P->Struct->IsChildOf(FAnimNode_Base::StaticStruct()))
		{
			NodeStructProp = P;
			break;
		}
	}
	if (!NodeStructProp)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not locate FAnimNode struct on '%s' — does the class inherit from FAnimNode_Base?"),
			*AnimNode->GetClass()->GetName()));
	}

	void* NodeStructAddr = NodeStructProp->ContainerPtrToValuePtr<void>(AnimNode);

	FProperty* TargetProp   = nullptr;
	void*      TargetContainer = nullptr;
	FString    ResolveError;
	if (!ResolvePropertyPath(NodeStructProp->Struct, NodeStructAddr, PropertyPath, TargetProp, TargetContainer, ResolveError))
	{
		return FMonolithActionResult::Error(ResolveError);
	}

	// Capture old value for diff.
	FString OldValueText;
	TargetProp->ExportText_InContainer(0, OldValueText, TargetContainer, TargetContainer, nullptr, PPF_None);

	// Write via ImportText — same parser the Details panel uses.
	AnimNode->Modify();
	const TCHAR* Buffer = *Value;
	void* TargetValue = TargetProp->ContainerPtrToValuePtr<void>(TargetContainer);
	const TCHAR* ImportResult = TargetProp->ImportText_Direct(Buffer, TargetValue, AnimNode, PPF_None);
	if (!ImportResult)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("ImportText failed for property '%s' with value '%s'"),
			*PropertyPath, *Value));
	}

	FString NewValueText;
	TargetProp->ExportText_InContainer(0, NewValueText, TargetContainer, TargetContainer, nullptr, PPF_None);

	// Refresh the node's UI and notify the BP so the change isn't lost on next save.
	AnimNode->ReconstructNode();
	ABP->MarkPackageDirty();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_id"), AnimNode->GetName());
	Root->SetStringField(TEXT("property_path"), PropertyPath);
	Root->SetStringField(TEXT("old_value"), OldValueText);
	Root->SetStringField(TEXT("new_value"), NewValueText);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: configure_pose_history_node (Sprint 4.2)
// Writes FAnimNode_PoseSearchHistoryCollector_Base properties by reflection.
// Trajectory comes from bGenerateTrajectory — there is NO CharacterTrajectoryComponent
// in UE 5.7 (gotcha #3).
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleConfigurePoseHistoryNode(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath = Params->GetStringField(TEXT("abp_path"));
	const FString NodeId  = Params->GetStringField(TEXT("node_id"));
	if (NodeId.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: node_id"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AbpPath));

	UEdGraphNode* FoundNode = FindNodeByName(ABP, NodeId, nullptr);
	if (!FoundNode) return FMonolithActionResult::Error(FString::Printf(TEXT("Node '%s' not found"), *NodeId));

	UAnimGraphNode_Base* AnimNode = Cast<UAnimGraphNode_Base>(FoundNode);
	if (!AnimNode) return FMonolithActionResult::Error(FString::Printf(
		TEXT("Node '%s' is not a UAnimGraphNode_Base (class: %s)"), *NodeId, *FoundNode->GetClass()->GetName()));

	UScriptStruct* NodeStruct = nullptr;
	void* NodeAddr = nullptr;
	FString ResolveError;
	if (!ResolveInnerAnimNode(AnimNode, NodeStruct, NodeAddr, ResolveError))
		return FMonolithActionResult::Error(ResolveError);

	GEditor->BeginTransaction(FText::FromString(TEXT("Configure Pose History Node")));
	AnimNode->Modify();

	TSharedPtr<FJsonObject> Applied = MakeShared<FJsonObject>();
	FString WriteError;
	bool bAnyWrite = false;

	bool bGenTraj;
	if (Params->TryGetBoolField(TEXT("generate_trajectory"), bGenTraj))
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("bGenerateTrajectory"), bGenTraj ? TEXT("true") : TEXT("false"), AnimNode, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetBoolField(TEXT("bGenerateTrajectory"), bGenTraj); bAnyWrite = true;
	}

	double NumVal = 0.0;
	if (Params->TryGetNumberField(TEXT("pose_count"), NumVal))
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("PoseCount"), FString::FromInt(static_cast<int32>(NumVal)), AnimNode, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetNumberField(TEXT("PoseCount"), static_cast<int32>(NumVal)); bAnyWrite = true;
	}
	if (Params->TryGetNumberField(TEXT("sampling_interval"), NumVal))
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("SamplingInterval"), FString::SanitizeFloat(NumVal), AnimNode, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetNumberField(TEXT("SamplingInterval"), NumVal); bAnyWrite = true;
	}
	if (Params->TryGetNumberField(TEXT("trajectory_history_count"), NumVal))
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("TrajectoryHistoryCount"), FString::FromInt(static_cast<int32>(NumVal)), AnimNode, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetNumberField(TEXT("TrajectoryHistoryCount"), static_cast<int32>(NumVal)); bAnyWrite = true;
	}
	if (Params->TryGetNumberField(TEXT("trajectory_prediction_count"), NumVal))
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("TrajectoryPredictionCount"), FString::FromInt(static_cast<int32>(NumVal)), AnimNode, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetNumberField(TEXT("TrajectoryPredictionCount"), static_cast<int32>(NumVal)); bAnyWrite = true;
	}

	const TArray<TSharedPtr<FJsonValue>>* BonesArr = nullptr;
	if (Params->TryGetArrayField(TEXT("collected_bones"), BonesArr) && BonesArr)
	{
		TArray<FString> BoneNames;
		for (const TSharedPtr<FJsonValue>& V : *BonesArr)
		{
			if (V.IsValid()) BoneNames.Add(V->AsString());
		}
		if (!WriteBoneReferenceArray(NodeStruct, NodeAddr, TEXT("CollectedBones"), BoneNames, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetNumberField(TEXT("CollectedBones"), BoneNames.Num()); bAnyWrite = true;
	}

	GEditor->EndTransaction();

	if (bAnyWrite)
	{
		AnimNode->ReconstructNode();
		ABP->MarkPackageDirty();
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("node_id"), AnimNode->GetName());
	Root->SetStringField(TEXT("node_struct"), NodeStruct->GetName());
	Root->SetObjectField(TEXT("applied"), Applied);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: configure_motion_matching_node (Sprint 4.3)
// Writes FAnimNode_MotionMatching props + base FAnimNode_BlendStack_Standalone
// props by reflection. MaxActiveBlends / bShouldFilterNotifies / NotifyRecencyTimeOut
// live on the BASE struct (gotcha #4); FindPropertyByName walks superstructs so the
// reflection write resolves them regardless. PoseJumpThresholdTime is FFloatInterval
// (gotcha #5) — written as (Min=..,Max=..).
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleConfigureMotionMatchingNode(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath = Params->GetStringField(TEXT("abp_path"));
	const FString NodeId  = Params->GetStringField(TEXT("node_id"));
	if (NodeId.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: node_id"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AbpPath));

	UEdGraphNode* FoundNode = FindNodeByName(ABP, NodeId, nullptr);
	if (!FoundNode) return FMonolithActionResult::Error(FString::Printf(TEXT("Node '%s' not found"), *NodeId));

	UAnimGraphNode_Base* AnimNode = Cast<UAnimGraphNode_Base>(FoundNode);
	if (!AnimNode) return FMonolithActionResult::Error(FString::Printf(
		TEXT("Node '%s' is not a UAnimGraphNode_Base (class: %s)"), *NodeId, *FoundNode->GetClass()->GetName()));

	UScriptStruct* NodeStruct = nullptr;
	void* NodeAddr = nullptr;
	FString ResolveError;
	if (!ResolveInnerAnimNode(AnimNode, NodeStruct, NodeAddr, ResolveError))
		return FMonolithActionResult::Error(ResolveError);

	GEditor->BeginTransaction(FText::FromString(TEXT("Configure Motion Matching Node")));
	AnimNode->Modify();

	TSharedPtr<FJsonObject> Applied = MakeShared<FJsonObject>();
	FString WriteError;
	bool bAnyWrite = false;
	double NumVal = 0.0;
	bool BoolVal = false;

	auto WriteNum = [&](const TCHAR* JsonKey, const FName& Prop, bool bAsInt) -> bool
	{
		double V;
		if (!Params->TryGetNumberField(JsonKey, V)) return true; // not provided — skip
		const FString Text = bAsInt ? FString::FromInt(static_cast<int32>(V)) : FString::SanitizeFloat(V);
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, Prop, Text, AnimNode, WriteError)) return false;
		if (bAsInt) Applied->SetNumberField(Prop.ToString(), static_cast<int32>(V));
		else        Applied->SetNumberField(Prop.ToString(), V);
		bAnyWrite = true;
		return true;
	};

	if (!WriteNum(TEXT("blend_time"), TEXT("BlendTime"), false))
	{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
	if (!WriteNum(TEXT("search_throttle"), TEXT("SearchThrottleTime"), false))
	{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
	if (!WriteNum(TEXT("notify_recency_timeout"), TEXT("NotifyRecencyTimeOut"), false))
	{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
	if (!WriteNum(TEXT("max_active_blends"), TEXT("MaxActiveBlends"), true))
	{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }

	if (Params->TryGetBoolField(TEXT("use_inertial_blend"), BoolVal))
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("bUseInertialBlend"), BoolVal ? TEXT("true") : TEXT("false"), AnimNode, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetBoolField(TEXT("bUseInertialBlend"), BoolVal); bAnyWrite = true;
	}
	if (Params->TryGetBoolField(TEXT("should_filter_notifies"), BoolVal))
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("bShouldFilterNotifies"), BoolVal ? TEXT("true") : TEXT("false"), AnimNode, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetBoolField(TEXT("bShouldFilterNotifies"), BoolVal); bAnyWrite = true;
	}

	// PoseJumpThresholdTime is an FFloatInterval — resolve current Min/Max, override
	// whichever was supplied, then write the whole struct via ImportText (Min=..,Max=..).
	const bool bHasMin = Params->TryGetNumberField(TEXT("pose_jump_threshold_min"), NumVal);
	double JumpMin = NumVal;
	const bool bHasMax = Params->TryGetNumberField(TEXT("pose_jump_threshold_max"), NumVal);
	double JumpMax = NumVal;
	if (bHasMin || bHasMax)
	{
		FProperty* IntervalProp = NodeStruct->FindPropertyByName(TEXT("PoseJumpThresholdTime"));
		FStructProperty* IntervalStructProp = CastField<FStructProperty>(IntervalProp);
		if (!IntervalStructProp)
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(TEXT("PoseJumpThresholdTime is not a struct property")); }

		// Read existing values to preserve the un-supplied side.
		void* IntervalAddr = IntervalStructProp->ContainerPtrToValuePtr<void>(NodeAddr);
		double CurMin = 0.0, CurMax = 0.0;
		if (FFloatProperty* MinP = CastField<FFloatProperty>(IntervalStructProp->Struct->FindPropertyByName(TEXT("Min"))))
			CurMin = MinP->GetPropertyValue_InContainer(IntervalAddr);
		if (FFloatProperty* MaxP = CastField<FFloatProperty>(IntervalStructProp->Struct->FindPropertyByName(TEXT("Max"))))
			CurMax = MaxP->GetPropertyValue_InContainer(IntervalAddr);

		const double FinalMin = bHasMin ? JumpMin : CurMin;
		const double FinalMax = bHasMax ? JumpMax : CurMax;
		const FString IntervalText = FString::Printf(TEXT("(Min=%s,Max=%s)"),
			*FString::SanitizeFloat(FinalMin), *FString::SanitizeFloat(FinalMax));
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("PoseJumpThresholdTime"), IntervalText, AnimNode, WriteError))
		{ GEditor->EndTransaction(); return FMonolithActionResult::Error(WriteError); }
		Applied->SetStringField(TEXT("PoseJumpThresholdTime"), IntervalText); bAnyWrite = true;
	}

	GEditor->EndTransaction();

	if (bAnyWrite)
	{
		AnimNode->ReconstructNode();
		ABP->MarkPackageDirty();
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("node_id"), AnimNode->GetName());
	Root->SetStringField(TEXT("node_struct"), NodeStruct->GetName());
	Root->SetObjectField(TEXT("applied"), Applied);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: build_motion_matching_node (Sprint 4.4 — COMPOSITE)
// Spawns a Pose History + Motion Matching node via the existing add_anim_graph_node
// internals (using the 4.1 "pose_history" alias), wires History pose-out -> MM
// pose-in via the connect internals, then assigns the MM Database pointer directly
// (a UObject pointer write, NOT AddAnimationAsset). Applies 4.2/4.3 defaults + compiles.
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleBuildMotionMatchingNode(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath      = Params->GetStringField(TEXT("abp_path"));
	const FString DatabasePath = Params->GetStringField(TEXT("database_path"));
	FString ChooserPath;
	Params->TryGetStringField(TEXT("chooser_path"), ChooserPath);

	if (DatabasePath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: database_path"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AbpPath));

	UPoseSearchDatabase* Database = FMonolithAssetUtils::LoadAssetByPath<UPoseSearchDatabase>(DatabasePath);
	if (!Database) return FMonolithActionResult::Error(FString::Printf(TEXT("UPoseSearchDatabase not found: %s"), *DatabasePath));

	// --- Spawn the Pose History node via existing add_anim_graph_node internals (alias from 4.1) ---
	TSharedPtr<FJsonObject> HistParams = MakeShared<FJsonObject>();
	HistParams->SetStringField(TEXT("asset_path"), AbpPath);
	HistParams->SetStringField(TEXT("node_type"), TEXT("pose_history"));
	HistParams->SetNumberField(TEXT("position_x"), 0.0);
	HistParams->SetNumberField(TEXT("position_y"), 0.0);
	FMonolithActionResult HistResult = HandleAddAnimGraphNode(HistParams);
	if (!HistResult.bSuccess) return HistResult;
	const FString HistNodeName = HistResult.Result.IsValid() ? HistResult.Result->GetStringField(TEXT("node_name")) : FString();

	// --- Spawn the Motion Matching node ---
	TSharedPtr<FJsonObject> MMParams = MakeShared<FJsonObject>();
	MMParams->SetStringField(TEXT("asset_path"), AbpPath);
	MMParams->SetStringField(TEXT("node_type"), TEXT("MotionMatching"));
	MMParams->SetNumberField(TEXT("position_x"), -400.0);
	MMParams->SetNumberField(TEXT("position_y"), 0.0);
	FMonolithActionResult MMResult = HandleAddAnimGraphNode(MMParams);
	if (!MMResult.bSuccess) return MMResult;
	const FString MMNodeName = MMResult.Result.IsValid() ? MMResult.Result->GetStringField(TEXT("node_name")) : FString();

	// --- Wire MM pose-out -> History pose-in via existing connect internals ---
	// Topology (matches Epic GASP): the Motion Matching node is an asset player whose
	// 'Pose' output feeds the Pose History collector's 'Source' input pose link; the
	// History node's own 'Pose' output then flows downstream to the graph result.
	// So the History node WRAPS the MM node's output, collecting its pose over time.
	TSharedPtr<FJsonObject> ConnParams = MakeShared<FJsonObject>();
	ConnParams->SetStringField(TEXT("asset_path"), AbpPath);
	ConnParams->SetStringField(TEXT("source_node"), MMNodeName);
	ConnParams->SetStringField(TEXT("source_pin"), TEXT("Pose"));
	ConnParams->SetStringField(TEXT("target_node"), HistNodeName);
	ConnParams->SetStringField(TEXT("target_pin"), TEXT("Source"));
	ConnParams->SetBoolField(TEXT("compile"), false);
	FMonolithActionResult ConnResult = HandleConnectAnimGraphPins(ConnParams);
	const bool bWired = ConnResult.bSuccess;
	FString WireNote = bWired ? TEXT("connected") : (ConnResult.ErrorMessage.IsEmpty() ? TEXT("not connected") : ConnResult.ErrorMessage);

	// --- Assign the MM node's Database pointer directly (UObject pointer write) ---
	UAnimBlueprint* ABP2 = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	UEdGraphNode* MMNode = FindNodeByName(ABP2, MMNodeName, nullptr);
	UAnimGraphNode_Base* MMAnim = Cast<UAnimGraphNode_Base>(MMNode);
	if (!MMAnim) return FMonolithActionResult::Error(TEXT("Spawned MotionMatching node could not be re-resolved"));

	UScriptStruct* MMStruct = nullptr;
	void* MMAddr = nullptr;
	FString ResolveError;
	if (!ResolveInnerAnimNode(MMAnim, MMStruct, MMAddr, ResolveError))
		return FMonolithActionResult::Error(ResolveError);

	GEditor->BeginTransaction(FText::FromString(TEXT("Assign Motion Matching Database")));
	MMAnim->Modify();

	// Database is TObjectPtr<const UPoseSearchDatabase> — the FObjectProperty carries no
	// C++ const, so a direct reflection pointer set is the correct write (not AddAnimationAsset).
	FProperty* DbProp = MMStruct->FindPropertyByName(TEXT("Database"));
	FObjectPropertyBase* DbObjProp = CastField<FObjectPropertyBase>(DbProp);
	if (!DbObjProp)
	{ GEditor->EndTransaction(); return FMonolithActionResult::Error(TEXT("MM node has no FObjectProperty 'Database'")); }
	DbObjProp->SetObjectPropertyValue_InContainer(MMAddr, Database);

	GEditor->EndTransaction();

	// --- Chooser-driven DB selection (best-effort note; Database is always set as fallback) ---
	bool bChooserNoted = false;
	if (!ChooserPath.IsEmpty())
	{
		// Chooser-driven selection is wired at runtime via an Anim Node Function calling
		// SetDatabaseToSearch/SetDatabasesToSearch from a chooser result; that function
		// graph wiring is out of scope for this composite. Database is set above as the
		// always-valid fallback; record the chooser path for the caller to wire the function.
		bChooserNoted = true;
	}

	// --- Apply 4.2 / 4.3 sensible defaults ---
	{
		TSharedPtr<FJsonObject> HistCfg = MakeShared<FJsonObject>();
		HistCfg->SetStringField(TEXT("abp_path"), AbpPath);
		HistCfg->SetStringField(TEXT("node_id"), HistNodeName);
		HistCfg->SetBoolField(TEXT("generate_trajectory"), true);
		HandleConfigurePoseHistoryNode(HistCfg);

		TSharedPtr<FJsonObject> MMCfg = MakeShared<FJsonObject>();
		MMCfg->SetStringField(TEXT("abp_path"), AbpPath);
		MMCfg->SetStringField(TEXT("node_id"), MMNodeName);
		MMCfg->SetNumberField(TEXT("blend_time"), 0.2);
		MMCfg->SetNumberField(TEXT("max_active_blends"), 4);
		HandleConfigureMotionMatchingNode(MMCfg);
	}

	// --- Wire History pose-out -> Output Pose (UAnimGraphNode_Root 'Result' input) ---
	// Without this the graph has no final pose driving the output, so the AnimBP plays
	// nothing. Resolve the main AnimGraph, find its Root node, and connect the History
	// node's 'Pose' output to the Root's 'Result' input via the same connect internals.
	bool bOutputPoseWired = false;
	FString OutputWireNote;
	{
		FString RootGraphError;
		UEdGraph* RootGraph = ResolveTargetGraph(ABP2, TEXT("AnimGraph"), TEXT(""), RootGraphError);
		UAnimGraphNode_Root* RootNode = nullptr;
		if (RootGraph)
		{
			TArray<UAnimGraphNode_Root*> Roots;
			RootGraph->GetNodesOfClass<UAnimGraphNode_Root>(Roots);
			if (Roots.Num() > 0)
			{
				RootNode = Roots[0];
			}
		}

		if (!RootNode)
		{
			OutputWireNote = RootGraph
				? TEXT("Output Pose (UAnimGraphNode_Root) not found in AnimGraph")
				: RootGraphError;
		}
		else
		{
			TSharedPtr<FJsonObject> RootConn = MakeShared<FJsonObject>();
			RootConn->SetStringField(TEXT("asset_path"), AbpPath);
			RootConn->SetStringField(TEXT("source_node"), HistNodeName);
			RootConn->SetStringField(TEXT("source_pin"), TEXT("Pose"));
			RootConn->SetStringField(TEXT("target_node"), RootNode->GetName());
			RootConn->SetStringField(TEXT("target_pin"), TEXT("Result"));
			RootConn->SetBoolField(TEXT("compile"), false);
			FMonolithActionResult RootConnResult = HandleConnectAnimGraphPins(RootConn);
			bOutputPoseWired = RootConnResult.bSuccess;
			OutputWireNote = bOutputPoseWired
				? TEXT("connected")
				: (RootConnResult.ErrorMessage.IsEmpty() ? TEXT("not connected") : RootConnResult.ErrorMessage);
		}
	}

	MMAnim->ReconstructNode();
	ABP2->MarkPackageDirty();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP2);
	FKismetEditorUtilities::CompileBlueprint(ABP2);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("pose_history_node"), HistNodeName);
	Root->SetStringField(TEXT("motion_matching_node"), MMNodeName);
	Root->SetStringField(TEXT("database"), DatabasePath);
	Root->SetBoolField(TEXT("wired"), bWired);
	Root->SetStringField(TEXT("wire_note"), WireNote);
	Root->SetBoolField(TEXT("output_pose_wired"), bOutputPoseWired);
	Root->SetStringField(TEXT("output_pose_wire_note"), OutputWireNote);
	if (bChooserNoted) Root->SetStringField(TEXT("chooser_path"), ChooserPath);
	Root->SetBoolField(TEXT("compiled"), true);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: get_anim_graph_output_connection (READ-ONLY)
// Find the UAnimGraphNode_Root and report whether its 'Result' input pose pin is
// linked, and by which node/pin. Confirms the graph drives the final output pose.
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleGetAnimGraphOutputConnection(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath = Params->GetStringField(TEXT("abp_path"));
	FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	if (GraphName.IsEmpty()) GraphName = TEXT("AnimGraph");

	if (AbpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: abp_path"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AbpPath));

	FString GraphError;
	UEdGraph* Graph = ResolveTargetGraph(ABP, GraphName, TEXT(""), GraphError);
	if (!Graph) return FMonolithActionResult::Error(GraphError);

	TArray<UAnimGraphNode_Root*> Roots;
	Graph->GetNodesOfClass<UAnimGraphNode_Root>(Roots);
	if (Roots.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("No Output Pose (UAnimGraphNode_Root) found in graph '%s'"), *GraphName));
	}

	UAnimGraphNode_Root* RootNode = Roots[0];
	UEdGraphPin* ResultPin = RootNode->FindPin(FName(TEXT("Result")), EGPD_Input);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("graph_name"), GraphName);
	Root->SetStringField(TEXT("root_node"), RootNode->GetName());

	if (!ResultPin)
	{
		Root->SetBoolField(TEXT("output_connected"), false);
		Root->SetStringField(TEXT("note"), TEXT("Output Pose node has no 'Result' input pin"));
		return FMonolithActionResult::Success(Root);
	}

	const bool bConnected = ResultPin->LinkedTo.Num() > 0;
	Root->SetBoolField(TEXT("output_connected"), bConnected);
	if (bConnected)
	{
		UEdGraphPin* SrcPin = ResultPin->LinkedTo[0];
		UEdGraphNode* SrcNode = SrcPin ? SrcPin->GetOwningNodeUnchecked() : nullptr;
		Root->SetStringField(TEXT("source_node"), SrcNode ? SrcNode->GetName() : FString(TEXT("<unknown>")));
		Root->SetStringField(TEXT("source_pin"), SrcPin ? SrcPin->PinName.ToString() : FString(TEXT("<unknown>")));
	}
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// AnimGraph authoring (Group 1)
// ---------------------------------------------------------------------------

namespace
{

/**
 * Shared body for add_apply_additive / add_apply_mesh_space_additive — identical
 * apart from the fixed node class (bMeshSpace selects the mesh-space sibling).
 * Spawns the node via SpawnAndWirePoseInput, wires Base/Additive from the named
 * source nodes if supplied, and writes the inner Alpha if supplied.
 */
FMonolithActionResult ApplyAdditiveImpl(const TSharedPtr<FJsonObject>& Params, bool bMeshSpace)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString BaseNode;     Params->TryGetStringField(TEXT("base_node"), BaseNode);
	FString AdditiveNode; Params->TryGetStringField(TEXT("additive_node"), AdditiveNode);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	const FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	double TempVal;
	float PosX = 200.f, PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	UClass* NodeClass = bMeshSpace
		? UAnimGraphNode_ApplyMeshSpaceAdditive::StaticClass()
		: UAnimGraphNode_ApplyAdditive::StaticClass();

	// Spawn first (no auto-wire — Base/Additive are wired explicitly below).
	FString SpawnError;
	UAnimGraphNode_Base* NewNode = SpawnAndWirePoseInput(TargetGraph, NodeClass, PosX, PosY, nullptr, NAME_None, SpawnError);
	if (!NewNode) return FMonolithActionResult::Error(SpawnError);

	// Wire Base / Additive from the supplied source nodes (intra-graph).
	auto WireInput = [&](const FString& SrcName, const TCHAR* PinName, FString& OutErr) -> bool
	{
		if (SrcName.IsEmpty()) return true; // nothing to wire is fine — caller can connect later
		UEdGraphNode* Src = FindNodeByName(ABP, SrcName, TargetGraph);
		if (!Src)
		{
			OutErr = FString::Printf(TEXT("%s source node '%s' not found in target graph"), PinName, *SrcName);
			return false;
		}
		UEdGraphPin* OutPin = FindPoseOutputPin(Src, FString());
		if (!OutPin)
		{
			OutErr = FString::Printf(TEXT("Source node '%s' has no pose output. Available outputs: [%s]"),
				*SrcName, *ListOutputPins(Src));
			return false;
		}
		UEdGraphPin* InPin = NewNode->FindPin(FName(PinName), EGPD_Input);
		if (!InPin)
		{
			OutErr = FString::Printf(TEXT("Pin '%s' not found on ApplyAdditive node"), PinName);
			return false;
		}
		const UEdGraphSchema* Schema = TargetGraph->GetSchema();
		GEditor->BeginTransaction(FText::FromString(TEXT("Wire Additive Input")));
		TargetGraph->Modify();
		const bool bOk = Schema->TryCreateConnection(OutPin, InPin);
		GEditor->EndTransaction();
		if (!bOk)
		{
			OutErr = FString::Printf(TEXT("TryCreateConnection failed: '%s.%s' -> additive.%s"),
				*SrcName, *OutPin->PinName.ToString(), PinName);
			return false;
		}
		return true;
	};

	FString WireError;
	if (!WireInput(BaseNode, TEXT("Base"), WireError))         return FMonolithActionResult::Error(WireError);
	if (!WireInput(AdditiveNode, TEXT("Additive"), WireError)) return FMonolithActionResult::Error(WireError);

	// Optional Alpha write on the inner FAnimNode_ApplyAdditive (shared field name on both variants).
	// Capture the resolve/import results — if the caller supplied alpha and the write failed, we must
	// surface it as a warning rather than silently reporting success with the default Alpha.
	bool bAlphaSupplied = false;
	bool bAlphaWriteFailed = false;
	FString AlphaWarning;
	if (Params->HasField(TEXT("alpha")))
	{
		bAlphaSupplied = true;
		const float Alpha = static_cast<float>(Params->GetNumberField(TEXT("alpha")));
		UScriptStruct* NodeStruct = nullptr; void* NodeAddr = nullptr; FString ResolveErr;
		if (ResolveInnerAnimNode(NewNode, NodeStruct, NodeAddr, ResolveErr))
		{
			FString AlphaErr;
			if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("Alpha"), FString::SanitizeFloat(Alpha), NewNode, AlphaErr))
			{
				bAlphaWriteFailed = true;
				AlphaWarning = FString::Printf(TEXT("Alpha was supplied but could not be written: %s. The node uses the default Alpha."), *AlphaErr);
			}
		}
		else
		{
			bAlphaWriteFailed = true;
			AlphaWarning = FString::Printf(TEXT("Alpha was supplied but the inner FAnimNode could not be resolved: %s. The node uses the default Alpha."), *ResolveErr);
		}
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_name"), NewNode->GetName());
	Root->SetStringField(TEXT("node_class"), NewNode->GetClass()->GetName());
	Root->SetBoolField(TEXT("mesh_space"), bMeshSpace);
	Root->SetBoolField(TEXT("base_wired"), !BaseNode.IsEmpty());
	Root->SetBoolField(TEXT("additive_wired"), !AdditiveNode.IsEmpty());
	if (bAlphaSupplied)
	{
		Root->SetBoolField(TEXT("alpha_write_failed"), bAlphaWriteFailed);
		if (bAlphaWriteFailed) Root->SetStringField(TEXT("warning"), AlphaWarning);
	}
	Root->SetArrayField(TEXT("pins"), BuildPinList(NewNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

} // anonymous namespace

// ---------------------------------------------------------------------------
// Action: add_apply_additive / add_apply_mesh_space_additive
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddApplyAdditive(const TSharedPtr<FJsonObject>& Params)
{
	return ApplyAdditiveImpl(Params, /*bMeshSpace=*/false);
}

FMonolithActionResult FMonolithAbpWriteActions::HandleAddApplyMeshSpaceAdditive(const TSharedPtr<FJsonObject>& Params)
{
	return ApplyAdditiveImpl(Params, /*bMeshSpace=*/true);
}

// ---------------------------------------------------------------------------
// Action: add_slot_node
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddSlotNode(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString SlotName;   Params->TryGetStringField(TEXT("slot_name"), SlotName);
	FString SourceNode; Params->TryGetStringField(TEXT("source_node"), SourceNode);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	const FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	bool bValidateSlot = true;
	if (Params->HasField(TEXT("validate_slot"))) bValidateSlot = Params->GetBoolField(TEXT("validate_slot"));

	double TempVal;
	float PosX = 200.f, PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	if (SlotName.IsEmpty())
	{
		// A slot node with no name silently passes the source pose through — refuse.
		return FMonolithActionResult::Error(TEXT("Missing required parameter: slot_name (an unnamed slot node is a no-op pass-through)"));
	}

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	// Non-fatal slot-name validation: montage slots are often registered after graph authoring,
	// so an unknown slot is a warning, not an error.
	bool bSlotFound = false;
	FString SlotWarning;
	if (bValidateSlot)
	{
		USkeleton* Skeleton = ABP->TargetSkeleton;
		if (Skeleton)
		{
			bSlotFound = Skeleton->ContainsSlotName(FName(*SlotName));
			if (!bSlotFound)
			{
				TArray<FString> ValidSlots;
				for (const FAnimSlotGroup& Group : Skeleton->GetSlotGroups())
				{
					for (const FName& Slot : Group.SlotNames)
					{
						ValidSlots.Add(Slot.ToString());
					}
				}
				SlotWarning = FString::Printf(
					TEXT("Slot '%s' is not registered on skeleton '%s'. Known slots: [%s]. The node was still created (montage slots are often registered after graph authoring)."),
					*SlotName, *Skeleton->GetName(), *FString::Join(ValidSlots, TEXT(", ")));
			}
		}
		else
		{
			SlotWarning = TEXT("ABP has no TargetSkeleton — slot name not validated.");
		}
	}

	// Spawn via shared helper, wiring the optional Source pose input.
	UEdGraphNode* Src = nullptr;
	if (!SourceNode.IsEmpty())
	{
		Src = FindNodeByName(ABP, SourceNode, TargetGraph);
		if (!Src) return FMonolithActionResult::Error(FString::Printf(TEXT("Source node '%s' not found in target graph"), *SourceNode));
	}

	FString SpawnError;
	UAnimGraphNode_Base* NewNode = SpawnAndWirePoseInput(
		TargetGraph, UAnimGraphNode_Slot::StaticClass(), PosX, PosY,
		Src, Src ? FName(TEXT("Source")) : NAME_None, SpawnError);
	if (!NewNode) return FMonolithActionResult::Error(SpawnError);

	// Write SlotName onto the inner FAnimNode_Slot via the same reflection path
	// set_anim_graph_node_property uses (persisted through compile).
	{
		UScriptStruct* NodeStruct = nullptr; void* NodeAddr = nullptr; FString ResolveErr;
		if (!ResolveInnerAnimNode(NewNode, NodeStruct, NodeAddr, ResolveErr))
		{
			return FMonolithActionResult::Error(ResolveErr);
		}
		FString WriteErr;
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("SlotName"), SlotName, NewNode, WriteErr))
		{
			return FMonolithActionResult::Error(WriteErr);
		}
		NewNode->ReconstructNode();
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_name"), NewNode->GetName());
	Root->SetStringField(TEXT("slot_name"), SlotName);
	Root->SetBoolField(TEXT("slot_validated"), bValidateSlot);
	Root->SetBoolField(TEXT("slot_found"), bSlotFound);
	if (!SlotWarning.IsEmpty()) Root->SetStringField(TEXT("warning"), SlotWarning);
	Root->SetBoolField(TEXT("source_wired"), Src != nullptr);
	Root->SetArrayField(TEXT("pins"), BuildPinList(NewNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: add_save_cached_pose
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddSaveCachedPose(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString CacheName;  Params->TryGetStringField(TEXT("cache_name"), CacheName);
	FString SourceNode; Params->TryGetStringField(TEXT("source_node"), SourceNode);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	const FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	double TempVal;
	float PosX = 200.f, PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	if (CacheName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: cache_name"));

	// Save nodes are sink nodes restricted to the main AnimGraph — reject a state target up front,
	// but the engine's IsCompatibleWithGraph below is authoritative.
	if (!StateName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Save Cached Pose nodes live only in the main AnimGraph, not inside a state's inner graph (they are sink nodes). Omit state_name."));
	}

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, TEXT(""), GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	// The Save node sinks the cached pose — wire the source into the 'Pose' input via the helper.
	UEdGraphNode* Src = nullptr;
	if (!SourceNode.IsEmpty())
	{
		Src = FindNodeByName(ABP, SourceNode, TargetGraph);
		if (!Src) return FMonolithActionResult::Error(FString::Printf(TEXT("Source node '%s' not found in target graph"), *SourceNode));
	}

	FString SpawnError;
	UAnimGraphNode_Base* NewNode = SpawnAndWirePoseInput(
		TargetGraph, UAnimGraphNode_SaveCachedPose::StaticClass(), PosX, PosY,
		Src, Src ? FName(TEXT("Pose")) : NAME_None, SpawnError);
	if (!NewNode) return FMonolithActionResult::Error(SpawnError);

	UAnimGraphNode_SaveCachedPose* SaveNode = Cast<UAnimGraphNode_SaveCachedPose>(NewNode);
	if (!SaveNode) return FMonolithActionResult::Error(TEXT("Spawned node is not a SaveCachedPose node"));

	// Surface the engine's own placement rejection rather than relying solely on our pre-check.
	if (!SaveNode->IsCompatibleWithGraph(TargetGraph))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Save Cached Pose node is not compatible with graph '%s' (engine IsCompatibleWithGraph rejected it). Save nodes must live in the main AnimGraph."),
			*TargetGraph->GetName()));
	}

	// CacheName is a public EditAnywhere UPROPERTY — set it directly, then OnRenameNode so the
	// node title + name validator stay consistent.
	SaveNode->CacheName = CacheName;
	SaveNode->OnRenameNode(CacheName);

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_name"), NewNode->GetName());
	Root->SetStringField(TEXT("cache_name"), CacheName);
	Root->SetBoolField(TEXT("source_wired"), Src != nullptr);
	Root->SetArrayField(TEXT("pins"), BuildPinList(NewNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: add_use_cached_pose
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddUseCachedPose(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString CacheName; Params->TryGetStringField(TEXT("cache_name"), CacheName);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");

	bool bValidatePair = true;
	if (Params->HasField(TEXT("validate_pair"))) bValidatePair = Params->GetBoolField(TEXT("validate_pair"));

	double TempVal;
	float PosX = 200.f, PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	if (CacheName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: cache_name"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, TEXT(""), GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	// Validate that a Save node with this CacheName exists in the graph — the classic failure mode
	// (mismatched names -> silent wrong compile) is exactly what this guards against.
	if (bValidatePair)
	{
		TArray<UAnimGraphNode_SaveCachedPose*> SaveNodes;
		TargetGraph->GetNodesOfClass<UAnimGraphNode_SaveCachedPose>(SaveNodes);
		bool bMatch = false;
		TArray<FString> Existing;
		for (UAnimGraphNode_SaveCachedPose* SaveNode : SaveNodes)
		{
			if (SaveNode)
			{
				Existing.Add(SaveNode->CacheName);
				if (SaveNode->CacheName == CacheName) bMatch = true;
			}
		}
		if (!bMatch)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("No Save Cached Pose node named '%s' exists in graph '%s'. Existing cache names: [%s]. Add the Save node first, or pass validate_pair=false."),
				*CacheName, *GraphName, *FString::Join(Existing, TEXT(", "))));
		}
	}

	FString SpawnError;
	UAnimGraphNode_Base* NewNode = SpawnAndWirePoseInput(
		TargetGraph, UAnimGraphNode_UseCachedPose::StaticClass(), PosX, PosY,
		nullptr, NAME_None, SpawnError);
	if (!NewNode) return FMonolithActionResult::Error(SpawnError);

	// NameOfCache is a private FString UPROPERTY on the editor node (NOT the inner FAnimNode) —
	// reflection-write it via FStrProperty, then ReconstructNode. The weak SaveCachedPoseNode
	// pointer re-resolves by name at compile.
	{
		FProperty* Prop = NewNode->GetClass()->FindPropertyByName(TEXT("NameOfCache"));
		FStrProperty* StrProp = CastField<FStrProperty>(Prop);
		if (!StrProp)
		{
			return FMonolithActionResult::Error(TEXT("Could not resolve 'NameOfCache' FStrProperty on UseCachedPose node"));
		}
		void* ValuePtr = StrProp->ContainerPtrToValuePtr<void>(NewNode);
		StrProp->SetPropertyValue(ValuePtr, CacheName);
		NewNode->ReconstructNode();
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_name"), NewNode->GetName());
	Root->SetStringField(TEXT("cache_name"), CacheName);
	Root->SetBoolField(TEXT("pair_validated"), bValidatePair);
	Root->SetArrayField(TEXT("pins"), BuildPinList(NewNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: set_output_pose_source
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleSetOutputPoseSource(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString SourceNode; Params->TryGetStringField(TEXT("source_node"), SourceNode);
	FString SourcePin;  Params->TryGetStringField(TEXT("source_pin"), SourcePin);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");

	bool bBreakExisting = true;
	if (Params->HasField(TEXT("break_existing"))) bBreakExisting = Params->GetBoolField(TEXT("break_existing"));

	if (SourceNode.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: source_node"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, TEXT(""), GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	// Locate the Output Pose (Root) node — same lookup the read-only reader uses.
	TArray<UAnimGraphNode_Root*> Roots;
	TargetGraph->GetNodesOfClass<UAnimGraphNode_Root>(Roots);
	if (Roots.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("No Output Pose (UAnimGraphNode_Root) found in graph '%s' (corrupt graph)"), *GraphName));
	}
	UAnimGraphNode_Root* RootNode = Roots[0];
	UEdGraphPin* ResultPin = RootNode->FindPin(FName(TEXT("Result")), EGPD_Input);
	if (!ResultPin)
	{
		return FMonolithActionResult::Error(TEXT("Output Pose node has no 'Result' input pin (corrupt graph)"));
	}

	UEdGraphNode* Src = FindNodeByName(ABP, SourceNode, TargetGraph);
	if (!Src) return FMonolithActionResult::Error(FString::Printf(TEXT("Source node '%s' not found in graph '%s'"), *SourceNode, *GraphName));

	if (Src->GetGraph() != RootNode->GetGraph())
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Source node '%s' is not in graph '%s' — the Output Pose connection must be intra-graph"), *SourceNode, *GraphName));
	}

	UEdGraphPin* OutPin = FindPoseOutputPin(Src, SourcePin);
	if (!OutPin)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Source node '%s' has no pose output pin (looked for '%s'). Available outputs: [%s]"),
			*SourceNode, SourcePin.IsEmpty() ? TEXT("<first pose-out>") : *SourcePin, *ListOutputPins(Src)));
	}

	// No-op if already driven by the same source pin.
	for (UEdGraphPin* Linked : ResultPin->LinkedTo)
	{
		if (Linked == OutPin)
		{
			TSharedPtr<FJsonObject> NoOp = MakeShared<FJsonObject>();
			NoOp->SetStringField(TEXT("asset_path"), AssetPath);
			NoOp->SetStringField(TEXT("graph_name"), GraphName);
			NoOp->SetStringField(TEXT("root_node"), RootNode->GetName());
			NoOp->SetStringField(TEXT("source_node"), SourceNode);
			NoOp->SetStringField(TEXT("source_pin"), OutPin->PinName.ToString());
			NoOp->SetBoolField(TEXT("unchanged"), true);
			NoOp->SetBoolField(TEXT("saved"), false);
			return FMonolithActionResult::Success(NoOp);
		}
	}

	GEditor->BeginTransaction(FText::FromString(TEXT("Set Output Pose Source")));
	TargetGraph->Modify();
	if (bBreakExisting)
	{
		ResultPin->BreakAllPinLinks();
	}
	const UEdGraphSchema* Schema = TargetGraph->GetSchema();
	const bool bConnected = Schema->TryCreateConnection(OutPin, ResultPin);
	GEditor->EndTransaction();

	if (!bConnected)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("TryCreateConnection failed: '%s.%s' -> OutputPose.Result. Pin types may be incompatible."),
			*SourceNode, *OutPin->PinName.ToString()));
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("graph_name"), GraphName);
	Root->SetStringField(TEXT("root_node"), RootNode->GetName());
	Root->SetStringField(TEXT("source_node"), SourceNode);
	Root->SetStringField(TEXT("source_pin"), OutPin->PinName.ToString());
	Root->SetBoolField(TEXT("unchanged"), false);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: set_state_result_source (Group 2)
//
// Per-state analogue of set_output_pose_source: wire a node already inside a
// state's inner graph into the state's result sink pin
// (UAnimStateNode::GetPoseSinkPinInsideState — ANIMGRAPH_API).
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleSetStateResultSource(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString MachineName; Params->TryGetStringField(TEXT("machine_name"), MachineName);
	FString StateName;   Params->TryGetStringField(TEXT("state_name"), StateName);
	FString SourceNode;  Params->TryGetStringField(TEXT("source_node"), SourceNode);
	FString SourcePin;   Params->TryGetStringField(TEXT("source_pin"), SourcePin);

	bool bBreakExisting = true;
	if (Params->HasField(TEXT("break_existing"))) bBreakExisting = Params->GetBoolField(TEXT("break_existing"));

	if (MachineName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: machine_name"));
	if (StateName.IsEmpty())   return FMonolithActionResult::Error(TEXT("Missing required parameter: state_name"));
	if (SourceNode.IsEmpty())  return FMonolithActionResult::Error(TEXT("Missing required parameter: source_node"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	UAnimationStateMachineGraph* SMGraph = FindSMGraphByName(ABP, MachineName);
	if (!SMGraph) return FMonolithActionResult::Error(FString::Printf(TEXT("State machine '%s' not found"), *MachineName));

	UAnimStateNode* StateNode = FindStateByName(SMGraph, StateName);
	if (!StateNode) return FMonolithActionResult::Error(FString::Printf(TEXT("State '%s' not found in state machine '%s'"), *StateName, *MachineName));

	UEdGraph* StateGraph = StateNode->GetBoundGraph();
	if (!StateGraph) return FMonolithActionResult::Error(FString::Printf(TEXT("State '%s' has no inner animation graph"), *StateName));

	// The state's result sink pin — the pose pin of the sink node inside the state graph.
	UEdGraphPin* SinkPin = StateNode->GetPoseSinkPinInsideState();
	if (!SinkPin)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("State '%s' has no result sink pin (GetPoseSinkPinInsideState returned null — corrupt state graph)"), *StateName));
	}

	// Source node must live inside this state's inner graph (connections are intra-graph).
	UEdGraphNode* Src = FindNodeByName(ABP, SourceNode, StateGraph);
	if (!Src)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Source node '%s' not found inside state '%s' — the source must be a node inside this state's inner graph"),
			*SourceNode, *StateName));
	}

	UEdGraphPin* OutPin = FindPoseOutputPin(Src, SourcePin);
	if (!OutPin)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Source node '%s' has no pose output pin (looked for '%s'). Available outputs: [%s]"),
			*SourceNode, SourcePin.IsEmpty() ? TEXT("<first pose-out>") : *SourcePin, *ListOutputPins(Src)));
	}

	// No-op if already driven by the same source pin.
	for (UEdGraphPin* Linked : SinkPin->LinkedTo)
	{
		if (Linked == OutPin)
		{
			TSharedPtr<FJsonObject> NoOp = MakeShared<FJsonObject>();
			NoOp->SetStringField(TEXT("asset_path"), AssetPath);
			NoOp->SetStringField(TEXT("machine_name"), MachineName);
			NoOp->SetStringField(TEXT("state_name"), StateName);
			NoOp->SetStringField(TEXT("source_node"), SourceNode);
			NoOp->SetStringField(TEXT("source_pin"), OutPin->PinName.ToString());
			NoOp->SetBoolField(TEXT("unchanged"), true);
			NoOp->SetBoolField(TEXT("saved"), false);
			return FMonolithActionResult::Success(NoOp);
		}
	}

	GEditor->BeginTransaction(FText::FromString(TEXT("Set State Result Source")));
	StateGraph->Modify();
	if (bBreakExisting)
	{
		SinkPin->BreakAllPinLinks();
	}
	const UEdGraphSchema* Schema = StateGraph->GetSchema();
	const bool bConnected = Schema->TryCreateConnection(OutPin, SinkPin);
	GEditor->EndTransaction();

	if (!bConnected)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("TryCreateConnection failed: '%s.%s' -> state result sink. Pin types may be incompatible."),
			*SourceNode, *OutPin->PinName.ToString()));
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("machine_name"), MachineName);
	Root->SetStringField(TEXT("state_name"), StateName);
	Root->SetStringField(TEXT("source_node"), SourceNode);
	Root->SetStringField(TEXT("source_pin"), OutPin->PinName.ToString());
	Root->SetBoolField(TEXT("unchanged"), false);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: add_blend_by_int (Group 2)
//
// Spawn UAnimGraphNode_BlendListByInt (ships with 2 BlendPose pins — one from the
// ctor, one from PostPlacedNewNode) and grow to num_poses via the ANIMGRAPH_API
// AddPinToBlendList(), which appends a BlendPose_k + BlendTime_k pin per call.
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddBlendByInt(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	const FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	double NumVal = 0.0;
	if (!Params->TryGetNumberField(TEXT("num_poses"), NumVal))
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: num_poses"));
	}
	const int32 NumPoses = static_cast<int32>(NumVal);
	if (NumPoses < 2)  return FMonolithActionResult::Error(TEXT("num_poses must be >= 2 (a blend list needs at least two poses)"));
	if (NumPoses > 32) return FMonolithActionResult::Error(TEXT("num_poses is capped at 32"));

	double TempVal;
	float PosX = 200.f, PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	FString SpawnError;
	UAnimGraphNode_Base* NewNode = SpawnAndWirePoseInput(
		TargetGraph, UAnimGraphNode_BlendListByInt::StaticClass(), PosX, PosY,
		nullptr, NAME_None, SpawnError);
	if (!NewNode) return FMonolithActionResult::Error(SpawnError);

	UAnimGraphNode_BlendListByInt* BlendNode = Cast<UAnimGraphNode_BlendListByInt>(NewNode);
	if (!BlendNode) return FMonolithActionResult::Error(TEXT("Spawned node is not a BlendListByInt node"));

	// The node ships with 2 BlendPose pins (ctor AddPose + PostPlacedNewNode AddPose). Grow the
	// delta to reach num_poses; AddPinToBlendList ReconstructNode()s internally each call.
	const int32 StartingPoses = 2;
	for (int32 i = StartingPoses; i < NumPoses; ++i)
	{
		BlendNode->AddPinToBlendList();
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);

	// BlendTime is a FoldProperty pin (meta=(PinShownByDefault, FoldProperty) on
	// FAnimNode_BlendListBase::BlendTime). Each AddPinToBlendList() grows BlendTime via
	// Node.AddPose() (value 0.1f) and reconstructs, but the per-pose BlendTime fold pins do not
	// reconcile against the blueprint's fold state until CompileBlueprint() recomputes it. During
	// the intermediate grows an unmatched BlendTime_k pin carries a non-default value (0.1 != the
	// autogenerated 0.0), so RewireOldPinsToNewPins retains it as an orphan (UK2Node.cpp ~L1439),
	// producing the "orphan BlendTime_1 pin" compile warning.
	//
	// The orphan is a distinct RETAINED pin object that RewireOldPinsToNewPins re-creates from the
	// old-pins snapshot on every reconstruct, so resetting its value is futile — the next
	// reconstruct re-orphans it. The orphan has no links (bNotConnectable, no LinkedTo), so remove
	// the orphan pins directly: removal is the only op that survives reconstruct. UEdGraphNode::
	// RemovePin (ENGINE_API public, EdGraphNode.h:623; impl EdGraphNode.cpp:464) drops the pin from
	// BlendNode->Pins and marks it garbage with NO reconstruct. Collect orphans into a local array
	// FIRST, then remove, so BlendNode->Pins is never mutated mid-iteration. Then mark structurally
	// modified + compile to settle, clearing the orphan-pin warning.
	TArray<UEdGraphPin*> OrphanPins;
	for (UEdGraphPin* Pin : BlendNode->Pins)
	{
		if (Pin && Pin->bOrphanedPin)
		{
			OrphanPins.Add(Pin);
		}
	}
	for (UEdGraphPin* Pin : OrphanPins)
	{
		BlendNode->RemovePin(Pin);
	}
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);

	ABP->MarkPackageDirty();

	// Count the realized BlendPose_* input pins so the caller can verify + wire them.
	int32 PoseInputPins = 0;
	for (UEdGraphPin* Pin : BlendNode->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Input && Pin->PinName.ToString().StartsWith(TEXT("BlendPose")))
		{
			++PoseInputPins;
		}
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_name"), NewNode->GetName());
	Root->SetNumberField(TEXT("requested_poses"), NumPoses);
	Root->SetNumberField(TEXT("blend_pose_pins"), PoseInputPins);
	Root->SetArrayField(TEXT("pins"), BuildPinList(NewNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: add_blend_by_enum (Group 2)
//
// Place a UAnimGraphNode_BlendListByEnum bound to a UEnum, exposing one pose pin per
// chosen enumerator (plus the always-present index-0 "Default" pin). The editor node's
// own pin-grow primitives are out of reach across the module boundary:
//   - ExposeEnumElementAsPin(FName) is protected (AnimGraphNode_BlendListByEnum.h:60-61),
//   - there is NO AddPinToBlendList on the enum node or the base (that exists only on the
//     Int node), and the class is UCLASS(MinimalAPI).
// So ExposeEnumElementAsPin is replicated externally (it does exactly: VisibleEnumEntries.Add +
// Node.AddPose() + ReconstructNode(), AnimGraphNode_BlendListByEnum.cpp:143-158):
//   - BoundEnum (protected UPROPERTY TObjectPtr<UEnum>, h:25-26) is reflection-set via
//     FObjectPropertyBase::SetObjectPropertyValue_InContainer (same idiom as :2186-2190).
//   - VisibleEnumEntries (protected UPROPERTY TArray<FName>, h:28-29) has an FNameProperty inner
//     DIRECTLY (a scalar array, NOT a struct array), so each enumerator name is appended via
//     FScriptArrayHelper + FNameProperty::SetPropertyValue on the raw slot.
//   - the inner FAnimNode_BlendListByEnum Node (public UPROPERTY, h:20-21) exposes the public
//     header-inline FAnimNode_BlendListBase::AddPose() (#if WITH_EDITOR, AnimNode_BlendListBase.h:
//     115-119) — inline, so no exported symbol is named.
// The enum names stored in VisibleEnumEntries use UEnum::GetNameByIndex(i) (the stored Names key),
// which BakeDataDuringCompilation round-trips through BoundEnum->GetIndexByName() (…ByEnum.cpp:
// 317-348) to build EnumToPoseIndex automatically — no manual EnumToPoseIndex write. Unexposed enum
// values fall through to the Default pose (index 0).
//
// The node ships with exactly ONE pose pin (its ctor calls Node.AddPose() once → the index-0
// Default pin). UNLIKE blend-by-int (StartingPoses=2), we do NOT pre-count starting poses; each
// exposed enumerator adds one AddPose() on top of the ctor's Default. After the loop a single
// ReconstructNode() materializes the BlendPose_k pins; then the SAME orphan-BlendTime strip +
// recompile tail that add_blend_by_int ships settles the FoldProperty orphan pins.
// ---------------------------------------------------------------------------

namespace
{

// Local duplicate of MonolithReflectionWalker.cpp's IsAutoMaxSentinel (lives in an anonymous
// namespace in MonolithCore; duplicated here to avoid a cross-module surface change for one
// 6-line predicate). Skip a given enum index ONLY if it is genuinely the auto-generated _MAX
// sentinel: the enum reports an existing max (UEnum::ContainsExistingMax()) AND the name ends in
// "_MAX". The naive "NumEnums()-1" drops the last REAL enumerator on enums with no sentinel
// (typical of UserDefinedEnums); the conditional form never does.
bool IsAutoMaxSentinelEntry(const UEnum* Enum, int32 Index)
{
	if (!Enum)
	{
		return false;
	}
	if (!Enum->ContainsExistingMax())
	{
		return false;
	}
	return Enum->GetNameStringByIndex(Index).EndsWith(TEXT("_MAX"), ESearchCase::CaseSensitive);
}

} // namespace

FMonolithActionResult FMonolithAbpWriteActions::HandleAddBlendByEnum(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	const FString EnumPath  = Params->HasField(TEXT("enum_path")) ? Params->GetStringField(TEXT("enum_path")) : TEXT("");
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	const FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	if (EnumPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: enum_path"));
	}

	double TempVal;
	float PosX = 200.f, PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	// --- Resolve the UEnum (try a full object load first, then a global object lookup by name). ---
	UEnum* Enum = LoadObject<UEnum>(nullptr, *EnumPath);
	if (!Enum)
	{
		Enum = FindFirstObject<UEnum>(*EnumPath, EFindFirstObjectOptions::NativeFirst);
	}
	if (!Enum)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not resolve enum_path '%s' to a UEnum. Pass a full object path (e.g. /Game/Enums/E_X.E_X) or a C++ enum name (e.g. EAnimGroupRole)."),
			*EnumPath));
	}

	// --- Build the default exposable-enumerator list (non-Hidden, non-_MAX), index-ordered. ---
	TArray<FName>   AvailableNames;     // stored Names key form (what BakeDataDuringCompilation expects)
	TArray<FString> AvailableShortStr;  // short, lower-cost match form for the caller's filter
	const int32 NumEntries = Enum->NumEnums();
	for (int32 i = 0; i < NumEntries; ++i)
	{
		if (IsAutoMaxSentinelEntry(Enum, i))
		{
			continue;
		}
#if WITH_METADATA
		if (Enum->HasMetaData(TEXT("Hidden"), i))
		{
			continue;
		}
#endif
		AvailableNames.Add(Enum->GetNameByIndex(i));
		AvailableShortStr.Add(Enum->GetNameStringByIndex(i));
	}

	if (AvailableNames.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Enum '%s' has no exposable enumerators (all entries are Hidden or the _MAX sentinel)."), *Enum->GetName()));
	}

	// --- Resolve the chosen enumerators (optional explicit subset; default = all available). ---
	// Match a requested name against either the full stored key (E::Walk) or the short name (Walk),
	// case-insensitively, mirroring UEnum::GetIndexByName's lenient resolution. De-dupe, preserving
	// the requested order; error on any unknown name with the valid list.
	TArray<FName> ChosenNames;
	if (Params->HasField(TEXT("enumerators")))
	{
		const TArray<TSharedPtr<FJsonValue>>* RawList = nullptr;
		if (!Params->TryGetArrayField(TEXT("enumerators"), RawList) || !RawList)
		{
			return FMonolithActionResult::Error(TEXT("Parameter 'enumerators' must be an array of enumerator name strings"));
		}

		for (const TSharedPtr<FJsonValue>& Val : *RawList)
		{
			FString Requested;
			if (!Val.IsValid() || !Val->TryGetString(Requested) || Requested.IsEmpty())
			{
				continue;
			}

			int32 MatchIdx = INDEX_NONE;
			for (int32 k = 0; k < AvailableNames.Num(); ++k)
			{
				if (AvailableNames[k].ToString().Equals(Requested, ESearchCase::IgnoreCase) ||
				    AvailableShortStr[k].Equals(Requested, ESearchCase::IgnoreCase))
				{
					MatchIdx = k;
					break;
				}
			}

			if (MatchIdx == INDEX_NONE)
			{
				return FMonolithActionResult::Error(FString::Printf(
					TEXT("Enumerator '%s' is not a valid exposable entry of enum '%s'. Valid: [%s]"),
					*Requested, *Enum->GetName(), *FString::Join(AvailableShortStr, TEXT(", "))));
			}

			ChosenNames.AddUnique(AvailableNames[MatchIdx]);
		}

		if (ChosenNames.Num() == 0)
		{
			return FMonolithActionResult::Error(TEXT("Parameter 'enumerators' resolved to no usable enumerator names"));
		}
	}
	else
	{
		ChosenNames = AvailableNames;
	}

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	FString SpawnError;
	UAnimGraphNode_Base* NewNode = SpawnAndWirePoseInput(
		TargetGraph, UAnimGraphNode_BlendListByEnum::StaticClass(), PosX, PosY,
		nullptr, NAME_None, SpawnError);
	if (!NewNode) return FMonolithActionResult::Error(SpawnError);

	UAnimGraphNode_BlendListByEnum* EnumNode = Cast<UAnimGraphNode_BlendListByEnum>(NewNode);
	if (!EnumNode) return FMonolithActionResult::Error(TEXT("Spawned node is not a BlendListByEnum node"));

	// --- Reflection-set the protected BoundEnum (TObjectPtr<UEnum>) on the editor node. ---
	FProperty* BoundEnumProp = EnumNode->GetClass()->FindPropertyByName(TEXT("BoundEnum"));
	FObjectPropertyBase* BoundEnumObjProp = CastField<FObjectPropertyBase>(BoundEnumProp);
	if (!BoundEnumObjProp)
	{
		return FMonolithActionResult::Error(TEXT("BlendListByEnum node has no FObjectProperty 'BoundEnum' (engine layout changed?)"));
	}

	// --- Resolve the protected VisibleEnumEntries (TArray<FName>) reflection handles. ---
	FArrayProperty* VisibleProp = CastField<FArrayProperty>(EnumNode->GetClass()->FindPropertyByName(TEXT("VisibleEnumEntries")));
	if (!VisibleProp)
	{
		return FMonolithActionResult::Error(TEXT("BlendListByEnum node has no array property 'VisibleEnumEntries' (engine layout changed?)"));
	}
	FNameProperty* VisibleInnerName = CastField<FNameProperty>(VisibleProp->Inner);
	if (!VisibleInnerName)
	{
		return FMonolithActionResult::Error(TEXT("'VisibleEnumEntries' inner is not an FNameProperty (engine layout changed?)"));
	}

	GEditor->BeginTransaction(FText::FromString(TEXT("Add Blend By Enum")));
	EnumNode->Modify();

	BoundEnumObjProp->SetObjectPropertyValue_InContainer(EnumNode, Enum);

	// Append each chosen enumerator name to VisibleEnumEntries (scalar FName array — the raw slot
	// IS the FName, no struct-inner step) and grow the inner pose array by one Default per entry.
	void* VisibleArrayPtr = VisibleProp->ContainerPtrToValuePtr<void>(EnumNode);
	FScriptArrayHelper VisibleHelper(VisibleProp, VisibleArrayPtr);
	for (const FName& EnumeratorName : ChosenNames)
	{
		const int32 Idx = VisibleHelper.AddValue();
		VisibleInnerName->SetPropertyValue(VisibleHelper.GetRawPtr(Idx), EnumeratorName);

		// Public header-inline AddPose() (FAnimNode_BlendListBase) — grows BlendPose + BlendTime.
		EnumNode->Node.AddPose();
	}

	EnumNode->ReconstructNode();

	GEditor->EndTransaction();

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);

	// Orphan-pin strip — identical to add_blend_by_int. Each Node.AddPose() grows the FoldProperty
	// BlendTime array (value 0.1f); during the intermediate grows an unmatched BlendTime_k pin is
	// retained as an orphan by RewireOldPinsToNewPins until CompileBlueprint reconciles the fold
	// state. The orphans have no links — remove them directly (collect first, then remove, so Pins
	// is not mutated mid-iteration), then recompile to clear the orphan-pin warning.
	TArray<UEdGraphPin*> OrphanPins;
	for (UEdGraphPin* Pin : EnumNode->Pins)
	{
		if (Pin && Pin->bOrphanedPin)
		{
			OrphanPins.Add(Pin);
		}
	}
	for (UEdGraphPin* Pin : OrphanPins)
	{
		EnumNode->RemovePin(Pin);
	}
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);

	ABP->MarkPackageDirty();

	// Count the realized BlendPose_* input pins (1 Default + N exposed enumerators).
	int32 PoseInputPins = 0;
	for (UEdGraphPin* Pin : EnumNode->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Input && Pin->PinName.ToString().StartsWith(TEXT("BlendPose")))
		{
			++PoseInputPins;
		}
	}

	// Echo the enumerator names actually exposed (short form) for caller readback / wiring.
	TArray<TSharedPtr<FJsonValue>> ExposedJson;
	for (const FName& Name : ChosenNames)
	{
		ExposedJson.Add(MakeShared<FJsonValueString>(Name.ToString()));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_name"), NewNode->GetName());
	Root->SetStringField(TEXT("enum_path"), EnumPath);
	Root->SetStringField(TEXT("bound_enum"), Enum->GetName());
	Root->SetNumberField(TEXT("pose_pins"), PoseInputPins);
	Root->SetNumberField(TEXT("exposed_enumerators"), ChosenNames.Num());
	Root->SetArrayField(TEXT("enumerators"), ExposedJson);
	Root->SetArrayField(TEXT("pins"), BuildPinList(NewNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: set_sync_group (Group 2)
//
// Write GroupName/GroupRole/Method on an asset-player node. The Sync UPROPERTYs
// on FAnimNode_SequencePlayer are WITH_EDITORONLY_DATA + meta=(FoldProperty) — they
// are NOT reachable by FindPropertyByName on the node struct. Use the concrete
// player's public ENGINE_API SetGroupName(FName)/SetGroupRole(EAnimGroupRole::Type)/
// SetGroupMethod(EAnimSyncMethod) overrides instead. The base FAnimNode_AssetPlayerBase
// versions return false (no-op); only concrete players write.
// ---------------------------------------------------------------------------

namespace
{

/** Map a role string (case-insensitive) to EAnimGroupRole::Type. Returns false on unknown. */
bool ParseAnimGroupRole(const FString& In, EAnimGroupRole::Type& Out)
{
	if (In.Equals(TEXT("CanBeLeader"), ESearchCase::IgnoreCase))            { Out = EAnimGroupRole::CanBeLeader; return true; }
	if (In.Equals(TEXT("AlwaysLeader"), ESearchCase::IgnoreCase))           { Out = EAnimGroupRole::AlwaysLeader; return true; }
	if (In.Equals(TEXT("AlwaysFollower"), ESearchCase::IgnoreCase))         { Out = EAnimGroupRole::AlwaysFollower; return true; }
	if (In.Equals(TEXT("TransitionLeader"), ESearchCase::IgnoreCase))       { Out = EAnimGroupRole::TransitionLeader; return true; }
	if (In.Equals(TEXT("TransitionFollower"), ESearchCase::IgnoreCase))     { Out = EAnimGroupRole::TransitionFollower; return true; }
	if (In.Equals(TEXT("ExclusiveAlwaysLeader"), ESearchCase::IgnoreCase))  { Out = EAnimGroupRole::ExclusiveAlwaysLeader; return true; }
	return false;
}

/** Map a sync-method string (case-insensitive) to EAnimSyncMethod. Returns false on unknown. */
bool ParseAnimSyncMethod(const FString& In, EAnimSyncMethod& Out)
{
	if (In.Equals(TEXT("DoNotSync"), ESearchCase::IgnoreCase)) { Out = EAnimSyncMethod::DoNotSync; return true; }
	if (In.Equals(TEXT("SyncGroup"), ESearchCase::IgnoreCase)) { Out = EAnimSyncMethod::SyncGroup; return true; }
	if (In.Equals(TEXT("Graph"), ESearchCase::IgnoreCase))     { Out = EAnimSyncMethod::Graph; return true; }
	return false;
}

} // anonymous namespace

FMonolithActionResult FMonolithAbpWriteActions::HandleSetSyncGroup(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeId;    Params->TryGetStringField(TEXT("node_id"), NodeId);
	FString GroupName; Params->TryGetStringField(TEXT("group_name"), GroupName);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("");
	const FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	if (NodeId.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: node_id"));
	if (!Params->HasField(TEXT("group_name"))) return FMonolithActionResult::Error(TEXT("Missing required parameter: group_name"));

	// Role / method default to CanBeLeader / SyncGroup; reject unknown spellings.
	EAnimGroupRole::Type Role = EAnimGroupRole::CanBeLeader;
	if (Params->HasField(TEXT("group_role")))
	{
		const FString RoleStr = Params->GetStringField(TEXT("group_role"));
		if (!ParseAnimGroupRole(RoleStr, Role))
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Unknown group_role '%s'. Valid: CanBeLeader / AlwaysLeader / AlwaysFollower / TransitionLeader / TransitionFollower / ExclusiveAlwaysLeader"),
				*RoleStr));
		}
	}
	EAnimSyncMethod Method = EAnimSyncMethod::SyncGroup;
	if (Params->HasField(TEXT("sync_method")))
	{
		const FString MethodStr = Params->GetStringField(TEXT("sync_method"));
		if (!ParseAnimSyncMethod(MethodStr, Method))
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Unknown sync_method '%s'. Valid: DoNotSync / SyncGroup / Graph"), *MethodStr));
		}
	}

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	// Optional graph scope (mirror set_anim_graph_node_property's lookup).
	UEdGraph* ScopeGraph = nullptr;
	if (!StateName.IsEmpty() || (!GraphName.IsEmpty() && !GraphName.Equals(TEXT("AnimGraph"), ESearchCase::IgnoreCase)))
	{
		FString GraphError;
		ScopeGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	}

	UEdGraphNode* FoundNode = FindNodeByName(ABP, NodeId, ScopeGraph);
	if (!FoundNode) return FMonolithActionResult::Error(FString::Printf(TEXT("Node '%s' not found"), *NodeId));

	UAnimGraphNode_Base* AnimNode = Cast<UAnimGraphNode_Base>(FoundNode);
	if (!AnimNode)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Node '%s' is not a UAnimGraphNode_Base (class: %s)"), *NodeId, *FoundNode->GetClass()->GetName()));
	}

	// Resolve the inner FAnimNode and confirm it is a concrete player with sync-group setters.
	UScriptStruct* NodeStruct = nullptr; void* NodeAddr = nullptr; FString ResolveErr;
	if (!ResolveInnerAnimNode(AnimNode, NodeStruct, NodeAddr, ResolveErr))
	{
		return FMonolithActionResult::Error(ResolveErr);
	}

	// FAnimNode_SequencePlayer / FAnimNode_BlendSpacePlayer both override the setters as ENGINE_API.
	// Cast through whichever concrete struct the node carries; reject node types without these settings.
	// Wrap the Modify()/setters/ReconstructNode() in a transaction for undo parity with the other
	// Group 1/2 handlers (every early-return error path must close the transaction first).
	GEditor->BeginTransaction(FText::FromString(TEXT("Set Sync Group")));
	AnimNode->Modify();
	bool bNameOk = false, bRoleOk = false, bMethodOk = false;
	FString PlayerKind;
	if (NodeStruct->IsChildOf(FAnimNode_SequencePlayer::StaticStruct()))
	{
		FAnimNode_SequencePlayer* Player = static_cast<FAnimNode_SequencePlayer*>(NodeAddr);
		bNameOk   = Player->SetGroupName(FName(*GroupName));
		bRoleOk   = Player->SetGroupRole(Role);
		bMethodOk = Player->SetGroupMethod(Method);
		PlayerKind = TEXT("SequencePlayer");
	}
	else if (NodeStruct->IsChildOf(FAnimNode_BlendSpacePlayer::StaticStruct()))
	{
		FAnimNode_BlendSpacePlayer* Player = static_cast<FAnimNode_BlendSpacePlayer*>(NodeAddr);
		bNameOk   = Player->SetGroupName(FName(*GroupName));
		bRoleOk   = Player->SetGroupRole(Role);
		bMethodOk = Player->SetGroupMethod(Method);
		PlayerKind = TEXT("BlendSpacePlayer");
	}
	else
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Node '%s' (inner struct '%s') does not support sync groups — only Sequence Player and BlendSpace Player nodes expose group settings."),
			*NodeId, *NodeStruct->GetName()));
	}

	if (!bNameOk && !bRoleOk && !bMethodOk)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Node '%s' (%s) rejected all sync-group writes — the concrete player override returned false."),
			*NodeId, *PlayerKind));
	}

	AnimNode->ReconstructNode();
	GEditor->EndTransaction();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_id"), AnimNode->GetName());
	Root->SetStringField(TEXT("player_kind"), PlayerKind);
	Root->SetStringField(TEXT("group_name"), GroupName);
	Root->SetBoolField(TEXT("group_name_set"), bNameOk);
	Root->SetBoolField(TEXT("group_role_set"), bRoleOk);
	Root->SetBoolField(TEXT("sync_method_set"), bMethodOk);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: set_layered_blend_bones (Group 2)
//
// Configure the per-layer branch filters on a Layered Blend Per Bone node. The
// node starts with 1 blend-pose pin / 1 LayerSetup entry (ctor AddFirstPose).
// LayerSetup is an editfixedsize array tracking BlendPoses, so we MUST grow the
// pins first (AddPinToBlendByFilter — ANIMGRAPH_API; calls Node.AddPose which
// SyncBlendMasksAndLayers keeps LayerSetup matched), THEN write each layer's
// BranchFilters (FBranchFilter{ FName BoneName; int32 BlendDepth; }).
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleSetLayeredBlendBones(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeId; Params->TryGetStringField(TEXT("node_id"), NodeId);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("");
	const FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	if (NodeId.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: node_id"));

	const TArray<TSharedPtr<FJsonValue>>* LayersArray = nullptr;
	if (!Params->TryGetArrayField(TEXT("layers"), LayersArray) || !LayersArray)
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: layers (array of { bones: [{ bone, depth }] })"));
	}
	const int32 NumLayers = LayersArray->Num();
	if (NumLayers < 1) return FMonolithActionResult::Error(TEXT("layers must contain at least one layer"));
	if (NumLayers > 32) return FMonolithActionResult::Error(TEXT("layers is capped at 32"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	UEdGraph* ScopeGraph = nullptr;
	if (!StateName.IsEmpty() || (!GraphName.IsEmpty() && !GraphName.Equals(TEXT("AnimGraph"), ESearchCase::IgnoreCase)))
	{
		FString GraphError;
		ScopeGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	}

	UEdGraphNode* FoundNode = FindNodeByName(ABP, NodeId, ScopeGraph);
	if (!FoundNode) return FMonolithActionResult::Error(FString::Printf(TEXT("Node '%s' not found"), *NodeId));

	UAnimGraphNode_LayeredBoneBlend* LayerNode = Cast<UAnimGraphNode_LayeredBoneBlend>(FoundNode);
	if (!LayerNode)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Node '%s' is not a Layered Blend Per Bone node (class: %s)"), *NodeId, *FoundNode->GetClass()->GetName()));
	}

	// The node starts with 1 blend-pose pin / 1 LayerSetup entry. Grow the delta FIRST — LayerSetup is
	// editfixedsize and tracks BlendPoses, so a reflection write into a not-yet-grown LayerSetup would fail.
	const int32 StartingLayers = 1;
	GEditor->BeginTransaction(FText::FromString(TEXT("Set Layered Blend Bones")));
	LayerNode->Modify();
	for (int32 i = StartingLayers; i < NumLayers; ++i)
	{
		LayerNode->AddPinToBlendByFilter();
	}

	// Resolve the inner FAnimNode_LayeredBoneBlend and its LayerSetup array.
	UScriptStruct* NodeStruct = nullptr; void* NodeAddr = nullptr; FString ResolveErr;
	if (!ResolveInnerAnimNode(LayerNode, NodeStruct, NodeAddr, ResolveErr))
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(ResolveErr);
	}

	FArrayProperty* LayerSetupProp = CastField<FArrayProperty>(NodeStruct->FindPropertyByName(TEXT("LayerSetup")));
	if (!LayerSetupProp)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("Could not resolve 'LayerSetup' array property on the inner node"));
	}
	FStructProperty* LayerElemProp = CastField<FStructProperty>(LayerSetupProp->Inner);
	if (!LayerElemProp || !LayerElemProp->Struct)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("LayerSetup inner is not a struct (FInputBlendPose expected)"));
	}
	// FInputBlendPose.BranchFilters : TArray<FBranchFilter>
	FArrayProperty* BranchFiltersProp = CastField<FArrayProperty>(LayerElemProp->Struct->FindPropertyByName(TEXT("BranchFilters")));
	if (!BranchFiltersProp)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("FInputBlendPose has no 'BranchFilters' array property"));
	}
	FStructProperty* FilterStructProp = CastField<FStructProperty>(BranchFiltersProp->Inner);
	if (!FilterStructProp || !FilterStructProp->Struct)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("BranchFilters inner is not a struct (FBranchFilter expected)"));
	}
	FNameProperty* BoneNameProp = CastField<FNameProperty>(FilterStructProp->Struct->FindPropertyByName(TEXT("BoneName")));
	FIntProperty* BlendDepthProp = CastField<FIntProperty>(FilterStructProp->Struct->FindPropertyByName(TEXT("BlendDepth")));
	if (!BoneNameProp || !BlendDepthProp)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("FBranchFilter is missing the expected BoneName (FName) / BlendDepth (int32) fields"));
	}

	void* LayerSetupAddr = LayerSetupProp->ContainerPtrToValuePtr<void>(NodeAddr);
	FScriptArrayHelper LayerHelper(LayerSetupProp, LayerSetupAddr);
	if (LayerHelper.Num() < NumLayers)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("LayerSetup has %d entries after growing pins but %d layers were requested — pin grow did not size the editfixedsize array as expected"),
			LayerHelper.Num(), NumLayers));
	}

	// Write each layer's BranchFilters from the JSON, element-by-element via reflection
	// (mirrors the WriteBoneReferenceArray pattern, generalized for FBranchFilter's two fields).
	int32 TotalFilters = 0;
	for (int32 LayerIdx = 0; LayerIdx < NumLayers; ++LayerIdx)
	{
		const TSharedPtr<FJsonValue>& LayerValue = (*LayersArray)[LayerIdx];
		const TSharedPtr<FJsonObject>* LayerObj = nullptr;
		if (!LayerValue.IsValid() || !LayerValue->TryGetObject(LayerObj) || !LayerObj)
		{
			GEditor->EndTransaction();
			return FMonolithActionResult::Error(FString::Printf(TEXT("layers[%d] is not an object"), LayerIdx));
		}

		void* LayerElemPtr = LayerHelper.GetRawPtr(LayerIdx);
		void* BranchArrayPtr = BranchFiltersProp->ContainerPtrToValuePtr<void>(LayerElemPtr);
		FScriptArrayHelper BranchHelper(BranchFiltersProp, BranchArrayPtr);
		BranchHelper.EmptyValues();

		const TArray<TSharedPtr<FJsonValue>>* BonesArray = nullptr;
		if ((*LayerObj)->TryGetArrayField(TEXT("bones"), BonesArray) && BonesArray)
		{
			for (const TSharedPtr<FJsonValue>& BoneVal : *BonesArray)
			{
				const TSharedPtr<FJsonObject>* BoneObj = nullptr;
				if (!BoneVal.IsValid() || !BoneVal->TryGetObject(BoneObj) || !BoneObj) continue;

				FString BoneName;
				if (!(*BoneObj)->TryGetStringField(TEXT("bone"), BoneName) || BoneName.IsEmpty())
				{
					GEditor->EndTransaction();
					return FMonolithActionResult::Error(FString::Printf(
						TEXT("layers[%d].bones entry is missing a non-empty 'bone' field"), LayerIdx));
				}
				int32 Depth = 0;
				double DepthVal = 0.0;
				if ((*BoneObj)->TryGetNumberField(TEXT("depth"), DepthVal)) Depth = static_cast<int32>(DepthVal);

				const int32 ElemIdx = BranchHelper.AddValue();
				void* FilterPtr = BranchHelper.GetRawPtr(ElemIdx);
				BoneNameProp->SetPropertyValue(BoneNameProp->ContainerPtrToValuePtr<void>(FilterPtr), FName(*BoneName));
				BlendDepthProp->SetPropertyValue(BlendDepthProp->ContainerPtrToValuePtr<void>(FilterPtr), Depth);
				++TotalFilters;
			}
		}
	}
	GEditor->EndTransaction();

	LayerNode->ReconstructNode();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_id"), LayerNode->GetName());
	Root->SetNumberField(TEXT("layers"), NumLayers);
	Root->SetNumberField(TEXT("layer_setup_entries"), LayerHelper.Num());
	Root->SetNumberField(TEXT("total_branch_filters"), TotalFilters);
	Root->SetArrayField(TEXT("pins"), BuildPinList(LayerNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}


// ---------------------------------------------------------------------------
// Pack C — build_foot_ik_pass (COMPOSITE)
//
// Inserts a lightweight foot-grounding pass into the post-MM pose chain. Foot IK
// (TwoBoneIK) + pelvis offset (ModifyBone) are SkeletalControl nodes that operate
// in COMPONENT space (their pose link is FComponentSpacePoseLink 'ComponentPose'),
// so the pass is bracketed by a LocalToComponentSpace converter at entry and a
// ComponentToLocalSpace converter at exit. The whole bracket is spliced between
// whatever currently drives the Output Pose (e.g. Inertialization) and the Root.
//
// Chain (local -> ... -> local):
//   [src] -> L2C(LocalPose) ==CS==> ModifyBone(pelvis) -> TwoBoneIK(L) -> TwoBoneIK(R) -> C2L -> [Root.Result]
//
// Foot IK alphas are driven by the contact_l/contact_r curves (AlphaInputType=Curve,
// AlphaCurveName=<curve>) so the planted foot is locked and swing-foot IK relaxes.
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleBuildFootIkPass(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath       = Params->GetStringField(TEXT("abp_path"));
	const FString LeftFootBone  = Params->GetStringField(TEXT("left_foot_bone"));
	const FString RightFootBone = Params->GetStringField(TEXT("right_foot_bone"));
	const FString PelvisBone    = Params->GetStringField(TEXT("pelvis_bone"));
	FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	if (GraphName.IsEmpty()) GraphName = TEXT("AnimGraph");
	FString LeftCurve  = Params->HasField(TEXT("left_contact_curve"))  ? Params->GetStringField(TEXT("left_contact_curve"))  : TEXT("contact_l");
	FString RightCurve = Params->HasField(TEXT("right_contact_curve")) ? Params->GetStringField(TEXT("right_contact_curve")) : TEXT("contact_r");

	if (AbpPath.IsEmpty())       return FMonolithActionResult::Error(TEXT("Missing required parameter: abp_path"));
	if (LeftFootBone.IsEmpty() || RightFootBone.IsEmpty() || PelvisBone.IsEmpty())
		return FMonolithActionResult::Error(TEXT("left_foot_bone, right_foot_bone and pelvis_bone are all required"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AbpPath));

	FString GraphError;
	UEdGraph* Graph = ResolveTargetGraph(ABP, GraphName, TEXT(""), GraphError);
	if (!Graph) return FMonolithActionResult::Error(GraphError);

	// --- Capture the current Output Pose source (the node feeding Root 'Result') ---
	TArray<UAnimGraphNode_Root*> Roots;
	Graph->GetNodesOfClass<UAnimGraphNode_Root>(Roots);
	if (Roots.Num() == 0)
		return FMonolithActionResult::Error(FString::Printf(TEXT("No Output Pose (UAnimGraphNode_Root) in graph '%s'"), *GraphName));
	UAnimGraphNode_Root* RootNode = Roots[0];
	UEdGraphPin* RootResultPin = RootNode->FindPin(FName(TEXT("Result")), EGPD_Input);
	if (!RootResultPin)
		return FMonolithActionResult::Error(TEXT("Output Pose node has no 'Result' input pin"));

	FString SrcNodeName, SrcPinName;
	if (RootResultPin->LinkedTo.Num() > 0 && RootResultPin->LinkedTo[0])
	{
		UEdGraphPin* SrcPin = RootResultPin->LinkedTo[0];
		UEdGraphNode* SrcNode = SrcPin->GetOwningNodeUnchecked();
		SrcNodeName = SrcNode ? SrcNode->GetName() : FString();
		SrcPinName  = SrcPin->PinName.ToString();
	}
	const bool bHadSource = !SrcNodeName.IsEmpty();

	// --- Local helper: spawn a node via add_anim_graph_node internals, return its node_name ---
	auto SpawnNode = [&](const TSharedPtr<FJsonObject>& P) -> FString
	{
		P->SetStringField(TEXT("asset_path"), AbpPath);
		P->SetStringField(TEXT("graph_name"), GraphName);
		FMonolithActionResult R = HandleAddAnimGraphNode(P);
		return (R.bSuccess && R.Result.IsValid()) ? R.Result->GetStringField(TEXT("node_name")) : FString();
	};

	// --- Spawn the bracket + IK nodes ---
	TSharedPtr<FJsonObject> L2CParams = MakeShared<FJsonObject>();
	L2CParams->SetStringField(TEXT("node_type"), TEXT("LocalToComponentSpace"));
	L2CParams->SetNumberField(TEXT("position_x"), 300.0);
	const FString L2CNode = SpawnNode(L2CParams);

	TSharedPtr<FJsonObject> PelvisParams = MakeShared<FJsonObject>();
	PelvisParams->SetStringField(TEXT("node_type"), TEXT("ModifyBone"));
	PelvisParams->SetStringField(TEXT("bone_to_modify"), PelvisBone);
	PelvisParams->SetNumberField(TEXT("position_x"), 500.0);
	const FString PelvisNode = SpawnNode(PelvisParams);

	TSharedPtr<FJsonObject> IkLParams = MakeShared<FJsonObject>();
	IkLParams->SetStringField(TEXT("node_type"), TEXT("TwoBoneIK"));
	IkLParams->SetStringField(TEXT("ik_bone"), LeftFootBone);
	IkLParams->SetNumberField(TEXT("position_x"), 700.0);
	const FString IkLNode = SpawnNode(IkLParams);

	TSharedPtr<FJsonObject> IkRParams = MakeShared<FJsonObject>();
	IkRParams->SetStringField(TEXT("node_type"), TEXT("TwoBoneIK"));
	IkRParams->SetStringField(TEXT("ik_bone"), RightFootBone);
	IkRParams->SetNumberField(TEXT("position_x"), 900.0);
	const FString IkRNode = SpawnNode(IkRParams);

	TSharedPtr<FJsonObject> C2LParams = MakeShared<FJsonObject>();
	C2LParams->SetStringField(TEXT("node_type"), TEXT("ComponentToLocalSpace"));
	C2LParams->SetNumberField(TEXT("position_x"), 1100.0);
	const FString C2LNode = SpawnNode(C2LParams);

	if (L2CNode.IsEmpty() || PelvisNode.IsEmpty() || IkLNode.IsEmpty() || IkRNode.IsEmpty() || C2LNode.IsEmpty())
		return FMonolithActionResult::Error(TEXT("One or more foot-IK pass nodes failed to spawn"));

	// --- Gate foot IK alphas by the contact curves (skeletal-control alpha-as-curve) ---
	auto SetProp = [&](const FString& NodeId, const FString& PropPath, const FString& Value)
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		P->SetStringField(TEXT("asset_path"), AbpPath);
		P->SetStringField(TEXT("graph_name"), GraphName);
		P->SetStringField(TEXT("node_id"), NodeId);
		P->SetStringField(TEXT("property_path"), PropPath);
		P->SetStringField(TEXT("value"), Value);
		HandleSetAnimGraphNodeProperty(P);
	};
	if (!LeftCurve.IsEmpty())
	{
		SetProp(IkLNode, TEXT("AlphaInputType"), TEXT("Curve"));
		SetProp(IkLNode, TEXT("AlphaCurveName"), LeftCurve);
	}
	if (!RightCurve.IsEmpty())
	{
		SetProp(IkRNode, TEXT("AlphaInputType"), TEXT("Curve"));
		SetProp(IkRNode, TEXT("AlphaCurveName"), RightCurve);
	}

	// --- Make the skeletal-control nodes NON-INERT ---
	// Without these, the pelvis ModifyBone leaves TranslationMode = BMM_Ignore (does nothing)
	// and the TwoBoneIK nodes solve toward EffectorLocation (0,0,0) in component space — which
	// yanks the feet to the component origin. Set real modes / reference frames so the pass is
	// functional. EffectorLocation itself is exposed as an input pin (auto-exposed by
	// add_anim_graph_node for TwoBoneIK) so a downstream ground-trace solve can drive it; until
	// then BoneSpace + EffectorTarget=foot bone makes EffectorLocation(0,0,0) an identity solve
	// (foot stays at its animated location) rather than a destructive component-origin pull.
	//
	// EBoneModificationMode: BMM_Ignore / BMM_Replace / BMM_Additive (AnimNode_ModifyBone.h:14-25).
	// EBoneControlSpace: BCS_WorldSpace / BCS_ComponentSpace / BCS_ParentBoneSpace / BCS_BoneSpace.
	// Enum names are imported by ImportText_Direct (the same parser the Details panel uses).

	// Pelvis offset: additive vertical adjust in component space (the Translation pin drives the amount).
	SetProp(PelvisNode, TEXT("TranslationMode"),  TEXT("BMM_Additive"));
	SetProp(PelvisNode, TEXT("TranslationSpace"), TEXT("BCS_ComponentSpace"));

	// Foot IK effectors: solve relative to the foot bone's own space, with the effector target
	// bound to the foot bone, so EffectorLocation is a meaningful (non-component-origin) offset.
	SetProp(IkLNode, TEXT("EffectorLocationSpace"), TEXT("BCS_BoneSpace"));
	SetProp(IkLNode, TEXT("EffectorTarget.BoneReference.BoneName"), LeftFootBone);
	SetProp(IkRNode, TEXT("EffectorLocationSpace"), TEXT("BCS_BoneSpace"));
	SetProp(IkRNode, TEXT("EffectorTarget.BoneReference.BoneName"), RightFootBone);

	// --- Wire the chain (verified pin names: LocalPose / ComponentPose / Pose / Result) ---
	auto Connect = [&](const FString& SN, const FString& SP, const FString& TN, const FString& TP) -> bool
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		P->SetStringField(TEXT("asset_path"), AbpPath);
		P->SetStringField(TEXT("graph_name"), GraphName);
		P->SetStringField(TEXT("source_node"), SN);
		P->SetStringField(TEXT("source_pin"), SP);
		P->SetStringField(TEXT("target_node"), TN);
		P->SetStringField(TEXT("target_pin"), TP);
		P->SetBoolField(TEXT("compile"), false);
		return HandleConnectAnimGraphPins(P).bSuccess;
	};

	TSharedPtr<FJsonObject> Wires = MakeShared<FJsonObject>();
	// entry: previous source (local) -> L2C 'LocalPose'
	if (bHadSource)
		Wires->SetBoolField(TEXT("src_to_entry"), Connect(SrcNodeName, SrcPinName, L2CNode, TEXT("LocalPose")));
	// component-space chain: L2C 'ComponentPose' -> ModifyBone 'ComponentPose' -> IK_L 'ComponentPose' -> IK_R 'ComponentPose'
	Wires->SetBoolField(TEXT("l2c_to_pelvis"), Connect(L2CNode, TEXT("ComponentPose"), PelvisNode, TEXT("ComponentPose")));
	Wires->SetBoolField(TEXT("pelvis_to_ikl"), Connect(PelvisNode, TEXT("Pose"), IkLNode, TEXT("ComponentPose")));
	Wires->SetBoolField(TEXT("ikl_to_ikr"),    Connect(IkLNode, TEXT("Pose"), IkRNode, TEXT("ComponentPose")));
	// exit: IK_R 'Pose' (component) -> C2L 'ComponentPose' -> Root 'Result' (local)
	Wires->SetBoolField(TEXT("ikr_to_c2l"),    Connect(IkRNode, TEXT("Pose"), C2LNode, TEXT("ComponentPose")));
	Wires->SetBoolField(TEXT("exit_to_root"),  Connect(C2LNode, TEXT("Pose"), RootNode->GetName(), TEXT("Result")));

	ABP->MarkPackageDirty();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("graph_name"), GraphName);
	Root->SetStringField(TEXT("previous_output_source"), bHadSource ? SrcNodeName : FString(TEXT("<none>")));
	// entry/exit so the caller can re-splice: entry consumes the upstream pose, exit drives Output Pose.
	Root->SetStringField(TEXT("entry_node"), L2CNode);
	Root->SetStringField(TEXT("entry_pin"), TEXT("LocalPose"));
	Root->SetStringField(TEXT("exit_node"), C2LNode);
	Root->SetStringField(TEXT("exit_pin"), TEXT("Pose"));
	Root->SetStringField(TEXT("pelvis_modify_node"), PelvisNode);
	Root->SetStringField(TEXT("foot_ik_left_node"), IkLNode);
	Root->SetStringField(TEXT("foot_ik_right_node"), IkRNode);
	Root->SetStringField(TEXT("left_contact_curve"), LeftCurve);
	Root->SetStringField(TEXT("right_contact_curve"), RightCurve);
	Root->SetObjectField(TEXT("wires"), Wires);
	Root->SetBoolField(TEXT("compiled"), true);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}


// ---------------------------------------------------------------------------
// Pack C — assign_post_process_anim_rig
//
// Sets USkeletalMesh::PostProcessAnimBlueprint (the post-process anim instance
// class), which runs after the main anim instance and before physics. Verified
// accessor: USkeletalMesh::SetPostProcessAnimBlueprint(TSubclassOf<UAnimInstance>)
// (SkeletalMesh.h:2235). Direct member access is deprecated; the setter is public.
// An empty post_process_abp_path clears the assignment.
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAssignPostProcessAnimRig(const TSharedPtr<FJsonObject>& Params)
{
	const FString MeshPath = Params->GetStringField(TEXT("mesh_path"));
	FString PostAbpPath;
	Params->TryGetStringField(TEXT("post_process_abp_path"), PostAbpPath);

	if (MeshPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: mesh_path"));

	USkeletalMesh* Mesh = FMonolithAssetUtils::LoadAssetByPath<USkeletalMesh>(MeshPath);
	if (!Mesh) return FMonolithActionResult::Error(FString::Printf(TEXT("SkeletalMesh not found: %s"), *MeshPath));

	TSubclassOf<UAnimInstance> PostClass = nullptr;
	const bool bClearing = PostAbpPath.IsEmpty() || PostAbpPath.Equals(TEXT("None"), ESearchCase::IgnoreCase);
	if (!bClearing)
	{
		// Accept either an AnimBlueprint asset (resolve its generated class) or a direct class path.
		UAnimBlueprint* PostAbp = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(PostAbpPath);
		if (PostAbp)
		{
			UClass* GenClass = PostAbp->GeneratedClass;
			if (!GenClass || !GenClass->IsChildOf(UAnimInstance::StaticClass()))
				return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint '%s' has no UAnimInstance generated class (recompile it first)"), *PostAbpPath));
			PostClass = GenClass;
		}
		else
		{
			// Fall back to resolving as a class path (e.g. /Game/.../ABP_X.ABP_X_C).
			UClass* AsClass = LoadClass<UAnimInstance>(nullptr, *PostAbpPath);
			if (!AsClass)
				return FMonolithActionResult::Error(FString::Printf(TEXT("Could not resolve post-process AnimBlueprint or AnimInstance class: %s"), *PostAbpPath));
			PostClass = AsClass;
		}
	}

	Mesh->Modify();
	Mesh->SetPostProcessAnimBlueprint(PostClass);
	Mesh->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("mesh_path"), MeshPath);
	Root->SetBoolField(TEXT("cleared"), bClearing);
	Root->SetStringField(TEXT("post_process_class"), PostClass ? PostClass->GetPathName() : FString(TEXT("<none>")));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// AnimGraph authoring (Group 3) — reflection-heavy Tier-2 nodes
// ---------------------------------------------------------------------------

namespace
{

/**
 * Resolve a single UClass from a user specifier (path or name) that must be a
 * non-abstract subclass of RequiredBase. Returns nullptr with OutError set on a
 * miss, an ambiguous match, or a wrong-base match. Reuses ResolveClassSpecifier
 * (the same path/name resolver add_anim_graph_node uses for node_class).
 */
UClass* ResolveSingleClassOfType(const FString& Specifier, UClass* RequiredBase,
                                 const TCHAR* WhatFor, FString& OutError)
{
	const FString Clean = CleanClassSpecifier(Specifier);
	if (Clean.IsEmpty())
	{
		OutError = FString::Printf(TEXT("Empty %s class specifier"), WhatFor);
		return nullptr;
	}

	TArray<UClass*> Matches = ResolveClassSpecifier(Clean);
	TArray<UClass*> Valid;
	for (UClass* Match : Matches)
	{
		if (Match && Match->IsChildOf(RequiredBase) && !Match->HasAnyClassFlags(CLASS_Abstract))
		{
			Valid.AddUnique(Match);
		}
	}

	if (Valid.Num() == 0)
	{
		OutError = FString::Printf(
			TEXT("Could not resolve %s '%s' to a non-abstract %s subclass. Provide a full class path such as '/Game/Path/Asset.Asset_C'."),
			WhatFor, *Clean, *RequiredBase->GetName());
		return nullptr;
	}
	if (Valid.Num() > 1)
	{
		OutError = FString::Printf(TEXT("Ambiguous %s '%s'. Matches: %s. Use a full class path."),
			WhatFor, *Clean, *DescribeClassMatches(Valid));
		return nullptr;
	}
	return Valid[0];
}

} // anonymous namespace

// ---------------------------------------------------------------------------
// Action: add_anim_control_rig_node (Group 3)
//
// Spawn UAnimGraphNode_ControlRig (a UAnimGraphNode_CustomProperty — NOT a
// BoundGraph-owning node, so the shared template/PerformAction spawn path is
// safe) and set the rig class. FAnimNode_ControlRig::ControlRigClass is a
// private TSubclassOf<UControlRig> but EditAnywhere (AnimNode_ControlRig.h:56-57),
// so it is reflection-writable via the same ImportTextOntoStruct path
// set_anim_graph_node_property uses (the public SetControlRigClass setter is
// avoided — it resolves ambiguously against a BP-library static). After the
// class write, ReconstructNode() fires the editor node's CreateCustomPins()
// (AnimGraphNode_ControlRig.cpp:45), which calls RebuildExposedProperties() and
// regenerates the rig's input/output pins from its exposed variables.
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddAnimControlRigNode(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString ControlRigClassSpec; Params->TryGetStringField(TEXT("control_rig_class"), ControlRigClassSpec);
	FString SourceNode;          Params->TryGetStringField(TEXT("source_node"), SourceNode);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	const FString StateName = Params->HasField(TEXT("state_name")) ? Params->GetStringField(TEXT("state_name")) : TEXT("");

	if (ControlRigClassSpec.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: control_rig_class"));

	double TempVal;
	float PosX = 200.f, PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	// Resolve the Control Rig class up-front so a bad class never spawns a node.
	FString ClassError;
	UClass* RigClass = ResolveSingleClassOfType(ControlRigClassSpec, UControlRig::StaticClass(), TEXT("control_rig_class"), ClassError);
	if (!RigClass) return FMonolithActionResult::Error(ClassError);

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, StateName, GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	// Spawn the node and (optionally) wire source_node's pose-out into the node's pose input.
	// FAnimNode_ControlRig's pose input pin is "Source" (FAnimNode_ControlRigBase pose link).
	UEdGraphNode* Src = nullptr;
	if (!SourceNode.IsEmpty())
	{
		Src = FindNodeByName(ABP, SourceNode, TargetGraph);
		if (!Src) return FMonolithActionResult::Error(FString::Printf(TEXT("source_node '%s' not found in target graph"), *SourceNode));
	}

	FString SpawnError;
	UAnimGraphNode_Base* NewNode = SpawnAndWirePoseInput(
		TargetGraph, UAnimGraphNode_ControlRig::StaticClass(), PosX, PosY,
		Src, Src ? FName(TEXT("Source")) : NAME_None, SpawnError);
	if (!NewNode) return FMonolithActionResult::Error(SpawnError);

	UAnimGraphNode_ControlRig* CRNode = Cast<UAnimGraphNode_ControlRig>(NewNode);
	if (!CRNode) return FMonolithActionResult::Error(TEXT("Spawned node is not a Control Rig anim node"));

	// Reflection-write the inner FAnimNode_ControlRig.ControlRigClass (private + EditAnywhere).
	UScriptStruct* NodeStruct = nullptr; void* NodeAddr = nullptr; FString ResolveErr;
	if (!ResolveInnerAnimNode(NewNode, NodeStruct, NodeAddr, ResolveErr))
	{
		return FMonolithActionResult::Error(ResolveErr);
	}

	GEditor->BeginTransaction(FText::FromString(TEXT("Set Control Rig Class")));
	NewNode->Modify();
	FString WriteErr;
	if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("ControlRigClass"), RigClass->GetPathName(), NewNode, WriteErr))
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not write ControlRigClass on the Control Rig node: %s"), *WriteErr));
	}

	// ReconstructNode() fires CreateCustomPins() -> RebuildExposedProperties(), regenerating the
	// rig's IO pins from its exposed variables (AnimGraphNode_ControlRig.cpp:45-50).
	NewNode->ReconstructNode();
	GEditor->EndTransaction();

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_name"), NewNode->GetName());
	Root->SetStringField(TEXT("node_class"), NewNode->GetClass()->GetName());
	Root->SetStringField(TEXT("control_rig_class"), RigClass->GetPathName());
	Root->SetBoolField(TEXT("pose_input_wired"), Src != nullptr);
	Root->SetArrayField(TEXT("pins"), BuildPinList(NewNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// Action: add_linked_anim_layer (Group 3)
//
// Spawn UAnimGraphNode_LinkedAnimLayer (UCLASS(MinimalAPI) — its SetLayerName /
// UpdateGuidForLayer / GetLayerName carry no ANIMGRAPH_API, so calling them from
// this module would LNK2019). The node owns FAnimNode_CustomProperty machinery,
// so spawn it pristine via FGraphNodeCreator (mirroring SpawnAndWirePoseInput's
// BoundGraph branch) rather than the template/duplicate path. Then drive it by
// reflection only:
//   - inner Node.Layer (FName, EditAnywhere)         AnimNode_LinkedAnimLayer.h:34
//   - inner Node.Interface (TSubclassOf, UPROPERTY)  AnimNode_LinkedAnimLayer.h:30
//   - inner Node.InstanceClass (TSubclassOf)         AnimNode_LinkedAnimGraph.h:41
//   - editor InterfaceGuid (FGuid, UPROPERTY)        AnimGraphNode_LinkedAnimLayer.h:30
// The Interface + InterfaceGuid are resolved from the ABP's implemented anim-layer
// interface graph whose name matches layer_name — exactly the engine's own
// GetInterfaceForLayer / GetGuidForLayer lookup (AnimGraphNode_LinkedAnimLayer.cpp:813,863):
// walk UBlueprint::ImplementedInterfaces, match InterfaceGraph->GetFName() == layer_name,
// read InterfaceDesc.Interface (the UAnimLayerInterface subclass) and InterfaceGraph->InterfaceGuid.
// ReconstructNode() then regenerates the layer's IO pins from the resolved interface.
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAbpWriteActions::HandleAddLinkedAnimLayer(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor) return FMonolithActionResult::Error(TEXT("Editor is not available"));

	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString LayerName;          Params->TryGetStringField(TEXT("layer_name"), LayerName);
	FString InterfaceClassSpec; Params->TryGetStringField(TEXT("interface_class"), InterfaceClassSpec);
	FString InstanceClassSpec;  Params->TryGetStringField(TEXT("instance_class"), InstanceClassSpec);
	const FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");

	if (LayerName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: layer_name"));

	double TempVal;
	float PosX = 200.f, PosY = 0.f;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<float>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<float>(TempVal);

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP) return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));

	// Resolve the interface + GUID from the ABP's implemented anim-layer interface graphs, exactly as
	// the engine's GetInterfaceForLayer/GetGuidForLayer do: match the interface graph whose name is the
	// layer name. This also validates that the ABP actually implements a layer with this name.
	const FName LayerFName(*LayerName);
	UClass* ResolvedInterfaceClass = nullptr;     // UAnimLayerInterface subclass that declares the layer
	FGuid   ResolvedGuid;
	bool    bFoundLayer = false;
	TArray<FString> AvailableLayers;              // for the not-found error listing

	UClass* RequestedInterface = nullptr;
	if (!InterfaceClassSpec.IsEmpty())
	{
		FString IfaceErr;
		RequestedInterface = ResolveSingleClassOfType(InterfaceClassSpec, UAnimLayerInterface::StaticClass(), TEXT("interface_class"), IfaceErr);
		if (!RequestedInterface) return FMonolithActionResult::Error(IfaceErr);
	}

	for (const FBPInterfaceDescription& InterfaceDesc : ABP->ImplementedInterfaces)
	{
		UClass* IfaceClass = InterfaceDesc.Interface;
		if (!IfaceClass || !IfaceClass->IsChildOf(UAnimLayerInterface::StaticClass()))
		{
			continue; // only anim-layer interfaces declare linkable layers
		}
		// If interface_class was supplied, only consider that interface's graphs.
		if (RequestedInterface && IfaceClass != RequestedInterface)
		{
			continue;
		}
		for (const UEdGraph* InterfaceGraph : InterfaceDesc.Graphs)
		{
			if (!InterfaceGraph) continue;
			AvailableLayers.AddUnique(InterfaceGraph->GetFName().ToString());
			if (InterfaceGraph->GetFName() == LayerFName)
			{
				ResolvedInterfaceClass = IfaceClass;
				ResolvedGuid = InterfaceGraph->InterfaceGuid;
				bFoundLayer = true;
				break;
			}
		}
		if (bFoundLayer) break;
	}

	if (!bFoundLayer)
	{
		if (AvailableLayers.Num() == 0)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("AnimBlueprint '%s' implements no anim-layer interface — nothing to link. Add a UAnimLayerInterface and declare the layer first."),
				*AssetPath));
		}
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Layer '%s' not found among the implemented anim-layer interface graphs. Available layers: [%s]"),
			*LayerName, *FString::Join(AvailableLayers, TEXT(", "))));
	}

	// Optional external instance class (only meaningful for non-self interface layers).
	UClass* InstanceClass = nullptr;
	if (!InstanceClassSpec.IsEmpty())
	{
		FString InstErr;
		InstanceClass = ResolveSingleClassOfType(InstanceClassSpec, UAnimInstance::StaticClass(), TEXT("instance_class"), InstErr);
		if (!InstanceClass) return FMonolithActionResult::Error(InstErr);
	}

	FString GraphError;
	UEdGraph* TargetGraph = ResolveTargetGraph(ABP, GraphName, TEXT(""), GraphError);
	if (!TargetGraph) return FMonolithActionResult::Error(GraphError);

	// Spawn pristine via FGraphNodeCreator — the LinkedAnimLayer custom-property machinery makes the
	// template/duplicate path unsafe (mirrors SpawnAndWirePoseInput's BoundGraph branch).
	GEditor->BeginTransaction(FText::FromString(TEXT("Add Linked Anim Layer")));
	TargetGraph->Modify();

	UAnimGraphNode_LinkedAnimLayer* LayerNode = nullptr;
	{
		FGraphNodeCreator<UAnimGraphNode_LinkedAnimLayer> Creator(*TargetGraph);
		LayerNode = Creator.CreateNode(/*bSelectNewNode=*/false);
		if (!LayerNode)
		{
			GEditor->EndTransaction();
			return FMonolithActionResult::Error(TEXT("FGraphNodeCreator failed to create the Linked Anim Layer node"));
		}
		LayerNode->NodePosX = static_cast<int32>(PosX);
		LayerNode->NodePosY = static_cast<int32>(PosY);
		Creator.Finalize();
	}

	LayerNode->Modify();

	// Reflection-write the inner FAnimNode_LinkedAnimLayer fields via the proven inner-struct path.
	UScriptStruct* NodeStruct = nullptr; void* NodeAddr = nullptr; FString ResolveErr;
	if (!ResolveInnerAnimNode(LayerNode, NodeStruct, NodeAddr, ResolveErr))
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(ResolveErr);
	}

	FString WriteErr;
	if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("Layer"), LayerName, LayerNode, WriteErr))
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(FString::Printf(TEXT("Could not write Layer name: %s"), *WriteErr));
	}
	// Interface: a non-self layer carries its declaring UAnimLayerInterface subclass.
	if (ResolvedInterfaceClass)
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("Interface"), ResolvedInterfaceClass->GetPathName(), LayerNode, WriteErr))
		{
			GEditor->EndTransaction();
			return FMonolithActionResult::Error(FString::Printf(TEXT("Could not write Interface class: %s"), *WriteErr));
		}
	}
	// InstanceClass: optional external anim instance (only valid for non-self interface layers).
	if (InstanceClass)
	{
		if (!ImportTextOntoStruct(NodeStruct, NodeAddr, TEXT("InstanceClass"), InstanceClass->GetPathName(), LayerNode, WriteErr))
		{
			GEditor->EndTransaction();
			return FMonolithActionResult::Error(FString::Printf(TEXT("Could not write InstanceClass: %s"), *WriteErr));
		}
	}

	// Keep the editor node's FunctionReference (FMemberReference) in sync with Node.Layer, exactly as
	// the engine's UAnimGraphNode_LinkedAnimLayer::SetLayerName does (AnimGraphNode_LinkedAnimLayer.cpp:841-855):
	// an external-interface layer references the layer function on the interface class (with its function
	// GUID); a self layer is a self member. Without this, GetLayerName()'s
	// ensure(FunctionReference.GetMemberName() == Node.Layer) (cpp:859) can fire on display and
	// jump-to-definition won't resolve. FunctionReference is protected on the base node, so build it
	// locally and copy it through the reflected UPROPERTY. ResolvedInterfaceClass maps to SetLayerName's
	// GetTargetClass() (non-null = external interface, null = self).
	{
		FMemberReference LayerFunctionRef;
		if (ResolvedInterfaceClass)
		{
			FGuid FunctionGuid;
			FBlueprintEditorUtils::GetFunctionGuidFromClassByFieldName(
				FBlueprintEditorUtils::GetMostUpToDateClass(ResolvedInterfaceClass), LayerFName, FunctionGuid);
			LayerFunctionRef.SetExternalMember(LayerFName, ResolvedInterfaceClass, FunctionGuid);
		}
		else
		{
			LayerFunctionRef.SetSelfMember(LayerFName);
		}

		if (FStructProperty* FuncRefProp = CastField<FStructProperty>(LayerNode->GetClass()->FindPropertyByName(TEXT("FunctionReference"))))
		{
			void* FuncRefAddr = FuncRefProp->ContainerPtrToValuePtr<void>(LayerNode);
			*static_cast<FMemberReference*>(FuncRefAddr) = LayerFunctionRef;
		}
		else
		{
			GEditor->EndTransaction();
			return FMonolithActionResult::Error(TEXT("Could not locate the FunctionReference UPROPERTY on the Linked Anim Layer node"));
		}
	}

	// Reflection-set the editor-node InterfaceGuid UPROPERTY (FGuid has a text form via ExportText).
	if (FStructProperty* GuidProp = CastField<FStructProperty>(LayerNode->GetClass()->FindPropertyByName(TEXT("InterfaceGuid"))))
	{
		void* GuidAddr = GuidProp->ContainerPtrToValuePtr<void>(LayerNode);
		*static_cast<FGuid*>(GuidAddr) = ResolvedGuid;
	}
	else
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("Could not locate the InterfaceGuid UPROPERTY on the Linked Anim Layer node"));
	}

	// ReconstructNode() regenerates the layer's IO pins from the resolved interface
	// (UAnimGraphNode_LinkedAnimLayer::ReconstructNode override -> CreateCustomPins).
	LayerNode->ReconstructNode();
	GEditor->EndTransaction();

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	FKismetEditorUtilities::CompileBlueprint(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("node_name"), LayerNode->GetName());
	Root->SetStringField(TEXT("layer_name"), LayerName);
	Root->SetStringField(TEXT("interface_class"), ResolvedInterfaceClass ? ResolvedInterfaceClass->GetPathName() : FString(TEXT("<self>")));
	Root->SetStringField(TEXT("interface_guid"), ResolvedGuid.ToString());
	Root->SetBoolField(TEXT("guid_resolved"), ResolvedGuid.IsValid());
	if (InstanceClass) Root->SetStringField(TEXT("instance_class"), InstanceClass->GetPathName());
	Root->SetArrayField(TEXT("pins"), BuildPinList(LayerNode));
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}
