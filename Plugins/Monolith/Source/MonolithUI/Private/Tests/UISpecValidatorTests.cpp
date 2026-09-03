// Copyright tumourlove. All Rights Reserved.
#if WITH_DEV_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

#include "Spec/UISpec.h"
#include "Spec/UISpecValidator.h"

/**
 * MonolithUI.SpecValidator.Empty
 *
 * Feeds the validator an empty JSON object `{}` and asserts that:
 *   * bIsValid is false.
 *   * Exactly one Error-severity finding is produced.
 *   * The finding's JsonPath points at the missing root.
 *   * The category is "Structure" (not "Parse" — parsing succeeded; the
 *     document was just empty).
 *
 * This is the smoke test for the Phase A validator skeleton. Subsequent
 * phases extend the validator with type-registry and allowlist checks; new
 * tests live alongside them rather than crowding this file.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUISpecValidatorEmptyTest,
    "MonolithUI.SpecValidator.Empty",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUISpecValidatorEmptyTest::RunTest(const FString& /*Parameters*/)
{
    const FUISpecValidationResult Result = FUISpecValidator::ValidateFromJson(TEXT("{}"));

    TestFalse(TEXT("Empty {} document is invalid"), Result.bIsValid);
    TestEqual(TEXT("Empty {} document yields exactly one error"), Result.Errors.Num(), 1);
    TestEqual(TEXT("Empty {} document yields zero warnings"), Result.Warnings.Num(), 0);

    if (Result.Errors.Num() == 1)
    {
        const FUISpecError& Err = Result.Errors[0];
        TestEqual(TEXT("Error category is Structure"), Err.Category, FName(TEXT("Structure")));
        TestEqual(TEXT("Error JsonPath points at /rootWidget"), Err.JsonPath, FString(TEXT("/rootWidget")));
        TestEqual(TEXT("Error severity is Error"), Err.Severity, EUISpecErrorSeverity::Error);
    }

    // Direct-document path: a default-constructed FUISpecDocument also has no
    // root and must produce the same Error finding.
    {
        FUISpecDocument Doc;
        const FUISpecValidationResult R2 = FUISpecValidator::Validate(Doc);
        TestFalse(TEXT("Default-constructed FUISpecDocument is invalid"), R2.bIsValid);
        TestEqual(TEXT("Default-constructed yields one error"), R2.Errors.Num(), 1);
    }

    // Whitespace / empty-string input is treated as missing-root, not a parse
    // error — keeps the LLM-facing surface predictable.
    {
        const FUISpecValidationResult R3 = FUISpecValidator::ValidateFromJson(TEXT("   "));
        TestFalse(TEXT("Whitespace-only input is invalid"), R3.bIsValid);
        TestEqual(TEXT("Whitespace-only input yields one error"), R3.Errors.Num(), 1);
        if (R3.Errors.Num() == 1)
        {
            TestEqual(TEXT("Whitespace error category is Structure"),
                R3.Errors[0].Category, FName(TEXT("Structure")));
        }
    }

    return true;
}

/**
 * MonolithUI.SpecValidator.MalformedJson
 *
 * Feeds the validator obviously malformed JSON and asserts the error path
 * surfaces a "Parse" category finding (not "Structure"). The line/column
 * fields are populated where the JSON deserializer can supply them.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUISpecValidatorMalformedJsonTest,
    "MonolithUI.SpecValidator.MalformedJson",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUISpecValidatorMalformedJsonTest::RunTest(const FString& /*Parameters*/)
{
    const FUISpecValidationResult Result = FUISpecValidator::ValidateFromJson(TEXT("{ this is not json"));

    TestFalse(TEXT("Malformed JSON is invalid"), Result.bIsValid);
    TestTrue(TEXT("Malformed JSON yields at least one error"), Result.Errors.Num() >= 1);
    if (Result.Errors.Num() >= 1)
    {
        TestEqual(TEXT("Parse error category"),
            Result.Errors[0].Category, FName(TEXT("Parse")));
    }

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
