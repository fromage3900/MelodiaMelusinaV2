#if WITH_DEV_AUTOMATION_TESTS
#include "MelodiaQuestManagerBase.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaQuestDefDefaultsTest, "Melodia.Quest.DefinitionDefaults", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaQuestDefDefaultsTest::RunTest(const FString& Parameters)
{
	FMelodiaQuestDef Def;
	TestEqual(TEXT("QuestId defaults to None"), Def.QuestId, NAME_None);
	TestEqual(TEXT("RequiredLevel defaults to 1"), Def.RequiredLevel, 1);
	TestEqual(TEXT("RewardXP defaults to 0"), Def.RewardXP, 0);
	TestEqual(TEXT("RewardGold defaults to 0"), Def.RewardGold, 0);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaQuestAcceptRejectTest, "Melodia.Quest.AcceptReject", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaQuestAcceptRejectTest::RunTest(const FString& Parameters)
{
	AMelodiaQuestManagerBase* Manager = NewObject<AMelodiaQuestManagerBase>();

	FMelodiaQuestDef Valid;
	Valid.QuestId = TEXT("Quest_Test_01");
	Valid.DisplayName = FText::FromString(TEXT("Test Quest"));
	Valid.RewardXP = 50;
	Valid.RewardGold = 100;

	FMelodiaQuestDef Empty;
	Empty.QuestId = NAME_None;

	TestFalse(TEXT("Empty quest rejected"), Manager->AcceptQuest(Empty));
	TestTrue(TEXT("Valid quest accepted"), Manager->AcceptQuest(Valid));
	TestFalse(TEXT("Duplicate quest rejected"), Manager->AcceptQuest(Valid));
	TestTrue(TEXT("Quest shows as active"), Manager->IsQuestActive(TEXT("Quest_Test_01")));

	TestTrue(TEXT("CompleteQuest succeeds"), Manager->CompleteQuest(TEXT("Quest_Test_01")));
	TestFalse(TEXT("CompleteQuest fails on already-completed"), Manager->CompleteQuest(TEXT("Quest_Test_01")));
	TestTrue(TEXT("Quest shows as completed"), Manager->IsQuestCompleted(TEXT("Quest_Test_01")));
	TestFalse(TEXT("Quest no longer active"), Manager->IsQuestActive(TEXT("Quest_Test_01")));

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaQuestRestoreStateTest, "Melodia.Quest.RestoreState", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaQuestRestoreStateTest::RunTest(const FString& Parameters)
{
	AMelodiaQuestManagerBase* Manager = NewObject<AMelodiaQuestManagerBase>();

	FMelodiaQuestDef Q1; Q1.QuestId = TEXT("Quest_Save_A"); Q1.RewardXP = 10;
	FMelodiaQuestDef Q2; Q2.QuestId = TEXT("Quest_Save_B"); Q2.RewardGold = 20;

	Manager->AcceptQuest(Q1);
	Manager->AcceptQuest(Q2);
	Manager->CompleteQuest(TEXT("Quest_Save_A"));

	TArray<FMelodiaQuestDef> SavedActive = Manager->GetActiveQuests();
	TArray<FName> SavedCompleted = Manager->GetCompletedQuestIds();

	TestEqual(TEXT("One active quest before restore"), SavedActive.Num(), 1);
	TestEqual(TEXT("One completed quest before restore"), SavedCompleted.Num(), 1);

	Manager->RestoreQuestState(SavedActive, SavedCompleted);
	TestTrue(TEXT("Quest_Save_B still active after restore"), Manager->IsQuestActive(TEXT("Quest_Save_B")));
	TestTrue(TEXT("Quest_Save_A still completed after restore"), Manager->IsQuestCompleted(TEXT("Quest_Save_A")));
	TestFalse(TEXT("Quest_Save_A not active after restore"), Manager->IsQuestActive(TEXT("Quest_Save_A")));

	return true;
}
#endif
