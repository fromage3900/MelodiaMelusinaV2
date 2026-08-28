#if WITH_DEV_AUTOMATION_TESTS

#include "MelodiaWardrobeSubsystem.h"
#include "MelodiaWardrobeComponent.h"
#include "MelodiaTraversalComponent.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaCosmeticTypes.h"
#include "Misc/AutomationTest.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Character.h"
#include "Components/SkeletalMeshComponent.h"

// ── Wardrobe Equip Roundtrip Test ─────────────────────────────────────────────

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMelodiaWardrobeEquipRoundtripTest,
    "Melodia.Wardrobe.EquipRoundtrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMelodiaWardrobeEquipRoundtripTest::RunTest(const FString& Parameters)
{
    // Editor commandlet worlds do not own a GameInstance. Build the smallest real
    // standalone context so this Product test exercises the same initialized
    // GameInstanceSubsystem graph as play, without requiring PIE or RiderLink.
    UGameInstance* GI = NewObject<UGameInstance>(GEngine);
    GI->InitializeStandalone(TEXT("MelodiaWardrobeEquipRoundtripWorld"));
    UWorld* World = GI->GetWorld();
    UMelodiaWardrobeSubsystem* Wardrobe = GI->GetSubsystem<UMelodiaWardrobeSubsystem>();
    if (!Wardrobe)
    {
        TestFalse(TEXT("Wardrobe subsystem not available"), true);
        return false;
    }

    // Test 1: Grant a cosmetic
    const FName TestCosmeticId = FName(TEXT("Cos_Accessories_MelusinaV2"));
    const FName TestGrantId = FName(TEXT("TestGrant_001"));
    
    TestTrue(TEXT("GrantCosmetic returns true on success"), 
        Wardrobe->GrantCosmetic(TestCosmeticId, TestGrantId));
    
    TestTrue(TEXT("IsOwned returns true after grant"), 
        Wardrobe->IsOwned(TestCosmeticId));

    // Test 2: Equip the cosmetic
    TestTrue(TEXT("EquipCosmetic returns true on success"), 
        Wardrobe->EquipCosmetic(TestCosmeticId));

    // Test 3: Verify equipped state
    const FMelodiaWardrobeState State = Wardrobe->GetState();
    TestTrue(TEXT("Equipped map contains the cosmetic"), 
        State.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Accessories) == TestCosmeticId);

    // Test 4: Unequip
    TestTrue(TEXT("UnequipSlot returns true on success"), 
        Wardrobe->UnequipSlot(EMelodiaWardrobeSlot::Accessories));

    // Test 5: Verify unequipped state
    const FMelodiaWardrobeState StateAfterUnequip = Wardrobe->GetState();
    TestFalse(TEXT("Equipped map no longer contains the cosmetic after unequip"), 
        StateAfterUnequip.EquippedCosmeticIds.Contains(EMelodiaWardrobeSlot::Accessories));

    // Test 6: Idempotency - grant same cosmetic again should return true but not duplicate
    TestTrue(TEXT("GrantCosmetic is idempotent (returns true for already owned)"), 
        Wardrobe->GrantCosmetic(TestCosmeticId, NAME_None));

    // Test 7: GrantId dedupe - same GrantId should be rejected within session
    const FName TestGrantId2 = FName(TEXT("TestGrant_002"));
    Wardrobe->GrantCosmetic(TestCosmeticId, TestGrantId2); // Should succeed (different GrantId)
    TestTrue(TEXT("Same GrantId rejected within session"), 
        !Wardrobe->GrantCosmetic(TestCosmeticId, TestGrantId2)); // Should fail (same GrantId)

    GI->Shutdown();
    GEngine->DestroyWorldContext(World);
    World->DestroyWorld(false);

    return true;
}


// ── Wardrobe Gameplay Hook Test ──────────────────────────────────────────────

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMelodiaWardrobeGameplayHookTest,
    "Melodia.Wardrobe.GameplayHook",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMelodiaWardrobeGameplayHookTest::RunTest(const FString& Parameters)
{
    UWorld* World = GEngine->GetWorldContexts()[0].World();
    if (!World)
    {
        TestFalse(TEXT("No world available"), true);
        return false;
    }

    UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(World);
    if (!Wardrobe)
    {
        TestFalse(TEXT("Wardrobe subsystem not available"), true);
        return false;
    }

    // Test 1: Resonant Weave outfit should unlock Glide capability
    const FName OutfitId = FName(TEXT("Cos_Accessories_MelusinaV2"));
    const FName GrantId = FName(TEXT("GlideTestGrant_001"));
    
    Wardrobe->GrantCosmetic(OutfitId, GrantId);
    Wardrobe->EquipCosmetic(OutfitId);

    // Test 2: Check that Glide capability is active
    TestTrue(TEXT("Glide capability is active when Resonant Weave is equipped"),
        Wardrobe->IsCapabilityActive(EMelodiaFormCapability::Glide, NAME_None));

    // Test 3: Check that the form is unlocked
    const FName EquippedFormId = Wardrobe->GetEquippedFormId(EMelodiaWardrobeSlot::Accessories);
    TestFalse(TEXT("Equipped accessory resolves an authored resonant form"), EquippedFormId.IsNone());
    TestTrue(TEXT("Equipped accessory's authored resonant form is unlocked"),
        Wardrobe->IsFormUnlocked(EquippedFormId));

    // Test 4: Unequip should remove the capability
    Wardrobe->UnequipSlot(EMelodiaWardrobeSlot::Accessories);
    TestFalse(TEXT("Glide capability is inactive after unequip"),
        Wardrobe->IsCapabilityActive(EMelodiaFormCapability::Glide, NAME_None));

    // Test 5: Re-equip should restore the capability
    Wardrobe->EquipCosmetic(OutfitId);
    TestTrue(TEXT("Glide capability is restored after re-equip"),
        Wardrobe->IsCapabilityActive(EMelodiaFormCapability::Glide, NAME_None));

    return true;
}


// ── Wardrobe Save/Load Roundtrip Test ────────────────────────────────────────

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMelodiaWardrobeSaveLoadRoundtripTest,
    "Melodia.Wardrobe.SaveLoadRoundtrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMelodiaWardrobeSaveLoadRoundtripTest::RunTest(const FString& Parameters)
{
    UWorld* World = GEngine->GetWorldContexts()[0].World();
    if (!World)
    {
        TestFalse(TEXT("No world available"), true);
        return false;
    }

    UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(World);
    UMelodiaNarrativeSubsystem* Narrative = UMelodiaNarrativeSubsystem::GetMelodiaNarrativeSubsystem(World);
    
    if (!Wardrobe || !Narrative)
    {
        TestFalse(TEXT("Subsystems not available"), true);
        return false;
    }

    // Setup: Grant and equip a cosmetic
    const FName OutfitId = FName(TEXT("Cos_Accessories_MelusinaV2"));
    const FName GrantId = FName(TEXT("SaveLoadTestGrant_001"));
    
    Wardrobe->GrantCosmetic(OutfitId, GrantId);
    Wardrobe->EquipCosmetic(OutfitId);

    // Capture state before save
    const FMelodiaWardrobeState StateBeforeSave = Wardrobe->GetState();
    const int32 OwnedCountBefore = StateBeforeSave.OwnedCosmeticIds.Num();
    const int32 EquippedCountBefore = StateBeforeSave.EquippedCosmeticIds.Num();

    // Simulate save: capture narrative record
    FMelodiaNarrativeRecord Record = Narrative->GetNarrativeRecord();
    
    // Verify record has the wardrobe data
    TestTrue(TEXT("Narrative record contains owned cosmetic after grant"),
        Record.OwnedCosmeticIds.Contains(OutfitId));
    TestTrue(TEXT("Narrative record contains equipped cosmetic after equip"),
        Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Accessories) == OutfitId);

    // Simulate load: restore narrative record
    Narrative->RestoreNarrativeRecord(Record);

    // Verify state after load
    const FMelodiaWardrobeState StateAfterLoad = Wardrobe->GetState();
    TestEqual(TEXT("Owned count matches after load"), 
        StateAfterLoad.OwnedCosmeticIds.Num(), OwnedCountBefore);
    TestEqual(TEXT("Equipped count matches after load"), 
        StateAfterLoad.EquippedCosmeticIds.Num(), EquippedCountBefore);

    return true;
}


// ── Wardrobe Traversal Integration Test ──────────────────────────────────────

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMelodiaWardrobeTraversalIntegrationTest,
    "Melodia.Wardrobe.TraversalIntegration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMelodiaWardrobeTraversalIntegrationTest::RunTest(const FString& Parameters)
{
    UWorld* World = GEngine->GetWorldContexts()[0].World();
    if (!World)
    {
        TestFalse(TEXT("No world available"), true);
        return false;
    }

    UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(World);
    if (!Wardrobe)
    {
        TestFalse(TEXT("Wardrobe subsystem not available"), true);
        return false;
    }

    // Test: QueryTraversalCapability through the interface
    FName BlockReason = NAME_None;
    const bool bCanGlide = Wardrobe->QueryTraversalCapability(
        FName(TEXT("capability.melodia.glide")), 
        NAME_None, 
        BlockReason);
    
    // Without equipped outfit, should be blocked
    TestFalse(TEXT("Glide is blocked without equipped outfit"), bCanGlide);

    // Equip the outfit
    const FName OutfitId = FName(TEXT("Cos_Accessories_MelusinaV2"));
    const FName GrantId = FName(TEXT("TraversalTestGrant_001"));
    Wardrobe->GrantCosmetic(OutfitId, GrantId);
    Wardrobe->EquipCosmetic(OutfitId);

    // Now glide should be available
    BlockReason = NAME_None;
    const bool bCanGlideAfterEquip = Wardrobe->QueryTraversalCapability(
        FName(TEXT("capability.melodia.glide")), 
        NAME_None, 
        BlockReason);
    
    TestTrue(TEXT("Glide is available after equipping Resonant Weave"), bCanGlideAfterEquip);

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
