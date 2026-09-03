#include "MonolithCoreTools.h"
#include "MonolithGuideTool.h"
#include "MonolithCoreModule.h"
#include "MonolithJsonUtils.h"
#include "MonolithHttpServer.h"
#include "MonolithSettings.h"
#include "MonolithUpdateSubsystem.h"
#include "EditorSubsystem.h"
#include "Misc/App.h"
#include "Editor.h"

// Known optional modules — namespaces that may not have registered actions
// depending on settings or missing plugin dependencies.
struct FKnownOptionalModule
{
	FString Namespace;
	FString SettingsField;   // bool property name on UMonolithSettings
	FString ToolName;        // MCP tool name (namespace_query)
	FString InstallHint;
};

static const TArray<FKnownOptionalModule>& GetKnownOptionalModules()
{
	static const TArray<FKnownOptionalModule> Modules = {
		{
			TEXT("gas"),
			TEXT("bEnableGAS"),
			TEXT("gas_query"),
			TEXT("MonolithGAS module provides Gameplay Ability System tooling (attributes, abilities, effects, cues). Requires GameplayAbilities plugin (engine-bundled).")
		},
		{
			TEXT("combograph"),
			TEXT("bEnableComboGraph"),
			TEXT("combograph_query"),
			TEXT("MonolithComboGraph module provides combo graph tooling (nodes, edges, transitions, effects). Requires ComboGraph plugin (Fab marketplace).")
		}
	};
	return Modules;
}

// Trim a (possibly multi-paragraph) registry description down to a single line
// for TERSE discover output. Detail mode keeps the full description; only the
// emitted terse field is shortened. The `filter` predicate matches the FULL
// description, never this trimmed form.
//
// Strategy: prefer cutting at the first sentence terminator ('.', '!', '?') at
// index >= MinSentence that is followed by a space or end-of-string (so we don't
// cut on "e.g."/"i.e." or on a version like "5.7"/"UK2Node_..."). Fall back to a
// HardCap, backing up to a word boundary, and append an ASCII "..." suffix. The
// suffix is three ASCII dots (NOT the Unicode ellipsis U+2026) to keep the source
// ASCII-only and avoid the project's UTF-8/mojibake release gotcha.
static FString MonolithTerseOneLineDescription(const FString& Full)
{
	const int32 HardCap = 150;
	const int32 MinSentence = 25;

	const int32 Len = Full.Len();

	// Find the first sentence terminator at index >= MinSentence followed by a
	// space (or end-of-string). sentenceEnd is the index AFTER the punctuation.
	int32 SentenceEnd = MAX_int32;
	for (int32 Index = MinSentence; Index < Len; ++Index)
	{
		const TCHAR Ch = Full[Index];
		if (Ch == TEXT('.') || Ch == TEXT('!') || Ch == TEXT('?'))
		{
			const bool bFollowedBySpaceOrEnd = (Index + 1 >= Len) || FChar::IsWhitespace(Full[Index + 1]);
			if (bFollowedBySpaceOrEnd)
			{
				SentenceEnd = Index + 1;
				break;
			}
		}
	}

	int32 Cut = FMath::Min(SentenceEnd, HardCap);

	// Already short (no sentence break before HardCap and within cap) — return as-is, no suffix.
	if (Cut >= Len)
	{
		return Full;
	}

	// If the HardCap landed mid-word, back up to the last whitespace before Cut.
	if (Cut == HardCap && !FChar::IsWhitespace(Full[Cut]))
	{
		int32 WordBoundary = Cut;
		while (WordBoundary > 0 && !FChar::IsWhitespace(Full[WordBoundary - 1]))
		{
			--WordBoundary;
		}
		if (WordBoundary > 0)
		{
			Cut = WordBoundary;
		}
	}

	// Strip any trailing whitespace AND sentence-terminator chars before appending
	// the "..." suffix, so a clean sentence cut ("...graph.") doesn't become four
	// dots ("...graph...."). Every trimmed description ends in exactly one "...".
	FString Trimmed = Full.Left(Cut);
	int32 Tail = Trimmed.Len();
	while (Tail > 0)
	{
		const TCHAR Ch = Trimmed[Tail - 1];
		if (FChar::IsWhitespace(Ch) || Ch == TEXT('.') || Ch == TEXT('!') || Ch == TEXT('?'))
		{
			--Tail;
		}
		else
		{
			break;
		}
	}
	Trimmed.LeftInline(Tail);
	Trimmed += TEXT("...");
	return Trimmed;
}

void FMonolithCoreTools::RegisterAll()
{
	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();

	// monolith_discover
	{
		TSharedPtr<FJsonObject> Schema = MakeShared<FJsonObject>();
		TSharedPtr<FJsonObject> NsProp = MakeShared<FJsonObject>();
		NsProp->SetStringField(TEXT("type"), TEXT("string"));
		NsProp->SetStringField(TEXT("description"), TEXT("Optional: filter to a specific namespace"));
		Schema->SetObjectField(TEXT("namespace"), NsProp);

		TSharedPtr<FJsonObject> CatProp = MakeShared<FJsonObject>();
		CatProp->SetStringField(TEXT("type"), TEXT("string"));
		CatProp->SetStringField(TEXT("description"), TEXT("Optional: filter actions within the namespace by category (e.g. 'CommonUI' inside 'ui')"));
		Schema->SetObjectField(TEXT("category"), CatProp);

		TSharedPtr<FJsonObject> DetailProp = MakeShared<FJsonObject>();
		DetailProp->SetStringField(TEXT("type"), TEXT("boolean"));
		DetailProp->SetStringField(TEXT("description"), TEXT("Optional: inline the full param schema for every action (default false = terse). 'verbose' is an accepted alias. Prefer describe_query action_schema for a single action's schema."));
		Schema->SetObjectField(TEXT("detail"), DetailProp);

		TSharedPtr<FJsonObject> VerboseProp = MakeShared<FJsonObject>();
		VerboseProp->SetStringField(TEXT("type"), TEXT("boolean"));
		VerboseProp->SetStringField(TEXT("description"), TEXT("Alias for detail; inline full param schemas. Prefer detail."));
		Schema->SetObjectField(TEXT("verbose"), VerboseProp);

		TSharedPtr<FJsonObject> FilterProp = MakeShared<FJsonObject>();
		FilterProp->SetStringField(TEXT("type"), TEXT("string"));
		FilterProp->SetStringField(TEXT("description"), TEXT("Optional: case-insensitive substring matched against each action's name or description (applied within the namespace)."));
		Schema->SetObjectField(TEXT("filter"), FilterProp);

		TSharedPtr<FJsonObject> OffsetProp = MakeShared<FJsonObject>();
		OffsetProp->SetStringField(TEXT("type"), TEXT("integer"));
		OffsetProp->SetStringField(TEXT("description"), TEXT("Optional: pagination start index (default 0). Only meaningful when limit > 0."));
		Schema->SetObjectField(TEXT("offset"), OffsetProp);

		TSharedPtr<FJsonObject> LimitProp = MakeShared<FJsonObject>();
		LimitProp->SetStringField(TEXT("type"), TEXT("integer"));
		LimitProp->SetStringField(TEXT("description"), TEXT("Optional: max actions to return (default 0 = ALL — no cap). Pagination is opt-in; with no limit the full action list is returned."));
		Schema->SetObjectField(TEXT("limit"), LimitProp);

		Registry.RegisterAction(
			TEXT("monolith"), TEXT("discover"),
			TEXT("List available tool namespaces and their actions. Pass namespace (and optional category) to filter. Per-namespace output is terse by default (action name + description); pass detail=true to inline param schemas, or use describe_query action_schema for one action. Supports filter (substring) and opt-in offset/limit pagination."),
			FMonolithActionHandler::CreateStatic(&FMonolithCoreTools::HandleDiscover),
			Schema
		);
		// Survivor A (plan §3.A) — read-only + idempotent enumeration.
		Registry.SetActionAnnotations(TEXT("monolith"), TEXT("discover"),
			/*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true,
			TEXT("Discover Monolith actions"));
	}

	// monolith_status
	{
		Registry.RegisterAction(
			TEXT("monolith"), TEXT("status"),
			TEXT("Get Monolith server health: version, uptime, port, registered action count, module status."),
			FMonolithActionHandler::CreateStatic(&FMonolithCoreTools::HandleStatus)
		);
		// Survivor A (plan §3.A) — pure server-health probe; read-only + idempotent.
		Registry.SetActionAnnotations(TEXT("monolith"), TEXT("status"),
			/*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true,
			TEXT("Monolith server status"));
	}

	// monolith_update
	{
		TSharedPtr<FJsonObject> Schema = MakeShared<FJsonObject>();
		TSharedPtr<FJsonObject> ActionProp = MakeShared<FJsonObject>();
		ActionProp->SetStringField(TEXT("type"), TEXT("string"));
		ActionProp->SetStringField(TEXT("description"), TEXT("'check' to compare versions, 'install' to download and stage update"));
		ActionProp->SetStringField(TEXT("default"), TEXT("check"));
		Schema->SetObjectField(TEXT("action"), ActionProp);

		Registry.RegisterAction(
			TEXT("monolith"), TEXT("update"),
			TEXT("Check for or install Monolith updates from GitHub Releases."),
			FMonolithActionHandler::CreateStatic(&FMonolithCoreTools::HandleUpdate),
			Schema
		);
		// Survivor A (plan §3.A) — DELIBERATELY UNANNOTATED. The 'install'
		// action variant modifies plugin source on disk and is not safely
		// read-only. Per plan §3.A: "DO NOT annotate monolith_update".
	}

	// monolith_reindex
	{
		Registry.RegisterAction(
			TEXT("monolith"), TEXT("reindex"),
			TEXT("Re-index the Monolith project database. Incremental by default (delta only). Pass force=true for full wipe+rebuild."),
			FMonolithActionHandler::CreateStatic(&FMonolithCoreTools::HandleReindex)
		);
		// Survivor A (plan §3.A) — destructive of cache state, but functionally
		// idempotent (re-running yields the same on-disk index). Conservative
		// honest values per plan guidance.
		Registry.SetActionAnnotations(TEXT("monolith"), TEXT("reindex"),
			/*bReadOnly=*/false, /*bDestructive=*/false, /*bIdempotent=*/true,
			TEXT("Rebuild Monolith index"));
	}

	// monolith_guide — editorial cross-namespace workflow guide (separate tool file,
	// one-tool-per-file; registers into the "monolith" namespace).
	FMonolithGuideTool::RegisterAll();
}

FMonolithActionResult FMonolithCoreTools::HandleDiscover(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();

	FString FilterNamespace;
	FString FilterCategory;
	if (Params.IsValid())
	{
		Params->TryGetStringField(TEXT("namespace"), FilterNamespace);
		Params->TryGetStringField(TEXT("category"), FilterCategory);
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

	TArray<FString> Namespaces = Registry.GetNamespaces();

	if (!FilterNamespace.IsEmpty())
	{
		// Filter to specific namespace — return detailed action list
		TArray<FMonolithActionInfo> Actions = Registry.GetActions(FilterNamespace);
		if (Actions.Num() == 0)
		{
			// Check if this is a known optional module
			const TArray<FKnownOptionalModule>& OptionalModules = GetKnownOptionalModules();
			const FKnownOptionalModule* Found = nullptr;
			for (const FKnownOptionalModule& Mod : OptionalModules)
			{
				if (Mod.Namespace.Equals(FilterNamespace, ESearchCase::IgnoreCase))
				{
					Found = &Mod;
					break;
				}
			}

			if (Found)
			{
				// Determine disabled vs not_installed by checking the settings toggle
				const UMonolithSettings* Settings = UMonolithSettings::Get();
				bool bSettingEnabled = false;
				if (Settings)
				{
					const FBoolProperty* Prop = CastField<FBoolProperty>(
						UMonolithSettings::StaticClass()->FindPropertyByName(*Found->SettingsField));
					if (Prop)
					{
						bSettingEnabled = Prop->GetPropertyValue_InContainer(Settings);
					}
				}

				Result->SetStringField(TEXT("namespace"), Found->Namespace);
				Result->SetNumberField(TEXT("actions"), 0);

				if (!bSettingEnabled)
				{
					Result->SetStringField(TEXT("status"), TEXT("disabled"));
					Result->SetStringField(TEXT("hint"),
						FString::Printf(TEXT("Enable in Project Settings > Plugins > Monolith > Modules > Optional (%s), then restart the editor."),
							*Found->SettingsField));
				}
				else
				{
					Result->SetStringField(TEXT("status"), TEXT("not_installed"));
					Result->SetStringField(TEXT("hint"), Found->InstallHint);
				}

				return FMonolithActionResult::Success(Result);
			}

			return FMonolithActionResult::Error(
				FString::Printf(TEXT("Unknown namespace: %s"), *FilterNamespace),
				FMonolithJsonUtils::ErrInvalidParams
			);
		}

		// Apply optional category filter (only meaningful when namespace is specified).
		if (!FilterCategory.IsEmpty())
		{
			Actions = Actions.FilterByPredicate([&FilterCategory](const FMonolithActionInfo& Info)
			{
				return Info.Category.Equals(FilterCategory, ESearchCase::IgnoreCase);
			});
		}

		// Terse-by-default: param schemas are omitted unless detail (canonical) or
		// verbose (alias) is set. Schemas are fetched lazily via describe_query
		// action_schema, or inlined for the whole namespace with detail=true.
		bool bDetail = false;
		Params->TryGetBoolField(TEXT("detail"), bDetail);          // canonical
		if (!bDetail)
		{
			Params->TryGetBoolField(TEXT("verbose"), bDetail);     // accepted alias
		}

		// Optional substring filter on action name OR description (case-insensitive).
		// Applied AFTER the category filter, BEFORE pagination.
		FString Filter;
		if (Params->TryGetStringField(TEXT("filter"), Filter) && !Filter.IsEmpty())
		{
			Actions = Actions.FilterByPredicate([&Filter](const FMonolithActionInfo& Info)
			{
				return Info.Action.Contains(Filter, ESearchCase::IgnoreCase)
					|| Info.Description.Contains(Filter, ESearchCase::IgnoreCase);
			});
		}

		// Pagination is OPT-IN. limit=0 (default) returns ALL post-filter actions so
		// discoverability never regresses; any limit>0 slices [offset, offset+limit).
		const int32 TotalCount = Actions.Num();
		int32 Offset = 0;
		int32 Limit = 0;
		Params->TryGetNumberField(TEXT("offset"), Offset);
		Params->TryGetNumberField(TEXT("limit"), Limit);

		int32 SliceStart = 0;
		int32 SliceEnd = TotalCount;
		if (Limit > 0)
		{
			SliceStart = FMath::Clamp(Offset, 0, TotalCount);
			SliceEnd = FMath::Clamp(SliceStart + Limit, SliceStart, TotalCount);
		}

		Result->SetStringField(TEXT("namespace"), FilterNamespace);
		if (!FilterCategory.IsEmpty())
		{
			Result->SetStringField(TEXT("category"), FilterCategory);
		}
		TArray<TSharedPtr<FJsonValue>> ActionArray;
		for (int32 Index = SliceStart; Index < SliceEnd; ++Index)
		{
			const FMonolithActionInfo& ActionInfo = Actions[Index];
			TSharedPtr<FJsonObject> ActionObj = MakeShared<FJsonObject>();
			ActionObj->SetStringField(TEXT("action"), ActionInfo.Action);
			// Terse mode emits a one-line description; detail mode keeps the full text.
			ActionObj->SetStringField(TEXT("description"),
				bDetail ? ActionInfo.Description : MonolithTerseOneLineDescription(ActionInfo.Description));
			if (!ActionInfo.Category.IsEmpty())
			{
				ActionObj->SetStringField(TEXT("category"), ActionInfo.Category);
			}
			if (bDetail && ActionInfo.ParamSchema.IsValid())
			{
				ActionObj->SetObjectField(TEXT("params"), ActionInfo.ParamSchema);
			}
			ActionArray.Add(MakeShared<FJsonValueObject>(ActionObj));
		}
		Result->SetArrayField(TEXT("actions"), ActionArray);

		// Always report the post-filter count (pre-slice). next_offset is emitted
		// only when a positive limit was supplied AND more actions remain.
		Result->SetNumberField(TEXT("total"), TotalCount);
		if (Limit > 0 && SliceEnd < TotalCount)
		{
			Result->SetNumberField(TEXT("next_offset"), SliceStart + Limit);
		}

		// Terse-only hint: tells the agent where to get the param schema it dropped.
		if (!bDetail)
		{
			Result->SetStringField(TEXT("schema_hint"),
				FString::Printf(TEXT("Param schemas omitted. Call describe_query(action_schema, target_namespace=\"%s\", target_action=\"<name>\") for one action's full schema, or pass detail=true to inline all."),
					*FilterNamespace));
		}
	}
	else
	{
		// Return all namespaces with action counts
		TArray<TSharedPtr<FJsonValue>> NsArray;
		for (const FString& Ns : Namespaces)
		{
			TArray<FMonolithActionInfo> Actions = Registry.GetActions(Ns);
			TSharedPtr<FJsonObject> NsObj = MakeShared<FJsonObject>();
			NsObj->SetStringField(TEXT("namespace"), Ns);
			NsObj->SetNumberField(TEXT("action_count"), Actions.Num());

			TArray<TSharedPtr<FJsonValue>> ActionNames;
			for (const FMonolithActionInfo& ActionInfo : Actions)
			{
				ActionNames.Add(MakeShared<FJsonValueString>(ActionInfo.Action));
			}
			NsObj->SetArrayField(TEXT("actions"), ActionNames);
			NsArray.Add(MakeShared<FJsonValueObject>(NsObj));
		}
		// Append known optional modules that aren't already registered
		const TArray<FKnownOptionalModule>& OptionalModules = GetKnownOptionalModules();
		const UMonolithSettings* Settings = UMonolithSettings::Get();

		TArray<TSharedPtr<FJsonValue>> OptionalArray;
		for (const FKnownOptionalModule& Mod : OptionalModules)
		{
			// Skip if this namespace already has registered actions (it's active)
			if (Namespaces.Contains(Mod.Namespace))
			{
				continue;
			}

			TSharedPtr<FJsonObject> OptObj = MakeShared<FJsonObject>();
			OptObj->SetStringField(TEXT("namespace"), Mod.Namespace);
			OptObj->SetStringField(TEXT("tool"), Mod.ToolName);
			OptObj->SetNumberField(TEXT("action_count"), 0);

			bool bSettingEnabled = false;
			if (Settings)
			{
				const FBoolProperty* Prop = CastField<FBoolProperty>(
					UMonolithSettings::StaticClass()->FindPropertyByName(*Mod.SettingsField));
				if (Prop)
				{
					bSettingEnabled = Prop->GetPropertyValue_InContainer(Settings);
				}
			}

			OptObj->SetStringField(TEXT("status"), bSettingEnabled ? TEXT("not_installed") : TEXT("disabled"));
			OptObj->SetStringField(TEXT("hint"), bSettingEnabled ? Mod.InstallHint
				: FString::Printf(TEXT("Enable in Project Settings > Plugins > Monolith > Modules > Optional (%s), then restart the editor."), *Mod.SettingsField));

			OptionalArray.Add(MakeShared<FJsonValueObject>(OptObj));
		}

		if (OptionalArray.Num() > 0)
		{
			Result->SetArrayField(TEXT("optional_modules"), OptionalArray);
		}

		Result->SetArrayField(TEXT("namespaces"), NsArray);
		Result->SetNumberField(TEXT("total_actions"), Registry.GetActionCount());
		Result->SetStringField(TEXT("guide_hint"), TEXT("Call monolith_guide() for editorial cross-namespace workflow recipes, decision matrices, and error-recovery maps. Section-keyed to bound context cost."));
	}

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithCoreTools::HandleStatus(const TSharedPtr<FJsonObject>& Params)
{
	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

	// Version
	Result->SetStringField(TEXT("version"), MONOLITH_VERSION);

	// Server status
	FMonolithHttpServer* Server = FMonolithCoreModule::Get().GetHttpServer();
	Result->SetBoolField(TEXT("server_running"), Server != nullptr && Server->IsRunning());
	Result->SetNumberField(TEXT("server_port"), Server ? Server->GetPort() : 0);

	// Registry stats
	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();
	Result->SetNumberField(TEXT("total_actions"), Registry.GetActionCount());
	Result->SetNumberField(TEXT("namespaces"), Registry.GetNamespaces().Num());

	// Engine info
	Result->SetStringField(TEXT("engine_version"), FApp::GetBuildVersion());

	// Project info
	Result->SetStringField(TEXT("project_name"), FApp::GetProjectName());

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithCoreTools::HandleUpdate(const TSharedPtr<FJsonObject>& Params)
{
	FString Action = TEXT("check");
	if (Params.IsValid())
	{
		Params->TryGetStringField(TEXT("action"), Action);
	}

	if (!GEditor)
	{
		return FMonolithActionResult::Error(TEXT("GEditor not available"));
	}

	UMonolithUpdateSubsystem* UpdateSubsystem = GEditor->GetEditorSubsystem<UMonolithUpdateSubsystem>();
	if (!UpdateSubsystem)
	{
		return FMonolithActionResult::Error(TEXT("MonolithUpdateSubsystem not available"));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

	if (Action == TEXT("check"))
	{
		const FMonolithVersionInfo& Info = UpdateSubsystem->GetVersionInfo();
		Result->SetStringField(TEXT("current_version"), Info.Current);
		Result->SetStringField(TEXT("pending_version"), Info.Pending.IsEmpty() ? TEXT("none") : Info.Pending);
		Result->SetBoolField(TEXT("staging"), Info.bStaging);
		Result->SetStringField(TEXT("status"), TEXT("check_initiated"));

		// Trigger async check — result will come via notification
		UpdateSubsystem->CheckForUpdate();

		return FMonolithActionResult::Success(Result);
	}
	else if (Action == TEXT("install"))
	{
		// Install requires a previous check to have found a version
		const FMonolithVersionInfo& Info = UpdateSubsystem->GetVersionInfo();
		if (Info.bStaging)
		{
			Result->SetStringField(TEXT("status"), TEXT("already_staged"));
			Result->SetStringField(TEXT("pending_version"), Info.Pending);
			Result->SetStringField(TEXT("message"), TEXT("Update already staged. Restart the editor to apply."));
			return FMonolithActionResult::Success(Result);
		}

		// Trigger a check that will show the notification with install button
		UpdateSubsystem->CheckForUpdate();
		Result->SetStringField(TEXT("status"), TEXT("checking_for_installable_update"));
		Result->SetStringField(TEXT("message"), TEXT("Checking GitHub for latest release. If available, an install notification will appear."));
		return FMonolithActionResult::Success(Result);
	}

	return FMonolithActionResult::Error(
		FString::Printf(TEXT("Unknown update action: %s. Use 'check' or 'install'."), *Action),
		FMonolithJsonUtils::ErrInvalidParams
	);
}

FMonolithActionResult FMonolithCoreTools::HandleReindex(const TSharedPtr<FJsonObject>& Params)
{
	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

	if (!FModuleManager::Get().IsModuleLoaded(TEXT("MonolithIndex")))
	{
		Result->SetStringField(TEXT("status"), TEXT("module_not_loaded"));
		Result->SetStringField(TEXT("message"), TEXT("MonolithIndex module is not loaded."));
		return FMonolithActionResult::Success(Result);
	}

	if (!GEditor)
	{
		return FMonolithActionResult::Error(TEXT("GEditor not available"));
	}

	bool bForce = Params.IsValid() && Params->HasField(TEXT("force"))
	              && Params->GetBoolField(TEXT("force"));

	UClass* IndexSubsystemClass = FindObject<UClass>(nullptr, TEXT("/Script/MonolithIndex.MonolithIndexSubsystem"));
	if (!IndexSubsystemClass)
	{
		Result->SetStringField(TEXT("status"), TEXT("subsystem_unavailable"));
		Result->SetStringField(TEXT("message"), TEXT("MonolithIndexSubsystem class not found."));
		return FMonolithActionResult::Success(Result);
	}

	UEditorSubsystem* IndexSubsystem = GEditor->GetEditorSubsystemBase(IndexSubsystemClass);
	if (!IndexSubsystem)
	{
		Result->SetStringField(TEXT("status"), TEXT("subsystem_unavailable"));
		Result->SetStringField(TEXT("message"), TEXT("MonolithIndexSubsystem instance not available."));
		return FMonolithActionResult::Success(Result);
	}

	FString FuncName;
	if (bForce)
	{
		FuncName = TEXT("StartFullIndex");
	}
	else
	{
		// Check if incremental is possible
		UFunction* CanIncrementalFunc = IndexSubsystemClass->FindFunctionByName(TEXT("CanDoIncrementalIndex"));
		if (CanIncrementalFunc)
		{
			struct { uint8 ReturnValue = 0; } Parms;
			FMemory::Memzero(&Parms, sizeof(Parms));
			IndexSubsystem->ProcessEvent(CanIncrementalFunc, &Parms);
			FuncName = Parms.ReturnValue != 0 ? TEXT("StartIncrementalIndex") : TEXT("StartFullIndex");
		}
		else
		{
			// Fallback if CanDoIncrementalIndex not found (old MonolithIndex version)
			FuncName = TEXT("StartFullIndex");
		}
	}

	UFunction* Func = IndexSubsystemClass->FindFunctionByName(*FuncName);
	if (Func)
	{
		IndexSubsystem->ProcessEvent(Func, nullptr);
		Result->SetStringField(TEXT("status"), TEXT("reindex_started"));
		Result->SetStringField(TEXT("message"),
			FString::Printf(TEXT("%s triggered successfully."),
				FuncName == TEXT("StartFullIndex") ? TEXT("Full re-index") : TEXT("Incremental index")));
	}
	else
	{
		Result->SetStringField(TEXT("status"), TEXT("function_not_found"));
		Result->SetStringField(TEXT("message"),
			FString::Printf(TEXT("Function %s not found."), *FuncName));
	}

	return FMonolithActionResult::Success(Result);
}
