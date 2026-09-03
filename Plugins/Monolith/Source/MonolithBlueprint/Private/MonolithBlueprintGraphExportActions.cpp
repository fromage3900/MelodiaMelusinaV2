#include "MonolithBlueprintGraphExportActions.h"
#include "MonolithBlueprintInternal.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraphSchema_K2.h"
#include "EdGraphUtilities.h"
#include "K2Node_Variable.h"
#include "K2Node_DynamicCast.h"
#include "K2Node_SpawnActorFromClass.h"
#include "EdGraphNode_Comment.h"
#include "Misc/SecureHash.h"

// ============================================================
//  Registration
// ============================================================

void FMonolithBlueprintGraphExportActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("blueprint"), TEXT("export_graph"),
		TEXT("Export a Blueprint graph to JSON with full node data and a separate connections array. "
			"Output is compatible with build_blueprint_from_spec input format."),
		FMonolithActionHandler::CreateStatic(&HandleExportGraph),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Graph name (defaults to first event graph)"))
			.Optional(TEXT("include_hidden_pins"), TEXT("bool"),
				TEXT("Emit hidden pins in nodes[].pins[], each flagged \"hidden\": true. "
					"Default false. connections[] always includes edges on hidden pins, so "
					"enable this when every edge must resolve to a listed pin."),
				TEXT("false"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("get_graph_fingerprint"),
		TEXT("Stable hash of a graph's structure, for detecting whether it changed. "
			"Order- and layout-independent: nodes are keyed semantically (function+class, event name, "
			"variable name, macro, cast class) rather than by K2Node_*_NN instance name, so deleting "
			"and re-adding an identical node does NOT change the fingerprint. "
			"EXCLUDED from every mode: node instance names, NodeGuids, comment nodes, and pin ordering. "
			"Modes: 'topology' (nodes+edges), 'topology+defaults' (adds unconnected input pin defaults), "
			"'full' (adds node positions -- use only for 'did anything at all change', never for assertions)."),
		FMonolithActionHandler::CreateStatic(&HandleGetGraphFingerprint),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Graph name (defaults to first event graph)"))
			.Optional(TEXT("mode"), TEXT("string"),
				TEXT("'topology' | 'topology+defaults' | 'full'"), TEXT("topology"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("assert_graph_matches"),
		TEXT("Assert that a graph contains an expected set of nodes and connections. "
			"'spec' takes the exact shape export_graph emits, so the authoring loop is: wire it once, "
			"export_graph, trim to the interesting nodes, and use that trimmed payload as the assertion. "
			"Nodes are matched on the same semantic key as get_graph_fingerprint (an 'id' field, if present, "
			"is tried first). mode 'subset' (default) requires the spec's nodes/connections to be present and "
			"ignores everything else; 'exact' additionally forbids extras. "
			"spec.forbidden_nodes: [{class, function}] asserts ABSENCE -- use it to prove a replaced node is "
			"really gone (e.g. no OpenLevel CallFunction remains, no SetInputMode remains). "
			"A failed assertion returns SUCCESS with matched:false and the specific misses, not an MCP error, "
			"so callers should branch on matched rather than wrapping this in try/except."),
		FMonolithActionHandler::CreateStatic(&HandleAssertGraphMatches),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path"))
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Graph name (defaults to first event graph)"))
			.Required(TEXT("spec"), TEXT("object"),
				TEXT("An export_graph payload or a subset of one: {nodes:[], connections:[], forbidden_nodes:[]}"))
			.Optional(TEXT("mode"), TEXT("string"), TEXT("'subset' | 'exact'"), TEXT("subset"))
			.Optional(TEXT("ignore_defaults"), TEXT("bool"),
				TEXT("Skip pin default_value comparison for spec nodes"), TEXT("false"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("copy_nodes"),
		TEXT("Copy nodes from one graph to another using UE native T3D export/import. "
			"Internal connections are preserved; external connections are silently dropped. Node IDs change on copy."),
		FMonolithActionHandler::CreateStatic(&HandleCopyNodes),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("source_asset"), TEXT("Source Blueprint asset path"))
			.Optional(TEXT("source_graph"), TEXT("string"), TEXT("Source graph name (defaults to first event graph)"))
			.Required(TEXT("node_ids"), TEXT("array"), TEXT("Array of node ID strings to copy"))
			.RequiredAssetPath(TEXT("target_asset"), TEXT("Target Blueprint asset path"))
			.Optional(TEXT("target_graph"), TEXT("string"), TEXT("Target graph name (defaults to first event graph)"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("duplicate_graph"),
		TEXT("Duplicate a function or macro graph within the same Blueprint. "
			"Only works for function and macro graphs (not event graphs)."),
		FMonolithActionHandler::CreateStatic(&HandleDuplicateGraph),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path"))
			.Required(TEXT("graph_name"), TEXT("string"), TEXT("Name of the graph to duplicate"))
			.Required(TEXT("new_name"), TEXT("string"), TEXT("Name for the duplicated graph"))
			.Build());
}

// ============================================================
//  Helper: Extended node serialization for export
// ============================================================

namespace
{
	/**
	 * Extended version of SerializeNode that adds extra type-specific fields:
	 * variable_name for Get/Set nodes, cast_class for DynamicCast, etc.
	 */
	TSharedPtr<FJsonObject> SerializeNodeExtended(UEdGraphNode* Node, bool bIncludeHiddenPins = false)
	{
		// Start with the standard serialization
		TSharedPtr<FJsonObject> NObj = MonolithBlueprintInternal::SerializeNode(Node, bIncludeHiddenPins);

		// Add variable_name for variable Get/Set nodes
		if (UK2Node_Variable* VarNode = Cast<UK2Node_Variable>(Node))
		{
			FName VarName = VarNode->GetVarName();
			if (VarName != NAME_None)
			{
				NObj->SetStringField(TEXT("variable_name"), VarName.ToString());
			}
			if (VarNode->VariableReference.IsSelfContext())
			{
				NObj->SetBoolField(TEXT("is_self_context"), true);
			}
			else if (UClass* OwnerClass = VarNode->VariableReference.GetMemberParentClass())
			{
				NObj->SetStringField(TEXT("variable_class"), OwnerClass->GetName());
			}
		}

		// Add cast_class for DynamicCast nodes
		if (UK2Node_DynamicCast* CastNode = Cast<UK2Node_DynamicCast>(Node))
		{
			if (CastNode->TargetType)
			{
				NObj->SetStringField(TEXT("cast_class"), CastNode->TargetType->GetName());
			}
		}

		// Add actor_class for SpawnActorFromClass nodes
		if (UK2Node_SpawnActorFromClass* SpawnNode = Cast<UK2Node_SpawnActorFromClass>(Node))
		{
			UClass* SpawnClass = SpawnNode->GetClassToSpawn();
			if (SpawnClass)
			{
				NObj->SetStringField(TEXT("actor_class"), SpawnClass->GetName());
			}
		}

		// Add comment dimensions for comment nodes
		if (UEdGraphNode_Comment* CommentNode = Cast<UEdGraphNode_Comment>(Node))
		{
			NObj->SetNumberField(TEXT("comment_size_x"), CommentNode->NodeWidth);
			NObj->SetNumberField(TEXT("comment_size_y"), CommentNode->NodeHeight);
			// CommentColor is FLinearColor (float RGBA 0-1)
			NObj->SetStringField(TEXT("comment_color"),
				FString::Printf(TEXT("(%.3f,%.3f,%.3f,%.3f)"),
					CommentNode->CommentColor.R,
					CommentNode->CommentColor.G,
					CommentNode->CommentColor.B,
					CommentNode->CommentColor.A));
		}

		return NObj;
	}

	// ------------------------------------------------------------
	//  Canonical form shared by get_graph_fingerprint and assert_graph_matches.
	//
	//  Helpers carry a GraphExport prefix because this module builds as a unity
	//  blob -- see Docs/specs/SPEC_MonolithBlueprint.md, file-local helpers must
	//  have module-unique names.
	// ------------------------------------------------------------

	/** Comment nodes are pure annotation and never part of structural identity. */
	bool GraphExportIsStructuralNode(UEdGraphNode* Node)
	{
		return Node && !Node->IsA<UEdGraphNode_Comment>();
	}

	/**
	 * Semantic identity of a node, derived from the fields SerializeNodeExtended
	 * already emits.
	 *
	 * Deliberately NOT Node->GetName(): that yields K2Node_CallFunction_17, whose
	 * numeric suffix changes when an identical node is deleted and re-added. A
	 * fingerprint built on instance names would report a change where none exists
	 * semantically, and an assertion built on them would fail after any re-add --
	 * which is exactly the workflow this is meant to verify.
	 */
	FString GraphExportSemanticNodeKey(const TSharedPtr<FJsonObject>& NObj)
	{
		if (!NObj.IsValid()) return TEXT("<null>");

		const FString Class = NObj->GetStringField(TEXT("class"));
		FString Discriminator;
		FString Tmp;

		if (NObj->TryGetStringField(TEXT("function"), Tmp) && !Tmp.IsEmpty())
		{
			FString OwnerClass;
			NObj->TryGetStringField(TEXT("function_class"), OwnerClass);
			Discriminator = OwnerClass.IsEmpty() ? Tmp : (OwnerClass + TEXT("::") + Tmp);
		}
		else if (NObj->TryGetStringField(TEXT("custom_name"), Tmp) && !Tmp.IsEmpty())
		{
			Discriminator = Tmp;
		}
		else if (NObj->TryGetStringField(TEXT("event_name"), Tmp) && !Tmp.IsEmpty())
		{
			Discriminator = Tmp;
		}
		else if (NObj->TryGetStringField(TEXT("variable_name"), Tmp) && !Tmp.IsEmpty())
		{
			FString VarClass;
			NObj->TryGetStringField(TEXT("variable_class"), VarClass);
			Discriminator = VarClass.IsEmpty() ? Tmp : (VarClass + TEXT("::") + Tmp);
		}
		else if (NObj->TryGetStringField(TEXT("macro_name"), Tmp) && !Tmp.IsEmpty())
		{
			Discriminator = Tmp;
		}
		else if (NObj->TryGetStringField(TEXT("cast_class"), Tmp) && !Tmp.IsEmpty())
		{
			Discriminator = Tmp;
		}
		else if (NObj->TryGetStringField(TEXT("actor_class"), Tmp) && !Tmp.IsEmpty())
		{
			Discriminator = Tmp;
		}
		else if (NObj->TryGetStringField(TEXT("delegate_property_name"), Tmp) && !Tmp.IsEmpty())
		{
			Discriminator = Tmp;
		}
		else
		{
			// Last resort. Titles are stable for structural nodes (Branch, Sequence,
			// Return) which carry no other discriminator.
			NObj->TryGetStringField(TEXT("title"), Discriminator);
		}

		return Class + TEXT("|") + Discriminator;
	}

	/**
	 * Semantic keys can legitimately repeat -- two calls to the same function in
	 * one graph are indistinguishable by key alone. Appending an occurrence index
	 * keeps the canonical form injective while staying independent of instance
	 * names. Callers must feed nodes in a deterministic (sorted) order.
	 */
	FString GraphExportDisambiguate(const FString& Key, TMap<FString, int32>& Seen)
	{
		int32& Count = Seen.FindOrAdd(Key);
		const FString Result = (Count == 0) ? Key : FString::Printf(TEXT("%s#%d"), *Key, Count);
		++Count;
		return Result;
	}

	FString GraphExportHashLines(const TArray<FString>& Lines)
	{
		const FString Joined = FString::Join(Lines, TEXT("\n"));
		FTCHARToUTF8 Utf8(*Joined);
		uint8 Digest[20];
		FSHA1::HashBuffer(Utf8.Get(), Utf8.Length(), Digest);
		return BytesToHex(Digest, 20).ToLower();
	}
}

// ============================================================
//  export_graph
// ============================================================

FMonolithActionResult FMonolithBlueprintGraphExportActions::HandleExportGraph(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString GraphName = Params->GetStringField(TEXT("graph_name"));
	UEdGraph* Graph = MonolithBlueprintInternal::FindGraphByName(BP, GraphName);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph not found: %s"), *GraphName));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetNumberField(TEXT("format_version"), 1);
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("graph_name"), Graph->GetName());

	// Determine graph type
	FString GraphType = TEXT("unknown");
	if (BP->UbergraphPages.Contains(Graph)) GraphType = TEXT("event_graph");
	else if (BP->FunctionGraphs.Contains(Graph)) GraphType = TEXT("function");
	else if (BP->MacroGraphs.Contains(Graph)) GraphType = TEXT("macro");
	else if (BP->DelegateSignatureGraphs.Contains(Graph)) GraphType = TEXT("delegate_signature");
	Root->SetStringField(TEXT("graph_type"), GraphType);

	bool bIncludeHiddenPins = false;
	Params->TryGetBoolField(TEXT("include_hidden_pins"), bIncludeHiddenPins);
	Root->SetBoolField(TEXT("include_hidden_pins"), bIncludeHiddenPins);

	// Serialize all nodes with extended info
	TArray<TSharedPtr<FJsonValue>> NodesArr;
	for (UEdGraphNode* Node : Graph->Nodes)
	{
		if (!Node) continue;
		NodesArr.Add(MakeShared<FJsonValueObject>(SerializeNodeExtended(Node, bIncludeHiddenPins)));
	}
	Root->SetArrayField(TEXT("nodes"), NodesArr);

	// Build separate connections array (material pattern)
	// Format: {from_node, from_pin, to_node, to_pin}
	// Only output each connection once (from the output side)
	TArray<TSharedPtr<FJsonValue>> ConnectionsArr;
	for (UEdGraphNode* Node : Graph->Nodes)
	{
		if (!Node) continue;
		for (UEdGraphPin* Pin : Node->Pins)
		{
			if (!Pin || Pin->Direction != EGPD_Output) continue;
			for (UEdGraphPin* LinkedPin : Pin->LinkedTo)
			{
				if (!LinkedPin || !LinkedPin->GetOwningNode()) continue;
				TSharedPtr<FJsonObject> Conn = MakeShared<FJsonObject>();
				Conn->SetStringField(TEXT("from_node"), Node->GetName());
				Conn->SetStringField(TEXT("from_pin"), Pin->PinName.ToString());
				Conn->SetStringField(TEXT("to_node"), LinkedPin->GetOwningNode()->GetName());
				Conn->SetStringField(TEXT("to_pin"), LinkedPin->PinName.ToString());
				// Unambiguous alternative to the name pair, for graphs where a node
				// carries two pins of the same name.
				Conn->SetStringField(TEXT("from_pin_id"), Pin->PinId.ToString());
				Conn->SetStringField(TEXT("to_pin_id"), LinkedPin->PinId.ToString());
				// This loop deliberately does not filter hidden pins -- dropping those
				// edges would delete real connections (self-pins on self-context calls).
				// Flag them instead so a consumer can reconcile against nodes[].pins[].
				if (Pin->bHidden) Conn->SetBoolField(TEXT("from_pin_hidden"), true);
				if (LinkedPin->bHidden) Conn->SetBoolField(TEXT("to_pin_hidden"), true);
				ConnectionsArr.Add(MakeShared<FJsonValueObject>(Conn));
			}
		}
	}
	Root->SetArrayField(TEXT("connections"), ConnectionsArr);

	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  Canonical graph model (shared by fingerprint + assert)
// ============================================================

namespace
{
	struct FGraphExportEntry
	{
		UEdGraphNode* Node = nullptr;
		TSharedPtr<FJsonObject> Json;
		FString BaseKey;      // semantic identity; may repeat
		FString NeighborSig;  // content-derived tiebreak for repeats
		FString FinalKey;     // BaseKey plus occurrence index
	};

	/**
	 * Build the canonical, order-independent model of a live graph.
	 *
	 * Two passes because disambiguating repeated semantic keys needs every node's
	 * base key to already exist. The tiebreak is a neighbourhood signature -- the
	 * node's own links expressed in terms of its neighbours' base keys -- which is
	 * derived purely from content, never from node position or instance name. That
	 * is what keeps the fingerprint stable across a save, a reload, or a
	 * delete-and-re-add of an identical node.
	 */
	void GraphExportBuildEntries(UEdGraph* Graph, TArray<FGraphExportEntry>& Out)
	{
		TMap<UEdGraphNode*, FString> BaseKeys;

		for (UEdGraphNode* N : Graph->Nodes)
		{
			if (!GraphExportIsStructuralNode(N)) continue;
			FGraphExportEntry E;
			E.Node = N;
			// Hidden pins included: an edge on a hidden pin is a real edge and must
			// contribute to identity.
			E.Json = SerializeNodeExtended(N, /*bIncludeHiddenPins=*/true);
			E.BaseKey = GraphExportSemanticNodeKey(E.Json);
			BaseKeys.Add(N, E.BaseKey);
			Out.Add(MoveTemp(E));
		}

		for (FGraphExportEntry& E : Out)
		{
			TArray<FString> Parts;
			for (UEdGraphPin* Pin : E.Node->Pins)
			{
				if (!Pin) continue;
				for (UEdGraphPin* L : Pin->LinkedTo)
				{
					if (!L || !L->GetOwningNode()) continue;
					const FString* NK = BaseKeys.Find(L->GetOwningNode());
					Parts.Add(FString::Printf(TEXT("%s:%s>%s.%s"),
						Pin->Direction == EGPD_Output ? TEXT("out") : TEXT("in"),
						*Pin->PinName.ToString(),
						NK ? **NK : TEXT("<external>"),
						*L->PinName.ToString()));
				}
				if (Pin->LinkedTo.Num() == 0 && !Pin->DefaultValue.IsEmpty())
				{
					Parts.Add(FString::Printf(TEXT("def:%s=%s"),
						*Pin->PinName.ToString(), *Pin->DefaultValue));
				}
			}
			Parts.Sort();
			E.NeighborSig = FString::Join(Parts, TEXT(";"));
		}

		Out.Sort([](const FGraphExportEntry& A, const FGraphExportEntry& B)
		{
			if (!A.BaseKey.Equals(B.BaseKey)) return A.BaseKey < B.BaseKey;
			return A.NeighborSig < B.NeighborSig;
		});

		TMap<FString, int32> Seen;
		for (FGraphExportEntry& E : Out)
		{
			E.FinalKey = GraphExportDisambiguate(E.BaseKey, Seen);
		}
	}
}

// ============================================================
//  get_graph_fingerprint
// ============================================================

FMonolithActionResult FMonolithBlueprintGraphExportActions::HandleGetGraphFingerprint(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	const FString GraphName = Params->GetStringField(TEXT("graph_name"));
	UEdGraph* Graph = MonolithBlueprintInternal::FindGraphByName(BP, GraphName);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph not found: %s"), *GraphName));
	}

	FString Mode = Params->GetStringField(TEXT("mode"));
	if (Mode.IsEmpty()) Mode = TEXT("topology");
	if (Mode != TEXT("topology") && Mode != TEXT("topology+defaults") && Mode != TEXT("full"))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown mode '%s'. Expected 'topology', 'topology+defaults' or 'full'."), *Mode));
	}
	const bool bDefaults = (Mode == TEXT("topology+defaults") || Mode == TEXT("full"));
	const bool bPositions = (Mode == TEXT("full"));

	TArray<FGraphExportEntry> Entries;
	GraphExportBuildEntries(Graph, Entries);

	TMap<UEdGraphNode*, FString> KeyOf;
	TMap<FString, int32> ClassHistogram;
	for (const FGraphExportEntry& E : Entries)
	{
		KeyOf.Add(E.Node, E.FinalKey);
		ClassHistogram.FindOrAdd(E.Json->GetStringField(TEXT("class")))++;
	}

	TArray<FString> NodeLines;
	TArray<FString> EdgeLines;
	TArray<FString> DefaultLines;
	TArray<FString> PosLines;

	for (const FGraphExportEntry& E : Entries)
	{
		NodeLines.Add(TEXT("N ") + E.FinalKey);

		if (bPositions)
		{
			PosLines.Add(FString::Printf(TEXT("P %s@%d,%d"),
				*E.FinalKey, E.Node->NodePosX, E.Node->NodePosY));
		}

		for (UEdGraphPin* Pin : E.Node->Pins)
		{
			if (!Pin) continue;

			// Emit each edge once, from the output side, so the pair is not counted twice.
			if (Pin->Direction == EGPD_Output)
			{
				for (UEdGraphPin* L : Pin->LinkedTo)
				{
					if (!L || !L->GetOwningNode()) continue;
					const FString* ToKey = KeyOf.Find(L->GetOwningNode());
					EdgeLines.Add(FString::Printf(TEXT("E %s.%s>%s.%s"),
						*E.FinalKey, *Pin->PinName.ToString(),
						ToKey ? **ToKey : TEXT("<external>"), *L->PinName.ToString()));
				}
			}

			if (bDefaults && Pin->Direction == EGPD_Input && Pin->LinkedTo.Num() == 0)
			{
				if (!Pin->DefaultValue.IsEmpty())
				{
					DefaultLines.Add(FString::Printf(TEXT("D %s.%s=%s"),
						*E.FinalKey, *Pin->PinName.ToString(), *Pin->DefaultValue));
				}
				else if (Pin->DefaultObject)
				{
					DefaultLines.Add(FString::Printf(TEXT("D %s.%s=@%s"),
						*E.FinalKey, *Pin->PinName.ToString(), *Pin->DefaultObject->GetPathName()));
				}
			}
		}
	}

	NodeLines.Sort();
	EdgeLines.Sort();
	DefaultLines.Sort();
	PosLines.Sort();

	TArray<FString> All;
	All.Append(NodeLines);
	All.Append(EdgeLines);
	All.Append(DefaultLines);
	All.Append(PosLines);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("graph_name"), Graph->GetName());
	Root->SetStringField(TEXT("mode"), Mode);
	Root->SetNumberField(TEXT("node_count"), Entries.Num());
	Root->SetNumberField(TEXT("connection_count"), EdgeLines.Num());
	Root->SetStringField(TEXT("fingerprint"), GraphExportHashLines(All));

	TSharedPtr<FJsonObject> Hist = MakeShared<FJsonObject>();
	for (const TPair<FString, int32>& Pair : ClassHistogram)
	{
		Hist->SetNumberField(Pair.Key, Pair.Value);
	}
	Root->SetObjectField(TEXT("node_class_histogram"), Hist);

	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  assert_graph_matches
// ============================================================

FMonolithActionResult FMonolithBlueprintGraphExportActions::HandleAssertGraphMatches(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	const FString GraphName = Params->GetStringField(TEXT("graph_name"));
	UEdGraph* Graph = MonolithBlueprintInternal::FindGraphByName(BP, GraphName);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph not found: %s"), *GraphName));
	}

	const TSharedPtr<FJsonObject>* SpecPtr = nullptr;
	if (!Params->TryGetObjectField(TEXT("spec"), SpecPtr) || !SpecPtr || !SpecPtr->IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: spec (an export_graph payload or subset of one)"));
	}
	const TSharedPtr<FJsonObject>& Spec = *SpecPtr;

	FString Mode = Params->GetStringField(TEXT("mode"));
	if (Mode.IsEmpty()) Mode = TEXT("subset");
	if (Mode != TEXT("subset") && Mode != TEXT("exact"))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown mode '%s'. Expected 'subset' or 'exact'."), *Mode));
	}
	bool bIgnoreDefaults = false;
	Params->TryGetBoolField(TEXT("ignore_defaults"), bIgnoreDefaults);

	// --- Actual side ------------------------------------------------------
	TArray<FGraphExportEntry> Entries;
	GraphExportBuildEntries(Graph, Entries);

	TMap<UEdGraphNode*, FString> BaseKeyOf;
	TMultiMap<FString, const FGraphExportEntry*> ActualByBaseKey;
	for (const FGraphExportEntry& E : Entries)
	{
		BaseKeyOf.Add(E.Node, E.BaseKey);
		ActualByBaseKey.Add(E.BaseKey, &E);
	}

	// Edges in base-key space. Subset matching asks "does an edge of this shape
	// exist between a node of this kind and a node of that kind", which is the
	// question a runbook actually needs; instance identity is not asserted.
	TSet<FString> ActualEdges;
	for (const FGraphExportEntry& E : Entries)
	{
		for (UEdGraphPin* Pin : E.Node->Pins)
		{
			if (!Pin || Pin->Direction != EGPD_Output) continue;
			for (UEdGraphPin* L : Pin->LinkedTo)
			{
				if (!L || !L->GetOwningNode()) continue;
				const FString* ToKey = BaseKeyOf.Find(L->GetOwningNode());
				ActualEdges.Add(FString::Printf(TEXT("%s.%s>%s.%s"),
					*E.BaseKey, *Pin->PinName.ToString(),
					ToKey ? **ToKey : TEXT("<external>"), *L->PinName.ToString()));
			}
		}
	}

	// --- Spec side --------------------------------------------------------
	TMap<FString, FString> SpecIdToBaseKey;   // exported instance id -> semantic key
	TArray<FString> SpecBaseKeys;
	const TArray<TSharedPtr<FJsonValue>>* SpecNodes = nullptr;
	if (Spec->TryGetArrayField(TEXT("nodes"), SpecNodes) && SpecNodes)
	{
		for (const TSharedPtr<FJsonValue>& V : *SpecNodes)
		{
			const TSharedPtr<FJsonObject> NObj = V->AsObject();
			if (!NObj.IsValid()) continue;
			const FString Key = GraphExportSemanticNodeKey(NObj);
			SpecBaseKeys.Add(Key);
			FString Id;
			if (NObj->TryGetStringField(TEXT("id"), Id) && !Id.IsEmpty())
			{
				SpecIdToBaseKey.Add(Id, Key);
			}
		}
	}

	TArray<TSharedPtr<FJsonValue>> MissingNodes;
	TArray<TSharedPtr<FJsonValue>> PinDefaultMismatches;
	int32 MatchedNodes = 0;

	if (SpecNodes)
	{
		for (const TSharedPtr<FJsonValue>& V : *SpecNodes)
		{
			const TSharedPtr<FJsonObject> NObj = V->AsObject();
			if (!NObj.IsValid()) continue;
			const FString Key = GraphExportSemanticNodeKey(NObj);

			TArray<const FGraphExportEntry*> Candidates;
			ActualByBaseKey.MultiFind(Key, Candidates);
			if (Candidates.Num() == 0)
			{
				TSharedPtr<FJsonObject> Miss = MakeShared<FJsonObject>();
				Miss->SetStringField(TEXT("class"), NObj->GetStringField(TEXT("class")));
				Miss->SetStringField(TEXT("key"), Key);
				Miss->SetStringField(TEXT("why"), TEXT("no node with this semantic key exists in the graph"));
				MissingNodes.Add(MakeShared<FJsonValueObject>(Miss));
				continue;
			}
			++MatchedNodes;

			if (bIgnoreDefaults) continue;

			// Compare only pin defaults the spec actually states.
			const TArray<TSharedPtr<FJsonValue>>* SpecPins = nullptr;
			if (!NObj->TryGetArrayField(TEXT("pins"), SpecPins) || !SpecPins) continue;

			for (const TSharedPtr<FJsonValue>& PV : *SpecPins)
			{
				const TSharedPtr<FJsonObject> PObj = PV->AsObject();
				if (!PObj.IsValid()) continue;
				FString Expected;
				if (!PObj->TryGetStringField(TEXT("default_value"), Expected) || Expected.IsEmpty()) continue;
				const FString PinName = PObj->GetStringField(TEXT("name"));

				bool bAnyMatched = false;
				FString ActualSeen;
				for (const FGraphExportEntry* Cand : Candidates)
				{
					for (UEdGraphPin* Pin : Cand->Node->Pins)
					{
						if (!Pin || !Pin->PinName.ToString().Equals(PinName, ESearchCase::IgnoreCase)) continue;
						ActualSeen = Pin->DefaultValue;
						if (Pin->DefaultValue.Equals(Expected)) { bAnyMatched = true; }
						break;
					}
					if (bAnyMatched) break;
				}
				if (!bAnyMatched)
				{
					TSharedPtr<FJsonObject> Mm = MakeShared<FJsonObject>();
					Mm->SetStringField(TEXT("node"), Key);
					Mm->SetStringField(TEXT("pin"), PinName);
					Mm->SetStringField(TEXT("expected"), Expected);
					Mm->SetStringField(TEXT("actual"), ActualSeen);
					PinDefaultMismatches.Add(MakeShared<FJsonValueObject>(Mm));
				}
			}
		}
	}

	// --- Connections ------------------------------------------------------
	TArray<TSharedPtr<FJsonValue>> MissingConnections;
	int32 MatchedConnections = 0;
	const TArray<TSharedPtr<FJsonValue>>* SpecConns = nullptr;
	if (Spec->TryGetArrayField(TEXT("connections"), SpecConns) && SpecConns)
	{
		for (const TSharedPtr<FJsonValue>& V : *SpecConns)
		{
			const TSharedPtr<FJsonObject> CObj = V->AsObject();
			if (!CObj.IsValid()) continue;
			const FString FromId = CObj->GetStringField(TEXT("from_node"));
			const FString ToId = CObj->GetStringField(TEXT("to_node"));
			const FString FromPin = CObj->GetStringField(TEXT("from_pin"));
			const FString ToPin = CObj->GetStringField(TEXT("to_pin"));

			// A connection references nodes by their exported instance id, so the
			// spec must also carry those nodes for the id to be resolvable.
			const FString* FromKey = SpecIdToBaseKey.Find(FromId);
			const FString* ToKey = SpecIdToBaseKey.Find(ToId);
			if (!FromKey || !ToKey)
			{
				TSharedPtr<FJsonObject> Miss = MakeShared<FJsonObject>();
				Miss->SetStringField(TEXT("from_node"), FromId);
				Miss->SetStringField(TEXT("from_pin"), FromPin);
				Miss->SetStringField(TEXT("to_node"), ToId);
				Miss->SetStringField(TEXT("to_pin"), ToPin);
				Miss->SetStringField(TEXT("why"),
					TEXT("connection references a node id that spec.nodes[] does not define, so it cannot be resolved"));
				MissingConnections.Add(MakeShared<FJsonValueObject>(Miss));
				continue;
			}

			const FString Edge = FString::Printf(TEXT("%s.%s>%s.%s"), **FromKey, *FromPin, **ToKey, *ToPin);
			if (ActualEdges.Contains(Edge))
			{
				++MatchedConnections;
			}
			else
			{
				TSharedPtr<FJsonObject> Miss = MakeShared<FJsonObject>();
				Miss->SetStringField(TEXT("from_node"), FromId);
				Miss->SetStringField(TEXT("from_pin"), FromPin);
				Miss->SetStringField(TEXT("to_node"), ToId);
				Miss->SetStringField(TEXT("to_pin"), ToPin);
				Miss->SetStringField(TEXT("why"), TEXT("no such edge in the graph"));
				MissingConnections.Add(MakeShared<FJsonValueObject>(Miss));
			}
		}
	}

	// --- forbidden_nodes: assert ABSENCE ----------------------------------
	TArray<TSharedPtr<FJsonValue>> ForbiddenPresent;
	const TArray<TSharedPtr<FJsonValue>>* Forbidden = nullptr;
	if (Spec->TryGetArrayField(TEXT("forbidden_nodes"), Forbidden) && Forbidden)
	{
		for (const TSharedPtr<FJsonValue>& V : *Forbidden)
		{
			const TSharedPtr<FJsonObject> FObj = V->AsObject();
			if (!FObj.IsValid()) continue;
			FString WantClass, WantFunc;
			FObj->TryGetStringField(TEXT("class"), WantClass);
			FObj->TryGetStringField(TEXT("function"), WantFunc);

			for (const FGraphExportEntry& E : Entries)
			{
				const FString ActualClass = E.Json->GetStringField(TEXT("class"));
				FString ActualFunc;
				E.Json->TryGetStringField(TEXT("function"), ActualFunc);

				const bool bClassHit = WantClass.IsEmpty() || ActualClass.Equals(WantClass, ESearchCase::IgnoreCase);
				const bool bFuncHit = WantFunc.IsEmpty() || ActualFunc.Equals(WantFunc, ESearchCase::IgnoreCase);
				if (bClassHit && bFuncHit && (!WantClass.IsEmpty() || !WantFunc.IsEmpty()))
				{
					TSharedPtr<FJsonObject> Hit = MakeShared<FJsonObject>();
					Hit->SetStringField(TEXT("node_id"), E.Json->GetStringField(TEXT("id")));
					Hit->SetStringField(TEXT("class"), ActualClass);
					if (!ActualFunc.IsEmpty()) Hit->SetStringField(TEXT("function"), ActualFunc);
					Hit->SetStringField(TEXT("why"), TEXT("forbidden node is still present"));
					ForbiddenPresent.Add(MakeShared<FJsonValueObject>(Hit));
				}
			}
		}
	}

	// --- Extras (exact mode only) -----------------------------------------
	TArray<TSharedPtr<FJsonValue>> ExtraNodes;
	if (Mode == TEXT("exact"))
	{
		TMap<FString, int32> SpecCounts;
		for (const FString& K : SpecBaseKeys) SpecCounts.FindOrAdd(K)++;
		TMap<FString, int32> ActualCounts;
		for (const FGraphExportEntry& E : Entries) ActualCounts.FindOrAdd(E.BaseKey)++;

		for (const TPair<FString, int32>& Pair : ActualCounts)
		{
			const int32 Want = SpecCounts.FindRef(Pair.Key);
			if (Pair.Value > Want)
			{
				TSharedPtr<FJsonObject> Extra = MakeShared<FJsonObject>();
				Extra->SetStringField(TEXT("key"), Pair.Key);
				Extra->SetNumberField(TEXT("actual_count"), Pair.Value);
				Extra->SetNumberField(TEXT("spec_count"), Want);
				ExtraNodes.Add(MakeShared<FJsonValueObject>(Extra));
			}
		}
	}

	const bool bMatched =
		MissingNodes.Num() == 0 &&
		MissingConnections.Num() == 0 &&
		PinDefaultMismatches.Num() == 0 &&
		ForbiddenPresent.Num() == 0 &&
		ExtraNodes.Num() == 0;

	const int32 SpecNodeCount = SpecNodes ? SpecNodes->Num() : 0;
	const int32 SpecConnCount = SpecConns ? SpecConns->Num() : 0;

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("matched"), bMatched);
	Root->SetStringField(TEXT("mode"), Mode);
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("graph_name"), Graph->GetName());
	Root->SetArrayField(TEXT("missing_nodes"), MissingNodes);
	Root->SetArrayField(TEXT("extra_nodes"), ExtraNodes);
	Root->SetArrayField(TEXT("missing_connections"), MissingConnections);
	Root->SetArrayField(TEXT("pin_default_mismatches"), PinDefaultMismatches);
	Root->SetArrayField(TEXT("forbidden_nodes_present"), ForbiddenPresent);
	Root->SetStringField(TEXT("summary"), FString::Printf(
		TEXT("%d/%d nodes, %d/%d connections, %d default mismatches, %d forbidden present"),
		MatchedNodes, SpecNodeCount, MatchedConnections, SpecConnCount,
		PinDefaultMismatches.Num(), ForbiddenPresent.Num()));

	// Deliberately Success even when matched is false -- an assertion miss is data
	// the caller must read and act on, not a transport-level error.
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  copy_nodes
// ============================================================

FMonolithActionResult FMonolithBlueprintGraphExportActions::HandleCopyNodes(const TSharedPtr<FJsonObject>& Params)
{
	// Load source Blueprint
	FString SourceAssetPath = Params->GetStringField(TEXT("source_asset"));
	if (SourceAssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: source_asset"));
	}
	UBlueprint* SourceBP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(SourceAssetPath);
	if (!SourceBP)
	{
		// Try level blueprint fallback
		SourceBP = MonolithBlueprintInternal::TryLoadLevelBlueprint(SourceAssetPath);
	}
	if (!SourceBP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Source Blueprint not found: %s"), *SourceAssetPath));
	}

	// Load target Blueprint
	FString TargetAssetPath = Params->GetStringField(TEXT("target_asset"));
	if (TargetAssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: target_asset"));
	}
	UBlueprint* TargetBP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(TargetAssetPath);
	if (!TargetBP)
	{
		TargetBP = MonolithBlueprintInternal::TryLoadLevelBlueprint(TargetAssetPath);
	}
	if (!TargetBP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Target Blueprint not found: %s"), *TargetAssetPath));
	}

	// Find source graph
	FString SourceGraphName = Params->GetStringField(TEXT("source_graph"));
	UEdGraph* SourceGraph = MonolithBlueprintInternal::FindGraphByName(SourceBP, SourceGraphName);
	if (!SourceGraph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Source graph not found: %s"), *SourceGraphName));
	}

	// Find target graph
	FString TargetGraphName = Params->GetStringField(TEXT("target_graph"));
	UEdGraph* TargetGraph = MonolithBlueprintInternal::FindGraphByName(TargetBP, TargetGraphName);
	if (!TargetGraph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Target graph not found: %s"), *TargetGraphName));
	}

	// Parse node IDs
	const TArray<TSharedPtr<FJsonValue>>* NodeIdValues = nullptr;
	if (!Params->TryGetArrayField(TEXT("node_ids"), NodeIdValues) || !NodeIdValues || NodeIdValues->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing or empty required parameter: node_ids"));
	}

	// Collect source nodes
	TSet<UObject*> NodesToExport;
	TArray<FString> NotFound;
	for (const TSharedPtr<FJsonValue>& IdVal : *NodeIdValues)
	{
		FString NodeId = IdVal->AsString();
		UEdGraphNode* Node = nullptr;
		for (UEdGraphNode* N : SourceGraph->Nodes)
		{
			if (N && N->GetName() == NodeId)
			{
				Node = N;
				break;
			}
		}
		if (Node)
		{
			NodesToExport.Add(Node);
		}
		else
		{
			NotFound.Add(NodeId);
		}
	}

	if (NodesToExport.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("None of the specified nodes were found in graph '%s'. Not found: %s"),
			*SourceGraph->GetName(), *FString::Join(NotFound, TEXT(", "))));
	}

	// Export via T3D text
	FString ExportedText;
	FEdGraphUtilities::ExportNodesToText(NodesToExport, ExportedText);

	// Import into target graph
	TSet<UEdGraphNode*> ImportedNodes;
	FEdGraphUtilities::ImportNodesFromText(TargetGraph, ExportedText, ImportedNodes);

	// Mark target Blueprint as modified
	FBlueprintEditorUtils::MarkBlueprintAsModified(TargetBP);

	// Build result
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("source_asset"), SourceAssetPath);
	Root->SetStringField(TEXT("source_graph"), SourceGraph->GetName());
	Root->SetStringField(TEXT("target_asset"), TargetAssetPath);
	Root->SetStringField(TEXT("target_graph"), TargetGraph->GetName());
	Root->SetNumberField(TEXT("nodes_copied"), ImportedNodes.Num());

	TArray<TSharedPtr<FJsonValue>> NewNodeIds;
	for (UEdGraphNode* ImportedNode : ImportedNodes)
	{
		if (ImportedNode)
		{
			NewNodeIds.Add(MakeShared<FJsonValueString>(ImportedNode->GetName()));
		}
	}
	Root->SetArrayField(TEXT("new_node_ids"), NewNodeIds);

	if (NotFound.Num() > 0)
	{
		TArray<TSharedPtr<FJsonValue>> NotFoundArr;
		for (const FString& Id : NotFound)
		{
			NotFoundArr.Add(MakeShared<FJsonValueString>(Id));
		}
		Root->SetArrayField(TEXT("not_found"), NotFoundArr);
		Root->SetStringField(TEXT("warning"),
			FString::Printf(TEXT("%d node(s) not found in source graph"), NotFound.Num()));
	}

	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  duplicate_graph
// ============================================================

FMonolithActionResult FMonolithBlueprintGraphExportActions::HandleDuplicateGraph(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString GraphName = Params->GetStringField(TEXT("graph_name"));
	if (GraphName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: graph_name"));
	}

	FString NewName = Params->GetStringField(TEXT("new_name"));
	if (NewName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: new_name"));
	}

	UEdGraph* SourceGraph = MonolithBlueprintInternal::FindGraphByName(BP, GraphName);
	if (!SourceGraph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph not found: %s"), *GraphName));
	}

	// Only allow duplication of function and macro graphs
	bool bIsFunction = BP->FunctionGraphs.Contains(SourceGraph);
	bool bIsMacro = BP->MacroGraphs.Contains(SourceGraph);

	if (!bIsFunction && !bIsMacro)
	{
		return FMonolithActionResult::Error(
			TEXT("Only function and macro graphs can be duplicated. Event graphs and delegate signature graphs are not supported."));
	}

	// Check if a graph with the new name already exists
	if (MonolithBlueprintInternal::FindGraphByName(BP, NewName))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("A graph named '%s' already exists in this Blueprint"), *NewName));
	}

	// Check the schema supports duplication
	const UEdGraphSchema* Schema = SourceGraph->GetSchema();
	if (!Schema || !Schema->CanDuplicateGraph(SourceGraph))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Schema does not allow duplication of graph '%s'"), *GraphName));
	}

	BP->Modify();

	// Duplicate via the graph schema (correct UE 5.7 pattern)
	UEdGraph* DuplicatedGraph = Schema->DuplicateGraph(SourceGraph);
	if (!DuplicatedGraph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to duplicate graph '%s'"), *GraphName));
	}

	DuplicatedGraph->Modify();

	// Generate new GUIDs and component templates for all nodes
	for (UEdGraphNode* EdGraphNode : DuplicatedGraph->Nodes)
	{
		if (EdGraphNode)
		{
			EdGraphNode->CreateNewGuid();
		}
	}

	// Add the duplicated graph to the appropriate array
	if (bIsFunction)
	{
		BP->FunctionGraphs.Add(DuplicatedGraph);
	}
	else // bIsMacro
	{
		BP->MacroGraphs.Add(DuplicatedGraph);
	}

	// Rename to the desired name (must happen after adding to graph array)
	FBlueprintEditorUtils::RenameGraph(DuplicatedGraph, NewName);

	// Mark modified
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	// Build result
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("source_graph"), GraphName);
	Root->SetStringField(TEXT("new_graph"), DuplicatedGraph->GetName());
	Root->SetStringField(TEXT("graph_type"), bIsFunction ? TEXT("function") : TEXT("macro"));
	Root->SetNumberField(TEXT("node_count"), DuplicatedGraph->Nodes.Num());

	return FMonolithActionResult::Success(Root);
}
