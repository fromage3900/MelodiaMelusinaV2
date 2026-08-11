#if WITH_DEV_AUTOMATION_TESTS
#include "MelodiaProgressionComponent.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaProgressionDefaultsTest, "Melodia.Progression.Defaults", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaProgressionDefaultsTest::RunTest(const FString& Parameters)
{
	UMelodiaProgressionComponent* Prog = NewObject<UMelodiaProgressionComponent>();
	TestEqual(TEXT("Level defaults to 1"), Prog->Level, 1);
	TestEqual(TEXT("CurrentXP defaults to 0"), Prog->CurrentXP, 0);
	TestEqual(TEXT("XPToNextLevel defaults to 100"), Prog->XPToNextLevel, 100);
	TestEqual(TEXT("Currency defaults to 0"), Prog->Currency, 0);
	TestTrue(TEXT("Inventory defaults to empty"), Prog->Inventory.IsEmpty());
	TestFalse(TEXT("Cannot level up at 0 XP"), Prog->CanLevelUp());
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaProgressionAddXPTest, "Melodia.Progression.AddXP", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaProgressionAddXPTest::RunTest(const FString& Parameters)
{
	UMelodiaProgressionComponent* Prog = NewObject<UMelodiaProgressionComponent>();

	TestEqual(TEXT("AddXP returns new total"), Prog->AddXP(25), 25);
	TestEqual(TEXT("CurrentXP is 25 after one award"), Prog->CurrentXP, 25);
	TestEqual(TEXT("AddXP accumulates"), Prog->AddXP(30), 55);
	TestEqual(TEXT("AddXP handles zero"), Prog->AddXP(0), 55);

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaProgressionAddCurrencyTest, "Melodia.Progression.AddCurrency", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaProgressionAddCurrencyTest::RunTest(const FString& Parameters)
{
	UMelodiaProgressionComponent* Prog = NewObject<UMelodiaProgressionComponent>();

	TestEqual(TEXT("AddCurrency returns new total"), Prog->AddCurrency(100), 100);
	TestEqual(TEXT("Currency is 100 after one award"), Prog->Currency, 100);
	TestEqual(TEXT("AddCurrency accumulates"), Prog->AddCurrency(50), 150);
	TestEqual(TEXT("AddCurrency handles zero"), Prog->AddCurrency(0), 150);

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaProgressionInventoryTest, "Melodia.Progression.Inventory", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaProgressionInventoryTest::RunTest(const FString& Parameters)
{
	UMelodiaProgressionComponent* Prog = NewObject<UMelodiaProgressionComponent>();

	Prog->AddItem(TEXT("Item_TestHeart"), FText::FromString(TEXT("Heart Token")));
	TestTrue(TEXT("HasItem returns true after AddItem"), Prog->HasItem(TEXT("Item_TestHeart")));
	TestEqual(TEXT("Quantity defaults to 1"), Prog->GetItemQuantity(TEXT("Item_TestHeart")), 1);
	TestFalse(TEXT("Nonexistent item not found"), Prog->HasItem(TEXT("Item_Nonexistent")));
	TestEqual(TEXT("GetItemQuantity for missing returns 0"), Prog->GetItemQuantity(TEXT("Item_Nonexistent")), 0);

	Prog->AddItem(TEXT("Item_TestHeart"), FText::GetEmpty(), 3);
	TestEqual(TEXT("AddItem stacks quantity"), Prog->GetItemQuantity(TEXT("Item_TestHeart")), 4);

	return true;
}
#endif
