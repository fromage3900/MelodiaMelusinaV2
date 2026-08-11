// Wiring-contract tests for the shipping integration lane.
//
// WHY THIS FILE EXISTS
//
// Every assertion below corresponds to a defect that actually shipped into the
// project and survived review, because the thing that was wrong looked correct in
// every graph read and every handoff doc:
//
//   * BP_BattleUI was never instantiated. ShowBattleUI had a live exec chain, so
//     it read as wired -- but nothing created the widget, so its target was null
//     and OnKeyDown, the rhythm highway, keyboard focus and teardown were all
//     dead code. Verifying a call site is not verifying the call.
//   * All eight rhythm skills had PatternAsset unset, so every session ran
//     uncharted and no notes ever scrolled. The minigame had authored data that
//     nothing referenced.
//   * The Harmony social-stat gate was unreachable, so two of three authored
//     quests could never be entered.
//   * RewardEquipment was hand-seeded and is NOT written by
//     author_melodia_persona_foundation.py -- re-running that script silently
//     drops it.
//
// These are asset-graph facts, not behaviour, so they are cheap to assert and
// they fail loudly the moment a seam goes dead. A red test here replaces a doc
// claim that someone would otherwise have to re-verify by hand -- which is the
// specific failure mode that cost this project the most time.
//
// SCOPE: these tests prove things are CONNECTED. They do not prove the loop
// PLAYS -- that still needs a PIE run comparing damage with the rhythm layer on
// against `melodia.Rhythm.Disable 1` (Decision 024).
//
// Do NOT use a full-Perfect vs full-Miss comparison as that A/B. Decision 016
// sets no miss penalty, ever, so both runs are expected to deal the same damage
// and the test would read as a false failure.

#if WITH_EDITOR && WITH_DEV_AUTOMATION_TESTS

// Relative: this file lives in Tests/, which UBT does not add to the module
// include path -- only the module root is on it.
#include "../MelodiaIntegrationConfig.h"
#include "../MelodiaPersonaTypes.h"
#include "../MelodiaRhythmSkillDefinition.h"
#include "../MelodiaStockContract.h"
#include "Misc/AutomationTest.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/ARFilter.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "UObject/SoftObjectPath.h"

namespace MelodiaWiringContract
{
	const TCHAR* const ConfigPath = TEXT("/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig.DA_MelodiaIntegrationConfig");
	const TCHAR* const PersonaPath = TEXT("/Game/MelodiaIntegration/Config/DA_MelodiaPersonaContent.DA_MelodiaPersonaContent");
	const TCHAR* const BattleControllerPath = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.BP_BattleController");
	const TCHAR* const SkillConfigDir = TEXT("/Game/MelodiaIntegration/Config");

	template <typename T>
	T* LoadChecked(FAutomationTestBase& Test, const TCHAR* Path)
	{
		T* Asset = LoadObject<T>(nullptr, Path);
		if (!Asset)
		{
			Test.AddError(FString::Printf(TEXT("Could not load required asset: %s"), Path));
		}
		return Asset;
	}

	/** All rhythm skill definitions discovered the same way the subsystem discovers them. */
	TArray<UMelodiaRhythmSkillDefinition*> GatherSkills()
	{
		TArray<UMelodiaRhythmSkillDefinition*> Skills;

		FAssetRegistryModule& AssetRegistry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
		AssetRegistry.Get().SearchAllAssets(/*bSynchronousSearch=*/true);

		FARFilter Filter;
		Filter.ClassPaths.Add(UMelodiaRhythmSkillDefinition::StaticClass()->GetClassPathName());
		Filter.bRecursivePaths = true;
		Filter.PackagePaths.Add(FName(SkillConfigDir));

		TArray<FAssetData> Found;
		AssetRegistry.Get().GetAssets(Filter, Found);
		for (const FAssetData& Data : Found)
		{
			if (UMelodiaRhythmSkillDefinition* Skill = Cast<UMelodiaRhythmSkillDefinition>(Data.GetAsset()))
			{
				Skills.Add(Skill);
			}
		}
		return Skills;
	}
}

// ---------------------------------------------------------------------------
// The battle UI must actually be created.
//
// BP_BattleUI owns OnKeyDown (Q/W/O/P -> RegisterLaneHit), OnKeyUp (the same
// four keys -> SetLanePressed false), ShowBattleUI (which creates and binds the
// rhythm highway) and HideBattleUI. If no node constructs it, every one of those
// is unreachable and the rhythm layer silently does nothing -- which is exactly
// what happened.
//
// The live copy is /Game/TurnBasedJRPGTemplate/... There is a second, complete
// copy under /Game/_ThirdParty/TurnBasedJRPGTemplate/ with its own
// BP_BattleController; it is a self-contained island that nothing in Melodia
// references. The substring match below cannot tell the two apart, so it passes
// whichever one you edited -- confirm the path before authoring.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWiringBattleUICreatedTest,
	"Melodia.Wiring.BattleUI.IsConstructed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWiringBattleUICreatedTest::RunTest(const FString& Parameters)
{
	using namespace MelodiaWiringContract;

	// Qualified deliberately: MelodiaStockContract.cpp declares an anonymous-namespace
	// constant of the same name, and a unity build merges both into one translation
	// unit, making the unqualified name ambiguous.
	UBlueprint* Controller = LoadChecked<UBlueprint>(*this, MelodiaWiringContract::BattleControllerPath);
	if (!Controller)
	{
		return false;
	}

	// Look for any node in any graph that references BP_BattleUI as a class. A
	// CreateWidget node stores it as a pin default, so a substring match over the
	// node's pins is both sufficient and resilient to node-id drift (node ids in
	// this Blueprint have changed repeatedly and must never be asserted on).
	bool bFound = false;
	TArray<UEdGraph*> Graphs;
	Controller->GetAllGraphs(Graphs);
	for (const UEdGraph* Graph : Graphs)
	{
		if (!Graph) { continue; }
		for (const UEdGraphNode* Node : Graph->Nodes)
		{
			if (!Node) { continue; }
			for (const UEdGraphPin* Pin : Node->Pins)
			{
				if (!Pin) { continue; }
				const bool bMentionsBattleUI =
					Pin->DefaultValue.Contains(TEXT("BP_BattleUI")) ||
					(Pin->DefaultObject && Pin->DefaultObject->GetPathName().Contains(TEXT("BP_BattleUI")));
				if (bMentionsBattleUI)
				{
					bFound = true;
					break;
				}
			}
			if (bFound) { break; }
		}
		if (bFound) { break; }
	}

	TestTrue(
		TEXT("BP_BattleController constructs BP_BattleUI. If this fails, the rhythm highway, "
			 "Q/W/O/P lane input and keyboard focus are all unreachable regardless of how they are wired."),
		bFound);

	return true;
}

// ---------------------------------------------------------------------------
// Every rhythm skill must have a chart.
//
// LoadChartForSkill returns false when PatternAsset does not resolve to a
// UMelodiaSongDataAsset with at least one chart. The session then runs
// "uncharted": the highway spawns, the lanes render, and no notes ever scroll.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWiringSkillChartsTest,
	"Melodia.Wiring.RhythmSkills.HaveCharts",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWiringSkillChartsTest::RunTest(const FString& Parameters)
{
	using namespace MelodiaWiringContract;

	const TArray<UMelodiaRhythmSkillDefinition*> Skills = GatherSkills();
	TestTrue(TEXT("At least one rhythm skill definition is discoverable"), Skills.Num() > 0);

	for (const UMelodiaRhythmSkillDefinition* Skill : Skills)
	{
		if (!Skill) { continue; }

		const FString SkillName = Skill->SkillId.ToString();

		TestFalse(
			FString::Printf(TEXT("Skill '%s' has a SkillId"), *Skill->GetName()),
			Skill->SkillId.IsNone());

		// A soft pointer that is merely non-null still resolves to nothing if the
		// asset was deleted, so assert on the load, not on IsNull().
		const bool bChartResolves = !Skill->PatternAsset.IsNull() && Skill->PatternAsset.LoadSynchronous() != nullptr;
		TestTrue(
			FString::Printf(
				TEXT("Skill '%s' has a PatternAsset that resolves. Without it the session runs "
					 "uncharted and no notes appear on the highway."),
				*SkillName),
			bChartResolves);

		TestTrue(
			FString::Printf(TEXT("Skill '%s' has a positive TempoBPM"), *SkillName),
			Skill->TempoBPM > 0.0f);

		// StartSession computes SessionEndBeat as IntroBeats + max(1, ActiveBeats).
		// A non-positive ActiveBeats would make the window degenerate.
		TestTrue(
			FString::Printf(TEXT("Skill '%s' has ActiveBeats >= 1"), *SkillName),
			Skill->ActiveBeats >= 1);
	}

	return true;
}

// ---------------------------------------------------------------------------
// Stock-skill -> rhythm-id mappings must resolve on both sides.
//
// A key that names a class which no longer exists, or a value naming a skill id
// nothing authors, is a silent no-op: StartSession returns 0 and the skill just
// quietly loses its minigame.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWiringSkillMappingTest,
	"Melodia.Wiring.RhythmSkills.MappingResolves",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWiringSkillMappingTest::RunTest(const FString& Parameters)
{
	using namespace MelodiaWiringContract;

	UMelodiaIntegrationConfig* Config = LoadChecked<UMelodiaIntegrationConfig>(*this, ConfigPath);
	if (!Config)
	{
		return false;
	}

	TSet<FName> AuthoredSkillIds;
	for (const UMelodiaRhythmSkillDefinition* Skill : GatherSkills())
	{
		if (Skill && !Skill->SkillId.IsNone())
		{
			AuthoredSkillIds.Add(Skill->SkillId);
		}
	}

	TestTrue(
		TEXT("StockSkillRhythmIds has at least one mapping. An empty map means no skill "
			 "ever starts a rhythm session."),
		Config->StockSkillRhythmIds.Num() > 0);

	for (const TPair<FName, FName>& Pair : Config->StockSkillRhythmIds)
	{
		TestTrue(
			FString::Printf(
				TEXT("StockSkillRhythmIds value '%s' (for stock class '%s') names an authored rhythm skill"),
				*Pair.Value.ToString(), *Pair.Key.ToString()),
			AuthoredSkillIds.Contains(Pair.Value));

		// Keys are runtime generated-class names, e.g. BP_FocusAttack_C. A key
		// missing the _C suffix will never match GetClass()->GetFName() at runtime
		// and is therefore dead -- a mistake that produces no error anywhere.
		TestTrue(
			FString::Printf(
				TEXT("StockSkillRhythmIds key '%s' looks like a generated class name (expected a _C suffix)"),
				*Pair.Key.ToString()),
			Pair.Key.ToString().EndsWith(TEXT("_C")));
	}

	return true;
}

// ---------------------------------------------------------------------------
// Persona content must agree with the narrative allowlist.
//
// The allowlist is the gate every Quill intent passes through. An authored id
// that is not allowlisted is rejected at runtime -- and because
// bRelaxedAllowlistInEditor lets unregistered ids through in PIE, this class of
// defect is invisible until a Shipping build.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWiringPersonaAllowlistTest,
	"Melodia.Wiring.Persona.AllowlistAgreement",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWiringPersonaAllowlistTest::RunTest(const FString& Parameters)
{
	using namespace MelodiaWiringContract;

	UMelodiaIntegrationConfig* Config = LoadChecked<UMelodiaIntegrationConfig>(*this, ConfigPath);
	UMelodiaPersonaContent* Persona = LoadChecked<UMelodiaPersonaContent>(*this, PersonaPath);
	if (!Config || !Persona)
	{
		return false;
	}

	TSet<FName> EquipmentIds;
	for (const FMelodiaEquipmentDefinition& Equipment : Persona->Equipment)
	{
		EquipmentIds.Add(Equipment.EquipmentId);
	}

	for (const FMelodiaQuestDefinition& Quest : Persona->Quests)
	{
		const FString QuestName = Quest.QuestId.ToString();

		TestTrue(
			FString::Printf(TEXT("Quest '%s' is allowlisted in Config->QuestIds"), *QuestName),
			Config->QuestIds.Contains(Quest.QuestId));

		if (!Quest.RewardId.IsNone())
		{
			TestTrue(
				FString::Printf(TEXT("Quest '%s' reward '%s' is allowlisted"), *QuestName, *Quest.RewardId.ToString()),
				Config->DialogueRewardIds.Contains(Quest.RewardId));
		}

		if (!Quest.CompletionFlagId.IsNone())
		{
			TestTrue(
				FString::Printf(TEXT("Quest '%s' completion flag '%s' is allowlisted"), *QuestName, *Quest.CompletionFlagId.ToString()),
				Config->NarrativeFlagIds.Contains(Quest.CompletionFlagId));
		}

		// This is the assertion that would have caught the unreachable Harmony
		// gate: a quest gated on a social stat nothing is permitted to grant can
		// never be entered, and its whole downstream chain dies with it.
		if (!Quest.RequiredSocialStatId.IsNone())
		{
			TestTrue(
				FString::Printf(
					TEXT("Quest '%s' is gated on social stat '%s', which must be allowlisted or the quest "
						 "is permanently unreachable"),
					*QuestName, *Quest.RequiredSocialStatId.ToString()),
				Config->SocialStatIds.Contains(Quest.RequiredSocialStatId));
		}

		// A prerequisite naming a quest that does not exist locks the chain.
		if (!Quest.PrerequisiteQuestId.IsNone())
		{
			const bool bPrereqExists = Persona->Quests.ContainsByPredicate(
				[&Quest](const FMelodiaQuestDefinition& Other) { return Other.QuestId == Quest.PrerequisiteQuestId; });
			TestTrue(
				FString::Printf(TEXT("Quest '%s' prerequisite '%s' names a real quest"), *QuestName, *Quest.PrerequisiteQuestId.ToString()),
				bPrereqExists);
		}
	}

	// RewardEquipment is hand-seeded and is NOT written by
	// author_melodia_persona_foundation.py. If that script is re-run, this map is
	// silently emptied and every quest reward becomes a no-op that still consumes
	// its once-only id.
	TestTrue(
		TEXT("RewardEquipment is populated. It is hand-seeded and not restored by the persona "
			 "authoring script, so an empty map here usually means the script was re-run."),
		Persona->RewardEquipment.Num() > 0);

	for (const TPair<FName, FName>& Pair : Persona->RewardEquipment)
	{
		TestTrue(
			FString::Printf(TEXT("RewardEquipment reward '%s' is allowlisted"), *Pair.Key.ToString()),
			Config->DialogueRewardIds.Contains(Pair.Key));

		TestTrue(
			FString::Printf(
				TEXT("RewardEquipment maps '%s' to equipment '%s', which must exist in Persona->Equipment"),
				*Pair.Key.ToString(), *Pair.Value.ToString()),
			EquipmentIds.Contains(Pair.Value));
	}

	// Every equipment definition must name a stock item, or RequestEquip cannot
	// resolve a class and the grant fails after the reward is already consumed.
	for (const FMelodiaEquipmentDefinition& Equipment : Persona->Equipment)
	{
		TestFalse(
			FString::Printf(TEXT("Equipment '%s' names a StockItemAssetId"), *Equipment.EquipmentId.ToString()),
			Equipment.StockItemAssetId.IsNone());
	}

	return true;
}

// ---------------------------------------------------------------------------
// The stock-Blueprint name contract.
//
// The integration layer reaches into stock Blueprints by name in ~29 places.
// Every one compiles regardless of whether the name still exists, so a rename on
// the Blueprint side turns into a silent runtime no-op -- exactly how Sir was
// "recruited" into a party he never joined, and how BP_BattleUI::battleController
// sat null with four readers and no writer.
//
// This asserts only that the names RESOLVE with the expected shape. It is
// deliberately cheap and deliberately narrow; behaviour is not in scope. The
// manifest lives in MelodiaStockContract.cpp and carries an explicit list of
// seams NOT yet asserted, each pending one editor read before it is added.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWiringStockContractTest,
	"Melodia.Wiring.StockContract.Resolves",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWiringStockContractTest::RunTest(const FString& Parameters)
{
	TArray<FMelodiaStockSeamResult> Results;
	const int32 BrokenCount = FMelodiaStockContract::Validate(Results);

	TestTrue(TEXT("The stock-contract manifest is not empty"), Results.Num() > 0);

	for (const FMelodiaStockSeamResult& Result : Results)
	{
		// Describe() states what was expected AND what was found, so a red here is
		// actionable without opening the editor to work out which half is wrong.
		TestTrue(Result.Describe(), !Result.IsBroken());
	}

	return BrokenCount == 0;
}

#endif // WITH_EDITOR && WITH_DEV_AUTOMATION_TESTS
