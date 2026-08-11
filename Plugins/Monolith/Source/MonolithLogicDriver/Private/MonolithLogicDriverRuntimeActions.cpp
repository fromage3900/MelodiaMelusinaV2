#include "MonolithLogicDriverRuntimeActions.h"
#include "MonolithParamSchema.h"

#if WITH_LOGICDRIVER

#include "MonolithLogicDriverInternal.h"
#include "Editor.h"
#include "EngineUtils.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

DEFINE_LOG_CATEGORY_STATIC(LogMonolithLDRuntime, Log, All);

// ── Shared PIE helper ──────────────────────────────────────────────

namespace
{
	struct FPIELookupResult
	{
		UObject* SMInstance = nullptr;
		UActorComponent* Component = nullptr;
		AActor* Actor = nullptr;
		FMonolithActionResult Error;
		bool bSuccess = false;
	};

	FPIELookupResult FindSMInstanceInPIE(const TSharedPtr<FJsonObject>& Params)
	{
		FPIELookupResult Result;

		FString ActorName = Params->GetStringField(TEXT("actor"));
		if (ActorName.IsEmpty())
		{
			Result.Error = FMonolithActionResult::Error(TEXT("Missing required param 'actor'"));
			return Result;
		}

		FString ComponentName;
		if (Params->HasField(TEXT("component_name")))
		{
			ComponentName = Params->GetStringField(TEXT("component_name"));
		}

		// Get PIE world
		FWorldContext* PIEContext = GEditor->GetPIEWorldContext();
		if (!PIEContext || !PIEContext->World())
		{
			Result.Error = FMonolithActionResult::Error(TEXT("PIE not running — start Play-In-Editor first"));
			return Result;
		}
		UWorld* PIEWorld = PIEContext->World();

		// Find actor
		for (TActorIterator<AActor> It(PIEWorld); It; ++It)
		{
			if (It->GetActorLabel() == ActorName || It->GetName() == ActorName)
			{
				Result.Actor = *It;
				break;
			}
		}
		if (!Result.Actor)
		{
			Result.Error = FMonolithActionResult::Error(FString::Printf(TEXT("Actor '%s' not found in PIE world"), *ActorName));
			return Result;
		}

		// Find SM component
		UClass* SMCompClass = MonolithLD::GetSMComponentClass();
		if (!SMCompClass)
		{
			Result.Error = FMonolithActionResult::Error(TEXT("SMStateMachineComponent class not found"));
			return Result;
		}

		for (UActorComponent* C : Result.Actor->GetComponents())
		{
			if (!C || !C->GetClass()->IsChildOf(SMCompClass)) continue;
			if (ComponentName.IsEmpty() || C->GetName() == ComponentName)
			{
				Result.Component = C;
				break;
			}
		}
		if (!Result.Component)
		{
			Result.Error = FMonolithActionResult::Error(FString::Printf(
				TEXT("No SM component%s found on actor '%s'"),
				ComponentName.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(" named '%s'"), *ComponentName),
				*ActorName));
			return Result;
		}

		// Get SM instance via reflection
		Result.SMInstance = MonolithLD::GetObjectProperty(Result.Component, TEXT("Instance"));
		if (!Result.SMInstance)
		{
			Result.SMInstance = MonolithLD::GetObjectProperty(Result.Component, TEXT("StateMachineInstance"));
		}
		if (!Result.SMInstance)
		{
			Result.Error = FMonolithActionResult::Error(TEXT("SM component has no active SM instance (is the SM started?)"));
			return Result;
		}

		Result.bSuccess = true;
		return Result;
	}

	/** Call a no-arg UFunction on a UObject by name. Returns true if found and called. */
	bool CallFunction(UObject* Obj, const TCHAR* FuncName)
	{
		if (!Obj) return false;
		UFunction* Func = Obj->FindFunction(FName(FuncName));
		if (!Func) return false;
		Obj->ProcessEvent(Func, nullptr);
		return true;
	}
}

// ── Registration ────────────────────────────────────────────────────

void FMonolithLogicDriverRuntimeActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("runtime_get_sm_state"),
		TEXT("Get the active state(s) of a live SM instance in PIE — state name, GUID, time in state"),
		FMonolithActionHandler::CreateStatic(&HandleRuntimeGetSMState),
		FParamSchemaBuilder()
			.Required(TEXT("actor"), TEXT("string"), TEXT("Actor label or name in PIE world"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("SM component name (if multiple on actor)"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("runtime_start_sm"),
		TEXT("Initialize and start a live SM instance during PIE"),
		FMonolithActionHandler::CreateStatic(&HandleRuntimeStartSM),
		FParamSchemaBuilder()
			.Required(TEXT("actor"), TEXT("string"), TEXT("Actor label or name in PIE world"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("SM component name"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("runtime_stop_sm"),
		TEXT("Stop a live SM instance during PIE"),
		FMonolithActionHandler::CreateStatic(&HandleRuntimeStopSM),
		FParamSchemaBuilder()
			.Required(TEXT("actor"), TEXT("string"), TEXT("Actor label or name in PIE world"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("SM component name"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("runtime_restart_sm"),
		TEXT("Restart a live SM instance during PIE (stop + initialize + start)"),
		FMonolithActionHandler::CreateStatic(&HandleRuntimeRestartSM),
		FParamSchemaBuilder()
			.Required(TEXT("actor"), TEXT("string"), TEXT("Actor label or name in PIE world"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("SM component name"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("runtime_switch_state"),
		TEXT("Force-switch to a specific state by GUID during PIE"),
		FMonolithActionHandler::CreateStatic(&HandleRuntimeSwitchState),
		FParamSchemaBuilder()
			.Required(TEXT("actor"), TEXT("string"), TEXT("Actor label or name in PIE world"))
			.Required(TEXT("state_guid"), TEXT("string"), TEXT("GUID of the target state node"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("SM component name"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("runtime_evaluate_transitions"),
		TEXT("Force transition evaluation on a live SM instance during PIE"),
		FMonolithActionHandler::CreateStatic(&HandleRuntimeEvaluateTransitions),
		FParamSchemaBuilder()
			.Required(TEXT("actor"), TEXT("string"), TEXT("Actor label or name in PIE world"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("SM component name"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("runtime_get_state_history"),
		TEXT("Get state transition history from a live SM instance during PIE"),
		FMonolithActionHandler::CreateStatic(&HandleRuntimeGetStateHistory),
		FParamSchemaBuilder()
			.Required(TEXT("actor"), TEXT("string"), TEXT("Actor label or name in PIE world"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("SM component name"))
			.Optional(TEXT("limit"), TEXT("number"), TEXT("Max history entries to return (default: 50)"))
			.Build());

	UE_LOG(LogMonolithLDRuntime, Log, TEXT("MonolithLogicDriver Runtime: registered 7 actions"));
}

// ── runtime_get_sm_state ────────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverRuntimeActions::HandleRuntimeGetSMState(const TSharedPtr<FJsonObject>& Params)
{
	FPIELookupResult Lookup = FindSMInstanceInPIE(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	UObject* SMInst = Lookup.SMInstance;

	// Get active state names via reflection
	// Try GetActiveStateNames or read ActiveStates array
	TArray<TSharedPtr<FJsonValue>> ActiveStates;

	// Try calling GetSingleActiveState — returns a struct with Guid and name
	// Fallback: read properties directly
	FString ActiveStateName = MonolithLD::GetStringProperty(SMInst, TEXT("ActiveStateName"));
	if (ActiveStateName.IsEmpty())
	{
		ActiveStateName = MonolithLD::GetStringProperty(SMInst, TEXT("CurrentStateName"));
	}

	float TimeInState = MonolithLD::GetFloatProperty(SMInst, TEXT("TimeInState"));
	bool bIsActive = MonolithLD::GetBoolProperty(SMInst, TEXT("bIsActive"));
	if (!bIsActive)
	{
		// Try alternative property name
		bIsActive = MonolithLD::GetBoolProperty(SMInst, TEXT("bHasStarted"));
	}

	// Try to get active state GUIDs via function call
	// USMInstance::GetSingleActiveStateGuid()
	FString ActiveStateGuid;
	{
		UFunction* Func = SMInst->FindFunction(TEXT("GetSingleActiveStateGuid"));
		if (Func)
		{
			struct { FGuid ReturnValue; } FuncParams;
			SMInst->ProcessEvent(Func, &FuncParams);
			ActiveStateGuid = FuncParams.ReturnValue.ToString();
		}
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
	Result->SetStringField(TEXT("component"), Lookup.Component->GetName());
	Result->SetBoolField(TEXT("is_active"), bIsActive);
	if (!ActiveStateName.IsEmpty()) Result->SetStringField(TEXT("active_state_name"), ActiveStateName);
	if (!ActiveStateGuid.IsEmpty()) Result->SetStringField(TEXT("active_state_guid"), ActiveStateGuid);
	Result->SetNumberField(TEXT("time_in_state"), TimeInState);

	return FMonolithActionResult::Success(Result);
}

// ── runtime_start_sm ────────────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverRuntimeActions::HandleRuntimeStartSM(const TSharedPtr<FJsonObject>& Params)
{
	FPIELookupResult Lookup = FindSMInstanceInPIE(Params);

	// For start, the SM instance might not exist yet — try calling on the component
	if (!Lookup.bSuccess && Lookup.Component)
	{
		// Start via component
		bool bCalledInit = CallFunction(Lookup.Component, TEXT("Initialize"));
		bool bCalledStart = CallFunction(Lookup.Component, TEXT("Start"));

		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
		Result->SetStringField(TEXT("component"), Lookup.Component->GetName());
		Result->SetBoolField(TEXT("initialized"), bCalledInit);
		Result->SetBoolField(TEXT("started"), bCalledStart);
		Result->SetStringField(TEXT("message"), TEXT("Started SM via component"));
		return FMonolithActionResult::Success(Result);
	}
	if (!Lookup.bSuccess) return Lookup.Error;

	bool bCalledInit = CallFunction(Lookup.SMInstance, TEXT("Initialize"));
	bool bCalledStart = CallFunction(Lookup.SMInstance, TEXT("Start"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
	Result->SetStringField(TEXT("component"), Lookup.Component->GetName());
	Result->SetBoolField(TEXT("initialized"), bCalledInit);
	Result->SetBoolField(TEXT("started"), bCalledStart);
	Result->SetStringField(TEXT("message"), TEXT("Started SM instance"));

	return FMonolithActionResult::Success(Result);
}

// ── runtime_stop_sm ─────────────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverRuntimeActions::HandleRuntimeStopSM(const TSharedPtr<FJsonObject>& Params)
{
	FPIELookupResult Lookup = FindSMInstanceInPIE(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	bool bCalled = CallFunction(Lookup.SMInstance, TEXT("Stop"));
	if (!bCalled)
	{
		// Try on component
		bCalled = CallFunction(Lookup.Component, TEXT("Stop"));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
	Result->SetStringField(TEXT("component"), Lookup.Component->GetName());
	Result->SetBoolField(TEXT("stopped"), bCalled);

	return FMonolithActionResult::Success(Result);
}

// ── runtime_restart_sm ──────────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverRuntimeActions::HandleRuntimeRestartSM(const TSharedPtr<FJsonObject>& Params)
{
	FPIELookupResult Lookup = FindSMInstanceInPIE(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	// Try Restart first, then fall back to Stop+Initialize+Start
	bool bRestarted = CallFunction(Lookup.SMInstance, TEXT("Restart"));
	if (!bRestarted)
	{
		CallFunction(Lookup.SMInstance, TEXT("Stop"));
		CallFunction(Lookup.SMInstance, TEXT("Initialize"));
		CallFunction(Lookup.SMInstance, TEXT("Start"));
		bRestarted = true;
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
	Result->SetStringField(TEXT("component"), Lookup.Component->GetName());
	Result->SetBoolField(TEXT("restarted"), bRestarted);

	return FMonolithActionResult::Success(Result);
}

// ── runtime_switch_state ────────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverRuntimeActions::HandleRuntimeSwitchState(const TSharedPtr<FJsonObject>& Params)
{
	FPIELookupResult Lookup = FindSMInstanceInPIE(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	FString StateGuidStr = Params->GetStringField(TEXT("state_guid"));
	if (StateGuidStr.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'state_guid'"));

	FGuid StateGuid;
	if (!FGuid::Parse(StateGuidStr, StateGuid))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Invalid GUID: '%s'"), *StateGuidStr));
	}

	// Try SwitchActiveState(FGuid) or SwitchActiveStateByQualifiedName
	UFunction* SwitchFunc = Lookup.SMInstance->FindFunction(TEXT("SwitchActiveState"));
	bool bSwitched = false;
	if (SwitchFunc)
	{
		struct { FGuid StateGuid; } FuncParams;
		FuncParams.StateGuid = StateGuid;
		Lookup.SMInstance->ProcessEvent(SwitchFunc, &FuncParams);
		bSwitched = true;
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
	Result->SetStringField(TEXT("state_guid"), StateGuidStr);
	Result->SetBoolField(TEXT("switched"), bSwitched);
	if (!bSwitched)
	{
		Result->SetStringField(TEXT("warning"), TEXT("SwitchActiveState function not found on SM instance"));
	}

	return FMonolithActionResult::Success(Result);
}

// ── runtime_evaluate_transitions ────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverRuntimeActions::HandleRuntimeEvaluateTransitions(const TSharedPtr<FJsonObject>& Params)
{
	FPIELookupResult Lookup = FindSMInstanceInPIE(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	bool bCalled = CallFunction(Lookup.SMInstance, TEXT("EvaluateTransitions"));
	if (!bCalled)
	{
		// Try alternative name
		bCalled = CallFunction(Lookup.SMInstance, TEXT("EvalTransitions"));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
	Result->SetStringField(TEXT("component"), Lookup.Component->GetName());
	Result->SetBoolField(TEXT("evaluated"), bCalled);
	if (!bCalled)
	{
		Result->SetStringField(TEXT("warning"), TEXT("EvaluateTransitions function not found on SM instance"));
	}

	return FMonolithActionResult::Success(Result);
}

// ── runtime_get_state_history ───────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverRuntimeActions::HandleRuntimeGetStateHistory(const TSharedPtr<FJsonObject>& Params)
{
	FPIELookupResult Lookup = FindSMInstanceInPIE(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	int32 Limit = 50;
	if (Params->HasField(TEXT("limit")))
	{
		Limit = static_cast<int32>(Params->GetNumberField(TEXT("limit")));
	}

	// Try to call GetStateHistory and read the result
	// The function may return a TArray of structs — fallback to property reading
	TArray<TSharedPtr<FJsonValue>> HistoryArr;

	// Try reading StateHistory array property directly
	FProperty* HistProp = Lookup.SMInstance->GetClass()->FindPropertyByName(TEXT("StateHistory"));
	if (!HistProp)
	{
		HistProp = Lookup.SMInstance->GetClass()->FindPropertyByName(TEXT("PreviousStateHistory"));
	}

	if (FArrayProperty* ArrayProp = CastField<FArrayProperty>(HistProp))
	{
		FScriptArrayHelper ArrayHelper(ArrayProp, ArrayProp->ContainerPtrToValuePtr<void>(Lookup.SMInstance));
		int32 Count = FMath::Min(ArrayHelper.Num(), Limit);
		for (int32 i = 0; i < Count; i++)
		{
			// Each element might be a struct — export as text
			FString ElemText;
			ArrayProp->Inner->ExportTextItem_Direct(ElemText, ArrayHelper.GetRawPtr(i), nullptr, nullptr, PPF_None);
			TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
			Entry->SetNumberField(TEXT("index"), i);
			Entry->SetStringField(TEXT("data"), ElemText);
			HistoryArr.Add(MakeShared<FJsonValueObject>(Entry));
		}
	}

	// Also read general SM status
	bool bIsActive = MonolithLD::GetBoolProperty(Lookup.SMInstance, TEXT("bIsActive"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
	Result->SetStringField(TEXT("component"), Lookup.Component->GetName());
	Result->SetBoolField(TEXT("is_active"), bIsActive);
	Result->SetNumberField(TEXT("history_count"), HistoryArr.Num());
	Result->SetArrayField(TEXT("history"), HistoryArr);

	if (HistoryArr.Num() == 0)
	{
		Result->SetStringField(TEXT("note"), TEXT("No state history found — SM may not track history, or no transitions have occurred"));
	}

	return FMonolithActionResult::Success(Result);
}

#else

void FMonolithLogicDriverRuntimeActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// Logic Driver not available
}

#endif // WITH_LOGICDRIVER
