#include "MonolithLogicDriverTextGraphActions.h"
#include "MonolithParamSchema.h"

#if WITH_LOGICDRIVER

#include "MonolithLogicDriverInternal.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

DEFINE_LOG_CATEGORY_STATIC(LogMonolithLDTextGraph, Log, All);

namespace
{
	/** Extract text/dialogue content from a node by scanning for text-like properties via reflection */
	TSharedPtr<FJsonObject> ExtractTextContent(UEdGraphNode* Node)
	{
		TSharedPtr<FJsonObject> TextInfo = MakeShared<FJsonObject>();
		if (!Node) return TextInfo;

		UClass* NodeClass = Node->GetClass();

		// Scan for text/string properties that look like dialogue or text graph content
		static const FName TextPropNames[] = {
			TEXT("TextGraph"),
			TEXT("TextGraphProperty"),
			TEXT("TextContent"),
			TEXT("DialogueText"),
			TEXT("Text"),
			TEXT("Body"),
			TEXT("Description"),
			TEXT("NodeText"),
			TEXT("SpeakerName"),
			TEXT("Speaker"),
		};

		for (TFieldIterator<FProperty> PropIt(NodeClass, EFieldIteratorFlags::IncludeSuper); PropIt; ++PropIt)
		{
			FProperty* Prop = *PropIt;
			if (!Prop) continue;

			// Skip base UEdGraphNode properties
			if (Prop->GetOwnerClass() == UEdGraphNode::StaticClass()) continue;

			FString PropName = Prop->GetName();
			bool bIsTextProp = false;

			// Check if this property name matches known text property patterns
			for (const FName& KnownName : TextPropNames)
			{
				if (PropName.Contains(KnownName.ToString()))
				{
					bIsTextProp = true;
					break;
				}
			}

			// Also check for FText/FString types with text-like content
			if (!bIsTextProp)
			{
				FString TypeStr = Prop->GetCPPType();
				if (TypeStr.Contains(TEXT("FText")) || TypeStr.Contains(TEXT("FSMTextGraphProperty")))
				{
					bIsTextProp = true;
				}
			}

			if (!bIsTextProp) continue;

			// Export value
			FString ValueText;
			const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Node);
			Prop->ExportTextItem_Direct(ValueText, ValuePtr, nullptr, nullptr, PPF_None);

			if (!ValueText.IsEmpty())
			{
				TextInfo->SetStringField(PropName, ValueText);
			}
		}

		return TextInfo;
	}
}

void FMonolithLogicDriverTextGraphActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("get_text_graph_content"),
		TEXT("Read FSMTextGraphProperty content (dialogue text, speaker names) from state nodes"),
		FMonolithActionHandler::CreateStatic(&HandleGetTextGraphContent),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Optional(TEXT("node_guid"), TEXT("string"), TEXT("Specific node GUID; if omitted reads all nodes"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("get_dialogue_flow"),
		TEXT("Walk entire SM and extract dialogue flow: speakers, lines, choices, branching paths"),
		FMonolithActionHandler::CreateStatic(&HandleGetDialogueFlow),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Build());

	UE_LOG(LogMonolithLDTextGraph, Log, TEXT("MonolithLogicDriver TextGraph: registered 2 actions"));
}

FMonolithActionResult FMonolithLogicDriverTextGraphActions::HandleGetTextGraphContent(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(SMBlueprint);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	FString TargetGuid;
	if (Params->HasField(TEXT("node_guid")))
	{
		TargetGuid = Params->GetStringField(TEXT("node_guid"));
	}

	TArray<TSharedPtr<FJsonValue>> NodesArr;

	auto ProcessNode = [&](UEdGraphNode* Node)
	{
		TSharedPtr<FJsonObject> TextContent = ExtractTextContent(Node);
		if (TextContent->Values.Num() == 0) return;

		TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
		Entry->SetStringField(TEXT("node_type"), MonolithLD::GetNodeType(Node));
		Entry->SetStringField(TEXT("node_name"), Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
		Entry->SetObjectField(TEXT("text_content"), TextContent);
		NodesArr.Add(MakeShared<FJsonValueObject>(Entry));
	};

	if (!TargetGuid.IsEmpty())
	{
		UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, TargetGuid);
		if (!Node) return FMonolithActionResult::Error(FString::Printf(TEXT("Node '%s' not found"), *TargetGuid));
		ProcessNode(Node);
	}
	else
	{
		for (UEdGraphNode* Node : RootGraph->Nodes)
		{
			if (Node) ProcessNode(Node);
		}
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetNumberField(TEXT("nodes_with_text"), NodesArr.Num());
	Result->SetArrayField(TEXT("nodes"), NodesArr);

	if (NodesArr.Num() == 0)
	{
		Result->SetStringField(TEXT("note"), TEXT("No text graph content found — this SM may not use FSMTextGraphProperty"));
	}

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverTextGraphActions::HandleGetDialogueFlow(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));

	FString LoadError;
	UBlueprint* SMBlueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!SMBlueprint) return FMonolithActionResult::Error(LoadError);

	UEdGraph* RootGraph = MonolithLD::GetRootGraph(SMBlueprint);
	if (!RootGraph) return FMonolithActionResult::Error(TEXT("No root SM graph found"));

	// Build flow graph: node info + adjacency
	struct FDialogueNode
	{
		FString Guid;
		FString Name;
		FString NodeType;
		TSharedPtr<FJsonObject> TextContent;
		TArray<FString> NextGuids; // Connected target node GUIDs (via transitions)
		bool bIsInitial = false;
	};

	TMap<FString, FDialogueNode> Nodes;

	// First pass: collect all state-like nodes
	for (UEdGraphNode* RawNode : RootGraph->Nodes)
	{
		if (!RawNode) continue;
		FString NodeType = MonolithLD::GetNodeType(RawNode);
		if (NodeType == TEXT("entry") || NodeType == TEXT("transition")) continue;

		FDialogueNode DN;
		DN.Guid = RawNode->NodeGuid.ToString();
		DN.Name = RawNode->GetNodeTitle(ENodeTitleType::FullTitle).ToString();
		DN.NodeType = NodeType;
		DN.TextContent = ExtractTextContent(RawNode);

		// Check if initial
		for (UEdGraphPin* Pin : RawNode->Pins)
		{
			if (Pin && Pin->Direction == EGPD_Input)
			{
				for (UEdGraphPin* LP : Pin->LinkedTo)
				{
					if (LP && LP->GetOwningNode() && MonolithLD::GetNodeType(LP->GetOwningNode()) == TEXT("entry"))
					{
						DN.bIsInitial = true;
					}
				}
			}
		}

		Nodes.Add(DN.Guid, DN);
	}

	// Second pass: build adjacency from transitions
	for (UEdGraphNode* RawNode : RootGraph->Nodes)
	{
		if (!RawNode || MonolithLD::GetNodeType(RawNode) != TEXT("transition")) continue;

		FString SourceGuid, TargetGuid;
		for (UEdGraphPin* Pin : RawNode->Pins)
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
			if (FDialogueNode* SrcNode = Nodes.Find(SourceGuid))
			{
				SrcNode->NextGuids.Add(TargetGuid);
			}
		}
	}

	// Build flow JSON — ordered by traversal from initial node
	TArray<TSharedPtr<FJsonValue>> FlowArr;
	TSet<FString> Visited;

	// BFS from initial nodes
	TArray<FString> Queue;
	for (const auto& Pair : Nodes)
	{
		if (Pair.Value.bIsInitial) Queue.Add(Pair.Key);
	}

	while (Queue.Num() > 0)
	{
		FString CurrentGuid = Queue[0];
		Queue.RemoveAt(0);

		if (Visited.Contains(CurrentGuid)) continue;
		Visited.Add(CurrentGuid);

		const FDialogueNode* DN = Nodes.Find(CurrentGuid);
		if (!DN) continue;

		TSharedPtr<FJsonObject> FlowNode = MakeShared<FJsonObject>();
		FlowNode->SetStringField(TEXT("node_guid"), DN->Guid);
		FlowNode->SetStringField(TEXT("name"), DN->Name);
		FlowNode->SetStringField(TEXT("type"), DN->NodeType);
		FlowNode->SetBoolField(TEXT("is_initial"), DN->bIsInitial);

		if (DN->TextContent.IsValid() && DN->TextContent->Values.Num() > 0)
		{
			FlowNode->SetObjectField(TEXT("text"), DN->TextContent);
		}

		// Choices / next states
		TArray<TSharedPtr<FJsonValue>> NextArr;
		for (const FString& NextGuid : DN->NextGuids)
		{
			const FDialogueNode* NextDN = Nodes.Find(NextGuid);
			if (NextDN)
			{
				TSharedPtr<FJsonObject> NextObj = MakeShared<FJsonObject>();
				NextObj->SetStringField(TEXT("node_guid"), NextGuid);
				NextObj->SetStringField(TEXT("name"), NextDN->Name);
				NextArr.Add(MakeShared<FJsonValueObject>(NextObj));
			}
			if (!Visited.Contains(NextGuid))
			{
				Queue.Add(NextGuid);
			}
		}
		FlowNode->SetNumberField(TEXT("choice_count"), NextArr.Num());
		FlowNode->SetArrayField(TEXT("next"), NextArr);

		FlowArr.Add(MakeShared<FJsonValueObject>(FlowNode));
	}

	// Add any unvisited nodes (disconnected)
	for (const auto& Pair : Nodes)
	{
		if (!Visited.Contains(Pair.Key))
		{
			TSharedPtr<FJsonObject> FlowNode = MakeShared<FJsonObject>();
			FlowNode->SetStringField(TEXT("node_guid"), Pair.Value.Guid);
			FlowNode->SetStringField(TEXT("name"), Pair.Value.Name);
			FlowNode->SetStringField(TEXT("type"), Pair.Value.NodeType);
			FlowNode->SetBoolField(TEXT("orphaned"), true);
			FlowArr.Add(MakeShared<FJsonValueObject>(FlowNode));
		}
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetNumberField(TEXT("total_nodes"), Nodes.Num());
	Result->SetArrayField(TEXT("flow"), FlowArr);

	return FMonolithActionResult::Success(Result);
}

#else

void FMonolithLogicDriverTextGraphActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// Logic Driver not available
}

#endif // WITH_LOGICDRIVER
