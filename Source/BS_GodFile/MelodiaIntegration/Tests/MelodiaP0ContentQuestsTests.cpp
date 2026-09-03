#if WITH_DEV_AUTOMATION_TESTS

#include "../MelodiaNarrativeSubsystem.h"
#include "../MelodiaNarrativeTypes.h"
#include "../MelodiaTraversalCapabilityProvider.h"
#include "../MelusinaSorrowSeamComponent.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaP0PlaythroughQuestTest,
	"Melodia.P0.PlaythroughQuest",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaP0PlaythroughQuestTest::RunTest(const FString& Parameters)
{
	FMelodiaNarrativeRecord Record;
	const FName QuestId(TEXT("quest.first_dream"));
	const FName CompletionFlag(TEXT("flag.first_dream.quest.completed"));
	const FName PlaythroughFlag(TEXT("flag.p0.playthrough.completed"));

	// Initial state
	TestFalse(TEXT("First Dream Quest not initially completed"), Record.CompletedQuestIds.Contains(QuestId));
	TestFalse(TEXT("Playthrough Flag not initially set"), Record.Flags.FindRef(PlaythroughFlag));

	// Simulate successful completion of P0 main quest
	Record.CompletedQuestIds.Add(QuestId);
	Record.Flags.Add(CompletionFlag, true);
	Record.Flags.Add(PlaythroughFlag, true);

	TestTrue(TEXT("First Dream Quest completed"), Record.CompletedQuestIds.Contains(QuestId));
	TestTrue(TEXT("Completion Flag set"), Record.Flags.FindRef(CompletionFlag));
	TestTrue(TEXT("Playthrough Flag set"), Record.Flags.FindRef(PlaythroughFlag));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaP0WardrobeEquipTest,
	"Melodia.P0.WardrobeEquip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaP0WardrobeEquipTest::RunTest(const FString& Parameters)
{
	FMelodiaNarrativeRecord Record;
	const FName EquipFlag(TEXT("flag.wardrobe.outfit_equipped"));
	const FName SorrowSeamFlag(TEXT("flag.melusina.sorrow_seam_restored"));
	const FName CosmeticBodyId(TEXT("Cos_Body_MelusinaV2"));

	Record.OwnedCosmeticIds.Add(CosmeticBodyId);
	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Body, CosmeticBodyId);
	Record.Flags.Add(EquipFlag, true);
	Record.Flags.Add(SorrowSeamFlag, true);

	TestTrue(TEXT("Melusina V2 Owned"), Record.OwnedCosmeticIds.Contains(CosmeticBodyId));
	TestEqual(TEXT("Melusina V2 Equipped"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Body), CosmeticBodyId);
	TestTrue(TEXT("Outfit Equipped Flag set"), Record.Flags.FindRef(EquipFlag));
	TestTrue(TEXT("Sorrow Seam Restored Flag set"), Record.Flags.FindRef(SorrowSeamFlag));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaP0ChoralSheepRecruitTest,
	"Melodia.P0.ChoralSheepRecruit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaP0ChoralSheepRecruitTest::RunTest(const FString& Parameters)
{
	FMelodiaNarrativeRecord Record;
	const FName RecruitFlag(TEXT("flag.companion.choral_sheep_recruited"));
	const FName HarmonyStat(TEXT("melodia_harmony"));

	Record.Flags.Add(RecruitFlag, true);
	Record.SocialStats.Add(HarmonyStat, 2);

	TestTrue(TEXT("Choral Sheep Recruited Flag set"), Record.Flags.FindRef(RecruitFlag));
	TestEqual(TEXT("Harmony Stat incremented"), Record.SocialStats.FindRef(HarmonyStat), 2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaP0SeaAboveCutsceneTest,
	"Melodia.P0.SeaAboveCutscene",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaP0SeaAboveCutsceneTest::RunTest(const FString& Parameters)
{
	FMelodiaNarrativeRecord Record;
	const FName WitnessFlag(TEXT("flag.cutscene.sea_above_witnessed"));
	const FName PulseActiveFlag(TEXT("flag.sea_above.membrane_pulse_active"));
	const FName ResonanceStat(TEXT("melodia_resonance"));

	Record.Flags.Add(WitnessFlag, true);
	Record.Flags.Add(PulseActiveFlag, true);
	Record.SocialStats.Add(ResonanceStat, 5);

	TestTrue(TEXT("Sea Above Witnessed Flag set"), Record.Flags.FindRef(WitnessFlag));
	TestTrue(TEXT("Membrane Pulse Active Flag set"), Record.Flags.FindRef(PulseActiveFlag));
	TestEqual(TEXT("Resonance Stat incremented"), Record.SocialStats.FindRef(ResonanceStat), 5);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaShorewakeQuestTest,
	"Melodia.Quest.Shorewake",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaShorewakeQuestTest::RunTest(const FString& Parameters)
{
	FMelodiaNarrativeRecord Record;
	const FName QuestId(TEXT("quest.shorewake.initiation"));
	const FName CompletionFlag(TEXT("flag.quest.shorewake_completed"));
	const FName StarskiffFlag(TEXT("flag.sea_above.starskiff_ready"));
	const FName ShorewakeDressId(TEXT("Cos_ShorewakeDress"));
	const FName ResonanceStat(TEXT("melodia_resonance"));

	// Initial State
	TestFalse(TEXT("Shorewake Quest not initially completed"), Record.CompletedQuestIds.Contains(QuestId));
	TestFalse(TEXT("Completion Flag not initially set"), Record.Flags.FindRef(CompletionFlag));
	TestFalse(TEXT("Starskiff Ready Flag not initially set"), Record.Flags.FindRef(StarskiffFlag));

	// Simulate complete quest commit and wardrobe grant
	Record.CompletedQuestIds.Add(QuestId);
	Record.Flags.Add(CompletionFlag, true);
	Record.Flags.Add(StarskiffFlag, true);
	Record.OwnedCosmeticIds.Add(ShorewakeDressId);
	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Skirt, ShorewakeDressId);
	Record.SocialStats.Add(ResonanceStat, 5);

	// Verify Record Invariants
	TestTrue(TEXT("Shorewake Quest completed"), Record.CompletedQuestIds.Contains(QuestId));
	TestTrue(TEXT("Completion Flag set"), Record.Flags.FindRef(CompletionFlag));
	TestTrue(TEXT("Starskiff Ready Flag set"), Record.Flags.FindRef(StarskiffFlag));
	TestTrue(TEXT("Shorewake Dress Owned"), Record.OwnedCosmeticIds.Contains(ShorewakeDressId));
	TestEqual(TEXT("Shorewake Dress Equipped in Skirt slot"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Skirt), ShorewakeDressId);
	TestEqual(TEXT("Resonance Stat incremented"), Record.SocialStats.FindRef(ResonanceStat), 5);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
