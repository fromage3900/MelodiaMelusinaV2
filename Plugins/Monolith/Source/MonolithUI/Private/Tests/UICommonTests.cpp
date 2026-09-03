// Copyright tumourlove. All Rights Reserved.
#if WITH_DEV_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Math/Color.h"

#include "MonolithUICommon.h"

/**
 * MonolithUI.Common.ParseColor.Hex
 *
 * Verifies the legacy degamma path (FLinearColor(FColor) ctor) still produces
 * the expected channels for #RRGGBB / #RRGGBBAA inputs and survives whitespace
 * trim. Failure here means a regression in the hoisted helper relative to the
 * inline `MonolithUIInternal::ParseColor` it replaced.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIParseColorHexTest,
    "MonolithUI.Common.ParseColor.Hex",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIParseColorHexTest::RunTest(const FString& /*Parameters*/)
{
    // #FF8800 — legacy ParseColor uses FLinearColor(FColor) which applies sRGB
    // degamma. Verify the result is an FLinearColor whose pre-degamma R byte
    // round-trips back to 0xFF when re-encoded via .ToFColor(true).
    {
        const FLinearColor C = MonolithUI::ParseColor(TEXT("#FF8800"));
        const FColor RoundTrip = C.ToFColor(true);
        TestEqual(TEXT("#FF8800 R"), (int32)RoundTrip.R, 0xFF);
        TestEqual(TEXT("#FF8800 G"), (int32)RoundTrip.G, 0x88);
        TestEqual(TEXT("#FF8800 B"), (int32)RoundTrip.B, 0x00);
        TestEqual(TEXT("#FF8800 A"), (int32)RoundTrip.A, 0xFF);
    }

    // Leading/trailing whitespace must be trimmed.
    {
        const FLinearColor C = MonolithUI::ParseColor(TEXT("  #FF8800  "));
        const FColor RoundTrip = C.ToFColor(true);
        TestEqual(TEXT("trimmed #FF8800 R"), (int32)RoundTrip.R, 0xFF);
    }

    // Unrecognised input falls back to White (legacy behaviour).
    {
        const FLinearColor C = MonolithUI::ParseColor(TEXT("not-a-color"));
        TestEqual(TEXT("garbage R"), C.R, 1.0f);
        TestEqual(TEXT("garbage G"), C.G, 1.0f);
        TestEqual(TEXT("garbage B"), C.B, 1.0f);
        TestEqual(TEXT("garbage A"), C.A, 1.0f);
    }

    return true;
}

/**
 * MonolithUI.Common.TryParseColor.Hex
 *
 * Verifies the no-degamma sRGB pass-through path (R/255 division) used when
 * feeding MD_UI material parameters where the Slate shader applies its own
 * gamma correction. Failure here means MD_UI gradients/shadows will render
 * with washed-out colors.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUITryParseColorHexTest,
    "MonolithUI.Common.TryParseColor.Hex",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUITryParseColorHexTest::RunTest(const FString& /*Parameters*/)
{
    constexpr float Tolerance = 1.0f / 255.0f * 0.5f;

    // 6-digit hex.
    {
        FLinearColor C;
        TestTrue(TEXT("#FF8800 returns true"), MonolithUI::TryParseColor(TEXT("#FF8800"), C));
        TestEqual(TEXT("#FF8800 R"), C.R, 1.0f, Tolerance);
        TestEqual(TEXT("#FF8800 G"), C.G, 0x88 / 255.0f, Tolerance);
        TestEqual(TEXT("#FF8800 B"), C.B, 0.0f, Tolerance);
        TestEqual(TEXT("#FF8800 A"), C.A, 1.0f, Tolerance);
    }

    // 8-digit hex with explicit alpha.
    {
        FLinearColor C;
        TestTrue(TEXT("#FF8800AA returns true"), MonolithUI::TryParseColor(TEXT("#FF8800AA"), C));
        TestEqual(TEXT("#FF8800AA A"), C.A, 0xAA / 255.0f, Tolerance);
    }

    // 3-digit hex (FColor::FromHex expands to 6).
    {
        FLinearColor C;
        TestTrue(TEXT("#F80 returns true"), MonolithUI::TryParseColor(TEXT("#F80"), C));
        // FColor::FromHex("F80") expands to 0xFF8800FF (each nibble doubled).
        TestEqual(TEXT("#F80 R"), C.R, 1.0f, Tolerance);
        TestEqual(TEXT("#F80 G"), C.G, 0x88 / 255.0f, Tolerance);
        TestEqual(TEXT("#F80 B"), C.B, 0.0f, Tolerance);
    }

    // Comma-delimited 3-component float (alpha defaults to 1).
    {
        FLinearColor C;
        TestTrue(TEXT("1.0,0.5,0.25 returns true"), MonolithUI::TryParseColor(TEXT("1.0,0.5,0.25"), C));
        TestEqual(TEXT("R"), C.R, 1.0f, KINDA_SMALL_NUMBER);
        TestEqual(TEXT("G"), C.G, 0.5f, KINDA_SMALL_NUMBER);
        TestEqual(TEXT("B"), C.B, 0.25f, KINDA_SMALL_NUMBER);
        TestEqual(TEXT("A defaults"), C.A, 1.0f, KINDA_SMALL_NUMBER);
    }

    // Comma-delimited 4-component float.
    {
        FLinearColor C;
        TestTrue(TEXT("1,0.5,0.25,0.8 returns true"), MonolithUI::TryParseColor(TEXT("1,0.5,0.25,0.8"), C));
        TestEqual(TEXT("A"), C.A, 0.8f, KINDA_SMALL_NUMBER);
    }

    // Malformed strings return false and leave OutColor untouched.
    {
        FLinearColor C(0.123f, 0.456f, 0.789f, 0.42f);
        TestFalse(TEXT("garbage returns false"), MonolithUI::TryParseColor(TEXT("not-a-color"), C));
        TestEqual(TEXT("OutColor untouched R"), C.R, 0.123f, KINDA_SMALL_NUMBER);

        TestFalse(TEXT("empty returns false"), MonolithUI::TryParseColor(TEXT(""), C));
        TestFalse(TEXT("#XYZ wrong length"), MonolithUI::TryParseColor(TEXT("#XYZW"), C));
        TestFalse(TEXT("only one comma part"), MonolithUI::TryParseColor(TEXT("1.0,0.5"), C));
    }

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
