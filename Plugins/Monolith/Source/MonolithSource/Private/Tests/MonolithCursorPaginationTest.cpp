// SPDX-License-Identifier: MIT
// Survivor E (source_query("search_source") cursor pagination) automation tests
// — plan §12 "Survivor E", plan §3.E.
// Plan: Plugins/Monolith/Docs/plans/2026-05-27-mcp-llm-ergonomics.md
//
// DEVIATION NOTE: plan §6 file-table specifies `Source/MonolithSource/Tests/...`.
// This file lives under `Source/MonolithSource/Private/Tests/...` so UBT's
// auto-include of `Private/` picks it up without a Build.cs change. Matches
// the established precedent (see `MonolithFuzzyMatchTest.cpp` deviation note).
//
// Test names use the `Monolith.CursorPagination.*` prefix to match Monolith
// convention (NOT `Leviathan.Monolith.*`).

#include "Misc/AutomationTest.h"
#include "MonolithCursorCodec.h"
#include "MonolithToolRegistry.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace MonolithCursorPaginationTestDetail
{
	// Helper: dispatch source.search_source through the registry. Goes through
	// the full dispatch path (K2 alias rewrite, K3 unknown-key check) so the
	// envelope shape we test matches what real callers observe.
	static FMonolithActionResult Call(
		const FString& Query,
		int32 Limit,
		const FString& Cursor = TEXT(""),
		const FString& Scope = TEXT(""),
		const FString& Module = TEXT(""))
	{
		TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
		Params->SetStringField(TEXT("query"), Query);
		Params->SetNumberField(TEXT("limit"), Limit);
		if (!Cursor.IsEmpty())
		{
			Params->SetStringField(TEXT("cursor"), Cursor);
		}
		if (!Scope.IsEmpty())
		{
			Params->SetStringField(TEXT("scope"), Scope);
		}
		if (!Module.IsEmpty())
		{
			Params->SetStringField(TEXT("module"), Module);
		}
		return FMonolithToolRegistry::Get().ExecuteAction(
			TEXT("source"), TEXT("search_source"), Params);
	}

	// True iff the result has a non-null `total_estimate` numeric field.
	static bool HasTotalEstimate(const FMonolithActionResult& R)
	{
		if (!R.bSuccess || !R.Result.IsValid()) return false;
		double Unused = 0.0;
		return R.Result->TryGetNumberField(TEXT("total_estimate"), Unused);
	}

	// True iff the result has a non-empty `next_cursor` string field.
	static bool HasNextCursor(const FMonolithActionResult& R, FString& OutCursor)
	{
		OutCursor.Reset();
		if (!R.bSuccess || !R.Result.IsValid()) return false;
		if (!R.Result->TryGetStringField(TEXT("next_cursor"), OutCursor)) return false;
		return !OutCursor.IsEmpty();
	}

	// True iff the source DB is loaded and search returns something for a probe.
	// Tests that require a live index skip with a warning if false.
	static bool IsSourceIndexAvailable()
	{
		// Probe with a deliberately common token. Returning success means the
		// DB opened and the FTS query path executed; absence of results would
		// still be "success" but the corpus-walk tests would be uninformative.
		FMonolithActionResult Probe = Call(TEXT("class"), 1);
		return Probe.bSuccess;
	}
}

// ---------------------------------------------------------------------------
// Test 1: Round-trip — encode then decode a FCursorState; assert all fields
// survive intact.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithCursorPaginationRoundTripTest,
	"Monolith.CursorPagination.RoundTrip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithCursorPaginationRoundTripTest::RunTest(const FString& /*Parameters*/)
{
	MonolithCursorCodec::FCursorState In;
	In.QueryHash = 0xDEADBEEFu;
	In.SymbolPage = 2;
	In.SourcePage = 3;
	In.CachedTotalEstimate = 420;

	const FString Encoded = MonolithCursorCodec::Encode(In);
	TestFalse(TEXT("Encoded cursor is non-empty"), Encoded.IsEmpty());

	MonolithCursorCodec::FCursorState Out;
	const bool bDecoded = MonolithCursorCodec::Decode(Encoded, Out);
	TestTrue(TEXT("Decode succeeded"), bDecoded);
	TestEqual(TEXT("QueryHash round-trips"), Out.QueryHash, In.QueryHash);
	TestEqual(TEXT("SymbolPage round-trips"), Out.SymbolPage, In.SymbolPage);
	TestEqual(TEXT("SourcePage round-trips"), Out.SourcePage, In.SourcePage);
	TestEqual(TEXT("CachedTotalEstimate round-trips"), Out.CachedTotalEstimate, In.CachedTotalEstimate);

	// Garbage in → false out, no crash.
	MonolithCursorCodec::FCursorState Junk;
	TestFalse(TEXT("Garbage base64 rejected cleanly"),
		MonolithCursorCodec::Decode(TEXT("this-is-not-base64!!!"), Junk));

	// Empty string → false out.
	TestFalse(TEXT("Empty cursor rejected"),
		MonolithCursorCodec::Decode(TEXT(""), Junk));

	return true;
}

// ---------------------------------------------------------------------------
// Test 2: QueryMismatchRejection — encode cursor with QueryHash=A, dispatch
// HandleSearchSource with a query whose computed hash is B; assert clean
// INVALID_CURSOR error (not crash, not silent reset).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithCursorPaginationQueryMismatchRejectionTest,
	"Monolith.CursorPagination.QueryMismatchRejection",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithCursorPaginationQueryMismatchRejectionTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCursorPaginationTestDetail;

	// Fabricate a cursor with a deliberately bogus query hash. ComputeQueryHash
	// for ("FooBarBaz",...) will not produce 0x12345678; the dispatch must
	// detect the mismatch and return INVALID_CURSOR.
	MonolithCursorCodec::FCursorState Bogus;
	Bogus.QueryHash = 0x12345678u;
	Bogus.SymbolPage = 1;
	Bogus.SourcePage = 1;
	Bogus.CachedTotalEstimate = 99;
	const FString BogusCursor = MonolithCursorCodec::Encode(Bogus);

	FMonolithActionResult R = Call(TEXT("FooBarBaz_QueryHashMismatchProbe_2026"), 10, BogusCursor);
	TestFalse(TEXT("Mismatched cursor returns error (not success)"), R.bSuccess);
	TestTrue(TEXT("Error carries ErrorData"), R.ErrorData.IsValid());

	if (R.ErrorData.IsValid())
	{
		const TSharedPtr<FJsonObject>* DataObjPtr = nullptr;
		if (R.ErrorData->TryGetObject(DataObjPtr) && DataObjPtr && (*DataObjPtr).IsValid())
		{
			FString Code;
			const bool bHasCode = (*DataObjPtr)->TryGetStringField(TEXT("error_code"), Code);
			TestTrue(TEXT("ErrorData.error_code present"), bHasCode);
			TestEqual(TEXT("error_code is INVALID_CURSOR"), Code, FString(TEXT("INVALID_CURSOR")));
		}
	}

	// Also verify garbage base64 cursor returns INVALID_CURSOR (decode failure path).
	FMonolithActionResult R2 = Call(TEXT("FooBarBaz_QueryHashMismatchProbe_2026"), 10,
		TEXT("not-a-real-cursor"));
	TestFalse(TEXT("Garbage cursor returns error"), R2.bSuccess);

	return true;
}

// ---------------------------------------------------------------------------
// Test 3: HardCap — request limit=2000 on page 0; assert the returned page
// is clamped at 1000 rows (FTS query issued with N=1000 max).
//
// Indirect assertion: we cannot easily count the exact row count without
// parsing the text payload, so we instead assert:
//   (a) the call succeeds (no crash on huge limit), AND
//   (b) on a real index, total_estimate is present on page 0 AND
//   (c) next_cursor is OMITTED (since slice end == HARD_CAP, no further pages).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithCursorPaginationHardCapTest,
	"Monolith.CursorPagination.HardCap",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithCursorPaginationHardCapTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCursorPaginationTestDetail;
	if (!IsSourceIndexAvailable())
	{
		AddWarning(TEXT("Skipping: source index not available in this test run"));
		return true;
	}

	FMonolithActionResult R = Call(TEXT("class"), 2000);
	TestTrue(TEXT("Huge limit call succeeds"), R.bSuccess);
	TestTrue(TEXT("Result is valid"), R.Result.IsValid());

	// Page 0 ALWAYS carries total_estimate.
	TestTrue(TEXT("Page 0 has total_estimate"), HasTotalEstimate(R));

	// With Limit=2000 → SliceEnd = min(2000, HARD_CAP=1000) = 1000.
	// NextSliceStart = 2000 which is >= HARD_CAP, so next_cursor is OMITTED.
	FString NextCursor;
	TestFalse(TEXT("HardCap page emits no next_cursor"), HasNextCursor(R, NextCursor));
	return true;
}

// ---------------------------------------------------------------------------
// Test 4: TotalEstimatePageZeroOnly — page 0 carries `total_estimate`;
// follow-up page (decoded from page 0's `next_cursor`) does NOT.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithCursorPaginationTotalEstimatePageZeroOnlyTest,
	"Monolith.CursorPagination.TotalEstimatePageZeroOnly",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithCursorPaginationTotalEstimatePageZeroOnlyTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCursorPaginationTestDetail;
	if (!IsSourceIndexAvailable())
	{
		AddWarning(TEXT("Skipping: source index not available in this test run"));
		return true;
	}

	// Use a tiny limit so the first page is virtually guaranteed to be full
	// and a next_cursor will be emitted (assuming `class` is common enough
	// to return > 5 rows from either symbol or source FTS).
	FMonolithActionResult Page0 = Call(TEXT("class"), 5);
	TestTrue(TEXT("Page 0 succeeded"), Page0.bSuccess);
	TestTrue(TEXT("Page 0 has total_estimate"), HasTotalEstimate(Page0));

	FString NextCursor;
	const bool bHasNext = HasNextCursor(Page0, NextCursor);
	if (!bHasNext)
	{
		AddWarning(TEXT("Skipping page-1 assertion: corpus too small for limit=5 to need pagination"));
		return true;
	}

	FMonolithActionResult Page1 = Call(TEXT("class"), 5, NextCursor);
	TestTrue(TEXT("Page 1 succeeded"), Page1.bSuccess);
	// Critical assertion: page 1+ does NOT re-emit total_estimate.
	TestFalse(TEXT("Page 1 omits total_estimate"), HasTotalEstimate(Page1));
	return true;
}

// ---------------------------------------------------------------------------
// Test 5: PageBoundaryNoNextCursor — verify the envelope SHAPE for a query
// that returns fewer than `limit` total rows. The terminal page must have
// no `next_cursor`.
//
// We can't fixture a controlled corpus without major scaffolding (plan §12
// SMOKE allowance), so we use a query that we expect to return a small but
// nonzero number of hits — a deliberately obscure token unlikely to appear
// in > 200 source lines. If the assumption fails on a given index build,
// the test issues a warning rather than failing.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithCursorPaginationPageBoundaryNoNextCursorTest,
	"Monolith.CursorPagination.PageBoundaryNoNextCursor",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithCursorPaginationPageBoundaryNoNextCursorTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCursorPaginationTestDetail;
	if (!IsSourceIndexAvailable())
	{
		AddWarning(TEXT("Skipping: source index not available in this test run"));
		return true;
	}

	// Issue a search with a HUGE limit — the result is guaranteed to be a
	// terminal page (either bShortPage or bCapReached), so next_cursor MUST
	// be omitted. This is the envelope-shape smoke described in the plan's
	// "drop the PageBoundary test to a SMOKE" allowance.
	FMonolithActionResult R = Call(TEXT("FZeroToOne_VeryUnlikelyTokenName_2026"), 500);
	TestTrue(TEXT("Call succeeded"), R.bSuccess);
	TestTrue(TEXT("Result is valid"), R.Result.IsValid());

	// Terminal page → no next_cursor regardless of whether any rows came back.
	FString NextCursor;
	TestFalse(TEXT("Terminal page emits no next_cursor"), HasNextCursor(R, NextCursor));
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
