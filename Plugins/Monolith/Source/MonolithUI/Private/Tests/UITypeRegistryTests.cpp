// Copyright tumourlove. All Rights Reserved.
#if WITH_DEV_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

#include "Components/PanelWidget.h"
#include "Components/VerticalBox.h"
#include "Components/Border.h"
#include "Components/TextBlock.h"
#include "Registry/MonolithUIRegistrySubsystem.h"
#include "Registry/UITypeRegistry.h"

/**
 * MonolithUI.Registry.KnowsVerticalBox
 *
 * Smoke test for B1 — after the editor subsystem's `Initialize()` (or a
 * forced `RescanWidgetTypes`), the registry must:
 *   * have an entry for token "VerticalBox"
 *   * with WidgetClass == UVerticalBox::StaticClass()
 *   * with ContainerKind == Panel
 *   * with MaxChildren == -1 (unbounded panel)
 *
 * Subsystem retrieval: `UMonolithUIRegistrySubsystem::Get()` returns null in
 * a non-editor context — the test guards on that and skips with a clear
 * message rather than asserting a null deref. Since the test flag forces
 * EditorContext, GEditor is expected to be live.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIRegistryKnowsVerticalBoxTest,
    "MonolithUI.Registry.KnowsVerticalBox",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIRegistryKnowsVerticalBoxTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available in editor context"), Sub))
    {
        return false;
    }

    const FUITypeRegistry& Registry = Sub->GetTypeRegistry();
    const FUITypeRegistryEntry* Entry = Registry.FindByToken(FName(TEXT("VerticalBox")));

    if (!TestNotNull(TEXT("Registry has VerticalBox entry"), Entry))
    {
        return false;
    }

    TestEqual(TEXT("Token matches"), Entry->Token, FName(TEXT("VerticalBox")));
    TestTrue(TEXT("WidgetClass is UVerticalBox"), Entry->WidgetClass.Get() == UVerticalBox::StaticClass());
    TestTrue(TEXT("ContainerKind is Panel"), Entry->ContainerKind == EUIContainerKind::Panel);
    TestEqual(TEXT("MaxChildren is -1 (unbounded)"), Entry->MaxChildren, -1);

    return true;
}

/**
 * MonolithUI.Registry.AbstractClassesFiltered (B10a)
 *
 * UPanelWidget itself is `UCLASS(Abstract, MinimalAPI)` — the reflection
 * walk MUST skip it. Same goes for any UCLASS(Abstract) UMG class. We
 * additionally probe UContentWidget which is also abstract.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIRegistryAbstractFilteredTest,
    "MonolithUI.Registry.AbstractClassesFiltered",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIRegistryAbstractFilteredTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const FUITypeRegistry& Registry = Sub->GetTypeRegistry();

    // UPanelWidget — abstract base. Token derived from class name.
    TestNull(TEXT("Abstract UPanelWidget is filtered out (PanelWidget token)"),
        Registry.FindByToken(FName(TEXT("PanelWidget"))));

    // UContentWidget — abstract.
    TestNull(TEXT("Abstract UContentWidget is filtered out (ContentWidget token)"),
        Registry.FindByToken(FName(TEXT("ContentWidget"))));

    // UWidget itself — base of the hierarchy. We explicitly skip it in the walk.
    TestNull(TEXT("UWidget base is filtered out (Widget token)"),
        Registry.FindByToken(FName(TEXT("Widget"))));

    return true;
}

/**
 * MonolithUI.Registry.ContentWidgetSingleChild
 *
 * UBorder (UContentWidget descendant) must classify as Content with
 * MaxChildren == 1. Sanity check on the classifier's order-sensitive
 * UContentWidget-before-UPanelWidget check.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIRegistryContentWidgetSingleChildTest,
    "MonolithUI.Registry.ContentWidgetSingleChild",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIRegistryContentWidgetSingleChildTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const FUITypeRegistryEntry* Border = Sub->GetTypeRegistry().FindByToken(FName(TEXT("Border")));
    if (!TestNotNull(TEXT("Registry has Border entry"), Border))
    {
        return false;
    }

    TestTrue(TEXT("Border is Content kind"), Border->ContainerKind == EUIContainerKind::Content);
    TestEqual(TEXT("Border MaxChildren is 1"), Border->MaxChildren, 1);
    TestTrue(TEXT("Border WidgetClass is UBorder"), Border->WidgetClass.Get() == UBorder::StaticClass());

    return true;
}

/**
 * MonolithUI.Registry.LeafWidgetClassified
 *
 * UTextBlock — leaf widget, no children. ContainerKind = Leaf, MaxChildren = 0.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIRegistryLeafClassifiedTest,
    "MonolithUI.Registry.LeafWidgetClassified",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIRegistryLeafClassifiedTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const FUITypeRegistryEntry* Text = Sub->GetTypeRegistry().FindByToken(FName(TEXT("TextBlock")));
    if (!TestNotNull(TEXT("Registry has TextBlock entry"), Text))
    {
        return false;
    }

    TestTrue(TEXT("TextBlock is Leaf kind"), Text->ContainerKind == EUIContainerKind::Leaf);
    TestEqual(TEXT("TextBlock MaxChildren is 0"), Text->MaxChildren, 0);

    return true;
}

/**
 * MonolithUI.Registry.RescanIdempotent (B10b prep)
 *
 * Calling `RescanWidgetTypes` twice in a row produces the same registry
 * size. This is the precondition for the OnPostEngineInit re-scan being
 * safe to run after the initial Initialize walk — re-registering an
 * existing entry must overwrite, not duplicate.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIRegistryRescanIdempotentTest,
    "MonolithUI.Registry.RescanIdempotent",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIRegistryRescanIdempotentTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const int32 BaselineCount = Sub->GetTypeRegistry().Num();

    Sub->RescanWidgetTypes();
    const int32 AfterFirstRescan = Sub->GetTypeRegistry().Num();

    Sub->RescanWidgetTypes();
    const int32 AfterSecondRescan = Sub->GetTypeRegistry().Num();

    TestEqual(TEXT("Registry size stable across rescans (1)"), AfterFirstRescan, BaselineCount);
    TestEqual(TEXT("Registry size stable across rescans (2)"), AfterSecondRescan, BaselineCount);

    // VerticalBox must still be registered after both re-scans.
    TestNotNull(TEXT("VerticalBox entry survives rescan"),
        Sub->GetTypeRegistry().FindByToken(FName(TEXT("VerticalBox"))));

    return true;
}

/**
 * MonolithUI.Registry.LateLoadedClassPickedUp (B10b — synthetic proxy)
 *
 * We cannot actually load a marketplace plugin mid-test. The closest
 * achievable proof: confirm that `RescanWidgetTypes` walks every currently
 * loaded UWidget descendant — so IF a late-loading plugin's UClasses are
 * present at re-scan time, they WILL appear in the registry.
 *
 * Methodology:
 *   1) Sample a known widget UClass that's guaranteed loaded (UButton).
 *   2) Force a re-scan.
 *   3) Confirm UButton is registered with the right WidgetClass pointer.
 *   4) Confirm the registry size is non-trivially > 5 (sanity-check that
 *      the walk isn't mis-filtering everything).
 *
 * This is NOT a regression test for the OnPostEngineInit dispatch lambda
 * itself — that lambda lives in `FMonolithUIModule::StartupModule` and is
 * exercised once per editor launch, not by automation.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIRegistryLateLoadProxyTest,
    "MonolithUI.Registry.LateLoadedClassPickedUp",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIRegistryLateLoadProxyTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    Sub->RescanWidgetTypes();

    const FUITypeRegistry& Registry = Sub->GetTypeRegistry();
    TestTrue(TEXT("Re-scan registers many widget types (>5)"), Registry.Num() > 5);

    // UButton — guaranteed loaded with stock UMG.
    const FUITypeRegistryEntry* Button = Registry.FindByToken(FName(TEXT("Button")));
    if (TestNotNull(TEXT("Button is registered after re-scan"), Button))
    {
        TestTrue(TEXT("Button WidgetClass valid"), Button->WidgetClass.IsValid());
    }

    return true;
}

/**
 * MonolithUI.Registry.HotReloadRefresh (B10c)
 *
 * Synthetic test for the hot-reload path: we cannot actually trigger a
 * Live Coding cycle in an automation test, so we exercise the same code
 * path by invoking `RefreshAfterReload` and asserting it does not throw,
 * does not corrupt the registry, and (importantly) returns 0 when no
 * entries are stale (which is the expected normal-state count).
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIRegistryHotReloadRefreshTest,
    "MonolithUI.Registry.HotReloadRefresh",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIRegistryHotReloadRefreshTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    const int32 BaselineCount = Sub->GetTypeRegistry().Num();

    // No-op refresh — every WidgetClass weak-ptr is still valid in a normal
    // session. Expect 0 refreshed entries.
    const int32 RefreshedCount = Sub->RefreshAfterReload();
    TestEqual(TEXT("RefreshAfterReload returns 0 when no entries are stale"), RefreshedCount, 0);

    // Registry size unchanged.
    TestEqual(TEXT("Registry size unchanged by no-op refresh"),
        Sub->GetTypeRegistry().Num(), BaselineCount);

    // VerticalBox still resolvable post-refresh.
    const FUITypeRegistryEntry* VBox = Sub->GetTypeRegistry().FindByToken(FName(TEXT("VerticalBox")));
    if (TestNotNull(TEXT("VerticalBox entry survives refresh"), VBox))
    {
        TestTrue(TEXT("VerticalBox WidgetClass still valid"), VBox->WidgetClass.IsValid());
    }

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
