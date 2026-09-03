// Copyright tumourlove. All Rights Reserved.
#if WITH_DEV_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

#include "Registry/MonolithUIRegistrySubsystem.h"
#include "Registry/UIPropertyAllowlist.h"
#include "Registry/UITypeRegistry.h"

/**
 * MonolithUI.Allowlist.VerticalBoxSlotPaddingAllowed (B4)
 *
 * After registry init + curated mappings, the allowlist must say:
 *   * ("VerticalBox", "Slot.Padding") -> true
 *   * ("VerticalBox", "Slot.RawTransientFlag") -> false
 *
 * This validates the projection-over-PropertyMappings build path and the
 * "unknown path defaults to deny" rule that gates Phase C's reflection helper.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAllowlistVerticalBoxSlotPaddingTest,
    "MonolithUI.Allowlist.VerticalBoxSlotPaddingAllowed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAllowlistVerticalBoxSlotPaddingTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const FUIPropertyAllowlist& Allowlist = Sub->GetAllowlist();

    TestTrue(TEXT("VerticalBox.Slot.Padding is allowed"),
        Allowlist.IsAllowed(FName(TEXT("VerticalBox")), TEXT("Slot.Padding")));

    TestFalse(TEXT("VerticalBox.Slot.RawTransientFlag is denied"),
        Allowlist.IsAllowed(FName(TEXT("VerticalBox")), TEXT("Slot.RawTransientFlag")));

    return true;
}

/**
 * MonolithUI.Allowlist.UnknownTypeDenied
 *
 * A widget token that is not in the registry must deny every property path.
 * This is the safe-default behaviour — unknown widget classes get no writes.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAllowlistUnknownTypeDeniedTest,
    "MonolithUI.Allowlist.UnknownTypeDenied",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAllowlistUnknownTypeDeniedTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const FUIPropertyAllowlist& Allowlist = Sub->GetAllowlist();
    const FName Bogus = FName(TEXT("WidgetThatDoesNotExist_91827463"));

    TestFalse(TEXT("Unknown widget rejects Slot.Padding"),
        Allowlist.IsAllowed(Bogus, TEXT("Slot.Padding")));
    TestFalse(TEXT("Unknown widget rejects Text"),
        Allowlist.IsAllowed(Bogus, TEXT("Text")));

    // GetAllowedPaths returns an empty (not null) array.
    TestEqual(TEXT("Unknown widget has empty allowed-paths list"),
        Allowlist.GetAllowedPaths(Bogus).Num(), 0);

    return true;
}

/**
 * MonolithUI.Allowlist.TextBlockTextAllowed
 *
 * TextBlock.Text is a curated mapping — should be allowed. Sanity-check on
 * the leaf-widget mapping path.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAllowlistTextBlockTextTest,
    "MonolithUI.Allowlist.TextBlockTextAllowed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAllowlistTextBlockTextTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const FUIPropertyAllowlist& Allowlist = Sub->GetAllowlist();

    TestTrue(TEXT("TextBlock.Text is allowed"),
        Allowlist.IsAllowed(FName(TEXT("TextBlock")), TEXT("Text")));
    TestTrue(TEXT("TextBlock.ColorAndOpacity is allowed"),
        Allowlist.IsAllowed(FName(TEXT("TextBlock")), TEXT("ColorAndOpacity")));
    TestTrue(TEXT("TextBlock.LineHeightPercentage is allowed"),
        Allowlist.IsAllowed(FName(TEXT("TextBlock")), TEXT("LineHeightPercentage")));
    TestTrue(TEXT("TextBlock.ApplyLineHeightToBottomLine is allowed"),
        Allowlist.IsAllowed(FName(TEXT("TextBlock")), TEXT("ApplyLineHeightToBottomLine")));
    TestFalse(TEXT("TextBlock.PrivateInternalCache is denied"),
        Allowlist.IsAllowed(FName(TEXT("TextBlock")), TEXT("PrivateInternalCache")));

    return true;
}

/**
 * MonolithUI.Allowlist.RoundedBorderCuratedMappings (B6)
 *
 * URoundedBorder lives in the optional EffectSurface provider lineage. The
 * Phase B curated mappings should already
 * cover CornerRadii / OutlineColor / OutlineWidth / FillColor + inherited
 * Border properties + standard slot mappings.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAllowlistRoundedBorderTest,
    "MonolithUI.Allowlist.RoundedBorderCuratedMappings",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAllowlistRoundedBorderTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const FUITypeRegistry& Registry = Sub->GetTypeRegistry();
    const FUITypeRegistryEntry* RoundedEntry = Registry.FindByToken(FName(TEXT("RoundedBorder")));

    if (!RoundedEntry)
    {
        // Optional provider not loaded in this test target -- skip cleanly.
        AddInfo(TEXT("RoundedBorder not registered (optional provider not loaded in this test target) -- skipping curated-mapping check"));
        return true;
    }

    const FUIPropertyAllowlist& Allowlist = Sub->GetAllowlist();
    const FName Token = FName(TEXT("RoundedBorder"));

    TestTrue(TEXT("RoundedBorder.CornerRadii allowed"),
        Allowlist.IsAllowed(Token, TEXT("CornerRadii")));
    TestTrue(TEXT("RoundedBorder.OutlineColor allowed"),
        Allowlist.IsAllowed(Token, TEXT("OutlineColor")));
    TestTrue(TEXT("RoundedBorder.OutlineWidth allowed"),
        Allowlist.IsAllowed(Token, TEXT("OutlineWidth")));
    TestTrue(TEXT("RoundedBorder.FillColor allowed"),
        Allowlist.IsAllowed(Token, TEXT("FillColor")));
    TestTrue(TEXT("RoundedBorder.Background (inherited) allowed"),
        Allowlist.IsAllowed(Token, TEXT("Background")));
    TestTrue(TEXT("RoundedBorder.Slot.Padding allowed"),
        Allowlist.IsAllowed(Token, TEXT("Slot.Padding")));

    return true;
}

/**
 * MonolithUI.Allowlist.InvalidationDropsCache
 *
 * `Invalidate()` should drop the cache; subsequent IsAllowed call should
 * rebuild and still return the correct answer.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAllowlistInvalidationTest,
    "MonolithUI.Allowlist.InvalidationDropsCache",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAllowlistInvalidationTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    // Force the cache to populate.
    const FUIPropertyAllowlist& Allowlist = Sub->GetAllowlist();
    TestTrue(TEXT("Pre-invalidate: Slot.Padding allowed"),
        Allowlist.IsAllowed(FName(TEXT("VerticalBox")), TEXT("Slot.Padding")));

    // Drive a re-scan which invalidates the allowlist as a side-effect.
    Sub->RescanWidgetTypes();

    // Cache must have rebuilt — same query still passes.
    TestTrue(TEXT("Post-rescan: Slot.Padding still allowed"),
        Allowlist.IsAllowed(FName(TEXT("VerticalBox")), TEXT("Slot.Padding")));

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
