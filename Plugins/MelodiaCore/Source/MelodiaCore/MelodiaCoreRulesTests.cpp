// Automation tests for Melodia's deterministic combat and songcraft rules.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#if WITH_DEV_AUTOMATION_TESTS

#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaBattleInputComponent.h"
#include "MelodiaCombatStateComponent.h"
#include "MelodiaEncounterTrigger.h"
#include "MelodiaEnemyDefinition.h"
#include "MelodiaNPCInteractionComponent.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaRoguelikeRunSubsystem.h"
#include "MelodiaNPCDefinition.h"
#include "MelodiaRhythmExecutionComponent.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "MelodiaRulesGenerated.h"
#include "Engine/GameInstance.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRhythmRulesTest, "Melodia.CoreRules.Rhythm", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRhythmRulesTest::RunTest(const FString& Parameters)
{
	const FMelodiaRhythmWindows Windows;

	const FMelodiaRhythmGradeResult Perfect = UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(20.0f, Windows);
	TestEqual(TEXT("20 ms grades Perfect"), Perfect.Grade, EMelodiaRhythmGrade::Perfect);
	TestEqual(TEXT("Perfect multiplier is capped at 1.5"), Perfect.CombatMultiplier, 1.5f);
	TestTrue(TEXT("Perfect counts as hit"), Perfect.bCountsAsHit);
	TestEqual(TEXT("Perfect boundary is inclusive"), UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(90.0f, Windows).Grade, EMelodiaRhythmGrade::Perfect);
	TestEqual(TEXT("Just outside Perfect becomes Great"), UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(90.01f, Windows).Grade, EMelodiaRhythmGrade::Great);
	TestEqual(TEXT("Great boundary is inclusive"), UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(120.0f, Windows).Grade, EMelodiaRhythmGrade::Great);
	TestEqual(TEXT("Just outside Great becomes Good"), UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(120.01f, Windows).Grade, EMelodiaRhythmGrade::Good);
	TestEqual(TEXT("Good boundary is inclusive"), UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(160.0f, Windows).Grade, EMelodiaRhythmGrade::Good);
	TestEqual(TEXT("Just outside Good becomes Miss"), UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(160.01f, Windows).Grade, EMelodiaRhythmGrade::Miss);
	TestEqual(TEXT("Early and late inputs grade symmetrically"), UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(-90.0f, Windows).Grade, UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(90.0f, Windows).Grade);

	const FMelodiaRhythmGradeResult Great = UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(110.0f, Windows);
	TestEqual(TEXT("110 ms grades Great"), Great.Grade, EMelodiaRhythmGrade::Great);

	const FMelodiaRhythmGradeResult Good = UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(140.0f, Windows);
	TestEqual(TEXT("140 ms grades Good"), Good.Grade, EMelodiaRhythmGrade::Good);

	const FMelodiaRhythmGradeResult Miss = UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(220.0f, Windows);
	TestEqual(TEXT("220 ms grades Miss"), Miss.Grade, EMelodiaRhythmGrade::Miss);
	TestEqual(TEXT("Miss multiplier follows generated accessibility rule"), Miss.CombatMultiplier, MelodiaRulesGen::MissMultiplier);
	TestFalse(TEXT("Miss does not count as hit"), Miss.bCountsAsHit);

	const float ComboCapped = UMelodiaCoreRulesLibrary::GetRhythmCombatMultiplier(EMelodiaRhythmGrade::Good, 20);
	TestEqual(TEXT("Combo bonus cannot exceed max combat multiplier"), ComboCapped, 1.5f);

	const int32 Crescendo = UMelodiaCoreRulesLibrary::ApplyCrescendoGain(98, EMelodiaRhythmGrade::Perfect, 100);
	TestEqual(TEXT("Crescendo gain clamps to max"), Crescendo, 100);
	TestEqual(TEXT("Perfect Crescendo gain follows generated rules"), UMelodiaCoreRulesLibrary::GetCrescendoGain(EMelodiaRhythmGrade::Perfect), MelodiaRulesGen::CrescendoGainPerfect);
	TestEqual(TEXT("Great Crescendo gain follows generated rules"), UMelodiaCoreRulesLibrary::GetCrescendoGain(EMelodiaRhythmGrade::Great), MelodiaRulesGen::CrescendoGainGreat);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRhythmReactivityRulesTest, "Melodia.CoreRules.RhythmReactivity", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRhythmReactivityRulesTest::RunTest(const FString& Parameters)
{
	UMelodiaRhythmReactivitySubsystem* Reactivity = NewObject<UMelodiaRhythmReactivitySubsystem>();
	TestNotNull(TEXT("Reactivity service can be created without a world"), Reactivity);
	if (!Reactivity)
	{
		return false;
	}

	Reactivity->NotifyBeat(999.0f, 2.0f);
	TestEqual(TEXT("BPM is clamped"), Reactivity->GetSignal().BPM, 400.0f);
	TestEqual(TEXT("Beat phase is clamped"), Reactivity->GetSignal().BeatPhase, 1.0f);
	TestEqual(TEXT("Beat pulse starts at one"), Reactivity->GetSignal().BeatPulse, 1.0f);

	Reactivity->NotifyCommandResolved(EMelodiaRhythmGrade::Perfect, 8.0f, -1.0f, 4.0f, 3);
	TestEqual(TEXT("Command energy is bounded"), Reactivity->GetSignal().CommandEnergy, 2.0f);
	TestEqual(TEXT("Combo is bounded"), Reactivity->GetSignal().ComboNormalized, 0.0f);
	TestEqual(TEXT("Crescendo is bounded"), Reactivity->GetSignal().CrescendoNormalized, 1.0f);
	TestEqual(TEXT("Perfect grade is preserved"), Reactivity->GetSignal().LastRhythmGrade, EMelodiaRhythmGrade::Perfect);

	Reactivity->NotifyBreak();
	Reactivity->NotifyVictory();
	TestEqual(TEXT("Break pulse fires"), Reactivity->GetSignal().BreakPulse, 1.0f);
	TestEqual(TEXT("Victory pulse fires"), Reactivity->GetSignal().VictoryPulse, 1.0f);

	Reactivity->ResetEncounter();
	TestEqual(TEXT("Reset clears command energy"), Reactivity->GetSignal().CommandEnergy, 0.0f);
	TestEqual(TEXT("Reset clears combat pulses"), Reactivity->GetSignal().BreakPulse, 0.0f);
	TestEqual(TEXT("Reset clears victory pulse"), Reactivity->GetSignal().VictoryPulse, 0.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaTurnEconomyRulesTest, "Melodia.CoreRules.TurnEconomy", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaTurnEconomyRulesTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("100 SPD costs 100 AV"), UMelodiaCoreRulesLibrary::CalculateAVCost(100), 100);
	TestEqual(TEXT("200 SPD costs 50 AV"), UMelodiaCoreRulesLibrary::CalculateAVCost(200), 50);
	TestEqual(TEXT("Speed clamps away from divide by zero"), UMelodiaCoreRulesLibrary::CalculateAVCost(0), 10000);

	TestEqual(TEXT("Shared SP clamps at max"), UMelodiaCoreRulesLibrary::ApplySharedSPDelta(4, 3, 5), 5);
	TestEqual(TEXT("Shared SP clamps at zero"), UMelodiaCoreRulesLibrary::ApplySharedSPDelta(1, -3, 5), 0);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaSongcraftRulesTest, "Melodia.CoreRules.Songcraft", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaSongcraftRulesTest::RunTest(const FString& Parameters)
{
	TArray<int32> Notes;
	Notes.Add(60);
	Notes.Add(64);
	Notes.Add(67);
	Notes.Add(72);

	TArray<float> Durations;
	Durations.Add(1.0f);
	Durations.Add(1.0f);
	Durations.Add(1.0f);
	Durations.Add(1.0f);

	TArray<FMelodiaSongMaterialInput> Materials;
	FMelodiaSongMaterialInput Crystal;
	Crystal.MaterialId = TEXT("MoonCrystal");
	Crystal.RarityTier = 3;
	Crystal.PowerModifier = 1.2f;
	Materials.Add(Crystal);

	const FMelodiaGeneratedSpell First = UMelodiaCoreRulesLibrary::GenerateSpellFromSong(Notes, Durations, EMelodiaInstrument::MusicBox, Materials);
	const FMelodiaGeneratedSpell Second = UMelodiaCoreRulesLibrary::GenerateSpellFromSong(Notes, Durations, EMelodiaInstrument::MusicBox, Materials);
	TestEqual(TEXT("Same composition produces same hash"), First.CompositionHash, Second.CompositionHash);
	TestEqual(TEXT("Same composition produces same spell id"), First.SpellId, Second.SpellId);
	TestTrue(TEXT("Generated spell has usable power"), First.Power > 0.0f);
	TestTrue(TEXT("Generated spell has legal SP cost"), First.SPCost >= 1 && First.SPCost <= 5);

	const int32 TrumpetHash = UMelodiaCoreRulesLibrary::MakeCompositionHash(Notes, Durations, EMelodiaInstrument::Trumpet, Materials);
	TestNotEqual(TEXT("Instrument changes composition hash"), First.CompositionHash, TrumpetHash);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRhythmExecutionGatingTest, "Melodia.CoreRules.RhythmExecutionGating", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRhythmExecutionGatingTest::RunTest(const FString& Parameters)
{
	UMelodiaRhythmExecutionComponent* Execution = NewObject<UMelodiaRhythmExecutionComponent>();
	TestNotNull(TEXT("Execution component can be created"), Execution);
	if (!Execution)
	{
		return false;
	}

	TestTrue(TEXT("Basic execution can start from idle"), Execution->BeginBasicExecution());
	TestTrue(TEXT("Execution is active after basic start"), Execution->IsExecutionActive());
	TestFalse(TEXT("Skill execution cannot start while another execution is active"), Execution->BeginSkillExecutionById(TEXT("Skill_Lv01_StarlitPing")));

	Execution->CancelExecution();
	TestFalse(TEXT("Execution is inactive after cancel"), Execution->IsExecutionActive());

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRhythmDamageOrderingTest, "Melodia.CoreRules.RhythmDamageOrdering", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRhythmDamageOrderingTest::RunTest(const FString& Parameters)
{
	const float BaseDamage = 25.0f;
	const float MissDamage = UMelodiaCoreRulesLibrary::CalculateRhythmDamage(BaseDamage, EMelodiaRhythmGrade::Miss);
	const float GoodDamage = UMelodiaCoreRulesLibrary::CalculateRhythmDamage(BaseDamage, EMelodiaRhythmGrade::Good);
	const float PerfectDamage = UMelodiaCoreRulesLibrary::CalculateRhythmDamage(BaseDamage, EMelodiaRhythmGrade::Perfect);

	TestTrue(TEXT("Miss damage is lower than Good damage"), MissDamage < GoodDamage);
	TestTrue(TEXT("Good damage is lower than Perfect damage"), GoodDamage < PerfectDamage);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaEncounterTriggerComponentsTest, "Melodia.CoreRules.EncounterTriggerComponents", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaEncounterTriggerComponentsTest::RunTest(const FString& Parameters)
{
	AMelodiaEncounterTrigger* Trigger = NewObject<AMelodiaEncounterTrigger>();
	TestNotNull(TEXT("Encounter trigger can be created"), Trigger);
	if (!Trigger)
	{
		return false;
	}

	TestNotNull(TEXT("Encounter trigger owns a box volume"), Trigger->TriggerVolume.Get());
	TestNotNull(TEXT("Encounter trigger owns visible label"), Trigger->EncounterLabel.Get());
	TestNotNull(TEXT("Encounter trigger owns visible light"), Trigger->EncounterLight.Get());
	TestTrue(TEXT("Encounter trigger prefers the host stock JRPG battle bridge by default"), Trigger->bPreferStockJRPGPresentation);
	TestNull(TEXT("Encounter trigger does not own a legacy rhythm execution component"), Trigger->FindComponentByClass<UMelodiaRhythmExecutionComponent>());

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaCombatStateSkillPointEconomyTest, "Melodia.CoreRules.SkillPointEconomy", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaOnboardingEnemyBalanceTest, "Melodia.CoreRules.OnboardingEnemyBalance", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaOnboardingEnemyBalanceTest::RunTest(const FString& Parameters)
{
	const TArray<FMelodiaEnemyDef> Enemies = UMelodiaEnemyDataAsset::GetDemoEnemies();
	auto Find = [&Enemies](const FName Id) -> const FMelodiaEnemyDef*
	{
		return Enemies.FindByPredicate([Id](const FMelodiaEnemyDef& Enemy) { return Enemy.EnemyId == Id; });
	};

	const FMelodiaEnemyDef* Crystal = Find(TEXT("CrystalShard"));
	const FMelodiaEnemyDef* Sakura = Find(TEXT("SakuraPhantom"));
	const FMelodiaEnemyDef* Stone = Find(TEXT("StoneGolem"));
	TestNotNull(TEXT("Crystal tutorial enemy exists"), Crystal);
	TestNotNull(TEXT("Sakura teaching enemy exists"), Sakura);
	TestNotNull(TEXT("Stone elite enemy exists"), Stone);
	if (Crystal && Sakura && Stone)
	{
		TestTrue(TEXT("HP creates increasing onboarding difficulty"), Crystal->MaxHP < Sakura->MaxHP && Sakura->MaxHP < Stone->MaxHP);
		TestTrue(TEXT("Every onboarding enemy can visibly break before defeat"), Crystal->MaxToughness < Crystal->MaxHP && Sakura->MaxToughness < Sakura->MaxHP && Stone->MaxToughness < Stone->MaxHP);
		TestTrue(TEXT("Stone remains the strongest onboarding strike"), Stone->BaseDamage > Sakura->BaseDamage && Sakura->BaseDamage > Crystal->BaseDamage);
	}
	return true;
}

bool FMelodiaCombatStateSkillPointEconomyTest::RunTest(const FString& Parameters)
{
	UMelodiaCombatStateComponent* CombatState = NewObject<UMelodiaCombatStateComponent>();
	TestNotNull(TEXT("Combat state can be created"), CombatState);
	if (!CombatState)
	{
		return false;
	}

	CombatState->SkillPointMax = 5;
	CombatState->SkillPoints = 3;
	CombatState->UltimateGauge = 60.0f;
	CombatState->ResetActionEconomy();
	TestEqual(TEXT("Encounter starts at generated shared SP"), CombatState->SkillPoints, MelodiaRulesGen::SharedSPStart);
	TestEqual(TEXT("Crescendo persists across encounter economy reset"), CombatState->UltimateGauge, 60.0f);

	CombatState->SkillPoints = 1;
	CombatState->PartyHP = 48.0f;
	CombatState->ApplyAffliction(EMelodiaSpellElement::Forte);
	CombatState->ApplyModifier(TEXT("TransientGuard"), EMelodiaModifierStat::DamageTaken, EMelodiaModifierOp::Mul, 0.8f, 2, EMelodiaModifierStacking::Refresh, 1);
	CombatState->ResetActionEconomy(false);
	TestEqual(TEXT("Sequential encounter preserves SP"), CombatState->SkillPoints, 1);
	TestEqual(TEXT("Sequential encounter preserves party HP"), CombatState->PartyHP, 48.0f);
	TestEqual(TEXT("Sequential encounter clears afflictions"), CombatState->ActiveAfflictions.Num(), 0);
	TestEqual(TEXT("Sequential encounter clears modifiers"), CombatState->ActiveModifiers.Num(), 0);

	CombatState->SkillPoints = 3;
	TestTrue(TEXT("Can spend available SP"), CombatState->CanSpendSkillPoints(3));
	TestFalse(TEXT("Cannot spend unavailable SP"), CombatState->CanSpendSkillPoints(4));

	TestTrue(TEXT("Spending available SP succeeds"), CombatState->SpendSkillPoints(2));
	TestEqual(TEXT("SP decreases by cost"), CombatState->SkillPoints, 1);
	TestEqual(TEXT("Skill activation count increments"), CombatState->SkillActivationCount, 1);

	TestEqual(TEXT("Basic SP gain clamps at max"), CombatState->AddSkillPoints(10), 5);
	TestEqual(TEXT("Basic activation count increments on positive gain"), CombatState->BasicActivationCount, 1);

	TestFalse(TEXT("Overspending fails"), CombatState->SpendSkillPoints(99));
	TestEqual(TEXT("Failed spend leaves SP unchanged"), CombatState->SkillPoints, 5);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaGeneratedModifierRulesTest, "Melodia.CoreRules.GeneratedModifiers", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaGeneratedModifierRulesTest::RunTest(const FString& Parameters)
{
	MelodiaRulesGen::FGeneratedModifier Modifier;
	TestTrue(TEXT("Crescendo modifier exists in generated registry"), MelodiaRulesGen::FindGeneratedModifier(TEXT("Crescendo_Minor"), Modifier));
	TestEqual(TEXT("Crescendo modifier targets attack"), FName(Modifier.Stat), FName(TEXT("attack")));
	TestEqual(TEXT("Crescendo modifier uses authored multiplier"), Modifier.Value, 1.1f);

	UMelodiaCombatStateComponent* CombatState = NewObject<UMelodiaCombatStateComponent>();
	TestNotNull(TEXT("Combat state can evaluate generated attack modifier"), CombatState);
	if (!CombatState)
	{
		return false;
	}

	CombatState->ApplyModifier(TEXT("Crescendo_Minor"), EMelodiaModifierStat::Attack, EMelodiaModifierOp::Mul, Modifier.Value, Modifier.DurationTurns, EMelodiaModifierStacking::Refresh, Modifier.MaxStacks);
	TestEqual(TEXT("Attack modifier changes subsequent damage base"), CombatState->EvaluateModifier(EMelodiaModifierStat::Attack, 25.0f), 27.5f);

	CombatState->EnemyToughnessMax = 10.0f;
	CombatState->ResetEnemyToughness();
	CombatState->ApplyEnemyToughnessDamage(10.0f);
	TestEqual(TEXT("Toughness damage follows generated reduction"), CombatState->LastToughnessDamage, 10.0f * MelodiaRulesGen::ToughnessReduction);
	TestEqual(TEXT("Toughness remains after one reduced hit"), CombatState->EnemyToughness, 6.0f);
	CombatState->ResetEnemyToughness();
	TestTrue(TEXT("Toughness damage opens a break follow-up"), CombatState->ApplyEnemyToughnessDamage(30.0f));
	TestTrue(TEXT("Break follow-up can be consumed once"), CombatState->ConsumeBreakFollowUp(8.0f));
	TestFalse(TEXT("Break follow-up cannot be consumed twice"), CombatState->ConsumeBreakFollowUp(8.0f));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRhythmExecutionResultPayloadTest, "Melodia.CoreRules.RhythmExecutionResultPayload", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRhythmExecutionResultPayloadTest::RunTest(const FString& Parameters)
{
	const FMelodiaRhythmExecutionResult DefaultResult;
	TestEqual(TEXT("Default result has no command"), DefaultResult.CommandType, EMelodiaRhythmCommandType::None);
	TestEqual(TEXT("Default skill cost is zero"), DefaultResult.SkillCost, 0);
	TestEqual(TEXT("Default skill scalar is neutral"), DefaultResult.SkillScalar, 1.0f);
	TestEqual(TEXT("Default average multiplier preserves miss damage"), DefaultResult.AverageGradeMultiplier, MelodiaRulesGen::MissMultiplier);
	TestEqual(TEXT("Default total notes is zero"), DefaultResult.TotalNotes, 0);

	FMelodiaRhythmExecutionResult SkillResult;
	SkillResult.CommandType = EMelodiaRhythmCommandType::Skill;
	SkillResult.SkillId = TEXT("Skill_Lv01_StarlitPing");
	SkillResult.SkillCost = 1;
	SkillResult.SkillScalar = 1.25f;
	SkillResult.AverageGradeMultiplier = 1.5f;
	SkillResult.HitCount = 2;
	SkillResult.PerfectCount = 2;
	SkillResult.MissCount = 0;
	SkillResult.TotalNotes = 2;

	TestEqual(TEXT("Skill payload keeps command type"), SkillResult.CommandType, EMelodiaRhythmCommandType::Skill);
	TestEqual(TEXT("Skill payload keeps skill id"), SkillResult.SkillId, FName(TEXT("Skill_Lv01_StarlitPing")));
	TestEqual(TEXT("Skill payload keeps hit count"), SkillResult.HitCount, 2);
	TestEqual(TEXT("Skill payload keeps perfect count"), SkillResult.PerfectCount, 2);
	TestEqual(TEXT("Skill payload keeps miss count"), SkillResult.MissCount, 0);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaCommandFeedbackRulesTest, "Melodia.CoreRules.CommandFeedback", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaCommandFeedbackRulesTest::RunTest(const FString& Parameters)
{
	UMelodiaBattleInputComponent* Input = NewObject<UMelodiaBattleInputComponent>();
	TestNotNull(TEXT("Battle input can format the selected skill"), Input);
	if (!Input)
	{
		return false;
	}

	Input->ActiveSkillId = TEXT("Skill_Lv01_StarlitPing");
	const FString Prompt = Input->GetActiveSkillPrompt();
	TestTrue(TEXT("Selected skill prompt exposes a display name"), Prompt.Contains(TEXT("Starlit")));
	TestTrue(TEXT("Selected skill prompt exposes SP cost before execution"), Prompt.Contains(TEXT("SP")));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaNPCInteractionRulesTest, "Melodia.CoreRules.NPCInteraction", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaNPCInteractionRulesTest::RunTest(const FString& Parameters)
{
	UMelodiaNPCInteractionComponent* Interaction = NewObject<UMelodiaNPCInteractionComponent>();
	TestNotNull(TEXT("NPC interaction component can be created"), Interaction);
	if (!Interaction)
	{
		return false;
	}

	Interaction->NPCId = TEXT("SD_02_PetalPriestess");
	Interaction->SpeakerName = FText::FromString(TEXT("Petal Priestess"));
	Interaction->DialogueLines = {
		FText::FromString(TEXT("The rhythm echo is awake.")),
		FText::FromString(TEXT("Trust the beat, then follow the lanterns.")),
	};
	Interaction->EncounterGuidance = FText::FromString(TEXT("The encounter waits beyond the lanterns."));

	TestTrue(TEXT("NPC exposes an interaction prompt"), !Interaction->GetPromptText().IsEmpty());
	TestTrue(TEXT("NPC interaction starts with authored dialogue"), Interaction->BeginInteraction());
	TestTrue(TEXT("Interaction remains active on first line"), Interaction->bInteractionActive);
	TestTrue(TEXT("Second dialogue line advances"), Interaction->AdvanceInteraction());
	TestTrue(TEXT("Guidance follows the final dialogue line"), Interaction->AdvanceInteraction());
	TestTrue(TEXT("Guidance is delivered once"), Interaction->bGuidanceDelivered);
	TestFalse(TEXT("Interaction finishes after guidance"), Interaction->AdvanceInteraction());
	TestFalse(TEXT("Interaction is inactive after finish"), Interaction->bInteractionActive);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaNPCBattleReferenceRulesTest, "Melodia.CoreRules.NPCBattleReferences", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaOpeningFlowRulesTest, "Melodia.CoreRules.OpeningFlow", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaOpeningFlowRulesTest::RunTest(const FString& Parameters)
{
	UGameInstance* GameInstance = NewObject<UGameInstance>();
	UMelodiaOpeningFlowSubsystem* Flow = NewObject<UMelodiaOpeningFlowSubsystem>(GameInstance);
	TestNotNull(TEXT("Opening flow can be created"), Flow);
	if (!Flow)
	{
		return false;
	}

	TestFalse(TEXT("Cannot enter Dreamstate before Sir departs"), Flow->NotifyDreamstateEntered());
	TestTrue(TEXT("Morning begins once"), Flow->BeginMorning());
	TestFalse(TEXT("Morning cannot begin twice"), Flow->BeginMorning());
	TestTrue(TEXT("Sir departure advances opening"), Flow->NotifySirDeparted());
	TestTrue(TEXT("Departure enters Dreamstate"), Flow->NotifyDreamstateEntered());
	TestTrue(TEXT("Dreamstate completion enters Zen exploration"), Flow->NotifyDreamstateCompleted());
	TestFalse(TEXT("Wrong enemy cannot unlock first dungeon"), Flow->NotifyZenEncounterVictory(TEXT("CrystalShard")));
	TestTrue(TEXT("Sakura Phantom unlocks first dungeon"), Flow->NotifyZenEncounterVictory(TEXT("SakuraPhantom")));
	TestTrue(TEXT("Opening records Heart token grant"), Flow->bHeartMelodyTokenGranted);
	TestFalse(TEXT("Repeated victory cannot unlock or grant twice"), Flow->NotifyZenEncounterVictory(TEXT("SakuraPhantom")));

	UMelodiaRoguelikeRunSubsystem* Run = NewObject<UMelodiaRoguelikeRunSubsystem>(GameInstance);
	TestEqual(TEXT("Heart token grant is explicit"), Run->GrantHeartMelodyTokens(), 1);
	TestEqual(TEXT("Invalid grant cannot remove tokens"), Run->GrantHeartMelodyTokens(-5), 1);
	Run->StartNewRun(MelodiaRulesGen::OpeningFirstDungeonSeed);
	TestEqual(TEXT("Opening Heart token survives first dungeon start"), Run->HeartMelodyTokens, 1);

	// SirRescued / ReturnedHome — zero-caller closure (Decision C, 2026-08-08)
	TestEqual(TEXT("Phase is FirstDungeonUnlocked before SirRescued"),
		Flow->Phase, EMelodiaOpeningPhase::FirstDungeonUnlocked);
	TestTrue(TEXT("SirRescued advances from FirstDungeonUnlocked"), Flow->NotifySirRescued());
	TestEqual(TEXT("Phase is SirRescued after notify"),
		Flow->Phase, EMelodiaOpeningPhase::SirRescued);
	TestFalse(TEXT("SirRescued cannot be repeated"), Flow->NotifySirRescued());
	TestTrue(TEXT("ReturnedHome advances from SirRescued"), Flow->NotifyReturnedHome());
	TestEqual(TEXT("Phase is ReturnedHome after notify"),
		Flow->Phase, EMelodiaOpeningPhase::ReturnedHome);
	TestFalse(TEXT("ReturnedHome cannot be repeated"), Flow->NotifyReturnedHome());
	TestFalse(TEXT("SirRescued fails after ReturnedHome"), Flow->NotifySirRescued());
	return true;
}

bool FMelodiaNPCBattleReferenceRulesTest::RunTest(const FString& Parameters)
{
	TSet<FName> KnownEnemyIds;
	for (const FMelodiaEnemyDef& Enemy : UMelodiaEnemyDataAsset::GetDemoEnemies())
	{
		KnownEnemyIds.Add(Enemy.EnemyId);
	}

	for (const FMelodiaNPCDefinition& NPC : UMelodiaNPCDataAsset::GetDemoNPCs())
	{
		if (!NPC.BattleEnemyId.IsNone())
		{
			TestTrue(FString::Printf(TEXT("NPC %s maps to a native battle enemy"), *NPC.NPCId.ToString()), KnownEnemyIds.Contains(NPC.BattleEnemyId));
		}
		if (!NPC.InteractionConfig.BattleEnemyId.IsNone())
		{
			TestTrue(FString::Printf(TEXT("NPC interaction %s maps to a native battle enemy"), *NPC.NPCId.ToString()), KnownEnemyIds.Contains(NPC.InteractionConfig.BattleEnemyId));
		}
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaAVTurnEconomyTest, "Melodia.CoreRules.AVTurnEconomy", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaAVTurnEconomyTest::RunTest(const FString& Parameters)
{
	// GS-003: a faster combatant accrues AV more slowly and can act twice
	// before a slow one. Player speed 160 vs enemy speed 80.
	const int32 FastCost = UMelodiaCoreRulesLibrary::CalculateAVCost(160, MelodiaRulesGen::BaseAV);
	const int32 SlowCost = UMelodiaCoreRulesLibrary::CalculateAVCost(80, MelodiaRulesGen::BaseAV);
	TestTrue(TEXT("Faster combatant pays less AV per action"), FastCost < SlowCost);

	int32 PlayerAV = FastCost;
	int32 EnemyAV = SlowCost;
	int32 PlayerActions = 0;
	// Player acts whenever PlayerAV <= EnemyAV before the enemy's AV comes due.
	while (PlayerAV <= EnemyAV)
	{
		++PlayerActions;
		PlayerAV = UMelodiaCoreRulesLibrary::AddAVCost(PlayerAV, 160, MelodiaRulesGen::BaseAV);
	}
	TestTrue(TEXT("Speed 160 acts at least twice before speed 80 acts once"), PlayerActions >= 2);

	// Delay push-back: adding a fraction of the enemy's action cost delays
	// its next turn past where it would otherwise have landed.
	const int32 DelayedEnemyAV = EnemyAV + FMath::Max(1, FMath::RoundToInt(0.5f * static_cast<float>(SlowCost)));
	TestTrue(TEXT("AV push-back defers the enemy's next action"), DelayedEnemyAV > EnemyAV);

	// Speed modifier feeds AV: HasteDance (mul 1.18) on the combat state
	// raises effective speed and therefore lowers the per-action AV cost.
	UMelodiaCombatStateComponent* CombatState = NewObject<UMelodiaCombatStateComponent>();
	TestNotNull(TEXT("Combat state can be created without a world"), CombatState);
	if (CombatState)
	{
		CombatState->ApplyModifier(TEXT("HasteDance"), EMelodiaModifierStat::Speed, EMelodiaModifierOp::Mul, 1.18f, 2, EMelodiaModifierStacking::Refresh, 1);
		const float HastedSpeed = CombatState->EvaluateModifier(EMelodiaModifierStat::Speed, 100.0f);
		TestEqual(TEXT("HasteDance raises effective speed to 118"), FMath::RoundToInt(HastedSpeed), 118);
		const int32 HastedCost = UMelodiaCoreRulesLibrary::CalculateAVCost(FMath::RoundToInt(HastedSpeed), MelodiaRulesGen::BaseAV);
		const int32 BaseCost = UMelodiaCoreRulesLibrary::CalculateAVCost(100, MelodiaRulesGen::BaseAV);
		TestTrue(TEXT("Hasted speed lowers AV cost"), HastedCost < BaseCost);
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRoguelikePhaseRulesTest, "Melodia.CoreRules.RoguelikePhaseMachine", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRoguelikePhaseRulesTest::RunTest(const FString& Parameters)
{
	UGameInstance* GameInstance = NewObject<UGameInstance>();
	UMelodiaRoguelikeRunSubsystem* Run = NewObject<UMelodiaRoguelikeRunSubsystem>(GameInstance);
	TestNotNull(TEXT("Run subsystem can be created"), Run);
	if (!Run)
	{
		return false;
	}

	Run->StagesPerDungeon = 3;
	Run->StartNewRun(1337);
	TestEqual(TEXT("New run waits for generation"), Run->Phase, EMelodiaRunPhase::Generating);
	Run->NotifyGenerationComplete(true);
	TestEqual(TEXT("Generation enters exploration"), Run->Phase, EMelodiaRunPhase::Exploring);
	TestTrue(TEXT("Encounter begins once"), Run->NotifyEncounterStarted());
	TestTrue(TEXT("Victory is recorded once"), Run->RecordEncounterResult(EMelodiaEncounterResult::Victory));
	TestEqual(TEXT("Victory presents rewards"), Run->Phase, EMelodiaRunPhase::RewardChoice);
	TestTrue(TEXT("Reward commits once"), Run->SelectReward(0));
	TestEqual(TEXT("Reward waits at the transition gate"), Run->Phase, EMelodiaRunPhase::Transitioning);
	TestEqual(TEXT("Reward does not advance the stage"), Run->CurrentStageIndex, 0);
	TestTrue(TEXT("Exit request advances exactly one stage"), Run->AdvanceStage());
	TestEqual(TEXT("Stage advanced once"), Run->CurrentStageIndex, 1);
	TestEqual(TEXT("Advance requests generation"), Run->Phase, EMelodiaRunPhase::Generating);
	TestFalse(TEXT("Duplicate advance is rejected"), Run->AdvanceStage());

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaModifierGainHooksTest, "Melodia.CoreRules.ModifierGainHooks", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaModifierGainHooksTest::RunTest(const FString& Parameters)
{
	// GS-005: UltGain/SPGain modifier stats must scale gauge/point awards, not
	// sit declared-but-unused in the registry.
	UMelodiaCombatStateComponent* CombatState = NewObject<UMelodiaCombatStateComponent>();
	TestNotNull(TEXT("Combat state can be created without a world"), CombatState);
	if (!CombatState)
	{
		return false;
	}

	CombatState->UltimateMax = 100.0f;
	CombatState->UltimateGauge = 0.0f;
	const float UnmodifiedGauge = CombatState->AddUltimateGauge(20.0f);
	TestEqual(TEXT("Unmodified UltGain applies delta as-is"), UnmodifiedGauge, 20.0f);

	CombatState->ApplyModifier(TEXT("ResonantFocus"), EMelodiaModifierStat::UltGain, EMelodiaModifierOp::Mul, 1.25f, 2, EMelodiaModifierStacking::Refresh, 1);
	const float BoostedGauge = CombatState->AddUltimateGauge(20.0f);
	TestEqual(TEXT("ResonantFocus scales UltGain by 1.25x"), BoostedGauge, 45.0f);

	CombatState->ClearModifiers();
	CombatState->SkillPointMax = 5;
	CombatState->SkillPoints = 0;
	CombatState->AddSkillPoints(1);
	TestEqual(TEXT("Unmodified SPGain applies delta as-is"), CombatState->SkillPoints, 1);

	CombatState->ApplyModifier(TEXT("TestSPBoost"), EMelodiaModifierStat::SPGain, EMelodiaModifierOp::Mul, 2.0f, 2, EMelodiaModifierStacking::Refresh, 1);
	CombatState->AddSkillPoints(1);
	TestEqual(TEXT("SPGain modifier scales positive award"), CombatState->SkillPoints, 3);

	CombatState->AddSkillPoints(-2);
	TestEqual(TEXT("SPGain modifier does not scale spending"), CombatState->SkillPoints, 1);

	return true;
}

#endif
