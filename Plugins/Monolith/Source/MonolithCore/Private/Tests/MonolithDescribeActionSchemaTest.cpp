// SPDX-License-Identifier: MIT
// RI ergonomics handover #6 (2026-05-29) automation tests for describe.action_schema.
// Handover: Plugins/Monolith/Docs/plans/2026-05-29-ri-ergonomics-improvements-handover.md
//
// Goals:
//   - `target_action` is the canonical param name and works on its own.
//   - `action` (legacy) still works via the K2 alias rewrite.
//   - Supplying BOTH `target_action` and `action` is a collision error.
//   - Missing-required-param error lists ALL missing required params at once
//     (not one round-trip at a time, which was the bug).
//
// Lives under Private/Tests/ for the same UBT auto-include reason as the other
// MonolithCore tests in this folder.

#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "MonolithToolRegistry.h"
#include "MonolithJsonUtils.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace MonolithDescribeActionSchemaTestDetail
{
	/** Resolve the registered describe action_schema; assumes FMonolithBulkFillActions::RegisterAll fired at module startup. */
	static FMonolithActionResult Invoke(const TSharedPtr<FJsonObject>& Params)
	{
		return FMonolithToolRegistry::Get().ExecuteAction(TEXT("describe"), TEXT("action_schema"), Params);
	}
}

// ---------------------------------------------------------------------------
// Test 1: Canonical `target_action` resolves the schema successfully.
// We point it at `describe.list_targets` (an action this test module knows
// is always present because the BulkFillActions register pack ships it).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDescribeActionSchemaTargetActionTest,
	"Monolith.Describe.ActionSchema.TargetAction",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDescribeActionSchemaTargetActionTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDescribeActionSchemaTestDetail;

	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("target_namespace"), TEXT("describe"));
	Params->SetStringField(TEXT("target_action"), TEXT("list_targets"));

	const FMonolithActionResult R = Invoke(Params);
	TestTrue(TEXT("target_action canonical resolves successfully"), R.bSuccess);
	if (R.bSuccess && R.Result.IsValid())
	{
		FString Ns, Act;
		R.Result->TryGetStringField(TEXT("namespace"), Ns);
		R.Result->TryGetStringField(TEXT("action"), Act);
		TestEqual(TEXT("namespace echoes describe"), Ns, FString(TEXT("describe")));
		TestEqual(TEXT("action echoes list_targets"), Act, FString(TEXT("list_targets")));
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 2: Legacy `action` alias still works.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDescribeActionSchemaLegacyActionAliasTest,
	"Monolith.Describe.ActionSchema.LegacyActionAlias",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDescribeActionSchemaLegacyActionAliasTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDescribeActionSchemaTestDetail;

	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("target_namespace"), TEXT("describe"));
	Params->SetStringField(TEXT("action"), TEXT("list_targets"));

	const FMonolithActionResult R = Invoke(Params);
	TestTrue(TEXT("legacy `action` alias resolves successfully"), R.bSuccess);
	if (R.bSuccess && R.Result.IsValid())
	{
		FString Act;
		R.Result->TryGetStringField(TEXT("action"), Act);
		TestEqual(TEXT("action echoes list_targets"), Act, FString(TEXT("list_targets")));
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 3: Supplying BOTH `target_action` and `action` collides (K2 contract).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDescribeActionSchemaAliasCollisionTest,
	"Monolith.Describe.ActionSchema.AliasCollision",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDescribeActionSchemaAliasCollisionTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDescribeActionSchemaTestDetail;

	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	Params->SetStringField(TEXT("target_namespace"), TEXT("describe"));
	Params->SetStringField(TEXT("target_action"), TEXT("list_targets"));
	Params->SetStringField(TEXT("action"), TEXT("list_targets"));

	const FMonolithActionResult R = Invoke(Params);
	TestFalse(TEXT("collision must error, not succeed"), R.bSuccess);
	if (!R.bSuccess)
	{
		TestTrue(TEXT("error message mentions collision"),
			R.ErrorMessage.Contains(TEXT("collision")) ||
			R.ErrorMessage.Contains(TEXT("Param collision")));
	}
	return true;
}

// ---------------------------------------------------------------------------
// Test 4: Missing BOTH required params — error must list both at once
// (the original RI handover #6 friction was discovering missing params
// one round-trip at a time).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDescribeActionSchemaMissingBothTest,
	"Monolith.Describe.ActionSchema.MissingBoth",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDescribeActionSchemaMissingBothTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDescribeActionSchemaTestDetail;

	// Empty params — nothing supplied.
	TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
	const FMonolithActionResult R = Invoke(Params);

	TestFalse(TEXT("missing required params must error"), R.bSuccess);
	if (!R.bSuccess)
	{
		TestTrue(TEXT("error mentions target_namespace"),
			R.ErrorMessage.Contains(TEXT("target_namespace")));
		TestTrue(TEXT("error mentions target_action"),
			R.ErrorMessage.Contains(TEXT("target_action")));
	}
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
