// Copyright tumourlove. All Rights Reserved.

// =============================================================================
// MonolithFixHintsTests.cpp
//
// Phase 3 (item 8) regression test for the ADDITIVE fix_hints extension on
// editor::get_build_errors (plan: 2026-06-10-llm-cpp-ergonomics-actions.md).
//
// FixHintsAdditive: synthesise error objects (LNK2019 on Z_Construct_*, a C4996
// line, a generated.h-last line, a DeveloperSettings LNK2019) and assert:
//   1. BuildFixHints returns a non-empty fix_hints[] naming the relevant fix.
//   2. The pre-existing fields on each error object (message/category/verbosity)
//      are BYTE-IDENTICAL before and after BuildFixHints — additive only. The
//      only added field is `fix_hint`.
//
// BuildFixHints reads the borrowed source DB when available, but the additive-
// contract assertions hold whether or not the DB resolves an owning module
// (the generic hint fallback still fires). The test does NOT require an indexed
// EngineSource.db.
// =============================================================================

#if WITH_DEV_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

#include "MonolithEditorActions.h"

namespace MonolithFixHintsTests
{
	/** Build one synthetic error object matching the per-error shape
	 *  HandleGetBuildErrors emits (message/category/verbosity — see
	 *  MonolithEditorActions.cpp MakeEntryObj). Named MakeErrorObj (NOT MakeError)
	 *  to avoid colliding with the engine's global MakeError template
	 *  (Templates/ValueOrError.h), which `using namespace` would otherwise drag
	 *  into unqualified lookup and trigger a C2665 ambiguity. */
	static TSharedPtr<FJsonObject> MakeErrorObj(const FString& Message, const FString& Category)
	{
		TSharedPtr<FJsonObject> O = MakeShared<FJsonObject>();
		O->SetStringField(TEXT("message"), Message);
		O->SetStringField(TEXT("category"), Category);
		O->SetStringField(TEXT("verbosity"), TEXT("Error"));
		return O;
	}

	/** Serialize an object's pre-existing fields (everything EXCEPT fix_hint) to a
	 *  stable string for byte-identical comparison. */
	static FString SerializeWithoutFixHint(const TSharedPtr<FJsonObject>& Obj)
	{
		TSharedPtr<FJsonObject> Copy = MakeShared<FJsonObject>();
		for (const auto& Pair : Obj->Values)
		{
			if (Pair.Key == TEXT("fix_hint")) { continue; }
			Copy->SetField(Pair.Key, Pair.Value);
		}
		FString Out;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Out);
		FJsonSerializer::Serialize(Copy.ToSharedRef(), Writer);
		return Out;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithFixHintsAdditiveTest,
	"Monolith.Editor.FixHints.Additive",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithFixHintsAdditiveTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithFixHintsTests;

	// Synthesise the error objects. The LNK2019 message embeds a Z_Construct_UClass_
	// symbol; the type name need not resolve in the DB (generic hint fallback fires).
	TArray<TSharedPtr<FJsonObject>> Errors;
	Errors.Add(MakeErrorObj(
		TEXT("error LNK2019: unresolved external symbol \"Z_Construct_UClass_UNiagaraSystem_NoRegister\" referenced in function ..."),
		TEXT("LogLinker")));
	Errors.Add(MakeErrorObj(
		TEXT("warning C4996: 'UWorld::GetGameInstance': was declared deprecated"),
		TEXT("LogCompile")));
	Errors.Add(MakeErrorObj(
		TEXT("error: '#include' of a 'generated.h' must be the last include in a header file"),
		TEXT("LogCompile")));
	Errors.Add(MakeErrorObj(
		TEXT("error LNK2019: unresolved external symbol referencing UDeveloperSettings::GetContainerName"),
		TEXT("LogLinker")));
	Errors.Add(MakeErrorObj(
		TEXT("Some unrelated error with no matching pattern"),
		TEXT("LogCompile")));

	// Snapshot the pre-existing fields BEFORE calling BuildFixHints.
	TArray<FString> Before;
	TArray<TSharedPtr<FJsonValue>> ErrorVals;
	for (const TSharedPtr<FJsonObject>& E : Errors)
	{
		Before.Add(SerializeWithoutFixHint(E));
		ErrorVals.Add(MakeShared<FJsonValueObject>(E));
	}

	// Run the additive hint builder.
	TArray<TSharedPtr<FJsonValue>> Hints = FMonolithEditorActions::BuildFixHints(ErrorVals);

	// At least the LNK2019/Z_Construct, C4996, generated.h-last, and DeveloperSettings
	// patterns must produce hints (4 of the 5 errors; the 5th matches nothing).
	TestTrue(TEXT("fix_hints non-empty"), Hints.Num() >= 4);

	// Collect the matched patterns.
	TSet<FString> Patterns;
	for (const TSharedPtr<FJsonValue>& V : Hints)
	{
		const TSharedPtr<FJsonObject>* O = nullptr;
		if (V->TryGetObject(O) && O)
		{
			FString P;
			(*O)->TryGetStringField(TEXT("pattern"), P);
			Patterns.Add(P);
			// Every hint has a non-empty hint string + an error_index.
			FString HintStr;
			TestTrue(TEXT("hint has text"), (*O)->TryGetStringField(TEXT("hint"), HintStr) && !HintStr.IsEmpty());
			TestTrue(TEXT("hint has error_index"), (*O)->HasField(TEXT("error_index")));
		}
	}
	TestTrue(TEXT("LNK2019_Z_Construct matched"), Patterns.Contains(TEXT("LNK2019_Z_Construct")));
	TestTrue(TEXT("C4996_deprecation matched"), Patterns.Contains(TEXT("C4996_deprecation")));
	TestTrue(TEXT("generated_h_not_last matched"), Patterns.Contains(TEXT("generated_h_not_last")));
	TestTrue(TEXT("LNK2019_DeveloperSettings matched"), Patterns.Contains(TEXT("LNK2019_DeveloperSettings")));

	// BYTE-IDENTICAL regression guard: the pre-existing fields are unchanged. The
	// only mutation BuildFixHints may make is ADDING a `fix_hint` field.
	for (int32 i = 0; i < Errors.Num(); ++i)
	{
		const FString After = SerializeWithoutFixHint(Errors[i]);
		TestEqual(FString::Printf(TEXT("error[%d] pre-existing fields byte-identical"), i), After, Before[i]);
	}

	// The unmatched error must NOT have gained a fix_hint.
	TestFalse(TEXT("unmatched error has no fix_hint"), Errors[4]->HasField(TEXT("fix_hint")));
	// A matched error DID gain a fix_hint.
	TestTrue(TEXT("matched error gained fix_hint"), Errors[0]->HasField(TEXT("fix_hint")));

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
