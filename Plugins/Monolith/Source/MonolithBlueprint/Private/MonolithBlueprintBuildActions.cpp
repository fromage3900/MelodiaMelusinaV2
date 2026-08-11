#include "MonolithBlueprintBuildActions.h"
#include "MonolithBlueprintInternal.h"
#include "MonolithBlueprintVariableActions.h"
#include "MonolithBlueprintComponentActions.h"
#include "MonolithBlueprintNodeActions.h"
#include "MonolithBlueprintCompileActions.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Editor.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

// ============================================================
//  Registration
// ============================================================

void FMonolithBlueprintBuildActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("blueprint"), TEXT("build_blueprint_from_spec"),
		TEXT("Declarative one-shot Blueprint graph builder. Takes a JSON spec and creates variables, components, "
		     "nodes, connections, and pin defaults in a single transaction. Modeled after build_material_graph. "
		     "Nodes use caller-defined 'id' fields that are resolved to actual UE node IDs in connections and pin_defaults. "
		     "Returns a full summary with ID mapping, connection results, and any warnings."),
		FMonolithActionHandler::CreateStatic(&HandleBuildBlueprintFromSpec),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"),   TEXT("Blueprint asset path (must already exist)"))
			.Optional(TEXT("graph_name"),   TEXT("string"),  TEXT("Target graph name (defaults to EventGraph)"))
			.Optional(TEXT("variables"),    TEXT("array"),   TEXT("Array of variable descriptors: [{name, type, default_value?, category?, instance_editable?, blueprint_read_only?, expose_on_spawn?, replicated?, transient?}]"))
			.Optional(TEXT("components"),   TEXT("array"),   TEXT("Array of component descriptors: [{name, class, parent?}]"))
			.Optional(TEXT("nodes"),        TEXT("array"),   TEXT("Array of node descriptors: [{id, type, position?, function_name?, target_class?, variable_name?, event_name?, macro_name?, macro_blueprint?, cast_class?, actor_class?, struct_type?, enum_type?, format?, num_entries?}]"))
			.Optional(TEXT("connections"),  TEXT("array"),   TEXT("Array of connection descriptors: [{source, source_pin, target, target_pin}] — source/target use the 'id' from nodes array"))
			.Optional(TEXT("pin_defaults"), TEXT("array"),   TEXT("Array of pin default descriptors: [{node_id, pin_name, value}] — node_id uses the 'id' from nodes array"))
			.Optional(TEXT("auto_compile"), TEXT("boolean"), TEXT("Compile the Blueprint after building (default: false)"))
			.Build());
}

// ============================================================
//  Helpers
// ============================================================

namespace
{
	/**
	 * Parse a JSON array field that may be either an actual array or a JSON string
	 * (Claude Code quirk: nested arrays sometimes arrive as serialized strings).
	 */
	bool ParseJsonArray(const TSharedPtr<FJsonObject>& Params, const FString& FieldName, TArray<TSharedPtr<FJsonValue>>& OutArray)
	{
		TSharedPtr<FJsonValue> Field = Params->TryGetField(FieldName);
		if (!Field.IsValid())
		{
			return false; // Field not present — not an error, just absent
		}

		if (Field->Type == EJson::Array)
		{
			OutArray = Field->AsArray();
			return true;
		}

		if (Field->Type == EJson::String)
		{
			TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Field->AsString());
			if (FJsonSerializer::Deserialize(Reader, OutArray))
			{
				return true;
			}
		}

		return false;
	}

	/** Build a sub-params object for delegating to an existing handler. */
	TSharedRef<FJsonObject> MakeSubParams(const FString& AssetPath)
	{
		TSharedRef<FJsonObject> Sub = MakeShared<FJsonObject>();
		Sub->SetStringField(TEXT("asset_path"), AssetPath);
		return Sub;
	}

	/** Extract a string field from a JSON object, returning empty string if absent. */
	FString GetStr(const TSharedPtr<FJsonObject>& Obj, const FString& Key)
	{
		FString Val;
		Obj->TryGetStringField(Key, Val);
		return Val;
	}
}

// ============================================================
//  build_blueprint_from_spec
// ============================================================

FMonolithActionResult FMonolithBlueprintBuildActions::HandleBuildBlueprintFromSpec(const TSharedPtr<FJsonObject>& Params)
{
	// ---- Load Blueprint ----
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString GraphName = GetStr(Params, TEXT("graph_name"));

	// Verify graph exists early
	UEdGraph* Graph = MonolithBlueprintInternal::FindGraphByName(BP, GraphName);
	if (!Graph)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Graph not found: %s"), GraphName.IsEmpty() ? TEXT("EventGraph") : *GraphName));
	}

	// ---- Begin transaction ----
	GEditor->BeginTransaction(NSLOCTEXT("Monolith", "BuildBPFromSpec", "Build Blueprint From Spec"));

	TArray<TSharedPtr<FJsonValue>> Warnings;
	int32 VariablesCreated = 0;
	int32 ComponentsCreated = 0;
	int32 NodesCreated = 0;
	int32 ConnectionsMade = 0;
	int32 PinDefaultsSet = 0;
	int32 Errors = 0;

	// ID mapping: spec "id" -> actual UE node GetName()
	TMap<FString, FString> IdMap;

	auto AddWarning = [&Warnings](const FString& Phase, const FString& Message)
	{
		TSharedPtr<FJsonObject> W = MakeShared<FJsonObject>();
		W->SetStringField(TEXT("phase"), Phase);
		W->SetStringField(TEXT("message"), Message);
		Warnings.Add(MakeShared<FJsonValueObject>(W));
	};

	auto AddError = [&Warnings, &Errors](const FString& Phase, const FString& Message)
	{
		TSharedPtr<FJsonObject> W = MakeShared<FJsonObject>();
		W->SetStringField(TEXT("phase"), Phase);
		W->SetStringField(TEXT("error"), Message);
		Warnings.Add(MakeShared<FJsonValueObject>(W));
		Errors++;
	};

	// ============================================================
	//  Phase 1: Variables
	// ============================================================
	{
		TArray<TSharedPtr<FJsonValue>> VarSpecs;
		if (ParseJsonArray(Params, TEXT("variables"), VarSpecs))
		{
			for (int32 i = 0; i < VarSpecs.Num(); ++i)
			{
				TSharedPtr<FJsonObject> VarObj = VarSpecs[i]->AsObject();
				if (!VarObj.IsValid())
				{
					AddError(TEXT("variables"), FString::Printf(TEXT("Variable at index %d is not a valid JSON object"), i));
					continue;
				}

				// Build params for HandleAddVariable
				TSharedRef<FJsonObject> SubParams = MakeSubParams(AssetPath);

				// Copy all fields from the variable spec
				for (const auto& Pair : VarObj->Values)
				{
					SubParams->SetField(Pair.Key, Pair.Value);
				}

				FMonolithActionResult Result = FMonolithBlueprintVariableActions::HandleAddVariable(SubParams);
				if (Result.bSuccess)
				{
					VariablesCreated++;
				}
				else
				{
					AddError(TEXT("variables"), FString::Printf(
						TEXT("Variable '%s': %s"), *GetStr(VarObj, TEXT("name")), *Result.ErrorMessage));
				}
			}
		}
	}

	// ============================================================
	//  Phase 2: Components
	// ============================================================
	{
		TArray<TSharedPtr<FJsonValue>> CompSpecs;
		if (ParseJsonArray(Params, TEXT("components"), CompSpecs))
		{
			for (int32 i = 0; i < CompSpecs.Num(); ++i)
			{
				TSharedPtr<FJsonObject> CompObj = CompSpecs[i]->AsObject();
				if (!CompObj.IsValid())
				{
					AddError(TEXT("components"), FString::Printf(TEXT("Component at index %d is not a valid JSON object"), i));
					continue;
				}

				TSharedRef<FJsonObject> SubParams = MakeSubParams(AssetPath);

				// Map spec fields to handler fields:
				// "name" -> "component_name", "class" -> "component_class"
				FString CompName = GetStr(CompObj, TEXT("name"));
				FString CompClass = GetStr(CompObj, TEXT("class"));
				FString CompParent = GetStr(CompObj, TEXT("parent"));

				SubParams->SetStringField(TEXT("component_name"), CompName);
				SubParams->SetStringField(TEXT("component_class"), CompClass);
				if (!CompParent.IsEmpty())
				{
					SubParams->SetStringField(TEXT("parent"), CompParent);
				}

				FMonolithActionResult Result = FMonolithBlueprintComponentActions::HandleAddComponent(SubParams);
				if (Result.bSuccess)
				{
					ComponentsCreated++;
				}
				else
				{
					AddError(TEXT("components"), FString::Printf(
						TEXT("Component '%s': %s"), *CompName, *Result.ErrorMessage));
				}
			}
		}
	}

	// ============================================================
	//  Phase 3: Nodes
	// ============================================================
	{
		TArray<TSharedPtr<FJsonValue>> NodeSpecs;
		if (ParseJsonArray(Params, TEXT("nodes"), NodeSpecs))
		{
			for (int32 i = 0; i < NodeSpecs.Num(); ++i)
			{
				TSharedPtr<FJsonObject> NodeObj = NodeSpecs[i]->AsObject();
				if (!NodeObj.IsValid())
				{
					AddError(TEXT("nodes"), FString::Printf(TEXT("Node at index %d is not a valid JSON object"), i));
					continue;
				}

				FString SpecId = GetStr(NodeObj, TEXT("id"));
				if (SpecId.IsEmpty())
				{
					AddError(TEXT("nodes"), FString::Printf(TEXT("Node at index %d is missing required 'id' field"), i));
					continue;
				}

				FString NodeType = GetStr(NodeObj, TEXT("type"));
				if (NodeType.IsEmpty())
				{
					AddError(TEXT("nodes"), FString::Printf(TEXT("Node '%s' is missing required 'type' field"), *SpecId));
					continue;
				}

				// Build params for HandleAddNode
				TSharedRef<FJsonObject> SubParams = MakeSubParams(AssetPath);
				SubParams->SetStringField(TEXT("node_type"), NodeType);

				if (!GraphName.IsEmpty())
				{
					SubParams->SetStringField(TEXT("graph_name"), GraphName);
				}

				// Copy optional node params — position, function_name, target_class, variable_name,
				// event_name, macro_name, macro_blueprint, cast_class, actor_class, struct_type,
				// enum_type, format, num_entries
				static const TCHAR* NodeParamKeys[] = {
					TEXT("position"), TEXT("function_name"), TEXT("target_class"),
					TEXT("variable_name"), TEXT("event_name"), TEXT("macro_name"),
					TEXT("macro_blueprint"), TEXT("cast_class"), TEXT("actor_class"),
					TEXT("struct_type"), TEXT("enum_type"), TEXT("format"), TEXT("num_entries")
				};

				for (const TCHAR* Key : NodeParamKeys)
				{
					TSharedPtr<FJsonValue> Val = NodeObj->TryGetField(Key);
					if (Val.IsValid())
					{
						SubParams->SetField(Key, Val);
					}
				}

				FMonolithActionResult Result = FMonolithBlueprintNodeActions::HandleAddNode(SubParams);
				if (Result.bSuccess)
				{
					NodesCreated++;

					// Extract the actual UE node ID from the result
					FString ActualNodeId;
					if (Result.Result.IsValid())
					{
						ActualNodeId = GetStr(Result.Result, TEXT("id"));
					}

					if (!ActualNodeId.IsEmpty())
					{
						IdMap.Add(SpecId, ActualNodeId);
					}
					else
					{
						AddWarning(TEXT("nodes"), FString::Printf(
							TEXT("Node '%s' created but could not extract UE node ID from result"), *SpecId));
					}
				}
				else
				{
					AddError(TEXT("nodes"), FString::Printf(
						TEXT("Node '%s' (type=%s): %s"), *SpecId, *NodeType, *Result.ErrorMessage));
				}
			}
		}
	}

	// ============================================================
	//  Phase 4: Connections
	// ============================================================
	{
		TArray<TSharedPtr<FJsonValue>> ConnSpecs;
		if (ParseJsonArray(Params, TEXT("connections"), ConnSpecs))
		{
			for (int32 i = 0; i < ConnSpecs.Num(); ++i)
			{
				TSharedPtr<FJsonObject> ConnObj = ConnSpecs[i]->AsObject();
				if (!ConnObj.IsValid())
				{
					AddError(TEXT("connections"), FString::Printf(TEXT("Connection at index %d is not a valid JSON object"), i));
					continue;
				}

				FString SourceSpecId = GetStr(ConnObj, TEXT("source"));
				FString SourcePin = GetStr(ConnObj, TEXT("source_pin"));
				FString TargetSpecId = GetStr(ConnObj, TEXT("target"));
				FString TargetPin = GetStr(ConnObj, TEXT("target_pin"));

				if (SourceSpecId.IsEmpty() || SourcePin.IsEmpty() || TargetSpecId.IsEmpty() || TargetPin.IsEmpty())
				{
					AddError(TEXT("connections"), FString::Printf(
						TEXT("Connection at index %d missing required fields (source, source_pin, target, target_pin)"), i));
					continue;
				}

				// Resolve spec IDs to actual UE node IDs
				const FString* SourceNodeId = IdMap.Find(SourceSpecId);
				const FString* TargetNodeId = IdMap.Find(TargetSpecId);

				if (!SourceNodeId)
				{
					AddError(TEXT("connections"), FString::Printf(
						TEXT("Connection %d: source '%s' not found in ID map — was the node created successfully?"), i, *SourceSpecId));
					continue;
				}
				if (!TargetNodeId)
				{
					AddError(TEXT("connections"), FString::Printf(
						TEXT("Connection %d: target '%s' not found in ID map — was the node created successfully?"), i, *TargetSpecId));
					continue;
				}

				// Build params for HandleConnectPins
				TSharedRef<FJsonObject> SubParams = MakeSubParams(AssetPath);
				SubParams->SetStringField(TEXT("source_node"), *SourceNodeId);
				SubParams->SetStringField(TEXT("source_pin"), SourcePin);
				SubParams->SetStringField(TEXT("target_node"), *TargetNodeId);
				SubParams->SetStringField(TEXT("target_pin"), TargetPin);

				if (!GraphName.IsEmpty())
				{
					SubParams->SetStringField(TEXT("graph_name"), GraphName);
				}

				FMonolithActionResult Result = FMonolithBlueprintNodeActions::HandleConnectPins(SubParams);
				if (Result.bSuccess)
				{
					ConnectionsMade++;
				}
				else
				{
					AddError(TEXT("connections"), FString::Printf(
						TEXT("Connection %d (%s.%s -> %s.%s): %s"),
						i, *SourceSpecId, *SourcePin, *TargetSpecId, *TargetPin, *Result.ErrorMessage));
				}
			}
		}
	}

	// ============================================================
	//  Phase 5: Pin Defaults
	// ============================================================
	{
		TArray<TSharedPtr<FJsonValue>> PinSpecs;
		if (ParseJsonArray(Params, TEXT("pin_defaults"), PinSpecs))
		{
			for (int32 i = 0; i < PinSpecs.Num(); ++i)
			{
				TSharedPtr<FJsonObject> PinObj = PinSpecs[i]->AsObject();
				if (!PinObj.IsValid())
				{
					AddError(TEXT("pin_defaults"), FString::Printf(TEXT("Pin default at index %d is not a valid JSON object"), i));
					continue;
				}

				FString SpecNodeId = GetStr(PinObj, TEXT("node_id"));
				FString PinName = GetStr(PinObj, TEXT("pin_name"));
				FString Value = GetStr(PinObj, TEXT("value"));

				if (SpecNodeId.IsEmpty() || PinName.IsEmpty())
				{
					AddError(TEXT("pin_defaults"), FString::Printf(
						TEXT("Pin default at index %d missing required fields (node_id, pin_name)"), i));
					continue;
				}

				// Resolve spec ID to actual UE node ID
				const FString* ActualNodeId = IdMap.Find(SpecNodeId);
				if (!ActualNodeId)
				{
					AddError(TEXT("pin_defaults"), FString::Printf(
						TEXT("Pin default %d: node_id '%s' not found in ID map — was the node created successfully?"), i, *SpecNodeId));
					continue;
				}

				// Build params for HandleSetPinDefault
				TSharedRef<FJsonObject> SubParams = MakeSubParams(AssetPath);
				SubParams->SetStringField(TEXT("node_id"), *ActualNodeId);
				SubParams->SetStringField(TEXT("pin_name"), PinName);
				SubParams->SetStringField(TEXT("value"), Value);

				if (!GraphName.IsEmpty())
				{
					SubParams->SetStringField(TEXT("graph_name"), GraphName);
				}

				FMonolithActionResult Result = FMonolithBlueprintNodeActions::HandleSetPinDefault(SubParams);
				if (Result.bSuccess)
				{
					PinDefaultsSet++;
				}
				else
				{
					AddError(TEXT("pin_defaults"), FString::Printf(
						TEXT("Pin default %d (%s.%s = '%s'): %s"),
						i, *SpecNodeId, *PinName, *Value, *Result.ErrorMessage));
				}
			}
		}
	}

	// ---- End transaction ----
	GEditor->EndTransaction();

	// ============================================================
	//  Phase 6: Auto-compile
	// ============================================================
	bool bCompiled = false;
	bool bCompileSuccess = false;
	TSharedPtr<FJsonObject> CompileResult;

	bool bAutoCompile = false;
	Params->TryGetBoolField(TEXT("auto_compile"), bAutoCompile);

	if (bAutoCompile)
	{
		TSharedRef<FJsonObject> CompileParams = MakeSubParams(AssetPath);
		FMonolithActionResult CResult = FMonolithBlueprintCompileActions::HandleCompileBlueprint(CompileParams);
		bCompiled = true;
		bCompileSuccess = CResult.bSuccess;
		CompileResult = CResult.Result;

		if (!CResult.bSuccess)
		{
			AddWarning(TEXT("compile"), FString::Printf(TEXT("Compilation failed: %s"), *CResult.ErrorMessage));
		}
	}

	// ============================================================
	//  Build response
	// ============================================================
	TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("graph"), Graph->GetName());
	Root->SetBoolField(TEXT("success"), Errors == 0);

	// Summary counts
	TSharedRef<FJsonObject> Summary = MakeShared<FJsonObject>();
	Summary->SetNumberField(TEXT("variables_created"), VariablesCreated);
	Summary->SetNumberField(TEXT("components_created"), ComponentsCreated);
	Summary->SetNumberField(TEXT("nodes_created"), NodesCreated);
	Summary->SetNumberField(TEXT("connections_made"), ConnectionsMade);
	Summary->SetNumberField(TEXT("pin_defaults_set"), PinDefaultsSet);
	Summary->SetNumberField(TEXT("errors"), Errors);
	Root->SetObjectField(TEXT("summary"), Summary);

	// ID mapping — spec IDs to UE node names
	TSharedRef<FJsonObject> IdMapJson = MakeShared<FJsonObject>();
	for (const auto& Pair : IdMap)
	{
		IdMapJson->SetStringField(Pair.Key, Pair.Value);
	}
	Root->SetObjectField(TEXT("id_map"), IdMapJson);

	// Warnings and errors
	if (Warnings.Num() > 0)
	{
		Root->SetArrayField(TEXT("details"), Warnings);
	}

	// Compile result
	if (bCompiled)
	{
		Root->SetBoolField(TEXT("compiled"), true);
		Root->SetBoolField(TEXT("compile_success"), bCompileSuccess);
		if (CompileResult.IsValid())
		{
			Root->SetObjectField(TEXT("compile_result"), CompileResult);
		}
	}

	return FMonolithActionResult::Success(Root);
}
