#include "MonolithAbpGraphSurgeryActions.h"
#include "MonolithAssetUtils.h"
#include "MonolithParamSchema.h"

#include "Animation/AnimBlueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraphSchema.h"
#include "EdGraphSchema_K2.h"
#include "K2Node.h"
#include "K2Node_DynamicCast.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "K2Node_CallFunction.h"
#include "K2Node_FunctionEntry.h"
#include "K2Node_Self.h"
#include "Engine/MemberReference.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/CompilerResultsLog.h"
#include "EditorAssetLibrary.h"
#include "UObject/Class.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectGlobals.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

#if WITH_CHOOSER
// UChooserTable lives on the Chooser module public include path (Chooser.Build.cs
// adds its Internal/ dir). The Evaluate-Chooser NODE class (K2Node_EvaluateChooser2)
// is in ChooserUncooked/Private and is NOT includable — it is resolved reflectively.
#include "Chooser.h"
#endif

// Resolvers shared with MonolithAbpWriteActions.cpp (same module, internal linkage there).
// Re-declared here as file-local helpers to keep this surgery file self-contained and
// independently rollback-able.

namespace
{

// ---------------------------------------------------------------------------
// Graph / node resolution
// ---------------------------------------------------------------------------

/** Collect every editable graph reachable from a Blueprint (ubergraphs, function graphs, state inner graphs). */
void GatherAllGraphs(UBlueprint* BP, TArray<UEdGraph*>& OutGraphs)
{
	if (!BP) return;
	BP->GetAllGraphs(OutGraphs);
}

/** Resolve a target graph by name from a Blueprint's full graph set. "AnimGraph" matches the main anim graph. */
UEdGraph* ResolveGraphByName(UBlueprint* BP, const FString& GraphName, FString& OutError)
{
	TArray<UEdGraph*> AllGraphs;
	GatherAllGraphs(BP, AllGraphs);

	if (GraphName.IsEmpty())
	{
		OutError = TEXT("graph_name is required");
		return nullptr;
	}

	// Exact name match first.
	for (UEdGraph* Graph : AllGraphs)
	{
		if (Graph && Graph->GetName() == GraphName)
		{
			return Graph;
		}
	}

	// "AnimGraph" alias: the main anim graph is conventionally named AnimGraph; if an exact
	// match failed, fall back to the first graph whose name contains "AnimGraph".
	if (GraphName.Equals(TEXT("AnimGraph"), ESearchCase::IgnoreCase))
	{
		for (UEdGraph* Graph : AllGraphs)
		{
			if (Graph && Graph->GetName().Contains(TEXT("AnimGraph")))
			{
				return Graph;
			}
		}
	}

	OutError = FString::Printf(TEXT("Graph '%s' not found in blueprint"), *GraphName);
	return nullptr;
}

/** Find a node by UObject name across all graphs of a Blueprint, or within a specific graph. */
UEdGraphNode* FindNodeByNameBP(UBlueprint* BP, const FString& NodeName, UEdGraph* InGraph = nullptr)
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

	TArray<UEdGraph*> AllGraphs;
	GatherAllGraphs(BP, AllGraphs);
	for (UEdGraph* Graph : AllGraphs)
	{
		if (UEdGraphNode* Found = SearchGraph(Graph))
		{
			return Found;
		}
	}
	return nullptr;
}

// ---------------------------------------------------------------------------
// Compile-with-error-harvest (mirrors MonolithBlueprintCompileActions.cpp:98-144)
// ---------------------------------------------------------------------------

/** Compile a Blueprint and harvest errors/warnings into the supplied JSON root. Returns true on UpToDate/UpToDateWithWarnings. */
bool CompileWithHarvest(UBlueprint* BP, const TSharedPtr<FJsonObject>& Root)
{
	FCompilerResultsLog Results;
	FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::SkipGarbageCollection, &Results);

	// Map compiler messages back to nodes via bHasCompilerMessage/ErrorMsg.
	TMap<FString, TPair<FString, FString>> NodeErrorMap; // ErrorMsg -> {NodeName, GraphName}
	{
		TArray<UEdGraph*> AllGraphs;
		BP->GetAllGraphs(AllGraphs);
		for (UEdGraph* Graph : AllGraphs)
		{
			if (!Graph) continue;
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				if (!Node || !Node->bHasCompilerMessage) continue;
				if (!Node->ErrorMsg.IsEmpty())
				{
					NodeErrorMap.Add(Node->ErrorMsg, TPair<FString, FString>(Node->GetName(), Graph->GetName()));
				}
			}
		}
	}

	TArray<TSharedPtr<FJsonValue>> ErrorArr, WarnArr;
	for (const TSharedRef<FTokenizedMessage>& Msg : Results.Messages)
	{
		TSharedPtr<FJsonObject> MsgObj = MakeShared<FJsonObject>();
		FString MsgText = Msg->ToText().ToString();
		MsgObj->SetStringField(TEXT("message"), MsgText);

		for (const auto& Pair : NodeErrorMap)
		{
			if (MsgText.Contains(Pair.Key) || Pair.Key.Contains(MsgText))
			{
				MsgObj->SetStringField(TEXT("node_id"), Pair.Value.Key);
				MsgObj->SetStringField(TEXT("graph_name"), Pair.Value.Value);
				break;
			}
		}

		if (Msg->GetSeverity() == EMessageSeverity::Error)
		{
			ErrorArr.Add(MakeShared<FJsonValueObject>(MsgObj));
		}
		else if (Msg->GetSeverity() == EMessageSeverity::Warning)
		{
			WarnArr.Add(MakeShared<FJsonValueObject>(MsgObj));
		}
	}

	FString StatusStr;
	switch (BP->Status)
	{
	case BS_Unknown:              StatusStr = TEXT("Unknown"); break;
	case BS_Dirty:                StatusStr = TEXT("Dirty"); break;
	case BS_Error:                StatusStr = TEXT("Error"); break;
	case BS_UpToDate:             StatusStr = TEXT("UpToDate"); break;
	case BS_UpToDateWithWarnings: StatusStr = TEXT("UpToDateWithWarnings"); break;
	case BS_BeingCreated:         StatusStr = TEXT("BeingCreated"); break;
	default:                      StatusStr = TEXT("Unknown"); break;
	}

	const bool bSuccess = (BP->Status == BS_UpToDate || BP->Status == BS_UpToDateWithWarnings);

	TSharedPtr<FJsonObject> CompileObj = MakeShared<FJsonObject>();
	CompileObj->SetBoolField(TEXT("success"), bSuccess);
	CompileObj->SetStringField(TEXT("status"), StatusStr);
	CompileObj->SetArrayField(TEXT("errors"), ErrorArr);
	CompileObj->SetArrayField(TEXT("warnings"), WarnArr);
	CompileObj->SetNumberField(TEXT("error_count"), ErrorArr.Num());
	CompileObj->SetNumberField(TEXT("warning_count"), WarnArr.Num());
	Root->SetObjectField(TEXT("compile"), CompileObj);

	return bSuccess;
}

// ---------------------------------------------------------------------------
// Pin serialization helpers
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> DescribePin(const UEdGraphPin* Pin)
{
	TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
	if (!Pin) return Obj;
	Obj->SetStringField(TEXT("name"), Pin->PinName.ToString());
	Obj->SetStringField(TEXT("direction"), Pin->Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
	Obj->SetStringField(TEXT("category"), Pin->PinType.PinCategory.ToString());
	Obj->SetNumberField(TEXT("link_count"), Pin->LinkedTo.Num());
	return Obj;
}

/** Snapshot of one external connection on a captured (about-to-be-removed) node. */
struct FCapturedLink
{
	FName        PinName;
	EEdGraphPinDirection Direction = EGPD_Input;
	FEdGraphPinType PinType;
	UEdGraphNode* OtherNode = nullptr; // remote endpoint node (still alive)
	FName        OtherPinName;
};

/** Capture every external link on a node so it can be re-resolved after the node is replaced. */
void CaptureExternalLinks(UEdGraphNode* Node, TArray<FCapturedLink>& Out)
{
	if (!Node) return;
	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (!Pin) continue;
		for (UEdGraphPin* Linked : Pin->LinkedTo)
		{
			if (!Linked || !Linked->GetOwningNodeUnchecked()) continue;
			FCapturedLink Cap;
			Cap.PinName = Pin->PinName;
			Cap.Direction = Pin->Direction;
			Cap.PinType = Pin->PinType;
			Cap.OtherNode = Linked->GetOwningNode();
			Cap.OtherPinName = Linked->PinName;
			Out.Add(Cap);
		}
	}
}

/** Find a pin on a node by name + direction. Returns nullptr if absent. */
UEdGraphPin* FindPinByNameDir(UEdGraphNode* Node, FName PinName, EEdGraphPinDirection Direction)
{
	if (!Node) return nullptr;
	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (Pin && Pin->PinName == PinName && Pin->Direction == Direction)
		{
			return Pin;
		}
	}
	return nullptr;
}

// ---------------------------------------------------------------------------
// Evaluate-Chooser reflective resolution
// ---------------------------------------------------------------------------

#if WITH_CHOOSER

/** Reflective /Script path of the v2 Evaluate Chooser K2 node. Verified module name: ChooserUncooked. */
static const TCHAR* EvaluateChooser2ClassPath = TEXT("/Script/ChooserUncooked.K2Node_EvaluateChooser2");

/** Resolve the UK2Node_EvaluateChooser2 UClass reflectively. Returns nullptr if the Chooser plugin module isn't loaded. */
UClass* ResolveEvaluateChooser2Class()
{
	// LoadClass forces the owning module's class to be available if the plugin is present.
	UClass* Cls = LoadClass<UObject>(nullptr, EvaluateChooser2ClassPath);
	if (!Cls)
	{
		Cls = FindObject<UClass>(nullptr, EvaluateChooser2ClassPath);
	}
	return Cls;
}

/** True if Node's class chain matches the Evaluate-Chooser v2 class (resolved reflectively). */
bool IsEvaluateChooser2Node(const UEdGraphNode* Node, UClass* EvalClass)
{
	return Node && EvalClass && Node->GetClass()->IsChildOf(EvalClass);
}

#endif // WITH_CHOOSER

// ---------------------------------------------------------------------------
// Node classification (F11)
// ---------------------------------------------------------------------------

/** A classified finding about one node in a duplicated/reparented ABP. */
struct FClassification
{
	FString NodeName;
	FString GraphName;
	FString NodeClass;
	FString Kind;        // cast / variable_get / function_call / evaluate_chooser
	FString Detail;      // target class / var name / function name
	FString Label;       // safe / requires_guard / requires_rebuild / remove_for_smoke
	FString Reason;
};

// ---------------------------------------------------------------------------
// Node-slice traversal (F12)
// ---------------------------------------------------------------------------

/** Parsed stop-rules for slice traversal. */
struct FStopRules
{
	TSet<FString> StopNodeNames;
	TSet<FString> StopNodeClasses; // matched against UClass GetName() (with/without 'U'/'K2Node_' prefix tolerance)
	int32 MaxNodes = 0;            // 0 = unbounded

	bool MatchesStopClass(const UEdGraphNode* Node) const
	{
		if (StopNodeClasses.Num() == 0 || !Node) return false;
		const FString ClassName = Node->GetClass()->GetName();
		for (const FString& Rule : StopNodeClasses)
		{
			if (ClassName == Rule || ClassName.Contains(Rule))
			{
				return true;
			}
		}
		return false;
	}
};

/** Parse the optional stop_rules JSON object. */
FStopRules ParseStopRules(const TSharedPtr<FJsonObject>& Params)
{
	FStopRules Rules;
	const TSharedPtr<FJsonObject>* StopObj = nullptr;
	if (Params->TryGetObjectField(TEXT("stop_rules"), StopObj) && StopObj && StopObj->IsValid())
	{
		const TArray<TSharedPtr<FJsonValue>>* Names = nullptr;
		if ((*StopObj)->TryGetArrayField(TEXT("stop_at_node_names"), Names) && Names)
		{
			for (const TSharedPtr<FJsonValue>& V : *Names)
			{
				if (V.IsValid()) Rules.StopNodeNames.Add(V->AsString());
			}
		}
		const TArray<TSharedPtr<FJsonValue>>* Classes = nullptr;
		if ((*StopObj)->TryGetArrayField(TEXT("stop_at_node_classes"), Classes) && Classes)
		{
			for (const TSharedPtr<FJsonValue>& V : *Classes)
			{
				if (V.IsValid()) Rules.StopNodeClasses.Add(V->AsString());
			}
		}
		int32 MaxN = 0;
		if ((*StopObj)->TryGetNumberField(TEXT("max_nodes"), MaxN))
		{
			Rules.MaxNodes = MaxN;
		}
	}
	return Rules;
}

/**
 * Collect the directional slice from a seed node. Direction 'downstream' follows output-pin
 * links to consumer nodes; 'upstream' follows input-pin links to source nodes. The seed itself
 * is included. Stop-rule boundaries are NOT included in the slice (traversal halts there).
 */
void CollectSlice(UEdGraphNode* Seed, bool bDownstream, const FStopRules& Rules, TSet<UEdGraphNode*>& OutSlice)
{
	if (!Seed) return;

	TArray<UEdGraphNode*> Frontier;
	Frontier.Add(Seed);
	OutSlice.Add(Seed);

	while (Frontier.Num() > 0)
	{
		if (Rules.MaxNodes > 0 && OutSlice.Num() >= Rules.MaxNodes)
		{
			break;
		}

		UEdGraphNode* Current = Frontier.Pop(EAllowShrinking::No);
		if (!Current) continue;

		for (UEdGraphPin* Pin : Current->Pins)
		{
			if (!Pin) continue;
			// Downstream walks outputs; upstream walks inputs.
			const bool bConsiderPin = bDownstream ? (Pin->Direction == EGPD_Output) : (Pin->Direction == EGPD_Input);
			if (!bConsiderPin) continue;

			for (UEdGraphPin* Linked : Pin->LinkedTo)
			{
				if (!Linked) continue;
				UEdGraphNode* Neighbour = Linked->GetOwningNodeUnchecked();
				if (!Neighbour || OutSlice.Contains(Neighbour)) continue;

				// Stop-rule boundary: do not include the boundary node and do not traverse past it.
				if (Rules.StopNodeNames.Contains(Neighbour->GetName()) || Rules.MatchesStopClass(Neighbour))
				{
					continue;
				}

				OutSlice.Add(Neighbour);
				Frontier.Add(Neighbour);
			}
		}
	}
}

/** Collect pins on nodes OUTSIDE the slice that link into the slice — these become orphaned on removal. */
TArray<TSharedPtr<FJsonValue>> ComputeOrphanedPins(const TSet<UEdGraphNode*>& Slice)
{
	TArray<TSharedPtr<FJsonValue>> Out;
	for (UEdGraphNode* SliceNode : Slice)
	{
		if (!SliceNode) continue;
		for (UEdGraphPin* Pin : SliceNode->Pins)
		{
			if (!Pin) continue;
			for (UEdGraphPin* Linked : Pin->LinkedTo)
			{
				if (!Linked) continue;
				UEdGraphNode* Remote = Linked->GetOwningNodeUnchecked();
				if (!Remote || Slice.Contains(Remote)) continue; // internal link — not orphaned
				TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
				Obj->SetStringField(TEXT("node"), Remote->GetName());
				Obj->SetStringField(TEXT("pin"), Linked->PinName.ToString());
				Obj->SetStringField(TEXT("direction"), Linked->Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
				const bool bIsExec = (Linked->PinType.PinCategory == TEXT("exec"));
				Obj->SetBoolField(TEXT("is_exec"), bIsExec);
				Out.Add(MakeShared<FJsonValueObject>(Obj));
			}
		}
	}
	return Out;
}

} // anonymous namespace


// ===========================================================================
//  Registration
// ===========================================================================

void FMonolithAbpGraphSurgeryActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// --- rebuild_evaluate_chooser_node ---
	Registry.RegisterAction(TEXT("animation"), TEXT("rebuild_evaluate_chooser_node"),
		TEXT("Delete + recreate a single Evaluate-Chooser (v2) node with pins regenerated from a target UChooserTable, preserving compatible exec/data connections. Reflectively spawns UK2Node_EvaluateChooser2. Degrades to detect-and-remove + manual-recreate spec if the reflective rebuild cannot complete. Requires the Chooser plugin (WITH_CHOOSER)."),
		FMonolithActionHandler::CreateStatic(&HandleRebuildEvaluateChooserNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("anim_blueprint"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("graph_name"), TEXT("string"), TEXT("Graph containing the node ('AnimGraph' for the main anim graph, or a function/event graph name)"))
			.Required(TEXT("node_ref"), TEXT("string"), TEXT("UObject name of the Evaluate-Chooser node to rebuild"))
			.RequiredAssetPath(TEXT("chooser_asset"), TEXT("UChooserTable asset to bind on the rebuilt node"))
			.Optional(TEXT("context_binding"), TEXT("string"), TEXT("Optional context binding hint (reserved; pins regenerate from the chooser context)"))
			.Build());

	// --- replace_evaluate_chooser_nodes ---
	Registry.RegisterAction(TEXT("animation"), TEXT("replace_evaluate_chooser_nodes"),
		TEXT("Batch-rebuild Evaluate-Chooser (v2) nodes across an ABP. Each replacement entry: {graph_name, node_ref, chooser_asset}. dry_run reports what would change without mutating. Requires the Chooser plugin (WITH_CHOOSER)."),
		FMonolithActionHandler::CreateStatic(&HandleReplaceEvaluateChooserNodes),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("anim_blueprint"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("replacements"), TEXT("array"), TEXT("Array of {graph_name, node_ref, chooser_asset} objects"))
			.Optional(TEXT("dry_run"), TEXT("bool"), TEXT("Report only, no mutation (default: true)"), TEXT("true"))
			.Build());

	// --- add_evaluate_chooser_node (Pack B) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("add_evaluate_chooser_node"),
		TEXT("Spawn a FRESH Evaluate-Chooser (v2) node into an ABP AnimGraph, bound to a UChooserTable. Reflectively creates UK2Node_EvaluateChooser2 (its header is in ChooserUncooked/Private and cannot be included). The node's 'Result' output pin type follows the chooser's OutputObjectType (e.g. UPoseSearchDatabase). Returns node_name + result_pin for wiring. Requires the Chooser plugin (WITH_CHOOSER)."),
		FMonolithActionHandler::CreateStatic(&HandleAddEvaluateChooserNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.RequiredAssetPath(TEXT("chooser_path"), TEXT("UChooserTable asset to bind on the new node"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph ('AnimGraph' for the main anim graph). Default: AnimGraph"), TEXT("AnimGraph"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("Node X position (default: 0)"), TEXT("0"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Node Y position (default: 0)"), TEXT("0"))
			.Build());

	// --- wire_chooser_to_motion_matching (Pack B) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("wire_chooser_to_motion_matching"),
		TEXT("Connect an Evaluate-Chooser node's 'Result' output (a UPoseSearchDatabase) to a Motion Matching node's 'Database' input pin, so the active MM database is chooser-driven. Use after add_evaluate_chooser_node + build_motion_matching_node. Requires the Chooser plugin (WITH_CHOOSER)."),
		FMonolithActionHandler::CreateStatic(&HandleWireChooserToMotionMatching),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("chooser_node"), TEXT("string"), TEXT("UObject name of the Evaluate-Chooser node (from add_evaluate_chooser_node response)"))
			.Required(TEXT("mm_node"), TEXT("string"), TEXT("UObject name of the Motion Matching node (from build_motion_matching_node response)"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Graph containing both nodes. Default: AnimGraph"), TEXT("AnimGraph"))
			.Build());

	// --- bind_chooser_database_via_threadsafe (Pack B) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("bind_chooser_database_via_threadsafe"),
		TEXT("WORKING exec-driven chooser pattern. Places the (exec-driven) EvaluateChooser2 node inside a thread-safe FUNCTION graph: wires the function entry's exec into the chooser's 'execute', sets the chooser context to 'self' (the AnimInstance) via a Self node, stores the chooser 'Result' (UPoseSearchDatabase) into the named SelectedDatabase variable, then exposes the Motion Matching node's 'Database' pin and feeds it from a VariableGet of that variable. Fixes the A-pose failure where a bare chooser dropped in the AnimGraph with 'execute' unconnected is pruned by the compiler. The function graph is created if absent and marked Thread Safe. Requires the Chooser plugin (WITH_CHOOSER)."),
		FMonolithActionHandler::CreateStatic(&HandleBindChooserDatabaseViaThreadSafe),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.RequiredAssetPath(TEXT("chooser_path"), TEXT("UChooserTable asset to bind"))
			.Required(TEXT("mm_node"), TEXT("string"), TEXT("UObject name of the Motion Matching node (from build_motion_matching_node)"))
			.Required(TEXT("selected_database_var"), TEXT("string"), TEXT("Name of the UPoseSearchDatabase variable to store the chooser result into (must already exist on the ABP)"))
			.Optional(TEXT("function_name"), TEXT("string"), TEXT("Thread-safe function graph to author the chooser into (created if absent). Default: SelectLocomotionDatabase"), TEXT("SelectLocomotionDatabase"))
			.Optional(TEXT("anim_graph_name"), TEXT("string"), TEXT("Graph containing the Motion Matching node. Default: AnimGraph"), TEXT("AnimGraph"))
			.Build());

	// --- bind_threadsafe_update_function (T1-L1) ---
	Registry.RegisterAction(TEXT("animation"), TEXT("bind_threadsafe_update_function"),
		TEXT("Insert a thread-safe BP-function CALL into an ABP's thread-safe FUNCTION graph (the surgery proven by bind_chooser_database_via_threadsafe, generalized from EvaluateChooser2 to a generic UK2Node_CallFunction). Resolves function.class+function.name to a UFunction*, asserts it is non-pure, BlueprintThreadSafe, Kismet-callable, has no return-param and a single non-exec result, then: creates/reuses a Thread-Safe function graph, wires FunctionEntry exec -> call exec, optionally feeds the call's self/object-context pin from a Self node, applies a small fixed arg_bindings set (pin -> literal default, or pin -> self), stores the call result into result_target.var via a VariableSet, and (optionally) feeds an AnimGraph target node pin via a VariableGet of that var. v1a SCOPE = known-signature BP-library/member static; unsupported signatures are rejected with a clear error (no silent mis-wire). Independent of the Chooser plugin."),
		FMonolithActionHandler::CreateStatic(&HandleBindThreadsafeUpdateFunction),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("abp_path"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("function"), TEXT("object"), TEXT("{class:'<UClass path or short name, e.g. /Script/AnimGraphRuntime.KismetAnimationLibrary or KismetMathLibrary>', name:'<UFunction name>'} — must resolve to a non-pure, BlueprintThreadSafe, Kismet-callable function with no return parameter"))
			.Optional(TEXT("arg_bindings"), TEXT("array"), TEXT("Optional [{pin:'<input pin name>', value:'<literal default>'} | {pin:'<object/self input pin name>', self:true}] — small fixed arg set. Unsupported bindings (unknown pin, non-literal-settable type) error rather than mis-wire. v1b arbitrary-signature binding is a gated follow-on."))
			.Required(TEXT("result_target"), TEXT("object"), TEXT("{var:'<self variable to store the call result into; created-elsewhere, must already exist>', node:'<optional AnimGraph node UObject name>', pin:'<optional input pin on that node>'} — the call's single non-exec result is stored into var via a VariableSet; if node+pin given an AnimGraph VariableGet feeds that pin"))
			.Optional(TEXT("function_name"), TEXT("string"), TEXT("Thread-safe function graph to author the call into (created if absent). Default: ThreadSafeUpdateFunction"), TEXT("ThreadSafeUpdateFunction"))
			.Optional(TEXT("anim_graph_name"), TEXT("string"), TEXT("Graph containing the result target node. Default: AnimGraph"), TEXT("AnimGraph"))
			.Build());

	// --- duplicate_reparent_and_sanitize ---
	Registry.RegisterAction(TEXT("animation"), TEXT("duplicate_reparent_and_sanitize"),
		TEXT("Duplicate an ABP, reparent it to new_parent_class, then walk every graph and classify casts / variable-gets / function-calls / Evaluate-Chooser nodes against the new parent's reflected surface. Each finding is labelled safe / requires_guard / requires_rebuild / remove_for_smoke. dry_run (default true) reports only."),
		FMonolithActionHandler::CreateStatic(&HandleDuplicateReparentAndSanitize),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("source_abp"), TEXT("Source Animation Blueprint asset path"))
			.RequiredAssetPath(TEXT("destination_path"), TEXT("Destination ABP asset path for the duplicate (e.g. /Game/Tests/Monolith/ABP_Copy)"))
			.Required(TEXT("new_parent_class"), TEXT("string"), TEXT("New parent AnimInstance class — name or /Script/.../...Class path or BlueprintGeneratedClass path"))
			.Optional(TEXT("dry_run"), TEXT("bool"), TEXT("Report only; when false the duplicate is created + reparented but auto-fix still requires opt-in (default: true)"), TEXT("true"))
			.Build());

	// --- find_node_slice ---
	Registry.RegisterAction(TEXT("animation"), TEXT("find_node_slice"),
		TEXT("Compute a directional node slice from a seed node (upstream or downstream) honouring stop_rules, without mutating the graph. Reports the slice node set, before/after node counts, and pins that would be orphaned by removal."),
		FMonolithActionHandler::CreateStatic(&HandleFindNodeSlice),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("anim_blueprint"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("graph_name"), TEXT("string"), TEXT("Graph containing the seed node"))
			.Required(TEXT("seed_node_ref"), TEXT("string"), TEXT("UObject name of the seed node"))
			.Optional(TEXT("direction"), TEXT("string"), TEXT("'upstream' (sources feeding the seed) or 'downstream' (consumers fed by the seed). Default: downstream"), TEXT("downstream"))
			.Optional(TEXT("stop_rules"), TEXT("object"), TEXT("Optional: {stop_at_node_names:[...], stop_at_node_classes:[...], max_nodes:N} — traversal halts at these boundaries"))
			.Build());

	// --- remove_node_slice ---
	Registry.RegisterAction(TEXT("animation"), TEXT("remove_node_slice"),
		TEXT("Remove a directional node slice (see find_node_slice) from an ABP graph. Reports before/after node counts, newly orphaned pins, and any broken required-exec continuity (surfaced, never silently auto-rewired). Recompiles with error harvest. dry_run (default true) reports only."),
		FMonolithActionHandler::CreateStatic(&HandleRemoveNodeSlice),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("anim_blueprint"), TEXT("Animation Blueprint asset path"))
			.Required(TEXT("graph_name"), TEXT("string"), TEXT("Graph containing the seed node"))
			.Required(TEXT("seed_node_ref"), TEXT("string"), TEXT("UObject name of the seed node"))
			.Optional(TEXT("direction"), TEXT("string"), TEXT("'upstream' or 'downstream' (default: downstream)"), TEXT("downstream"))
			.Optional(TEXT("stop_rules"), TEXT("object"), TEXT("Optional: {stop_at_node_names:[...], stop_at_node_classes:[...], max_nodes:N}"))
			.Optional(TEXT("dry_run"), TEXT("bool"), TEXT("Report only, no mutation (default: true)"), TEXT("true"))
			.Build());
}


// ===========================================================================
//  F12 — find_node_slice
// ===========================================================================

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleFindNodeSlice(const TSharedPtr<FJsonObject>& Params)
{
	const FString AssetPath = Params->GetStringField(TEXT("anim_blueprint"));
	const FString GraphName = Params->GetStringField(TEXT("graph_name"));
	const FString SeedRef = Params->GetStringField(TEXT("seed_node_ref"));
	FString DirectionStr = TEXT("downstream");
	Params->TryGetStringField(TEXT("direction"), DirectionStr);
	const bool bDownstream = !DirectionStr.Equals(TEXT("upstream"), ESearchCase::IgnoreCase);

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AssetPath));
	}

	FString GraphErr;
	UEdGraph* Graph = ResolveGraphByName(ABP, GraphName, GraphErr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(GraphErr);
	}

	UEdGraphNode* Seed = FindNodeByNameBP(ABP, SeedRef, Graph);
	if (!Seed)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Seed node '%s' not found in graph '%s'"), *SeedRef, *GraphName));
	}

	const FStopRules Rules = ParseStopRules(Params);
	TSet<UEdGraphNode*> Slice;
	CollectSlice(Seed, bDownstream, Rules, Slice);

	TArray<TSharedPtr<FJsonValue>> SliceArr;
	for (UEdGraphNode* Node : Slice)
	{
		if (!Node) continue;
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("node"), Node->GetName());
		Obj->SetStringField(TEXT("class"), Node->GetClass()->GetName());
		Obj->SetStringField(TEXT("title"), Node->GetNodeTitle(ENodeTitleType::ListView).ToString());
		SliceArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("anim_blueprint"), AssetPath);
	Root->SetStringField(TEXT("graph_name"), Graph->GetName());
	Root->SetStringField(TEXT("seed_node"), Seed->GetName());
	Root->SetStringField(TEXT("direction"), bDownstream ? TEXT("downstream") : TEXT("upstream"));
	Root->SetNumberField(TEXT("graph_node_count"), Graph->Nodes.Num());
	Root->SetNumberField(TEXT("slice_node_count"), Slice.Num());
	Root->SetNumberField(TEXT("node_count_after_removal"), Graph->Nodes.Num() - Slice.Num());
	Root->SetArrayField(TEXT("slice"), SliceArr);
	Root->SetArrayField(TEXT("orphaned_pins"), ComputeOrphanedPins(Slice));
	return FMonolithActionResult::Success(Root);
}


// ===========================================================================
//  F12 — remove_node_slice
// ===========================================================================

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleRemoveNodeSlice(const TSharedPtr<FJsonObject>& Params)
{
	const FString AssetPath = Params->GetStringField(TEXT("anim_blueprint"));
	const FString GraphName = Params->GetStringField(TEXT("graph_name"));
	const FString SeedRef = Params->GetStringField(TEXT("seed_node_ref"));
	FString DirectionStr = TEXT("downstream");
	Params->TryGetStringField(TEXT("direction"), DirectionStr);
	const bool bDownstream = !DirectionStr.Equals(TEXT("upstream"), ESearchCase::IgnoreCase);
	bool bDryRun = true;
	Params->TryGetBoolField(TEXT("dry_run"), bDryRun);

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AssetPath));
	}

	FString GraphErr;
	UEdGraph* Graph = ResolveGraphByName(ABP, GraphName, GraphErr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(GraphErr);
	}

	UEdGraphNode* Seed = FindNodeByNameBP(ABP, SeedRef, Graph);
	if (!Seed)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Seed node '%s' not found in graph '%s'"), *SeedRef, *GraphName));
	}

	const FStopRules Rules = ParseStopRules(Params);
	TSet<UEdGraphNode*> Slice;
	CollectSlice(Seed, bDownstream, Rules, Slice);

	const int32 CountBefore = Graph->Nodes.Num();

	// Capture orphaned pins + broken-exec continuity BEFORE removal (links are still intact).
	TArray<TSharedPtr<FJsonValue>> OrphanedPins = ComputeOrphanedPins(Slice);

	// Broken exec continuity: any exec link crossing the slice boundary is a severed exec path.
	TArray<TSharedPtr<FJsonValue>> BrokenExec;
	for (const TSharedPtr<FJsonValue>& V : OrphanedPins)
	{
		const TSharedPtr<FJsonObject>* Obj = nullptr;
		if (V->TryGetObject(Obj) && Obj && (*Obj)->HasField(TEXT("is_exec")))
		{
			bool bExec = false;
			(*Obj)->TryGetBoolField(TEXT("is_exec"), bExec);
			if (bExec)
			{
				BrokenExec.Add(V);
			}
		}
	}

	TArray<TSharedPtr<FJsonValue>> RemovedArr;
	for (UEdGraphNode* Node : Slice)
	{
		if (Node)
		{
			RemovedArr.Add(MakeShared<FJsonValueString>(Node->GetName()));
		}
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("anim_blueprint"), AssetPath);
	Root->SetStringField(TEXT("graph_name"), Graph->GetName());
	Root->SetStringField(TEXT("seed_node"), Seed->GetName());
	Root->SetStringField(TEXT("direction"), bDownstream ? TEXT("downstream") : TEXT("upstream"));
	Root->SetBoolField(TEXT("dry_run"), bDryRun);
	Root->SetNumberField(TEXT("node_count_before"), CountBefore);
	Root->SetNumberField(TEXT("slice_node_count"), Slice.Num());
	Root->SetArrayField(TEXT("removed_nodes"), RemovedArr);
	Root->SetArrayField(TEXT("orphaned_pins"), OrphanedPins);
	Root->SetArrayField(TEXT("broken_exec_continuity"), BrokenExec);
	if (BrokenExec.Num() > 0)
	{
		Root->SetStringField(TEXT("warning"), TEXT("Removing this slice severs required exec continuity at the listed pins. These are surfaced, not auto-rewired — wire them manually if the graph must remain executable."));
	}

	if (bDryRun)
	{
		Root->SetNumberField(TEXT("node_count_after"), CountBefore - Slice.Num());
		Root->SetBoolField(TEXT("removed"), false);
		return FMonolithActionResult::Success(Root);
	}

	// Mutate: RemoveNode breaks all links by default.
	int32 RemovedCount = 0;
	for (UEdGraphNode* Node : Slice)
	{
		if (Node && IsValid(Node))
		{
			Node->BreakAllNodeLinks();
			if (Graph->RemoveNode(Node))
			{
				++RemovedCount;
			}
		}
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	const bool bCompileOk = CompileWithHarvest(ABP, Root);

	Root->SetNumberField(TEXT("removed_count"), RemovedCount);
	Root->SetNumberField(TEXT("node_count_after"), Graph->Nodes.Num());
	Root->SetBoolField(TEXT("removed"), true);
	Root->SetBoolField(TEXT("compile_ok"), bCompileOk);
	Root->SetBoolField(TEXT("saved"), false); // saving is the caller's concern (editor.save_packages)
	return FMonolithActionResult::Success(Root);
}


// ===========================================================================
//  F11 — duplicate_reparent_and_sanitize
// ===========================================================================

namespace
{

/** Resolve an AnimInstance-derived parent class from a name or path. */
UClass* ResolveParentClass(const FString& Spec, FString& OutError)
{
	UClass* Cls = nullptr;

	// Full /Script or /Game path (BlueprintGeneratedClass paths end in _C).
	if (Spec.Contains(TEXT("/")))
	{
		Cls = LoadObject<UClass>(nullptr, *Spec);
	}

	if (!Cls)
	{
		FString CleanName = Spec;
		if (CleanName.StartsWith(TEXT("U")) || CleanName.StartsWith(TEXT("A")))
		{
			// Try the prefix-stripped form first, then the literal.
			Cls = FindFirstObject<UClass>(*CleanName.Mid(1), EFindFirstObjectOptions::NativeFirst);
		}
		if (!Cls)
		{
			Cls = FindFirstObject<UClass>(*CleanName, EFindFirstObjectOptions::NativeFirst);
		}
	}

	if (!Cls)
	{
		OutError = FString::Printf(TEXT("Parent class '%s' not found"), *Spec);
		return nullptr;
	}
	return Cls;
}

/** True if NewParent (or its CDO property set) exposes a property/function with the given name. */
bool ParentHasMember(UClass* NewParent, const FName MemberName)
{
	if (!NewParent) return false;
	if (FindFProperty<FProperty>(NewParent, MemberName)) return true;
	if (NewParent->FindFunctionByName(MemberName)) return true;
	return false;
}

/** True if the variable is defined locally on the duplicate (retained across reparent). */
bool VarDefinedLocally(UBlueprint* BP, const FName VarName)
{
	if (!BP) return false;
	for (const FBPVariableDescription& V : BP->NewVariables)
		if (V.VarName == VarName) return true;
	if (UClass* GC = BP->SkeletonGeneratedClass ? BP->SkeletonGeneratedClass : BP->GeneratedClass)
		if (FindFProperty<FProperty>(GC, VarName)) return true;
	return false;
}

/** Classify one node against the new parent's reflected surface. */
void ClassifyNode(UEdGraphNode* Node, const FString& GraphName, UClass* NewParent, UBlueprint* WorkingBP,
#if WITH_CHOOSER
	UClass* EvalChooserClass,
#endif
	FClassification& Out)
{
	Out.NodeName = Node->GetName();
	Out.GraphName = GraphName;
	Out.NodeClass = Node->GetClass()->GetName();
	Out.Label = TEXT("safe");
	Out.Reason = TEXT("No inherited-surface conflict detected against the new parent.");

#if WITH_CHOOSER
	if (IsEvaluateChooser2Node(Node, EvalChooserClass))
	{
		Out.Kind = TEXT("evaluate_chooser");
		Out.Label = TEXT("requires_rebuild");
		Out.Reason = TEXT("Evaluate-Chooser node context is tied to the old parent; rebuild against a parent-local chooser via animation.rebuild_evaluate_chooser_node.");
		return;
	}
#endif

	if (UK2Node_DynamicCast* CastNode = Cast<UK2Node_DynamicCast>(Node))
	{
		Out.Kind = TEXT("cast");
		UClass* Target = CastNode->TargetType;
		Out.Detail = Target ? Target->GetName() : TEXT("<null>");
		// A cast to a class the new parent is NOT compatible with becomes a guard-requiring chain.
		if (Target && NewParent && !NewParent->IsChildOf(Target) && !Target->IsChildOf(NewParent))
		{
			Out.Label = TEXT("requires_guard");
			Out.Reason = FString::Printf(TEXT("Cast target '%s' is unrelated to the new parent '%s'; the cast may fail at runtime and needs an IsValid guard."), *Out.Detail, *NewParent->GetName());
		}
		return;
	}

	if (UK2Node_VariableGet* VarNode = Cast<UK2Node_VariableGet>(Node))
	{
		Out.Kind = TEXT("variable_get");
		const FName VarName = VarNode->GetVarName();
		Out.Detail = VarName.ToString();
		// A self-context variable read whose name is absent on the new parent is a stale read.
		const bool bSelfContext = VarNode->VariableReference.IsSelfContext();
		if (bSelfContext && !ParentHasMember(NewParent, VarName) && !VarDefinedLocally(WorkingBP, VarName))
		{
			Out.Label = TEXT("requires_guard");
			Out.Reason = FString::Printf(TEXT("Variable '%s' is read from self but is not present on the new parent '%s'."), *Out.Detail, NewParent ? *NewParent->GetName() : TEXT("<null>"));
		}
		return;
	}

	if (UK2Node_CallFunction* CallNode = Cast<UK2Node_CallFunction>(Node))
	{
		Out.Kind = TEXT("function_call");
		const FName FuncName = CallNode->GetFunctionName();
		Out.Detail = FuncName.ToString();
		UFunction* Resolved = CallNode->GetTargetFunction();
		// Terminal sandbox-only chains (e.g. Compute_CenterScreenTrace) that resolve to nothing
		// on the new parent are flagged for smoke removal.
		if (!Resolved)
		{
			Out.Label = TEXT("remove_for_smoke");
			Out.Reason = FString::Printf(TEXT("Function '%s' does not resolve against the new parent surface; this is a stale terminal chain — remove for smoke via animation.remove_node_slice."), *Out.Detail);
		}
		return;
	}

	Out.Kind = TEXT("other");
}

} // anonymous namespace

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleDuplicateReparentAndSanitize(const TSharedPtr<FJsonObject>& Params)
{
	const FString SourcePath = Params->GetStringField(TEXT("source_abp"));
	const FString DestPath = Params->GetStringField(TEXT("destination_path"));
	const FString NewParentSpec = Params->GetStringField(TEXT("new_parent_class"));
	bool bDryRun = true;
	Params->TryGetBoolField(TEXT("dry_run"), bDryRun);

	UAnimBlueprint* SourceABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(SourcePath);
	if (!SourceABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Source Animation Blueprint not found: %s"), *SourcePath));
	}

	FString ParentErr;
	UClass* NewParent = ResolveParentClass(NewParentSpec, ParentErr);
	if (!NewParent)
	{
		return FMonolithActionResult::Error(ParentErr);
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("source_abp"), SourcePath);
	Root->SetStringField(TEXT("destination_path"), DestPath);
	Root->SetStringField(TEXT("new_parent_class"), NewParent->GetPathName());
	Root->SetBoolField(TEXT("dry_run"), bDryRun);

#if WITH_CHOOSER
	UClass* EvalChooserClass = ResolveEvaluateChooser2Class();
	Root->SetBoolField(TEXT("evaluate_chooser_class_resolved"), EvalChooserClass != nullptr);
#endif

	// In dry_run we classify against the SOURCE asset (no mutation, no duplicate created).
	// In non-dry_run we duplicate + reparent, then classify against the duplicate.
	UAnimBlueprint* WorkingABP = SourceABP;

	if (!bDryRun)
	{
		if (FMonolithAssetUtils::LoadAssetByPath<UObject>(DestPath))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Destination already exists: %s"), *DestPath));
		}
		UObject* Dup = UEditorAssetLibrary::DuplicateAsset(SourcePath, DestPath);
		UAnimBlueprint* DupABP = Cast<UAnimBlueprint>(Dup);
		if (!DupABP)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("DuplicateAsset failed: %s -> %s"), *SourcePath, *DestPath));
		}

		// Reparent (headless variant of FBlueprintEditor::ReparentBlueprint_NewParentChosen).
		DupABP->Modify();
		DupABP->ParentClass = NewParent;
		FBlueprintEditorUtils::RefreshAllNodes(DupABP);
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(DupABP);
		CompileWithHarvest(DupABP, Root); // populate bHasCompilerMessage before classifying
		WorkingABP = DupABP;
		Root->SetStringField(TEXT("duplicated_to"), DupABP->GetPathName());
	}

	// Walk every graph and classify.
	TArray<UEdGraph*> AllGraphs;
	GatherAllGraphs(WorkingABP, AllGraphs);

	int32 SafeN = 0, GuardN = 0, RebuildN = 0, RemoveN = 0;
	TArray<TSharedPtr<FJsonValue>> Findings;
	for (UEdGraph* Graph : AllGraphs)
	{
		if (!Graph) continue;
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (!Node) continue;
			FClassification C;
			ClassifyNode(Node, Graph->GetName(), NewParent, WorkingABP,
#if WITH_CHOOSER
				EvalChooserClass,
#endif
				C);

			// Only surface non-trivial findings (cast/var/func/chooser) — skip "safe/other" noise.
			if (C.Kind == TEXT("other"))
			{
				continue;
			}

			if (C.Label == TEXT("requires_guard")) ++GuardN;
			else if (C.Label == TEXT("requires_rebuild")) ++RebuildN;
			else if (C.Label == TEXT("remove_for_smoke")) ++RemoveN;
			else ++SafeN;

			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			Obj->SetStringField(TEXT("node"), C.NodeName);
			Obj->SetStringField(TEXT("graph"), C.GraphName);
			Obj->SetStringField(TEXT("node_class"), C.NodeClass);
			Obj->SetStringField(TEXT("kind"), C.Kind);
			Obj->SetStringField(TEXT("detail"), C.Detail);
			Obj->SetStringField(TEXT("label"), C.Label);
			Obj->SetStringField(TEXT("reason"), C.Reason);
			Findings.Add(MakeShared<FJsonValueObject>(Obj));
		}
	}

	TSharedPtr<FJsonObject> Summary = MakeShared<FJsonObject>();
	Summary->SetNumberField(TEXT("safe"), SafeN);
	Summary->SetNumberField(TEXT("requires_guard"), GuardN);
	Summary->SetNumberField(TEXT("requires_rebuild"), RebuildN);
	Summary->SetNumberField(TEXT("remove_for_smoke"), RemoveN);
	Root->SetObjectField(TEXT("summary"), Summary);
	Root->SetArrayField(TEXT("findings"), Findings);
	Root->SetStringField(TEXT("classified_against"), bDryRun ? TEXT("source") : TEXT("duplicate"));
	return FMonolithActionResult::Success(Root);
}


// ===========================================================================
//  F10 — Evaluate-Chooser node surgery (reflective UK2Node_EvaluateChooser2)
// ===========================================================================

#if WITH_CHOOSER

namespace
{

/**
 * Shared reflective spawn of a UK2Node_EvaluateChooser2. NewObject<UK2Node>(Graph, EvalClass),
 * binds the Chooser FObjectProperty BEFORE pin generation (pin shape derives from the chooser
 * context), adds the node to the graph, then AllocateDefaultPins + PostPlacedNewNode + ReconstructNode.
 * Returns the spawned node or nullptr if the reflective set could not be performed. Used by both the
 * delete-and-rebuild path (RebuildOneChooserNode) and the spawn-fresh path (Pack B
 * add_evaluate_chooser_node) so the reflective logic lives in one place.
 */
UK2Node* SpawnEvaluateChooser2Node(UEdGraph* Graph, UClass* EvalClass, UObject* ChooserTable,
	int32 PosX, int32 PosY)
{
	if (!Graph || !EvalClass) return nullptr;

	FObjectProperty* ChooserProp = FindFProperty<FObjectProperty>(EvalClass, TEXT("Chooser"));
	if (!ChooserProp) return nullptr;

	UK2Node* Spawned = NewObject<UK2Node>(Graph, EvalClass, NAME_None, RF_Transactional);
	if (!Spawned) return nullptr;

	Graph->Modify();
	Graph->AddNode(Spawned, /*bUserAction=*/false, /*bSelectNewNode=*/false);
	Spawned->CreateNewGuid();
	Spawned->NodePosX = PosX;
	Spawned->NodePosY = PosY;

	// Bind the chooser BEFORE pin generation — pin shape (the 'Result' output type) derives
	// from the chooser's OutputObjectType. For a PoseSearchDatabase chooser, Result is a
	// UPoseSearchDatabase object pin, compatible with the MM node's 'Database' input.
	ChooserProp->SetObjectPropertyValue_InContainer(Spawned, ChooserTable);

	Spawned->AllocateDefaultPins();
	Spawned->PostPlacedNewNode(); // UEdGraphNode::PostPlacedNewNode() takes no args in UE 5.7
	Spawned->ReconstructNode();   // regenerate pins from the bound chooser context
	return Spawned;
}

/**
 * Core rebuild of one Evaluate-Chooser node. Captures the old node's external links, spawns a fresh
 * UK2Node_EvaluateChooser2 reflectively, binds the chooser, regenerates pins, reconnects type+name
 * compatible links, removes the old node. Reports reconnected + unreconnected links into OutEntry.
 *
 * Degrades gracefully: if the reflective spawn cannot produce a usable node, the old node is still
 * removed and a manual-recreate spec is emitted; bRebuilt is set false in that case.
 */
bool RebuildOneChooserNode(UBlueprint* /*BP*/, UEdGraph* Graph, UEdGraphNode* OldNode, UClass* EvalClass,
	UObject* ChooserTable, const TSharedPtr<FJsonObject>& OutEntry, bool& bRebuilt)
{
	bRebuilt = false;

	// Capture the old node's external links and pin spec for the manual-recreate fallback.
	TArray<FCapturedLink> Captured;
	CaptureExternalLinks(OldNode, Captured);

	TArray<TSharedPtr<FJsonValue>> OldPinsArr;
	for (UEdGraphPin* Pin : OldNode->Pins)
	{
		OldPinsArr.Add(MakeShared<FJsonValueObject>(DescribePin(Pin)));
	}
	OutEntry->SetArrayField(TEXT("old_pins"), OldPinsArr);

	// Spawn the new node reflectively (shared helper — see SpawnEvaluateChooser2Node).
	UEdGraphNode* NewNode = SpawnEvaluateChooser2Node(Graph, EvalClass, ChooserTable,
		OldNode->NodePosX, OldNode->NodePosY);

	if (NewNode)
	{
		// Reconnect name + type compatible links. After ReconstructNode the old pin pointers
		// on OldNode are still valid (OldNode not yet removed); new pins are re-resolved by name.
		int32 Reconnected = 0;
		TArray<TSharedPtr<FJsonValue>> Unreconnected;
		// Defer to the schema's connection logic so it coerces wildcard/Knot (reroute) pin types
		// instead of failing on a strict PinType equality check.
		const UEdGraphSchema* Schema = Graph->GetSchema();
		for (const FCapturedLink& Cap : Captured)
		{
			UEdGraphPin* NewPin = FindPinByNameDir(NewNode, Cap.PinName, Cap.Direction);
			UEdGraphPin* OtherPin = (Cap.OtherNode && IsValid(Cap.OtherNode))
				? FindPinByNameDir(Cap.OtherNode, Cap.OtherPinName,
					Cap.Direction == EGPD_Input ? EGPD_Output : EGPD_Input)
				: nullptr;

			bool bConnected = false;
			FString DisallowReason;
			if (NewPin && OtherPin && Schema)
			{
				const FPinConnectionResponse Resp = Schema->CanCreateConnection(NewPin, OtherPin);
				if (Resp.Response != CONNECT_RESPONSE_DISALLOW)
				{
					Schema->TryCreateConnection(NewPin, OtherPin);
					bConnected = true;
				}
				else
				{
					DisallowReason = Resp.Message.ToString();
				}
			}

			if (bConnected)
			{
				++Reconnected;
			}
			else
			{
				TSharedPtr<FJsonObject> U = MakeShared<FJsonObject>();
				U->SetStringField(TEXT("pin"), Cap.PinName.ToString());
				U->SetStringField(TEXT("remote_node"), Cap.OtherNode ? Cap.OtherNode->GetName() : TEXT("<gone>"));
				U->SetStringField(TEXT("remote_pin"), Cap.OtherPinName.ToString());
				U->SetStringField(TEXT("reason"), !NewPin ? TEXT("pin absent on rebuilt node")
					: (!OtherPin ? TEXT("remote pin not found")
						: (!DisallowReason.IsEmpty() ? DisallowReason : TEXT("schema disallowed connection"))));
				Unreconnected.Add(MakeShared<FJsonValueObject>(U));
			}
		}

		// Remove the old node (breaks its links by default).
		OldNode->BreakAllNodeLinks();
		Graph->RemoveNode(OldNode);

		OutEntry->SetStringField(TEXT("new_node"), NewNode->GetName());
		OutEntry->SetNumberField(TEXT("reconnected"), Reconnected);
		OutEntry->SetArrayField(TEXT("unreconnected"), Unreconnected);
		bRebuilt = true;
		return true;
	}

	// ---- DEGRADED FALLBACK ----
	// Reflective spawn failed. Remove the stale node and emit a precise manual-recreate spec.
	TArray<TSharedPtr<FJsonValue>> ManualLinks;
	for (const FCapturedLink& Cap : Captured)
	{
		TSharedPtr<FJsonObject> L = MakeShared<FJsonObject>();
		L->SetStringField(TEXT("pin"), Cap.PinName.ToString());
		L->SetStringField(TEXT("direction"), Cap.Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
		L->SetStringField(TEXT("remote_node"), Cap.OtherNode ? Cap.OtherNode->GetName() : TEXT("<gone>"));
		L->SetStringField(TEXT("remote_pin"), Cap.OtherPinName.ToString());
		ManualLinks.Add(MakeShared<FJsonValueObject>(L));
	}

	OldNode->BreakAllNodeLinks();
	Graph->RemoveNode(OldNode);

	TSharedPtr<FJsonObject> ManualSpec = MakeShared<FJsonObject>();
	ManualSpec->SetStringField(TEXT("instruction"), TEXT("Reflective UK2Node_EvaluateChooser2 spawn unavailable. Stale node removed. Manually add an Evaluate Chooser node, bind the chooser below, then re-wire the listed pins."));
	ManualSpec->SetStringField(TEXT("graph"), Graph->GetName());
	ManualSpec->SetStringField(TEXT("chooser_asset"), ChooserTable ? ChooserTable->GetPathName() : TEXT("<none>"));
	ManualSpec->SetArrayField(TEXT("pins_to_rewire"), ManualLinks);
	OutEntry->SetObjectField(TEXT("manual_recreate_spec"), ManualSpec);
	OutEntry->SetStringField(TEXT("degraded"), TEXT("Reflective rebuild could not complete; degraded to detect-and-remove + manual spec."));
	return true; // the removal path still succeeded
}

} // anonymous namespace


FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleRebuildEvaluateChooserNode(const TSharedPtr<FJsonObject>& Params)
{
	const FString AssetPath = Params->GetStringField(TEXT("anim_blueprint"));
	const FString GraphName = Params->GetStringField(TEXT("graph_name"));
	const FString NodeRef = Params->GetStringField(TEXT("node_ref"));
	const FString ChooserPath = Params->GetStringField(TEXT("chooser_asset"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AssetPath));
	}

	UClass* EvalClass = ResolveEvaluateChooser2Class();
	if (!EvalClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not resolve Evaluate-Chooser node class at '%s'. Is the Chooser plugin enabled and loaded?"),
			EvaluateChooser2ClassPath));
	}

	UChooserTable* Chooser = FMonolithAssetUtils::LoadAssetByPath<UChooserTable>(ChooserPath);
	if (!Chooser)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Chooser table not found: %s"), *ChooserPath));
	}

	FString GraphErr;
	UEdGraph* Graph = ResolveGraphByName(ABP, GraphName, GraphErr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(GraphErr);
	}

	UEdGraphNode* OldNode = FindNodeByNameBP(ABP, NodeRef, Graph);
	if (!OldNode)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node '%s' not found in graph '%s'"), *NodeRef, *GraphName));
	}
	if (!IsEvaluateChooser2Node(OldNode, EvalClass))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Node '%s' is a %s, not an Evaluate-Chooser (v2) node"), *NodeRef, *OldNode->GetClass()->GetName()));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("anim_blueprint"), AssetPath);
	Root->SetStringField(TEXT("graph_name"), Graph->GetName());
	Root->SetStringField(TEXT("node_ref"), NodeRef);
	Root->SetStringField(TEXT("chooser_asset"), Chooser->GetPathName());
	Root->SetStringField(TEXT("resolved_node_class"), EvalClass->GetPathName());

	bool bRebuilt = false;
	RebuildOneChooserNode(ABP, Graph, OldNode, EvalClass, Chooser, Root, bRebuilt);

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	const bool bCompileOk = CompileWithHarvest(ABP, Root);

	Root->SetBoolField(TEXT("rebuilt"), bRebuilt);
	Root->SetBoolField(TEXT("compile_ok"), bCompileOk);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}


FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleReplaceEvaluateChooserNodes(const TSharedPtr<FJsonObject>& Params)
{
	const FString AssetPath = Params->GetStringField(TEXT("anim_blueprint"));
	bool bDryRun = true;
	Params->TryGetBoolField(TEXT("dry_run"), bDryRun);

	const TArray<TSharedPtr<FJsonValue>>* Replacements = nullptr;
	if (!Params->TryGetArrayField(TEXT("replacements"), Replacements) || !Replacements)
	{
		return FMonolithActionResult::Error(TEXT("replacements array is required"));
	}

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AssetPath));
	}

	UClass* EvalClass = ResolveEvaluateChooser2Class();
	if (!EvalClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not resolve Evaluate-Chooser node class at '%s'. Is the Chooser plugin enabled and loaded?"),
			EvaluateChooser2ClassPath));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("anim_blueprint"), AssetPath);
	Root->SetBoolField(TEXT("dry_run"), bDryRun);
	Root->SetStringField(TEXT("resolved_node_class"), EvalClass->GetPathName());

	TArray<TSharedPtr<FJsonValue>> Results;
	int32 Rebuilt = 0, Degraded = 0, Failed = 0;

	for (const TSharedPtr<FJsonValue>& V : *Replacements)
	{
		const TSharedPtr<FJsonObject>* EntryPtr = nullptr;
		if (!V->TryGetObject(EntryPtr) || !EntryPtr)
		{
			continue;
		}
		const TSharedPtr<FJsonObject>& Entry = *EntryPtr;

		FString GraphName, NodeRef, ChooserPath;
		Entry->TryGetStringField(TEXT("graph_name"), GraphName);
		Entry->TryGetStringField(TEXT("node_ref"), NodeRef);
		Entry->TryGetStringField(TEXT("chooser_asset"), ChooserPath);

		TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
		Out->SetStringField(TEXT("graph_name"), GraphName);
		Out->SetStringField(TEXT("node_ref"), NodeRef);
		Out->SetStringField(TEXT("chooser_asset"), ChooserPath);

		FString GraphErr;
		UEdGraph* Graph = ResolveGraphByName(ABP, GraphName, GraphErr);
		if (!Graph)
		{
			Out->SetStringField(TEXT("error"), GraphErr);
			++Failed;
			Results.Add(MakeShared<FJsonValueObject>(Out));
			continue;
		}

		UEdGraphNode* OldNode = FindNodeByNameBP(ABP, NodeRef, Graph);
		if (!OldNode || !IsEvaluateChooser2Node(OldNode, EvalClass))
		{
			Out->SetStringField(TEXT("error"), FString::Printf(TEXT("Node '%s' not found or not an Evaluate-Chooser node"), *NodeRef));
			++Failed;
			Results.Add(MakeShared<FJsonValueObject>(Out));
			continue;
		}

		UChooserTable* Chooser = FMonolithAssetUtils::LoadAssetByPath<UChooserTable>(ChooserPath);
		if (!Chooser)
		{
			Out->SetStringField(TEXT("error"), FString::Printf(TEXT("Chooser table not found: %s"), *ChooserPath));
			++Failed;
			Results.Add(MakeShared<FJsonValueObject>(Out));
			continue;
		}

		if (bDryRun)
		{
			Out->SetBoolField(TEXT("would_rebuild"), true);
			TArray<TSharedPtr<FJsonValue>> OldPinsArr;
			for (UEdGraphPin* Pin : OldNode->Pins)
			{
				OldPinsArr.Add(MakeShared<FJsonValueObject>(DescribePin(Pin)));
			}
			Out->SetArrayField(TEXT("old_pins"), OldPinsArr);
			Results.Add(MakeShared<FJsonValueObject>(Out));
			continue;
		}

		bool bRebuilt = false;
		RebuildOneChooserNode(ABP, Graph, OldNode, EvalClass, Chooser, Out, bRebuilt);
		if (bRebuilt) ++Rebuilt; else ++Degraded;
		Results.Add(MakeShared<FJsonValueObject>(Out));
	}

	Root->SetArrayField(TEXT("results"), Results);
	Root->SetNumberField(TEXT("rebuilt"), Rebuilt);
	Root->SetNumberField(TEXT("degraded"), Degraded);
	Root->SetNumberField(TEXT("failed"), Failed);

	if (!bDryRun && (Rebuilt + Degraded) > 0)
	{
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
		const bool bCompileOk = CompileWithHarvest(ABP, Root);
		Root->SetBoolField(TEXT("compile_ok"), bCompileOk);
	}
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}


// ===========================================================================
//  Pack B — add_evaluate_chooser_node (spawn-fresh, no-delete)
// ===========================================================================

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleAddEvaluateChooserNode(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath     = Params->GetStringField(TEXT("abp_path"));
	const FString ChooserPath = Params->GetStringField(TEXT("chooser_path"));
	FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	if (GraphName.IsEmpty()) GraphName = TEXT("AnimGraph");

	double TempVal;
	int32 PosX = 0, PosY = 0;
	if (Params->TryGetNumberField(TEXT("position_x"), TempVal)) PosX = static_cast<int32>(TempVal);
	if (Params->TryGetNumberField(TEXT("position_y"), TempVal)) PosY = static_cast<int32>(TempVal);

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AbpPath));
	}

	UClass* EvalClass = ResolveEvaluateChooser2Class();
	if (!EvalClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not resolve Evaluate-Chooser node class at '%s'. Is the Chooser plugin enabled and loaded?"),
			EvaluateChooser2ClassPath));
	}

	UChooserTable* Chooser = FMonolithAssetUtils::LoadAssetByPath<UChooserTable>(ChooserPath);
	if (!Chooser)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Chooser table not found: %s"), *ChooserPath));
	}

	FString GraphErr;
	UEdGraph* Graph = ResolveGraphByName(ABP, GraphName, GraphErr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(GraphErr);
	}

	// Spawn-fresh variant of RebuildOneChooserNode: reuse its reflective spawn helper, but with
	// no old node to capture/delete. The node binds the chooser and regenerates its pins; the
	// 'Result' output pin's type follows the chooser's OutputObjectType (PoseSearchDatabase here).
	UK2Node* NewNode = SpawnEvaluateChooser2Node(Graph, EvalClass, Chooser, PosX, PosY);
	if (!NewNode)
	{
		return FMonolithActionResult::Error(TEXT("Reflective UK2Node_EvaluateChooser2 spawn failed (no 'Chooser' FObjectProperty or node could not be created)."));
	}

	// Locate the output result pin. The Evaluate-Chooser v2 node names its primary output 'Result'
	// (EvaluateChooserNode.cpp:520). Prefer that by name; fall back to the first output data pin.
	UEdGraphPin* ResultPin = FindPinByNameDir(NewNode, FName(TEXT("Result")), EGPD_Output);
	if (!ResultPin)
	{
		for (UEdGraphPin* Pin : NewNode->Pins)
		{
			if (Pin && Pin->Direction == EGPD_Output
				&& Pin->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
			{
				ResultPin = Pin;
				break;
			}
		}
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("graph_name"), Graph->GetName());
	Root->SetStringField(TEXT("chooser_path"), Chooser->GetPathName());
	Root->SetStringField(TEXT("resolved_node_class"), EvalClass->GetPathName());
	Root->SetStringField(TEXT("node_name"), NewNode->GetName());
	Root->SetStringField(TEXT("result_pin"), ResultPin ? ResultPin->PinName.ToString() : FString());
	Root->SetBoolField(TEXT("result_pin_found"), ResultPin != nullptr);

	TArray<TSharedPtr<FJsonValue>> PinArr;
	for (UEdGraphPin* Pin : NewNode->Pins)
	{
		PinArr.Add(MakeShared<FJsonValueObject>(DescribePin(Pin)));
	}
	Root->SetArrayField(TEXT("pins"), PinArr);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}


// ===========================================================================
//  Pack B — wire_chooser_to_motion_matching
// ===========================================================================

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleWireChooserToMotionMatching(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath        = Params->GetStringField(TEXT("abp_path"));
	const FString ChooserNodeRef = Params->GetStringField(TEXT("chooser_node"));
	const FString MMNodeRef      = Params->GetStringField(TEXT("mm_node"));
	FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	if (GraphName.IsEmpty()) GraphName = TEXT("AnimGraph");

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AbpPath));
	}

	FString GraphErr;
	UEdGraph* Graph = ResolveGraphByName(ABP, GraphName, GraphErr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(GraphErr);
	}

	UEdGraphNode* ChooserNode = FindNodeByNameBP(ABP, ChooserNodeRef, Graph);
	if (!ChooserNode)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Chooser node '%s' not found in graph '%s'"), *ChooserNodeRef, *GraphName));
	}
	UEdGraphNode* MMNode = FindNodeByNameBP(ABP, MMNodeRef, Graph);
	if (!MMNode)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Motion Matching node '%s' not found in graph '%s'"), *MMNodeRef, *GraphName));
	}

	// Chooser side: the 'Result' output (PoseSearchDatabase for a DB chooser). Fall back to the
	// first non-exec output pin.
	UEdGraphPin* SourcePin = FindPinByNameDir(ChooserNode, FName(TEXT("Result")), EGPD_Output);
	if (!SourcePin)
	{
		for (UEdGraphPin* Pin : ChooserNode->Pins)
		{
			if (Pin && Pin->Direction == EGPD_Output
				&& Pin->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
			{
				SourcePin = Pin;
				break;
			}
		}
	}
	if (!SourcePin)
	{
		return FMonolithActionResult::Error(TEXT("Chooser node has no output result pin to wire"));
	}

	// MM side: the FAnimNode_MotionMatching 'Database' property is UPROPERTY(meta=(PinShownByDefault)),
	// so the input pin is named 'Database' (AnimNode_MotionMatching.h:110-111). Verified.
	UEdGraphPin* TargetPin = FindPinByNameDir(MMNode, FName(TEXT("Database")), EGPD_Input);
	if (!TargetPin)
	{
		return FMonolithActionResult::Error(TEXT("Motion Matching node has no 'Database' input pin. Ensure the node is a UAnimGraphNode_MotionMatching with the Database pin shown."));
	}

	const UEdGraphSchema* Schema = Graph->GetSchema();
	if (!Schema)
	{
		return FMonolithActionResult::Error(TEXT("Graph has no schema"));
	}

	const FPinConnectionResponse Resp = Schema->CanCreateConnection(SourcePin, TargetPin);
	if (Resp.Response == CONNECT_RESPONSE_DISALLOW)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Schema disallowed Result -> Database connection: %s"), *Resp.Message.ToString()));
	}

	Graph->Modify();
	ChooserNode->Modify();
	MMNode->Modify();
	const bool bConnected = Schema->TryCreateConnection(SourcePin, TargetPin);

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("graph_name"), Graph->GetName());
	Root->SetStringField(TEXT("chooser_node"), ChooserNode->GetName());
	Root->SetStringField(TEXT("chooser_pin"), SourcePin->PinName.ToString());
	Root->SetStringField(TEXT("mm_node"), MMNode->GetName());
	Root->SetStringField(TEXT("mm_pin"), TargetPin->PinName.ToString());
	Root->SetBoolField(TEXT("connected"), bConnected);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}

// ===========================================================================
//  Pack B — bind_chooser_database_via_threadsafe (WORKING exec-driven pattern)
// ===========================================================================

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleBindChooserDatabaseViaThreadSafe(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath     = Params->GetStringField(TEXT("abp_path"));
	const FString ChooserPath = Params->GetStringField(TEXT("chooser_path"));
	const FString MMNodeRef   = Params->GetStringField(TEXT("mm_node"));
	const FString DbVar       = Params->GetStringField(TEXT("selected_database_var"));
	FString FuncName = Params->HasField(TEXT("function_name")) ? Params->GetStringField(TEXT("function_name")) : TEXT("SelectLocomotionDatabase");
	if (FuncName.IsEmpty()) FuncName = TEXT("SelectLocomotionDatabase");
	FString AnimGraphName = Params->HasField(TEXT("anim_graph_name")) ? Params->GetStringField(TEXT("anim_graph_name")) : TEXT("AnimGraph");
	if (AnimGraphName.IsEmpty()) AnimGraphName = TEXT("AnimGraph");

	if (DbVar.IsEmpty()) return FMonolithActionResult::Error(TEXT("selected_database_var is required"));
	if (MMNodeRef.IsEmpty()) return FMonolithActionResult::Error(TEXT("mm_node is required"));

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AbpPath));
	}

	UClass* EvalClass = ResolveEvaluateChooser2Class();
	if (!EvalClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not resolve Evaluate-Chooser node class at '%s'. Is the Chooser plugin enabled and loaded?"),
			EvaluateChooser2ClassPath));
	}

	UChooserTable* Chooser = FMonolithAssetUtils::LoadAssetByPath<UChooserTable>(ChooserPath);
	if (!Chooser)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Chooser table not found: %s"), *ChooserPath));
	}

	// --- 1) Ensure the thread-safe FUNCTION graph exists. ---
	UEdGraph* FuncGraph = nullptr;
	for (UEdGraph* G : ABP->FunctionGraphs)
	{
		if (G && G->GetName() == FuncName) { FuncGraph = G; break; }
	}
	bool bFuncCreated = false;
	if (!FuncGraph)
	{
		FuncGraph = FBlueprintEditorUtils::CreateNewGraph(
			ABP, FName(*FuncName), UEdGraph::StaticClass(), UEdGraphSchema_K2::StaticClass());
		if (!FuncGraph)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to create function graph: %s"), *FuncName));
		}
		FBlueprintEditorUtils::AddFunctionGraph<UClass>(ABP, FuncGraph, /*bIsUserCreated=*/true, /*SignatureFromObject=*/(UClass*)nullptr);
		bFuncCreated = true;
	}

	// Locate the function entry node and mark the function Thread Safe.
	UK2Node_FunctionEntry* EntryNode = nullptr;
	for (UEdGraphNode* Node : FuncGraph->Nodes)
	{
		EntryNode = Cast<UK2Node_FunctionEntry>(Node);
		if (EntryNode) break;
	}
	if (!EntryNode)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("No function entry node in graph '%s'"), *FuncName));
	}
	EntryNode->Modify();
	EntryNode->MetaData.bThreadSafe = true;

	// --- 2) Spawn the EvaluateChooser2 node inside the function graph (reuse shared helper). ---
	UK2Node* ChooserNode = SpawnEvaluateChooser2Node(FuncGraph, EvalClass, Chooser, 300, 0);
	if (!ChooserNode)
	{
		return FMonolithActionResult::Error(TEXT("Reflective UK2Node_EvaluateChooser2 spawn failed (no 'Chooser' FObjectProperty or node could not be created)."));
	}

	// Assert the chooser object is non-null (so the node is not pruned for an empty binding).
	if (FObjectProperty* ChooserProp = FindFProperty<FObjectProperty>(EvalClass, TEXT("Chooser")))
	{
		if (ChooserProp->GetObjectPropertyValue_InContainer(ChooserNode) == nullptr)
		{
			return FMonolithActionResult::Error(TEXT("Chooser binding is null after spawn — node would be pruned. Aborting."));
		}
	}

	const UEdGraphSchema* Schema = FuncGraph->GetSchema();
	if (!Schema) return FMonolithActionResult::Error(TEXT("Function graph has no schema"));

	// --- 3) Wire FunctionEntry exec -> chooser 'execute' input. ---
	int32 Wired = 0;
	UEdGraphPin* EntryThen = FindPinByNameDir(EntryNode, UEdGraphSchema_K2::PN_Then, EGPD_Output);
	UEdGraphPin* ChooserExecIn = FindPinByNameDir(ChooserNode, UEdGraphSchema_K2::PN_Execute, EGPD_Input);
	if (EntryThen && ChooserExecIn && Schema->TryCreateConnection(EntryThen, ChooserExecIn)) ++Wired;

	// --- 4) Context = self. Spawn a Self node and wire it to the chooser's context (object) input. ---
	//    The context input pin is named after the chooser's configured context class FName, so we
	//    locate it generically: the first NON-exec, NON-'Result' object/interface INPUT pin.
	UK2Node_Self* SelfNode = NewObject<UK2Node_Self>(FuncGraph);
	FuncGraph->AddNode(SelfNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
	SelfNode->CreateNewGuid();
	SelfNode->NodePosX = 100;
	SelfNode->NodePosY = 150;
	SelfNode->AllocateDefaultPins();
	UEdGraphPin* SelfOut = nullptr;
	for (UEdGraphPin* P : SelfNode->Pins)
	{
		if (P && P->Direction == EGPD_Output) { SelfOut = P; break; }
	}

	UEdGraphPin* ContextPin = nullptr;
	for (UEdGraphPin* P : ChooserNode->Pins)
	{
		if (!P || P->Direction != EGPD_Input) continue;
		if (P->PinType.PinCategory == UEdGraphSchema_K2::PC_Exec) continue;
		if (P->PinName == FName(TEXT("Result"))) continue;
		if (P->PinType.PinCategory == UEdGraphSchema_K2::PC_Object ||
			P->PinType.PinCategory == UEdGraphSchema_K2::PC_Interface)
		{
			ContextPin = P;
			break;
		}
	}
	FString ContextPinName;
	if (SelfOut && ContextPin)
	{
		ContextPinName = ContextPin->PinName.ToString();
		const FPinConnectionResponse Resp = Schema->CanCreateConnection(SelfOut, ContextPin);
		if (Resp.Response != CONNECT_RESPONSE_DISALLOW && Schema->TryCreateConnection(SelfOut, ContextPin)) ++Wired;
	}

	// --- 5) Spawn a VariableSet for the SelectedDatabase var; wire chooser.Result -> set value,
	//        chooser exec out -> set exec in. ---
	UK2Node_VariableSet* SetNode = NewObject<UK2Node_VariableSet>(FuncGraph);
	SetNode->VariableReference.SetSelfMember(FName(*DbVar));
	FuncGraph->AddNode(SetNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
	SetNode->CreateNewGuid();
	SetNode->NodePosX = 600;
	SetNode->NodePosY = 0;
	SetNode->AllocateDefaultPins();

	UEdGraphPin* ResultPin = FindPinByNameDir(ChooserNode, FName(TEXT("Result")), EGPD_Output);
	if (!ResultPin)
	{
		for (UEdGraphPin* P : ChooserNode->Pins)
		{
			if (P && P->Direction == EGPD_Output && P->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
			{ ResultPin = P; break; }
		}
	}
	// VariableSet value input pin is named after the variable.
	UEdGraphPin* SetValuePin = FindPinByNameDir(SetNode, FName(*DbVar), EGPD_Input);
	if (!SetValuePin)
	{
		for (UEdGraphPin* P : SetNode->Pins)
		{
			if (P && P->Direction == EGPD_Input && P->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
			{ SetValuePin = P; break; }
		}
	}
	bool bResultWired = false;
	if (ResultPin && SetValuePin)
	{
		const FPinConnectionResponse Resp = Schema->CanCreateConnection(ResultPin, SetValuePin);
		if (Resp.Response != CONNECT_RESPONSE_DISALLOW)
		{
			bResultWired = Schema->TryCreateConnection(ResultPin, SetValuePin);
			if (bResultWired) ++Wired;
		}
	}
	// chooser exec out -> set exec in.
	UEdGraphPin* ChooserExecOut = FindPinByNameDir(ChooserNode, UEdGraphSchema_K2::PN_Execute, EGPD_Output);
	UEdGraphPin* SetExecIn = FindPinByNameDir(SetNode, UEdGraphSchema_K2::PN_Execute, EGPD_Input);
	if (ChooserExecOut && SetExecIn && Schema->TryCreateConnection(ChooserExecOut, SetExecIn)) ++Wired;

	// --- 6) AnimGraph side: spawn a VariableGet of the var and feed the MM 'Database' pin. ---
	FString GraphErr;
	UEdGraph* AnimGraph = ResolveGraphByName(ABP, AnimGraphName, GraphErr);
	if (!AnimGraph)
	{
		return FMonolithActionResult::Error(GraphErr);
	}
	UEdGraphNode* MMNode = FindNodeByNameBP(ABP, MMNodeRef, AnimGraph);
	if (!MMNode)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Motion Matching node '%s' not found in graph '%s'"), *MMNodeRef, *AnimGraphName));
	}
	UEdGraphPin* DatabasePin = FindPinByNameDir(MMNode, FName(TEXT("Database")), EGPD_Input);
	if (!DatabasePin)
	{
		return FMonolithActionResult::Error(TEXT("Motion Matching node has no 'Database' input pin. Ensure the node is a UAnimGraphNode_MotionMatching with the Database pin shown."));
	}

	UK2Node_VariableGet* GetNode = NewObject<UK2Node_VariableGet>(AnimGraph);
	GetNode->VariableReference.SetSelfMember(FName(*DbVar));
	AnimGraph->AddNode(GetNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
	GetNode->CreateNewGuid();
	GetNode->NodePosX = MMNode->NodePosX - 250;
	GetNode->NodePosY = MMNode->NodePosY;
	GetNode->AllocateDefaultPins();

	UEdGraphPin* GetValuePin = FindPinByNameDir(GetNode, FName(*DbVar), EGPD_Output);
	if (!GetValuePin)
	{
		for (UEdGraphPin* P : GetNode->Pins)
		{
			if (P && P->Direction == EGPD_Output && P->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
			{ GetValuePin = P; break; }
		}
	}
	const UEdGraphSchema* AnimSchema = AnimGraph->GetSchema();
	bool bDbWired = false;
	FString DbWireError;
	if (GetValuePin && AnimSchema)
	{
		const FPinConnectionResponse Resp = AnimSchema->CanCreateConnection(GetValuePin, DatabasePin);
		if (Resp.Response != CONNECT_RESPONSE_DISALLOW)
		{
			bDbWired = AnimSchema->TryCreateConnection(GetValuePin, DatabasePin);
			if (bDbWired) ++Wired;
		}
		else
		{
			DbWireError = Resp.Message.ToString();
		}
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("function_name"), FuncName);
	Root->SetBoolField(TEXT("function_created"), bFuncCreated);
	Root->SetBoolField(TEXT("function_thread_safe"), EntryNode->MetaData.bThreadSafe);
	Root->SetStringField(TEXT("chooser_node"), ChooserNode->GetName());
	Root->SetStringField(TEXT("chooser_path"), Chooser->GetPathName());
	Root->SetStringField(TEXT("context_pin"), ContextPinName);
	Root->SetStringField(TEXT("set_node"), SetNode->GetName());
	Root->SetStringField(TEXT("get_node"), GetNode->GetName());
	Root->SetStringField(TEXT("mm_node"), MMNode->GetName());
	Root->SetStringField(TEXT("selected_database_var"), DbVar);
	Root->SetBoolField(TEXT("result_wired_to_var"), bResultWired);
	Root->SetBoolField(TEXT("database_pin_wired"), bDbWired);
	if (!DbWireError.IsEmpty()) Root->SetStringField(TEXT("database_wire_error"), DbWireError);
	Root->SetNumberField(TEXT("connections_made"), Wired);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}


#else // !WITH_CHOOSER

// Off-gate stubs: register cleanly, return a precise "not available" error rather than failing to link.

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleRebuildEvaluateChooserNode(const TSharedPtr<FJsonObject>& /*Params*/)
{
	return FMonolithActionResult::Error(TEXT("Chooser plugin not available (WITH_CHOOSER=0). Evaluate-Chooser node surgery is disabled in this build."));
}

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleReplaceEvaluateChooserNodes(const TSharedPtr<FJsonObject>& /*Params*/)
{
	return FMonolithActionResult::Error(TEXT("Chooser plugin not available (WITH_CHOOSER=0). Evaluate-Chooser node surgery is disabled in this build."));
}

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleAddEvaluateChooserNode(const TSharedPtr<FJsonObject>& /*Params*/)
{
	return FMonolithActionResult::Error(TEXT("Chooser plugin not available (WITH_CHOOSER=0). add_evaluate_chooser_node is disabled in this build."));
}

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleWireChooserToMotionMatching(const TSharedPtr<FJsonObject>& /*Params*/)
{
	return FMonolithActionResult::Error(TEXT("Chooser plugin not available (WITH_CHOOSER=0). wire_chooser_to_motion_matching is disabled in this build."));
}

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleBindChooserDatabaseViaThreadSafe(const TSharedPtr<FJsonObject>& /*Params*/)
{
	return FMonolithActionResult::Error(TEXT("Chooser plugin not available (WITH_CHOOSER=0). bind_chooser_database_via_threadsafe is disabled in this build."));
}

#endif // WITH_CHOOSER


// ===========================================================================
//  T1-L1 — bind_threadsafe_update_function
//
//  GENERALIZES HandleBindChooserDatabaseViaThreadSafe. Reuses the SAME thread-safe
//  function-graph surgery (CreateNewGraph/AddFunctionGraph, EntryNode->MetaData.bThreadSafe,
//  FunctionEntry exec -> node exec, Self -> context, node.Result -> VariableSet,
//  AnimGraph VariableGet -> target pin), but swaps the reflective UK2Node_EvaluateChooser2
//  spawn for a UK2Node_CallFunction bound via SetFromFunction(UFunction*).
//
//  NOT gated on WITH_CHOOSER: UK2Node_CallFunction is always available. The helper
//  functions (ResolveGraphByName / FindNodeByNameBP / FindPinByNameDir) live in the
//  always-compiled anonymous namespace at the top of this file.
// ===========================================================================

namespace
{

/**
 * Resolve a UClass from a /Script path, a BlueprintGeneratedClass path, or a bare short name.
 * Mirrors the established Monolith resolution order: TryFindTypeSlow (path or short name) ->
 * LoadClass (forces the owning module/asset to load) -> FindObject. Returns nullptr if unresolved.
 */
UClass* ResolveClassFlexible(const FString& ClassNameOrPath)
{
	if (ClassNameOrPath.IsEmpty()) return nullptr;

	// TryFindTypeSlow handles both a fully-qualified /Script/...Class path and a bare short name.
	if (UClass* Found = UClass::TryFindTypeSlow<UClass>(ClassNameOrPath))
	{
		return Found;
	}
	// Path form may need the owning module/package loaded first.
	if (ClassNameOrPath.Contains(TEXT(".")) || ClassNameOrPath.Contains(TEXT("/")))
	{
		if (UClass* Loaded = LoadClass<UObject>(nullptr, *ClassNameOrPath))
		{
			return Loaded;
		}
		if (UClass* Obj = FindObject<UClass>(nullptr, *ClassNameOrPath))
		{
			return Obj;
		}
	}
	return nullptr;
}

/**
 * v1a thread-safe-call guard. Mirrors UAnimGraphNode_CallFunction::ValidateFunction (AnimGraph,
 * AnimGraphNode_CallFunction.cpp:235-274) plus AreFunctionParamsValid: a function dropped into a
 * thread-safe anim-graph function call MUST be non-pure, BlueprintThreadSafe, Kismet-callable, not
 * internal-use-only, and carry NO return-parameter property. Returns false + a precise reason for
 * any rejection so unsupported signatures are reported, never silently mis-wired.
 */
bool ValidateThreadSafeCallTarget(const UFunction* Fn, FString& OutError)
{
	if (!Fn)
	{
		OutError = TEXT("function could not be resolved");
		return false;
	}
	if (!UEdGraphSchema_K2::CanUserKismetCallFunction(Fn))
	{
		OutError = FString::Printf(TEXT("function '%s' is not user-callable from a Blueprint (not BlueprintCallable / not Kismet-callable)"), *Fn->GetName());
		return false;
	}
	if (Fn->HasAnyFunctionFlags(FUNC_BlueprintPure))
	{
		OutError = FString::Printf(TEXT("function '%s' is BlueprintPure — pure functions have no exec pins and cannot be exec-driven in a thread-safe function graph (v1a requires an exec-callable function)"), *Fn->GetName());
		return false;
	}
	if (!FBlueprintEditorUtils::HasFunctionBlueprintThreadSafeMetaData(Fn))
	{
		OutError = FString::Printf(TEXT("function '%s' is not marked BlueprintThreadSafe — it cannot be called from BlueprintThreadSafeUpdateAnimation / a thread-safe function graph"), *Fn->GetName());
		return false;
	}
	if (Fn->HasMetaData(FBlueprintMetadata::MD_BlueprintInternalUseOnly))
	{
		OutError = FString::Printf(TEXT("function '%s' is BlueprintInternalUseOnly and cannot be wired by the user"), *Fn->GetName());
		return false;
	}
	// Anim-graph rule (AreFunctionParamsValid): return parameters are not processable in the anim graph.
	for (TFieldIterator<FProperty> It(Fn); It; ++It)
	{
		if (It->HasAnyPropertyFlags(CPF_ReturnParm))
		{
			OutError = FString::Printf(TEXT("function '%s' has a C++ return parameter — anim-graph thread-safe calls do not allow return params (use an out-param / output-pin signature)"), *Fn->GetName());
			return false;
		}
	}
	return true;
}

} // namespace

FMonolithActionResult FMonolithAbpGraphSurgeryActions::HandleBindThreadsafeUpdateFunction(const TSharedPtr<FJsonObject>& Params)
{
	const FString AbpPath = Params->GetStringField(TEXT("abp_path"));

	// function = { class, name }
	const TSharedPtr<FJsonObject>* FuncObjPtr = nullptr;
	if (!Params->TryGetObjectField(TEXT("function"), FuncObjPtr) || !FuncObjPtr || !FuncObjPtr->IsValid())
	{
		return FMonolithActionResult::Error(TEXT("function is required and must be an object { class, name }"));
	}
	const TSharedPtr<FJsonObject>& FuncObj = *FuncObjPtr;
	FString FuncClassName, FuncMethodName;
	FuncObj->TryGetStringField(TEXT("class"), FuncClassName);
	FuncObj->TryGetStringField(TEXT("name"), FuncMethodName);
	if (FuncClassName.IsEmpty() || FuncMethodName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("function.class and function.name are both required"));
	}

	// result_target = { var, [node], [pin] }
	const TSharedPtr<FJsonObject>* ResultObjPtr = nullptr;
	if (!Params->TryGetObjectField(TEXT("result_target"), ResultObjPtr) || !ResultObjPtr || !ResultObjPtr->IsValid())
	{
		return FMonolithActionResult::Error(TEXT("result_target is required and must be an object { var, [node], [pin] }"));
	}
	const TSharedPtr<FJsonObject>& ResultObj = *ResultObjPtr;
	FString ResultVar, TargetNodeRef, TargetPinName;
	ResultObj->TryGetStringField(TEXT("var"), ResultVar);
	ResultObj->TryGetStringField(TEXT("node"), TargetNodeRef);
	ResultObj->TryGetStringField(TEXT("pin"), TargetPinName);
	if (ResultVar.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("result_target.var is required (the self variable to store the call result into; it must already exist on the ABP)"));
	}

	FString FuncGraphName = Params->HasField(TEXT("function_name")) ? Params->GetStringField(TEXT("function_name")) : TEXT("ThreadSafeUpdateFunction");
	if (FuncGraphName.IsEmpty()) FuncGraphName = TEXT("ThreadSafeUpdateFunction");
	FString AnimGraphName = Params->HasField(TEXT("anim_graph_name")) ? Params->GetStringField(TEXT("anim_graph_name")) : TEXT("AnimGraph");
	if (AnimGraphName.IsEmpty()) AnimGraphName = TEXT("AnimGraph");

	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AbpPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Animation Blueprint not found: %s"), *AbpPath));
	}

	// --- 0) Resolve + validate the target UFunction (v1a known-signature guard). ---
	UClass* FuncClass = ResolveClassFlexible(FuncClassName);
	if (!FuncClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not resolve function class '%s' (tried path + short-name resolution). Provide a /Script/<Module>.<Class> path or a loaded class short name."), *FuncClassName));
	}
	UFunction* TargetFn = FuncClass->FindFunctionByName(FName(*FuncMethodName));
	if (!TargetFn)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Function '%s' not found on class '%s'."), *FuncMethodName, *FuncClass->GetName()));
	}
	FString GuardError;
	if (!ValidateThreadSafeCallTarget(TargetFn, GuardError))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Unsupported function signature for a thread-safe call: %s"), *GuardError));
	}

	// --- 1) Ensure the thread-safe FUNCTION graph exists. (Reused verbatim from the chooser path.) ---
	UEdGraph* FuncGraph = nullptr;
	for (UEdGraph* G : ABP->FunctionGraphs)
	{
		if (G && G->GetName() == FuncGraphName) { FuncGraph = G; break; }
	}
	bool bFuncCreated = false;
	if (!FuncGraph)
	{
		FuncGraph = FBlueprintEditorUtils::CreateNewGraph(
			ABP, FName(*FuncGraphName), UEdGraph::StaticClass(), UEdGraphSchema_K2::StaticClass());
		if (!FuncGraph)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to create function graph: %s"), *FuncGraphName));
		}
		FBlueprintEditorUtils::AddFunctionGraph<UClass>(ABP, FuncGraph, /*bIsUserCreated=*/true, /*SignatureFromObject=*/(UClass*)nullptr);
		bFuncCreated = true;
	}

	UK2Node_FunctionEntry* EntryNode = nullptr;
	for (UEdGraphNode* Node : FuncGraph->Nodes)
	{
		EntryNode = Cast<UK2Node_FunctionEntry>(Node);
		if (EntryNode) break;
	}
	if (!EntryNode)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No function entry node in graph '%s'"), *FuncGraphName));
	}
	EntryNode->Modify();
	EntryNode->MetaData.bThreadSafe = true;

	// --- 2) Spawn the UK2Node_CallFunction and bind it via SetFromFunction (DIVERGENCE from chooser:
	//        the reflective EvaluateChooser2 spawn is replaced by a standard CallFunction node). ---
	UK2Node_CallFunction* CallNode = NewObject<UK2Node_CallFunction>(FuncGraph);
	FuncGraph->AddNode(CallNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
	CallNode->CreateNewGuid();
	CallNode->NodePosX = 300;
	CallNode->NodePosY = 0;
	CallNode->SetFromFunction(TargetFn);
	CallNode->AllocateDefaultPins();

	const UEdGraphSchema* Schema = FuncGraph->GetSchema();
	if (!Schema) return FMonolithActionResult::Error(TEXT("Function graph has no schema"));

	// --- 3) Wire FunctionEntry exec -> call node exec input. ---
	int32 Wired = 0;
	UEdGraphPin* EntryThen = FindPinByNameDir(EntryNode, UEdGraphSchema_K2::PN_Then, EGPD_Output);
	UEdGraphPin* CallExecIn = FindPinByNameDir(CallNode, UEdGraphSchema_K2::PN_Execute, EGPD_Input);
	if (EntryThen && CallExecIn && Schema->TryCreateConnection(EntryThen, CallExecIn)) ++Wired;

	// --- 4) Self-context: if the call has a 'self' target pin (member function), feed it from a Self node
	//        so the call runs against the AnimInstance. BP-library statics expose no self pin (skipped). ---
	FString ContextPinName;
	bool bSelfWired = false;
	UEdGraphPin* SelfTargetPin = CallNode->FindPin(UEdGraphSchema_K2::PN_Self, EGPD_Input);
	if (SelfTargetPin && SelfTargetPin->LinkedTo.Num() == 0)
	{
		UK2Node_Self* SelfNode = NewObject<UK2Node_Self>(FuncGraph);
		FuncGraph->AddNode(SelfNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
		SelfNode->CreateNewGuid();
		SelfNode->NodePosX = 100;
		SelfNode->NodePosY = 150;
		SelfNode->AllocateDefaultPins();
		UEdGraphPin* SelfOut = nullptr;
		for (UEdGraphPin* P : SelfNode->Pins)
		{
			if (P && P->Direction == EGPD_Output) { SelfOut = P; break; }
		}
		if (SelfOut)
		{
			const FPinConnectionResponse Resp = Schema->CanCreateConnection(SelfOut, SelfTargetPin);
			if (Resp.Response != CONNECT_RESPONSE_DISALLOW && Schema->TryCreateConnection(SelfOut, SelfTargetPin))
			{
				bSelfWired = true;
				ContextPinName = SelfTargetPin->PinName.ToString();
				++Wired;
			}
		}
	}

	// --- 5) Apply the small fixed v1a arg_bindings set. {pin, value} sets a literal default;
	//        {pin, self:true} wires a Self node into an object/self input pin. Anything we cannot set
	//        (unknown pin, exec/output pin, non-literal-settable type) is REJECTED, not mis-wired. ---
	TArray<TSharedPtr<FJsonValue>> AppliedBindings;
	const TArray<TSharedPtr<FJsonValue>>* ArgBindings = nullptr;
	if (Params->TryGetArrayField(TEXT("arg_bindings"), ArgBindings) && ArgBindings)
	{
		for (const TSharedPtr<FJsonValue>& V : *ArgBindings)
		{
			const TSharedPtr<FJsonObject>* EntryPtr = nullptr;
			if (!V->TryGetObject(EntryPtr) || !EntryPtr)
			{
				return FMonolithActionResult::Error(TEXT("each arg_bindings entry must be an object { pin, value } or { pin, self }"));
			}
			const TSharedPtr<FJsonObject>& Entry = *EntryPtr;
			FString PinName;
			Entry->TryGetStringField(TEXT("pin"), PinName);
			if (PinName.IsEmpty())
			{
				return FMonolithActionResult::Error(TEXT("arg_bindings entry missing required 'pin'"));
			}
			UEdGraphPin* InPin = FindPinByNameDir(CallNode, FName(*PinName), EGPD_Input);
			if (!InPin)
			{
				return FMonolithActionResult::Error(FString::Printf(
					TEXT("arg_bindings pin '%s' is not an input pin on the call node '%s' — reject rather than mis-wire"), *PinName, *FuncMethodName));
			}
			if (InPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Exec)
			{
				return FMonolithActionResult::Error(FString::Printf(TEXT("arg_bindings pin '%s' is an exec pin — only data input pins are bindable"), *PinName));
			}

			bool bWantSelf = false;
			Entry->TryGetBoolField(TEXT("self"), bWantSelf);
			if (bWantSelf)
			{
				if (InPin->PinType.PinCategory != UEdGraphSchema_K2::PC_Object &&
					InPin->PinType.PinCategory != UEdGraphSchema_K2::PC_Interface)
				{
					return FMonolithActionResult::Error(FString::Printf(
						TEXT("arg_bindings pin '%s' has self:true but is not an object/interface pin — cannot wire Self"), *PinName));
				}
				UK2Node_Self* ArgSelf = NewObject<UK2Node_Self>(FuncGraph);
				FuncGraph->AddNode(ArgSelf, /*bUserAction=*/false, /*bSelectNewNode=*/false);
				ArgSelf->CreateNewGuid();
				ArgSelf->NodePosX = 100;
				ArgSelf->NodePosY = 300;
				ArgSelf->AllocateDefaultPins();
				UEdGraphPin* ArgSelfOut = nullptr;
				for (UEdGraphPin* P : ArgSelf->Pins)
				{
					if (P && P->Direction == EGPD_Output) { ArgSelfOut = P; break; }
				}
				if (!ArgSelfOut || !Schema->TryCreateConnection(ArgSelfOut, InPin))
				{
					return FMonolithActionResult::Error(FString::Printf(TEXT("failed to wire Self into arg pin '%s'"), *PinName));
				}
				++Wired;
			}
			else
			{
				FString LiteralValue;
				if (!Entry->TryGetStringField(TEXT("value"), LiteralValue))
				{
					return FMonolithActionResult::Error(FString::Printf(
						TEXT("arg_bindings pin '%s' has neither a 'value' literal nor 'self:true' — v1a binds literal defaults or self only"), *PinName));
				}
				// Literal default: only settable on a non-object data pin (object pins need a wire, not a default).
				if (InPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Object ||
					InPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Interface ||
					InPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Struct)
				{
					return FMonolithActionResult::Error(FString::Printf(
						TEXT("arg_bindings pin '%s' is an object/struct pin; v1a sets literal defaults only on scalar/string/enum pins (object inputs require a wire — use self:true or defer to v1b)"), *PinName));
				}
				Schema->TrySetDefaultValue(*InPin, LiteralValue);
				if (InPin->DefaultValue != LiteralValue && InPin->DefaultTextValue.ToString() != LiteralValue)
				{
					return FMonolithActionResult::Error(FString::Printf(
						TEXT("arg_bindings literal '%s' was rejected by pin '%s' (incompatible value for its type) — rejecting rather than mis-wiring"), *LiteralValue, *PinName));
				}
			}

			TSharedPtr<FJsonObject> AppliedEntry = MakeShared<FJsonObject>();
			AppliedEntry->SetStringField(TEXT("pin"), PinName);
			AppliedEntry->SetStringField(TEXT("mode"), bWantSelf ? TEXT("self") : TEXT("literal"));
			AppliedBindings.Add(MakeShared<FJsonValueObject>(AppliedEntry));
		}
	}

	// --- 6) Locate the call's single non-exec result OUTPUT pin. v1a requires exactly one. ---
	UEdGraphPin* ResultPin = nullptr;
	int32 OutputDataPins = 0;
	for (UEdGraphPin* P : CallNode->Pins)
	{
		if (!P || P->Direction != EGPD_Output) continue;
		if (P->PinType.PinCategory == UEdGraphSchema_K2::PC_Exec) continue;
		++OutputDataPins;
		if (!ResultPin) ResultPin = P;
	}
	if (OutputDataPins == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("function '%s' has no non-exec output pin to route into result_target.var — v1a requires a single result output"), *FuncMethodName));
	}
	if (OutputDataPins > 1)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("function '%s' has %d output pins; v1a supports a single result output only (multi-output binding is a v1b follow-on)"), *FuncMethodName, OutputDataPins));
	}

	// --- 7) VariableSet of result_target.var; wire call.Result -> set value, call exec out -> set exec in.
	//        (Reused verbatim from the chooser path.) ---
	UK2Node_VariableSet* SetNode = NewObject<UK2Node_VariableSet>(FuncGraph);
	SetNode->VariableReference.SetSelfMember(FName(*ResultVar));
	FuncGraph->AddNode(SetNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
	SetNode->CreateNewGuid();
	SetNode->NodePosX = 600;
	SetNode->NodePosY = 0;
	SetNode->AllocateDefaultPins();

	UEdGraphPin* SetValuePin = FindPinByNameDir(SetNode, FName(*ResultVar), EGPD_Input);
	if (!SetValuePin)
	{
		for (UEdGraphPin* P : SetNode->Pins)
		{
			if (P && P->Direction == EGPD_Input && P->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
			{ SetValuePin = P; break; }
		}
	}
	if (!SetValuePin)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("VariableSet for '%s' has no value input pin — does the variable exist on the ABP?"), *ResultVar));
	}
	bool bResultWired = false;
	{
		const FPinConnectionResponse Resp = Schema->CanCreateConnection(ResultPin, SetValuePin);
		if (Resp.Response == CONNECT_RESPONSE_DISALLOW)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("call result pin (type '%s') is incompatible with variable '%s': %s — reject rather than mis-wire"),
				*ResultPin->PinType.PinCategory.ToString(), *ResultVar, *Resp.Message.ToString()));
		}
		bResultWired = Schema->TryCreateConnection(ResultPin, SetValuePin);
		if (bResultWired) ++Wired;
	}
	UEdGraphPin* CallExecOut = FindPinByNameDir(CallNode, UEdGraphSchema_K2::PN_Then, EGPD_Output);
	UEdGraphPin* SetExecIn = FindPinByNameDir(SetNode, UEdGraphSchema_K2::PN_Execute, EGPD_Input);
	if (CallExecOut && SetExecIn && Schema->TryCreateConnection(CallExecOut, SetExecIn)) ++Wired;

	// --- 8) Optional AnimGraph side: feed result_target.node's input pin from a VariableGet of the var.
	//        (Reused verbatim from the chooser path; skipped when node/pin omitted.) ---
	bool bTargetWired = false;
	FString TargetWireError;
	FString ResolvedTargetNode, ResolvedTargetPin;
	if (!TargetNodeRef.IsEmpty() && !TargetPinName.IsEmpty())
	{
		FString GraphErr;
		UEdGraph* AnimGraph = ResolveGraphByName(ABP, AnimGraphName, GraphErr);
		if (!AnimGraph)
		{
			return FMonolithActionResult::Error(GraphErr);
		}
		UEdGraphNode* TargetNode = FindNodeByNameBP(ABP, TargetNodeRef, AnimGraph);
		if (!TargetNode)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("result_target.node '%s' not found in graph '%s'"), *TargetNodeRef, *AnimGraphName));
		}
		UEdGraphPin* TargetPin = FindPinByNameDir(TargetNode, FName(*TargetPinName), EGPD_Input);
		if (!TargetPin)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("result_target.pin '%s' is not an input pin on node '%s'"), *TargetPinName, *TargetNodeRef));
		}

		UK2Node_VariableGet* GetNode = NewObject<UK2Node_VariableGet>(AnimGraph);
		GetNode->VariableReference.SetSelfMember(FName(*ResultVar));
		AnimGraph->AddNode(GetNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
		GetNode->CreateNewGuid();
		GetNode->NodePosX = TargetNode->NodePosX - 250;
		GetNode->NodePosY = TargetNode->NodePosY;
		GetNode->AllocateDefaultPins();

		UEdGraphPin* GetValuePin = FindPinByNameDir(GetNode, FName(*ResultVar), EGPD_Output);
		if (!GetValuePin)
		{
			for (UEdGraphPin* P : GetNode->Pins)
			{
				if (P && P->Direction == EGPD_Output && P->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
				{ GetValuePin = P; break; }
			}
		}
		const UEdGraphSchema* AnimSchema = AnimGraph->GetSchema();
		if (GetValuePin && AnimSchema)
		{
			const FPinConnectionResponse Resp = AnimSchema->CanCreateConnection(GetValuePin, TargetPin);
			if (Resp.Response != CONNECT_RESPONSE_DISALLOW)
			{
				bTargetWired = AnimSchema->TryCreateConnection(GetValuePin, TargetPin);
				if (bTargetWired) ++Wired;
			}
			else
			{
				TargetWireError = Resp.Message.ToString();
			}
		}
		ResolvedTargetNode = TargetNode->GetName();
		ResolvedTargetPin = TargetPin->PinName.ToString();
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(ABP);
	ABP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("abp_path"), AbpPath);
	Root->SetStringField(TEXT("function_name"), FuncGraphName);
	Root->SetBoolField(TEXT("function_created"), bFuncCreated);
	Root->SetBoolField(TEXT("function_thread_safe"), EntryNode->MetaData.bThreadSafe);
	Root->SetStringField(TEXT("resolved_function"), TargetFn->GetPathName());
	Root->SetStringField(TEXT("call_node"), CallNode->GetName());
	Root->SetBoolField(TEXT("self_context_wired"), bSelfWired);
	if (!ContextPinName.IsEmpty()) Root->SetStringField(TEXT("context_pin"), ContextPinName);
	Root->SetArrayField(TEXT("arg_bindings_applied"), AppliedBindings);
	Root->SetStringField(TEXT("set_node"), SetNode->GetName());
	Root->SetStringField(TEXT("result_pin"), ResultPin->PinName.ToString());
	Root->SetStringField(TEXT("selected_result_var"), ResultVar);
	Root->SetBoolField(TEXT("result_wired_to_var"), bResultWired);
	if (!ResolvedTargetNode.IsEmpty())
	{
		Root->SetStringField(TEXT("target_node"), ResolvedTargetNode);
		Root->SetStringField(TEXT("target_pin"), ResolvedTargetPin);
		Root->SetBoolField(TEXT("target_pin_wired"), bTargetWired);
		if (!TargetWireError.IsEmpty()) Root->SetStringField(TEXT("target_wire_error"), TargetWireError);
	}
	Root->SetNumberField(TEXT("connections_made"), Wired);
	Root->SetBoolField(TEXT("saved"), false);
	return FMonolithActionResult::Success(Root);
}
