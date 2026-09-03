#include "MonolithNiagaraQueryLibrary.h"

#include "MonolithToolRegistry.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
	/** Serialize a JSON object to a compact FString (matches the in-module idiom at MonolithNiagaraActions.cpp:1303). */
	FString JsonObjectToString(const TSharedPtr<FJsonObject>& Obj)
	{
		FString Out;
		if (!Obj.IsValid())
		{
			return Out;
		}
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Out);
		FJsonSerializer::Serialize(Obj.ToSharedRef(), Writer);
		return Out;
	}

	/** Build a parseable JSON error envelope so callers never receive an empty string on failure. */
	FString MakeErrorEnvelope(const FString& Message, int32 Code)
	{
		const TSharedPtr<FJsonObject> Env = MakeShared<FJsonObject>();
		Env->SetBoolField(TEXT("success"), false);
		Env->SetStringField(TEXT("error"), Message);
		Env->SetNumberField(TEXT("code"), Code);
		return JsonObjectToString(Env);
	}

	/** Set a string field only when non-empty, so empty inputs fall through to the action's own default. */
	void SetOptionalString(const TSharedPtr<FJsonObject>& Params, const FString& Field, const FString& Value)
	{
		if (!Value.IsEmpty())
		{
			Params->SetStringField(Field, Value);
		}
	}

	/** Set an int field only when positive, so non-positive inputs fall through to the action's own default. */
	void SetOptionalPositiveInt(const TSharedPtr<FJsonObject>& Params, const FString& Field, int32 Value)
	{
		if (Value > 0)
		{
			Params->SetNumberField(Field, Value);
		}
	}
}

/**
 * Shared execution path for every wrapper node. Applies the MUST-FIX A defensive guards:
 *   - HasAction pre-flight (registry not yet populated / unknown namespace / unknown action),
 *   - null-/failed-Result protection (never ToSharedRef() a null Result),
 * always setting bOutSuccess + OutError and returning parseable JSON (never an empty string).
 */
static FString ExecuteNiagaraActionAsJson(
	const FString& Action,
	const TSharedPtr<FJsonObject>& Params,
	bool& bOutSuccess,
	FString& OutError)
{
	bOutSuccess = false;
	OutError.Reset();

	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();

	// MUST-FIX A (a)+(b): registry not yet populated, unknown namespace, or unknown action.
	if (!Registry.HasAction(TEXT("niagara"), Action))
	{
		OutError = FString::Printf(
			TEXT("Niagara action '%s' is not registered (registry not yet populated or unknown action)."), *Action);
		return MakeErrorEnvelope(OutError, -32601 /* method not found */);
	}

	const TSharedPtr<FJsonObject> SafeParams = Params.IsValid() ? Params : MakeShared<FJsonObject>();
	const FMonolithActionResult Result = Registry.ExecuteAction(TEXT("niagara"), Action, SafeParams);

	if (!Result.bSuccess)
	{
		OutError = Result.ErrorMessage.IsEmpty()
			? FString::Printf(TEXT("Niagara action '%s' failed with no error message."), *Action)
			: Result.ErrorMessage;
		return MakeErrorEnvelope(OutError, Result.ErrorCode);
	}

	// MUST-FIX A (c): success reported but Result payload is null — do NOT dereference into a crash.
	if (!Result.Result.IsValid())
	{
		OutError = FString::Printf(
			TEXT("Niagara action '%s' reported success but returned a null result payload."), *Action);
		return MakeErrorEnvelope(OutError, -32603 /* internal error */);
	}

	bOutSuccess = true;
	return JsonObjectToString(Result.Result);
}

// =====================================================================================
// Inspection
// =====================================================================================

FString UMonolithNiagaraQueryLibrary::GetNiagaraSystemInfo(
	const FString& AssetPath, const FString& DetailLevel, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	SetOptionalString(Params, TEXT("detail_level"), DetailLevel);
	return ExecuteNiagaraActionAsJson(TEXT("get_system_summary"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraEmitters(
	const FString& AssetPath, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	return ExecuteNiagaraActionAsJson(TEXT("list_emitters"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraEmitterSummary(
	const FString& AssetPath, const FString& Emitter, const FString& DetailLevel, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	Params->SetStringField(TEXT("emitter"), Emitter);
	SetOptionalString(Params, TEXT("detail_level"), DetailLevel);
	return ExecuteNiagaraActionAsJson(TEXT("get_emitter_summary"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraModules(
	const FString& AssetPath, const FString& Emitter, const FString& Usage, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	Params->SetStringField(TEXT("emitter"), Emitter);
	SetOptionalString(Params, TEXT("usage"), Usage);
	return ExecuteNiagaraActionAsJson(TEXT("get_ordered_modules"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraModuleInputs(
	const FString& AssetPath, const FString& Emitter, const FString& ModuleNode, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	Params->SetStringField(TEXT("emitter"), Emitter);
	Params->SetStringField(TEXT("module_node"), ModuleNode);
	return ExecuteNiagaraActionAsJson(TEXT("get_module_inputs"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraModuleGraph(
	const FString& ScriptPath, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("script_path"), ScriptPath);
	return ExecuteNiagaraActionAsJson(TEXT("get_module_graph"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraParameters(
	const FString& AssetPath, const FString& Emitter, const FString& Scope, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	SetOptionalString(Params, TEXT("emitter"), Emitter);
	SetOptionalString(Params, TEXT("scope"), Scope);
	return ExecuteNiagaraActionAsJson(TEXT("get_all_parameters"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraUserParameters(
	const FString& AssetPath, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	return ExecuteNiagaraActionAsJson(TEXT("get_user_parameters"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraRenderers(
	const FString& AssetPath, const FString& Emitter, bool bIncludeBindings, int32 RendererIndex,
	bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	Params->SetStringField(TEXT("emitter"), Emitter);

	if (bIncludeBindings)
	{
		// get_renderer_bindings requires a renderer_index; report the specific binding set.
		Params->SetNumberField(TEXT("renderer_index"), RendererIndex);
		return ExecuteNiagaraActionAsJson(TEXT("get_renderer_bindings"), Params, bSuccess, OutError);
	}

	return ExecuteNiagaraActionAsJson(TEXT("list_renderers"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraEvents(
	const FString& AssetPath, const FString& Emitter, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	Params->SetStringField(TEXT("emitter"), Emitter);
	return ExecuteNiagaraActionAsJson(TEXT("get_event_handlers"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraDIFunctions(
	const FString& DIClass, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("di_class"), DIClass);
	return ExecuteNiagaraActionAsJson(TEXT("get_di_functions"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraSimulationStages(
	const FString& AssetPath, const FString& Emitter, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	Params->SetStringField(TEXT("emitter"), Emitter);
	return ExecuteNiagaraActionAsJson(TEXT("get_simulation_stages"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraStats(
	const FString& AssetPath, bool bCompileFirst, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	if (bCompileFirst)
	{
		Params->SetBoolField(TEXT("compile_first"), true);
	}
	return ExecuteNiagaraActionAsJson(TEXT("get_system_diagnostics"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraInventory(
	const FString& Search, const FString& Path, int32 Limit, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	SetOptionalString(Params, TEXT("search"), Search);
	SetOptionalString(Params, TEXT("path"), Path);
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	return ExecuteNiagaraActionAsJson(TEXT("list_systems"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraHLSLOutput(
	const FString& AssetPath, const FString& Emitter, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	Params->SetStringField(TEXT("emitter"), Emitter);
	return ExecuteNiagaraActionAsJson(TEXT("get_compiled_gpu_hlsl"), Params, bSuccess, OutError);
}

// =====================================================================================
// Search & Discovery
// =====================================================================================

FString UMonolithNiagaraQueryLibrary::SearchNiagaraSystems(
	const FString& Search, const FString& Path, int32 Limit, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	SetOptionalString(Params, TEXT("search"), Search);
	SetOptionalString(Params, TEXT("path"), Path);
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	return ExecuteNiagaraActionAsJson(TEXT("list_systems"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::SearchNiagaraModules(
	const FString& Search, const FString& Usage, int32 Limit, bool bIncludeMetadata, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	SetOptionalString(Params, TEXT("search"), Search);
	SetOptionalString(Params, TEXT("usage"), Usage);
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	if (bIncludeMetadata)
	{
		Params->SetBoolField(TEXT("include_metadata"), true);
	}
	return ExecuteNiagaraActionAsJson(TEXT("list_module_scripts"), Params, bSuccess, OutError);
}

// =====================================================================================
// Tranche 2 (#64): Search & Discovery gap-action nodes + per-system DI
// =====================================================================================

FString UMonolithNiagaraQueryLibrary::SearchNiagaraByParameter(
	const FString& ParameterName, const FString& ParameterType, const FString& Folder, int32 Limit,
	bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("parameter_name"), ParameterName);
	SetOptionalString(Params, TEXT("parameter_type"), ParameterType);
	SetOptionalString(Params, TEXT("folder"), Folder);
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	return ExecuteNiagaraActionAsJson(TEXT("search_by_parameter"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::SearchNiagaraByDataInterface(
	const FString& DIClass, const FString& Folder, int32 Limit, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("di_class"), DIClass);
	SetOptionalString(Params, TEXT("folder"), Folder);
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	return ExecuteNiagaraActionAsJson(TEXT("search_by_data_interface"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::QueryNiagara(
	const FString& QueryString, const FString& Folder, int32 Limit, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("query_string"), QueryString);
	SetOptionalString(Params, TEXT("folder"), Folder);
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	return ExecuteNiagaraActionAsJson(TEXT("query_niagara"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::FindSimilarNiagaraSystems(
	const FString& AssetPath, float Threshold, int32 Limit, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	// Forward threshold only when in (0,1); non-positive falls through to the action's 0.5 default.
	if (Threshold > 0.0f)
	{
		Params->SetNumberField(TEXT("threshold"), Threshold);
	}
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	return ExecuteNiagaraActionAsJson(TEXT("find_similar_systems"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::SearchNiagaraByMaterial(
	const FString& MaterialPath, const FString& Folder, int32 Limit, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("material_path"), MaterialPath);
	SetOptionalString(Params, TEXT("folder"), Folder);
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	return ExecuteNiagaraActionAsJson(TEXT("search_by_material"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::FindNiagaraReferences(
	const FString& AssetPath, int32 Limit, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	SetOptionalPositiveInt(Params, TEXT("limit"), Limit);
	return ExecuteNiagaraActionAsJson(TEXT("find_niagara_references"), Params, bSuccess, OutError);
}

FString UMonolithNiagaraQueryLibrary::GetNiagaraDataInterfaces(
	const FString& AssetPath, bool& bSuccess, FString& OutError)
{
	const TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("asset_path"), AssetPath);
	return ExecuteNiagaraActionAsJson(TEXT("list_system_data_interfaces"), Params, bSuccess, OutError);
}
