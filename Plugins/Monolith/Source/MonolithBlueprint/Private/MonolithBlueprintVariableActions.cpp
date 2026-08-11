#include "MonolithBlueprintVariableActions.h"
#include "MonolithBlueprintInternal.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "EdGraphSchema_K2.h"
#include "Net/UnrealNetwork.h"

// ============================================================
//  Registration
// ============================================================

void FMonolithBlueprintVariableActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("blueprint"), TEXT("add_variable"),
		TEXT("Add a new member variable to a Blueprint. Supports all primitive types, structs, enums, objects, and container types (array:, set:, map:)."),
		FMonolithActionHandler::CreateStatic(&HandleAddVariable),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"),        TEXT("Blueprint asset path"))
			.Required(TEXT("name"),               TEXT("string"),  TEXT("Variable name"))
			.Required(TEXT("type"),               TEXT("string"),  TEXT("Pin type string (e.g. bool, int, float, string, struct:Vector, object:Actor, array:float)"))
			.Optional(TEXT("default_value"),      TEXT("string"),  TEXT("Default value as string"))
			.Optional(TEXT("category"),           TEXT("string"),  TEXT("Category for organization in the Blueprint editor"))
			.Optional(TEXT("instance_editable"),  TEXT("boolean"), TEXT("Whether the variable is editable on instances (default: true)"),  TEXT("true"))
			.Optional(TEXT("blueprint_read_only"),TEXT("boolean"), TEXT("Whether the variable is read-only in Blueprints (default: false)"), TEXT("false"))
			.Optional(TEXT("expose_on_spawn"),    TEXT("boolean"), TEXT("Expose as a spawn parameter (default: false)"), TEXT("false"))
			.Optional(TEXT("replicated"),         TEXT("boolean"), TEXT("Replicate this variable over the network (default: false)"), TEXT("false"))
			.Optional(TEXT("transient"),          TEXT("boolean"), TEXT("Mark as transient — not serialized (default: false)"), TEXT("false"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("remove_variable"),
		TEXT("Remove a member variable from a Blueprint by name."),
		FMonolithActionHandler::CreateStatic(&HandleRemoveVariable),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path"))
			.Required(TEXT("name"),       TEXT("string"), TEXT("Variable name to remove"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("rename_variable"),
		TEXT("Rename a member variable in a Blueprint, updating all references in graphs."),
		FMonolithActionHandler::CreateStatic(&HandleRenameVariable),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path"))
			.Required(TEXT("old_name"),   TEXT("string"), TEXT("Current variable name"))
			.Required(TEXT("new_name"),   TEXT("string"), TEXT("New variable name"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("set_variable_type"),
		TEXT("Change the type of an existing member variable. All graph nodes referencing the variable will be refreshed."),
		FMonolithActionHandler::CreateStatic(&HandleSetVariableType),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path"))
			.Required(TEXT("name"),       TEXT("string"), TEXT("Variable name"))
			.Required(TEXT("type"),       TEXT("string"), TEXT("New pin type string (e.g. bool, float, struct:Vector, array:int)"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("set_variable_defaults"),
		TEXT("Update metadata and flags on an existing Blueprint variable. Only provided fields are changed."),
		FMonolithActionHandler::CreateStatic(&HandleSetVariableDefaults),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"),        TEXT("Blueprint asset path"))
			.Required(TEXT("name"),               TEXT("string"),  TEXT("Variable name"))
			.Optional(TEXT("default_value"),      TEXT("string"),  TEXT("New default value as string"))
			.Optional(TEXT("category"),           TEXT("string"),  TEXT("New category"))
			.Optional(TEXT("instance_editable"),  TEXT("boolean"), TEXT("Whether editable on instances"))
			.Optional(TEXT("blueprint_read_only"),TEXT("boolean"), TEXT("Whether read-only in Blueprints"))
			.Optional(TEXT("expose_on_spawn"),    TEXT("boolean"), TEXT("Expose as spawn parameter"))
			.Optional(TEXT("replicated"),         TEXT("boolean"), TEXT("Replicate over network"))
			.Optional(TEXT("transient"),          TEXT("boolean"), TEXT("Mark as transient (not serialized)"))
			.Optional(TEXT("save_game"),          TEXT("boolean"), TEXT("Include in save game serialization"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("add_local_variable"),
		TEXT("Add a local variable to a Blueprint function graph."),
		FMonolithActionHandler::CreateStatic(&HandleAddLocalVariable),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"),    TEXT("Blueprint asset path"))
			.Required(TEXT("function_name"), TEXT("string"), TEXT("Function graph name"))
			.Required(TEXT("name"),          TEXT("string"), TEXT("Local variable name"))
			.Required(TEXT("type"),          TEXT("string"), TEXT("Pin type string"))
			.Optional(TEXT("default_value"), TEXT("string"), TEXT("Default value as string"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("remove_local_variable"),
		TEXT("Remove a local variable from a Blueprint function graph."),
		FMonolithActionHandler::CreateStatic(&HandleRemoveLocalVariable),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"),    TEXT("Blueprint asset path"))
			.Required(TEXT("function_name"), TEXT("string"), TEXT("Function graph name"))
			.Required(TEXT("name"),          TEXT("string"), TEXT("Local variable name to remove"))
			.Build());

	// ---- Wave 7 ----

	Registry.RegisterAction(TEXT("blueprint"), TEXT("add_replicated_variable"),
		TEXT("Add a replicated member variable to a Blueprint with full network replication settings. "
		     "Optionally creates an OnRep_ notification function. Requires the Blueprint's parent class to support replication."),
		FMonolithActionHandler::CreateStatic(&HandleAddReplicatedVariable),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"),            TEXT("Blueprint asset path"))
			.Required(TEXT("variable_name"),         TEXT("string"),  TEXT("Variable name"))
			.Required(TEXT("type"),                  TEXT("string"),  TEXT("Pin type string (e.g. bool, int, float, object:Actor)"))
			.Optional(TEXT("replication_condition"), TEXT("string"),  TEXT("ELifetimeCondition: None, InitialOnly, OwnerOnly, SkipOwner, SimulatedOnly, AutonomousOnly, SimulatedOrPhysics, InitialOrOwner, Custom (default: None)"), TEXT("None"))
			.Optional(TEXT("create_on_rep"),         TEXT("boolean"), TEXT("Create an OnRep_<VarName> function stub and link it to the variable (default: false)"), TEXT("false"))
			.Optional(TEXT("default_value"),         TEXT("string"),  TEXT("Default value as string"))
			.Optional(TEXT("category"),              TEXT("string"),  TEXT("Category for organization in the Blueprint editor"))
			.Build());
}

// ============================================================
//  Helper: apply optional property flags to a variable entry
// ============================================================

namespace
{
	/**
	 * Walk BP->NewVariables and apply flag changes to the entry whose VarName matches.
	 * Returns true if the variable was found.
	 */
	bool ApplyVariableFlags(
		UBlueprint* BP,
		const FName& VarName,
		const TSharedPtr<FJsonObject>& Params,
		const FString& DefaultValue,
		bool bApplyDefault)
	{
		for (FBPVariableDescription& Var : BP->NewVariables)
		{
			if (Var.VarName != VarName) continue;

			// Default value
			if (bApplyDefault && !DefaultValue.IsEmpty())
			{
				Var.DefaultValue = DefaultValue;
			}

			// instance_editable → toggles CPF_DisableEditOnInstance
			bool bInstanceEditable;
			if (Params->TryGetBoolField(TEXT("instance_editable"), bInstanceEditable))
			{
				if (bInstanceEditable)
					Var.PropertyFlags &= ~CPF_DisableEditOnInstance;
				else
					Var.PropertyFlags |= CPF_DisableEditOnInstance;
			}

			// blueprint_read_only → CPF_BlueprintReadOnly
			bool bBlueprintReadOnly;
			if (Params->TryGetBoolField(TEXT("blueprint_read_only"), bBlueprintReadOnly))
			{
				if (bBlueprintReadOnly)
					Var.PropertyFlags |= CPF_BlueprintReadOnly;
				else
					Var.PropertyFlags &= ~CPF_BlueprintReadOnly;
			}

			// expose_on_spawn → CPF_ExposeOnSpawn
			bool bExposeOnSpawn;
			if (Params->TryGetBoolField(TEXT("expose_on_spawn"), bExposeOnSpawn))
			{
				if (bExposeOnSpawn)
					Var.PropertyFlags |= CPF_ExposeOnSpawn;
				else
					Var.PropertyFlags &= ~CPF_ExposeOnSpawn;
			}

			// replicated → CPF_Net
			bool bReplicated;
			if (Params->TryGetBoolField(TEXT("replicated"), bReplicated))
			{
				if (bReplicated)
					Var.PropertyFlags |= CPF_Net;
				else
					Var.PropertyFlags &= ~CPF_Net;
			}

			// transient → CPF_Transient
			bool bTransient;
			if (Params->TryGetBoolField(TEXT("transient"), bTransient))
			{
				if (bTransient)
					Var.PropertyFlags |= CPF_Transient;
				else
					Var.PropertyFlags &= ~CPF_Transient;
			}

			// save_game → CPF_SaveGame
			bool bSaveGame;
			if (Params->TryGetBoolField(TEXT("save_game"), bSaveGame))
			{
				if (bSaveGame)
					Var.PropertyFlags |= CPF_SaveGame;
				else
					Var.PropertyFlags &= ~CPF_SaveGame;
			}

			return true;
		}
		return false;
	}
} // anonymous namespace

// ============================================================
//  add_variable
// ============================================================

FMonolithActionResult FMonolithBlueprintVariableActions::HandleAddVariable(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString Name = Params->GetStringField(TEXT("name"));
	if (Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: name"));
	}

	FString TypeStr = Params->GetStringField(TEXT("type"));
	if (TypeStr.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: type"));
	}

	// Normalize common aliases so users get sensible errors instead of silent bool fallback.
	// Only normalize bare base types (not container-prefixed ones like "array:vector").
	{
		// Wave 7: Accept soft reference shorthands before other normalization
		// soft_object:ClassName -> softobject:ClassName
		// soft_class:ClassName  -> softclass:ClassName
		if (TypeStr.StartsWith(TEXT("soft_object:"), ESearchCase::IgnoreCase))
		{
			TypeStr = TEXT("softobject:") + TypeStr.Mid(12);
		}
		else if (TypeStr.StartsWith(TEXT("soft_class:"), ESearchCase::IgnoreCase))
		{
			TypeStr = TEXT("softclass:") + TypeStr.Mid(11);
		}

		// Build a mutable working copy of just the base portion for alias checks
		auto NormalizeBaseType = [](const FString& In) -> FString
		{
			if (In.Equals(TEXT("integer"),    ESearchCase::IgnoreCase)) return TEXT("int");
			if (In.Equals(TEXT("boolean"),    ESearchCase::IgnoreCase)) return TEXT("bool");
			if (In.Equals(TEXT("vector"),     ESearchCase::IgnoreCase)) return TEXT("struct:Vector");
			if (In.Equals(TEXT("rotator"),    ESearchCase::IgnoreCase)) return TEXT("struct:Rotator");
			if (In.Equals(TEXT("transform"),  ESearchCase::IgnoreCase)) return TEXT("struct:Transform");
			if (In.Equals(TEXT("color"),      ESearchCase::IgnoreCase)) return TEXT("struct:LinearColor");
			if (In.Equals(TEXT("linearcolor"),ESearchCase::IgnoreCase)) return TEXT("struct:LinearColor");
			return In;
		};

		// Handle container prefixes — only normalize the part after the prefix
		static const TCHAR* Prefixes[] = { TEXT("array:"), TEXT("set:"), TEXT("map:") };
		bool bHandled = false;
		for (const TCHAR* Prefix : Prefixes)
		{
			if (TypeStr.StartsWith(Prefix))
			{
				FString BaseStr = TypeStr.Mid(FCString::Strlen(Prefix));
				FString Normalized = NormalizeBaseType(BaseStr);
				if (Normalized != BaseStr)
				{
					TypeStr = FString(Prefix) + Normalized;
				}
				bHandled = true;
				break;
			}
		}
		if (!bHandled)
		{
			TypeStr = NormalizeBaseType(TypeStr);
		}
	}

	FName VarName(*Name);
	FEdGraphPinType PinType = MonolithBlueprintInternal::ParsePinTypeFromString(TypeStr);

	// If the resolved type is the bool fallback but the caller didn't ask for bool,
	// the type string was unrecognized — return a clear error instead of silently creating a bool.
	{
		// Extract base type (strip container prefix for the check)
		FString BaseForCheck = TypeStr;
		for (const TCHAR* Prefix : { TEXT("array:"), TEXT("set:"), TEXT("map:") })
		{
			if (TypeStr.StartsWith(Prefix))
			{
				BaseForCheck = TypeStr.Mid(FCString::Strlen(Prefix));
				break;
			}
		}
		// Known prefixed types that ParsePinTypeFromString handles correctly
		const bool bKnownPrefixedType =
			BaseForCheck.StartsWith(TEXT("object:")) ||
			BaseForCheck.StartsWith(TEXT("class:"))  ||
			BaseForCheck.StartsWith(TEXT("struct:"))  ||
			BaseForCheck.StartsWith(TEXT("enum:"))   ||
			BaseForCheck.StartsWith(TEXT("softobject:")) ||
			BaseForCheck.StartsWith(TEXT("softclass:"));
		const bool bCallerWantsBool =
			BaseForCheck.Equals(TEXT("bool"), ESearchCase::IgnoreCase);

		if (!bCallerWantsBool && !bKnownPrefixedType &&
			PinType.PinCategory == UEdGraphSchema_K2::PC_Boolean)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Unknown variable type '%s'. Valid types: bool, byte, int, int64, float, double, string, text, name, Vector, Rotator, Transform, LinearColor. "
				     "For structs use struct:<Name>, objects use object:<Class>, enums use enum:<Name>. "
				     "Container types: array:<type>, set:<type>, map:<key>:<value>."),
				*TypeStr));
		}
	}

	FString DefaultValue = Params->GetStringField(TEXT("default_value"));

	// Check for existing variable with same name
	for (const FBPVariableDescription& Existing : BP->NewVariables)
	{
		if (Existing.VarName == VarName)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("A variable named '%s' already exists in this Blueprint"), *Name));
		}
	}

	// Add the variable
	FBlueprintEditorUtils::AddMemberVariable(BP, VarName, PinType, DefaultValue);

	// Apply optional metadata flags
	FString Category = Params->GetStringField(TEXT("category"));
	if (!Category.IsEmpty())
	{
		FBlueprintEditorUtils::SetBlueprintVariableCategory(BP, VarName, nullptr, FText::FromString(Category));
	}

	// instance_editable defaults to true — apply via SetBlueprintOnlyEditableFlag
	bool bInstanceEditable = true;
	Params->TryGetBoolField(TEXT("instance_editable"), bInstanceEditable);
	FBlueprintEditorUtils::SetBlueprintOnlyEditableFlag(BP, VarName, !bInstanceEditable);

	// blueprint_read_only defaults to false
	bool bBlueprintReadOnly = false;
	Params->TryGetBoolField(TEXT("blueprint_read_only"), bBlueprintReadOnly);
	FBlueprintEditorUtils::SetBlueprintPropertyReadOnlyFlag(BP, VarName, bBlueprintReadOnly);

	// Remaining flags via direct FBPVariableDescription modification
	// (expose_on_spawn, replicated, transient — no dedicated BlueprintEditorUtils functions)
	ApplyVariableFlags(BP, VarName, Params, TEXT(""), false);

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("variable"), Name);
	Root->SetStringField(TEXT("type"), TypeStr);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  remove_variable
// ============================================================

FMonolithActionResult FMonolithBlueprintVariableActions::HandleRemoveVariable(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString Name = Params->GetStringField(TEXT("name"));
	if (Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: name"));
	}

	FName VarName(*Name);

	// Verify the variable exists before removing
	bool bFound = false;
	for (const FBPVariableDescription& Var : BP->NewVariables)
	{
		if (Var.VarName == VarName)
		{
			bFound = true;
			break;
		}
	}
	if (!bFound)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Variable not found: %s"), *Name));
	}

	FBlueprintEditorUtils::RemoveMemberVariable(BP, VarName);
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("removed_variable"), Name);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  rename_variable
// ============================================================

FMonolithActionResult FMonolithBlueprintVariableActions::HandleRenameVariable(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString OldName = Params->GetStringField(TEXT("old_name"));
	FString NewName = Params->GetStringField(TEXT("new_name"));

	if (OldName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: old_name"));
	}
	if (NewName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: new_name"));
	}

	FName OldVarName(*OldName);

	// Verify source variable exists
	bool bFound = false;
	for (const FBPVariableDescription& Var : BP->NewVariables)
	{
		if (Var.VarName == OldVarName)
		{
			bFound = true;
			break;
		}
	}
	if (!bFound)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Variable not found: %s"), *OldName));
	}

	FBlueprintEditorUtils::RenameMemberVariable(BP, OldVarName, FName(*NewName));
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("old_name"), OldName);
	Root->SetStringField(TEXT("new_name"), NewName);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  set_variable_type
// ============================================================

FMonolithActionResult FMonolithBlueprintVariableActions::HandleSetVariableType(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString Name = Params->GetStringField(TEXT("name"));
	if (Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: name"));
	}

	FString TypeStr = Params->GetStringField(TEXT("type"));
	if (TypeStr.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: type"));
	}

	FName VarName(*Name);

	// Verify the variable exists
	bool bFound = false;
	for (const FBPVariableDescription& Var : BP->NewVariables)
	{
		if (Var.VarName == VarName)
		{
			bFound = true;
			break;
		}
	}
	if (!bFound)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Variable not found: %s"), *Name));
	}

	FEdGraphPinType NewType = MonolithBlueprintInternal::ParsePinTypeFromString(TypeStr);
	FBlueprintEditorUtils::ChangeMemberVariableType(BP, VarName, NewType);
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("variable"), Name);
	Root->SetStringField(TEXT("new_type"), TypeStr);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  set_variable_defaults
// ============================================================

FMonolithActionResult FMonolithBlueprintVariableActions::HandleSetVariableDefaults(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString Name = Params->GetStringField(TEXT("name"));
	if (Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: name"));
	}

	FName VarName(*Name);

	// Verify the variable exists
	bool bFound = false;
	for (const FBPVariableDescription& Var : BP->NewVariables)
	{
		if (Var.VarName == VarName)
		{
			bFound = true;
			break;
		}
	}
	if (!bFound)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Variable not found: %s"), *Name));
	}

	// Apply category if provided
	FString Category = Params->GetStringField(TEXT("category"));
	if (!Category.IsEmpty())
	{
		FBlueprintEditorUtils::SetBlueprintVariableCategory(BP, VarName, nullptr, FText::FromString(Category));
	}

	// Apply instance_editable if provided
	bool bInstanceEditable;
	if (Params->TryGetBoolField(TEXT("instance_editable"), bInstanceEditable))
	{
		FBlueprintEditorUtils::SetBlueprintOnlyEditableFlag(BP, VarName, !bInstanceEditable);
	}

	// Apply blueprint_read_only if provided
	bool bBlueprintReadOnly;
	if (Params->TryGetBoolField(TEXT("blueprint_read_only"), bBlueprintReadOnly))
	{
		FBlueprintEditorUtils::SetBlueprintPropertyReadOnlyFlag(BP, VarName, bBlueprintReadOnly);
	}

	// Apply default_value and remaining flags via direct FBPVariableDescription modification
	FString DefaultValue = Params->GetStringField(TEXT("default_value"));
	bool bHasDefaultValue = !DefaultValue.IsEmpty();
	ApplyVariableFlags(BP, VarName, Params, DefaultValue, bHasDefaultValue);

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("variable"), Name);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  add_local_variable
// ============================================================

FMonolithActionResult FMonolithBlueprintVariableActions::HandleAddLocalVariable(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString FunctionName = Params->GetStringField(TEXT("function_name"));
	if (FunctionName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: function_name"));
	}

	FString Name = Params->GetStringField(TEXT("name"));
	if (Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: name"));
	}

	FString TypeStr = Params->GetStringField(TEXT("type"));
	if (TypeStr.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: type"));
	}

	UEdGraph* FuncGraph = MonolithBlueprintInternal::FindGraphByName(BP, FunctionName);
	if (!FuncGraph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Function graph not found: %s"), *FunctionName));
	}

	// Verify this graph is actually a function graph
	if (!BP->FunctionGraphs.Contains(FuncGraph))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Graph '%s' is not a function graph — local variables are only supported in functions"), *FunctionName));
	}

	FEdGraphPinType PinType = MonolithBlueprintInternal::ParsePinTypeFromString(TypeStr);
	FString DefaultValue = Params->GetStringField(TEXT("default_value"));

	FBlueprintEditorUtils::AddLocalVariable(BP, FuncGraph, FName(*Name), PinType, DefaultValue);
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("function"), FunctionName);
	Root->SetStringField(TEXT("variable"), Name);
	Root->SetStringField(TEXT("type"), TypeStr);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  remove_local_variable
// ============================================================

FMonolithActionResult FMonolithBlueprintVariableActions::HandleRemoveLocalVariable(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString FunctionName = Params->GetStringField(TEXT("function_name"));
	if (FunctionName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: function_name"));
	}

	FString Name = Params->GetStringField(TEXT("name"));
	if (Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: name"));
	}

	UEdGraph* FuncGraph = MonolithBlueprintInternal::FindGraphByName(BP, FunctionName);
	if (!FuncGraph)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Function graph not found: %s"), *FunctionName));
	}

	// Resolve the UFunction from the skeleton class — required by RemoveLocalVariable
	UFunction* Func = nullptr;
	if (BP->SkeletonGeneratedClass)
	{
		Func = BP->SkeletonGeneratedClass->FindFunctionByName(FName(*FunctionName));
	}
	if (!Func)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Could not resolve UFunction for '%s' — skeleton class may need recompile"), *FunctionName));
	}

	// Verify the local variable exists by checking the FunctionEntry node's LocalVariables directly
	FName LocalVarName(*Name);
	bool bFound = false;
	TArray<UK2Node_FunctionEntry*> EntryNodes;
	FuncGraph->GetNodesOfClass<UK2Node_FunctionEntry>(EntryNodes);
	if (EntryNodes.Num() > 0)
	{
		for (const FBPVariableDescription& LocalVar : EntryNodes[0]->LocalVariables)
		{
			if (LocalVar.VarName == LocalVarName)
			{
				bFound = true;
				break;
			}
		}
	}
	if (!bFound)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Local variable not found: %s in function %s"), *Name, *FunctionName));
	}

	// RemoveLocalVariable takes const UStruct* — UFunction derives from UStruct
	FBlueprintEditorUtils::RemoveLocalVariable(BP, static_cast<const UStruct*>(Func), LocalVarName);
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("function"), FunctionName);
	Root->SetStringField(TEXT("removed_variable"), Name);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  add_replicated_variable  (Wave 7)
// ============================================================

FMonolithActionResult FMonolithBlueprintVariableActions::HandleAddReplicatedVariable(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}

	FString VarNameStr = Params->GetStringField(TEXT("variable_name"));
	if (VarNameStr.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: variable_name"));
	}

	FString TypeStr = Params->GetStringField(TEXT("type"));
	if (TypeStr.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: type"));
	}

	// Normalize type string the same way HandleAddVariable does
	{
		if (TypeStr.StartsWith(TEXT("soft_object:"), ESearchCase::IgnoreCase))
			TypeStr = TEXT("softobject:") + TypeStr.Mid(12);
		else if (TypeStr.StartsWith(TEXT("soft_class:"), ESearchCase::IgnoreCase))
			TypeStr = TEXT("softclass:") + TypeStr.Mid(11);
	}

	FName VarName(*VarNameStr);
	FEdGraphPinType PinType = MonolithBlueprintInternal::ParsePinTypeFromString(TypeStr);

	// Check for name collision
	for (const FBPVariableDescription& Existing : BP->NewVariables)
	{
		if (Existing.VarName == VarName)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("A variable named '%s' already exists in this Blueprint."), *VarNameStr));
		}
	}

	// Parse replication condition string -> ELifetimeCondition
	FString ConditionStr = Params->GetStringField(TEXT("replication_condition"));
	if (ConditionStr.IsEmpty()) ConditionStr = TEXT("None");

	// Accept both "COND_OwnerOnly" and "OwnerOnly" forms
	if (ConditionStr.StartsWith(TEXT("COND_"), ESearchCase::IgnoreCase))
	{
		ConditionStr = ConditionStr.Mid(5);
	}

	ELifetimeCondition LifetimeCondition = COND_None;
	{
		static const TMap<FString, ELifetimeCondition> ConditionMap = {
			{TEXT("None"),               COND_None},
			{TEXT("InitialOnly"),        COND_InitialOnly},
			{TEXT("OwnerOnly"),          COND_OwnerOnly},
			{TEXT("SkipOwner"),          COND_SkipOwner},
			{TEXT("SimulatedOnly"),      COND_SimulatedOnly},
			{TEXT("AutonomousOnly"),     COND_AutonomousOnly},
			{TEXT("SimulatedOrPhysics"), COND_SimulatedOrPhysics},
			{TEXT("InitialOrOwner"),     COND_InitialOrOwner},
			{TEXT("Custom"),             COND_Custom},
		};
		if (const ELifetimeCondition* Found = ConditionMap.Find(ConditionStr))
		{
			LifetimeCondition = *Found;
		}
		else
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Unknown replication_condition '%s'. Valid values: None, InitialOnly, OwnerOnly, SkipOwner, SimulatedOnly, AutonomousOnly, SimulatedOrPhysics, InitialOrOwner, Custom"),
				*ConditionStr));
		}
	}

	bool bCreateOnRep = false;
	Params->TryGetBoolField(TEXT("create_on_rep"), bCreateOnRep);

	FString DefaultValue = Params->GetStringField(TEXT("default_value"));

	// Step 1: Add the variable
	FBlueprintEditorUtils::AddMemberVariable(BP, VarName, PinType, DefaultValue);

	// Step 2: Set replication flags and condition directly on the variable description
	for (FBPVariableDescription& Var : BP->NewVariables)
	{
		if (Var.VarName != VarName) continue;

		// Set the CPF_Net flag to mark this variable as replicated
		Var.PropertyFlags |= CPF_Net;

		// Set the replication condition
		Var.ReplicationCondition = LifetimeCondition;

		break;
	}

	// Apply optional category
	FString Category = Params->GetStringField(TEXT("category"));
	if (!Category.IsEmpty())
	{
		FBlueprintEditorUtils::SetBlueprintVariableCategory(BP, VarName, nullptr, FText::FromString(Category));
	}

	// Step 3: Optionally create OnRep function and link it
	FString OnRepFunctionName;
	if (bCreateOnRep)
	{
		OnRepFunctionName = FString::Printf(TEXT("OnRep_%s"), *VarNameStr);
		FName OnRepFuncName(*OnRepFunctionName);

		// Check the function doesn't already exist
		bool bFuncExists = false;
		for (const UEdGraph* FuncGraph : BP->FunctionGraphs)
		{
			if (FuncGraph && FuncGraph->GetFName() == OnRepFuncName)
			{
				bFuncExists = true;
				break;
			}
		}

		if (!bFuncExists)
		{
			// Create the function graph
			UEdGraph* OnRepGraph = FBlueprintEditorUtils::CreateNewGraph(
				BP, OnRepFuncName, UEdGraph::StaticClass(), UEdGraphSchema_K2::StaticClass());

			if (OnRepGraph)
			{
				FBlueprintEditorUtils::AddFunctionGraph<UClass>(BP, OnRepGraph, /*bIsUserCreated=*/true, nullptr);

				// Link the variable to this OnRep function
				FBlueprintEditorUtils::SetBlueprintVariableRepNotifyFunc(BP, VarName, OnRepFuncName);
			}
			else
			{
				// Non-fatal: variable was created, just couldn't make the OnRep stub
				OnRepFunctionName = TEXT("");
			}
		}
		else
		{
			// Function already exists — just link it
			FBlueprintEditorUtils::SetBlueprintVariableRepNotifyFunc(BP, VarName, OnRepFuncName);
		}
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("variable_name"), VarNameStr);
	Root->SetStringField(TEXT("type"), TypeStr);
	Root->SetBoolField(TEXT("replicated"), true);
	Root->SetStringField(TEXT("replication_condition"), ConditionStr);
	if (bCreateOnRep && !OnRepFunctionName.IsEmpty())
	{
		Root->SetStringField(TEXT("on_rep_function"), OnRepFunctionName);
	}
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}
