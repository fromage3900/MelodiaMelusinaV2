#if WITH_DEV_AUTOMATION_TESTS
#include "MelodiaNPCInteractionComponent.h"
#include "MelodiaQuestManagerBase.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaNPCInteractionDefaultsTest, "Melodia.NPC.InteractionDefaults", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaNPCInteractionDefaultsTest::RunTest(const FString& Parameters)
{
	UMelodiaNPCInteractionComponent* Comp = NewObject<UMelodiaNPCInteractionComponent>();

	// The component carries a default EncounterGuidance line (authored content),
	// so clear it to test the "no authored content" contract deterministically.
	Comp->EncounterGuidance = FText();

	TestEqual(TEXT("NPCId defaults to None"), Comp->NPCId, NAME_None);
	TestFalse(TEXT("HasDialogue returns false with no content"), Comp->HasDialogue());
	TestFalse(TEXT("bInteractionActive defaults to false"), Comp->bInteractionActive);
	TestFalse(TEXT("bIsQuestGiver defaults to false"), Comp->bIsQuestGiver);
	TestEqual(TEXT("CurrentDialogueIndex defaults to INDEX_NONE"), Comp->CurrentDialogueIndex, INDEX_NONE);
	TestFalse(TEXT("BeginInteraction returns false with no dialogue"), Comp->BeginInteraction());

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaNPCQuestGiverTest, "Melodia.NPC.QuestGiverDefaults", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaNPCQuestGiverTest::RunTest(const FString& Parameters)
{
	UMelodiaNPCInteractionComponent* Comp = NewObject<UMelodiaNPCInteractionComponent>();

	TestEqual(TEXT("QuestToGive.QuestId defaults to None"), Comp->QuestToGive.QuestId, NAME_None);
	TestEqual(TEXT("QuestToCompleteOnEnd defaults to None"), Comp->QuestToCompleteOnEnd, NAME_None);
	TestEqual(TEXT("QuestToGive.RewardXP defaults to 0"), Comp->QuestToGive.RewardXP, 0);
	TestEqual(TEXT("QuestToGive.RewardGold defaults to 0"), Comp->QuestToGive.RewardGold, 0);

	Comp->bIsQuestGiver = true;
	Comp->QuestToGive.QuestId = TEXT("Quest_NPC_Test");
	TestTrue(TEXT("bIsQuestGiver is settable"), Comp->bIsQuestGiver);

	return true;
}
#endif
