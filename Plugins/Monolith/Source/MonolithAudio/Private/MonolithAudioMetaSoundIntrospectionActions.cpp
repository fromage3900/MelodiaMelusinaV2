#include "MonolithAudioMetaSoundIntrospectionActions.h"

#if WITH_METASOUND

#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"
#include "MonolithAssetUtils.h"

// MetaSound Engine
#include "MetasoundSource.h"
#include "Metasound.h"

// MetaSound Frontend
#include "MetasoundDocumentInterface.h"
#include "MetasoundFrontendDocument.h"

// Engine
#include "AssetRegistry/IAssetRegistry.h"
#include "AssetRegistry/AssetRegistryModule.h"

// JSON
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ============================================================================
// Internal helpers — file-local linkage via anonymous namespace.
// Prefix `Introspection_` to disambiguate from same-named members on
// FMonolithAudioSoundCueActions (different translation unit, different class,
// no ODR collision possible — but the prefix removes any future risk under
// Unity builds and aids navigation in IDEs.)
// ============================================================================

namespace
{
	IMetaSoundDocumentInterface* Introspection_GetDocumentInterface(UObject* Asset)
	{
		if (!Asset)
		{
			return nullptr;
		}
		return Cast<IMetaSoundDocumentInterface>(Asset);
	}

	const FMetasoundFrontendGraph* Introspection_GetGraphFromDoc(
		const FMetasoundFrontendDocument& Doc,
		const FString& PageIdStr)
	{
		if (PageIdStr.IsEmpty())
		{
			return &Doc.RootGraph.GetConstDefaultGraph();
		}

		FGuid PageId;
		if (!FGuid::Parse(PageIdStr, PageId))
		{
			return nullptr;
		}

		const FMetasoundFrontendGraph* FoundGraph = nullptr;
		Doc.RootGraph.IterateGraphPages([&](const FMetasoundFrontendGraph& Page)
		{
			if (Page.PageID == PageId)
			{
				FoundGraph = &Page;
			}
		});

		return FoundGraph;
	}

	/** Resolve a class GUID against the document's Dependencies + Subgraphs. */
	FString Introspection_ResolveClassName(const FGuid& ClassID, const FMetasoundFrontendDocument& Doc)
	{
		for (const FMetasoundFrontendClass& Dep : Doc.Dependencies)
		{
			if (Dep.ID == ClassID)
			{
				return Dep.Metadata.GetClassName().ToString();
			}
		}
		for (const FMetasoundFrontendGraphClass& Sub : Doc.Subgraphs)
		{
			if (Sub.ID == ClassID)
			{
				return Sub.Metadata.GetClassName().ToString();
			}
		}
		// Root graph itself has a class GUID
		if (Doc.RootGraph.ID == ClassID)
		{
			return Doc.RootGraph.Metadata.GetClassName().ToString();
		}
		return TEXT("Unknown");
	}

	const FMetasoundFrontendNode* Introspection_FindNodeById(const FMetasoundFrontendGraph& Graph, const FGuid& NodeId)
	{
		for (const FMetasoundFrontendNode& Node : Graph.Nodes)
		{
			if (Node.GetID() == NodeId)
			{
				return &Node;
			}
		}
		return nullptr;
	}

	/** Collect edges touching a given node, optionally filtered by direction. */
	TArray<const FMetasoundFrontendEdge*> Introspection_GetNodeEdges(
		const FMetasoundFrontendGraph& Graph,
		const FGuid& NodeId,
		bool bIncoming,
		bool bOutgoing)
	{
		TArray<const FMetasoundFrontendEdge*> Out;
		for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
		{
			if (bIncoming && Edge.ToNodeID == NodeId)
			{
				Out.Add(&Edge);
			}
			else if (bOutgoing && Edge.FromNodeID == NodeId)
			{
				Out.Add(&Edge);
			}
		}
		return Out;
	}

	TSharedPtr<FJsonObject> Introspection_SerializeLiteral(const FMetasoundFrontendLiteral& Literal)
	{
		TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
		Out->SetStringField(TEXT("type"), UEnum::GetValueAsString(Literal.GetType()));
		// Best-effort literal-value extraction. The exact getter shape varies by type;
		// we surface the type tag plus a string-coerced value when possible.
		FString AsString;
		if (Literal.TryGet(AsString))
		{
			Out->SetStringField(TEXT("value"), AsString);
		}
		else
		{
			float AsFloat = 0.f;
			int32 AsInt = 0;
			bool AsBool = false;
			if (Literal.TryGet(AsFloat))
			{
				Out->SetNumberField(TEXT("value"), AsFloat);
			}
			else if (Literal.TryGet(AsInt))
			{
				Out->SetNumberField(TEXT("value"), AsInt);
			}
			else if (Literal.TryGet(AsBool))
			{
				Out->SetBoolField(TEXT("value"), AsBool);
			}
		}
		return Out;
	}

	TSharedPtr<FJsonObject> Introspection_SerializeVariable(const FMetasoundFrontendVariable& Variable)
	{
		TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
		Out->SetStringField(TEXT("name"), Variable.Name.ToString());
		Out->SetStringField(TEXT("type_name"), Variable.TypeName.ToString());
		Out->SetStringField(TEXT("variable_id"), Variable.ID.ToString());
		Out->SetObjectField(TEXT("literal"), Introspection_SerializeLiteral(Variable.Literal));
		return Out;
	}

	/** Find an input vertex by VertexID on a node's interface. */
	const FMetasoundFrontendVertex* Introspection_FindInputVertex(const FMetasoundFrontendNode& Node, const FGuid& VertexId)
	{
		for (const FMetasoundFrontendVertex& V : Node.Interface.Inputs)
		{
			if (V.VertexID == VertexId)
			{
				return &V;
			}
		}
		return nullptr;
	}

	const FMetasoundFrontendVertex* Introspection_FindOutputVertex(const FMetasoundFrontendNode& Node, const FGuid& VertexId)
	{
		for (const FMetasoundFrontendVertex& V : Node.Interface.Outputs)
		{
			if (V.VertexID == VertexId)
			{
				return &V;
			}
		}
		return nullptr;
	}

	TSharedPtr<FJsonObject> Introspection_SerializeVertex(const FMetasoundFrontendVertex& Vertex)
	{
		TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
		Out->SetStringField(TEXT("name"), Vertex.Name.ToString());
		Out->SetStringField(TEXT("type_name"), Vertex.TypeName.ToString());
		Out->SetStringField(TEXT("vertex_id"), Vertex.VertexID.ToString());
		return Out;
	}

	/** Serialize an edge with vertex-name resolution by walking the graph's nodes. */
	TSharedPtr<FJsonObject> Introspection_SerializeEdge(const FMetasoundFrontendEdge& Edge, const FMetasoundFrontendGraph& Graph)
	{
		TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
		Out->SetStringField(TEXT("from_node_id"), Edge.FromNodeID.ToString());
		Out->SetStringField(TEXT("from_vertex_id"), Edge.FromVertexID.ToString());
		Out->SetStringField(TEXT("to_node_id"), Edge.ToNodeID.ToString());
		Out->SetStringField(TEXT("to_vertex_id"), Edge.ToVertexID.ToString());

		// Best-effort vertex-name resolution.
		if (const FMetasoundFrontendNode* FromNode = Introspection_FindNodeById(Graph, Edge.FromNodeID))
		{
			if (const FMetasoundFrontendVertex* FromVertex = Introspection_FindOutputVertex(*FromNode, Edge.FromVertexID))
			{
				Out->SetStringField(TEXT("from_vertex_name"), FromVertex->Name.ToString());
				Out->SetStringField(TEXT("from_vertex_type"), FromVertex->TypeName.ToString());
			}
			Out->SetStringField(TEXT("from_node_name"), FromNode->Name.ToString());
		}
		if (const FMetasoundFrontendNode* ToNode = Introspection_FindNodeById(Graph, Edge.ToNodeID))
		{
			if (const FMetasoundFrontendVertex* ToVertex = Introspection_FindInputVertex(*ToNode, Edge.ToVertexID))
			{
				Out->SetStringField(TEXT("to_vertex_name"), ToVertex->Name.ToString());
				Out->SetStringField(TEXT("to_vertex_type"), ToVertex->TypeName.ToString());
			}
			Out->SetStringField(TEXT("to_node_name"), ToNode->Name.ToString());
		}
		return Out;
	}

	TSharedPtr<FJsonObject> Introspection_SerializeNodeSummary(const FMetasoundFrontendNode& Node, const FMetasoundFrontendDocument& Doc)
	{
		TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
		Out->SetStringField(TEXT("node_id"), Node.GetID().ToString());
		Out->SetStringField(TEXT("name"), Node.Name.ToString());
		Out->SetStringField(TEXT("class_id"), Node.ClassID.ToString());
		Out->SetStringField(TEXT("class_name"), Introspection_ResolveClassName(Node.ClassID, Doc));
		Out->SetNumberField(TEXT("input_count"), Node.Interface.Inputs.Num());
		Out->SetNumberField(TEXT("output_count"), Node.Interface.Outputs.Num());
		return Out;
	}

	TSharedPtr<FJsonObject> Introspection_SerializeNode(const FMetasoundFrontendNode& Node, const FMetasoundFrontendDocument& Doc)
	{
		TSharedPtr<FJsonObject> Out = Introspection_SerializeNodeSummary(Node, Doc);

		TArray<TSharedPtr<FJsonValue>> InputsArray;
		for (const FMetasoundFrontendVertex& V : Node.Interface.Inputs)
		{
			InputsArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeVertex(V)));
		}
		Out->SetArrayField(TEXT("inputs"), InputsArray);

		TArray<TSharedPtr<FJsonValue>> OutputsArray;
		for (const FMetasoundFrontendVertex& V : Node.Interface.Outputs)
		{
			OutputsArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeVertex(V)));
		}
		Out->SetArrayField(TEXT("outputs"), OutputsArray);

		// Per-node input-literal defaults (if any).
		TArray<TSharedPtr<FJsonValue>> LiteralsArray;
		for (const FMetasoundFrontendVertexLiteral& VL : Node.InputLiterals)
		{
			TSharedPtr<FJsonObject> LitJson = MakeShared<FJsonObject>();
			LitJson->SetStringField(TEXT("vertex_id"), VL.VertexID.ToString());
			LitJson->SetObjectField(TEXT("literal"), Introspection_SerializeLiteral(VL.Value));
			LiteralsArray.Add(MakeShared<FJsonValueObject>(LitJson));
		}
		Out->SetArrayField(TEXT("input_literals"), LiteralsArray);

		return Out;
	}
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithAudioMetaSoundIntrospectionActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("audio"), TEXT("list_metasounds"),
		TEXT("List all MetaSound assets in the project (Sources + Patches)"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleListMetaSounds),
		FParamSchemaBuilder()
			.Optional(TEXT("filter"), TEXT("string"), TEXT("Filter by name substring"))
			.Optional(TEXT("type"), TEXT("string"), TEXT("Filter by type: Source, Patch, or All"), TEXT("All"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("list_metasound_documents"),
		TEXT("List all graph pages in a MetaSound asset's on-disk document"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleListMetaSoundDocuments),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("get_metasound_document"),
		TEXT("Get the full graph data (nodes, edges, variables) for one MetaSound document page"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundDocument),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Optional(TEXT("page_id"), TEXT("string"), TEXT("Page GUID (default: default page)"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("get_metasound_summary"),
		TEXT("Get lightweight node summaries (no pin details) for a MetaSound document page"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundSummary),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Optional(TEXT("page_id"), TEXT("string"), TEXT("Page GUID (default: default page)"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("inspect_metasound_node_instance"),
		TEXT("Get full per-instance pin dump and incoming/outgoing edges for one node by ID or name"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleInspectMetaSoundNodeInstance),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Optional(TEXT("node_id"), TEXT("string"), TEXT("Node GUID"))
			.Optional(TEXT("node_name"), TEXT("string"), TEXT("Node name"))
			.Optional(TEXT("page_id"), TEXT("string"), TEXT("Page GUID (default: default page)"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("get_metasound_document_connections"),
		TEXT("Get all on-disk edges for a node or for the full document graph"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundDocumentConnections),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Optional(TEXT("node_id"), TEXT("string"), TEXT("Filter by node GUID"))
			.Optional(TEXT("page_id"), TEXT("string"), TEXT("Page GUID (default: default page)"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("get_metasound_document_variables"),
		TEXT("Get graph-local variables on a MetaSound document page"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundDocumentVariables),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Optional(TEXT("page_id"), TEXT("string"), TEXT("Page GUID (default: default page)"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("get_metasound_user_parameters"),
		TEXT("Get document-level input/output parameters (user-exposed) with defaults and metadata"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundUserParameters),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("search_metasound_document_nodes"),
		TEXT("Find nodes by class name or node name substring in a MetaSound document page"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleSearchMetaSoundDocumentNodes),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Required(TEXT("query"), TEXT("string"), TEXT("Search string (matches class or node name, case-insensitive)"))
			.Optional(TEXT("page_id"), TEXT("string"), TEXT("Page GUID (default: default page)"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("get_metasound_info"),
		TEXT("Get MetaSound asset overview (type, class, version, default-graph counts)"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundInfo),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("get_metasound_dependencies"),
		TEXT("Get referenced node-class dependencies and subgraphs for a MetaSound document"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundDependencies),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("validate_metasound"),
		TEXT("Validate a MetaSound document for errors (duplicate node IDs, dangling edges) and warnings (unconnected inputs)"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioMetaSoundIntrospectionActions::HandleValidateMetaSound),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MetaSound asset path"))
			.Build());
}

// ============================================================================
// Handlers — ported from PR #18 by @alakangas, namespace changed metasound -> audio
// ============================================================================

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleListMetaSoundDocuments(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);

	TArray<TSharedPtr<FJsonValue>> PagesArray;
	Doc.RootGraph.IterateGraphPages([&](const FMetasoundFrontendGraph& Page)
	{
		TSharedPtr<FJsonObject> PageJson = MakeShared<FJsonObject>();
		PageJson->SetStringField(TEXT("page_id"), Page.PageID.ToString());
		PageJson->SetNumberField(TEXT("node_count"), Page.Nodes.Num());
		PageJson->SetNumberField(TEXT("edge_count"), Page.Edges.Num());
		PageJson->SetNumberField(TEXT("variable_count"), Page.Variables.Num());
		PagesArray.Add(MakeShared<FJsonValueObject>(PageJson));
	});

	Result->SetArrayField(TEXT("pages"), PagesArray);
	Result->SetNumberField(TEXT("page_count"), PagesArray.Num());
	Result->SetNumberField(TEXT("subgraph_count"), Doc.Subgraphs.Num());
	Result->SetNumberField(TEXT("dependency_count"), Doc.Dependencies.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundDocument(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString PageIdStr = Params->HasField(TEXT("page_id")) ? Params->GetStringField(TEXT("page_id")) : FString();

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();
	const FMetasoundFrontendGraph* Graph = Introspection_GetGraphFromDoc(Doc, PageIdStr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph page not found: %s"), *PageIdStr), FMonolithJsonUtils::ErrInvalidParams);
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetStringField(TEXT("page_id"), Graph->PageID.ToString());

	TArray<TSharedPtr<FJsonValue>> NodesArray;
	for (const FMetasoundFrontendNode& Node : Graph->Nodes)
	{
		NodesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeNode(Node, Doc)));
	}
	Result->SetArrayField(TEXT("nodes"), NodesArray);

	TArray<TSharedPtr<FJsonValue>> EdgesArray;
	for (const FMetasoundFrontendEdge& Edge : Graph->Edges)
	{
		EdgesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeEdge(Edge, *Graph)));
	}
	Result->SetArrayField(TEXT("edges"), EdgesArray);

	TArray<TSharedPtr<FJsonValue>> VariablesArray;
	for (const FMetasoundFrontendVariable& Variable : Graph->Variables)
	{
		VariablesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeVariable(Variable)));
	}
	Result->SetArrayField(TEXT("variables"), VariablesArray);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundSummary(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString PageIdStr = Params->HasField(TEXT("page_id")) ? Params->GetStringField(TEXT("page_id")) : FString();

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();
	const FMetasoundFrontendGraph* Graph = Introspection_GetGraphFromDoc(Doc, PageIdStr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph page not found: %s"), *PageIdStr), FMonolithJsonUtils::ErrInvalidParams);
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetStringField(TEXT("page_id"), Graph->PageID.ToString());

	TArray<TSharedPtr<FJsonValue>> NodesArray;
	for (const FMetasoundFrontendNode& Node : Graph->Nodes)
	{
		NodesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeNodeSummary(Node, Doc)));
	}
	Result->SetArrayField(TEXT("nodes"), NodesArray);
	Result->SetNumberField(TEXT("node_count"), Graph->Nodes.Num());
	Result->SetNumberField(TEXT("edge_count"), Graph->Edges.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleInspectMetaSoundNodeInstance(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString PageIdStr = Params->HasField(TEXT("page_id")) ? Params->GetStringField(TEXT("page_id")) : FString();
	FString NodeIdStr = Params->HasField(TEXT("node_id")) ? Params->GetStringField(TEXT("node_id")) : FString();
	FString NodeName = Params->HasField(TEXT("node_name")) ? Params->GetStringField(TEXT("node_name")) : FString();

	if (NodeIdStr.IsEmpty() && NodeName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Must provide either node_id or node_name"), FMonolithJsonUtils::ErrInvalidParams);
	}

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();
	const FMetasoundFrontendGraph* Graph = Introspection_GetGraphFromDoc(Doc, PageIdStr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph page not found: %s"), *PageIdStr), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendNode* FoundNode = nullptr;
	if (!NodeIdStr.IsEmpty())
	{
		FGuid NodeId;
		if (FGuid::Parse(NodeIdStr, NodeId))
		{
			FoundNode = Introspection_FindNodeById(*Graph, NodeId);
		}
	}
	else if (!NodeName.IsEmpty())
	{
		FName SearchName(*NodeName);
		for (const FMetasoundFrontendNode& Node : Graph->Nodes)
		{
			if (Node.Name == SearchName)
			{
				FoundNode = &Node;
				break;
			}
		}
	}

	if (!FoundNode)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Node not found: %s"),
			!NodeIdStr.IsEmpty() ? *NodeIdStr : *NodeName), FMonolithJsonUtils::ErrInvalidParams);
	}

	TSharedPtr<FJsonObject> Result = Introspection_SerializeNode(*FoundNode, Doc);

	TArray<const FMetasoundFrontendEdge*> InputEdges = Introspection_GetNodeEdges(*Graph, FoundNode->GetID(), true, false);
	TArray<const FMetasoundFrontendEdge*> OutputEdges = Introspection_GetNodeEdges(*Graph, FoundNode->GetID(), false, true);

	TArray<TSharedPtr<FJsonValue>> InputEdgesArray;
	for (const FMetasoundFrontendEdge* Edge : InputEdges)
	{
		InputEdgesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeEdge(*Edge, *Graph)));
	}
	Result->SetArrayField(TEXT("incoming_edges"), InputEdgesArray);

	TArray<TSharedPtr<FJsonValue>> OutputEdgesArray;
	for (const FMetasoundFrontendEdge* Edge : OutputEdges)
	{
		OutputEdgesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeEdge(*Edge, *Graph)));
	}
	Result->SetArrayField(TEXT("outgoing_edges"), OutputEdgesArray);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundDocumentConnections(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString PageIdStr = Params->HasField(TEXT("page_id")) ? Params->GetStringField(TEXT("page_id")) : FString();
	FString NodeIdStr = Params->HasField(TEXT("node_id")) ? Params->GetStringField(TEXT("node_id")) : FString();

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();
	const FMetasoundFrontendGraph* Graph = Introspection_GetGraphFromDoc(Doc, PageIdStr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph page not found: %s"), *PageIdStr), FMonolithJsonUtils::ErrInvalidParams);
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);

	TArray<TSharedPtr<FJsonValue>> EdgesArray;

	if (!NodeIdStr.IsEmpty())
	{
		FGuid NodeId;
		if (!FGuid::Parse(NodeIdStr, NodeId))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Invalid node_id GUID: %s"), *NodeIdStr), FMonolithJsonUtils::ErrInvalidParams);
		}

		TArray<const FMetasoundFrontendEdge*> Edges = Introspection_GetNodeEdges(*Graph, NodeId, true, true);
		for (const FMetasoundFrontendEdge* Edge : Edges)
		{
			EdgesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeEdge(*Edge, *Graph)));
		}
		Result->SetStringField(TEXT("node_id"), NodeIdStr);
	}
	else
	{
		for (const FMetasoundFrontendEdge& Edge : Graph->Edges)
		{
			EdgesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeEdge(Edge, *Graph)));
		}
	}

	Result->SetArrayField(TEXT("edges"), EdgesArray);
	Result->SetNumberField(TEXT("edge_count"), EdgesArray.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundDocumentVariables(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString PageIdStr = Params->HasField(TEXT("page_id")) ? Params->GetStringField(TEXT("page_id")) : FString();

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();
	const FMetasoundFrontendGraph* Graph = Introspection_GetGraphFromDoc(Doc, PageIdStr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph page not found: %s"), *PageIdStr), FMonolithJsonUtils::ErrInvalidParams);
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);

	TArray<TSharedPtr<FJsonValue>> VariablesArray;
	for (const FMetasoundFrontendVariable& Variable : Graph->Variables)
	{
		VariablesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeVariable(Variable)));
	}

	Result->SetArrayField(TEXT("variables"), VariablesArray);
	Result->SetNumberField(TEXT("variable_count"), VariablesArray.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundUserParameters(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);

	const FMetasoundFrontendClassInterface& ClassInterface = Doc.RootGraph.GetDefaultInterface();

	TArray<TSharedPtr<FJsonValue>> InputsArray;
	for (const FMetasoundFrontendClassInput& Input : ClassInterface.Inputs)
	{
		TSharedPtr<FJsonObject> InputJson = MakeShared<FJsonObject>();
		InputJson->SetStringField(TEXT("name"), Input.Name.ToString());
		InputJson->SetStringField(TEXT("type"), Input.TypeName.ToString());
		InputJson->SetStringField(TEXT("vertex_id"), Input.VertexID.ToString());
		InputJson->SetStringField(TEXT("node_id"), Input.NodeID.ToString());

#if WITH_EDITORONLY_DATA
		InputJson->SetStringField(TEXT("display_name"), Input.Metadata.GetDisplayName().ToString());
		InputJson->SetStringField(TEXT("description"), Input.Metadata.GetDescription().ToString());
#endif

		if (const FMetasoundFrontendLiteral* DefaultLiteral = Input.FindConstDefault(Metasound::Frontend::DefaultPageID))
		{
			InputJson->SetObjectField(TEXT("default_value"), Introspection_SerializeLiteral(*DefaultLiteral));
		}

		InputsArray.Add(MakeShared<FJsonValueObject>(InputJson));
	}

	TArray<TSharedPtr<FJsonValue>> OutputsArray;
	for (const FMetasoundFrontendClassOutput& Output : ClassInterface.Outputs)
	{
		TSharedPtr<FJsonObject> OutputJson = MakeShared<FJsonObject>();
		OutputJson->SetStringField(TEXT("name"), Output.Name.ToString());
		OutputJson->SetStringField(TEXT("type"), Output.TypeName.ToString());
		OutputJson->SetStringField(TEXT("vertex_id"), Output.VertexID.ToString());
		OutputJson->SetStringField(TEXT("node_id"), Output.NodeID.ToString());

#if WITH_EDITORONLY_DATA
		OutputJson->SetStringField(TEXT("display_name"), Output.Metadata.GetDisplayName().ToString());
		OutputJson->SetStringField(TEXT("description"), Output.Metadata.GetDescription().ToString());
#endif

		OutputsArray.Add(MakeShared<FJsonValueObject>(OutputJson));
	}

	Result->SetArrayField(TEXT("inputs"), InputsArray);
	Result->SetArrayField(TEXT("outputs"), OutputsArray);
	Result->SetNumberField(TEXT("input_count"), InputsArray.Num());
	Result->SetNumberField(TEXT("output_count"), OutputsArray.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleSearchMetaSoundDocumentNodes(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	FString Query = Params->GetStringField(TEXT("query"));
	FString PageIdStr = Params->HasField(TEXT("page_id")) ? Params->GetStringField(TEXT("page_id")) : FString();

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();
	const FMetasoundFrontendGraph* Graph = Introspection_GetGraphFromDoc(Doc, PageIdStr);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Graph page not found: %s"), *PageIdStr), FMonolithJsonUtils::ErrInvalidParams);
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetStringField(TEXT("query"), Query);

	FString QueryLower = Query.ToLower();
	TArray<TSharedPtr<FJsonValue>> MatchesArray;

	for (const FMetasoundFrontendNode& Node : Graph->Nodes)
	{
		FString ClassName = Introspection_ResolveClassName(Node.ClassID, Doc);
		FString NodeName = Node.Name.ToString();

		if (ClassName.ToLower().Contains(QueryLower) || NodeName.ToLower().Contains(QueryLower))
		{
			MatchesArray.Add(MakeShared<FJsonValueObject>(Introspection_SerializeNodeSummary(Node, Doc)));
		}
	}

	Result->SetArrayField(TEXT("matches"), MatchesArray);
	Result->SetNumberField(TEXT("match_count"), MatchesArray.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundInfo(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetStringField(TEXT("asset_class"), Asset->GetClass()->GetName());

	if (Cast<UMetaSoundSource>(Asset))
	{
		Result->SetStringField(TEXT("type"), TEXT("Source"));
	}
	else if (Cast<UMetaSoundPatch>(Asset))
	{
		Result->SetStringField(TEXT("type"), TEXT("Patch"));
	}
	else
	{
		Result->SetStringField(TEXT("type"), TEXT("Unknown"));
	}

	Result->SetStringField(TEXT("root_graph_class"), Doc.RootGraph.Metadata.GetClassName().ToString());

	TSharedPtr<FJsonObject> VersionJson = MakeShared<FJsonObject>();
	VersionJson->SetNumberField(TEXT("major"), Doc.RootGraph.Metadata.GetVersion().Major);
	VersionJson->SetNumberField(TEXT("minor"), Doc.RootGraph.Metadata.GetVersion().Minor);
	Result->SetObjectField(TEXT("version"), VersionJson);

	const FMetasoundFrontendGraph& DefaultGraph = Doc.RootGraph.GetConstDefaultGraph();
	Result->SetNumberField(TEXT("node_count"), DefaultGraph.Nodes.Num());
	Result->SetNumberField(TEXT("edge_count"), DefaultGraph.Edges.Num());
	Result->SetNumberField(TEXT("variable_count"), DefaultGraph.Variables.Num());
	const FMetasoundFrontendClassInterface& InfoInterface = Doc.RootGraph.GetDefaultInterface();
	Result->SetNumberField(TEXT("input_count"), InfoInterface.Inputs.Num());
	Result->SetNumberField(TEXT("output_count"), InfoInterface.Outputs.Num());
	Result->SetNumberField(TEXT("dependency_count"), Doc.Dependencies.Num());
	Result->SetNumberField(TEXT("subgraph_count"), Doc.Subgraphs.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleGetMetaSoundDependencies(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);

	TArray<TSharedPtr<FJsonValue>> DepsArray;
	for (const FMetasoundFrontendClass& Dep : Doc.Dependencies)
	{
		TSharedPtr<FJsonObject> DepJson = MakeShared<FJsonObject>();
		DepJson->SetStringField(TEXT("id"), Dep.ID.ToString());
		DepJson->SetStringField(TEXT("class_name"), Dep.Metadata.GetClassName().ToString());

		FString TypeStr;
		switch (Dep.Metadata.GetType())
		{
		case EMetasoundFrontendClassType::External:
			TypeStr = TEXT("External");
			break;
		case EMetasoundFrontendClassType::Graph:
			TypeStr = TEXT("Graph");
			break;
		case EMetasoundFrontendClassType::Input:
			TypeStr = TEXT("Input");
			break;
		case EMetasoundFrontendClassType::Output:
			TypeStr = TEXT("Output");
			break;
		case EMetasoundFrontendClassType::Variable:
			TypeStr = TEXT("Variable");
			break;
		case EMetasoundFrontendClassType::VariableDeferredAccessor:
			TypeStr = TEXT("VariableDeferredAccessor");
			break;
		case EMetasoundFrontendClassType::VariableAccessor:
			TypeStr = TEXT("VariableAccessor");
			break;
		case EMetasoundFrontendClassType::VariableMutator:
			TypeStr = TEXT("VariableMutator");
			break;
		default:
			TypeStr = TEXT("Unknown");
			break;
		}
		DepJson->SetStringField(TEXT("type"), TypeStr);

		TSharedPtr<FJsonObject> DepVersionJson = MakeShared<FJsonObject>();
		DepVersionJson->SetNumberField(TEXT("major"), Dep.Metadata.GetVersion().Major);
		DepVersionJson->SetNumberField(TEXT("minor"), Dep.Metadata.GetVersion().Minor);
		DepJson->SetObjectField(TEXT("version"), DepVersionJson);

		DepsArray.Add(MakeShared<FJsonValueObject>(DepJson));
	}

	TArray<TSharedPtr<FJsonValue>> SubgraphsArray;
	for (const FMetasoundFrontendGraphClass& Subgraph : Doc.Subgraphs)
	{
		TSharedPtr<FJsonObject> SubJson = MakeShared<FJsonObject>();
		SubJson->SetStringField(TEXT("id"), Subgraph.ID.ToString());
		SubJson->SetStringField(TEXT("class_name"), Subgraph.Metadata.GetClassName().ToString());

		const FMetasoundFrontendGraph& SubGraph = Subgraph.GetConstDefaultGraph();
		SubJson->SetNumberField(TEXT("node_count"), SubGraph.Nodes.Num());

		SubgraphsArray.Add(MakeShared<FJsonValueObject>(SubJson));
	}

	Result->SetArrayField(TEXT("dependencies"), DepsArray);
	Result->SetArrayField(TEXT("subgraphs"), SubgraphsArray);
	Result->SetNumberField(TEXT("dependency_count"), DepsArray.Num());
	Result->SetNumberField(TEXT("subgraph_count"), SubgraphsArray.Num());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleListMetaSounds(const TSharedPtr<FJsonObject>& Params)
{
	FString Filter = Params->HasField(TEXT("filter")) ? Params->GetStringField(TEXT("filter")) : FString();
	FString TypeFilter = Params->HasField(TEXT("type")) ? Params->GetStringField(TEXT("type")) : TEXT("All");

	IAssetRegistry& AssetRegistry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();

	TArray<FAssetData> SourceAssets;
	TArray<FAssetData> PatchAssets;

	bool bIncludeSources = TypeFilter.Equals(TEXT("All"), ESearchCase::IgnoreCase) || TypeFilter.Equals(TEXT("Source"), ESearchCase::IgnoreCase);
	bool bIncludePatches = TypeFilter.Equals(TEXT("All"), ESearchCase::IgnoreCase) || TypeFilter.Equals(TEXT("Patch"), ESearchCase::IgnoreCase);

	if (bIncludeSources)
	{
		AssetRegistry.GetAssetsByClass(UMetaSoundSource::StaticClass()->GetClassPathName(), SourceAssets);
	}
	if (bIncludePatches)
	{
		AssetRegistry.GetAssetsByClass(UMetaSoundPatch::StaticClass()->GetClassPathName(), PatchAssets);
	}

	TArray<FAssetData> AllAssets;
	AllAssets.Append(SourceAssets);
	AllAssets.Append(PatchAssets);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> AssetsArray;

	FString FilterLower = Filter.ToLower();

	for (const FAssetData& AssetData : AllAssets)
	{
		FString AssetName = AssetData.AssetName.ToString();

		if (!Filter.IsEmpty() && !AssetName.ToLower().Contains(FilterLower))
		{
			continue;
		}

		TSharedPtr<FJsonObject> AssetJson = MakeShared<FJsonObject>();
		AssetJson->SetStringField(TEXT("name"), AssetName);
		AssetJson->SetStringField(TEXT("path"), AssetData.PackageName.ToString());
		AssetJson->SetStringField(TEXT("object_path"), AssetData.GetObjectPathString());

		if (AssetData.AssetClassPath == UMetaSoundSource::StaticClass()->GetClassPathName())
		{
			AssetJson->SetStringField(TEXT("type"), TEXT("Source"));
		}
		else
		{
			AssetJson->SetStringField(TEXT("type"), TEXT("Patch"));
		}

		AssetsArray.Add(MakeShared<FJsonValueObject>(AssetJson));
	}

	Result->SetArrayField(TEXT("assets"), AssetsArray);
	Result->SetNumberField(TEXT("count"), AssetsArray.Num());
	Result->SetStringField(TEXT("filter"), Filter);
	Result->SetStringField(TEXT("type_filter"), TypeFilter);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithAudioMetaSoundIntrospectionActions::HandleValidateMetaSound(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));

	UObject* Asset = FMonolithAssetUtils::LoadAssetByPath(AssetPath);
	if (!Asset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset not found: %s"), *AssetPath), FMonolithJsonUtils::ErrInvalidParams);
	}

	IMetaSoundDocumentInterface* DocInterface = Introspection_GetDocumentInterface(Asset);
	if (!DocInterface)
	{
		return FMonolithActionResult::Error(TEXT("Asset is not a MetaSound"), FMonolithJsonUtils::ErrInvalidParams);
	}

	const FMetasoundFrontendDocument& Doc = DocInterface->GetConstDocument();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);

	TArray<TSharedPtr<FJsonValue>> ErrorsArray;
	TArray<TSharedPtr<FJsonValue>> WarningsArray;

	const FMetasoundFrontendGraph& Graph = Doc.RootGraph.GetConstDefaultGraph();

	TSet<FGuid> NodeIds;
	for (const FMetasoundFrontendNode& Node : Graph.Nodes)
	{
		if (NodeIds.Contains(Node.GetID()))
		{
			TSharedPtr<FJsonObject> ErrJson = MakeShared<FJsonObject>();
			ErrJson->SetStringField(TEXT("type"), TEXT("duplicate_node_id"));
			ErrJson->SetStringField(TEXT("node_id"), Node.GetID().ToString());
			ErrJson->SetStringField(TEXT("node_name"), Node.Name.ToString());
			ErrorsArray.Add(MakeShared<FJsonValueObject>(ErrJson));
		}
		NodeIds.Add(Node.GetID());
	}

	for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
	{
		if (!NodeIds.Contains(Edge.FromNodeID))
		{
			TSharedPtr<FJsonObject> ErrJson = MakeShared<FJsonObject>();
			ErrJson->SetStringField(TEXT("type"), TEXT("dangling_edge"));
			ErrJson->SetStringField(TEXT("message"), TEXT("Edge references non-existent source node"));
			ErrJson->SetStringField(TEXT("from_node_id"), Edge.FromNodeID.ToString());
			ErrorsArray.Add(MakeShared<FJsonValueObject>(ErrJson));
		}
		if (!NodeIds.Contains(Edge.ToNodeID))
		{
			TSharedPtr<FJsonObject> ErrJson = MakeShared<FJsonObject>();
			ErrJson->SetStringField(TEXT("type"), TEXT("dangling_edge"));
			ErrJson->SetStringField(TEXT("message"), TEXT("Edge references non-existent target node"));
			ErrJson->SetStringField(TEXT("to_node_id"), Edge.ToNodeID.ToString());
			ErrorsArray.Add(MakeShared<FJsonValueObject>(ErrJson));
		}
	}

	for (const FMetasoundFrontendNode& Node : Graph.Nodes)
	{
		int32 IncomingCount = 0;
		for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
		{
			if (Edge.ToNodeID == Node.GetID())
			{
				IncomingCount++;
			}
		}

		bool bHasDefaults = Node.InputLiterals.Num() > 0;
		int32 UnconnectedInputs = Node.Interface.Inputs.Num() - IncomingCount;

		if (UnconnectedInputs > 0 && !bHasDefaults)
		{
			TSharedPtr<FJsonObject> WarnJson = MakeShared<FJsonObject>();
			WarnJson->SetStringField(TEXT("type"), TEXT("unconnected_inputs"));
			WarnJson->SetStringField(TEXT("node_id"), Node.GetID().ToString());
			WarnJson->SetStringField(TEXT("node_name"), Node.Name.ToString());
			WarnJson->SetNumberField(TEXT("unconnected_count"), UnconnectedInputs);
			WarningsArray.Add(MakeShared<FJsonValueObject>(WarnJson));
		}
	}

	Result->SetArrayField(TEXT("errors"), ErrorsArray);
	Result->SetArrayField(TEXT("warnings"), WarningsArray);
	Result->SetNumberField(TEXT("error_count"), ErrorsArray.Num());
	Result->SetNumberField(TEXT("warning_count"), WarningsArray.Num());
	Result->SetBoolField(TEXT("valid"), ErrorsArray.Num() == 0);

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_METASOUND
