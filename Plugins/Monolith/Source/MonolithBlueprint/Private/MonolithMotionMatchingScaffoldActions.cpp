#include "MonolithMotionMatchingScaffoldActions.h"
#include "MonolithBlueprintInternal.h"
#include "MonolithBlueprintComponentActions.h"
#include "MonolithBlueprintCDOActions.h"
#include "MonolithBlueprintCompileActions.h"
#include "MonolithBlueprintGraphActions.h"
#include "MonolithBlueprintNodeActions.h"
#include "MonolithBlueprintVariableActions.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "MonolithAssetUtils.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Engine/InheritableComponentHandler.h"
#include "Engine/SCS_Node.h"
#include "Engine/SimpleConstructionScript.h"
#include "Animation/AnimBlueprint.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Editor.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "UObject/UnrealType.h"
#include "UObject/Package.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "EditorAssetLibrary.h"

// Enhanced Input — UInputMappingContext / UInputAction live in the EnhancedInput
// module (verified: Engine/Plugins/EnhancedInput/Source/EnhancedInput/Public/).
#include "InputMappingContext.h"
#include "InputAction.h"

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

void FMonolithMotionMatchingScaffoldActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("blueprint"), TEXT("set_anim_class"),
		TEXT("Point a character/actor Blueprint's skeletal mesh component at an AnimBP's generated class. "
			 "Resolves the named component (on a Character BP the inherited mesh is 'Mesh'), sets its "
			 "AnimClass UPROPERTY to the AnimBP GeneratedClass, and warns (without failing) if the AnimBP "
			 "graph contains no Motion Matching node. Marks the Blueprint modified."),
		FMonolithActionHandler::CreateStatic(&HandleSetAnimClass),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("bp_path"), TEXT("Character/actor Blueprint asset path"))
			.Required(TEXT("component"), TEXT("string"), TEXT("Skeletal mesh component variable name (e.g. 'Mesh' on a Character BP)"))
			.RequiredAssetPath(TEXT("anim_bp_path"), TEXT("Animation Blueprint asset path whose generated class becomes the AnimClass"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("apply_movement_preset"),
		TEXT("Apply a CharacterMovementComponent locomotion preset to a character Blueprint's CDO. "
			 "Presets: 'orient_to_movement' (bOrientRotationToMovement=true, bUseControllerDesiredRotation=false, "
			 "RotationRate set) and 'strafe_controller_desired' (the inverse + MaxAcceleration set). "
			 "Marks the Blueprint modified."),
		FMonolithActionHandler::CreateStatic(&HandleApplyMovementPreset),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("bp_path"), TEXT("Character Blueprint asset path"))
			.Required(TEXT("preset"), TEXT("string"), TEXT("Preset name: 'orient_to_movement' | 'strafe_controller_desired'"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("add_engine_component_typed"),
		TEXT("Resolve a UActorComponent subclass by friendly name and add it to a Blueprint's construction "
			 "script. General utility. NOTE: CharacterTrajectory is intentionally NOT special-cased — there is "
			 "no CharacterTrajectoryComponent in UE 5.7; Motion Matching trajectory is AnimBP-side "
			 "(Pose History node bGenerateTrajectory)."),
		FMonolithActionHandler::CreateStatic(&HandleAddEngineComponentTyped),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("bp_path"), TEXT("Blueprint asset path"))
			.Required(TEXT("component_type"), TEXT("string"), TEXT("UActorComponent subclass friendly name (e.g. 'SpringArmComponent')"))
			.Required(TEXT("component_name"), TEXT("string"), TEXT("Variable name for the new component"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("scaffold_locomotion_input"),
		TEXT("Create a UInputMappingContext asset + one UInputAction asset per 'actions' entry, then add "
			 "event-graph nodes binding each action to AddMovementInput. Reuses add_event_node / add_nodes_bulk "
			 "/ connect_pins_bulk. Marks the Blueprint modified."),
		FMonolithActionHandler::CreateStatic(&HandleScaffoldLocomotionInput),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("bp_path"), TEXT("Character Blueprint asset path"))
			.RequiredAssetPath(TEXT("imc_path"), TEXT("Asset path for the new InputMappingContext"))
			.Required(TEXT("actions"), TEXT("array"), TEXT("Array of {name, value_type} — value_type one of Digital(bool)/Axis1D/Axis2D/Axis3D. One UInputAction asset created per entry."))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("validate_animbp_variable_contract"),
		TEXT("Reflection-walk the AnimBP's exposed (BlueprintReadWrite) variables against the character "
			 "Blueprint's published variables. Reports 'missing' (the ABP reads a var the BP does not publish) "
			 "and 'extra' (the BP publishes a var the ABP does not consume). Read-only — no mutation."),
		FMonolithActionHandler::CreateStatic(&HandleValidateAnimBpVariableContract),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.RequiredAssetPath(TEXT("bp_path"), TEXT("Character Blueprint asset path"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("scaffold_motion_matching_character"),
		TEXT("COMPOSITE: create or reparent a character Blueprint (default parent ACharacter so it has Mesh + "
			 "CharacterMovementComponent), optionally set the skeletal mesh, then apply the AnimClass (set_anim_class) "
			 "and a CharacterMovementComponent preset (apply_movement_preset, default 'orient_to_movement'). "
			 "Trajectory is AnimBP-side (bGenerateTrajectory) — no trajectory component is added. Compiles the BP."),
		FMonolithActionHandler::CreateStatic(&HandleScaffoldMotionMatchingCharacter),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("bp_path"), TEXT("Character Blueprint asset path (created if absent, reparented if present)"))
			.Optional(TEXT("parent_class"), TEXT("string"), TEXT("Parent class for a newly-created BP (default 'Character')"), TEXT("Character"))
			.RequiredAssetPath(TEXT("anim_bp_path"), TEXT("Animation Blueprint asset path"))
			.OptionalAssetPath(TEXT("mesh"), TEXT("Skeletal mesh asset to assign to the mesh component (optional)"))
			.Optional(TEXT("movement_preset"), TEXT("string"), TEXT("CMC preset (default 'orient_to_movement')"), TEXT("orient_to_movement"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("get_inherited_component_override"),
		TEXT("READ-ONLY: report the effective value(s) of a component override on a child Blueprint. "
			 "Resolves the effective component template (CDO subobject for an inherited native component "
			 "like a Character's mesh, or the Inheritable Component Handler override for an SCS-inherited "
			 "component), reads the requested property (or a default set: AnimClass, SkeletalMesh, "
			 "AnimationMode) by reflection, and reports 'source' (cdo_native / ich / scs). This is the "
			 "verified read of what set_anim_class / set_mesh / set_component_property actually persisted."),
		FMonolithActionHandler::CreateStatic(&HandleGetInheritedComponentOverride),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("bp_path"), TEXT("Child Blueprint asset path"))
			.Required(TEXT("component"), TEXT("string"), TEXT("Component variable name or alias (e.g. 'Mesh' resolves to a Character's CharacterMesh0)"))
			.Optional(TEXT("property_name"), TEXT("string"), TEXT("Single property to read; if omitted, a default set is reported (AnimClass, SkeletalMesh, AnimationMode)"))
			.Build());

	// -----------------------------------------------------------------------
	// Pack A — thread-safe AnimBP event-graph authoring (anim-aware composites)
	// -----------------------------------------------------------------------

	Registry.RegisterAction(TEXT("blueprint"), TEXT("scaffold_threadsafe_update"),
		TEXT("Override UAnimInstance::BlueprintThreadSafeUpdateAnimation on an Animation Blueprint so it "
			 "reads owning-pawn state on the worker thread. Thin anim-aware wrapper over override_parent_function "
			 "(GetOverrideFunctionClass + AddFunctionGraph against the declaring UAnimInstance class), so a FUTURE "
			 "C++ AnimInstance parent can absorb the body without a graph rewrite. Returns the override graph name "
			 "and entry node id for downstream chaining. No-ops cleanly if the override already exists."),
		FMonolithActionHandler::CreateStatic(&HandleScaffoldThreadSafeUpdate),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("add_pawn_owner_access"),
		TEXT("Inside the thread-safe update graph, author a TryGetPawnOwner call (UAnimInstance::TryGetPawnOwner — "
			 "worker-thread safe) followed by a Cast-To-Character node, and return the cast result pin name so "
			 "subsequent nodes can read pawn / CharacterMovementComponent members. Ensures the thread-safe update "
			 "exists first (composes scaffold_threadsafe_update). Reuses add_nodes_bulk + connect_pins_bulk internals."),
		FMonolithActionHandler::CreateStatic(&HandleAddPawnOwnerAccess),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Optional(TEXT("cast_class"), TEXT("string"), TEXT("Class to cast the pawn owner to (default 'Character'). Use an overridable parent type for a future C++ AnimInstance swap."), TEXT("Character"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("scaffold_locomotion_anim_values"),
		TEXT("COMPOSITE: ensure a thread-safe update/function graph exists, create the locomotion anim variables (Velocity vector, "
			 "GroundSpeed float, Acceleration vector, bIsMoving bool, bIsCrouched bool), then author a FULLY WIRED node graph that "
			 "reads pawn state via GENUINE thread-safe Property Access (UK2Node_PropertyAccess) and SETs each anim var. "
			 "THREAD-SAFE BY CONSTRUCTION: the pawn-state SOURCES are Property Access reads (Velocity/Acceleration/crouch), NOT a "
			 "TryGetPawnOwner -> Cast -> getter chain (that chain triggers 'Accessing an object reference is not thread-safe'). "
			 "Velocity feeds Set Velocity + VSizeXY -> Set GroundSpeed; Acceleration feeds Set Acceleration; crouch feeds Set bIsCrouched; "
			 "bIsMoving = (GroundSpeed > threshold AND NOT Acceleration.IsNearlyZero). The pure math (VSizeXY, compares, AND/NOT) and the "
			 "Set-anim-var nodes are unchanged; only the read SOURCE is Property Access. "
			 "PATHS: velocity_path / acceleration_path / crouch_path are verbatim Property Access resolution chains. They DEFAULT to the "
			 "Game Animation Sample SandboxCharacter_CMC_ABP layout (a 'CharacterProperties' member struct populated game-thread-side: "
			 "Velocity/InputAcceleration/Stance). If your AnimBP does NOT have that struct, supply paths into a source your AnimBP exposes "
			 "(e.g. an AnimInstance member variable) — Property Access resolves a member of the AnimInstance itself, so the access root must "
			 "exist on the AnimBP. Authors into BlueprintThreadSafeUpdateAnimation by default; pass target_graph to author into a named "
			 "thread-safe FUNCTION graph (e.g. 'UpdateEssentialValues'). Reuses add_variable + add_property_access_node + add_nodes_bulk + connect_pins_bulk."),
		FMonolithActionHandler::CreateStatic(&HandleScaffoldLocomotionAnimValues),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Optional(TEXT("target_graph"),     TEXT("string"), TEXT("Thread-safe graph/function to author into (default 'BlueprintThreadSafeUpdateAnimation'). Pass a function name like 'UpdateEssentialValues' to write into that function graph; it must already exist (override/author it first)."), {TEXT("function_name"), TEXT("graph_name")})
			.Optional(TEXT("velocity_var"),     TEXT("string"), TEXT("Name override for the Velocity vector var (default 'Velocity')"),         TEXT("Velocity"))
			.Optional(TEXT("ground_speed_var"), TEXT("string"), TEXT("Name override for the GroundSpeed float var (default 'GroundSpeed')"),    TEXT("GroundSpeed"))
			.Optional(TEXT("acceleration_var"), TEXT("string"), TEXT("Name override for the Acceleration vector var (default 'Acceleration')"), TEXT("Acceleration"))
			.Optional(TEXT("is_moving_var"),    TEXT("string"), TEXT("Name override for the bIsMoving bool var (default 'bIsMoving')"),         TEXT("bIsMoving"))
			.Optional(TEXT("is_crouched_var"),  TEXT("string"), TEXT("Name override for the bIsCrouched bool var (default 'bIsCrouched')"),     TEXT("bIsCrouched"))
			.Optional(TEXT("velocity_path"),     TEXT("array"), TEXT("Property Access path (array of strings) for Velocity. Default: ['CharacterProperties','Velocity'] (Game Animation Sample). For a UserDefinedStruct field use the GUID-suffixed internal name."))
			.Optional(TEXT("acceleration_path"), TEXT("array"), TEXT("Property Access path for Acceleration. Default: ['CharacterProperties','InputAcceleration']."))
			.Optional(TEXT("crouch_path"),       TEXT("array"), TEXT("Property Access path for the crouch SOURCE (must resolve to a BOOL to feed the bIsCrouched var cleanly). NO default — the Game Animation Sample exposes a Stance ENUM, not a bool, so crouch is SKIPPED unless you supply a bool path. When omitted, the bIsCrouched var is created but left unset (no dangling pin)."))
			.Build());

	// -----------------------------------------------------------------------
	// Pack D — movement tuning (CMC speed bands)
	// -----------------------------------------------------------------------

	Registry.RegisterAction(TEXT("blueprint"), TEXT("apply_locomotion_speed_band"),
		TEXT("Set CharacterMovementComponent speed-band caps on a Character Blueprint's CDO: MaxWalkSpeed "
			 "(baseline = run_speed unless max_walk_speed given), MaxWalkSpeedCrouched (= crouch_speed), "
			 "MaxAcceleration, BrakingDecelerationWalking. walk/jog/run are documented band values the Behavior "
			 "Tree picks from at runtime (these are the CMC caps; the BT's SetMaxWalkSpeed varies within them). "
			 "Uses the same persistence handshake as apply_movement_preset (set_component_property -> structural "
			 "modify -> compile for the inherited native CMC). Returns the applied values + the band echo."),
		FMonolithActionHandler::CreateStatic(&HandleApplyLocomotionSpeedBand),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("bp_path"), TEXT("Character Blueprint asset path"))
			.Required(TEXT("walk_speed"),  TEXT("number"), TEXT("Walk band speed (documented; BT picks within the cap)"))
			.Required(TEXT("run_speed"),   TEXT("number"), TEXT("Run band speed; becomes the MaxWalkSpeed cap unless max_walk_speed overrides"))
			.Required(TEXT("crouch_speed"),TEXT("number"), TEXT("Crouch band speed; written to MaxWalkSpeedCrouched"))
			.Optional(TEXT("jog_speed"),   TEXT("number"), TEXT("Jog band speed (documented; BT picks within the cap)"))
			.Optional(TEXT("max_walk_speed"),         TEXT("number"), TEXT("Explicit MaxWalkSpeed cap override (defaults to run_speed)"))
			.Optional(TEXT("max_acceleration"),       TEXT("number"), TEXT("MaxAcceleration (default 2048)"))
			.Optional(TEXT("braking_deceleration"),   TEXT("number"), TEXT("BrakingDecelerationWalking (default 2048)"))
			.Build());
}

// ---------------------------------------------------------------------------
// File-local helpers
// ---------------------------------------------------------------------------

namespace
{
	/** Build a sub-params object seeded with asset_path for delegation to existing handlers. */
	TSharedRef<FJsonObject> MakeSub(const FString& AssetPath)
	{
		TSharedRef<FJsonObject> Sub = MakeShared<FJsonObject>();
		Sub->SetStringField(TEXT("asset_path"), AssetPath);
		return Sub;
	}

	/**
	 * Shared component resolver: resolve a component on a Blueprint by alias, exact
	 * variable name, OR class — consistently for 5.1 / 5.2 / 5.3.
	 *
	 * Resolution order:
	 *   1. SCS-added node by exact (case-insensitive) variable name.
	 *   2. Native/inherited component on the CDO by exact name (e.g. "CharacterMesh0",
	 *      "CharMoveComp", or any author-named component).
	 *   3. Friendly alias (or empty name) → first component of the requested class on
	 *      the CDO. On a Character BP the inherited skeletal mesh is "CharacterMesh0"
	 *      (ACharacter::MeshComponentName) and the movement comp is "CharMoveComp"
	 *      (CharacterMovementComponentName) — so "Mesh"/"SkeletalMesh"/"CharacterMovement"
	 *      never match by name. We fall back to class match, which tolerates the engine's
	 *      private native component names without the caller knowing them.
	 *
	 * RequiredClass constrains every match; pass UActorComponent::StaticClass() for "any".
	 * Aliases is the set of friendly names that trigger the class fallback.
	 */
	UActorComponent* ResolveComponentOnBP(
		UBlueprint* BP,
		const FString& CompName,
		UClass* RequiredClass,
		const TArray<FString>& Aliases)
	{
		if (!BP || !RequiredClass) return nullptr;

		const bool bIsAlias = Aliases.ContainsByPredicate(
			[&CompName](const FString& A) { return A.Equals(CompName, ESearchCase::IgnoreCase); });

		// 1) SCS-added node by exact name (author-defined components).
		if (!CompName.IsEmpty() && BP->SimpleConstructionScript)
		{
			if (USCS_Node* Node = BP->SimpleConstructionScript->FindSCSNode(FName(*CompName)))
			{
				if (Node->ComponentTemplate && Node->ComponentTemplate->IsA(RequiredClass))
				{
					return Node->ComponentTemplate;
				}
			}
		}

		if (!BP->GeneratedClass) return nullptr;
		UObject* CDO = BP->GeneratedClass->GetDefaultObject(/*bCreateIfNeeded=*/false);
		AActor* CDOActor = Cast<AActor>(CDO);
		if (!CDOActor) return nullptr;

		TArray<UActorComponent*> Comps;
		CDOActor->GetComponents(Comps);

		// 2) Native/inherited component by exact name (e.g. "CharacterMesh0", custom name).
		if (!CompName.IsEmpty() && !bIsAlias)
		{
			for (UActorComponent* Comp : Comps)
			{
				if (!Comp || !Comp->IsA(RequiredClass)) continue;
				if (Comp->GetName().Equals(CompName, ESearchCase::IgnoreCase) ||
					Comp->GetFName() == FName(*CompName))
				{
					return Comp;
				}
			}
		}

		// 3) Alias OR empty name → first component of the required class on the CDO.
		//    Resolves "Mesh"/"SkeletalMesh" → CharacterMesh0 and the CMC lookup → CharMoveComp.
		if (bIsAlias || CompName.IsEmpty())
		{
			for (UActorComponent* Comp : Comps)
			{
				if (Comp && Comp->IsA(RequiredClass))
				{
					return Comp;
				}
			}
		}

		return nullptr;
	}

	/**
	 * Walk an AnimBP's graphs looking for a Motion Matching graph node by class name.
	 * Done by string match on the node class so MonolithBlueprint need not depend on
	 * the PoseSearchEditor module. Returns true if a UAnimGraphNode_MotionMatching*
	 * node is present.
	 */
	bool AnimBpHasMotionMatchingNode(UAnimBlueprint* ABP)
	{
		if (!ABP) return false;

		auto ScanGraphs = [](const TArray<TObjectPtr<UEdGraph>>& Graphs) -> bool
		{
			for (const TObjectPtr<UEdGraph>& Graph : Graphs)
			{
				if (!Graph) continue;
				for (UEdGraphNode* Node : Graph->Nodes)
				{
					if (!Node || !Node->GetClass()) continue;
					const FString ClassName = Node->GetClass()->GetName();
					if (ClassName.Contains(TEXT("MotionMatching")))
					{
						return true;
					}
				}
			}
			return false;
		};

		if (ScanGraphs(ABP->FunctionGraphs)) return true;
		if (ScanGraphs(ABP->UbergraphPages)) return true;
		return false;
	}

	/** Collect the BlueprintReadWrite-exposed variable names of a generated class (declared on that class only). */
	void CollectExposedVarNames(UClass* GeneratedClass, TSet<FString>& Out)
	{
		if (!GeneratedClass) return;
		for (TFieldIterator<FProperty> It(GeneratedClass, EFieldIteratorFlags::ExcludeSuper); It; ++It)
		{
			FProperty* Prop = *It;
			if (!Prop) continue;
			// BlueprintReadWrite => CPF_BlueprintVisible without CPF_BlueprintReadOnly.
			if (Prop->HasAnyPropertyFlags(CPF_BlueprintVisible) &&
				!Prop->HasAnyPropertyFlags(CPF_BlueprintReadOnly))
			{
				Out.Add(Prop->GetName());
			}
		}
	}
}

// ---------------------------------------------------------------------------
// 5.1 — set_anim_class
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleSetAnimClass(const TSharedPtr<FJsonObject>& Params)
{
	const FString BpPath = Params->GetStringField(TEXT("bp_path"));
	const FString CompName = Params->GetStringField(TEXT("component"));
	const FString AnimBpPath = Params->GetStringField(TEXT("anim_bp_path"));

	if (BpPath.IsEmpty())     return FMonolithActionResult::Error(TEXT("Missing required parameter: bp_path"));
	if (CompName.IsEmpty())   return FMonolithActionResult::Error(TEXT("Missing required parameter: component"));
	if (AnimBpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: anim_bp_path"));

	UBlueprint* BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(BpPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *BpPath));
	}

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AnimBpPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AnimBpPath));
	}
	if (!ABP->GeneratedClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Animation Blueprint '%s' has no GeneratedClass (compile it first)"), *AnimBpPath));
	}

	// Resolve by alias-or-name-or-class. "Mesh"/"SkeletalMesh" are friendly aliases that
	// fall back to the skeletal-mesh component on the CDO (ACharacter's is "CharacterMesh0",
	// NOT "Mesh"); an explicit exact name ("CharacterMesh0" or a custom name) still works.
	UActorComponent* MeshComp = ResolveComponentOnBP(
		BP, CompName, USkeletalMeshComponent::StaticClass(),
		{ TEXT("Mesh"), TEXT("SkeletalMesh") });
	USkeletalMeshComponent* SMC = Cast<USkeletalMeshComponent>(MeshComp);
	if (!SMC)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Skeletal mesh component '%s' not found on '%s' "
				 "(use 'Mesh'/'SkeletalMesh' alias, the exact name e.g. 'CharacterMesh0', or a custom name)"),
			*CompName, *BpPath));
	}

	// Warn (do not fail) if the AnimBP graph has no Motion Matching node.
	const bool bHasMMNode = AnimBpHasMotionMatchingNode(ABP);

	// Set the AnimClass UPROPERTY (TSubclassOf<UAnimInstance> AnimClass, SkeletalMeshComponent.h:372)
	// directly on the component template, then notify so it serialises. We use the public
	// SetAnimClass setter where the template is a live instance; for a template subobject
	// the direct field write + PostEditChange is the asset-time path mirrored by
	// set_component_property's setter discipline.
	//
	// PERSISTENCE: the mesh component is an INHERITED NATIVE component (ACharacter's
	// CharacterMesh0 has no SCS node, so no Inheritable Component Handler override exists).
	// The write lands on the CDO subobject directly. MarkBlueprintAsModified alone does NOT
	// re-serialise that CDO override — it silently reverts on the next reload/recompile.
	// The CDO override only persists if the Blueprint is structurally modified AND recompiled.
	BP->Modify();
	SMC->Modify();
	SMC->SetAnimInstanceClass(ABP->GeneratedClass);

	FProperty* AnimClassProp = USkeletalMeshComponent::StaticClass()->FindPropertyByName(TEXT("AnimClass"));
	if (AnimClassProp)
	{
		FPropertyChangedEvent ChangeEvent(AnimClassProp, EPropertyChangeType::ValueSet);
		SMC->PostEditChangeProperty(ChangeEvent);
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	BP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("bp_path"), BpPath);
	Root->SetStringField(TEXT("component"), CompName);
	Root->SetStringField(TEXT("anim_bp_path"), AnimBpPath);
	Root->SetStringField(TEXT("anim_class"), ABP->GeneratedClass->GetName());
	Root->SetBoolField(TEXT("motion_matching_node_found"), bHasMMNode);
	if (!bHasMMNode)
	{
		Root->SetStringField(TEXT("warning"),
			TEXT("AnimBP graph contains no Motion Matching node — AnimClass was set anyway."));
	}
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// 5.2 — apply_movement_preset
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleApplyMovementPreset(const TSharedPtr<FJsonObject>& Params)
{
	const FString BpPath = Params->GetStringField(TEXT("bp_path"));
	const FString Preset = Params->GetStringField(TEXT("preset"));

	if (BpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: bp_path"));
	if (Preset.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: preset"));

	UBlueprint* BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(BpPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *BpPath));
	}

	// Resolve the CharacterMovementComponent BY CLASS on the CDO — the native inherited
	// CMC is named "CharMoveComp" (ACharacter::CharacterMovementComponentName), NOT
	// "CharacterMovement", so a name lookup fails. We resolve the UClass by name (body-only,
	// no CMC header needed) then find the component instance, and pass its REAL name to
	// set_component_property.
	UClass* CmcClass = FindFirstObject<UClass>(TEXT("CharacterMovementComponent"), EFindFirstObjectOptions::NativeFirst);
	if (!CmcClass)
	{
		CmcClass = FindFirstObject<UClass>(TEXT("UCharacterMovementComponent"), EFindFirstObjectOptions::NativeFirst);
	}
	if (!CmcClass)
	{
		return FMonolithActionResult::Error(TEXT("apply_movement_preset: UCharacterMovementComponent class not found"));
	}
	// Empty name → resolver returns the first component of the class on the CDO.
	UActorComponent* CmcComp = ResolveComponentOnBP(BP, FString(), CmcClass, {});
	if (!CmcComp)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("apply_movement_preset: no CharacterMovementComponent found on '%s' (is the parent a Character?)"), *BpPath));
	}
	const FString CmcName = CmcComp->GetName();

	// Build the property tree for this preset, then write each via set_component_property
	// (honours the Details-panel write path + PostEditChange notifications).
	TArray<TPair<FString, FString>> Writes;
	if (Preset.Equals(TEXT("orient_to_movement"), ESearchCase::IgnoreCase))
	{
		Writes.Emplace(TEXT("bOrientRotationToMovement"), TEXT("true"));
		Writes.Emplace(TEXT("bUseControllerDesiredRotation"), TEXT("false"));
		Writes.Emplace(TEXT("RotationRate"), TEXT("(Pitch=0.0,Yaw=500.0,Roll=0.0)"));
	}
	else if (Preset.Equals(TEXT("strafe_controller_desired"), ESearchCase::IgnoreCase))
	{
		Writes.Emplace(TEXT("bOrientRotationToMovement"), TEXT("false"));
		Writes.Emplace(TEXT("bUseControllerDesiredRotation"), TEXT("true"));
		Writes.Emplace(TEXT("MaxAcceleration"), TEXT("2048.0"));
	}
	else
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown preset '%s'. Expected 'orient_to_movement' or 'strafe_controller_desired'."), *Preset));
	}

	TArray<TSharedPtr<FJsonValue>> Applied;
	for (const TPair<FString, FString>& Write : Writes)
	{
		TSharedRef<FJsonObject> Sub = MakeSub(BpPath);
		Sub->SetStringField(TEXT("component_name"), CmcName);
		Sub->SetStringField(TEXT("property_name"), Write.Key);
		Sub->SetStringField(TEXT("value"), Write.Value);

		FMonolithActionResult R = FMonolithBlueprintComponentActions::HandleSetComponentProperty(Sub);
		if (!R.bSuccess)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("apply_movement_preset: failed to set '%s' on %s — %s"),
				*Write.Key, *CmcName, *R.ErrorMessage));
		}
		TSharedPtr<FJsonObject> A = MakeShared<FJsonObject>();
		A->SetStringField(TEXT("property"), Write.Key);
		A->SetStringField(TEXT("value"), Write.Value);
		Applied.Add(MakeShared<FJsonValueObject>(A));
	}

	FBlueprintEditorUtils::MarkBlueprintAsModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("bp_path"), BpPath);
	Root->SetStringField(TEXT("preset"), Preset);
	Root->SetStringField(TEXT("component"), CmcName);
	Root->SetArrayField(TEXT("applied"), Applied);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// 5.3 — add_engine_component_typed
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleAddEngineComponentTyped(const TSharedPtr<FJsonObject>& Params)
{
	const FString BpPath = Params->GetStringField(TEXT("bp_path"));
	const FString CompType = Params->GetStringField(TEXT("component_type"));
	const FString CompName = Params->GetStringField(TEXT("component_name"));

	if (BpPath.IsEmpty())   return FMonolithActionResult::Error(TEXT("Missing required parameter: bp_path"));
	if (CompType.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: component_type"));
	if (CompName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: component_name"));

	// Resolve the class by friendly name — same NativeFirst probe the chooser fix uses.
	// Accept bare or U-prefixed name. NOTE: CharacterTrajectory is NOT special-cased —
	// no such component exists in UE 5.7 (Motion Matching trajectory is AnimBP-side).
	UClass* CompClass = FindFirstObject<UClass>(*CompType, EFindFirstObjectOptions::NativeFirst);
	if (!CompClass)
	{
		CompClass = FindFirstObject<UClass>(*(TEXT("U") + CompType), EFindFirstObjectOptions::NativeFirst);
	}
	if (!CompClass)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Component class not found: %s"), *CompType));
	}
	if (!CompClass->IsChildOf(UActorComponent::StaticClass()))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Class '%s' is not a UActorComponent subclass"), *CompType));
	}

	// Delegate to the shipped add_component handler (resolves the class itself, but we
	// validated above for a precise error message). Pass the canonical class name.
	TSharedRef<FJsonObject> Sub = MakeSub(BpPath);
	Sub->SetStringField(TEXT("component_class"), CompClass->GetName());
	Sub->SetStringField(TEXT("component_name"), CompName);

	return FMonolithBlueprintComponentActions::HandleAddComponent(Sub);
}

// ---------------------------------------------------------------------------
// 5.4 — scaffold_locomotion_input
// ---------------------------------------------------------------------------

namespace
{
	/** Map a friendly value_type string to EInputActionValueType. Defaults to Boolean. */
	EInputActionValueType ParseValueType(const FString& In)
	{
		if (In.Equals(TEXT("Axis1D"), ESearchCase::IgnoreCase) || In.Equals(TEXT("float"), ESearchCase::IgnoreCase))
			return EInputActionValueType::Axis1D;
		if (In.Equals(TEXT("Axis2D"), ESearchCase::IgnoreCase) || In.Equals(TEXT("Vector2D"), ESearchCase::IgnoreCase))
			return EInputActionValueType::Axis2D;
		if (In.Equals(TEXT("Axis3D"), ESearchCase::IgnoreCase) || In.Equals(TEXT("Vector"), ESearchCase::IgnoreCase))
			return EInputActionValueType::Axis3D;
		return EInputActionValueType::Boolean; // Digital
	}

	/** Create a UDataAsset-derived asset (IMC or IA) at a /Game path. Returns nullptr on collision/failure. */
	UObject* CreateInputAsset(UClass* AssetClass, const FString& PackagePath, FString& OutError)
	{
		int32 LastSlash = INDEX_NONE;
		if (!PackagePath.FindLastChar(TEXT('/'), LastSlash))
		{
			OutError = FString::Printf(TEXT("Invalid asset path (no '/'): %s"), *PackagePath);
			return nullptr;
		}
		const FString AssetName = PackagePath.Mid(LastSlash + 1);
		if (AssetName.IsEmpty())
		{
			OutError = FString::Printf(TEXT("Asset path must not end with '/': %s"), *PackagePath);
			return nullptr;
		}

		if (FMonolithAssetUtils::AssetExists(PackagePath))
		{
			OutError = FString::Printf(TEXT("Asset already exists: %s"), *PackagePath);
			return nullptr;
		}

		UPackage* Pkg = CreatePackage(*PackagePath);
		if (!Pkg)
		{
			OutError = FString::Printf(TEXT("Failed to create package: %s"), *PackagePath);
			return nullptr;
		}

		UObject* NewAsset = NewObject<UObject>(Pkg, AssetClass, FName(*AssetName), RF_Public | RF_Standalone);
		if (!NewAsset)
		{
			OutError = FString::Printf(TEXT("NewObject failed for %s at %s"), *AssetClass->GetName(), *PackagePath);
			return nullptr;
		}
		Pkg->MarkPackageDirty();
		FAssetRegistryModule::AssetCreated(NewAsset);
		return NewAsset;
	}
}

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleScaffoldLocomotionInput(const TSharedPtr<FJsonObject>& Params)
{
	const FString BpPath = Params->GetStringField(TEXT("bp_path"));
	const FString ImcPath = Params->GetStringField(TEXT("imc_path"));

	if (BpPath.IsEmpty())  return FMonolithActionResult::Error(TEXT("Missing required parameter: bp_path"));
	if (ImcPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: imc_path"));

	const TArray<TSharedPtr<FJsonValue>>* ActionsArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("actions"), ActionsArr) || !ActionsArr || ActionsArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("'actions' is required and must be a non-empty array of {name, value_type}"));
	}

	UBlueprint* BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(BpPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *BpPath));
	}

	// --- Create the InputMappingContext asset ---
	FString CreateError;
	UObject* ImcObj = CreateInputAsset(UInputMappingContext::StaticClass(), ImcPath, CreateError);
	if (!ImcObj)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("scaffold_locomotion_input: %s"), *CreateError));
	}

	// IA assets get created next to the IMC, under <imc_dir>/IA_<Name>.
	int32 ImcSlash = INDEX_NONE;
	ImcPath.FindLastChar(TEXT('/'), ImcSlash);
	const FString ImcDir = (ImcSlash != INDEX_NONE) ? ImcPath.Left(ImcSlash) : TEXT("/Game");

	TArray<TSharedPtr<FJsonValue>> CreatedActions;
	TArray<FString> ActionNames;

	for (const TSharedPtr<FJsonValue>& Entry : *ActionsArr)
	{
		const TSharedPtr<FJsonObject> Obj = Entry.IsValid() ? Entry->AsObject() : nullptr;
		if (!Obj.IsValid())
		{
			return FMonolithActionResult::Error(TEXT("Each 'actions' entry must be an object {name, value_type}"));
		}
		FString ActName;
		Obj->TryGetStringField(TEXT("name"), ActName);
		if (ActName.IsEmpty())
		{
			return FMonolithActionResult::Error(TEXT("Each 'actions' entry requires a non-empty 'name'"));
		}
		FString ValueType;
		Obj->TryGetStringField(TEXT("value_type"), ValueType);

		const FString IaPath = FString::Printf(TEXT("%s/IA_%s"), *ImcDir, *ActName);
		FString IaError;
		UObject* IaObj = CreateInputAsset(UInputAction::StaticClass(), IaPath, IaError);
		if (!IaObj)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("scaffold_locomotion_input: failed creating InputAction '%s' — %s"), *ActName, *IaError));
		}
		if (UInputAction* IA = Cast<UInputAction>(IaObj))
		{
			IA->ValueType = ParseValueType(ValueType);
			IA->MarkPackageDirty();
		}

		ActionNames.Add(ActName);
		TSharedPtr<FJsonObject> AOut = MakeShared<FJsonObject>();
		AOut->SetStringField(TEXT("name"), ActName);
		AOut->SetStringField(TEXT("ia_path"), IaPath);
		AOut->SetStringField(TEXT("value_type"), ValueType.IsEmpty() ? TEXT("Digital") : ValueType);
		CreatedActions.Add(MakeShared<FJsonValueObject>(AOut));
	}

	// --- Event-graph wiring: a BeginPlay/Tick-anchored AddMovementInput scaffold. ---
	// We drop one AddMovementInput CallFunction node per action so the locomotion
	// movement-input plumbing exists; binding the EnhancedInput action events is left
	// to the AnimBP/character author (the IA assets are now in place to bind against).
	int32 NodesAdded = 0;
	for (const FString& ActName : ActionNames)
	{
		TSharedRef<FJsonObject> NodeSub = MakeSub(BpPath);
		NodeSub->SetStringField(TEXT("node_type"), TEXT("call_function"));
		NodeSub->SetStringField(TEXT("function_name"), TEXT("AddMovementInput"));
		NodeSub->SetStringField(TEXT("target_class"), TEXT("Pawn"));
		FMonolithActionResult NR = FMonolithBlueprintNodeActions::HandleAddNode(NodeSub);
		if (NR.bSuccess)
		{
			NodesAdded++;
		}
	}

	FBlueprintEditorUtils::MarkBlueprintAsModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("bp_path"), BpPath);
	Root->SetStringField(TEXT("imc_path"), ImcPath);
	Root->SetArrayField(TEXT("actions"), CreatedActions);
	Root->SetNumberField(TEXT("add_movement_input_nodes"), NodesAdded);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// 5.5 — validate_animbp_variable_contract
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleValidateAnimBpVariableContract(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath = Params->GetStringField(TEXT("abp_path"));
	const FString BpPath = Params->GetStringField(TEXT("bp_path"));

	if (AbpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: abp_path"));
	if (BpPath.IsEmpty())  return FMonolithActionResult::Error(TEXT("Missing required parameter: bp_path"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP || !ABP->GeneratedClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Animation Blueprint not found or not compiled: %s"), *AbpPath));
	}

	UBlueprint* BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(BpPath);
	if (!BP || !BP->GeneratedClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Blueprint not found or not compiled: %s"), *BpPath));
	}

	TSet<FString> AbpVars;
	CollectExposedVarNames(ABP->GeneratedClass, AbpVars);

	TSet<FString> BpVars;
	CollectExposedVarNames(BP->GeneratedClass, BpVars);

	// missing: ABP exposes/reads a variable the BP does not publish.
	// extra:   BP publishes a variable the ABP does not consume.
	TArray<TSharedPtr<FJsonValue>> Missing;
	for (const FString& V : AbpVars)
	{
		if (!BpVars.Contains(V)) Missing.Add(MakeShared<FJsonValueString>(V));
	}
	TArray<TSharedPtr<FJsonValue>> Extra;
	for (const FString& V : BpVars)
	{
		if (!AbpVars.Contains(V)) Extra.Add(MakeShared<FJsonValueString>(V));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("bp_path"), BpPath);
	Root->SetNumberField(TEXT("abp_exposed_var_count"), AbpVars.Num());
	Root->SetNumberField(TEXT("bp_published_var_count"), BpVars.Num());
	Root->SetArrayField(TEXT("missing"), Missing);
	Root->SetArrayField(TEXT("extra"), Extra);
	Root->SetBoolField(TEXT("contract_satisfied"), Missing.Num() == 0);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// 5.6 — scaffold_motion_matching_character (COMPOSITE — composes 5.1 + 5.2)
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleScaffoldMotionMatchingCharacter(const TSharedPtr<FJsonObject>& Params)
{
	const FString BpPath = Params->GetStringField(TEXT("bp_path"));
	const FString AnimBpPath = Params->GetStringField(TEXT("anim_bp_path"));

	if (BpPath.IsEmpty())     return FMonolithActionResult::Error(TEXT("Missing required parameter: bp_path"));
	if (AnimBpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: anim_bp_path"));

	FString ParentClass = Params->GetStringField(TEXT("parent_class"));
	if (ParentClass.IsEmpty()) ParentClass = TEXT("Character");

	FString MovementPreset = Params->GetStringField(TEXT("movement_preset"));
	if (MovementPreset.IsEmpty()) MovementPreset = TEXT("orient_to_movement");

	FString Mesh;
	Params->TryGetStringField(TEXT("mesh"), Mesh);

	TArray<TSharedPtr<FJsonValue>> Steps;
	auto NoteStep = [&Steps](const FString& Name, bool bOk, const FString& Detail)
	{
		TSharedPtr<FJsonObject> S = MakeShared<FJsonObject>();
		S->SetStringField(TEXT("step"), Name);
		S->SetBoolField(TEXT("success"), bOk);
		if (!Detail.IsEmpty()) S->SetStringField(TEXT("detail"), Detail);
		Steps.Add(MakeShared<FJsonValueObject>(S));
	};

	// --- Create or reparent the character Blueprint ---
	UBlueprint* BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(BpPath);
	if (!BP)
	{
		// Create new BP at bp_path with the chosen parent (default Character — gives Mesh + CMC).
		TSharedRef<FJsonObject> CreateSub = MakeShared<FJsonObject>();
		CreateSub->SetStringField(TEXT("save_path"), BpPath);
		CreateSub->SetStringField(TEXT("parent_class"), ParentClass);
		FMonolithActionResult CR = FMonolithBlueprintCompileActions::HandleCreateBlueprint(CreateSub);
		if (!CR.bSuccess)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("scaffold_motion_matching_character: create_blueprint failed — %s"), *CR.ErrorMessage));
		}
		NoteStep(TEXT("create_blueprint"), true, ParentClass);
		BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(BpPath);
		if (!BP)
		{
			return FMonolithActionResult::Error(TEXT("scaffold_motion_matching_character: BP created but failed to reload"));
		}
	}
	else
	{
		// Existing BP — reparent if the requested parent differs.
		const FString CurrentParent = BP->ParentClass ? BP->ParentClass->GetName() : TEXT("None");
		if (!CurrentParent.Equals(ParentClass, ESearchCase::IgnoreCase) &&
			!CurrentParent.Equals(FString(TEXT("A")) + ParentClass, ESearchCase::IgnoreCase))
		{
			TSharedRef<FJsonObject> ReparentSub = MakeSub(BpPath);
			ReparentSub->SetStringField(TEXT("new_parent_class"), ParentClass);
			FMonolithActionResult RR = FMonolithBlueprintGraphActions::HandleReparentBlueprint(ReparentSub);
			NoteStep(TEXT("reparent_blueprint"), RR.bSuccess, RR.bSuccess ? ParentClass : RR.ErrorMessage);
		}
		else
		{
			NoteStep(TEXT("reparent_blueprint"), true, TEXT("already correct parent — skipped"));
		}
	}

	// --- Optional: set the skeletal mesh — resolve the mesh component BY CLASS, then write
	//     the mesh asset DIRECTLY via SetSkeletalMeshAsset + the full persistence handshake.
	//     The mesh component on a Character is an INHERITED NATIVE component (CharacterMesh0,
	//     no SCS node), so the write lands on the CDO subobject. As with set_anim_class, that
	//     override only persists if the Blueprint is structurally modified AND recompiled —
	//     MarkBlueprintAsModified alone reverts it on reload. ---
	if (!Mesh.IsEmpty())
	{
		UActorComponent* MeshComp = ResolveComponentOnBP(
			BP, TEXT("Mesh"), USkeletalMeshComponent::StaticClass(),
			{ TEXT("Mesh"), TEXT("SkeletalMesh") });
		USkeletalMeshComponent* MeshSMC = Cast<USkeletalMeshComponent>(MeshComp);
		USkeletalMesh* MeshAsset = FMonolithAssetUtils::LoadAssetByPath<USkeletalMesh>(Mesh);
		if (!MeshSMC)
		{
			NoteStep(TEXT("set_mesh"), false, TEXT("no skeletal mesh component found on BP"));
		}
		else if (!MeshAsset)
		{
			NoteStep(TEXT("set_mesh"), false, FString::Printf(TEXT("skeletal mesh asset not found: %s"), *Mesh));
		}
		else
		{
			BP->Modify();
			MeshSMC->Modify();
			MeshSMC->SetSkeletalMeshAsset(MeshAsset);

			// The persisted UPROPERTY is SkinnedAsset (SkeletalMeshAsset is Transient); notify
			// the serialised property so the override is recorded against the CDO subobject.
			if (FProperty* MeshProp = USkeletalMeshComponent::StaticClass()->FindPropertyByName(TEXT("SkinnedAsset")))
			{
				FPropertyChangedEvent ChangeEvent(MeshProp, EPropertyChangeType::ValueSet);
				MeshSMC->PostEditChangeProperty(ChangeEvent);
			}

			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			FKismetEditorUtilities::CompileBlueprint(BP);
			BP->MarkPackageDirty();
			NoteStep(TEXT("set_mesh"), true, Mesh);
		}
	}

	// --- Compose 5.1: set_anim_class on the 'Mesh' component ---
	{
		TSharedRef<FJsonObject> AnimSub = MakeShared<FJsonObject>();
		AnimSub->SetStringField(TEXT("bp_path"), BpPath);
		AnimSub->SetStringField(TEXT("component"), TEXT("Mesh"));
		AnimSub->SetStringField(TEXT("anim_bp_path"), AnimBpPath);
		FMonolithActionResult AR = HandleSetAnimClass(AnimSub);
		if (!AR.bSuccess)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("scaffold_motion_matching_character: set_anim_class failed — %s"), *AR.ErrorMessage));
		}
		NoteStep(TEXT("set_anim_class"), true, AnimBpPath);
	}

	// --- Compose 5.2: apply_movement_preset ---
	{
		TSharedRef<FJsonObject> PresetSub = MakeShared<FJsonObject>();
		PresetSub->SetStringField(TEXT("bp_path"), BpPath);
		PresetSub->SetStringField(TEXT("preset"), MovementPreset);
		FMonolithActionResult PR = HandleApplyMovementPreset(PresetSub);
		if (!PR.bSuccess)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("scaffold_motion_matching_character: apply_movement_preset failed — %s"), *PR.ErrorMessage));
		}
		NoteStep(TEXT("apply_movement_preset"), true, MovementPreset);
	}

	// --- Compile ---
	{
		TSharedRef<FJsonObject> CompileSub = MakeSub(BpPath);
		FMonolithActionResult CR = FMonolithBlueprintCompileActions::HandleCompileBlueprint(CompileSub);
		NoteStep(TEXT("compile"), CR.bSuccess, CR.bSuccess ? TEXT("") : CR.ErrorMessage);
	}

	FBlueprintEditorUtils::MarkBlueprintAsModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("bp_path"), BpPath);
	Root->SetStringField(TEXT("parent_class"), ParentClass);
	Root->SetStringField(TEXT("anim_bp_path"), AnimBpPath);
	Root->SetStringField(TEXT("movement_preset"), MovementPreset);
	if (!Mesh.IsEmpty()) Root->SetStringField(TEXT("mesh"), Mesh);
	Root->SetArrayField(TEXT("steps"), Steps);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// 5.7 — get_inherited_component_override (READ-ONLY)
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleGetInheritedComponentOverride(const TSharedPtr<FJsonObject>& Params)
{
	const FString BpPath = Params->GetStringField(TEXT("bp_path"));
	const FString CompName = Params->GetStringField(TEXT("component"));
	FString SingleProp;
	Params->TryGetStringField(TEXT("property_name"), SingleProp);

	if (BpPath.IsEmpty())   return FMonolithActionResult::Error(TEXT("Missing required parameter: bp_path"));
	if (CompName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: component"));

	UBlueprint* BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(BpPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *BpPath));
	}

	// Resolve the EFFECTIVE component template. ResolveComponentOnBP returns the SCS
	// template when the component is author-declared on this BP, otherwise the component
	// on the CDO (which reflects native defaults + any ICH override + inherited values).
	UActorComponent* Comp = ResolveComponentOnBP(
		BP, CompName, UActorComponent::StaticClass(),
		{ TEXT("Mesh"), TEXT("SkeletalMesh") });
	if (!Comp)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Component '%s' not found on '%s'"), *CompName, *BpPath));
	}

	// Classify the override source.
	//   scs        — declared as an SCS node on THIS Blueprint.
	//   ich        — SCS-inherited from a parent BP with an Inheritable Component Handler override.
	//   cdo_native — inherited native component (no SCS node anywhere); value read off the CDO.
	FString SourceClass = TEXT("cdo_native");
	{
		bool bIsThisBpScs = false;
		if (BP->SimpleConstructionScript)
		{
			for (USCS_Node* Node : BP->SimpleConstructionScript->GetAllNodes())
			{
				if (Node && (Node->GetVariableName() == Comp->GetFName() ||
					(Node->ComponentTemplate && Node->ComponentTemplate->GetName().Equals(Comp->GetName(), ESearchCase::IgnoreCase))))
				{
					bIsThisBpScs = true;
					break;
				}
			}
		}

		if (bIsThisBpScs)
		{
			SourceClass = TEXT("scs");
		}
		else if (UBlueprintGeneratedClass* BPGC = Cast<UBlueprintGeneratedClass>(BP->GeneratedClass))
		{
			// An SCS-inherited component (declared on a parent BP) carries its override on
			// this BP's Inheritable Component Handler. If an ICH exists and holds an override
			// template matching this component's name, classify as 'ich'; otherwise the value
			// is the plain inherited/native default read off the CDO.
			if (UInheritableComponentHandler* ICH = BPGC->GetInheritableComponentHandler(/*bCreateIfNecessary=*/false))
			{
				for (auto RecordIt = ICH->CreateRecordIterator(); RecordIt; ++RecordIt)
				{
					if (RecordIt->ComponentTemplate &&
						RecordIt->ComponentTemplate->GetName().Equals(Comp->GetName(), ESearchCase::IgnoreCase))
					{
						SourceClass = TEXT("ich");
						break;
					}
				}
			}
		}
	}

	// Build the property list to read.
	TArray<FString> PropsToRead;
	if (!SingleProp.IsEmpty())
	{
		PropsToRead.Add(SingleProp);
	}
	else
	{
		PropsToRead.Add(TEXT("AnimClass"));
		PropsToRead.Add(TEXT("SkeletalMesh"));
		PropsToRead.Add(TEXT("AnimationMode"));
	}

	TSharedPtr<FJsonObject> PropsObj = MakeShared<FJsonObject>();
	for (const FString& PName : PropsToRead)
	{
		FProperty* Prop = Comp->GetClass()->FindPropertyByName(FName(*PName));
		if (!Prop)
		{
			for (TFieldIterator<FProperty> It(Comp->GetClass()); It; ++It)
			{
				if (It->GetName().Equals(PName, ESearchCase::IgnoreCase)) { Prop = *It; break; }
			}
		}
		if (!Prop)
		{
			// Property not present on this component class — report as not-applicable.
			PropsObj->SetStringField(PName, TEXT("<property not found on component>"));
			continue;
		}
		const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Comp);
		FString Exported;
		Prop->ExportText_Direct(Exported, ValuePtr, ValuePtr, const_cast<UActorComponent*>(Comp), PPF_None);
		PropsObj->SetStringField(Prop->GetName(), Exported);
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("bp_path"), BpPath);
	Root->SetStringField(TEXT("component"), CompName);
	Root->SetStringField(TEXT("resolved_component"), Comp->GetName());
	Root->SetStringField(TEXT("component_class"), Comp->GetClass()->GetName());
	Root->SetStringField(TEXT("source"), SourceClass);
	Root->SetObjectField(TEXT("properties"), PropsObj);
	return FMonolithActionResult::Success(Root);
}

// ===========================================================================
// Pack A — thread-safe AnimBP event-graph authoring
// ===========================================================================

namespace
{
	/** Name the engine gives the BlueprintThreadSafeUpdateAnimation override function graph. */
	static const TCHAR* kThreadSafeUpdateFuncName = TEXT("BlueprintThreadSafeUpdateAnimation");

	/** Return the override function graph for the thread-safe update, or nullptr if absent. */
	UEdGraph* FindThreadSafeUpdateGraph(UAnimBlueprint* ABP)
	{
		if (!ABP) return nullptr;
		for (const TObjectPtr<UEdGraph>& Graph : ABP->FunctionGraphs)
		{
			if (Graph && Graph->GetName() == kThreadSafeUpdateFuncName)
			{
				return Graph.Get();
			}
		}
		return nullptr;
	}

	/**
	 * Ensure the thread-safe update override exists on the AnimBP. Idempotent: returns
	 * true if the override already exists OR was created successfully. OutCreated reports
	 * whether this call authored it. Delegates to override_parent_function (the same
	 * GetOverrideFunctionClass + AddFunctionGraph path used elsewhere).
	 */
	bool EnsureThreadSafeUpdate(const FString& AbpPath, UAnimBlueprint* ABP, bool& bOutCreated, FString& OutError)
	{
		bOutCreated = false;
		if (FindThreadSafeUpdateGraph(ABP))
		{
			return true; // already present
		}

		TSharedRef<FJsonObject> Sub = MakeShared<FJsonObject>();
		Sub->SetStringField(TEXT("asset_path"), AbpPath);
		Sub->SetStringField(TEXT("parent_function_name"), kThreadSafeUpdateFuncName);
		FMonolithActionResult R = FMonolithBlueprintGraphActions::HandleOverrideParentFunction(Sub);
		if (!R.bSuccess)
		{
			OutError = R.ErrorMessage;
			return false;
		}
		bOutCreated = true;
		return true;
	}

	/**
	 * Pull a temp_id -> node_id map out of an add_nodes_bulk result. That handler returns
	 * { "nodes_created": [ { temp_id, node_id, ... }, ... ], "count": N } in Result.
	 */
	void ExtractBulkNodeIds(const FMonolithActionResult& BulkResult, TMap<FString, FString>& OutMap)
	{
		if (!BulkResult.bSuccess || !BulkResult.Result.IsValid()) return;
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		if (!BulkResult.Result->TryGetArrayField(TEXT("nodes_created"), Arr) || !Arr) return;
		for (const TSharedPtr<FJsonValue>& Entry : *Arr)
		{
			const TSharedPtr<FJsonObject> Obj = Entry.IsValid() ? Entry->AsObject() : nullptr;
			if (!Obj.IsValid()) continue;
			FString TempId, NodeId;
			Obj->TryGetStringField(TEXT("temp_id"), TempId);
			Obj->TryGetStringField(TEXT("node_id"), NodeId);
			if (!TempId.IsEmpty() && !NodeId.IsEmpty())
			{
				OutMap.Add(TempId, NodeId);
			}
		}
	}
}

// ---------------------------------------------------------------------------
// A.1 — scaffold_threadsafe_update
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleScaffoldThreadSafeUpdate(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath = Params->GetStringField(TEXT("abp_path"));
	if (AbpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: abp_path"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AbpPath));
	}

	bool bCreated = false;
	FString OverrideError;
	if (!EnsureThreadSafeUpdate(AbpPath, ABP, bCreated, OverrideError))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("scaffold_threadsafe_update: failed to override %s — %s"),
			kThreadSafeUpdateFuncName, *OverrideError));
	}

	// Locate the entry node of the override graph so callers can chain logic off its exec.
	UEdGraph* Graph = FindThreadSafeUpdateGraph(ABP);
	FString EntryNodeId;
	if (Graph)
	{
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (Node && Node->GetClass() && Node->GetClass()->GetName().Contains(TEXT("FunctionEntry")))
			{
				EntryNodeId = Node->GetName();
				break;
			}
		}
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("graph_name"), kThreadSafeUpdateFuncName);
	Root->SetStringField(TEXT("entry_node_id"), EntryNodeId);
	Root->SetBoolField(TEXT("created"), bCreated);
	Root->SetBoolField(TEXT("already_existed"), !bCreated);
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// A.2 — add_pawn_owner_access
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleAddPawnOwnerAccess(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath = Params->GetStringField(TEXT("abp_path"));
	if (AbpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: abp_path"));

	FString CastClass = Params->GetStringField(TEXT("cast_class"));
	if (CastClass.IsEmpty()) CastClass = TEXT("Character");

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AbpPath));
	}

	// Ensure the thread-safe update exists first (compose A.1).
	bool bCreated = false;
	FString EnsureError;
	if (!EnsureThreadSafeUpdate(AbpPath, ABP, bCreated, EnsureError))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("add_pawn_owner_access: thread-safe update unavailable — %s"), *EnsureError));
	}

	// Author TryGetPawnOwner + Cast-To-<CastClass> in the override graph via add_nodes_bulk.
	// TryGetPawnOwner is a UAnimInstance member (self-context), worker-thread safe.
	TSharedRef<FJsonObject> NodesSub = MakeShared<FJsonObject>();
	NodesSub->SetStringField(TEXT("asset_path"), AbpPath);
	NodesSub->SetStringField(TEXT("graph_name"), kThreadSafeUpdateFuncName);
	{
		TArray<TSharedPtr<FJsonValue>> Nodes;

		// TryGetPawnOwner — CallFunction on the AnimInstance (self).
		TSharedPtr<FJsonObject> PawnNode = MakeShared<FJsonObject>();
		PawnNode->SetStringField(TEXT("temp_id"), TEXT("get_pawn"));
		PawnNode->SetStringField(TEXT("node_type"), TEXT("call_function"));
		PawnNode->SetStringField(TEXT("function_name"), TEXT("TryGetPawnOwner"));
		PawnNode->SetStringField(TEXT("target_class"), TEXT("AnimInstance"));
		Nodes.Add(MakeShared<FJsonValueObject>(PawnNode));

		// DynamicCast to the requested class (DynamicCast node takes 'cast_class').
		TSharedPtr<FJsonObject> CastNode = MakeShared<FJsonObject>();
		CastNode->SetStringField(TEXT("temp_id"), TEXT("cast_pawn"));
		CastNode->SetStringField(TEXT("node_type"), TEXT("cast"));
		CastNode->SetStringField(TEXT("cast_class"), CastClass);
		Nodes.Add(MakeShared<FJsonValueObject>(CastNode));

		NodesSub->SetArrayField(TEXT("nodes"), Nodes);
		NodesSub->SetBoolField(TEXT("auto_layout"), true);
	}

	FMonolithActionResult NR = FMonolithBlueprintNodeActions::HandleAddNodesBulk(NodesSub);
	if (!NR.bSuccess)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("add_pawn_owner_access: add_nodes_bulk failed — %s"), *NR.ErrorMessage));
	}

	// Resolve the real node ids from the temp_id -> node_id map add_nodes_bulk returns.
	TMap<FString, FString> IdMap;
	ExtractBulkNodeIds(NR, IdMap);
	const FString GetPawnNodeId = IdMap.FindRef(TEXT("get_pawn"));
	const FString CastNodeId    = IdMap.FindRef(TEXT("cast_pawn"));

	// Wire TryGetPawnOwner return -> cast object input via connect_pins_bulk. Pin names are
	// the engine defaults (CallFunction return = "ReturnValue"; DynamicCast input = "Object").
	if (!GetPawnNodeId.IsEmpty() && !CastNodeId.IsEmpty())
	{
		TSharedRef<FJsonObject> ConnSub = MakeShared<FJsonObject>();
		ConnSub->SetStringField(TEXT("asset_path"), AbpPath);
		ConnSub->SetStringField(TEXT("graph_name"), kThreadSafeUpdateFuncName);
		TArray<TSharedPtr<FJsonValue>> Conns;
		TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
		C->SetStringField(TEXT("source_node"), GetPawnNodeId);
		C->SetStringField(TEXT("source_pin"), TEXT("ReturnValue"));
		C->SetStringField(TEXT("target_node"), CastNodeId);
		C->SetStringField(TEXT("target_pin"), TEXT("Object"));
		Conns.Add(MakeShared<FJsonValueObject>(C));
		ConnSub->SetArrayField(TEXT("connections"), Conns);
		FMonolithBlueprintNodeActions::HandleConnectPinsBulk(ConnSub); // best-effort wire
	}

	FBlueprintEditorUtils::MarkBlueprintAsModified(ABP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("graph_name"), kThreadSafeUpdateFuncName);
	Root->SetStringField(TEXT("cast_class"), CastClass);
	Root->SetStringField(TEXT("get_pawn_node_id"), GetPawnNodeId);
	Root->SetStringField(TEXT("cast_node_id"), CastNodeId);
	// The cast result pin (the As<CastClass> output) is what downstream nodes read pawn/CMC from.
	Root->SetStringField(TEXT("cast_result_pin"), FString::Printf(TEXT("As%s"), *CastClass));
	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// A.3 — scaffold_locomotion_anim_values (COMPOSITE)
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleScaffoldLocomotionAnimValues(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath = Params->GetStringField(TEXT("abp_path"));
	if (AbpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: abp_path"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AbpPath));
	}

	// Name overrides (default to the §4.1 contract names).
	auto VarName = [&Params](const TCHAR* Key, const TCHAR* Default) -> FString
	{
		FString V = Params->GetStringField(Key);
		return V.IsEmpty() ? FString(Default) : V;
	};
	const FString VelocityVar     = VarName(TEXT("velocity_var"),     TEXT("Velocity"));
	const FString GroundSpeedVar  = VarName(TEXT("ground_speed_var"), TEXT("GroundSpeed"));
	const FString AccelerationVar  = VarName(TEXT("acceleration_var"), TEXT("Acceleration"));
	const FString IsMovingVar     = VarName(TEXT("is_moving_var"),    TEXT("bIsMoving"));
	const FString IsCrouchedVar   = VarName(TEXT("is_crouched_var"),  TEXT("bIsCrouched"));

	// Target graph: default to the thread-safe update; allow a named thread-safe FUNCTION graph.
	const FString TargetGraphName = VarName(TEXT("target_graph"), kThreadSafeUpdateFuncName);

	// Property Access paths for the pawn-state SOURCES. velocity/acceleration default to the
	// Game Animation Sample 'CharacterProperties' member-struct layout; crouch has no default
	// (the sample's crouch source is an enum, not a bool) and is skipped when omitted.
	auto ParsePath = [&Params](const TCHAR* Key, const TArray<FString>& Default) -> TArray<FString>
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		if (Params->TryGetArrayField(Key, Arr) && Arr && Arr->Num() > 0)
		{
			TArray<FString> Out;
			for (const TSharedPtr<FJsonValue>& E : *Arr)
			{
				FString S;
				if (E.IsValid() && E->TryGetString(S) && !S.IsEmpty()) Out.Add(S);
			}
			if (Out.Num() > 0) return Out;
		}
		return Default;
	};
	const TArray<FString> VelocityPath     = ParsePath(TEXT("velocity_path"),     { TEXT("CharacterProperties"), TEXT("Velocity") });
	const TArray<FString> AccelerationPath  = ParsePath(TEXT("acceleration_path"), { TEXT("CharacterProperties"), TEXT("InputAcceleration") });
	const TArray<FString> CrouchPath        = ParsePath(TEXT("crouch_path"),       {});  // no default — skip when empty
	const bool bWireCrouch = CrouchPath.Num() > 0;

	TArray<TSharedPtr<FJsonValue>> Steps;
	auto NoteStep = [&Steps](const FString& Name, bool bOk, const FString& Detail)
	{
		TSharedPtr<FJsonObject> S = MakeShared<FJsonObject>();
		S->SetStringField(TEXT("step"), Name);
		S->SetBoolField(TEXT("success"), bOk);
		if (!Detail.IsEmpty()) S->SetStringField(TEXT("detail"), Detail);
		Steps.Add(MakeShared<FJsonValueObject>(S));
	};

	// 1) Ensure the TARGET thread-safe graph exists.
	//    - Default target (BlueprintThreadSafeUpdateAnimation): author the override if absent.
	//    - Named function target (e.g. UpdateEssentialValues): it must already exist — we do NOT
	//      synthesise an arbitrary function here (use add_function / scaffold_threadsafe_update or
	//      author it first). We only verify presence so the writes land in a real graph.
	//    No pawn/cast chain is authored — the pawn-state SOURCES are Property Access reads (Step 3b),
	//    which is what makes the result thread-safe.
	const bool bTargetIsThreadSafeUpdate = TargetGraphName.Equals(kThreadSafeUpdateFuncName, ESearchCase::IgnoreCase);
	if (bTargetIsThreadSafeUpdate)
	{
		bool bCreated = false; FString Err;
		if (!EnsureThreadSafeUpdate(AbpPath, ABP, bCreated, Err))
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("scaffold_locomotion_anim_values: thread-safe update unavailable — %s"), *Err));
		}
		NoteStep(TEXT("scaffold_threadsafe_update"), true, bCreated ? TEXT("created") : TEXT("already existed"));
	}
	else
	{
		if (!MonolithBlueprintInternal::FindGraphByName(ABP, TargetGraphName))
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("scaffold_locomotion_anim_values: target_graph '%s' not found on the AnimBP. Create/override it first "
				     "(it must be a thread-safe function graph)."), *TargetGraphName));
		}
		NoteStep(TEXT("verify_target_graph"), true, TargetGraphName);
	}

	// 2) Create the locomotion anim variables (idempotent — add_variable warns/errors on
	//    a duplicate, which we tolerate so re-running the composite is safe).
	struct FVarSpec { FString Name; const TCHAR* Type; };
	const TArray<FVarSpec> Vars = {
		{ VelocityVar,    TEXT("struct:Vector") },
		{ GroundSpeedVar, TEXT("float") },
		{ AccelerationVar,TEXT("struct:Vector") },
		{ IsMovingVar,    TEXT("bool") },
		{ IsCrouchedVar,  TEXT("bool") },
	};
	int32 VarsCreated = 0;
	for (const FVarSpec& V : Vars)
	{
		TSharedRef<FJsonObject> VarSub = MakeShared<FJsonObject>();
		VarSub->SetStringField(TEXT("asset_path"), AbpPath);
		VarSub->SetStringField(TEXT("name"), V.Name);
		VarSub->SetStringField(TEXT("type"), V.Type);
		VarSub->SetStringField(TEXT("category"), TEXT("Locomotion"));
		VarSub->SetBoolField(TEXT("instance_editable"), false);
		FMonolithActionResult VR = FMonolithBlueprintVariableActions::HandleAddVariable(VarSub);
		if (VR.bSuccess) { ++VarsCreated; }
		NoteStep(FString::Printf(TEXT("add_variable:%s"), *V.Name), VR.bSuccess,
			VR.bSuccess ? FString(V.Type) : VR.ErrorMessage);
	}

	// 3) Author a FULLY WIRED node graph inside the target thread-safe graph.
	//
	//    Topology (all inside TargetGraphName):
	//      FunctionEntry.then -> set_velocity -> set_groundspeed -> set_accel -> [set_iscrouched ->] set_ismoving (exec)
	//      pa_velocity.Value -> set_velocity.<Velocity> AND -> vsize_xy.A
	//      vsize_xy.ReturnValue -> set_groundspeed.<GroundSpeed> AND -> speed_gt.A
	//      pa_accel.Value -> set_accel.<Acceleration> AND -> accel_nz.A
	//      [pa_crouch.Value -> set_iscrouched.<bIsCrouched>]
	//      speed_gt.ReturnValue -> moving_and.A ; accel_nz.ReturnValue -> not_accel.A ; not_accel.ReturnValue -> moving_and.B
	//      moving_and.ReturnValue -> set_ismoving.<bIsMoving>
	//
	//    The pawn-state SOURCES (Velocity / Acceleration / crouch) are GENUINE thread-safe
	//    Property Access reads (add_property_access_node — real UK2Node_PropertyAccess), NOT a
	//    TryGetPawnOwner -> Cast -> getter chain. That is the entire point: a cast-result self-pin
	//    deref on the worker thread is what raises 'Accessing an object reference is not thread-safe'.
	//    Property Access is resolved thread-safe (or game-thread-cached) by the AnimBP compiler.

	// 3a) Bulk-author the pure math + the setters (no pawn/cast chain, no getter calls).
	TSharedRef<FJsonObject> NodesSub = MakeShared<FJsonObject>();
	NodesSub->SetStringField(TEXT("asset_path"), AbpPath);
	NodesSub->SetStringField(TEXT("graph_name"), TargetGraphName);
	{
		TArray<TSharedPtr<FJsonValue>> Nodes;

		auto AddCallNoTarget = [&Nodes](const TCHAR* TempId, const TCHAR* Func)
		{
			TSharedPtr<FJsonObject> N = MakeShared<FJsonObject>();
			N->SetStringField(TEXT("temp_id"), TempId);
			N->SetStringField(TEXT("node_type"), TEXT("call_function"));
			N->SetStringField(TEXT("function_name"), Func);
			N->SetStringField(TEXT("target_class"), TEXT("KismetMathLibrary"));
			Nodes.Add(MakeShared<FJsonValueObject>(N));
		};
		auto AddSet = [&Nodes](const TCHAR* TempId, const FString& VarName)
		{
			TSharedPtr<FJsonObject> N = MakeShared<FJsonObject>();
			N->SetStringField(TEXT("temp_id"), TempId);
			N->SetStringField(TEXT("node_type"), TEXT("VariableSet"));
			N->SetStringField(TEXT("variable_name"), VarName);
			Nodes.Add(MakeShared<FJsonValueObject>(N));
		};

		// Pure math — KismetMathLibrary statics (no self pin, inherently thread-safe).
		AddCallNoTarget(TEXT("vsize_xy"),   TEXT("VSizeXY"));
		AddCallNoTarget(TEXT("speed_gt"),   TEXT("Greater_DoubleDouble"));
		AddCallNoTarget(TEXT("accel_nz"),   TEXT("Vector_IsNearlyZero"));
		AddCallNoTarget(TEXT("not_accel"),  TEXT("Not_PreBool"));
		AddCallNoTarget(TEXT("moving_and"), TEXT("BooleanAND"));

		// Setters for each anim var.
		AddSet(TEXT("set_velocity"),    VelocityVar);
		AddSet(TEXT("set_groundspeed"), GroundSpeedVar);
		AddSet(TEXT("set_accel"),       AccelerationVar);
		if (bWireCrouch) AddSet(TEXT("set_iscrouched"), IsCrouchedVar);
		AddSet(TEXT("set_ismoving"),    IsMovingVar);

		NodesSub->SetArrayField(TEXT("nodes"), Nodes);
		NodesSub->SetBoolField(TEXT("auto_layout"), true);
	}

	FMonolithActionResult NR = FMonolithBlueprintNodeActions::HandleAddNodesBulk(NodesSub);
	NoteStep(TEXT("add_nodes_bulk"), NR.bSuccess, NR.bSuccess ? TEXT("") : NR.ErrorMessage);

	TMap<FString, FString> IdMap;
	ExtractBulkNodeIds(NR, IdMap);

	// 3b) Author the pawn-state SOURCES as GENUINE thread-safe Property Access nodes.
	auto AddPropAccessNode = [&](const TArray<FString>& APath) -> FString
	{
		TSharedRef<FJsonObject> Sub = MakeShared<FJsonObject>();
		Sub->SetStringField(TEXT("asset_path"), AbpPath);
		Sub->SetStringField(TEXT("graph_name"), TargetGraphName);
		TArray<TSharedPtr<FJsonValue>> PathArr;
		for (const FString& S : APath) { PathArr.Add(MakeShared<FJsonValueString>(S)); }
		Sub->SetArrayField(TEXT("path"), PathArr);
		FMonolithActionResult R = FMonolithBlueprintNodeActions::HandleAddPropertyAccessNode(Sub);
		if (!R.bSuccess || !R.Result.IsValid()) return FString();
		FString NodeId; R.Result->TryGetStringField(TEXT("node_id"), NodeId);
		return NodeId;
	};
	const FString PaVelocityId = AddPropAccessNode(VelocityPath);
	const FString PaAccelId     = AddPropAccessNode(AccelerationPath);
	const FString PaCrouchId    = bWireCrouch ? AddPropAccessNode(CrouchPath) : FString();
	NoteStep(TEXT("add_property_access_node"),
		!PaVelocityId.IsEmpty() && !PaAccelId.IsEmpty() && (!bWireCrouch || !PaCrouchId.IsEmpty()),
		FString::Printf(TEXT("velocity=%s acceleration=%s crouch=%s"),
			*PaVelocityId, *PaAccelId, bWireCrouch ? *PaCrouchId : TEXT("(skipped)")));

	// 3c) Resolve the FunctionEntry node id (exec source for the chain).
	FString EntryNodeId;
	if (UEdGraph* TsGraph = MonolithBlueprintInternal::FindGraphByName(ABP, TargetGraphName))
	{
		for (UEdGraphNode* Node : TsGraph->Nodes)
		{
			if (Node && Node->GetClass() && Node->GetClass()->GetName().Contains(TEXT("FunctionEntry")))
			{
				EntryNodeId = Node->GetName();
				break;
			}
		}
	}

	// 3d) Wire every connection via connect_pins_bulk. Pin names are engine defaults:
	//      CallFunction pure return = "ReturnValue"; FunctionEntry exec out = "then";
	//      VariableSet: exec "execute"/"then", value-in = the variable name.
	//      Property Access node: output data pin = "Value" (the resolved leaf read).
	const FString VSizeXY   = IdMap.FindRef(TEXT("vsize_xy"));
	const FString SpeedGt   = IdMap.FindRef(TEXT("speed_gt"));
	const FString AccelNz   = IdMap.FindRef(TEXT("accel_nz"));
	const FString NotAccel  = IdMap.FindRef(TEXT("not_accel"));
	const FString MovingAnd = IdMap.FindRef(TEXT("moving_and"));
	const FString SetVel    = IdMap.FindRef(TEXT("set_velocity"));
	const FString SetGspd   = IdMap.FindRef(TEXT("set_groundspeed"));
	const FString SetAccel  = IdMap.FindRef(TEXT("set_accel"));
	const FString SetCrouch = bWireCrouch ? IdMap.FindRef(TEXT("set_iscrouched")) : FString();
	const FString SetMoving = IdMap.FindRef(TEXT("set_ismoving"));

	TArray<TSharedPtr<FJsonValue>> Conns;
	auto Wire = [&Conns](const FString& SN, const TCHAR* SP, const FString& TN, const TCHAR* TP)
	{
		if (SN.IsEmpty() || TN.IsEmpty()) return;
		TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
		C->SetStringField(TEXT("source_node"), SN);
		C->SetStringField(TEXT("source_pin"), SP);
		C->SetStringField(TEXT("target_node"), TN);
		C->SetStringField(TEXT("target_pin"), TP);
		Conns.Add(MakeShared<FJsonValueObject>(C));
	};

	// Exec chain: Entry -> SetVel -> SetGspd -> SetAccel -> [SetCrouch ->] SetMoving.
	Wire(EntryNodeId, TEXT("then"), SetVel,   TEXT("execute"));
	Wire(SetVel,      TEXT("then"), SetGspd,  TEXT("execute"));
	Wire(SetGspd,     TEXT("then"), SetAccel, TEXT("execute"));
	if (bWireCrouch)
	{
		Wire(SetAccel,  TEXT("then"), SetCrouch, TEXT("execute"));
		Wire(SetCrouch, TEXT("then"), SetMoving, TEXT("execute"));
	}
	else
	{
		Wire(SetAccel,  TEXT("then"), SetMoving, TEXT("execute"));
	}

	// Velocity SOURCE = Property Access 'Value' -> Set Velocity + VSizeXY.A.
	Wire(PaVelocityId, TEXT("Value"), SetVel,  *VelocityVar);
	Wire(PaVelocityId, TEXT("Value"), VSizeXY, TEXT("A"));

	// GroundSpeed -> Set GroundSpeed + Greater compare A.
	Wire(VSizeXY, TEXT("ReturnValue"), SetGspd, *GroundSpeedVar);
	Wire(VSizeXY, TEXT("ReturnValue"), SpeedGt, TEXT("A"));

	// Acceleration SOURCE = Property Access 'Value' -> Set Acceleration + IsNearlyZero A.
	Wire(PaAccelId, TEXT("Value"), SetAccel, *AccelerationVar);
	Wire(PaAccelId, TEXT("Value"), AccelNz,  TEXT("A"));

	// crouch SOURCE = Property Access 'Value' -> Set bIsCrouched (only when a bool path was supplied).
	if (bWireCrouch)
	{
		Wire(PaCrouchId, TEXT("Value"), SetCrouch, *IsCrouchedVar);
	}

	// bIsMoving = (GroundSpeed > threshold) AND NOT (Accel.IsNearlyZero).
	Wire(SpeedGt,   TEXT("ReturnValue"), MovingAnd, TEXT("A"));
	Wire(AccelNz,   TEXT("ReturnValue"), NotAccel,  TEXT("A"));
	Wire(NotAccel,  TEXT("ReturnValue"), MovingAnd, TEXT("B"));
	Wire(MovingAnd, TEXT("ReturnValue"), SetMoving, *IsMovingVar);

	int32 Connected = 0;
	{
		TSharedRef<FJsonObject> ConnSub = MakeShared<FJsonObject>();
		ConnSub->SetStringField(TEXT("asset_path"), AbpPath);
		ConnSub->SetStringField(TEXT("graph_name"), TargetGraphName);
		ConnSub->SetArrayField(TEXT("connections"), Conns);
		FMonolithActionResult CR = FMonolithBlueprintNodeActions::HandleConnectPinsBulk(ConnSub);
		if (CR.bSuccess && CR.Result.IsValid())
		{
			double C = 0.0; CR.Result->TryGetNumberField(TEXT("connected"), C);
			Connected = (int32)C;
		}
		NoteStep(TEXT("connect_pins_bulk"), CR.bSuccess,
			FString::Printf(TEXT("%d/%d connected"), Connected, Conns.Num()));
	}

	// Set the GroundSpeed threshold default on the compare's B pin (3.0 cm/s).
	{
		TSharedRef<FJsonObject> DefSub = MakeShared<FJsonObject>();
		DefSub->SetStringField(TEXT("asset_path"), AbpPath);
		DefSub->SetStringField(TEXT("graph_name"), TargetGraphName);
		DefSub->SetStringField(TEXT("node_id"), SpeedGt);
		DefSub->SetStringField(TEXT("pin_name"), TEXT("B"));
		DefSub->SetStringField(TEXT("value"), TEXT("3.0"));
		FMonolithBlueprintNodeActions::HandleSetPinDefault(DefSub); // best-effort
	}

	// Surface the temp_id -> node_id map (plus the property-access node ids) for callers.
	TSharedPtr<FJsonObject> NodeIdMap = MakeShared<FJsonObject>();
	for (const TPair<FString, FString>& KV : IdMap)
	{
		NodeIdMap->SetStringField(KV.Key, KV.Value);
	}
	if (!PaVelocityId.IsEmpty()) NodeIdMap->SetStringField(TEXT("pa_velocity"), PaVelocityId);
	if (!PaAccelId.IsEmpty())    NodeIdMap->SetStringField(TEXT("pa_acceleration"), PaAccelId);
	if (!PaCrouchId.IsEmpty())   NodeIdMap->SetStringField(TEXT("pa_crouch"), PaCrouchId);
	if (!EntryNodeId.IsEmpty())  NodeIdMap->SetStringField(TEXT("function_entry"), EntryNodeId);

	FBlueprintEditorUtils::MarkBlueprintAsModified(ABP);

	TArray<TSharedPtr<FJsonValue>> VarNames;
	for (const FVarSpec& V : Vars) { VarNames.Add(MakeShared<FJsonValueString>(V.Name)); }

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("graph_name"), TargetGraphName);
	Root->SetArrayField(TEXT("anim_variables"), VarNames);
	Root->SetNumberField(TEXT("variables_created"), VarsCreated);
	Root->SetNumberField(TEXT("connections_made"), Connected);
	Root->SetArrayField(TEXT("steps"), Steps);
	Root->SetObjectField(TEXT("node_id_map"), NodeIdMap);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ===========================================================================
// Pack D — apply_locomotion_speed_band
// ===========================================================================

FMonolithActionResult FMonolithMotionMatchingScaffoldActions::HandleApplyLocomotionSpeedBand(const TSharedPtr<FJsonObject>& Params)
{
	const FString BpPath = Params->GetStringField(TEXT("bp_path"));
	if (BpPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: bp_path"));

	double WalkSpeed = 0.0, RunSpeed = 0.0, CrouchSpeed = 0.0;
	if (!Params->TryGetNumberField(TEXT("walk_speed"), WalkSpeed))
		return FMonolithActionResult::Error(TEXT("Missing required parameter: walk_speed"));
	if (!Params->TryGetNumberField(TEXT("run_speed"), RunSpeed))
		return FMonolithActionResult::Error(TEXT("Missing required parameter: run_speed"));
	if (!Params->TryGetNumberField(TEXT("crouch_speed"), CrouchSpeed))
		return FMonolithActionResult::Error(TEXT("Missing required parameter: crouch_speed"));

	double JogSpeed = 0.0; Params->TryGetNumberField(TEXT("jog_speed"), JogSpeed);

	// MaxWalkSpeed cap defaults to run_speed; explicit override wins.
	double MaxWalkSpeed = RunSpeed;
	Params->TryGetNumberField(TEXT("max_walk_speed"), MaxWalkSpeed);
	double MaxAcceleration = 2048.0;
	Params->TryGetNumberField(TEXT("max_acceleration"), MaxAcceleration);
	double BrakingDecel = 2048.0;
	Params->TryGetNumberField(TEXT("braking_deceleration"), BrakingDecel);

	UBlueprint* BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(BpPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *BpPath));
	}

	// Resolve the CMC BY CLASS on the CDO — same handshake as apply_movement_preset
	// (the native inherited CMC is "CharMoveComp", not "CharacterMovement").
	UClass* CmcClass = FindFirstObject<UClass>(TEXT("CharacterMovementComponent"), EFindFirstObjectOptions::NativeFirst);
	if (!CmcClass)
	{
		CmcClass = FindFirstObject<UClass>(TEXT("UCharacterMovementComponent"), EFindFirstObjectOptions::NativeFirst);
	}
	if (!CmcClass)
	{
		return FMonolithActionResult::Error(TEXT("apply_locomotion_speed_band: UCharacterMovementComponent class not found"));
	}
	UActorComponent* CmcComp = ResolveComponentOnBP(BP, FString(), CmcClass, {});
	if (!CmcComp)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("apply_locomotion_speed_band: no CharacterMovementComponent found on '%s' (is the parent a Character?)"), *BpPath));
	}
	const FString CmcName = CmcComp->GetName();

	// Write each CMC cap via set_component_property (Details-panel write path +
	// PostEditChange), mirroring apply_movement_preset.
	TArray<TPair<FString, FString>> Writes;
	Writes.Emplace(TEXT("MaxWalkSpeed"),              FString::SanitizeFloat(MaxWalkSpeed));
	Writes.Emplace(TEXT("MaxWalkSpeedCrouched"),      FString::SanitizeFloat(CrouchSpeed));
	Writes.Emplace(TEXT("MaxAcceleration"),           FString::SanitizeFloat(MaxAcceleration));
	Writes.Emplace(TEXT("BrakingDecelerationWalking"),FString::SanitizeFloat(BrakingDecel));

	TArray<TSharedPtr<FJsonValue>> Applied;
	for (const TPair<FString, FString>& Write : Writes)
	{
		TSharedRef<FJsonObject> Sub = MakeSub(BpPath);
		Sub->SetStringField(TEXT("component_name"), CmcName);
		Sub->SetStringField(TEXT("property_name"), Write.Key);
		Sub->SetStringField(TEXT("value"), Write.Value);

		FMonolithActionResult R = FMonolithBlueprintComponentActions::HandleSetComponentProperty(Sub);
		if (!R.bSuccess)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("apply_locomotion_speed_band: failed to set '%s' on %s — %s"),
				*Write.Key, *CmcName, *R.ErrorMessage));
		}
		TSharedPtr<FJsonObject> A = MakeShared<FJsonObject>();
		A->SetStringField(TEXT("property"), Write.Key);
		A->SetStringField(TEXT("value"), Write.Value);
		Applied.Add(MakeShared<FJsonValueObject>(A));
	}

	// Same persistence handshake as set_anim_class / apply_movement_preset for an inherited
	// native component: structural-modify + recompile so the CDO override survives reload.
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	BP->MarkPackageDirty();

	// Echo the documented gait band (BT picks within these caps at runtime).
	TSharedPtr<FJsonObject> Band = MakeShared<FJsonObject>();
	Band->SetNumberField(TEXT("walk"), WalkSpeed);
	if (JogSpeed > 0.0) Band->SetNumberField(TEXT("jog"), JogSpeed);
	Band->SetNumberField(TEXT("run"), RunSpeed);
	Band->SetNumberField(TEXT("crouch"), CrouchSpeed);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("bp_path"), BpPath);
	Root->SetStringField(TEXT("component"), CmcName);
	Root->SetArrayField(TEXT("applied"), Applied);
	Root->SetObjectField(TEXT("band"), Band);
	return FMonolithActionResult::Success(Root);
}
