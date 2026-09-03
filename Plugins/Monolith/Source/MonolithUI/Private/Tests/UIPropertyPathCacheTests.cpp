// Copyright tumourlove. All Rights Reserved.
#if WITH_DEV_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

#include "Components/Border.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Registry/MonolithUIRegistrySubsystem.h"
#include "Registry/UIPropertyPathCache.h"

/**
 * MonolithUI.Cache.GetPopulatesAndHits (C1)
 *
 * First call to Get for a (RootStructName, PropertyPath) pair must:
 *   - return a valid resolved chain
 *   - increment MissCount by 1
 *   - leave HitCount at 0
 * Second call to the SAME pair must:
 *   - return a valid resolved chain (re-validated, identical contents)
 *   - increment HitCount by 1
 *   - leave MissCount unchanged
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICacheGetPopulatesAndHitsTest,
    "MonolithUI.Cache.GetPopulatesAndHits",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICacheGetPopulatesAndHitsTest::RunTest(const FString& /*Parameters*/)
{
    // Use a freshly-constructed cache so prior test runs don't pollute counters.
    FUIPropertyPathCache LocalCache;

    UClass* const TextBlockClass = UTextBlock::StaticClass();
    const FName RootName = TextBlockClass->GetFName();
    const FString Path(TEXT("Visibility"));

    // First call: miss -> populate.
    const FUIPropertyPathChain First = LocalCache.Get(RootName, TextBlockClass, Path);
    TestTrue(TEXT("First Get returns a valid chain"), First.bValid);
    TestEqual(TEXT("Chain length is 1 for flat path"), First.PropertyChain.Num(), 1);
    TestEqual(TEXT("Miss counter is 1"), LocalCache.GetMissCount(), (int64)1);
    TestEqual(TEXT("Hit counter is 0"), LocalCache.GetHitCount(), (int64)0);
    TestEqual(TEXT("Cache size is 1"), LocalCache.Num(), 1);

    // Second call: hit -> bump HitCount.
    const FUIPropertyPathChain Second = LocalCache.Get(RootName, TextBlockClass, Path);
    TestTrue(TEXT("Second Get returns a valid chain"), Second.bValid);
    TestEqual(TEXT("Hit counter is 1 after second call"), LocalCache.GetHitCount(), (int64)1);
    TestEqual(TEXT("Miss counter still 1"), LocalCache.GetMissCount(), (int64)1);
    TestEqual(TEXT("Cache size still 1"), LocalCache.Num(), 1);

    // Property pointer should match across calls (same UClass, same FProperty*).
    TestEqual(TEXT("PropertyChain[0] identical across hit/miss"),
        First.PropertyChain[0], Second.PropertyChain[0]);

    return true;
}

/**
 * MonolithUI.Cache.NestedPathResolves
 *
 * Nested path (`Slot.LayoutData`) resolves through a chain of length 2:
 *   [0] FObjectProperty Slot -> UCanvasPanelSlot
 *   [1] FStructProperty LayoutData -> FAnchorData
 * (The actual classes vary by parent slot — for UTextBlock with no explicit
 *  parent we fall back to a property whose nesting we can verify.)
 *
 * We use UVerticalBox::FlowDirectionPreference (single-segment) AND a known
 * nested path on FMargin via UBorder's Padding... but UBorder.Padding is a
 * top-level FStructProperty so the nested path test uses Slot which is on
 * UWidget. Instead we test: UWidget has FObjectProperty `Slot` of type UPanelSlot
 * — `Slot.Parent` is too dynamic, so we test a static struct nest on FMargin
 * embedded inside FProperty walks via UBorder.Padding.Left.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICacheNestedPathTest,
    "MonolithUI.Cache.NestedPathResolves",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICacheNestedPathTest::RunTest(const FString& /*Parameters*/)
{
    FUIPropertyPathCache LocalCache;

    // UBorder has a UPROPERTY FMargin Padding — Padding.Left is a 2-hop chain.
    // Pass the live UClass (post-fix API): UBorder lives in /Script/UMG/, so
    // the prior FindObject<UStruct>(nullptr, "Border") would return nullptr
    // and the test would silently bail with TestNotNull failing. The new API
    // accepts the live UClass directly and never needs the transient-package
    // probe.
    UClass* const BorderClass = UBorder::StaticClass();
    const FName BorderName = BorderClass->GetFName();

    const FUIPropertyPathChain Chain = LocalCache.Get(BorderName, BorderClass, TEXT("Padding.Left"));
    TestTrue(TEXT("Padding.Left resolves"), Chain.bValid);
    TestEqual(TEXT("Chain length is 2"), Chain.PropertyChain.Num(), 2);
    TestEqual(TEXT("Struct chain length is 2"), Chain.StructChain.Num(), 2);
    TestEqual(TEXT("Miss counter is 1"), LocalCache.GetMissCount(), (int64)1);

    return true;
}

/**
 * MonolithUI.Cache.InvalidPathReturnsInvalidChain
 *
 * Path that doesn't resolve must return bValid=false and NOT cache an entry
 * (otherwise repeated bad calls would burn cache slots).
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICacheInvalidPathTest,
    "MonolithUI.Cache.InvalidPathReturnsInvalidChain",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICacheInvalidPathTest::RunTest(const FString& /*Parameters*/)
{
    FUIPropertyPathCache LocalCache;

    UClass* const TextBlockClass = UTextBlock::StaticClass();
    const FUIPropertyPathChain Chain = LocalCache.Get(
        TextBlockClass->GetFName(),
        TextBlockClass,
        TEXT("DefinitelyNotAPropertyOnAnyTextBlock"));

    TestFalse(TEXT("Invalid path returns bValid=false"), Chain.bValid);
    TestEqual(TEXT("Chain is empty"), Chain.PropertyChain.Num(), 0);
    TestEqual(TEXT("Invalid lookups still count as miss"), LocalCache.GetMissCount(), (int64)1);
    TestEqual(TEXT("Invalid lookups are NOT cached"), LocalCache.Num(), 0);

    return true;
}

/**
 * MonolithUI.Cache.UnknownRootStructReturnsInvalid
 *
 * Asking for a root struct name that doesn't resolve via FindObject must
 * return an invalid chain rather than crash.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICacheUnknownRootTest,
    "MonolithUI.Cache.UnknownRootStructReturnsInvalid",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICacheUnknownRootTest::RunTest(const FString& /*Parameters*/)
{
    FUIPropertyPathCache LocalCache;

    // Post-fix API requires a live UStruct -- passing nullptr is the new
    // "unknown root" condition. The cache must short-circuit cleanly.
    const FUIPropertyPathChain Chain = LocalCache.Get(
        FName(TEXT("StructThatDoesNotExist_91827463")),
        /*RootStruct=*/nullptr,
        TEXT("AnyProperty"));

    TestFalse(TEXT("Unknown root returns bValid=false"), Chain.bValid);
    TestEqual(TEXT("Cache stays empty"), LocalCache.Num(), 0);

    return true;
}

/**
 * MonolithUI.Cache.LRUEvictionAtCapacity
 *
 * With a cap of 2, inserting 3 distinct entries must evict the
 * least-recently-used one. EvictionCount increments by 1.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICacheLRUEvictionTest,
    "MonolithUI.Cache.LRUEvictionAtCapacity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICacheLRUEvictionTest::RunTest(const FString& /*Parameters*/)
{
    FUIPropertyPathCache LocalCache(/*Capacity=*/2);

    UClass* const TextBlockClass = UTextBlock::StaticClass();
    UClass* const VerticalBoxClass = UVerticalBox::StaticClass();
    const FName TextBlockName = TextBlockClass->GetFName();
    const FName VerticalBoxName = VerticalBoxClass->GetFName();

    // Insert 1: TextBlock.Visibility (LRU stamp 1).
    LocalCache.Get(TextBlockName, TextBlockClass, TEXT("Visibility"));
    // Insert 2: TextBlock.RenderOpacity (LRU stamp 2). Cache full at 2/2.
    LocalCache.Get(TextBlockName, TextBlockClass, TEXT("RenderOpacity"));
    TestEqual(TEXT("Cache size hits cap"), LocalCache.Num(), 2);
    TestEqual(TEXT("No evictions yet"), LocalCache.GetEvictionCount(), (int64)0);

    // Insert 3: VerticalBox.Visibility — should evict TextBlock.Visibility.
    LocalCache.Get(VerticalBoxName, VerticalBoxClass, TEXT("Visibility"));
    TestEqual(TEXT("Cache size still 2 (cap)"), LocalCache.Num(), 2);
    TestEqual(TEXT("Eviction count is 1"), LocalCache.GetEvictionCount(), (int64)1);

    // Re-Get the evicted entry: should miss (counts as miss, not hit).
    const int64 MissesBefore = LocalCache.GetMissCount();
    const int64 HitsBefore = LocalCache.GetHitCount();
    LocalCache.Get(TextBlockName, TextBlockClass, TEXT("Visibility"));
    TestEqual(TEXT("Re-get of evicted entry counts as miss"),
        LocalCache.GetMissCount(), MissesBefore + 1);
    TestEqual(TEXT("Hit count unchanged"), LocalCache.GetHitCount(), HitsBefore);

    return true;
}

/**
 * MonolithUI.Cache.ResetClearsEntriesAndKeepsCounters
 *
 * Reset() drops cache contents but NOT diagnostic counters (those reset via
 * ResetCounters). Two-call separation is intentional — counters are useful
 * across reloads.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICacheResetTest,
    "MonolithUI.Cache.ResetClearsEntriesAndKeepsCounters",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICacheResetTest::RunTest(const FString& /*Parameters*/)
{
    FUIPropertyPathCache LocalCache;

    UClass* const TextBlockClass = UTextBlock::StaticClass();
    LocalCache.Get(TextBlockClass->GetFName(), TextBlockClass, TEXT("Visibility"));
    LocalCache.Get(TextBlockClass->GetFName(), TextBlockClass, TEXT("Visibility"));
    TestEqual(TEXT("Pre-reset cache size"), LocalCache.Num(), 1);
    TestEqual(TEXT("Pre-reset miss count"), LocalCache.GetMissCount(), (int64)1);
    TestEqual(TEXT("Pre-reset hit count"), LocalCache.GetHitCount(), (int64)1);

    LocalCache.Reset();
    TestEqual(TEXT("Post-reset cache empty"), LocalCache.Num(), 0);
    TestEqual(TEXT("Post-reset miss count survives"), LocalCache.GetMissCount(), (int64)1);
    TestEqual(TEXT("Post-reset hit count survives"), LocalCache.GetHitCount(), (int64)1);

    LocalCache.ResetCounters();
    TestEqual(TEXT("Post-ResetCounters miss count is 0"), LocalCache.GetMissCount(), (int64)0);
    TestEqual(TEXT("Post-ResetCounters hit count is 0"), LocalCache.GetHitCount(), (int64)0);

    return true;
}

/**
 * MonolithUI.Cache.SubsystemHasCache
 *
 * The registry subsystem owns a cache instance — verify the accessor surface
 * that downstream callers (action handlers) rely on.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICacheSubsystemAccessTest,
    "MonolithUI.Cache.SubsystemHasCache",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICacheSubsystemAccessTest::RunTest(const FString& /*Parameters*/)
{
    UMonolithUIRegistrySubsystem* Sub = UMonolithUIRegistrySubsystem::Get();
    if (!TestNotNull(TEXT("UMonolithUIRegistrySubsystem available"), Sub))
    {
        return false;
    }

    FUIPropertyPathCache* Cache = Sub->GetPathCache();
    TestNotNull(TEXT("Subsystem exposes a non-null path cache"), Cache);

    if (Cache)
    {
        TestEqual(TEXT("Default cache cap is 256"), Cache->Capacity(), 256);
    }

    return true;
}

/**
 * MonolithUI.Cache.NestedPathOnScriptPackageClassResolves (regression)
 *
 * Regression test for the FUIPropertyPathCache bug where nested-path lookups
 * (`A.B.C`) on UClasses living in `/Script/<Module>/` packages always returned
 * an invalid chain. Root cause: the miss path called
 * `FindObject<UStruct>(nullptr, *RootStructName.ToString())`, which probes the
 * transient package -- where UClasses do NOT live. UClasses live in
 * `/Script/UMG/`, `/Script/MonolithUI/`, etc. Net effect: every nested-path
 * call into ApplyJsonPath / Apply emitted spurious `PropertyNotFound`
 * warnings, e.g. for a nested optional-provider widget path.
 *
 * Symptom in production: `ui::apply_effect_surface_preset` and
 * `ui::build_ui_from_spec` (with `effect: {...}` sub-bag) emitted dozens of
 * `PropertyNotFound (path 'Config.Shape.CornerRadii' did not resolve on
 * EffectSurface)` warnings. Flat-path writes (Visibility, Opacity) were
 * unaffected because their 1-segment chains avoided the nested-walk codepath.
 *
 * The fix: caller passes the live `UClass*` directly into Get; the FName key
 * remains the cache key but the resolution path no longer needs a transient-
 * package FindObject lookup. UBorder.Padding.Left exercises the EXACT shape
 * of the original failure -- a 2-hop nested chain on a UClass shipped in
 * `/Script/UMG/`. If this test passes, the optional-provider failure mode is
 * structurally fixed.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICacheNestedPathOnScriptPackageClassTest,
    "MonolithUI.Cache.NestedPathOnScriptPackageClassResolves",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICacheNestedPathOnScriptPackageClassTest::RunTest(const FString& /*Parameters*/)
{
    FUIPropertyPathCache LocalCache;

    // UBorder lives in /Script/UMG/ -- a perfect stand-in for any UClass
    // provided by a non-transient script package.
    UClass* const BorderClass = UBorder::StaticClass();
    const FName BorderName = BorderClass->GetFName();

    // SANITY: the very lookup the old code did would have failed --
    // demonstrates we are testing the right scenario.
    UStruct* const TransientLookup = FindObject<UStruct>(nullptr, *BorderName.ToString());
    TestNull(
        TEXT("Pre-fix lookup pattern (FindObject in transient package) returns null for /Script/<Module>/ UClass -- confirms regression scenario"),
        TransientLookup);

    // Nested path on the UClass. Pre-fix this returned bValid=false with a
    // miss; post-fix it returns a valid 2-hop chain.
    const FUIPropertyPathChain MissChain = LocalCache.Get(BorderName, BorderClass, TEXT("Padding.Left"));
    TestTrue(TEXT("Nested path resolves on /Script/<Module>/ UClass"), MissChain.bValid);
    TestEqual(TEXT("Chain length is 2 (Padding -> Left)"), MissChain.PropertyChain.Num(), 2);
    TestEqual(TEXT("StructChain length is 2"), MissChain.StructChain.Num(), 2);
    TestEqual(TEXT("StructChain[0] is the UBorder UClass"), MissChain.StructChain[0], (UStruct*)BorderClass);

    // Hit path also returns valid chain (proves revalidate-against-live-root
    // works -- the prior implementation would have failed revalidation here
    // too because RevalidateEntry called the same broken FindObject).
    const FUIPropertyPathChain HitChain = LocalCache.Get(BorderName, BorderClass, TEXT("Padding.Left"));
    TestTrue(TEXT("Cached hit returns valid chain after revalidation"), HitChain.bValid);
    TestEqual(TEXT("Hit returns identical FProperty[0]"), HitChain.PropertyChain[0], MissChain.PropertyChain[0]);
    TestEqual(TEXT("Hit returns identical FProperty[1]"), HitChain.PropertyChain[1], MissChain.PropertyChain[1]);
    TestEqual(TEXT("Exactly one miss recorded"), LocalCache.GetMissCount(), (int64)1);
    TestEqual(TEXT("Exactly one hit recorded"), LocalCache.GetHitCount(), (int64)1);

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
