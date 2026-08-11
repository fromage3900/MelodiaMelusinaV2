#include "MonolithToolRegistry.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "MonolithFuzzyMatch.h"
#include "HAL/PlatformMisc.h"
#include "Dom/JsonValue.h"

// =============================================================================
//  FMonolithParamSchema — K2 alias rewriting + K3 unknown-key detection
// =============================================================================

bool FMonolithParamSchema::ApplyAliases(
	const TSharedPtr<FJsonObject>& Schema,
	const TSharedPtr<FJsonObject>& Params,
	FString& OutCollision)
{
	if (!Schema.IsValid() || !Params.IsValid())
	{
		return true;
	}

	for (const auto& Pair : Schema->Values)
	{
		const FString Canonical = MonolithKeyToString(Pair.Key);

		const TSharedPtr<FJsonObject>* ParamDef = nullptr;
		if (!Pair.Value->TryGetObject(ParamDef) || !ParamDef)
		{
			continue;
		}

		const TArray<TSharedPtr<FJsonValue>>* AliasArr = nullptr;
		if (!(*ParamDef)->TryGetArrayField(TEXT("aliases"), AliasArr) || !AliasArr)
		{
			continue;
		}

		const bool bCanonicalPresent = Params->HasField(Canonical);

		for (const TSharedPtr<FJsonValue>& AliasVal : *AliasArr)
		{
			FString Alias;
			if (!AliasVal.IsValid() || !AliasVal->TryGetString(Alias))
			{
				continue;
			}

			if (!Params->HasField(Alias))
			{
				continue;
			}

			if (bCanonicalPresent)
			{
				OutCollision = FString::Printf(
					TEXT("Param collision: both canonical '%s' and alias '%s' supplied. Use only one. — supply either the canonical param OR its alias, never both."),
					*Canonical, *Alias);
				return false;
			}

			// Rewrite alias -> canonical (preserve value).
			TSharedPtr<FJsonValue> Val = Params->TryGetField(Alias);
			if (Val.IsValid())
			{
				Params->SetField(Canonical, Val);
			}
			Params->RemoveField(Alias);
			break; // Only one alias rewrite per canonical.
		}
	}

	return true;
}

TArray<FString> FMonolithParamSchema::FindUnknownKeys(
	const TSharedPtr<FJsonObject>& Schema,
	const TSharedPtr<FJsonObject>& Params)
{
	TArray<FString> Unknown;
	if (!Schema.IsValid() || !Params.IsValid())
	{
		return Unknown;
	}

	// Build the set of allowed keys: canonical names + their declared aliases.
	TSet<FString> Allowed;
	for (const auto& Pair : Schema->Values)
	{
		Allowed.Add(MonolithKeyToString(Pair.Key));

		const TSharedPtr<FJsonObject>* ParamDef = nullptr;
		if (!Pair.Value->TryGetObject(ParamDef) || !ParamDef)
		{
			continue;
		}
		const TArray<TSharedPtr<FJsonValue>>* AliasArr = nullptr;
		if ((*ParamDef)->TryGetArrayField(TEXT("aliases"), AliasArr) && AliasArr)
		{
			for (const TSharedPtr<FJsonValue>& AV : *AliasArr)
			{
				FString A;
				if (AV.IsValid() && AV->TryGetString(A))
				{
					Allowed.Add(A);
				}
			}
		}
	}

	// Legacy wbp_path/asset_path back-compat: allow asset_path everywhere.
	Allowed.Add(TEXT("asset_path"));

	// Survivor B (plan §3.B) — universal response-shaping params. Allow these
	// on EVERY action so the K3 STRICT_PARAMS=1 path does not hard-fail on
	// `_fields` / `_omit` / `_compact_json`. The post-filter at the bottom
	// of ExecuteAction consumes + acts on them.
	Allowed.Add(TEXT("_fields"));
	Allowed.Add(TEXT("_omit"));
	Allowed.Add(TEXT("_compact_json"));
	// Phase 1.1 (RI ergonomics handover #3) — nested-payload shaping params.
	// `_row_fields` filters each row of the unique top-level list payload;
	// `_path_fields` retains only matching dotted leaves. Same allowlist
	// treatment as the original three.
	Allowed.Add(TEXT("_row_fields"));
	Allowed.Add(TEXT("_path_fields"));

	for (const auto& Pair : Params->Values)
	{
		const FString PairKeyStr = MonolithKeyToString(Pair.Key);
		if (!Allowed.Contains(PairKeyStr))
		{
			Unknown.Add(PairKeyStr);
		}
	}

	return Unknown;
}

bool FMonolithParamSchema::IsStrictParamsEnabled()
{
	const FString Val = FPlatformMisc::GetEnvironmentVariable(TEXT("STRICT_PARAMS"));
	return Val == TEXT("1");
}

// =============================================================================
//  FMonolithToolRegistry
// =============================================================================

FMonolithToolRegistry& FMonolithToolRegistry::Get()
{
	static FMonolithToolRegistry Instance;
	return Instance;
}

void FMonolithToolRegistry::RegisterAction(
	const FString& Namespace,
	const FString& Action,
	const FString& Description,
	const FMonolithActionHandler& Handler,
	const TSharedPtr<FJsonObject>& ParamSchema,
	const FString& Category)
{
	FScopeLock Lock(&RegistryLock);

	FString Key = MakeKey(Namespace, Action);

	if (Actions.Contains(Key))
	{
		UE_LOG(LogMonolith, Warning, TEXT("Overwriting existing action: %s"), *Key);
	}

	FRegisteredAction RegAction;
	RegAction.Info.Namespace = Namespace;
	RegAction.Info.Action = Action;
	RegAction.Info.Description = Description;
	RegAction.Info.Category = Category;
	RegAction.Info.ParamSchema = ParamSchema;
	RegAction.Handler = Handler;

	Actions.Add(Key, MoveTemp(RegAction));
	NamespaceActions.FindOrAdd(Namespace).AddUnique(Key);

	UE_LOG(LogMonolith, Verbose, TEXT("Registered action: %s — %s"), *Key, *Description);
}

void FMonolithToolRegistry::UnregisterNamespace(const FString& Namespace)
{
	FScopeLock Lock(&RegistryLock);

	if (TArray<FString>* Keys = NamespaceActions.Find(Namespace))
	{
		for (const FString& Key : *Keys)
		{
			Actions.Remove(Key);
		}
		UE_LOG(LogMonolith, Log, TEXT("Unregistered namespace: %s (%d actions)"), *Namespace, Keys->Num());
		NamespaceActions.Remove(Namespace);
	}
}

FMonolithActionResult FMonolithToolRegistry::ExecuteAction(
	const FString& Namespace,
	const FString& Action,
	const TSharedPtr<FJsonObject>& Params)
{
	FScopeLock Lock(&RegistryLock);

	FString Key = MakeKey(Namespace, Action);
	FRegisteredAction* RegAction = Actions.Find(Key);

	if (!RegAction)
	{
		// Survivor C (plan §3.C) — fuzzy-match top-3 suggestions on Unknown
		// action / Unknown namespace. CRITICAL: snapshot the relevant keys
		// under RegistryLock, then DROP the lock before sweeping Levenshtein.
		// Holding the lock during the O(N·|key|·|action|) sweep would block
		// every concurrent tools/list and tools/call (plan §10 Threading).
		const bool bKnownNamespace = NamespaceActions.Contains(Namespace);
		TArray<FString> CandidateKeys;
		FString FuzzyNeedle;
		FString SuggestionKind; // "action" | "namespace" — drives JSON key in suggestions
		if (bKnownNamespace)
		{
			// Action typo within a known namespace. Snapshot the bare action
			// names for this namespace and Levenshtein against `Action`.
			if (const TArray<FString>* NsKeys = NamespaceActions.Find(Namespace))
			{
				CandidateKeys.Reserve(NsKeys->Num());
				for (const FString& FullKey : *NsKeys)
				{
					// FullKey is "namespace.action" — slice the action half.
					int32 DotIdx = INDEX_NONE;
					if (FullKey.FindChar(TEXT('.'), DotIdx))
					{
						CandidateKeys.Add(FullKey.Mid(DotIdx + 1));
					}
					else
					{
						CandidateKeys.Add(FullKey);
					}
				}
			}
			FuzzyNeedle = Action;
			SuggestionKind = TEXT("action");
		}
		else
		{
			// Namespace typo. Snapshot all known namespace names.
			NamespaceActions.GetKeys(CandidateKeys);
			FuzzyNeedle = Namespace;
			SuggestionKind = TEXT("namespace");
		}

		// Drop the lock BEFORE the Levenshtein sweep. The snapshot is now ours.
		Lock.Unlock();

		TArray<MonolithFuzzyMatchDetail::FFuzzyCandidate> Top3 =
			MonolithFuzzyMatchDetail::ScoreFuzzyMatches(FuzzyNeedle, CandidateKeys, /*TopN=*/3);

		// Build the suggestions JSON payload regardless of whether any matched —
		// an empty array on the wire is still informative (the agent learns the
		// needle is novel, not just misspelled).
		TArray<TSharedPtr<FJsonValue>> SuggestionArray;
		for (const MonolithFuzzyMatchDetail::FFuzzyCandidate& C : Top3)
		{
			TSharedPtr<FJsonObject> SObj = MakeShared<FJsonObject>();
			SObj->SetStringField(SuggestionKind, C.Key);
			SObj->SetNumberField(TEXT("score"), C.Score);
			SuggestionArray.Add(MakeShared<FJsonValueObject>(SObj));
		}

		TSharedPtr<FJsonObject> ErrorDataObj = MakeShared<FJsonObject>();
		ErrorDataObj->SetArrayField(TEXT("suggestions"), SuggestionArray);
		ErrorDataObj->SetStringField(TEXT("kind"), SuggestionKind);

		FString MsgSuffix;
		if (Top3.Num() > 0)
		{
			TArray<FString> Names;
			for (const auto& C : Top3) { Names.Add(C.Key); }
			MsgSuffix = FString::Printf(TEXT(" Did you mean: %s?"), *FString::Join(Names, TEXT(", ")));
		}

		if (bKnownNamespace)
		{
			return FMonolithActionResult::Error(
				FString::Printf(TEXT("Unknown action: %s.%s — call monolith_discover(\"%s\") to enumerate valid actions in this namespace.%s"),
					*Namespace, *Action, *Namespace, *MsgSuffix),
				FMonolithJsonUtils::ErrMethodNotFound
			).WithErrorData(ErrorDataObj);
		}
		else
		{
			return FMonolithActionResult::Error(
				FString::Printf(TEXT("Unknown namespace: %s — call monolith_discover() to enumerate valid namespaces.%s"),
					*Namespace, *MsgSuffix),
				FMonolithJsonUtils::ErrMethodNotFound
			).WithErrorData(ErrorDataObj);
		}
	}

	if (!RegAction->Handler.IsBound())
	{
		return FMonolithActionResult::Error(
			FString::Printf(TEXT("Action handler not bound: %s — this is a Monolith bug; the action is registered but its handler delegate is null. Report at github.com/tumourlove/monolith."), *Key),
			FMonolithJsonUtils::ErrInternalError
		);
	}

	const FMonolithActionInfo& ActionInfo = RegAction->Info;
	TSharedPtr<FJsonObject> EffectiveParams = Params.IsValid() ? Params : MakeShared<FJsonObject>();

	// K2 — alias rewriting BEFORE the required-param check.
	if (ActionInfo.ParamSchema.IsValid())
	{
		FString Collision;
		if (!FMonolithParamSchema::ApplyAliases(ActionInfo.ParamSchema, EffectiveParams, Collision))
		{
			return FMonolithActionResult::Error(Collision, FMonolithJsonUtils::ErrInvalidParams);
		}
	}

	// Validate required params from schema before dispatching.
	// Skip asset_path — GetAssetPath() accepts both asset_path and system_path aliases
	// and produces a clear error message itself.
	if (ActionInfo.ParamSchema.IsValid())
	{
		TArray<FString> Missing;
		for (const auto& Pair : ActionInfo.ParamSchema->Values)
		{
			const FString PairKeyStr = MonolithKeyToString(Pair.Key);
			if (PairKeyStr == TEXT("asset_path")) continue;

			const TSharedPtr<FJsonObject>* ParamDef = nullptr;
			if (Pair.Value->TryGetObject(ParamDef) && ParamDef)
			{
				bool bRequired = false;
				(*ParamDef)->TryGetBoolField(TEXT("required"), bRequired);
				if (bRequired && !EffectiveParams->HasField(PairKeyStr))
				{
					// Legacy wbp_path / asset_path aliasing: accept asset_path as substitute for wbp_path
					// (only fires for schemas not migrated to K2 aliases).
					if (PairKeyStr == TEXT("wbp_path") && EffectiveParams->HasField(TEXT("asset_path")))
						continue;
					Missing.Add(PairKeyStr);
				}
			}
		}
		if (Missing.Num() > 0)
		{
			TArray<FString> Provided;
			for (const auto& P : EffectiveParams->Values) Provided.Add(MonolithKeyToString(P.Key));
			return FMonolithActionResult::Error(
				FString::Printf(TEXT("Missing required param(s): [%s]. Provided keys: [%s] — inspect the action's parameter schema via monolith_discover(\"<namespace>\") and supply all required fields."),
					*FString::Join(Missing, TEXT(", ")),
					*FString::Join(Provided, TEXT(", "))));
		}
	}

	// Survivor D (plan §3.D) — schema-tagged path-kind handling.
	// Runs AFTER K2 alias rewrite (so the key the schema sees matches the
	// param name in EffectiveParams) and BEFORE K3 unknown-key check.
	//
	//   - Kind == AssetPath: `\` rewritten to `/` (silent fix-up + warning).
	//   - Kind == DiskPath:  backslash detected → warning, NO rewrite.
	//                        (Per RI ergonomics handover #5, 2026-05-29: the
	//                        DiskPath indexes store paths with forward slashes,
	//                        but DiskPath legitimately COULD address a real OS
	//                        path so we never silently rewrite — we just warn
	//                        loudly. The trap was silent-empty-on-backslash.)
	//   - All other Kinds (Other, GameplayTag) pass through untouched.
	//
	// Warnings appended to the same K3 warnings[] channel by the post-handler
	// block below.
	TArray<FString> PathParamWarnings;
	if (ActionInfo.ParamSchema.IsValid())
	{
		for (const auto& SchemaPair : ActionInfo.ParamSchema->Values)
		{
			const TSharedPtr<FJsonObject>* ParamDefPtr = nullptr;
			if (!SchemaPair.Value->TryGetObject(ParamDefPtr) || !ParamDefPtr || !ParamDefPtr->IsValid())
			{
				continue;
			}
			FString KindStr;
			if (!(*ParamDefPtr)->TryGetStringField(TEXT("kind"), KindStr))
			{
				continue; // No kind tag → Other (default) → no rewrite.
			}
			const EMonolithParamKind Kind = MonolithParamKind::FromString(KindStr);
			if (Kind != EMonolithParamKind::AssetPath && Kind != EMonolithParamKind::DiskPath)
			{
				continue;
			}

			const FString ParamName = MonolithKeyToString(SchemaPair.Key);
			FString Value;
			if (!EffectiveParams->TryGetStringField(ParamName, Value))
			{
				continue;
			}
			if (!Value.Contains(TEXT("\\")))
			{
				continue;
			}

			if (Kind == EMonolithParamKind::AssetPath)
			{
				FString Rewritten = Value.Replace(TEXT("\\"), TEXT("/"));
				EffectiveParams->SetStringField(ParamName, Rewritten);
				PathParamWarnings.Add(FString::Printf(
					TEXT("Normalised backslashes in 'asset_path' param '%s' — future calls should use forward slashes."),
					*ParamName));
			}
			else // DiskPath
			{
				FString Suggested = Value.Replace(TEXT("\\"), TEXT("/"));
				PathParamWarnings.Add(FString::Printf(
					TEXT("DiskPath param '%s' contains backslashes — paths in this index are stored with forward slashes ('/'), so a query for '%s' will likely return zero results. Convert to '%s'."),
					*ParamName, *Value, *Suggested));
			}
		}
	}

	// K3 — unknown-key detection (after required-check, before dispatch).
	TArray<FString> Unknown;
	if (ActionInfo.ParamSchema.IsValid())
	{
		Unknown = FMonolithParamSchema::FindUnknownKeys(ActionInfo.ParamSchema, EffectiveParams);

		if (Unknown.Num() > 0)
		{
			for (const FString& K : Unknown)
			{
				UE_LOG(LogMonolith, Warning,
					TEXT("Unknown param '%s' for action '%s:%s' (typo? not in schema)"),
					*K, *Namespace, *Action);
			}

			if (FMonolithParamSchema::IsStrictParamsEnabled())
			{
				return FMonolithActionResult::Error(
					FString::Printf(TEXT("STRICT_PARAMS=1: rejected action '%s:%s' due to unknown params: [%s] — unset STRICT_PARAMS or remove the unknown params from the call."),
						*Namespace, *Action, *FString::Join(Unknown, TEXT(", "))),
					FMonolithJsonUtils::ErrInvalidParams);
			}
		}
	}

	// Release lock before executing handler (handlers may take time)
	FMonolithActionHandler HandlerCopy = RegAction->Handler;
	Lock.Unlock();

	FMonolithActionResult ActionResult = HandlerCopy.Execute(EffectiveParams);

	// Collect ALL post-handler warnings into a single channel, then attach once.
	// Sources, in order:
	//   1. K3 unknown-param soft-warn (pre-existing behaviour)
	//   2. Survivor D — AssetPath \→/ rewrite warnings (plan §3.D)
	//   3. Survivor B — response-shaping warnings (plan §3.B, e.g. _fields/_omit collision)
	if (ActionResult.bSuccess && ActionResult.Result.IsValid())
	{
		TArray<FString> AllWarnings;
		AllWarnings.Append(PathParamWarnings);
		for (const FString& K : Unknown)
		{
			AllWarnings.Add(FString::Printf(TEXT("Unknown param '%s' for action '%s:%s'"), *K, *Namespace, *Action));
		}

		// Survivor B post-filter — mutates ActionResult.Result in-place and may
		// append its own warnings (e.g., mutually-exclusive _fields + _omit).
		// Runs BEFORE attaching the warnings array so its warnings get included
		// in the final emit; runs AFTER warning collection so the filter cannot
		// strip the warnings[] key out from under us via _fields whitelist.
		// (We attach warnings to ActionResult.Result AFTER ApplyResponseShaping.)
		ApplyResponseShaping(ActionResult.Result, EffectiveParams, AllWarnings);

		if (AllWarnings.Num() > 0 && ActionResult.Result.IsValid())
		{
			TArray<TSharedPtr<FJsonValue>> Existing;
			const TArray<TSharedPtr<FJsonValue>>* Found = nullptr;
			if (ActionResult.Result->TryGetArrayField(TEXT("warnings"), Found) && Found)
			{
				Existing = *Found;
			}
			for (const FString& W : AllWarnings)
			{
				Existing.Add(MakeShared<FJsonValueString>(W));
			}
			ActionResult.Result->SetArrayField(TEXT("warnings"), Existing);
		}
	}

	return ActionResult;
}

TArray<FString> FMonolithToolRegistry::GetNamespaces() const
{
	FScopeLock Lock(&RegistryLock);
	TArray<FString> Result;
	NamespaceActions.GetKeys(Result);
	return Result;
}

TArray<FMonolithActionInfo> FMonolithToolRegistry::GetActions(const FString& Namespace) const
{
	FScopeLock Lock(&RegistryLock);
	TArray<FMonolithActionInfo> Result;

	if (const TArray<FString>* Keys = NamespaceActions.Find(Namespace))
	{
		for (const FString& Key : *Keys)
		{
			if (const FRegisteredAction* RegAction = Actions.Find(Key))
			{
				Result.Add(RegAction->Info);
			}
		}
	}
	return Result;
}

TArray<FMonolithActionInfo> FMonolithToolRegistry::GetAllActions() const
{
	FScopeLock Lock(&RegistryLock);
	TArray<FMonolithActionInfo> Result;
	for (const auto& Pair : Actions)
	{
		Result.Add(Pair.Value.Info);
	}
	return Result;
}

bool FMonolithToolRegistry::HasAction(const FString& Namespace, const FString& Action) const
{
	FScopeLock Lock(&RegistryLock);
	return Actions.Contains(MakeKey(Namespace, Action));
}

int32 FMonolithToolRegistry::GetActionCount() const
{
	FScopeLock Lock(&RegistryLock);
	return Actions.Num();
}

void FMonolithToolRegistry::SetDispatcherAnnotations(
	const FString& Namespace,
	const FMonolithDispatcherAnnotations& Annotations)
{
	FScopeLock Lock(&RegistryLock);
	DispatcherAnnotations.Add(Namespace, Annotations);
}

FMonolithDispatcherAnnotations FMonolithToolRegistry::GetDispatcherAnnotations(const FString& Namespace) const
{
	FScopeLock Lock(&RegistryLock);
	if (const FMonolithDispatcherAnnotations* Found = DispatcherAnnotations.Find(Namespace))
	{
		return *Found;
	}
	return FMonolithDispatcherAnnotations{};
}

void FMonolithToolRegistry::SetActionAnnotations(
	const FString& Namespace,
	const FString& Action,
	bool bReadOnly,
	bool bDestructive,
	bool bIdempotent,
	const FString& Title)
{
	FScopeLock Lock(&RegistryLock);
	FString Key = MakeKey(Namespace, Action);
	if (FRegisteredAction* RegAction = Actions.Find(Key))
	{
		RegAction->Info.bReadOnlyHint = bReadOnly;
		RegAction->Info.bDestructiveHint = bDestructive;
		RegAction->Info.bIdempotentHint = bIdempotent;
		RegAction->Info.Title = Title;
	}
}
