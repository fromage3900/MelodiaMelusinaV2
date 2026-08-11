// SPDX-License-Identifier: MIT
// RI ergonomics handover #9 (2026-05-29) — doc-vs-reality drift guard.
// Handover: Plugins/Monolith/Docs/plans/2026-05-29-ri-ergonomics-improvements-handover.md
//
// WHY THIS TEST EXISTS
// --------------------
// CHANGELOG.md / SPEC docs are hand-written and drift from the registered
// reality. This session caught TWO false claims by live test:
//   (a) CHANGELOG claimed `decision.list_decisions`'s `path_filter` "rewrites
//       `\` -> `/`" — it does NOT (it is a DiskPath, which is never rewritten).
//   (b) CHANGELOG claimed `project.audit_orphan_assets` exposes an
//       `AssetPath path_prefix` param — that param does not exist at all.
//
// This test asserts a SEED set of documented param claims against the LIVE
// registry (`FMonolithToolRegistry::Get().GetActions(namespace)` ->
// `FMonolithActionInfo::ParamSchema`). The ParamSchema is a flat JSON object of
//   param_name -> { "type": <string>, "required": <bool>, "kind"?: <string>, ... }
// exactly the shape `describe_query("action_schema")` returns as "params"
// (see MonolithBulkFillActions.cpp HandleDescribeActionSchema ~line 226). The
// `kind` field is emitted ONLY when non-default (Other) — see
// MonolithParamSchema.h AddParam (`SetStringField(TEXT("kind"), ...)`), and the
// dispatcher reads it back the same way at MonolithToolRegistry.cpp ~line 384.
//
// HOW TO EXTEND
// -------------
// Add a row to the GetSeedAssertions() table below for any action+param claim a
// doc makes that you want guarded. Each row is:
//   { Namespace, Action, ParamName, bShouldExist, ExpectedKind }
//     - bShouldExist == true  : the param MUST be present in the schema.
//     - bShouldExist == false : the param MUST be ABSENT (catches drift like the
//                               phantom `path_prefix` claim).
//     - ExpectedKind          : if non-empty AND bShouldExist, the `kind` field
//                               must equal this string ("DiskPath" / "AssetPath"
//                               / "GameplayTag"). Empty string = don't assert the
//                               kind (param existence only). A param with no
//                               `kind` field is treated as kind "Other".
// Keep this a SEED set focused on high-value / drift-prone claims, NOT an
// exhaustive mirror of every action — exhaustive coverage belongs in
// discover()-backed audits, not a compiled test.
//
// GATING
// ------
// The registry is only populated when modules load (editor running). This
// automation test runs inside the editor, so the registry IS populated. If a
// seed row names a namespace/action that is NOT registered (e.g. an optional-
// dependency-gated namespace that is off in this build), the row is SKIPPED with
// a logged note — never a hard failure — so the test stays green across build
// configs that omit optional deps.

#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "MonolithToolRegistry.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

namespace MonolithDocRealityTestDetail
{
	/** One documented claim about an action's param surface, asserted vs the live registry. */
	struct FDocClaim
	{
		const TCHAR* Namespace;
		const TCHAR* Action;
		const TCHAR* ParamName;
		bool         bShouldExist;
		const TCHAR* ExpectedKind; // "" = don't assert kind
	};

	/**
	 * SEED assertions — the handover-flagged high-value claims plus a couple of
	 * RI actions. Extend this table per the HOW TO EXTEND block at file top.
	 */
	static TArray<FDocClaim> GetSeedAssertions()
	{
		return {
			// (a) Handover drift bug #5 / CHANGELOG line ~11: `path_filter` is a
			//     DiskPath (never rewritten) — NOT an AssetPath. Assert it exists
			//     AND that its kind is exactly DiskPath, so a future flip to
			//     AssetPath (which WOULD rewrite) trips this test.
			{ TEXT("decision"), TEXT("list_decisions"), TEXT("path_filter"), true,  TEXT("DiskPath") },

			// (b) Handover drift bug #4 / CHANGELOG line ~51: `audit_orphan_assets`
			//     does NOT have a `path_prefix` param. Assert ABSENCE — this is the
			//     exact phantom-param claim that drifted. If someone re-adds the
			//     false doc claim without adding the param, this catches it; if they
			//     add the param for real, flip bShouldExist to true here.
			{ TEXT("project"),  TEXT("audit_orphan_assets"), TEXT("path_prefix"),       false, TEXT("") },
			// ...and assert the params that DO exist, so doc claims about them stay honest.
			{ TEXT("project"),  TEXT("audit_orphan_assets"), TEXT("asset_class_filter"), true,  TEXT("") },
			{ TEXT("project"),  TEXT("audit_orphan_assets"), TEXT("limit"),              true,  TEXT("") },
			{ TEXT("project"),  TEXT("audit_orphan_assets"), TEXT("cursor"),             true,  TEXT("") },

			// A couple more RI actions whose path params are documented as DiskPath.
			{ TEXT("risk"),     TEXT("list_conditional_gates"), TEXT("path_filter"),     true,  TEXT("DiskPath") },
			{ TEXT("risk"),     TEXT("get_hotspot_score"),      TEXT("file_path"),       true,  TEXT("DiskPath") },
		};
	}

	/** Locate an action in the live registry. Returns nullptr if the namespace/action is not registered. */
	static const FMonolithActionInfo* FindAction(const FString& Namespace, const FString& Action,
		TArray<FMonolithActionInfo>& OutActionsHolder)
	{
		OutActionsHolder = FMonolithToolRegistry::Get().GetActions(Namespace);
		return OutActionsHolder.FindByPredicate(
			[&Action](const FMonolithActionInfo& Info){ return Info.Action == Action; });
	}

	/** Read the `kind` of a param from a ParamSchema JSON object. "" if the param or kind field is absent. */
	static FString ReadParamKind(const TSharedPtr<FJsonObject>& Schema, const FString& ParamName)
	{
		if (!Schema.IsValid()) { return FString(); }
		const TSharedPtr<FJsonValue> ParamVal = Schema->TryGetField(ParamName);
		if (!ParamVal.IsValid()) { return FString(); }
		const TSharedPtr<FJsonObject>* ParamObj = nullptr;
		if (!ParamVal->TryGetObject(ParamObj) || !ParamObj || !ParamObj->IsValid()) { return FString(); }
		FString Kind;
		(*ParamObj)->TryGetStringField(TEXT("kind"), Kind);
		return Kind; // empty => no kind tag => Other (default)
	}

	static bool ParamExists(const TSharedPtr<FJsonObject>& Schema, const FString& ParamName)
	{
		return Schema.IsValid() && Schema->HasField(ParamName);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithDocRealityDriftTest,
	"Monolith.ReflectionIntel.DocRealityDrift",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithDocRealityDriftTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithDocRealityTestDetail;

	const TArray<FDocClaim> Claims = GetSeedAssertions();
	int32 Asserted = 0;
	int32 Skipped  = 0;

	for (const FDocClaim& Claim : Claims)
	{
		const FString Namespace(Claim.Namespace);
		const FString Action(Claim.Action);
		const FString ParamName(Claim.ParamName);

		TArray<FMonolithActionInfo> ActionsHolder;
		const FMonolithActionInfo* Found = FindAction(Namespace, Action, ActionsHolder);

		// Not registered (e.g. optional-dep-gated namespace off this build) -> SKIP, never fail.
		if (Found == nullptr)
		{
			AddInfo(FString::Printf(
				TEXT("SKIP: %s.%s is not registered in this build — skipping the '%s' claim."),
				*Namespace, *Action, *ParamName));
			++Skipped;
			continue;
		}

		const TSharedPtr<FJsonObject>& Schema = Found->ParamSchema;
		const bool bExists = ParamExists(Schema, ParamName);

		if (Claim.bShouldExist)
		{
			TestTrue(FString::Printf(
				TEXT("DOC DRIFT: %s.%s should expose param '%s' but the live registry has no such param."),
				*Namespace, *Action, *ParamName), bExists);

			const FString ExpectedKind(Claim.ExpectedKind);
			if (bExists && !ExpectedKind.IsEmpty())
			{
				const FString ActualKind = ReadParamKind(Schema, ParamName);
				const FString ActualKindDisplay = ActualKind.IsEmpty() ? TEXT("Other(no-kind)") : ActualKind;
				TestEqual(FString::Printf(
					TEXT("DOC DRIFT: %s.%s param '%s' kind mismatch — doc asserts '%s', registry has '%s'."),
					*Namespace, *Action, *ParamName, *ExpectedKind, *ActualKindDisplay),
					ActualKind, ExpectedKind);
			}
		}
		else
		{
			TestFalse(FString::Printf(
				TEXT("DOC DRIFT: %s.%s must NOT expose param '%s' (phantom doc claim) but the registry has it."),
				*Namespace, *Action, *ParamName), bExists);
		}
		++Asserted;
	}

	AddInfo(FString::Printf(
		TEXT("DocRealityDrift: %d claim(s) asserted, %d skipped (unregistered)."),
		Asserted, Skipped));

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
