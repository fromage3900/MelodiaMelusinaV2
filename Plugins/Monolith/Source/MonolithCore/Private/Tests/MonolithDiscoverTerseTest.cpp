// SPDX-License-Identifier: MIT
// Automation tests for terse monolith_discover(namespace).
// Plan: Plugins/Monolith/Docs/plans/2026-06-19-terse-discover.md (Field 10)
//
// Goals:
//   - Per-namespace discover is terse by default: action + description, NO `params`.
//   - `detail=true` (canonical) inlines the full per-action param schema.
//   - `verbose=true` is an accepted alias for `detail=true`.
//   - `filter` substring-matches name OR description (case-insensitive).
//   - Default (no limit) returns the FULL action list (discoverability gate).
//   - Pagination (offset/limit) is opt-in; limit=0 = ALL; out-of-range clamps.
//   - Unknown namespace still errors.
//
// Lives under Private/Tests/ for the same UBT auto-include reason as the other
// MonolithCore tests in this folder.

#include "Misc/AutomationTest.h"
#include "MonolithToolRegistry.h"
#include "MonolithJsonUtils.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace MonolithDiscoverTerseTestDetail
{
	/** Run monolith.discover with the given params. */
	static FMonolithActionResult Discover(const TSharedPtr<FJsonObject>& Params)
	{
		return FMonolithToolRegistry::Get().ExecuteAction(TEXT("monolith"), TEXT("discover"), Params);
	}

	/** Build a map of action name -> emitted description from a discover result's actions array. */
	static TMap<FString, FString> DescriptionsByAction(const FMonolithActionResult& R)
	{
		TMap<FString, FString> Out;
		if (!R.bSuccess || !R.Result.IsValid())
		{
			return Out;
		}
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		if (!R.Result->TryGetArrayField(TEXT("actions"), Arr) || !Arr)
		{
			return Out;
		}
		for (const TSharedPtr<FJsonValue>& Val : *Arr)
		{
			const TSharedPtr<FJsonObject>* Obj = nullptr;
			if (Val.IsValid() && Val->TryGetObject(Obj) && Obj)
			{
				FString Name, Desc;
				(*Obj)->TryGetStringField(TEXT("action"), Name);
				(*Obj)->TryGetStringField(TEXT("description"), Desc);
				Out.Add(Name, Desc);
			}
		}
		return Out;
	}

	/** Full (unfiltered) action count for the monolith namespace — the discoverability baseline. */
	static int32 FullActionCount()
	{
		return FMonolithToolRegistry::Get().GetActions(TEXT("monolith")).Num();
	}

	/** Pull the `actions` array out of a successful discover result, or null. */
	static const TArray<TSharedPtr<FJsonValue>>* GetActionsArray(const FMonolithActionResult& R)
	{
		if (!R.bSuccess || !R.Result.IsValid())
		{
			return nullptr;
		}
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		R.Result->TryGetArrayField(TEXT("actions"), Arr);
		return Arr;
	}
}

// ---------------------------------------------------------------------------
// Test 1: Terse default — each action obj has action+description, NO `params`;
// top-level `schema_hint` present.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDiscoverTerseDefaultTest,
	"Monolith.Discover.Terse.Default",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDiscoverTerseDefaultTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDiscoverTerseTestDetail;

	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("namespace"), TEXT("monolith"));

	const FMonolithActionResult R = Discover(Params);
	TestTrue(TEXT("terse discover succeeds"), R.bSuccess);

	const TArray<TSharedPtr<FJsonValue>>* Arr = GetActionsArray(R);
	TestNotNull(TEXT("actions array present"), Arr);
	if (Arr)
	{
		TestTrue(TEXT("at least one action returned"), Arr->Num() > 0);
		for (const TSharedPtr<FJsonValue>& Val : *Arr)
		{
			const TSharedPtr<FJsonObject>* Obj = nullptr;
			if (Val.IsValid() && Val->TryGetObject(Obj) && Obj)
			{
				TestTrue(TEXT("action obj has 'action'"), (*Obj)->HasField(TEXT("action")));
				TestTrue(TEXT("action obj has 'description'"), (*Obj)->HasField(TEXT("description")));
				TestFalse(TEXT("terse action obj has NO 'params'"), (*Obj)->HasField(TEXT("params")));
			}
		}
	}

	if (R.bSuccess && R.Result.IsValid())
	{
		TestTrue(TEXT("terse result has top-level schema_hint"), R.Result->HasField(TEXT("schema_hint")));
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 2: Detail opt-in — each action obj HAS `params`.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDiscoverDetailOptInTest,
	"Monolith.Discover.Terse.DetailOptIn",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDiscoverDetailOptInTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDiscoverTerseTestDetail;

	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("namespace"), TEXT("monolith"));
	Params->SetBoolField(TEXT("detail"), true);

	const FMonolithActionResult R = Discover(Params);
	TestTrue(TEXT("detail discover succeeds"), R.bSuccess);

	const TArray<TSharedPtr<FJsonValue>>* Arr = GetActionsArray(R);
	TestNotNull(TEXT("actions array present"), Arr);
	if (Arr)
	{
		// In detail mode every monolith action that carries a ParamSchema emits
		// `params`. At least one monolith action (discover/update) has a schema, so
		// assert at least one action obj carries params.
		bool bAnyHasParams = false;
		for (const TSharedPtr<FJsonValue>& Val : *Arr)
		{
			const TSharedPtr<FJsonObject>* Obj = nullptr;
			if (Val.IsValid() && Val->TryGetObject(Obj) && Obj && (*Obj)->HasField(TEXT("params")))
			{
				bAnyHasParams = true;
				break;
			}
		}
		TestTrue(TEXT("detail mode inlines params on at least one action"), bAnyHasParams);
	}

	if (R.bSuccess && R.Result.IsValid())
	{
		TestFalse(TEXT("detail result has NO schema_hint"), R.Result->HasField(TEXT("schema_hint")));
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 3: verbose alias — output is byte-IDENTICAL to detail:true (verbose is a
// registered param, so no spurious unknown-param warning is emitted).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDiscoverVerboseAliasTest,
	"Monolith.Discover.Terse.VerboseAlias",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDiscoverVerboseAliasTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDiscoverTerseTestDetail;

	TSharedPtr<FJsonObject> VerboseParams = MakeShared<FJsonObject>();
	VerboseParams->SetStringField(TEXT("namespace"), TEXT("monolith"));
	VerboseParams->SetBoolField(TEXT("verbose"), true);
	const FMonolithActionResult VerboseR = Discover(VerboseParams);
	TestTrue(TEXT("verbose discover succeeds"), VerboseR.bSuccess);

	TSharedPtr<FJsonObject> DetailParams = MakeShared<FJsonObject>();
	DetailParams->SetStringField(TEXT("namespace"), TEXT("monolith"));
	DetailParams->SetBoolField(TEXT("detail"), true);
	const FMonolithActionResult DetailR = Discover(DetailParams);
	TestTrue(TEXT("detail discover succeeds"), DetailR.bSuccess);

	if (VerboseR.bSuccess && VerboseR.Result.IsValid())
	{
		// verbose must be a recognized param — no spurious unknown-param warning.
		TestFalse(TEXT("verbose result carries no warnings"), VerboseR.Result->HasField(TEXT("warnings")));
	}

	if (VerboseR.Result.IsValid() && DetailR.Result.IsValid())
	{
		const FString VerboseStr = FMonolithJsonUtils::Serialize(VerboseR.Result);
		const FString DetailStr = FMonolithJsonUtils::Serialize(DetailR.Result);
		TestEqual(TEXT("verbose output is byte-identical to detail output"), VerboseStr, DetailStr);
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 4: filter — only actions whose name/description contains "status"
// (case-insensitive); `total` reflects the filtered count.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDiscoverFilterTest,
	"Monolith.Discover.Terse.Filter",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDiscoverFilterTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDiscoverTerseTestDetail;

	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("namespace"), TEXT("monolith"));
	Params->SetStringField(TEXT("filter"), TEXT("status"));

	const FMonolithActionResult R = Discover(Params);
	TestTrue(TEXT("filtered discover succeeds"), R.bSuccess);

	const TArray<TSharedPtr<FJsonValue>>* Arr = GetActionsArray(R);
	TestNotNull(TEXT("actions array present"), Arr);
	if (Arr)
	{
		// Every returned action must match "status" in name OR description (case-insensitive).
		for (const TSharedPtr<FJsonValue>& Val : *Arr)
		{
			const TSharedPtr<FJsonObject>* Obj = nullptr;
			if (Val.IsValid() && Val->TryGetObject(Obj) && Obj)
			{
				FString Name, Desc;
				(*Obj)->TryGetStringField(TEXT("action"), Name);
				(*Obj)->TryGetStringField(TEXT("description"), Desc);
				const bool bMatches = Name.Contains(TEXT("status"), ESearchCase::IgnoreCase)
					|| Desc.Contains(TEXT("status"), ESearchCase::IgnoreCase);
				TestTrue(TEXT("filtered action matches 'status'"), bMatches);
			}
		}

		// `total` equals the filtered (returned) count when no pagination is applied.
		if (R.Result.IsValid())
		{
			int32 Total = -1;
			R.Result->TryGetNumberField(TEXT("total"), Total);
			TestEqual(TEXT("total equals filtered count"), Total, Arr->Num());
		}
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 5: default returns FULL list — no limit => array length == total ==
// full action count; NO next_offset (nothing truncated).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDiscoverFullListTest,
	"Monolith.Discover.Terse.FullList",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDiscoverFullListTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDiscoverTerseTestDetail;

	const int32 Full = FullActionCount();
	TestTrue(TEXT("namespace has at least one action"), Full > 0);

	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("namespace"), TEXT("monolith"));

	const FMonolithActionResult R = Discover(Params);
	TestTrue(TEXT("default discover succeeds"), R.bSuccess);

	const TArray<TSharedPtr<FJsonValue>>* Arr = GetActionsArray(R);
	TestNotNull(TEXT("actions array present"), Arr);
	if (Arr)
	{
		TestEqual(TEXT("default array length == full action count"), Arr->Num(), Full);
	}
	if (R.bSuccess && R.Result.IsValid())
	{
		int32 Total = -1;
		R.Result->TryGetNumberField(TEXT("total"), Total);
		TestEqual(TEXT("total == full action count"), Total, Full);
		TestFalse(TEXT("no next_offset when nothing truncated"), R.Result->HasField(TEXT("next_offset")));
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 6: opt-in pagination — offset:1,limit:1 => exactly 1 action, total=full
// count, next_offset present when more remain; limit:0 returns ALL; out-of-range
// offset/limit clamp without error.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDiscoverPaginationTest,
	"Monolith.Discover.Terse.Pagination",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDiscoverPaginationTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDiscoverTerseTestDetail;

	const int32 Full = FullActionCount();
	TestTrue(TEXT("namespace has multiple actions for pagination"), Full >= 2);

	// offset:1, limit:1 => exactly one action returned.
	{
		TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
		Params->SetStringField(TEXT("namespace"), TEXT("monolith"));
		Params->SetNumberField(TEXT("offset"), 1);
		Params->SetNumberField(TEXT("limit"), 1);

		const FMonolithActionResult R = Discover(Params);
		TestTrue(TEXT("paginated discover succeeds"), R.bSuccess);

		const TArray<TSharedPtr<FJsonValue>>* Arr = GetActionsArray(R);
		TestNotNull(TEXT("actions array present"), Arr);
		if (Arr)
		{
			TestEqual(TEXT("limit:1 returns exactly 1 action"), Arr->Num(), 1);
		}
		if (R.Result.IsValid())
		{
			int32 Total = -1;
			R.Result->TryGetNumberField(TEXT("total"), Total);
			TestEqual(TEXT("total still reports full count under pagination"), Total, Full);

			// More remain after offset 1 + limit 1 when Full > 2 ; equals when Full == 2.
			const bool bMoreRemain = (1 + 1) < Full;
			if (bMoreRemain)
			{
				TestTrue(TEXT("next_offset present when more remain"), R.Result->HasField(TEXT("next_offset")));
				int32 NextOffset = -1;
				R.Result->TryGetNumberField(TEXT("next_offset"), NextOffset);
				TestEqual(TEXT("next_offset == offset + limit"), NextOffset, 2);
			}
			else
			{
				TestFalse(TEXT("no next_offset when slice reaches end"), R.Result->HasField(TEXT("next_offset")));
			}
		}
	}

	// limit:0 returns ALL (explicit no-cap sentinel).
	{
		TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
		Params->SetStringField(TEXT("namespace"), TEXT("monolith"));
		Params->SetNumberField(TEXT("limit"), 0);

		const FMonolithActionResult R = Discover(Params);
		TestTrue(TEXT("limit:0 discover succeeds"), R.bSuccess);
		const TArray<TSharedPtr<FJsonValue>>* Arr = GetActionsArray(R);
		TestNotNull(TEXT("actions array present"), Arr);
		if (Arr)
		{
			TestEqual(TEXT("limit:0 returns ALL actions"), Arr->Num(), Full);
		}
		if (R.Result.IsValid())
		{
			TestFalse(TEXT("limit:0 emits no next_offset"), R.Result->HasField(TEXT("next_offset")));
		}
	}

	// Out-of-range offset/limit clamp without error.
	{
		TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
		Params->SetStringField(TEXT("namespace"), TEXT("monolith"));
		Params->SetNumberField(TEXT("offset"), Full + 100);
		Params->SetNumberField(TEXT("limit"), 50);

		const FMonolithActionResult R = Discover(Params);
		TestTrue(TEXT("out-of-range pagination still succeeds (clamped)"), R.bSuccess);
		const TArray<TSharedPtr<FJsonValue>>* Arr = GetActionsArray(R);
		TestNotNull(TEXT("actions array present"), Arr);
		if (Arr)
		{
			TestEqual(TEXT("offset past end yields empty slice"), Arr->Num(), 0);
		}
		if (R.Result.IsValid())
		{
			int32 Total = -1;
			R.Result->TryGetNumberField(TEXT("total"), Total);
			TestEqual(TEXT("total unaffected by clamped offset"), Total, Full);
			TestFalse(TEXT("no next_offset when offset clamped past end"), R.Result->HasField(TEXT("next_offset")));
		}
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 8: terse description trim invariant (blueprint namespace).
// For every action: (a) terse description length <= HardCap + 3 (the "..."),
// and (b) the terse description with any trailing "..." removed is a prefix of
// the full (detail) description. AND at least one action whose full description
// exceeds HardCap must have a terse description ending in "..." (proves trimming
// actually fires). HardCap mirrors MonolithTerseOneLineDescription (150).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDiscoverTerseTrimInvariantTest,
	"Monolith.Discover.Terse.TrimInvariant",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDiscoverTerseTrimInvariantTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDiscoverTerseTestDetail;

	// Mirror the helper's HardCap; terse descriptions never exceed HardCap + len("...").
	const int32 HardCap = 150;
	const FString Ellipsis = TEXT("...");

	// blueprint is registered in-editor and has long, multi-paragraph descriptions.
	TSharedPtr<FJsonObject> TerseParams = MakeShared<FJsonObject>();
	TerseParams->SetStringField(TEXT("namespace"), TEXT("blueprint"));
	const FMonolithActionResult TerseR =
		FMonolithToolRegistry::Get().ExecuteAction(TEXT("monolith"), TEXT("discover"), TerseParams);

	TSharedPtr<FJsonObject> DetailParams = MakeShared<FJsonObject>();
	DetailParams->SetStringField(TEXT("namespace"), TEXT("blueprint"));
	DetailParams->SetBoolField(TEXT("detail"), true);
	const FMonolithActionResult DetailR =
		FMonolithToolRegistry::Get().ExecuteAction(TEXT("monolith"), TEXT("discover"), DetailParams);

	if (!TerseR.bSuccess || !DetailR.bSuccess)
	{
		// blueprint namespace not registered (e.g. headless) — skip rather than fail.
		AddInfo(TEXT("blueprint namespace unavailable; skipping trim-invariant test"));
		return true;
	}

	const TMap<FString, FString> Terse = DescriptionsByAction(TerseR);
	const TMap<FString, FString> Full = DescriptionsByAction(DetailR);
	TestTrue(TEXT("blueprint returned at least one action"), Terse.Num() > 0);

	bool bAnyTrimmed = false;
	for (const TPair<FString, FString>& Pair : Terse)
	{
		const FString& TerseDesc = Pair.Value;
		const FString* FullDescPtr = Full.Find(Pair.Key);
		TestNotNull(TEXT("detail description exists for action"), FullDescPtr);
		if (!FullDescPtr)
		{
			continue;
		}
		const FString& FullDesc = *FullDescPtr;

		// (a) terse length bounded by HardCap + len("...").
		TestTrue(TEXT("terse description length <= HardCap + 3"),
			TerseDesc.Len() <= HardCap + Ellipsis.Len());

		// (b) terse-minus-ellipsis is a prefix of the full description.
		FString Core = TerseDesc;
		const bool bEndsWithEllipsis = Core.EndsWith(Ellipsis, ESearchCase::CaseSensitive);
		if (bEndsWithEllipsis)
		{
			Core.LeftChopInline(Ellipsis.Len());
		}
		// Trimming right-trims trailing whitespace before appending "..."; a prefix
		// match after TrimEnd on the full description tolerates that boundary.
		TestTrue(TEXT("terse core is a prefix of the full description"),
			FullDesc.StartsWith(Core, ESearchCase::CaseSensitive));

		if (bEndsWithEllipsis && FullDesc.Len() > HardCap)
		{
			bAnyTrimmed = true;
		}
	}

	TestTrue(TEXT("at least one long description was trimmed with '...'"), bAnyTrimmed);
	return true;
}

// ---------------------------------------------------------------------------
// Test 7: unknown namespace — error path still fires.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDiscoverUnknownNamespaceTest,
	"Monolith.Discover.Terse.UnknownNamespace",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDiscoverUnknownNamespaceTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDiscoverTerseTestDetail;

	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("namespace"), TEXT("definitely_not_a_real_namespace_xyz"));

	const FMonolithActionResult R = Discover(Params);
	TestFalse(TEXT("unknown namespace must error"), R.bSuccess);
	if (!R.bSuccess)
	{
		TestTrue(TEXT("error mentions the unknown namespace"),
			R.ErrorMessage.Contains(TEXT("Unknown namespace")));
	}
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
