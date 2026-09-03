// Automation tests for Melusina character, presentation, wardrobe, and traversal systems.
// (Source/BS_GodFile/MelodiaIntegration/Tests/MelusinaIntegrationTests.cpp)

#if WITH_DEV_AUTOMATION_TESTS

#include "../MelusinaSorrowSeamComponent.h"
#include "../MelodiaNarrativeTypes.h"
#include "../MelodiaNarrativeSubsystem.h"
#include "../MelodiaTraversalCapabilityProvider.h"
#include "Misc/AutomationTest.h"

// ---------------------------------------------------------------------------
// Melusina Sorrow Seam Presentation & Sheen Constants
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelusinaSorrowSeamConstantsTest,
	"Melodia.Melusina.SorrowSeam.ConstantsAndDefaults",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelusinaSorrowSeamConstantsTest::RunTest(const FString& Parameters)
{
	// 1. Static sheen thresholds matching specs/melusina_sorrow_seam.v1.json
	TestEqual(TEXT("PristineSheen matches spec (0.18f)"), UMelusinaSorrowSeamComponent::PristineSheen, 0.18f);
	TestEqual(TEXT("HealedSheen matches spec (0.32f)"), UMelusinaSorrowSeamComponent::HealedSheen, 0.32f);

	// 2. Component Class Default Object (CDO) invariants
	const UMelusinaSorrowSeamComponent* CDO = GetDefault<UMelusinaSorrowSeamComponent>();
	if (!CDO)
	{
		AddError(TEXT("Could not obtain UMelusinaSorrowSeamComponent CDO."));
		return false;
	}

	TestTrue(TEXT("SorrowSeam component can tick"), CDO->PrimaryComponentTick.bCanEverTick);
	TestEqual(TEXT("SorrowSeam ticks in TG_PostPhysics"), CDO->PrimaryComponentTick.TickGroup, TG_PostPhysics);
	TestEqual(TEXT("MendLerpSpeed default is 1.5f"), CDO->MendLerpSpeed, 1.5f);

	return true;
}

// ---------------------------------------------------------------------------
// Melusina Wardrobe Slot Mapping & Narrative Record Persistence Contract
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelusinaWardrobeEquipContractTest,
	"Melodia.Melusina.Wardrobe.SlotEquipContract",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelusinaWardrobeEquipContractTest::RunTest(const FString& Parameters)
{
	FMelodiaNarrativeRecord Record;
	Record.Version = FMelodiaNarrativeRecord::CurrentVersion;

	// Populate Melusina wardrobe slots
	const FName DressId(TEXT("Cos_Dress_Melusina"));
	const FName GlovesId(TEXT("Cos_Gloves_Melusina"));
	const FName TrailId(TEXT("Cos_Trail_Melusina_SorrowSeam"));
	const FName HairCharmId(TEXT("Cos_Hair_Melusina_Water"));

	Record.OwnedCosmeticIds.Add(DressId);
	Record.OwnedCosmeticIds.Add(GlovesId);
	Record.OwnedCosmeticIds.Add(TrailId);
	Record.OwnedCosmeticIds.Add(HairCharmId);

	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Body, DressId);
	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Gloves, GlovesId);
	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Trail, TrailId);
	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::HairCharm, HairCharmId);

	TestEqual(TEXT("Record contains 4 owned cosmetics"), Record.OwnedCosmeticIds.Num(), 4);
	TestEqual(TEXT("Record contains 4 equipped slots"), Record.EquippedCosmeticIds.Num(), 4);

	// Test migration preserves all equipped Melusina slots
	TestTrue(TEXT("Migration succeeds"), UMelodiaNarrativeSubsystem::MigrateRecord(Record));
	TestEqual(TEXT("Equipped Body is Dress"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Body), DressId);
	TestEqual(TEXT("Equipped Gloves is Gloves"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Gloves), GlovesId);
	TestEqual(TEXT("Equipped Trail is SorrowSeam"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Trail), TrailId);
	TestEqual(TEXT("Equipped HairCharm is WaterHair"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::HairCharm), HairCharmId);

	return true;
}

// ---------------------------------------------------------------------------
// Melusina Traversal Capability Invariants
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelusinaTraversalCapabilityContractTest,
	"Melodia.Melusina.Traversal.CapabilityContract",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelusinaTraversalCapabilityContractTest::RunTest(const FString& Parameters)
{
	// Canonical traversal capability identifiers
	TestEqual(TEXT("Glide capability ID"), MelodiaTraversalCapability::Glide, FName(TEXT("capability.melodia.glide")));
	TestEqual(TEXT("Dash capability ID"), MelodiaTraversalCapability::Dash, FName(TEXT("capability.melodia.dash")));
	TestEqual(TEXT("Swim capability ID"), MelodiaTraversalCapability::Swim, FName(TEXT("capability.melodia.swim")));

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
