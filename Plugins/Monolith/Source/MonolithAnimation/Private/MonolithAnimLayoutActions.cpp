#include "MonolithAnimLayoutActions.h"
#include "MonolithAssetUtils.h"
#include "MonolithParamSchema.h"
#include "IMonolithGraphFormatter.h"

#include "Animation/AnimBlueprint.h"
#include "AnimGraphNode_StateMachine.h"
#include "AnimationGraph.h"
#include "AnimationStateMachineGraph.h"
#include "AnimStateNode.h"
#include "AnimationStateGraph.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

void FMonolithAnimLayoutActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("animation"), TEXT("auto_layout"),
		TEXT("Auto-layout nodes in an Animation Blueprint graph. With formatter='auto' (default) it uses "
			 "Blueprint Assist if available and otherwise falls back to a built-in dependency-aware layered "
			 "layout that needs no plugin (available in release builds). formatter='builtin' forces the "
			 "built-in layout. Asset must be open in the editor."),
		FMonolithActionHandler::CreateStatic(&HandleAutoLayout),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Animation Blueprint asset path"))
			.Optional(TEXT("graph_name"), TEXT("string"),
				TEXT("Graph to layout: 'AnimGraph' (default), state machine name, or 'all' for every graph"), TEXT("AnimGraph"))
			.Optional(TEXT("formatter"), TEXT("string"),
				TEXT("Formatter: 'auto' (default, Blueprint Assist if available else built-in), "
					 "'blueprint_assist' (BA or error), 'builtin' (built-in layered layout, no plugin needed), "
					 "'monolith' (alias for 'builtin')"),
				TEXT("auto"))
			.Optional(TEXT("column_spacing"), TEXT("number"),
				TEXT("Built-in layout: horizontal spacing between dependency columns (default 320)"), TEXT("320"))
			.Optional(TEXT("row_spacing"), TEXT("number"),
				TEXT("Built-in layout: vertical spacing between nodes within a column (default 180)"), TEXT("180"))
			.Build());
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

namespace
{

/** Collect all formattable graphs from an ABP: the main AnimGraph, all state machine graphs, and state inner graphs. */
void CollectAllGraphs(UAnimBlueprint* ABP, TArray<TPair<FString, UEdGraph*>>& OutGraphs)
{
	for (UEdGraph* Graph : ABP->FunctionGraphs)
	{
		if (!Graph) continue;

		// Add the top-level graph (e.g. AnimGraph)
		OutGraphs.Add(TPair<FString, UEdGraph*>(Graph->GetName(), Graph));

		// Dig into state machine nodes
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			UAnimGraphNode_StateMachine* SMNode = Cast<UAnimGraphNode_StateMachine>(Node);
			if (!SMNode) continue;

			UAnimationStateMachineGraph* SMGraph = Cast<UAnimationStateMachineGraph>(SMNode->EditorStateMachineGraph);
			if (!SMGraph) continue;

			// The SM graph itself
			FString SMTitle = SMNode->GetNodeTitle(ENodeTitleType::FullTitle).ToString();
			int32 NewlineIdx = INDEX_NONE;
			if (SMTitle.FindChar(TEXT('\n'), NewlineIdx))
			{
				SMTitle.LeftInline(NewlineIdx);
			}
			OutGraphs.Add(TPair<FString, UEdGraph*>(SMTitle, SMGraph));

			// Each state's inner graph
			for (UEdGraphNode* SMChild : SMGraph->Nodes)
			{
				UAnimStateNode* StateNode = Cast<UAnimStateNode>(SMChild);
				if (!StateNode || !StateNode->BoundGraph) continue;

				FString StateLabel = FString::Printf(TEXT("%s.%s"), *SMTitle, *StateNode->GetStateName());
				OutGraphs.Add(TPair<FString, UEdGraph*>(StateLabel, StateNode->BoundGraph));
			}
		}
	}
}

/** Find the main AnimGraph (first UAnimationGraph in FunctionGraphs). */
UEdGraph* FindAnimGraph(UAnimBlueprint* ABP)
{
	for (UEdGraph* Graph : ABP->FunctionGraphs)
	{
		if (UAnimationGraph* AG = Cast<UAnimationGraph>(Graph))
		{
			return AG;
		}
	}
	return nullptr;
}

/** Find a state machine graph by display title. */
UEdGraph* FindSMGraphByTitle(UAnimBlueprint* ABP, const FString& MachineName)
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

/** Format a single graph via IMonolithGraphFormatter. Returns a JSON object with results. */
TSharedPtr<FJsonObject> FormatSingleGraph(const FString& GraphLabel, UEdGraph* Graph, bool bExplicitBA, FString& OutError)
{
	bool bBAAvailable = IMonolithGraphFormatter::IsAvailable()
		&& IMonolithGraphFormatter::Get().SupportsGraph(Graph);

	if (!bBAAvailable)
	{
		if (bExplicitBA)
		{
			OutError = FString::Printf(
				TEXT("Blueprint Assist formatter not available or does not support graph '%s'. "
					 "Ensure Blueprint Assist plugin is installed and the asset is open in the editor."),
				*GraphLabel);
		}
		else
		{
			OutError = FString::Printf(
				TEXT("No formatter available for graph '%s'. Install Blueprint Assist plugin and ensure the asset is open in the editor."),
				*GraphLabel);
		}
		return nullptr;
	}

	int32 NodesFormatted = 0;
	FString FormatError;
	bool bSuccess = IMonolithGraphFormatter::Get().FormatGraph(Graph, NodesFormatted, FormatError);

	if (!bSuccess)
	{
		OutError = FString::Printf(TEXT("Formatter failed on graph '%s': %s"), *GraphLabel, *FormatError);
		return nullptr;
	}

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("graph"), GraphLabel);
	ResultObj->SetNumberField(TEXT("nodes_formatted"), NodesFormatted);
	ResultObj->SetStringField(TEXT("formatter_used"), TEXT("blueprint_assist"));
	return ResultObj;
}

// ---------------------------------------------------------------------------
// Built-in layered layout (no Blueprint Assist dependency).
//
// Pure UEdGraph traversal: builds the connection DAG from each node's input
// pins, assigns a column = max(upstream column) + 1 via longest-path layering
// (Kahn-style relaxation that tolerates cycles), then writes NodePosX/NodePosY
// directly. Pose flows left->right (sources at column 0, the Output Pose / sink
// at the highest column, matching the editor's reading order). This path
// references no Blueprint Assist symbol and compiles with WITH_BLUEPRINT_ASSIST=0.
// ---------------------------------------------------------------------------

/**
 * Layered layout for a single graph. Returns a result JSON object on success,
 * or nullptr with OutError set. Writes NodePosX/NodePosY on every node.
 */
TSharedPtr<FJsonObject> BuiltinLayoutSingleGraph(
	const FString& GraphLabel, UEdGraph* Graph, float ColumnSpacing, float RowSpacing, FString& OutError)
{
	if (!Graph)
	{
		OutError = FString::Printf(TEXT("Graph '%s' is null"), *GraphLabel);
		return nullptr;
	}

	// Stable node set (skip nulls). Index by pointer for the relaxation pass.
	TArray<UEdGraphNode*> Nodes;
	Nodes.Reserve(Graph->Nodes.Num());
	for (UEdGraphNode* Node : Graph->Nodes)
	{
		if (Node)
		{
			Nodes.Add(Node);
		}
	}

	if (Nodes.Num() == 0)
	{
		// Empty graph is a no-op success, not an error.
		TSharedPtr<FJsonObject> EmptyObj = MakeShared<FJsonObject>();
		EmptyObj->SetStringField(TEXT("graph"), GraphLabel);
		EmptyObj->SetNumberField(TEXT("nodes_formatted"), 0);
		EmptyObj->SetStringField(TEXT("formatter_used"), TEXT("builtin"));
		return EmptyObj;
	}

	TMap<UEdGraphNode*, int32> IndexOf;
	IndexOf.Reserve(Nodes.Num());
	for (int32 i = 0; i < Nodes.Num(); ++i)
	{
		IndexOf.Add(Nodes[i], i);
	}

	// Upstream adjacency: for each node, the set of node-indices feeding ANY of
	// its input pins (a node's column must exceed all of these). Mirrors the
	// engine's own pin walk (EdGraphSchema_K2.cpp: Pin->Direction / Pin->LinkedTo
	// / LinkedPin->GetOwningNode()).
	TArray<TSet<int32>> Upstream;
	Upstream.SetNum(Nodes.Num());
	for (int32 i = 0; i < Nodes.Num(); ++i)
	{
		for (UEdGraphPin* Pin : Nodes[i]->Pins)
		{
			if (!Pin || Pin->Direction != EGPD_Input)
			{
				continue;
			}
			for (UEdGraphPin* LinkedPin : Pin->LinkedTo)
			{
				if (!LinkedPin)
				{
					continue;
				}
				UEdGraphNode* OwningNode = LinkedPin->GetOwningNode();
				if (const int32* SrcIdx = IndexOf.Find(OwningNode))
				{
					if (*SrcIdx != i) // ignore self-links
					{
						Upstream[i].Add(*SrcIdx);
					}
				}
			}
		}
	}

	// Longest-path layering by iterative relaxation. Column[i] = max upstream
	// column + 1. Bounded by Nodes.Num() iterations so cyclic graphs (which a
	// valid anim graph should not contain) terminate instead of looping forever.
	TArray<int32> Column;
	Column.Init(0, Nodes.Num());
	const int32 MaxIterations = Nodes.Num();
	for (int32 Iter = 0; Iter < MaxIterations; ++Iter)
	{
		bool bChanged = false;
		for (int32 i = 0; i < Nodes.Num(); ++i)
		{
			int32 Desired = 0;
			for (int32 Src : Upstream[i])
			{
				Desired = FMath::Max(Desired, Column[Src] + 1);
			}
			if (Desired > Column[i])
			{
				Column[i] = Desired;
				bChanged = true;
			}
		}
		if (!bChanged)
		{
			break;
		}
	}

	// Group nodes by column, preserving original graph order within a column to
	// keep the result deterministic and avoid overlap.
	int32 MaxColumn = 0;
	for (int32 c : Column)
	{
		MaxColumn = FMath::Max(MaxColumn, c);
	}

	TArray<TArray<int32>> ColumnBuckets;
	ColumnBuckets.SetNum(MaxColumn + 1);
	for (int32 i = 0; i < Nodes.Num(); ++i)
	{
		ColumnBuckets[Column[i]].Add(i);
	}

	// Assign positions. X increases with column (left-to-right pose flow). Within
	// a column, stack rows top-to-bottom with fixed spacing so no two nodes share
	// a position.
	const int32 SafeColumnSpacing = FMath::Max(1, FMath::RoundToInt(ColumnSpacing));
	const int32 SafeRowSpacing = FMath::Max(1, FMath::RoundToInt(RowSpacing));

	for (int32 c = 0; c <= MaxColumn; ++c)
	{
		const TArray<int32>& Bucket = ColumnBuckets[c];
		const int32 PosX = c * SafeColumnSpacing;
		for (int32 Row = 0; Row < Bucket.Num(); ++Row)
		{
			UEdGraphNode* Node = Nodes[Bucket[Row]];
			Node->NodePosX = PosX;
			Node->NodePosY = Row * SafeRowSpacing;
		}
	}

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("graph"), GraphLabel);
	ResultObj->SetNumberField(TEXT("nodes_formatted"), Nodes.Num());
	ResultObj->SetNumberField(TEXT("columns"), MaxColumn + 1);
	ResultObj->SetStringField(TEXT("formatter_used"), TEXT("builtin"));
	return ResultObj;
}

/**
 * Per-graph formatter dispatch. Chooses Blueprint Assist or the built-in layered
 * layout based on the requested formatter and BA availability:
 *   - bForceBuiltin: always built-in (formatter 'builtin'/'monolith').
 *   - bExplicitBA: BA only; errors via FormatSingleGraph if BA is unavailable.
 *   - 'auto': BA when available + supports the graph, otherwise built-in fallback.
 * Returns a result JSON object on success, or nullptr with OutError set.
 */
TSharedPtr<FJsonObject> LayoutSingleGraphDispatch(
	const FString& GraphLabel, UEdGraph* Graph,
	bool bExplicitBA, bool bForceBuiltin,
	float ColumnSpacing, float RowSpacing, FString& OutError)
{
	if (bForceBuiltin)
	{
		return BuiltinLayoutSingleGraph(GraphLabel, Graph, ColumnSpacing, RowSpacing, OutError);
	}

	const bool bBAAvailable = IMonolithGraphFormatter::IsAvailable()
		&& IMonolithGraphFormatter::Get().SupportsGraph(Graph);

	if (bExplicitBA)
	{
		// BA explicitly requested: use BA or surface BA's own error (no fallback).
		return FormatSingleGraph(GraphLabel, Graph, /*bExplicitBA=*/true, OutError);
	}

	// 'auto': prefer BA, fall back to built-in when BA is absent/unsupported.
	if (bBAAvailable)
	{
		return FormatSingleGraph(GraphLabel, Graph, /*bExplicitBA=*/false, OutError);
	}
	return BuiltinLayoutSingleGraph(GraphLabel, Graph, ColumnSpacing, RowSpacing, OutError);
}

} // anonymous namespace

// ---------------------------------------------------------------------------
// Action: auto_layout
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithAnimLayoutActions::HandleAutoLayout(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString GraphName = Params->HasField(TEXT("graph_name")) ? Params->GetStringField(TEXT("graph_name")) : TEXT("AnimGraph");
	FString Formatter = Params->HasField(TEXT("formatter")) ? Params->GetStringField(TEXT("formatter")) : TEXT("auto");

	// Validate formatter param. 'monolith' is accepted as an alias for 'builtin'
	// (the built-in layered layout IS the Monolith-native formatter now).
	if (Formatter != TEXT("auto") && Formatter != TEXT("blueprint_assist")
		&& Formatter != TEXT("builtin") && Formatter != TEXT("monolith"))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown formatter '%s'. Supported: 'auto', 'blueprint_assist', 'builtin', 'monolith'"), *Formatter));
	}

	// Built-in layout spacing (only used by the builtin path).
	const float ColumnSpacing = Params->HasField(TEXT("column_spacing"))
		? static_cast<float>(Params->GetNumberField(TEXT("column_spacing"))) : 320.0f;
	const float RowSpacing = Params->HasField(TEXT("row_spacing"))
		? static_cast<float>(Params->GetNumberField(TEXT("row_spacing"))) : 180.0f;

	// Load the AnimBlueprint
	UAnimBlueprint* ABP = FMonolithAssetUtils::LoadAssetByPath<UAnimBlueprint>(AssetPath);
	if (!ABP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("AnimBlueprint not found: %s"), *AssetPath));
	}

	const bool bExplicitBA = (Formatter == TEXT("blueprint_assist"));
	const bool bForceBuiltin = (Formatter == TEXT("builtin") || Formatter == TEXT("monolith"));

	// --- "all" mode: format every graph ---
	if (GraphName.Equals(TEXT("all"), ESearchCase::IgnoreCase))
	{
		TArray<TPair<FString, UEdGraph*>> AllGraphs;
		CollectAllGraphs(ABP, AllGraphs);

		if (AllGraphs.Num() == 0)
		{
			return FMonolithActionResult::Error(TEXT("No graphs found in this Animation Blueprint"));
		}

		TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
		Root->SetStringField(TEXT("asset_path"), AssetPath);
		Root->SetStringField(TEXT("mode"), TEXT("all"));

		TArray<TSharedPtr<FJsonValue>> ResultsArr;
		TArray<TSharedPtr<FJsonValue>> ErrorsArr;
		int32 TotalFormatted = 0;

		for (const auto& Pair : AllGraphs)
		{
			FString Error;
			TSharedPtr<FJsonObject> GraphResult = LayoutSingleGraphDispatch(
				Pair.Key, Pair.Value, bExplicitBA, bForceBuiltin, ColumnSpacing, RowSpacing, Error);
			if (GraphResult)
			{
				TotalFormatted++;
				ResultsArr.Add(MakeShared<FJsonValueObject>(GraphResult));
			}
			else
			{
				TSharedPtr<FJsonObject> ErrObj = MakeShared<FJsonObject>();
				ErrObj->SetStringField(TEXT("graph"), Pair.Key);
				ErrObj->SetStringField(TEXT("error"), Error);
				ErrorsArr.Add(MakeShared<FJsonValueObject>(ErrObj));
			}
		}

		Root->SetArrayField(TEXT("formatted"), ResultsArr);
		Root->SetNumberField(TEXT("graphs_formatted"), TotalFormatted);
		Root->SetNumberField(TEXT("graphs_total"), AllGraphs.Num());

		if (ErrorsArr.Num() > 0)
		{
			Root->SetArrayField(TEXT("errors"), ErrorsArr);
		}

		if (TotalFormatted == 0)
		{
			// All graphs failed — return error with details. With the built-in
			// fallback this only happens when BA is explicitly required and absent.
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Failed to format any of %d graphs. Try formatter='builtin' (no plugin needed), "
					 "or install Blueprint Assist and ensure the asset is open in the editor."),
				AllGraphs.Num()));
		}

		return FMonolithActionResult::Success(Root);
	}

	// --- Single graph mode ---
	UEdGraph* TargetGraph = nullptr;
	FString GraphLabel;

	if (GraphName.Equals(TEXT("AnimGraph"), ESearchCase::IgnoreCase) || GraphName.IsEmpty())
	{
		TargetGraph = FindAnimGraph(ABP);
		GraphLabel = TEXT("AnimGraph");
		if (!TargetGraph)
		{
			return FMonolithActionResult::Error(TEXT("No AnimGraph found in this Animation Blueprint"));
		}
	}
	else
	{
		// Treat as state machine name
		TargetGraph = FindSMGraphByTitle(ABP, GraphName);
		GraphLabel = GraphName;
		if (!TargetGraph)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Graph '%s' not found. Use 'AnimGraph' for the main graph, a state machine name, or 'all'."),
				*GraphName));
		}
	}

	FString Error;
	TSharedPtr<FJsonObject> GraphResult = LayoutSingleGraphDispatch(
		GraphLabel, TargetGraph, bExplicitBA, bForceBuiltin, ColumnSpacing, RowSpacing, Error);
	if (!GraphResult)
	{
		return FMonolithActionResult::Error(Error);
	}

	// Wrap in a top-level result
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("graph"), GraphLabel);
	Root->SetNumberField(TEXT("nodes_formatted"), GraphResult->GetNumberField(TEXT("nodes_formatted")));
	Root->SetStringField(TEXT("formatter_used"), GraphResult->GetStringField(TEXT("formatter_used")));

	return FMonolithActionResult::Success(Root);
}
