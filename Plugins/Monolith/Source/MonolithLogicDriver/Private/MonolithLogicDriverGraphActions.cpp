#include "MonolithLogicDriverGraphActions.h"
#include "MonolithParamSchema.h"

#if WITH_LOGICDRIVER

#include "MonolithLogicDriverInternal.h"
#include "IMonolithGraphFormatter.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Kismet2/BlueprintEditorUtils.h"

DEFINE_LOG_CATEGORY_STATIC(LogMonolithLDGraph, Log, All);

void FMonolithLogicDriverGraphActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ── Read (Phase 1) ──

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("get_sm_structure"),
		TEXT("Get hierarchical JSON structure of an entire state machine: states, transitions, conduits, nested SMs, GUIDs"),
		FMonolithActionHandler::CreateStatic(&HandleGetSMStructure),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Optional(TEXT("depth"), TEXT("number"), TEXT("Max nesting depth (-1 = unlimited)"), TEXT("-1"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("get_node_details"),
		TEXT("Get detailed info for a specific node including all UPROPERTY values and connections"),
		FMonolithActionHandler::CreateStatic(&HandleGetNodeDetails),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Node GUID to inspect"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("get_node_connections"),
		TEXT("List all inbound and outbound transitions for a node"),
		FMonolithActionHandler::CreateStatic(&HandleGetNodeConnections),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Node GUID to query connections for"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("find_nodes_by_type"),
		TEXT("Find all nodes of a given type (state/transition/conduit/any_state/state_machine) in the SM"),
		FMonolithActionHandler::CreateStatic(&HandleFindNodesByType),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_type"), TEXT("string"), TEXT("Node type: state, transition, conduit, any_state, state_machine"))
			.Build());

	// ── Write (Phase 2A) ──

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("add_state"),
		TEXT("Add a state node to a Logic Driver state machine graph"),
		FMonolithActionHandler::CreateStatic(&HandleAddState),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Optional(TEXT("name"), TEXT("string"), TEXT("State name"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("X position in graph"), TEXT("0"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Y position in graph"), TEXT("0"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("add_transition"),
		TEXT("Add a transition between two nodes in a Logic Driver state machine"),
		FMonolithActionHandler::CreateStatic(&HandleAddTransition),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("source_guid"), TEXT("string"), TEXT("Source node GUID"))
			.Required(TEXT("target_guid"), TEXT("string"), TEXT("Target node GUID"))
			.Optional(TEXT("priority"), TEXT("number"), TEXT("Transition priority"), TEXT("0"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("add_conduit"),
		TEXT("Add a conduit node to a Logic Driver state machine graph"),
		FMonolithActionHandler::CreateStatic(&HandleAddConduit),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Optional(TEXT("name"), TEXT("string"), TEXT("Conduit name"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("X position in graph"), TEXT("0"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Y position in graph"), TEXT("0"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("add_state_machine_node"),
		TEXT("Add a nested state machine node to a Logic Driver state machine graph"),
		FMonolithActionHandler::CreateStatic(&HandleAddStateMachineNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Optional(TEXT("name"), TEXT("string"), TEXT("Nested SM name"))
			.OptionalAssetPath(TEXT("reference_path"), TEXT("Path to existing SM Blueprint to reference"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("X position in graph"), TEXT("0"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Y position in graph"), TEXT("0"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("add_any_state_node"),
		TEXT("Add an Any State node to a Logic Driver state machine graph"),
		FMonolithActionHandler::CreateStatic(&HandleAddAnyStateNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Optional(TEXT("position_x"), TEXT("number"), TEXT("X position in graph"), TEXT("0"))
			.Optional(TEXT("position_y"), TEXT("number"), TEXT("Y position in graph"), TEXT("0"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("remove_node"),
		TEXT("Remove a node from a Logic Driver state machine graph (breaks all connections first)"),
		FMonolithActionHandler::CreateStatic(&HandleRemoveNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("GUID of node to remove"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("set_node_properties"),
		TEXT("Set UPROPERTY values on a Logic Driver node via reflection"),
		FMonolithActionHandler::CreateStatic(&HandleSetNodeProperties),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Node GUID"))
			.Required(TEXT("properties"), TEXT("object"), TEXT("Key-value pairs of property names to values"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("set_initial_state"),
		TEXT("Set a state as the initial state by rewiring the entry node"),
		FMonolithActionHandler::CreateStatic(&HandleSetInitialState),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("GUID of state to make initial"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("set_end_state"),
		TEXT("Set or clear the end state flag on a state node"),
		FMonolithActionHandler::CreateStatic(&HandleSetEndState),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Node GUID"))
			.Required(TEXT("is_end_state"), TEXT("boolean"), TEXT("Whether this state is an end state"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("set_node_class"),
		TEXT("Set the custom node class (NodeInstanceClass) on a Logic Driver node via reflection"),
		FMonolithActionHandler::CreateStatic(&HandleSetNodeClass),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Node GUID"))
			.RequiredAssetPath(TEXT("class_path"), TEXT("Full class path for the node instance class"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("rename_node"),
		TEXT("Rename a node in a Logic Driver state machine"),
		FMonolithActionHandler::CreateStatic(&HandleRenameNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Node GUID"))
			.Required(TEXT("new_name"), TEXT("string"), TEXT("New name for the node"))
			.Build());

	// ── Compile (Phase 1) ──

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("compile_state_machine"),
		TEXT("Compile a Logic Driver State Machine Blueprint and return success/failure with error messages"),
		FMonolithActionHandler::CreateStatic(&HandleCompileStateMachine),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path to compile"))
			.Build());

	// ── Advanced Read (Phase 2C) ──

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("find_nodes_by_class"),
		TEXT("Find all nodes whose class name matches a given string (full or partial match)"),
		FMonolithActionHandler::CreateStatic(&HandleFindNodesByClass),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("class_name"), TEXT("string"), TEXT("Full or partial class name to match against node classes"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("get_sm_statistics"),
		TEXT("Get statistics for a state machine: state/transition/conduit/nested SM counts, max depth, total nodes"),
		FMonolithActionHandler::CreateStatic(&HandleGetSMStatistics),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Build());

	// ── Layout (Phase 4) ──

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("move_node"),
		TEXT("Move a node to a specific position in the graph editor"),
		FMonolithActionHandler::CreateStatic(&HandleMoveNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Node GUID to move"))
			.Required(TEXT("position_x"), TEXT("number"), TEXT("New X position"))
			.Required(TEXT("position_y"), TEXT("number"), TEXT("New Y position"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("auto_arrange_graph"),
		TEXT("Auto-arrange all nodes in a state machine graph. Uses Blueprint Assist formatter if available, otherwise built-in BFS layout"),
		FMonolithActionHandler::CreateStatic(&HandleAutoArrangeGraph),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Optional(TEXT("formatter"), TEXT("string"), TEXT("Formatter to use: default, blueprint_assist, builtin"), TEXT("default"))
			.Build());

	UE_LOG(LogMonolithLDGraph, Log, TEXT("MonolithLogicDriver Graph: registered 20 actions (6 read + 13 write + compile)"));
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleGetSMStructure(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	}

	int32 Depth = -1;
	if (Params->HasField(TEXT("depth")))
	{
		Depth = static_cast<int32>(Params->GetNumberField(TEXT("depth")));
	}

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint)
	{
		return FMonolithActionResult::Error(LoadError);
	}

	TSharedPtr<FJsonObject> Structure = MonolithLD::SMStructureToJson(SMBlueprint, Depth);
	if (!Structure.IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Failed to serialize SM structure"));
	}

	return FMonolithActionResult::Success(Structure);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleGetNodeDetails(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	if (AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	}
	if (NodeGuid.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));
	}

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint)
	{
		return FMonolithActionResult::Error(LoadError);
	}

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(SMBlueprint);
	if (!RootGraph)
	{
		return FMonolithActionResult::Error(TEXT("No root SM graph found"));
	}

	UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!Node)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));
	}

	// Get detailed node JSON from the helper
	TSharedPtr<FJsonObject> Result = MonolithLD::NodeToJson(Node, /*bDetailed=*/ true);

	// Add all UPROPERTY values via reflection
	TSharedPtr<FJsonObject> Properties = MakeShared<FJsonObject>();
	for (TFieldIterator<FProperty> PropIt(Node->GetClass()); PropIt; ++PropIt)
	{
		FProperty* Prop = *PropIt;
		if (!Prop || !Prop->HasAnyPropertyFlags(CPF_Edit | CPF_BlueprintVisible))
		{
			continue;
		}

		FString ValueStr;
		const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Node);
		Prop->ExportTextItem_Direct(ValueStr, ValuePtr, nullptr, Node, PPF_None);
		Properties->SetStringField(Prop->GetName(), ValueStr);
	}
	Result->SetObjectField(TEXT("properties"), Properties);

	// Full connection list with details
	TArray<TSharedPtr<FJsonValue>> AllConnections;
	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (!Pin) continue;
		for (UEdGraphPin* LinkedPin : Pin->LinkedTo)
		{
			if (!LinkedPin || !LinkedPin->GetOwningNode()) continue;

			UEdGraphNode* ConnectedRaw = LinkedPin->GetOwningNode();
			TSharedPtr<FJsonObject> ConnJson = MakeShared<FJsonObject>();
			ConnJson->SetStringField(TEXT("node_guid"), ConnectedRaw->NodeGuid.ToString());
			ConnJson->SetStringField(TEXT("direction"), Pin->Direction == EGPD_Input ? TEXT("inbound") : TEXT("outbound"));
			ConnJson->SetStringField(TEXT("pin_name"), Pin->PinName.ToString());
			ConnJson->SetStringField(TEXT("connected_pin_name"), LinkedPin->PinName.ToString());

			// Get name — use GetNodeTitle for all nodes (no direct SM cast needed)
			ConnJson->SetStringField(TEXT("node_name"), ConnectedRaw->GetNodeTitle(ENodeTitleType::FullTitle).ToString());

			AllConnections.Add(MakeShared<FJsonValueObject>(ConnJson));
		}
	}
	Result->SetArrayField(TEXT("all_connections"), AllConnections);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleGetNodeConnections(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	if (AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	}
	if (NodeGuid.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));
	}

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint)
	{
		return FMonolithActionResult::Error(LoadError);
	}

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(SMBlueprint);
	if (!RootGraph)
	{
		return FMonolithActionResult::Error(TEXT("No root SM graph found"));
	}

	UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!Node)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));
	}

	TArray<TSharedPtr<FJsonValue>> Inbound;
	TArray<TSharedPtr<FJsonValue>> Outbound;

	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (!Pin) continue;

		for (UEdGraphPin* LinkedPin : Pin->LinkedTo)
		{
			if (!LinkedPin || !LinkedPin->GetOwningNode()) continue;

			UEdGraphNode* ConnectedRaw = LinkedPin->GetOwningNode();
			TSharedPtr<FJsonObject> ConnJson = MakeShared<FJsonObject>();
			ConnJson->SetStringField(TEXT("node_guid"), ConnectedRaw->NodeGuid.ToString());
			ConnJson->SetStringField(TEXT("name"), ConnectedRaw->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
			ConnJson->SetStringField(TEXT("type"), MonolithLD::GetNodeType(ConnectedRaw));

			if (Pin->Direction == EGPD_Input)
			{
				Inbound.Add(MakeShared<FJsonValueObject>(ConnJson));
			}
			else
			{
				Outbound.Add(MakeShared<FJsonValueObject>(ConnJson));
			}
		}
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("inbound"), Inbound);
	Result->SetArrayField(TEXT("outbound"), Outbound);
	Result->SetNumberField(TEXT("inbound_count"), Inbound.Num());
	Result->SetNumberField(TEXT("outbound_count"), Outbound.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleFindNodesByType(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeType = Params->GetStringField(TEXT("node_type"));
	if (AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	}
	if (NodeType.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'node_type'"));
	}

	// Validate node_type
	NodeType = NodeType.ToLower();
	if (NodeType != TEXT("state") && NodeType != TEXT("transition") && NodeType != TEXT("conduit")
		&& NodeType != TEXT("any_state") && NodeType != TEXT("state_machine"))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Invalid node_type '%s'. Must be: state, transition, conduit, any_state, state_machine"), *NodeType));
	}

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint)
	{
		return FMonolithActionResult::Error(LoadError);
	}

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(SMBlueprint);
	if (!RootGraph)
	{
		return FMonolithActionResult::Error(TEXT("No root SM graph found"));
	}

	TArray<TSharedPtr<FJsonValue>> MatchingNodes;

	for (UEdGraphNode* RawNode : RootGraph->Nodes)
	{
		if (!RawNode) continue;

		FString DetectedType = MonolithLD::GetNodeType(RawNode);
		if (DetectedType == NodeType)
		{
			TSharedPtr<FJsonObject> NodeJson = MonolithLD::NodeToJson(RawNode);
			MatchingNodes.Add(MakeShared<FJsonValueObject>(NodeJson));
		}
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("nodes"), MatchingNodes);
	Result->SetNumberField(TEXT("count"), MatchingNodes.Num());
	Result->SetStringField(TEXT("node_type"), NodeType);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleFindNodesByClass(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString ClassName = Params->GetStringField(TEXT("class_name"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (ClassName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'class_name'"));

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(SMBlueprint);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	TArray<TSharedPtr<FJsonValue>> MatchingNodes;

	for (UEdGraphNode* RawNode : RootGraph->Nodes)
	{
		if (!RawNode) continue;
		FString NodeClassName = RawNode->GetClass()->GetName();
		if (NodeClassName.Contains(ClassName))
		{
			TSharedPtr<FJsonObject> NodeJson = MonolithLD::NodeToJson(RawNode, true);
			NodeJson->SetStringField(TEXT("node_class"), NodeClassName);
			MatchingNodes.Add(MakeShared<FJsonValueObject>(NodeJson));
		}
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("nodes"), MatchingNodes);
	Result->SetNumberField(TEXT("count"), MatchingNodes.Num());
	Result->SetStringField(TEXT("class_name_filter"), ClassName);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleGetSMStatistics(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(SMBlueprint);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	int32 StateCount = 0, TransitionCount = 0, ConduitCount = 0;
	int32 NestedSMCount = 0, AnyStateCount = 0, EntryCount = 0;
	int32 TotalNodes = 0;
	bool bHasInitialState = false;
	int32 EndStateCount = 0;
	int32 OrphanedStateCount = 0; // States with no inbound connections (except initial)

	for (UEdGraphNode* RawNode : RootGraph->Nodes)
	{
		if (!RawNode) continue;
		TotalNodes++;

		FString NodeType = MonolithLD::GetNodeType(RawNode);
		if (NodeType == TEXT("state"))
		{
			StateCount++;
			if (MonolithLD::GetBoolProperty(RawNode, TEXT("bIsEndState")))
			{
				EndStateCount++;
			}
			// Check if initial (connected from entry)
			bool bIsInitial = false;
			bool bHasInbound = false;
			UClass* BaseClass = MonolithLD::GetSMGraphNodeBaseClass();
			for (UEdGraphPin* Pin : RawNode->Pins)
			{
				if (Pin && Pin->Direction == EGPD_Input)
				{
					for (UEdGraphPin* LinkedPin : Pin->LinkedTo)
					{
						if (LinkedPin && LinkedPin->GetOwningNode())
						{
							bHasInbound = true;
							UEdGraphNode* SourceNode = LinkedPin->GetOwningNode();
							if (!BaseClass || !SourceNode->GetClass()->IsChildOf(BaseClass))
							{
								bIsInitial = true;
							}
						}
					}
				}
			}
			if (bIsInitial) bHasInitialState = true;
			if (!bHasInbound && !bIsInitial) OrphanedStateCount++;
		}
		else if (NodeType == TEXT("transition")) TransitionCount++;
		else if (NodeType == TEXT("conduit"))     ConduitCount++;
		else if (NodeType == TEXT("state_machine")) NestedSMCount++;
		else if (NodeType == TEXT("any_state"))   AnyStateCount++;
		else if (NodeType == TEXT("entry"))       EntryCount++;
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetNumberField(TEXT("total_nodes"), TotalNodes);
	Result->SetNumberField(TEXT("states"), StateCount);
	Result->SetNumberField(TEXT("transitions"), TransitionCount);
	Result->SetNumberField(TEXT("conduits"), ConduitCount);
	Result->SetNumberField(TEXT("nested_state_machines"), NestedSMCount);
	Result->SetNumberField(TEXT("any_state_nodes"), AnyStateCount);
	Result->SetNumberField(TEXT("entry_nodes"), EntryCount);
	Result->SetNumberField(TEXT("end_states"), EndStateCount);
	Result->SetNumberField(TEXT("orphaned_states"), OrphanedStateCount);
	Result->SetBoolField(TEXT("has_initial_state"), bHasInitialState);

	// Complexity: transitions / states ratio
	if (StateCount > 0)
	{
		Result->SetNumberField(TEXT("transition_density"), static_cast<double>(TransitionCount) / StateCount);
	}

	return FMonolithActionResult::Success(Result);
}

// ── Shared helper: load blueprint + get root graph + mark dirty after lambda ──
namespace
{
	/** Set a UPROPERTY on a UObject via reflection using an exported text value. Returns true on success. */
	bool SetPropertyByName(UObject* Obj, const FString& PropName, const FString& Value)
	{
		if (!Obj) return false;
		FProperty* Prop = Obj->GetClass()->FindPropertyByName(*PropName);
		if (!Prop) return false;
		void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Obj);
		return Prop->ImportText_Direct(*Value, ValuePtr, Obj, PPF_None) != nullptr;
	}

	/** Create a graph node of the given class in the graph. Common boilerplate. */
	UEdGraphNode* CreateGraphNode(UEdGraph* Graph, UClass* NodeClass, int32 PosX, int32 PosY)
	{
		if (!Graph || !NodeClass) return nullptr;
		UEdGraphNode* NewNode = NewObject<UEdGraphNode>(Graph, NodeClass);
		NewNode->CreateNewGuid();
		NewNode->NodePosX = PosX;
		NewNode->NodePosY = PosY;
		Graph->AddNode(NewNode, /*bFromUI=*/false, /*bSelectNewNode=*/false);
		NewNode->PostPlacedNewNode();
		NewNode->AllocateDefaultPins();
		return NewNode;
	}

	/** Try to set a node's name via NodeInstanceTemplate->NodeDescription.Name. */
	void TrySetNodeName(UEdGraphNode* Node, const FString& Name)
	{
		if (Name.IsEmpty() || !Node) return;
		MonolithLD::SetNodeName(Node, Name);
	}

	/** Mark blueprint as structurally modified + dirty. */
	void MarkModified(UBlueprint* Blueprint)
	{
		if (!Blueprint) return;
		Blueprint->Modify();
		Blueprint->MarkPackageDirty();
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
	}
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleAddState(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty())
		return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UClass* StateClass = MonolithLD::GetSMGraphNodeStateClass();
	if (!StateClass) return FMonolithActionResult::Error(TEXT("SMGraphNode_StateNode class not found — is Logic Driver loaded?"));

	int32 PosX = Params->HasField(TEXT("position_x")) ? static_cast<int32>(Params->GetNumberField(TEXT("position_x"))) : 0;
	int32 PosY = Params->HasField(TEXT("position_y")) ? static_cast<int32>(Params->GetNumberField(TEXT("position_y"))) : 0;

	UEdGraphNode* NewNode = CreateGraphNode(RootGraph, StateClass, PosX, PosY);
	if (!NewNode) return FMonolithActionResult::Error(TEXT("Failed to create state node"));

	FString Name = Params->GetStringField(TEXT("name"));
	TrySetNodeName(NewNode, Name);

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MonolithLD::NodeToJson(NewNode, true);
	Result->SetStringField(TEXT("action"), TEXT("add_state"));
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleAddTransition(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString SourceGuid = Params->GetStringField(TEXT("source_guid"));
	FString TargetGuid = Params->GetStringField(TEXT("target_guid"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (SourceGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'source_guid'"));
	if (TargetGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'target_guid'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UEdGraphNode* SourceNode = MonolithLD::FindNodeByGuid(RootGraph, SourceGuid);
	if (!SourceNode) return FMonolithActionResult::Error(FString::Printf(TEXT("Source node not found: %s"), *SourceGuid));

	UEdGraphNode* TargetNode = MonolithLD::FindNodeByGuid(RootGraph, TargetGuid);
	if (!TargetNode) return FMonolithActionResult::Error(FString::Printf(TEXT("Target node not found: %s"), *TargetGuid));

	UClass* TransClass = MonolithLD::GetSMGraphNodeTransitionClass();
	if (!TransClass) return FMonolithActionResult::Error(TEXT("SMGraphNode_TransitionEdge class not found"));

	// Position transition midway between source and target
	int32 PosX = (SourceNode->NodePosX + TargetNode->NodePosX) / 2;
	int32 PosY = (SourceNode->NodePosY + TargetNode->NodePosY) / 2;

	UEdGraphNode* TransNode = CreateGraphNode(RootGraph, TransClass, PosX, PosY);
	if (!TransNode) return FMonolithActionResult::Error(TEXT("Failed to create transition node"));

	// Wire: source output -> transition input, transition output -> target input
	UEdGraphPin* SourceOutPin = nullptr;
	for (UEdGraphPin* Pin : SourceNode->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Output) { SourceOutPin = Pin; break; }
	}

	UEdGraphPin* TransInPin = nullptr;
	UEdGraphPin* TransOutPin = nullptr;
	for (UEdGraphPin* Pin : TransNode->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Input && !TransInPin) TransInPin = Pin;
		if (Pin && Pin->Direction == EGPD_Output && !TransOutPin) TransOutPin = Pin;
	}

	UEdGraphPin* TargetInPin = nullptr;
	for (UEdGraphPin* Pin : TargetNode->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Input) { TargetInPin = Pin; break; }
	}

	if (SourceOutPin && TransInPin) SourceOutPin->MakeLinkTo(TransInPin);
	if (TransOutPin && TargetInPin) TransOutPin->MakeLinkTo(TargetInPin);

	// Set priority if specified
	if (Params->HasField(TEXT("priority")))
	{
		int32 Priority = static_cast<int32>(Params->GetNumberField(TEXT("priority")));
		SetPropertyByName(TransNode, TEXT("PriorityOrder"), FString::FromInt(Priority));
	}

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MonolithLD::NodeToJson(TransNode, true);
	Result->SetStringField(TEXT("action"), TEXT("add_transition"));
	Result->SetStringField(TEXT("source_guid"), SourceGuid);
	Result->SetStringField(TEXT("target_guid"), TargetGuid);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleAddConduit(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UClass* ConduitClass = MonolithLD::GetSMGraphNodeConduitClass();
	if (!ConduitClass) return FMonolithActionResult::Error(TEXT("SMGraphNode_ConduitNode class not found"));

	int32 PosX = Params->HasField(TEXT("position_x")) ? static_cast<int32>(Params->GetNumberField(TEXT("position_x"))) : 0;
	int32 PosY = Params->HasField(TEXT("position_y")) ? static_cast<int32>(Params->GetNumberField(TEXT("position_y"))) : 0;

	UEdGraphNode* NewNode = CreateGraphNode(RootGraph, ConduitClass, PosX, PosY);
	if (!NewNode) return FMonolithActionResult::Error(TEXT("Failed to create conduit node"));

	FString Name = Params->GetStringField(TEXT("name"));
	TrySetNodeName(NewNode, Name);

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MonolithLD::NodeToJson(NewNode, true);
	Result->SetStringField(TEXT("action"), TEXT("add_conduit"));
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleAddStateMachineNode(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UClass* SMNodeClass = MonolithLD::GetSMGraphNodeSMClass();
	if (!SMNodeClass) return FMonolithActionResult::Error(TEXT("SMGraphNode_StateMachineStateNode class not found"));

	int32 PosX = Params->HasField(TEXT("position_x")) ? static_cast<int32>(Params->GetNumberField(TEXT("position_x"))) : 0;
	int32 PosY = Params->HasField(TEXT("position_y")) ? static_cast<int32>(Params->GetNumberField(TEXT("position_y"))) : 0;

	UEdGraphNode* NewNode = CreateGraphNode(RootGraph, SMNodeClass, PosX, PosY);
	if (!NewNode) return FMonolithActionResult::Error(TEXT("Failed to create state machine node"));

	FString Name = Params->GetStringField(TEXT("name"));
	TrySetNodeName(NewNode, Name);

	// If a reference_path is provided, try to set it via reflection
	FString ReferencePath = Params->GetStringField(TEXT("reference_path"));
	if (!ReferencePath.IsEmpty())
	{
		// Try setting ReferencedStateMachine or similar property
		SetPropertyByName(NewNode, TEXT("ReferencedStateMachineName"), ReferencePath);
		SetPropertyByName(NewNode, TEXT("ReferencedStateMachine"), ReferencePath);
	}

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MonolithLD::NodeToJson(NewNode, true);
	Result->SetStringField(TEXT("action"), TEXT("add_state_machine_node"));
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleAddAnyStateNode(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UClass* AnyStateClass = MonolithLD::GetSMGraphNodeAnyStateClass();
	if (!AnyStateClass) return FMonolithActionResult::Error(TEXT("SMGraphNode_AnyStateNode class not found"));

	int32 PosX = Params->HasField(TEXT("position_x")) ? static_cast<int32>(Params->GetNumberField(TEXT("position_x"))) : 0;
	int32 PosY = Params->HasField(TEXT("position_y")) ? static_cast<int32>(Params->GetNumberField(TEXT("position_y"))) : 0;

	UEdGraphNode* NewNode = CreateGraphNode(RootGraph, AnyStateClass, PosX, PosY);
	if (!NewNode) return FMonolithActionResult::Error(TEXT("Failed to create Any State node"));

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MonolithLD::NodeToJson(NewNode, true);
	Result->SetStringField(TEXT("action"), TEXT("add_any_state_node"));
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleRemoveNode(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (NodeGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!Node) return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));

	// Don't allow removing the entry node
	FString NodeType = MonolithLD::GetNodeType(Node);
	if (NodeType == TEXT("entry"))
	{
		return FMonolithActionResult::Error(TEXT("Cannot remove the entry node"));
	}

	// Break all pin connections first
	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (Pin)
		{
			Pin->BreakAllPinLinks();
		}
	}

	// Capture info before removal
	FString RemovedName = Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString();

	Node->DestroyNode();

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("action"), TEXT("remove_node"));
	Result->SetStringField(TEXT("removed_guid"), NodeGuid);
	Result->SetStringField(TEXT("removed_name"), RemovedName);
	Result->SetStringField(TEXT("removed_type"), NodeType);
	Result->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleSetNodeProperties(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (NodeGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));

	const TSharedPtr<FJsonObject>* PropertiesObj = nullptr;
	if (!Params->TryGetObjectField(TEXT("properties"), PropertiesObj) || !PropertiesObj || !(*PropertiesObj).IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param 'properties' (must be an object)"));
	}

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!Node) return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));

	TArray<FString> SetProps;
	TArray<FString> FailedProps;

	for (const auto& Pair : (*PropertiesObj)->Values)
	{
		FString ValueStr;
		if (Pair.Value->Type == EJson::String)
		{
			ValueStr = Pair.Value->AsString();
		}
		else if (Pair.Value->Type == EJson::Number)
		{
			ValueStr = FString::SanitizeFloat(Pair.Value->AsNumber());
		}
		else if (Pair.Value->Type == EJson::Boolean)
		{
			ValueStr = Pair.Value->AsBool() ? TEXT("True") : TEXT("False");
		}
		else
		{
			// For complex types, try string representation
			ValueStr = Pair.Value->AsString();
		}

		if (SetPropertyByName(Node, Pair.Key, ValueStr))
		{
			SetProps.Add(Pair.Key);
		}
		else
		{
			FailedProps.Add(Pair.Key);
		}
	}

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("action"), TEXT("set_node_properties"));
	Result->SetStringField(TEXT("node_guid"), NodeGuid);
	Result->SetNumberField(TEXT("set_count"), SetProps.Num());
	Result->SetNumberField(TEXT("failed_count"), FailedProps.Num());

	TArray<TSharedPtr<FJsonValue>> SetArr, FailArr;
	for (const FString& S : SetProps) SetArr.Add(MakeShared<FJsonValueString>(S));
	for (const FString& S : FailedProps) FailArr.Add(MakeShared<FJsonValueString>(S));
	Result->SetArrayField(TEXT("set_properties"), SetArr);
	Result->SetArrayField(TEXT("failed_properties"), FailArr);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleSetInitialState(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (NodeGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UEdGraphNode* TargetNode = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!TargetNode) return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));

	// Find the entry node — it's the one whose type is "entry"
	UEdGraphNode* EntryNode = nullptr;
	for (UEdGraphNode* N : RootGraph->Nodes)
	{
		if (N && MonolithLD::GetNodeType(N) == TEXT("entry"))
		{
			EntryNode = N;
			break;
		}
	}
	if (!EntryNode)
	{
		return FMonolithActionResult::Error(TEXT("No entry node found in the state machine graph"));
	}

	// Find the entry node's output pin
	UEdGraphPin* EntryOutPin = nullptr;
	for (UEdGraphPin* Pin : EntryNode->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Output)
		{
			EntryOutPin = Pin;
			break;
		}
	}
	if (!EntryOutPin)
	{
		return FMonolithActionResult::Error(TEXT("Entry node has no output pin"));
	}

	// Break existing connection from entry
	FString PreviousInitialGuid;
	if (EntryOutPin->LinkedTo.Num() > 0 && EntryOutPin->LinkedTo[0])
	{
		PreviousInitialGuid = EntryOutPin->LinkedTo[0]->GetOwningNode()->NodeGuid.ToString();
	}
	EntryOutPin->BreakAllPinLinks();

	// Connect entry to target node's input pin
	UEdGraphPin* TargetInPin = nullptr;
	for (UEdGraphPin* Pin : TargetNode->Pins)
	{
		if (Pin && Pin->Direction == EGPD_Input)
		{
			TargetInPin = Pin;
			break;
		}
	}
	if (!TargetInPin)
	{
		return FMonolithActionResult::Error(TEXT("Target node has no input pin"));
	}

	EntryOutPin->MakeLinkTo(TargetInPin);

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("action"), TEXT("set_initial_state"));
	Result->SetStringField(TEXT("node_guid"), NodeGuid);
	Result->SetStringField(TEXT("previous_initial_guid"), PreviousInitialGuid);
	Result->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleSetEndState(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (NodeGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));

	bool bIsEndState = true;
	if (Params->HasField(TEXT("is_end_state")))
	{
		bIsEndState = Params->GetBoolField(TEXT("is_end_state"));
	}

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!Node) return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));

	// Set bIsEndState via reflection
	FString ValueStr = bIsEndState ? TEXT("True") : TEXT("False");
	bool bSet = SetPropertyByName(Node, TEXT("bIsEndState"), ValueStr);
	if (!bSet)
	{
		// Try alternate property name
		bSet = SetPropertyByName(Node, TEXT("bAlwaysUpdate"), ValueStr);  // fallback
		if (!bSet)
		{
			return FMonolithActionResult::Error(TEXT("Could not find bIsEndState property on this node — is it a state node?"));
		}
	}

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("action"), TEXT("set_end_state"));
	Result->SetStringField(TEXT("node_guid"), NodeGuid);
	Result->SetBoolField(TEXT("is_end_state"), bIsEndState);
	Result->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleSetNodeClass(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	FString ClassPath = Params->GetStringField(TEXT("class_path"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (NodeGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));
	if (ClassPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'class_path'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!Node) return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));

	// Resolve the class
	UClass* NodeInstanceClass = FindFirstObject<UClass>(*ClassPath, EFindFirstObjectOptions::NativeFirst);
	if (!NodeInstanceClass)
	{
		// Try loading as a Blueprint-generated class
		UObject* LoadedObj = StaticLoadObject(UClass::StaticClass(), nullptr, *ClassPath);
		NodeInstanceClass = Cast<UClass>(LoadedObj);
	}
	if (!NodeInstanceClass)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Could not find or load class: %s"), *ClassPath));
	}

	// Try setting via reflection — Logic Driver uses NodeInstanceClass property
	static const FName CandidateProps[] = {
		TEXT("NodeInstanceClass"), TEXT("StateClass"), TEXT("TransitionClass"), TEXT("ConduitClass")
	};

	bool bSet = false;
	for (const FName& PropName : CandidateProps)
	{
		FProperty* Prop = Node->GetClass()->FindPropertyByName(PropName);
		if (!Prop) continue;

		FClassProperty* ClassProp = CastField<FClassProperty>(Prop);
		if (ClassProp)
		{
			void* ValuePtr = ClassProp->ContainerPtrToValuePtr<void>(Node);
			ClassProp->SetObjectPropertyValue(ValuePtr, NodeInstanceClass);
			bSet = true;
			break;
		}
		// Also try FSoftClassPath / TSoftClassPtr via text import
		FString ExportText = NodeInstanceClass->GetPathName();
		void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Node);
		if (Prop->ImportText_Direct(*ExportText, ValuePtr, Node, PPF_None))
		{
			bSet = true;
			break;
		}
	}

	if (!bSet)
	{
		return FMonolithActionResult::Error(TEXT("Could not find a suitable class property (NodeInstanceClass, StateClass, etc.) on this node"));
	}

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("action"), TEXT("set_node_class"));
	Result->SetStringField(TEXT("node_guid"), NodeGuid);
	Result->SetStringField(TEXT("class_path"), NodeInstanceClass->GetPathName());
	Result->SetStringField(TEXT("class_name"), NodeInstanceClass->GetName());
	Result->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleRenameNode(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	FString NewName = Params->GetStringField(TEXT("new_name"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (NodeGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));
	if (NewName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'new_name'"));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!Node) return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));

	FString OldName = MonolithLD::GetNodeName(Node);

	MonolithLD::SetNodeName(Node, NewName);

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("action"), TEXT("rename_node"));
	Result->SetStringField(TEXT("node_guid"), NodeGuid);
	Result->SetStringField(TEXT("old_name"), OldName);
	Result->SetStringField(TEXT("new_name"), NewName);
	Result->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleMoveNode(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	if (NodeGuid.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'node_guid'"));
	if (!Params->HasField(TEXT("position_x"))) return FMonolithActionResult::Error(TEXT("Missing required param 'position_x'"));
	if (!Params->HasField(TEXT("position_y"))) return FMonolithActionResult::Error(TEXT("Missing required param 'position_y'"));

	int32 PosX = static_cast<int32>(Params->GetNumberField(TEXT("position_x")));
	int32 PosY = static_cast<int32>(Params->GetNumberField(TEXT("position_y")));

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, NodeGuid);
	if (!Node) return FMonolithActionResult::Error(FString::Printf(TEXT("Node not found with GUID '%s'"), *NodeGuid));

	int32 OldX = Node->NodePosX;
	int32 OldY = Node->NodePosY;

	Node->NodePosX = PosX;
	Node->NodePosY = PosY;

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("action"), TEXT("move_node"));
	Result->SetStringField(TEXT("node_guid"), NodeGuid);
	Result->SetNumberField(TEXT("old_x"), OldX);
	Result->SetNumberField(TEXT("old_y"), OldY);
	Result->SetNumberField(TEXT("new_x"), PosX);
	Result->SetNumberField(TEXT("new_y"), PosY);
	Result->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleAutoArrangeGraph(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));

	FString FormatterMode = TEXT("default");
	if (Params->HasField(TEXT("formatter")))
	{
		FormatterMode = Params->GetStringField(TEXT("formatter")).ToLower();
	}

	FString LoadError;
	UBlueprint* BP = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!BP) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(BP);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	// Try IMonolithGraphFormatter if not explicitly requesting builtin
	if (FormatterMode != TEXT("builtin"))
	{
		if (IMonolithGraphFormatter::IsAvailable())
		{
			IMonolithGraphFormatter& Formatter = IMonolithGraphFormatter::Get();
			if (Formatter.SupportsGraph(RootGraph))
			{
				int32 NodesFormatted = 0;
				FString FormatError;
				bool bOk = Formatter.FormatGraph(RootGraph, NodesFormatted, FormatError);
				if (bOk)
				{
					MarkModified(BP);

					TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
					Result->SetStringField(TEXT("action"), TEXT("auto_arrange_graph"));
					Result->SetStringField(TEXT("asset_path"), AssetPath);
					Result->SetStringField(TEXT("formatter_used"), TEXT("external"));
					Result->SetNumberField(TEXT("nodes_formatted"), NodesFormatted);
					Result->SetBoolField(TEXT("success"), true);
					return FMonolithActionResult::Success(Result);
				}
				// If formatter failed and we're in "default" mode, fall through to builtin
				if (FormatterMode == TEXT("blueprint_assist"))
				{
					return FMonolithActionResult::Error(FString::Printf(TEXT("Formatter failed: %s"), *FormatError));
				}
			}
			else if (FormatterMode == TEXT("blueprint_assist"))
			{
				return FMonolithActionResult::Error(TEXT("External formatter does not support this graph type"));
			}
		}
		else if (FormatterMode == TEXT("blueprint_assist"))
		{
			return FMonolithActionResult::Error(TEXT("No external graph formatter is available (Blueprint Assist not loaded?)"));
		}
	}

	// ── Built-in BFS layout ──
	constexpr int32 HSpacing = 300;
	constexpr int32 VSpacing = 200;

	// Find entry/initial node
	UEdGraphNode* EntryNode = nullptr;
	UEdGraphNode* InitialState = nullptr;

	for (UEdGraphNode* Node : RootGraph->Nodes)
	{
		if (!Node) continue;
		if (MonolithLD::GetNodeType(Node) == TEXT("entry"))
		{
			EntryNode = Node;
			// Find what entry connects to
			for (UEdGraphPin* Pin : Node->Pins)
			{
				if (Pin && Pin->Direction == EGPD_Output && Pin->LinkedTo.Num() > 0 && Pin->LinkedTo[0])
				{
					InitialState = Pin->LinkedTo[0]->GetOwningNode();
				}
			}
			break;
		}
	}

	if (!InitialState)
	{
		// No initial state — just pick first state node
		for (UEdGraphNode* Node : RootGraph->Nodes)
		{
			if (!Node) continue;
			FString NT = MonolithLD::GetNodeType(Node);
			if (NT == TEXT("state") || NT == TEXT("state_machine") || NT == TEXT("conduit"))
			{
				InitialState = Node;
				break;
			}
		}
	}

	if (!InitialState)
	{
		return FMonolithActionResult::Error(TEXT("No state nodes found in graph"));
	}

	// Build adjacency from states (skip transitions — they'll follow their connected nodes)
	// Map guid -> outgoing state guids (through transitions)
	TMap<FString, TArray<FString>> Adjacency;
	TMap<FString, UEdGraphNode*> GuidToNode;

	for (UEdGraphNode* Node : RootGraph->Nodes)
	{
		if (!Node) continue;
		FString NT = MonolithLD::GetNodeType(Node);
		if (NT == TEXT("state") || NT == TEXT("state_machine") || NT == TEXT("conduit") || NT == TEXT("any_state"))
		{
			GuidToNode.Add(Node->NodeGuid.ToString(), Node);
			Adjacency.FindOrAdd(Node->NodeGuid.ToString());
		}
	}

	// Walk transitions to build adjacency
	for (UEdGraphNode* Node : RootGraph->Nodes)
	{
		if (!Node) continue;
		if (MonolithLD::GetNodeType(Node) != TEXT("transition")) continue;

		FString SourceGuid, TargetGuid;
		for (UEdGraphPin* Pin : Node->Pins)
		{
			if (!Pin) continue;
			if (Pin->Direction == EGPD_Input && Pin->LinkedTo.Num() > 0 && Pin->LinkedTo[0])
			{
				SourceGuid = Pin->LinkedTo[0]->GetOwningNode()->NodeGuid.ToString();
			}
			if (Pin->Direction == EGPD_Output && Pin->LinkedTo.Num() > 0 && Pin->LinkedTo[0])
			{
				TargetGuid = Pin->LinkedTo[0]->GetOwningNode()->NodeGuid.ToString();
			}
		}

		if (!SourceGuid.IsEmpty() && !TargetGuid.IsEmpty())
		{
			Adjacency.FindOrAdd(SourceGuid).AddUnique(TargetGuid);
		}
	}

	// BFS from initial state
	TArray<TArray<FString>> Levels; // each level = array of guids at that column
	TSet<FString> Visited;
	TArray<FString> CurrentLevel;
	CurrentLevel.Add(InitialState->NodeGuid.ToString());
	Visited.Add(InitialState->NodeGuid.ToString());

	while (CurrentLevel.Num() > 0)
	{
		Levels.Add(CurrentLevel);
		TArray<FString> NextLevel;

		for (const FString& Guid : CurrentLevel)
		{
			TArray<FString>* Neighbors = Adjacency.Find(Guid);
			if (!Neighbors) continue;
			for (const FString& NeighGuid : *Neighbors)
			{
				if (!Visited.Contains(NeighGuid))
				{
					Visited.Add(NeighGuid);
					NextLevel.Add(NeighGuid);
				}
			}
		}

		CurrentLevel = NextLevel;
	}

	// Place any unvisited states at the end
	TArray<FString> Unvisited;
	for (const auto& Pair : GuidToNode)
	{
		if (!Visited.Contains(Pair.Key))
		{
			Unvisited.Add(Pair.Key);
		}
	}
	if (Unvisited.Num() > 0)
	{
		Levels.Add(Unvisited);
	}

	// Position entry node
	if (EntryNode)
	{
		EntryNode->NodePosX = 0;
		EntryNode->NodePosY = 0;
	}

	// Position state nodes level by level
	int32 NodesPositioned = 0;
	for (int32 Col = 0; Col < Levels.Num(); ++Col)
	{
		const TArray<FString>& Level = Levels[Col];
		int32 StartY = -((Level.Num() - 1) * VSpacing) / 2;

		for (int32 Row = 0; Row < Level.Num(); ++Row)
		{
			UEdGraphNode** NodePtr = GuidToNode.Find(Level[Row]);
			if (NodePtr && *NodePtr)
			{
				(*NodePtr)->NodePosX = (Col + 1) * HSpacing; // +1 to leave room for entry
				(*NodePtr)->NodePosY = StartY + Row * VSpacing;
				NodesPositioned++;
			}
		}
	}

	MarkModified(BP);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("action"), TEXT("auto_arrange_graph"));
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetStringField(TEXT("formatter_used"), TEXT("builtin_bfs"));
	Result->SetNumberField(TEXT("nodes_formatted"), NodesPositioned);
	Result->SetNumberField(TEXT("levels"), Levels.Num());
	Result->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverGraphActions::HandleCompileStateMachine(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
	}

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint)
	{
		return FMonolithActionResult::Error(LoadError);
	}

	FString CompileError;
	bool bSuccess = MonolithLD::CompileSMBlueprint(SMBlueprint, CompileError);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetBoolField(TEXT("compiled"), bSuccess);
	Result->SetStringField(TEXT("status"), bSuccess ? TEXT("success") : TEXT("error"));
	if (!bSuccess)
	{
		Result->SetStringField(TEXT("error"), CompileError);
	}

	return FMonolithActionResult::Success(Result);
}

#else

void FMonolithLogicDriverGraphActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// Logic Driver not available
}

#endif // WITH_LOGICDRIVER
