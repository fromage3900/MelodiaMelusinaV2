#include "MonolithLogicDriverNodeActions.h"
#include "MonolithParamSchema.h"

#if WITH_LOGICDRIVER

#include "MonolithLogicDriverInternal.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "GameplayTagContainer.h"
#include "GameplayTagsManager.h"

DEFINE_LOG_CATEGORY_STATIC(LogMonolithLDNode, Log, All);

// ── Reflection helpers (local) ──────────────────────────────────────

namespace
{

/** Set a bool UPROPERTY on an object via reflection. Returns true if property was found and set. */
bool SetBoolProp(UObject* Obj, FName PropName, bool Value)
{
	if (!Obj) return false;
	FBoolProperty* Prop = CastField<FBoolProperty>(Obj->GetClass()->FindPropertyByName(PropName));
	if (!Prop) return false;
	Obj->Modify();
	Prop->SetPropertyValue(Prop->ContainerPtrToValuePtr<void>(Obj), Value);
	return true;
}

/** Set an int32 UPROPERTY on an object via reflection. */
bool SetIntProp(UObject* Obj, FName PropName, int32 Value)
{
	if (!Obj) return false;
	FIntProperty* Prop = CastField<FIntProperty>(Obj->GetClass()->FindPropertyByName(PropName));
	if (!Prop) return false;
	Obj->Modify();
	Prop->SetPropertyValue(Prop->ContainerPtrToValuePtr<void>(Obj), Value);
	return true;
}

/** Set a float UPROPERTY on an object via reflection (handles both float and double backing). */
bool SetFloatProp(UObject* Obj, FName PropName, float Value)
{
	if (!Obj) return false;
	FProperty* Prop = Obj->GetClass()->FindPropertyByName(PropName);
	if (!Prop) return false;
	Obj->Modify();
	if (FFloatProperty* FP = CastField<FFloatProperty>(Prop))
	{
		FP->SetPropertyValue(FP->ContainerPtrToValuePtr<void>(Obj), Value);
		return true;
	}
	if (FDoubleProperty* DP = CastField<FDoubleProperty>(Prop))
	{
		DP->SetPropertyValue(DP->ContainerPtrToValuePtr<void>(Obj), static_cast<double>(Value));
		return true;
	}
	return false;
}

/** Set a byte/enum UPROPERTY from a string via reflection (uses ImportText). */
bool SetEnumPropFromString(UObject* Obj, FName PropName, const FString& Value)
{
	if (!Obj) return false;
	FProperty* Prop = Obj->GetClass()->FindPropertyByName(PropName);
	if (!Prop) return false;
	Obj->Modify();
	void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Obj);
	return Prop->ImportText_Direct(*Value, ValuePtr, Obj, PPF_None) != nullptr;
}

/** Set a linear color UPROPERTY from "R,G,B,A" string. */
bool SetColorProp(UObject* Obj, FName PropName, const FString& ColorStr)
{
	if (!Obj) return false;
	FStructProperty* Prop = CastField<FStructProperty>(Obj->GetClass()->FindPropertyByName(PropName));
	if (!Prop) return false;

	TArray<FString> Parts;
	ColorStr.ParseIntoArray(Parts, TEXT(","));
	if (Parts.Num() < 3) return false;

	FLinearColor Color;
	Color.R = FCString::Atof(*Parts[0]);
	Color.G = FCString::Atof(*Parts[1]);
	Color.B = FCString::Atof(*Parts[2]);
	Color.A = Parts.Num() >= 4 ? FCString::Atof(*Parts[3]) : 1.0f;

	// Check if it's FLinearColor
	if (Prop->Struct == TBaseStructure<FLinearColor>::Get())
	{
		Obj->Modify();
		FLinearColor* Dest = Prop->ContainerPtrToValuePtr<FLinearColor>(Obj);
		*Dest = Color;
		return true;
	}
	return false;
}

/** Load blueprint, get root graph, find node — common boilerplate. Returns error result if anything fails. */
struct FNodeLookupResult
{
	UBlueprint* Blueprint = nullptr;
	UEdGraph* Graph = nullptr;
	UEdGraphNode* Node = nullptr;
	FMonolithActionResult Error;
	bool bSuccess = false;
};

FNodeLookupResult LoadAndFindNode(const TSharedPtr<FJsonObject>& Params)
{
	FNodeLookupResult Result;

	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty())
	{
		Result.Error = FMonolithActionResult::Error(TEXT("Missing required param 'asset_path'"));
		return Result;
	}

	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));
	if (NodeGuid.IsEmpty())
	{
		// Also check transition_guid for set_transition_condition
		NodeGuid = Params->GetStringField(TEXT("transition_guid"));
	}
	if (NodeGuid.IsEmpty())
	{
		Result.Error = FMonolithActionResult::Error(TEXT("Missing required param 'node_guid' (or 'transition_guid')"));
		return Result;
	}

	FString LoadError;
	Result.Blueprint = MonolithLD::LoadSMBlueprint(AssetPath, LoadError);
	if (!Result.Blueprint)
	{
		Result.Error = FMonolithActionResult::Error(LoadError);
		return Result;
	}

	Result.Graph = MonolithLD::GetRootGraph(Result.Blueprint);
	if (!Result.Graph)
	{
		Result.Error = FMonolithActionResult::Error(TEXT("No root SM graph found"));
		return Result;
	}

	Result.Node = MonolithLD::FindNodeByGuid(Result.Graph, NodeGuid);
	if (!Result.Node)
	{
		Result.Error = FMonolithActionResult::Error(FString::Printf(TEXT("Node with GUID '%s' not found"), *NodeGuid));
		return Result;
	}

	Result.bSuccess = true;
	return Result;
}

} // anonymous namespace

// ── Registration ────────────────────────────────────────────────────

void FMonolithLogicDriverNodeActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ── configure_state (29) ──
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("configure_state"),
		TEXT("Set state node configuration flags (always_update, disable_tick_transition, exclude_from_any_state) via reflection"),
		FMonolithActionHandler::CreateStatic(&HandleConfigureState),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("State node GUID"))
			.Optional(TEXT("always_update"), TEXT("boolean"), TEXT("Force state to update every tick"), TEXT(""))
			.Optional(TEXT("disable_tick_transition"), TEXT("boolean"), TEXT("Disable tick-based transition evaluation"), TEXT(""))
			.Optional(TEXT("exclude_from_any_state"), TEXT("boolean"), TEXT("Exclude this state from AnyState transitions"), TEXT(""))
			.Build());

	// ── configure_transition (30) ──
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("configure_transition"),
		TEXT("Set transition properties (priority, color, eval_mode, can_eval_with_start_state) via reflection"),
		FMonolithActionHandler::CreateStatic(&HandleConfigureTransition),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Transition node GUID"))
			.Optional(TEXT("priority"), TEXT("number"), TEXT("Transition priority order (lower = higher priority)"), TEXT(""))
			.Optional(TEXT("color"), TEXT("string"), TEXT("Transition color as 'R,G,B,A' (0-1 floats)"), TEXT(""))
			.Optional(TEXT("eval_mode"), TEXT("string"), TEXT("Evaluation mode string (imported via reflection)"), TEXT(""))
			.Optional(TEXT("can_eval_with_start_state"), TEXT("boolean"), TEXT("Allow evaluation when source state is the start state"), TEXT(""))
			.Build());

	// ── configure_conduit (31) ──
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("configure_conduit"),
		TEXT("Set conduit properties (eval_with_transitions, conduit_as_state) via reflection"),
		FMonolithActionHandler::CreateStatic(&HandleConfigureConduit),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Conduit node GUID"))
			.Optional(TEXT("eval_with_transitions"), TEXT("boolean"), TEXT("Evaluate conduit with transitions"), TEXT(""))
			.Optional(TEXT("conduit_as_state"), TEXT("boolean"), TEXT("Treat conduit as a state"), TEXT(""))
			.Build());

	// ── set_transition_condition (32) ──
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("set_transition_condition"),
		TEXT("Set transition condition type: always_true, time_delay, event_based, or tag_check. Sets properties via reflection (no graph rewiring)."),
		FMonolithActionHandler::CreateStatic(&HandleSetTransitionCondition),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("transition_guid"), TEXT("string"), TEXT("Transition node GUID"))
			.Required(TEXT("condition_type"), TEXT("string"), TEXT("Condition type: always_true, time_delay, event_based, tag_check"))
			.Optional(TEXT("params"), TEXT("object"), TEXT("Condition-specific params: {duration}, {event_name}, {tag, match_type}"), TEXT(""))
			.Build());

	// ── set_state_tags (36) ──
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("set_state_tags"),
		TEXT("Set gameplay tags on a state node. Clears existing tags and applies the provided array."),
		FMonolithActionHandler::CreateStatic(&HandleSetStateTags),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("State node GUID"))
			.Required(TEXT("gameplay_tags"), TEXT("array"), TEXT("Array of gameplay tag strings (e.g. ['State.Combat.Attacking'])"))
			.Build());

	// ── get_exposed_properties (Phase 3) ──
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("get_exposed_properties"),
		TEXT("Read all exposed graph properties on SM nodes — FSMGraphProperty variables visible in the graph editor"),
		FMonolithActionHandler::CreateStatic(&HandleGetExposedProperties),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Optional(TEXT("node_guid"), TEXT("string"), TEXT("Specific node GUID; if omitted, reads all nodes"))
			.Build());

	// ── set_exposed_property (Phase 3) ──
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("set_exposed_property"),
		TEXT("Set an exposed property value on an SM node by name via reflection"),
		FMonolithActionHandler::CreateStatic(&HandleSetExposedProperty),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Node GUID"))
			.Required(TEXT("property_name"), TEXT("string"), TEXT("Property name to set"))
			.Required(TEXT("value"), TEXT("string"), TEXT("New value (imported via reflection)"))
			.Build());

	// ── configure_state_machine_node (Phase 3) ──
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("configure_state_machine_node"),
		TEXT("Configure a nested state machine node: reuse behavior, independent tick, and other settings"),
		FMonolithActionHandler::CreateStatic(&HandleConfigureStateMachineNode),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("SM Blueprint asset path"))
			.Required(TEXT("node_guid"), TEXT("string"), TEXT("Nested SM node GUID"))
			.Optional(TEXT("reuse_if_not_end_state"), TEXT("boolean"), TEXT("Reuse the SM if it hasn't reached an end state"))
			.Optional(TEXT("reuse_current_state"), TEXT("boolean"), TEXT("Reuse current state on re-entry"))
			.Optional(TEXT("allow_independent_tick"), TEXT("boolean"), TEXT("Allow this nested SM to tick independently"))
			.Build());

	UE_LOG(LogMonolithLDNode, Log, TEXT("MonolithLogicDriver Node: registered 8 actions"));
}

// ── configure_state (29) ────────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverNodeActions::HandleConfigureState(const TSharedPtr<FJsonObject>& Params)
{
	FNodeLookupResult Lookup = LoadAndFindNode(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	UEdGraphNode* Node = Lookup.Node;

	// Verify it's a state node
	FString NodeType = MonolithLD::GetNodeType(Node);
	if (NodeType != TEXT("state") && NodeType != TEXT("any_state"))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node is type '%s', expected 'state' or 'any_state'"), *NodeType));
	}

	TArray<FString> Applied;

	if (Params->HasField(TEXT("always_update")))
	{
		bool bVal = Params->GetBoolField(TEXT("always_update"));
		if (SetBoolProp(Node, TEXT("bAlwaysUpdate"), bVal))
			Applied.Add(FString::Printf(TEXT("bAlwaysUpdate=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("Property 'bAlwaysUpdate' not found on %s"), *Node->GetClass()->GetName());
	}

	if (Params->HasField(TEXT("disable_tick_transition")))
	{
		bool bVal = Params->GetBoolField(TEXT("disable_tick_transition"));
		if (SetBoolProp(Node, TEXT("bDisableTickTransitionEvaluation"), bVal))
			Applied.Add(FString::Printf(TEXT("bDisableTickTransitionEvaluation=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("Property 'bDisableTickTransitionEvaluation' not found on %s"), *Node->GetClass()->GetName());
	}

	if (Params->HasField(TEXT("exclude_from_any_state")))
	{
		bool bVal = Params->GetBoolField(TEXT("exclude_from_any_state"));
		if (SetBoolProp(Node, TEXT("bExcludeFromAnyState"), bVal))
			Applied.Add(FString::Printf(TEXT("bExcludeFromAnyState=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("Property 'bExcludeFromAnyState' not found on %s"), *Node->GetClass()->GetName());
	}

	if (Applied.Num() == 0)
	{
		{ TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>(); R->SetStringField(TEXT("message"), TEXT("No properties were set (none provided or none matched)")); return FMonolithActionResult::Success(R); }
	}

	// Mark blueprint modified
	Lookup.Blueprint->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
	Result->SetStringField(TEXT("node_type"), NodeType);

	TArray<TSharedPtr<FJsonValue>> AppliedArr;
	for (const FString& S : Applied)
		AppliedArr.Add(MakeShared<FJsonValueString>(S));
	Result->SetArrayField(TEXT("properties_set"), AppliedArr);

	return FMonolithActionResult::Success(Result);
}

// ── configure_transition (30) ───────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverNodeActions::HandleConfigureTransition(const TSharedPtr<FJsonObject>& Params)
{
	FNodeLookupResult Lookup = LoadAndFindNode(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	UEdGraphNode* Node = Lookup.Node;

	FString NodeType = MonolithLD::GetNodeType(Node);
	if (NodeType != TEXT("transition"))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node is type '%s', expected 'transition'"), *NodeType));
	}

	TArray<FString> Applied;

	if (Params->HasField(TEXT("priority")))
	{
		int32 Val = static_cast<int32>(Params->GetNumberField(TEXT("priority")));
		if (SetIntProp(Node, TEXT("PriorityOrder"), Val))
			Applied.Add(FString::Printf(TEXT("PriorityOrder=%d"), Val));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("Property 'PriorityOrder' not found on %s"), *Node->GetClass()->GetName());
	}

	if (Params->HasField(TEXT("color")))
	{
		FString ColorStr = Params->GetStringField(TEXT("color"));
		// Try NodeTintColor and TransitionColor as potential property names
		if (SetColorProp(Node, TEXT("NodeTintColor"), ColorStr))
			Applied.Add(FString::Printf(TEXT("NodeTintColor=%s"), *ColorStr));
		else if (SetColorProp(Node, TEXT("TransitionColor"), ColorStr))
			Applied.Add(FString::Printf(TEXT("TransitionColor=%s"), *ColorStr));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("No color property found on %s"), *Node->GetClass()->GetName());
	}

	if (Params->HasField(TEXT("eval_mode")))
	{
		FString ModeStr = Params->GetStringField(TEXT("eval_mode"));
		// Try common LD property names for evaluation mode
		if (SetEnumPropFromString(Node, TEXT("ConditionalEvaluationType"), ModeStr))
			Applied.Add(FString::Printf(TEXT("ConditionalEvaluationType=%s"), *ModeStr));
		else if (SetEnumPropFromString(Node, TEXT("EvalMode"), ModeStr))
			Applied.Add(FString::Printf(TEXT("EvalMode=%s"), *ModeStr));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("No eval mode property found on %s"), *Node->GetClass()->GetName());
	}

	if (Params->HasField(TEXT("can_eval_with_start_state")))
	{
		bool bVal = Params->GetBoolField(TEXT("can_eval_with_start_state"));
		if (SetBoolProp(Node, TEXT("bCanEvaluateWithStartState"), bVal))
			Applied.Add(FString::Printf(TEXT("bCanEvaluateWithStartState=%s"), bVal ? TEXT("true") : TEXT("false")));
		else if (SetBoolProp(Node, TEXT("bCanEvalWithStartState"), bVal))
			Applied.Add(FString::Printf(TEXT("bCanEvalWithStartState=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("No can_eval_with_start_state property found on %s"), *Node->GetClass()->GetName());
	}

	if (Applied.Num() == 0)
	{
		{ TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>(); R->SetStringField(TEXT("message"), TEXT("No properties were set (none provided or none matched)")); return FMonolithActionResult::Success(R); }
	}

	Lookup.Blueprint->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
	Result->SetStringField(TEXT("node_type"), NodeType);

	TArray<TSharedPtr<FJsonValue>> AppliedArr;
	for (const FString& S : Applied)
		AppliedArr.Add(MakeShared<FJsonValueString>(S));
	Result->SetArrayField(TEXT("properties_set"), AppliedArr);

	return FMonolithActionResult::Success(Result);
}

// ── configure_conduit (31) ──────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverNodeActions::HandleConfigureConduit(const TSharedPtr<FJsonObject>& Params)
{
	FNodeLookupResult Lookup = LoadAndFindNode(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	UEdGraphNode* Node = Lookup.Node;

	FString NodeType = MonolithLD::GetNodeType(Node);
	if (NodeType != TEXT("conduit"))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node is type '%s', expected 'conduit'"), *NodeType));
	}

	TArray<FString> Applied;

	if (Params->HasField(TEXT("eval_with_transitions")))
	{
		bool bVal = Params->GetBoolField(TEXT("eval_with_transitions"));
		if (SetBoolProp(Node, TEXT("bEvalWithTransitions"), bVal))
			Applied.Add(FString::Printf(TEXT("bEvalWithTransitions=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("Property 'bEvalWithTransitions' not found on %s"), *Node->GetClass()->GetName());
	}

	if (Params->HasField(TEXT("conduit_as_state")))
	{
		// LD Pro sometimes exposes this as bUseConduitAsState or similar
		bool bVal = Params->GetBoolField(TEXT("conduit_as_state"));
		if (SetBoolProp(Node, TEXT("bConduitAsState"), bVal))
			Applied.Add(FString::Printf(TEXT("bConduitAsState=%s"), bVal ? TEXT("true") : TEXT("false")));
		else if (SetBoolProp(Node, TEXT("bUseConduitAsState"), bVal))
			Applied.Add(FString::Printf(TEXT("bUseConduitAsState=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("No conduit_as_state property found on %s"), *Node->GetClass()->GetName());
	}

	if (Applied.Num() == 0)
	{
		{ TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>(); R->SetStringField(TEXT("message"), TEXT("No properties were set (none provided or none matched)")); return FMonolithActionResult::Success(R); }
	}

	Lookup.Blueprint->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
	Result->SetStringField(TEXT("node_type"), NodeType);

	TArray<TSharedPtr<FJsonValue>> AppliedArr;
	for (const FString& S : Applied)
		AppliedArr.Add(MakeShared<FJsonValueString>(S));
	Result->SetArrayField(TEXT("properties_set"), AppliedArr);

	return FMonolithActionResult::Success(Result);
}

// ── set_transition_condition (32) ───────────────────────────────────

FMonolithActionResult FMonolithLogicDriverNodeActions::HandleSetTransitionCondition(const TSharedPtr<FJsonObject>& Params)
{
	FNodeLookupResult Lookup = LoadAndFindNode(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	UEdGraphNode* Node = Lookup.Node;

	FString NodeType = MonolithLD::GetNodeType(Node);
	if (NodeType != TEXT("transition"))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node is type '%s', expected 'transition'"), *NodeType));
	}

	FString ConditionType = Params->GetStringField(TEXT("condition_type"));
	if (ConditionType.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'condition_type'"));
	}

	// Get optional condition params
	const TSharedPtr<FJsonObject>* CondParamsPtr = nullptr;
	TSharedPtr<FJsonObject> CondParams;
	if (Params->HasTypedField<EJson::Object>(TEXT("params")))
	{
		Params->TryGetObjectField(TEXT("params"), CondParamsPtr);
		if (CondParamsPtr)
			CondParams = *CondParamsPtr;
	}

	TArray<FString> Applied;

	if (ConditionType == TEXT("always_true"))
	{
		// Set properties that make the transition always evaluate to true / auto-advance
		// bCanEvaluate = true, bAutoForwardIfTrue variants
		if (SetBoolProp(Node, TEXT("bCanEvaluate"), true))
			Applied.Add(TEXT("bCanEvaluate=true"));
		if (SetBoolProp(Node, TEXT("bAutoForwardIfTrue"), true))
			Applied.Add(TEXT("bAutoForwardIfTrue=true"));
		// Some LD versions use bAlwaysTrue directly
		if (SetBoolProp(Node, TEXT("bAlwaysTrue"), true))
			Applied.Add(TEXT("bAlwaysTrue=true"));
	}
	else if (ConditionType == TEXT("time_delay"))
	{
		float Duration = 1.0f;
		if (CondParams && CondParams->HasField(TEXT("duration")))
		{
			Duration = static_cast<float>(CondParams->GetNumberField(TEXT("duration")));
		}

		// Try various property names for transition delay/duration
		if (SetFloatProp(Node, TEXT("TransitionDuration"), Duration))
			Applied.Add(FString::Printf(TEXT("TransitionDuration=%.2f"), Duration));
		else if (SetFloatProp(Node, TEXT("TimeInState"), Duration))
			Applied.Add(FString::Printf(TEXT("TimeInState=%.2f"), Duration));

		// Also try to set the transition to use time-based evaluation
		if (SetBoolProp(Node, TEXT("bUseCustomTransitionTime"), true))
			Applied.Add(TEXT("bUseCustomTransitionTime=true"));
	}
	else if (ConditionType == TEXT("event_based"))
	{
		FString EventName;
		if (CondParams && CondParams->HasField(TEXT("event_name")))
		{
			EventName = CondParams->GetStringField(TEXT("event_name"));
		}

		if (SetBoolProp(Node, TEXT("bCanEvaluateFromEvent"), true))
			Applied.Add(TEXT("bCanEvaluateFromEvent=true"));
		if (SetBoolProp(Node, TEXT("bCanEvalFromEvent"), true))
			Applied.Add(TEXT("bCanEvalFromEvent=true"));

		// Try to set the event trigger type or name
		if (!EventName.IsEmpty())
		{
			if (SetEnumPropFromString(Node, TEXT("EventTriggerType"), EventName))
				Applied.Add(FString::Printf(TEXT("EventTriggerType=%s"), *EventName));
		}
	}
	else if (ConditionType == TEXT("tag_check"))
	{
		FString TagString;
		FString MatchType = TEXT("Exact");
		if (CondParams)
		{
			if (CondParams->HasField(TEXT("tag")))
				TagString = CondParams->GetStringField(TEXT("tag"));
			if (CondParams->HasField(TEXT("match_type")))
				MatchType = CondParams->GetStringField(TEXT("match_type"));
		}

		if (TagString.IsEmpty())
		{
			return FMonolithActionResult::Error(TEXT("tag_check requires 'tag' in params"));
		}

		// Try to find a GameplayTag container on the transition
		FStructProperty* TagsProp = CastField<FStructProperty>(Node->GetClass()->FindPropertyByName(TEXT("TransitionTags")));
		if (!TagsProp)
			TagsProp = CastField<FStructProperty>(Node->GetClass()->FindPropertyByName(TEXT("GameplayTags")));

		if (TagsProp && TagsProp->Struct == FGameplayTagContainer::StaticStruct())
		{
			Node->Modify();
			FGameplayTagContainer* Container = TagsProp->ContainerPtrToValuePtr<FGameplayTagContainer>(Node);
			Container->Reset();

			FGameplayTag Tag = FGameplayTag::RequestGameplayTag(FName(*TagString), false);
			if (Tag.IsValid())
			{
				Container->AddTag(Tag);
				Applied.Add(FString::Printf(TEXT("%s={%s}"), *TagsProp->GetName(), *TagString));
			}
			else
			{
				UE_LOG(LogMonolithLDNode, Warning, TEXT("Gameplay tag '%s' is not registered"), *TagString);
				Applied.Add(FString::Printf(TEXT("%s={%s} (tag not registered, added anyway)"), *TagsProp->GetName(), *TagString));
				// Still add as raw tag — it may become valid after project load
				Container->AddTag(FGameplayTag::RequestGameplayTag(FName(*TagString), false));
			}
		}
		else
		{
			UE_LOG(LogMonolithLDNode, Warning, TEXT("No GameplayTagContainer property found on transition %s"), *Node->GetClass()->GetName());
		}

		// Try to set match type
		if (!MatchType.IsEmpty())
		{
			if (SetEnumPropFromString(Node, TEXT("TagMatchType"), MatchType))
				Applied.Add(FString::Printf(TEXT("TagMatchType=%s"), *MatchType));
		}
	}
	else
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown condition_type '%s'. Expected: always_true, time_delay, event_based, tag_check"), *ConditionType));
	}

	if (Applied.Num() == 0)
	{
		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("message"), FString::Printf(
			TEXT("condition_type '%s' accepted but no matching properties found on node class %s. "
			     "Complex conditions may require graph-level Blueprint rewiring (out of scope for v1)."),
			*ConditionType, *Node->GetClass()->GetName()));
		return FMonolithActionResult::Success(R);
	}

	Lookup.Blueprint->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
	Result->SetStringField(TEXT("condition_type"), ConditionType);

	TArray<TSharedPtr<FJsonValue>> AppliedArr;
	for (const FString& S : Applied)
		AppliedArr.Add(MakeShared<FJsonValueString>(S));
	Result->SetArrayField(TEXT("properties_set"), AppliedArr);

	return FMonolithActionResult::Success(Result);
}

// ── Phase 3 stubs ───────────────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverNodeActions::HandleGetExposedProperties(const TSharedPtr<FJsonObject>& Params)
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

	// Lambda to extract exposed properties from a node
	auto ExtractExposedProps = [](UEdGraphNode* Node) -> TSharedPtr<FJsonObject>
	{
		TSharedPtr<FJsonObject> NodeResult = MakeShared<FJsonObject>();
		NodeResult->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
		NodeResult->SetStringField(TEXT("node_type"), MonolithLD::GetNodeType(Node));
		NodeResult->SetStringField(TEXT("node_name"), Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString());

		TArray<TSharedPtr<FJsonValue>> PropsArr;
		UClass* NodeClass = Node->GetClass();

		for (TFieldIterator<FProperty> PropIt(NodeClass, EFieldIteratorFlags::IncludeSuper); PropIt; ++PropIt)
		{
			FProperty* Prop = *PropIt;
			if (!Prop) continue;

			// Check if it's an exposed graph property — look for FSMGraphProperty or similar struct
			// Also include any EditAnywhere/BlueprintVisible property that's SM-specific
			FString PropClassName = Prop->GetOwnerClass() ? Prop->GetOwnerClass()->GetName() : TEXT("");

			// Skip base UEdGraphNode properties
			if (Prop->GetOwnerClass() == UEdGraphNode::StaticClass()) continue;
			if (!Prop->HasAnyPropertyFlags(CPF_Edit | CPF_BlueprintVisible)) continue;

			// Check if this is an FSMGraphProperty struct or a directly exposed variable
			bool bIsSMProperty = PropClassName.Contains(TEXT("SMGraph"))
				|| PropClassName.Contains(TEXT("SMState"))
				|| PropClassName.Contains(TEXT("SMNode"));
			if (!bIsSMProperty) continue;

			TSharedPtr<FJsonObject> PropObj = MakeShared<FJsonObject>();
			PropObj->SetStringField(TEXT("name"), Prop->GetName());
			PropObj->SetStringField(TEXT("type"), Prop->GetCPPType());
			PropObj->SetStringField(TEXT("owner_class"), PropClassName);

			// Read current value
			FString ValueText;
			const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Node);
			Prop->ExportTextItem_Direct(ValueText, ValuePtr, nullptr, nullptr, PPF_None);
			PropObj->SetStringField(TEXT("value"), ValueText);

			// Metadata
			if (Prop->HasMetaData(TEXT("DisplayName")))
			{
				PropObj->SetStringField(TEXT("display_name"), Prop->GetMetaData(TEXT("DisplayName")));
			}

			PropsArr.Add(MakeShared<FJsonValueObject>(PropObj));
		}

		NodeResult->SetNumberField(TEXT("property_count"), PropsArr.Num());
		NodeResult->SetArrayField(TEXT("properties"), PropsArr);
		return NodeResult;
	};

	TArray<TSharedPtr<FJsonValue>> NodesArr;

	if (!TargetGuid.IsEmpty())
	{
		// Single node
		UEdGraphNode* Node = MonolithLD::FindNodeByGuid(RootGraph, TargetGuid);
		if (!Node) return FMonolithActionResult::Error(FString::Printf(TEXT("Node '%s' not found"), *TargetGuid));
		NodesArr.Add(MakeShared<FJsonValueObject>(ExtractExposedProps(Node)));
	}
	else
	{
		// All nodes
		for (UEdGraphNode* Node : RootGraph->Nodes)
		{
			if (!Node) continue;
			FString NodeType = MonolithLD::GetNodeType(Node);
			if (NodeType == TEXT("entry") || NodeType == TEXT("transition")) continue;
			NodesArr.Add(MakeShared<FJsonValueObject>(ExtractExposedProps(Node)));
		}
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetNumberField(TEXT("node_count"), NodesArr.Num());
	Result->SetArrayField(TEXT("nodes"), NodesArr);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverNodeActions::HandleSetExposedProperty(const TSharedPtr<FJsonObject>& Params)
{
	FNodeLookupResult Lookup = LoadAndFindNode(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	FString PropertyName = Params->GetStringField(TEXT("property_name"));
	if (PropertyName.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required param 'property_name'"));

	FString Value = Params->GetStringField(TEXT("value"));

	UEdGraphNode* Node = Lookup.Node;

	// Find the property
	FProperty* Prop = Node->GetClass()->FindPropertyByName(FName(*PropertyName));
	if (!Prop)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Property '%s' not found on node class '%s'"),
			*PropertyName, *Node->GetClass()->GetName()));
	}

	// Read old value for comparison
	FString OldValue;
	void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Node);
	Prop->ExportTextItem_Direct(OldValue, ValuePtr, nullptr, nullptr, PPF_None);

	// Set the new value via ImportText
	Node->Modify();
	const TCHAR* ImportResult = Prop->ImportText_Direct(*Value, ValuePtr, Node, PPF_None);
	if (!ImportResult)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to set property '%s' to '%s' (ImportText failed)"),
			*PropertyName, *Value));
	}

	Lookup.Blueprint->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
	Result->SetStringField(TEXT("property_name"), PropertyName);
	Result->SetStringField(TEXT("old_value"), OldValue);
	Result->SetStringField(TEXT("new_value"), Value);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverNodeActions::HandleConfigureStateMachineNode(const TSharedPtr<FJsonObject>& Params)
{
	FNodeLookupResult Lookup = LoadAndFindNode(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	UEdGraphNode* Node = Lookup.Node;
	FString NodeType = MonolithLD::GetNodeType(Node);
	if (NodeType != TEXT("state_machine"))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node is type '%s', expected 'state_machine'"), *NodeType));
	}

	TArray<FString> Applied;

	if (Params->HasField(TEXT("reuse_if_not_end_state")))
	{
		bool bVal = Params->GetBoolField(TEXT("reuse_if_not_end_state"));
		if (SetBoolProp(Node, TEXT("bReuseIfNotEndState"), bVal))
			Applied.Add(FString::Printf(TEXT("bReuseIfNotEndState=%s"), bVal ? TEXT("true") : TEXT("false")));
		else if (SetBoolProp(Node, TEXT("bReuseReference"), bVal))
			Applied.Add(FString::Printf(TEXT("bReuseReference=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("No reuse_if_not_end_state property found on %s"), *Node->GetClass()->GetName());
	}

	if (Params->HasField(TEXT("reuse_current_state")))
	{
		bool bVal = Params->GetBoolField(TEXT("reuse_current_state"));
		if (SetBoolProp(Node, TEXT("bReuseCurrentState"), bVal))
			Applied.Add(FString::Printf(TEXT("bReuseCurrentState=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("Property 'bReuseCurrentState' not found on %s"), *Node->GetClass()->GetName());
	}

	if (Params->HasField(TEXT("allow_independent_tick")))
	{
		bool bVal = Params->GetBoolField(TEXT("allow_independent_tick"));
		if (SetBoolProp(Node, TEXT("bAllowIndependentTick"), bVal))
			Applied.Add(FString::Printf(TEXT("bAllowIndependentTick=%s"), bVal ? TEXT("true") : TEXT("false")));
		else
			UE_LOG(LogMonolithLDNode, Warning, TEXT("Property 'bAllowIndependentTick' not found on %s"), *Node->GetClass()->GetName());
	}

	if (Applied.Num() == 0)
	{
		{ TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>(); R->SetStringField(TEXT("message"), TEXT("No properties were set (none provided or none matched)")); return FMonolithActionResult::Success(R); }
	}

	Lookup.Blueprint->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
	Result->SetStringField(TEXT("node_type"), NodeType);

	TArray<TSharedPtr<FJsonValue>> AppliedArr;
	for (const FString& S : Applied)
		AppliedArr.Add(MakeShared<FJsonValueString>(S));
	Result->SetArrayField(TEXT("properties_set"), AppliedArr);

	return FMonolithActionResult::Success(Result);
}

// ── set_state_tags (36) ─────────────────────────────────────────────

FMonolithActionResult FMonolithLogicDriverNodeActions::HandleSetStateTags(const TSharedPtr<FJsonObject>& Params)
{
	FNodeLookupResult Lookup = LoadAndFindNode(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	UEdGraphNode* Node = Lookup.Node;

	FString NodeType = MonolithLD::GetNodeType(Node);
	if (NodeType != TEXT("state") && NodeType != TEXT("any_state") && NodeType != TEXT("state_machine"))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Node is type '%s', expected a state-like node"), *NodeType));
	}

	if (!Params->HasField(TEXT("gameplay_tags")))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'gameplay_tags'"));
	}

	const TArray<TSharedPtr<FJsonValue>>& TagArray = Params->GetArrayField(TEXT("gameplay_tags"));

	// Find a GameplayTagContainer property — try common names
	FStructProperty* TagsProp = nullptr;
	static const FName TagPropNames[] = {
		TEXT("GameplayTags"),
		TEXT("NodeTags"),
		TEXT("StateTags"),
		TEXT("Tags")
	};
	for (const FName& PropName : TagPropNames)
	{
		FStructProperty* Candidate = CastField<FStructProperty>(Node->GetClass()->FindPropertyByName(PropName));
		if (Candidate && Candidate->Struct == FGameplayTagContainer::StaticStruct())
		{
			TagsProp = Candidate;
			break;
		}
	}

	if (!TagsProp)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("No FGameplayTagContainer property found on node class '%s'. "
			     "Searched: GameplayTags, NodeTags, StateTags, Tags"),
			*Node->GetClass()->GetName()));
	}

	Node->Modify();
	FGameplayTagContainer* Container = TagsProp->ContainerPtrToValuePtr<FGameplayTagContainer>(Node);
	Container->Reset();

	TArray<FString> AddedTags;
	TArray<FString> InvalidTags;

	for (const TSharedPtr<FJsonValue>& TagVal : TagArray)
	{
		FString TagString = TagVal->AsString();
		if (TagString.IsEmpty()) continue;

		FGameplayTag Tag = FGameplayTag::RequestGameplayTag(FName(*TagString), false);
		if (Tag.IsValid())
		{
			Container->AddTag(Tag);
			AddedTags.Add(TagString);
		}
		else
		{
			InvalidTags.Add(TagString);
			UE_LOG(LogMonolithLDNode, Warning, TEXT("Gameplay tag '%s' not registered — skipping"), *TagString);
		}
	}

	Lookup.Blueprint->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
	Result->SetStringField(TEXT("property_name"), TagsProp->GetName());
	Result->SetNumberField(TEXT("tags_set"), AddedTags.Num());

	TArray<TSharedPtr<FJsonValue>> AddedArr;
	for (const FString& S : AddedTags)
		AddedArr.Add(MakeShared<FJsonValueString>(S));
	Result->SetArrayField(TEXT("tags"), AddedArr);

	if (InvalidTags.Num() > 0)
	{
		TArray<TSharedPtr<FJsonValue>> InvalidArr;
		for (const FString& S : InvalidTags)
			InvalidArr.Add(MakeShared<FJsonValueString>(S));
		Result->SetArrayField(TEXT("invalid_tags"), InvalidArr);
	}

	return FMonolithActionResult::Success(Result);
}

#else

void FMonolithLogicDriverNodeActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// Logic Driver not available
}

#endif // WITH_LOGICDRIVER
