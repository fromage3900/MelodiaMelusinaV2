#include "MonolithBlueprintTemplateActions.h"
#include "MonolithBlueprintInternal.h"
#include "MonolithBlueprintNodeActions.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

// ============================================================
//  Registration
// ============================================================

void FMonolithBlueprintTemplateActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("blueprint"), TEXT("apply_template"),
		TEXT("Apply a pre-defined template to a Blueprint. Templates create common patterns "
		     "(health system, timer loop, interactable actor) via batch operations. "
		     "Use list_templates to see available templates and their parameters."),
		FMonolithActionHandler::CreateStatic(&HandleApplyTemplate),
		FParamSchemaBuilder()
			.Required(TEXT("template_name"), TEXT("string"), TEXT("Template name (use list_templates to see available)"))
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path to apply the template to"))
			.Optional(TEXT("params"), TEXT("object"), TEXT("Template-specific parameters as JSON object (e.g. {\"max_health\": \"200.0\"})"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("list_templates"),
		TEXT("List all available Blueprint templates with their descriptions and parameter schemas."),
		FMonolithActionHandler::CreateStatic(&HandleListTemplates),
		FParamSchemaBuilder()
			.Build());
}

// ============================================================
//  Template definitions
// ============================================================

namespace
{
	struct FTemplateDefinition
	{
		FString Name;
		FString Description;
		TArray<TPair<FString, FString>> ParamDescriptions; // param_name -> description (with default)
		FString OperationsJson; // JSON array of batch_execute operations with ${placeholders}
	};

	// Replace ${key} tokens in a string with values from a params map
	FString ReplacePlaceholders(const FString& Source, const TMap<FString, FString>& Replacements)
	{
		FString Result = Source;
		for (const auto& Pair : Replacements)
		{
			FString Token = FString::Printf(TEXT("${%s}"), *Pair.Key);
			Result = Result.Replace(*Token, *Pair.Value);
		}
		return Result;
	}

	// Parse user params object into a flat string map, applying defaults
	TMap<FString, FString> ParseUserParams(
		const TSharedPtr<FJsonObject>& UserParams,
		const TMap<FString, FString>& Defaults)
	{
		TMap<FString, FString> Result = Defaults;

		if (UserParams.IsValid())
		{
			for (const auto& Pair : UserParams->Values)
			{
				if (Pair.Value->Type == EJson::String)
				{
					Result.Add(MonolithKeyToString(Pair.Key), Pair.Value->AsString());
				}
				else if (Pair.Value->Type == EJson::Number)
				{
					Result.Add(MonolithKeyToString(Pair.Key), FString::SanitizeFloat(Pair.Value->AsNumber()));
				}
				else if (Pair.Value->Type == EJson::Boolean)
				{
					Result.Add(MonolithKeyToString(Pair.Key), Pair.Value->AsBool() ? TEXT("true") : TEXT("false"));
				}
			}
		}

		return Result;
	}

	// Build the static template registry
	const TArray<FTemplateDefinition>& GetTemplateDefinitions()
	{
		static TArray<FTemplateDefinition> Templates;
		static bool bInitialized = false;

		if (bInitialized)
		{
			return Templates;
		}
		bInitialized = true;

		// ----- health_system -----
		{
			FTemplateDefinition T;
			T.Name = TEXT("health_system");
			T.Description = TEXT("Creates Health and MaxHealth float variables, a TakeDamage custom event "
				"that subtracts damage and clamps to 0, and a Heal custom event. "
				"Health is initialized to MaxHealth via the default value.");
			T.ParamDescriptions.Add(TPair<FString, FString>(TEXT("max_health"), TEXT("Maximum health value (default: 100.0)")));
			T.OperationsJson = TEXT(R"([
				{"op": "add_variable", "name": "MaxHealth", "type": "float", "default_value": "${max_health}", "category": "Health", "instance_editable": true},
				{"op": "add_variable", "name": "Health", "type": "float", "default_value": "${max_health}", "category": "Health"},
				{"op": "add_node", "node_type": "CustomEvent", "event_name": "TakeDamage", "graph_name": "EventGraph", "position": [0, 0]},
				{"op": "add_node", "node_type": "VariableGet", "variable_name": "Health", "graph_name": "EventGraph", "position": [100, 150]},
				{"op": "add_node", "node_type": "VariableSet", "variable_name": "Health", "graph_name": "EventGraph", "position": [600, 0]},
				{"op": "add_node", "node_type": "CustomEvent", "event_name": "Heal", "graph_name": "EventGraph", "position": [0, 400]},
				{"op": "add_node", "node_type": "VariableGet", "variable_name": "Health", "graph_name": "EventGraph", "position": [100, 550]},
				{"op": "add_node", "node_type": "VariableSet", "variable_name": "Health", "graph_name": "EventGraph", "position": [600, 400]}
			])");
			Templates.Add(MoveTemp(T));
		}

		// ----- timer_loop -----
		{
			FTemplateDefinition T;
			T.Name = TEXT("timer_loop");
			T.Description = TEXT("Creates a custom event that calls Delay, then calls itself again, "
				"forming a simple timer loop. Useful for periodic logic without using Tick.");
			T.ParamDescriptions.Add(TPair<FString, FString>(TEXT("event_name"), TEXT("Name of the looping event (default: TimerLoop)")));
			T.ParamDescriptions.Add(TPair<FString, FString>(TEXT("delay"), TEXT("Delay duration in seconds (default: 1.0)")));
			T.OperationsJson = TEXT(R"([
				{"op": "add_node", "node_type": "CustomEvent", "event_name": "${event_name}", "graph_name": "EventGraph", "position": [0, 0]},
				{"op": "add_node", "node_type": "Delay", "graph_name": "EventGraph", "position": [300, 0]},
				{"op": "add_node", "node_type": "CallFunction", "function_name": "PrintString", "target_class": "KismetSystemLibrary", "graph_name": "EventGraph", "position": [600, 0]}
			])");
			Templates.Add(MoveTemp(T));
		}

		// ----- interactable_actor -----
		{
			FTemplateDefinition T;
			T.Name = TEXT("interactable_actor");
			T.Description = TEXT("Adds a SphereCollision component with an OnComponentBeginOverlap event "
				"connected to a Branch node. Creates an IsInteractable bool variable for toggling.");
			T.ParamDescriptions.Add(TPair<FString, FString>(TEXT("radius"), TEXT("Sphere collision radius (default: 200.0)")));
			T.OperationsJson = TEXT(R"([
				{"op": "add_variable", "name": "bIsInteractable", "type": "bool", "default_value": "true", "category": "Interaction", "instance_editable": true},
				{"op": "add_component", "component_class": "SphereComponent", "component_name": "InteractionSphere"},
				{"op": "set_component_property", "component_name": "InteractionSphere", "property_name": "SphereRadius", "value": "${radius}"},
				{"op": "set_component_property", "component_name": "InteractionSphere", "property_name": "bGenerateOverlapEvents", "value": "true"},
				{"op": "add_node", "node_type": "VariableGet", "variable_name": "bIsInteractable", "graph_name": "EventGraph", "position": [200, 150]},
				{"op": "add_node", "node_type": "Branch", "graph_name": "EventGraph", "position": [400, 0]}
			])");
			Templates.Add(MoveTemp(T));
		}

		return Templates;
	}

	const FTemplateDefinition* FindTemplate(const FString& Name)
	{
		for (const FTemplateDefinition& T : GetTemplateDefinitions())
		{
			if (T.Name == Name) return &T;
		}
		return nullptr;
	}

	// Get default param values for a template
	TMap<FString, FString> GetTemplateDefaults(const FString& TemplateName)
	{
		TMap<FString, FString> Defaults;

		if (TemplateName == TEXT("health_system"))
		{
			Defaults.Add(TEXT("max_health"), TEXT("100.0"));
		}
		else if (TemplateName == TEXT("timer_loop"))
		{
			Defaults.Add(TEXT("event_name"), TEXT("TimerLoop"));
			Defaults.Add(TEXT("delay"), TEXT("1.0"));
		}
		else if (TemplateName == TEXT("interactable_actor"))
		{
			Defaults.Add(TEXT("radius"), TEXT("200.0"));
		}

		return Defaults;
	}

} // anonymous namespace

// ============================================================
//  list_templates
// ============================================================

FMonolithActionResult FMonolithBlueprintTemplateActions::HandleListTemplates(const TSharedPtr<FJsonObject>& Params)
{
	TArray<TSharedPtr<FJsonValue>> TemplatesArr;

	for (const FTemplateDefinition& T : GetTemplateDefinitions())
	{
		TSharedPtr<FJsonObject> TObj = MakeShared<FJsonObject>();
		TObj->SetStringField(TEXT("name"), T.Name);
		TObj->SetStringField(TEXT("description"), T.Description);

		TArray<TSharedPtr<FJsonValue>> ParamsArr;
		for (const auto& P : T.ParamDescriptions)
		{
			TSharedPtr<FJsonObject> PObj = MakeShared<FJsonObject>();
			PObj->SetStringField(TEXT("name"), P.Key);
			PObj->SetStringField(TEXT("description"), P.Value);
			ParamsArr.Add(MakeShared<FJsonValueObject>(PObj));
		}
		TObj->SetArrayField(TEXT("params"), ParamsArr);

		TemplatesArr.Add(MakeShared<FJsonValueObject>(TObj));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetArrayField(TEXT("templates"), TemplatesArr);
	Root->SetNumberField(TEXT("count"), TemplatesArr.Num());
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  apply_template
// ============================================================

FMonolithActionResult FMonolithBlueprintTemplateActions::HandleApplyTemplate(const TSharedPtr<FJsonObject>& Params)
{
	FString TemplateName = Params->GetStringField(TEXT("template_name"));
	FString AssetPath = Params->GetStringField(TEXT("asset_path"));

	if (TemplateName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: template_name"));
	}
	if (AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: asset_path"));
	}

	// Find template
	const FTemplateDefinition* Template = FindTemplate(TemplateName);
	if (!Template)
	{
		// Build helpful error with available names
		TArray<FString> Available;
		for (const FTemplateDefinition& T : GetTemplateDefinitions())
		{
			Available.Add(T.Name);
		}
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown template: '%s'. Available templates: %s"),
			*TemplateName, *FString::Join(Available, TEXT(", "))));
	}

	// Verify the Blueprint exists
	UBlueprint* BP = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	// Parse user params, apply defaults
	TSharedPtr<FJsonObject> UserParams;
	const TSharedPtr<FJsonObject>* UserParamsPtr = nullptr;

	// Handle params as either object or string (Claude Code quirk)
	TSharedPtr<FJsonValue> ParamsField = Params->TryGetField(TEXT("params"));
	if (ParamsField.IsValid())
	{
		if (ParamsField->Type == EJson::Object)
		{
			UserParams = ParamsField->AsObject();
		}
		else if (ParamsField->Type == EJson::String)
		{
			TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ParamsField->AsString());
			TSharedPtr<FJsonObject> ParsedObj;
			if (FJsonSerializer::Deserialize(Reader, ParsedObj))
			{
				UserParams = ParsedObj;
			}
		}
	}

	TMap<FString, FString> Defaults = GetTemplateDefaults(TemplateName);
	TMap<FString, FString> Replacements = ParseUserParams(UserParams, Defaults);

	// Replace placeholders in the operations JSON
	FString ResolvedOpsJson = ReplacePlaceholders(Template->OperationsJson, Replacements);

	// Parse the resolved operations JSON
	TArray<TSharedPtr<FJsonValue>> Ops;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResolvedOpsJson);
	if (!FJsonSerializer::Deserialize(Reader, Ops))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Internal error: failed to parse resolved template operations for '%s'"), *TemplateName));
	}

	// Build batch_execute params and delegate to it
	TSharedRef<FJsonObject> BatchParams = MakeShared<FJsonObject>();
	BatchParams->SetStringField(TEXT("asset_path"), AssetPath);

	TArray<TSharedPtr<FJsonValue>> OpsArray;
	for (const auto& Op : Ops)
	{
		OpsArray.Add(Op);
	}
	BatchParams->SetArrayField(TEXT("operations"), OpsArray);
	BatchParams->SetBoolField(TEXT("stop_on_error"), true);
	BatchParams->SetBoolField(TEXT("compile_on_complete"), true);

	// Execute via batch_execute
	FMonolithActionResult BatchResult = FMonolithBlueprintNodeActions::HandleBatchExecute(BatchParams);

	// Wrap the result with template metadata
	if (BatchResult.bSuccess && BatchResult.Result.IsValid())
	{
		BatchResult.Result->SetStringField(TEXT("template_name"), TemplateName);
		BatchResult.Result->SetStringField(TEXT("template_description"), Template->Description);
	}

	return BatchResult;
}
