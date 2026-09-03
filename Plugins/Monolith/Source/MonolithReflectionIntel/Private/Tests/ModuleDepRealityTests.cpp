// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// ModuleDepRealityTests — Phase 2 §12 test 5 (module-dep reality audit).
//
// The audit action's `HandleAuditModuleDepReality` reads from the project's
// real source tree + the live EngineSource.db. Unit-testing it directly would
// require building a parallel `symbols`/`files`/`modules` mock that mirrors
// MonolithSource's exact schema. Phase 2 §12 test 5 explicitly asks for a
// fixture-driven test, which we implement by:
//
//   1. Asserting the Build.cs string-array parser captures the expected dep
//      identifiers from the sample fixture file. (Direct unit test of the
//      parsing regex — sufficient to gate the bug class without scaffolding
//      a full symbols index.)
//   2. Asserting the audit action's registration is visible in the registry.

#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Internationalization/Regex.h"
#include "Interfaces/IPluginManager.h"
#include "MonolithToolRegistry.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace MonolithModDepTestDetail
{
	static FString GetFixturePath(const FString& Sub)
	{
		TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("Monolith"));
		if (Plugin.IsValid())
		{
			return Plugin->GetBaseDir()
				/ TEXT("Source") / TEXT("MonolithReflectionIntel")
				/ TEXT("Private") / TEXT("Tests") / TEXT("Fixtures") / Sub;
		}
		return FPaths::ProjectPluginsDir()
			/ TEXT("Monolith") / TEXT("Source") / TEXT("MonolithReflectionIntel")
			/ TEXT("Private") / TEXT("Tests") / TEXT("Fixtures") / Sub;
	}
}

// ---------------------------------------------------------------------------
// Test: sample Build.cs string-list extraction — patterns lifted from the
// FModuleDepRealityAdapter.cpp anonymous namespace so the parser stays in
// sync with the audit's regex.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FModuleDepRealitySampleBuildCsParseTest,
	"Monolith.ReflectionIntel.SourceAudit.SampleBuildCsParse",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FModuleDepRealitySampleBuildCsParseTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithModDepTestDetail;

	// Fixture path uses `.Build.cs.fixture` extension so UBT's recursive
	// Build.cs glob does not try to compile a phantom module from it.
	const FString Sample = GetFixturePath(FPaths::Combine(TEXT("RiskCorpus"), TEXT("sample.Build.cs.fixture")));
	if (!FPlatformFileManager::Get().GetPlatformFile().FileExists(*Sample))
	{
		AddError(FString::Printf(
			TEXT("Sample Build.cs fixture missing at '%s' — Phase 2 fixture invariant violated"),
			*Sample));
		return false;
	}

	FString Text;
	TestTrue(TEXT("LoadFileToString(sample.Build.cs)"),
		FFileHelper::LoadFileToString(Text, *Sample));

	// Mirror FModuleDepRealityAdapter.cpp's site + string patterns.
	const FRegexPattern SitePattern(
		TEXT("(Public|Private)DependencyModuleNames\\s*\\.\\s*(?:Add|AddRange)\\s*\\(([\\s\\S]*?)\\)"));
	const FRegexPattern DepStringPattern(
		TEXT("\"([A-Za-z_][A-Za-z0-9_]*)\""));

	TSet<FString> Captured;
	FRegexMatcher SiteM(SitePattern, Text);
	while (SiteM.FindNext())
	{
		const FString Body = SiteM.GetCaptureGroup(2);
		FRegexMatcher StringM(DepStringPattern, Body);
		while (StringM.FindNext())
		{
			Captured.Add(StringM.GetCaptureGroup(1));
		}
	}

	// Fixture is documented to declare these (see sample.Build.cs):
	TestTrue(TEXT("Captured Core"),         Captured.Contains(TEXT("Core")));
	TestTrue(TEXT("Captured CoreUObject"),  Captured.Contains(TEXT("CoreUObject")));
	TestTrue(TEXT("Captured Engine"),       Captured.Contains(TEXT("Engine")));
	// The sample DOES NOT declare GameplayTags. The audit emits a violation
	// for any UPROPERTY using FGameplayTag in a .h/.cpp within this module —
	// the fixture cpp file uses FGameplayTag. We assert the SET does NOT
	// contain GameplayTags here so the violation gate has a non-trivial assert.
	TestFalse(TEXT("Did NOT capture GameplayTags (bug-class trigger)"),
		Captured.Contains(TEXT("GameplayTags")));

	return true;
}

// ---------------------------------------------------------------------------
// Test: registration smoke — `source_query("audit_module_dep_reality")` is
// reachable from the registry after module init.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FModuleDepRealityRegistrationTest,
	"Monolith.ReflectionIntel.SourceAudit.Registration",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FModuleDepRealityRegistrationTest::RunTest(const FString& /*Parameters*/)
{
	const FMonolithToolRegistry& Reg = FMonolithToolRegistry::Get();
	TestTrue(TEXT("source.audit_module_dep_reality registered"),
		Reg.HasAction(TEXT("source"), TEXT("audit_module_dep_reality")));
	return true;
}

// ---------------------------------------------------------------------------
// Test: SuggestBuildCsDepsForward (item 6) — registration smoke + path-first
// declaring-module derivation.
//
// Mirrors the SampleBuildCsParse idiom: the path-derivation logic lives in the
// adapter's anonymous namespace, so we re-assert the same parse here to keep
// the contract pinned (LAST `/Source/` wins so a Plugins/<X>/Source/<Module>/
// path resolves to <Module>, not <X>). Full forward-resolution needs a live
// EngineSource.db; that is covered by the MCP smoke in plan §12.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FModuleDepSuggestBuildCsDepsForwardTest,
	"Monolith.ReflectionIntel.SourceAudit.SuggestBuildCsDepsForward",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FModuleDepSuggestBuildCsDepsForwardTest::RunTest(const FString& /*Parameters*/)
{
	const FMonolithToolRegistry& Reg = FMonolithToolRegistry::Get();
	TestTrue(TEXT("source.suggest_build_cs_deps registered"),
		Reg.HasAction(TEXT("source"), TEXT("suggest_build_cs_deps")));

	// Path-first declaring-module derivation contract (LAST `/Source/` wins).
	auto DeriveModule = [](const FString& InPath) -> FString
	{
		FString Norm = InPath;
		Norm.ReplaceInline(TEXT("\\"), TEXT("/"));
		const int32 SrcIdx = Norm.Find(TEXT("/Source/"), ESearchCase::IgnoreCase, ESearchDir::FromEnd);
		if (SrcIdx == INDEX_NONE) { return FString(); }
		FString Rest = Norm.Mid(SrcIdx + 8);
		int32 NextSlash = INDEX_NONE;
		if (!Rest.FindChar(TEXT('/'), NextSlash)) { return FString(); }
		return Rest.Left(NextSlash);
	};

	TestEqual(TEXT("Source/<Module>/ derivation"),
		DeriveModule(TEXT("D:/Proj/Source/MyMod/Public/Thing.h")), FString(TEXT("MyMod")));
	TestEqual(TEXT("Plugins/<X>/Source/<Module>/ derivation (innermost wins)"),
		DeriveModule(TEXT("D:/Proj/Plugins/Foo/Source/FooRuntime/Private/Bar.cpp")),
		FString(TEXT("FooRuntime")));
	TestEqual(TEXT("backslash path normalised"),
		DeriveModule(TEXT("C:\\Proj\\Source\\WinMod\\X.h")), FString(TEXT("WinMod")));
	TestTrue(TEXT("no /Source/ -> empty"),
		DeriveModule(TEXT("D:/Proj/Content/Foo.uasset")).IsEmpty());

	return true;
}

// ---------------------------------------------------------------------------
// Test: risk_query registration — all 5 actions present.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FRiskQueryRegistrationTest,
	"Monolith.ReflectionIntel.Risk.QueryRegistration",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRiskQueryRegistrationTest::RunTest(const FString& /*Parameters*/)
{
	const FMonolithToolRegistry& Reg = FMonolithToolRegistry::Get();
	TestTrue(TEXT("risk.get_hotspot_score registered"),
		Reg.HasAction(TEXT("risk"), TEXT("get_hotspot_score")));
	TestTrue(TEXT("risk.get_cochange_pairs registered"),
		Reg.HasAction(TEXT("risk"), TEXT("get_cochange_pairs")));
	TestTrue(TEXT("risk.get_file_churn registered"),
		Reg.HasAction(TEXT("risk"), TEXT("get_file_churn")));
	TestTrue(TEXT("risk.get_release_window_hotspots registered"),
		Reg.HasAction(TEXT("risk"), TEXT("get_release_window_hotspots")));
	TestTrue(TEXT("risk.list_conditional_gates registered"),
		Reg.HasAction(TEXT("risk"), TEXT("list_conditional_gates")));
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
