#include "MonolithBlueprintT3DActions.h"
#include "MonolithBlueprintInternal.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/CompilerResultsLog.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraphSchema_K2.h"
#include "EdGraphUtilities.h"
#include "K2Node_CallFunction.h"
#include "ScopedTransaction.h"
#include "Misc/Guid.h"

// ============================================================
//  Registration
// ============================================================

void FMonolithBlueprintT3DActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	const TCHAR* T3DDesc =
		TEXT("Raw T3D node text, exactly as UE puts on the clipboard when you copy nodes in a "
			"Blueprint graph. Get a known-good sample with export_graph on a hand-wired graph, or "
			"by copying nodes in the editor and pasting into a text file. Placeholder tokens are "
			"supported: {{GUID:name}} mints one stable FGuid per distinct name for the duration of "
			"the call (use the same name in two places to point at the same node), and {{name}} is "
			"substituted from the 'placeholders' map.");

	Registry.RegisterAction(TEXT("blueprint"), TEXT("inject_nodes_t3d"),
		TEXT("Inject nodes into a graph from raw T3D text in ONE atomic transaction. "
			"This is the fast path for authoring: a multi-node cluster that would take a dozen "
			"add_node/connect_nodes round trips lands in a single call, and a failure leaves the "
			"graph untouched rather than half-wired. "
			"Order of operations: resolve placeholders -> reflection pre-flight (every node class "
			"must resolve; every K2Node_CallFunction MemberName must exist on its MemberParent) -> "
			"UE's own CanImportNodesFromText -> ImportNodesFromText inside a transaction. "
			"Any pre-flight failure aborts BEFORE the graph is touched. "
			"Returns a compact node summary, NOT raw T3D -- re-export with export_graph if you need "
			"the full text. Pair with get_graph_fingerprint before/after to prove the edit landed. "
			"Use dry_run:true (or validate_nodes_t3d) to check a payload without mutating anything."),
		FMonolithActionHandler::CreateStatic(&HandleInjectNodesT3D),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path ('$current' for the open level BP)"))
			.Required(TEXT("t3d"), TEXT("string"), T3DDesc)
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (defaults to first event graph)"))
			.Optional(TEXT("placeholders"), TEXT("object"), TEXT("Map of {{token}} -> replacement string"))
			.Optional(TEXT("dry_run"), TEXT("bool"),
				TEXT("Run placeholder resolution and the full pre-flight, then stop without mutating. "
					"Returns the same validation payload as validate_nodes_t3d."), TEXT("false"))
			.Optional(TEXT("auto_layout"), TEXT("bool"),
				TEXT("Reposition injected nodes into a left-to-right execution flow. Only the injected "
					"nodes move; existing nodes are left alone. For a full-graph tidy use the "
					"auto_layout action instead."), TEXT("false"))
			.Optional(TEXT("position"), TEXT("object"),
				TEXT("{x, y} graph-space origin for the injected cluster. Defaults to below-right of "
					"the existing content so nothing lands on top of current nodes."))
			.Optional(TEXT("compile"), TEXT("bool"),
				TEXT("Compile after injecting and report error/warning counts."), TEXT("true"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("validate_nodes_t3d"),
		TEXT("Pre-flight a T3D payload against the reflection system WITHOUT touching any graph. "
			"Reports unresolvable node classes, missing functions, malformed Begin/End nesting, and "
			"unresolved {{placeholders}}. Identical to inject_nodes_t3d with dry_run:true. "
			"Cheap -- run it before injecting into anything you care about."),
		FMonolithActionHandler::CreateStatic(&HandleValidateNodesT3D),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path (target graph context)"))
			.Required(TEXT("t3d"), TEXT("string"), T3DDesc)
			.Optional(TEXT("graph_name"), TEXT("string"), TEXT("Target graph name (defaults to first event graph)"))
			.Optional(TEXT("placeholders"), TEXT("object"), TEXT("Map of {{token}} -> replacement string"))
			.Build());
}

// ============================================================
//  Internals
// ============================================================

namespace MonolithT3DInternal
{
	/** One problem found during pre-flight. Fatal entries abort the injection. */
	struct FFinding
	{
		FString Severity;   // "error" | "warning"
		FString Kind;       // machine-readable category
		FString Detail;
		FString Context;    // node name / class the finding attaches to
	};

	/**
	 * Substitute {{GUID:name}} and {{name}} tokens.
	 *
	 * {{GUID:name}} mints one FGuid per distinct name, so the same name used on a node's
	 * NodeGuid and on a pin's LinkedTo reference resolves to the same value and the link
	 * survives the import. Formatted to match UE's own T3D guid style (no separators, upper).
	 */
	static FString ResolvePlaceholders(const FString& In,
		const TSharedPtr<FJsonObject>& Map,
		TArray<FString>& OutMinted,
		TArray<FFinding>& OutFindings)
	{
		FString Out = In;

		// {{GUID:name}}
		TMap<FString, FString> Minted;
		int32 GuardIterations = 0;
		while (GuardIterations++ < 4096)
		{
			int32 Start = Out.Find(TEXT("{{GUID:"));
			if (Start == INDEX_NONE) break;
			int32 End = Out.Find(TEXT("}}"), ESearchCase::CaseSensitive, ESearchDir::FromStart, Start);
			if (End == INDEX_NONE)
			{
				OutFindings.Add({TEXT("error"), TEXT("malformed_placeholder"),
					TEXT("Unterminated {{GUID:...}} token (missing '}}')"), TEXT("")});
				break;
			}
			const FString Name = Out.Mid(Start + 7, End - (Start + 7));
			FString* Existing = Minted.Find(Name);
			if (!Existing)
			{
				const FString NewGuid = FGuid::NewGuid().ToString(EGuidFormats::Digits).ToUpper();
				Minted.Add(Name, NewGuid);
				OutMinted.Add(FString::Printf(TEXT("%s=%s"), *Name, *NewGuid));
				Existing = Minted.Find(Name);
			}
			Out = Out.Left(Start) + *Existing + Out.Mid(End + 2);
		}

		// {{name}} from the caller-supplied map
		if (Map.IsValid())
		{
			for (const auto& Pair : Map->Values)
			{
				FString Value;
				if (Pair.Value.IsValid() && Pair.Value->TryGetString(Value))
				{
					Out = Out.Replace(*FString::Printf(TEXT("{{%s}}"), *Pair.Key), *Value, ESearchCase::CaseSensitive);
				}
			}
		}

		// Anything still unresolved is a hard error -- it would import as literal text.
		int32 Leftover = Out.Find(TEXT("{{"));
		if (Leftover != INDEX_NONE)
		{
			const int32 LeftEnd = Out.Find(TEXT("}}"), ESearchCase::CaseSensitive, ESearchDir::FromStart, Leftover);
			const FString Token = (LeftEnd != INDEX_NONE)
				? Out.Mid(Leftover, LeftEnd - Leftover + 2)
				: Out.Mid(Leftover, 32);
			OutFindings.Add({TEXT("error"), TEXT("unresolved_placeholder"),
				FString::Printf(TEXT("Token %s was never substituted; add it to 'placeholders'"), *Token),
				TEXT("")});
		}

		return Out;
	}

	/** Pull the value of Key="..." or Key=Value from a single T3D line. */
	static bool ExtractField(const FString& Line, const TCHAR* Key, FString& Out)
	{
		const FString Needle = FString::Printf(TEXT("%s="), Key);
		int32 At = Line.Find(Needle, ESearchCase::CaseSensitive);
		if (At == INDEX_NONE) return false;
		int32 Cursor = At + Needle.Len();
		if (!Line.IsValidIndex(Cursor)) return false;

		if (Line[Cursor] == TEXT('"'))
		{
			const int32 Close = Line.Find(TEXT("\""), ESearchCase::CaseSensitive, ESearchDir::FromStart, Cursor + 1);
			if (Close == INDEX_NONE) return false;
			Out = Line.Mid(Cursor + 1, Close - Cursor - 1);
			return true;
		}

		int32 Stop = Cursor;
		while (Line.IsValidIndex(Stop) && Line[Stop] != TEXT(' ') && Line[Stop] != TEXT(',') && Line[Stop] != TEXT(')'))
		{
			++Stop;
		}
		Out = Line.Mid(Cursor, Stop - Cursor);
		return !Out.IsEmpty();
	}

	/** Strip Class'"..."' / "..." decoration off an object path. */
	static FString CleanPath(FString Path)
	{
		Path.TrimStartAndEndInline();
		int32 Quote = Path.Find(TEXT("\""));
		if (Quote != INDEX_NONE)
		{
			const int32 Close = Path.Find(TEXT("\""), ESearchCase::CaseSensitive, ESearchDir::FromStart, Quote + 1);
			if (Close != INDEX_NONE)
			{
				Path = Path.Mid(Quote + 1, Close - Quote - 1);
			}
		}
		Path.RemoveFromEnd(TEXT("'"));
		return Path;
	}

	/**
	 * Reflection pre-flight.
	 *
	 * Walks the T3D looking for the two things that actually fail at import time and produce
	 * a silently broken node rather than an error: a node class that no longer exists, and a
	 * CallFunction whose MemberName is not on its MemberParent. The second is the common one
	 * after a C++ rename -- the node imports fine and shows up red in the editor.
	 */
	static void PreflightT3D(const FString& T3D, TArray<FFinding>& Out, int32& OutNodeCount)
	{
		OutNodeCount = 0;
		int32 Depth = 0;
		FString CurrentNodeName;
		FString CurrentMemberParent;

		TArray<FString> Lines;
		T3D.ParseIntoArrayLines(Lines, /*bCullEmpty*/ false);

		for (const FString& Raw : Lines)
		{
			const FString Line = Raw.TrimStartAndEnd();

			if (Line.StartsWith(TEXT("Begin Object")))
			{
				++Depth;
				FString ClassPath, NodeName;
				const bool bHasClass = ExtractField(Line, TEXT("Class"), ClassPath);
				ExtractField(Line, TEXT("Name"), NodeName);

				if (bHasClass)
				{
					++OutNodeCount;
					CurrentNodeName = NodeName;
					CurrentMemberParent.Reset();

					const FString Clean = CleanPath(ClassPath);
					if (!LoadObject<UClass>(nullptr, *Clean))
					{
						Out.Add({TEXT("error"), TEXT("unresolved_node_class"),
							FString::Printf(TEXT("Node class does not resolve: %s"), *Clean),
							NodeName});
					}
				}
				continue;
			}

			if (Line.StartsWith(TEXT("End Object")))
			{
				--Depth;
				if (Depth < 0)
				{
					Out.Add({TEXT("error"), TEXT("malformed_t3d"),
						TEXT("'End Object' without a matching 'Begin Object'"), CurrentNodeName});
					Depth = 0;
				}
				continue;
			}

			// FunctionReference=(MemberParent=Class'"/Script/X.Y"',MemberName="Z")
			if (Line.Contains(TEXT("MemberParent=")))
			{
				FString Parent;
				if (ExtractField(Line, TEXT("MemberParent"), Parent))
				{
					CurrentMemberParent = CleanPath(Parent);
				}
			}
			if (Line.Contains(TEXT("MemberName=")))
			{
				FString MemberName;
				if (ExtractField(Line, TEXT("MemberName"), MemberName) && !CurrentMemberParent.IsEmpty())
				{
					if (UClass* ParentClass = LoadObject<UClass>(nullptr, *CurrentMemberParent))
					{
						// Only assert on functions. Variable/delegate MemberNames resolve through
						// different paths (property, BP-generated skeleton) and a miss here would
						// be a false positive.
						const bool bLooksLikeFunction = Line.Contains(TEXT("FunctionReference"))
							|| CurrentNodeName.Contains(TEXT("CallFunction"));
						if (bLooksLikeFunction && !ParentClass->FindFunctionByName(FName(*MemberName)))
						{
							Out.Add({TEXT("error"), TEXT("unresolved_function"),
								FString::Printf(TEXT("Function '%s' not found on %s"),
									*MemberName, *CurrentMemberParent),
								CurrentNodeName});
						}
					}
					else
					{
						Out.Add({TEXT("warning"), TEXT("unresolved_member_parent"),
							FString::Printf(TEXT("MemberParent does not resolve: %s "
								"(function existence not checked)"), *CurrentMemberParent),
							CurrentNodeName});
					}
				}
			}
		}

		if (Depth != 0)
		{
			Out.Add({TEXT("error"), TEXT("malformed_t3d"),
				FString::Printf(TEXT("Unbalanced Begin/End Object nesting (depth %d at end of payload)"), Depth),
				TEXT("")});
		}
		if (OutNodeCount == 0)
		{
			Out.Add({TEXT("error"), TEXT("empty_payload"),
				TEXT("No 'Begin Object Class=' found -- this is not node T3D"), TEXT("")});
		}
	}

	static TSharedPtr<FJsonObject> FindingsToJson(const TArray<FFinding>& Findings, bool& bOutHasError)
	{
		bOutHasError = false;
		TArray<TSharedPtr<FJsonValue>> Arr;
		for (const FFinding& F : Findings)
		{
			if (F.Severity == TEXT("error")) bOutHasError = true;
			TSharedPtr<FJsonObject> O = MakeShared<FJsonObject>();
			O->SetStringField(TEXT("severity"), F.Severity);
			O->SetStringField(TEXT("kind"), F.Kind);
			O->SetStringField(TEXT("detail"), F.Detail);
			if (!F.Context.IsEmpty()) O->SetStringField(TEXT("node"), F.Context);
			Arr.Add(MakeShared<FJsonValueObject>(O));
		}
		TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
		Root->SetArrayField(TEXT("findings"), Arr);
		return Root;
	}

	/** Shared entry for inject and validate. bMutate=false stops after pre-flight. */
	static FMonolithActionResult Run(const TSharedPtr<FJsonObject>& Params, bool bMutate)
	{
		FString AssetPath;
		UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
		if (!BP)
		{
			BP = MonolithBlueprintInternal::TryLoadLevelBlueprint(AssetPath);
		}
		if (!BP)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
		}

		FString GraphName;
		Params->TryGetStringField(TEXT("graph_name"), GraphName);
		UEdGraph* Graph = MonolithBlueprintInternal::FindGraphByName(BP, GraphName);
		if (!Graph)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Graph not found: '%s' on %s"), *GraphName, *AssetPath));
		}

		FString T3D;
		if (!Params->TryGetStringField(TEXT("t3d"), T3D) || T3D.IsEmpty())
		{
			return FMonolithActionResult::Error(TEXT("Missing required parameter: t3d"));
		}

		// --- resolve placeholders -------------------------------------------------
		const TSharedPtr<FJsonObject>* PlaceholderMap = nullptr;
		Params->TryGetObjectField(TEXT("placeholders"), PlaceholderMap);

		TArray<FFinding> Findings;
		TArray<FString> Minted;
		const FString Resolved = ResolvePlaceholders(
			T3D, PlaceholderMap ? *PlaceholderMap : nullptr, Minted, Findings);

		// --- reflection pre-flight ------------------------------------------------
		int32 DeclaredNodes = 0;
		PreflightT3D(Resolved, Findings, DeclaredNodes);

		// --- UE's own gate --------------------------------------------------------
		const bool bEngineAccepts = FEdGraphUtilities::CanImportNodesFromText(Graph, Resolved);
		if (!bEngineAccepts)
		{
			Findings.Add({TEXT("error"), TEXT("rejected_by_engine"),
				TEXT("FEdGraphUtilities::CanImportNodesFromText refused this payload for this graph "
					"(usually a node type the target graph does not allow -- e.g. an event node in a "
					"function graph, or a latent node in a const function)"), TEXT("")});
		}

		bool bHasError = false;
		TSharedPtr<FJsonObject> Root = FindingsToJson(Findings, bHasError);
		Root->SetStringField(TEXT("asset_path"), AssetPath);
		Root->SetStringField(TEXT("graph"), Graph->GetName());
		Root->SetNumberField(TEXT("declared_nodes"), DeclaredNodes);
		Root->SetBoolField(TEXT("engine_accepts"), bEngineAccepts);
		Root->SetBoolField(TEXT("valid"), !bHasError);
		if (Minted.Num() > 0)
		{
			TArray<TSharedPtr<FJsonValue>> MintedArr;
			for (const FString& M : Minted) MintedArr.Add(MakeShared<FJsonValueString>(M));
			Root->SetArrayField(TEXT("minted_guids"), MintedArr);
		}

		const bool bDryRun = !bMutate || Params->GetBoolField(TEXT("dry_run"));
		if (bDryRun || bHasError)
		{
			Root->SetBoolField(TEXT("injected"), false);
			Root->SetStringField(TEXT("reason"),
				bHasError ? TEXT("pre-flight failed; graph not touched")
						  : TEXT("dry run; graph not touched"));
			// A failed pre-flight is a successful *call* that reports valid:false, matching
			// assert_graph_matches. Callers branch on 'valid', not on MCP error handling.
			return FMonolithActionResult::Success(Root);
		}

		// --- atomic injection -----------------------------------------------------
		int32 OriginX = 0, OriginY = 0;
		const TSharedPtr<FJsonObject>* PosObj = nullptr;
		if (Params->TryGetObjectField(TEXT("position"), PosObj) && PosObj)
		{
			OriginX = (int32)(*PosObj)->GetNumberField(TEXT("x"));
			OriginY = (int32)(*PosObj)->GetNumberField(TEXT("y"));
		}
		else
		{
			// Park the cluster clear of existing content instead of on top of it.
			int32 MaxY = 0;
			for (UEdGraphNode* N : Graph->Nodes)
			{
				if (N) MaxY = FMath::Max(MaxY, N->NodePosY);
			}
			OriginY = Graph->Nodes.Num() > 0 ? MaxY + 320 : 0;
		}

		TSet<UEdGraphNode*> Imported;
		{
			FScopedTransaction Transaction(
				NSLOCTEXT("MonolithBlueprintT3DActions", "InjectNodesT3D", "Monolith Inject Nodes (T3D)"));
			Graph->Modify();
			FEdGraphUtilities::ImportNodesFromText(Graph, Resolved, Imported);

			if (Imported.Num() == 0)
			{
				// Nothing landed -- drop the transaction rather than leaving an empty undo entry.
				Transaction.Cancel();
				Root->SetBoolField(TEXT("injected"), false);
				Root->SetStringField(TEXT("reason"),
					TEXT("ImportNodesFromText returned no nodes despite passing pre-flight"));
				Root->SetBoolField(TEXT("valid"), false);
				return FMonolithActionResult::Success(Root);
			}

			// Guarantee unique guids. Re-importing the same payload twice otherwise yields
			// colliding NodeGuids, which breaks fingerprinting and the editor's own diffing.
			TSet<FGuid> Seen;
			for (UEdGraphNode* N : Graph->Nodes)
			{
				if (N && !Imported.Contains(N)) Seen.Add(N->NodeGuid);
			}
			for (UEdGraphNode* N : Imported)
			{
				if (!N) continue;
				if (Seen.Contains(N->NodeGuid)) N->CreateNewGuid();
				Seen.Add(N->NodeGuid);
			}

			// Offset the cluster to the chosen origin, preserving relative layout.
			int32 MinX = MAX_int32, MinY = MAX_int32;
			for (UEdGraphNode* N : Imported)
			{
				if (!N) continue;
				MinX = FMath::Min(MinX, N->NodePosX);
				MinY = FMath::Min(MinY, N->NodePosY);
			}
			if (MinX != MAX_int32)
			{
				const int32 DX = OriginX - MinX;
				const int32 DY = OriginY - MinY;
				for (UEdGraphNode* N : Imported)
				{
					if (!N) continue;
					N->NodePosX += DX;
					N->NodePosY += DY;
					N->SnapToGrid(16);
				}
			}

			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
		}

		// --- compact readback -----------------------------------------------------
		TArray<TSharedPtr<FJsonValue>> NodeArr;
		for (UEdGraphNode* N : Imported)
		{
			if (!N) continue;
			TSharedPtr<FJsonObject> O = MakeShared<FJsonObject>();
			O->SetStringField(TEXT("id"), N->GetName());
			O->SetStringField(TEXT("class"), N->GetClass()->GetName());
			O->SetStringField(TEXT("title"), N->GetNodeTitle(ENodeTitleType::ListView).ToString());
			O->SetNumberField(TEXT("x"), N->NodePosX);
			O->SetNumberField(TEXT("y"), N->NodePosY);
			int32 Linked = 0;
			for (UEdGraphPin* P : N->Pins)
			{
				if (P) Linked += P->LinkedTo.Num();
			}
			O->SetNumberField(TEXT("linked_pins"), Linked);
			NodeArr.Add(MakeShared<FJsonValueObject>(O));
		}
		Root->SetArrayField(TEXT("nodes"), NodeArr);
		Root->SetNumberField(TEXT("nodes_injected"), Imported.Num());
		Root->SetBoolField(TEXT("injected"), true);

		if (Imported.Num() != DeclaredNodes)
		{
			Root->SetStringField(TEXT("warning"), FString::Printf(
				TEXT("Payload declared %d node(s) but %d were imported. UE drops nodes the target "
					"graph will not accept; compare 'nodes' against your payload."),
				DeclaredNodes, Imported.Num()));
		}

		// --- optional compile -----------------------------------------------------
		bool bCompile = true;
		Params->TryGetBoolField(TEXT("compile"), bCompile);
		if (bCompile)
		{
			FCompilerResultsLog Results;
			Results.bSilentMode = true;
			FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::SkipGarbageCollection, &Results);
			Root->SetNumberField(TEXT("compile_errors"), Results.NumErrors);
			Root->SetNumberField(TEXT("compile_warnings"), Results.NumWarnings);
			Root->SetBoolField(TEXT("compiled_clean"), Results.NumErrors == 0);
		}

		Root->SetStringField(TEXT("next"),
			TEXT("Nodes are in the graph but the asset is NOT saved. Save it with "
				"editor/save_asset, and prove the edit with get_graph_fingerprint or "
				"assert_graph_matches."));

		return FMonolithActionResult::Success(Root);
	}
}

// ============================================================
//  Handlers
// ============================================================

FMonolithActionResult FMonolithBlueprintT3DActions::HandleInjectNodesT3D(const TSharedPtr<FJsonObject>& Params)
{
	return MonolithT3DInternal::Run(Params, /*bMutate*/ true);
}

FMonolithActionResult FMonolithBlueprintT3DActions::HandleValidateNodesT3D(const TSharedPtr<FJsonObject>& Params)
{
	return MonolithT3DInternal::Run(Params, /*bMutate*/ false);
}
