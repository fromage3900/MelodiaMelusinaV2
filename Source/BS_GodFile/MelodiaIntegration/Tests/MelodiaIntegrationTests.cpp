// Automation tests for the SHIPPING integration lane (Source/BS_GodFile/MelodiaIntegration).
//
// Context: before 2026-07-30 this project had 9 automation test files and 25 Python test files,
// all of them aimed at Plugins/MelodiaCore -- the quarantined lane -- and zero aimed at the code
// that actually ships. These tests exist to close that gap, starting with the paths whose silent
// failure is most expensive: save-schema migration and the no-music-clock guards.
//
// Scope note: everything here is deliberately world-free so it runs fast and cannot flake.
// Subsystem-level behaviour (intent allowlist, social-stat persistence, quest gating) needs a
// GameInstance and is the next tranche.

#if WITH_DEV_AUTOMATION_TESTS

// Relative: this file lives in a Tests/ subdirectory, which UBT does not add to
// the module include path -- only the module root is on it.
#include "../MelodiaNarrativeTypes.h"
#include "../MelodiaNarrativeSubsystem.h"
#include "../MelodiaMusicClockSubsystem.h"
#include "../MelodiaJRPGPresentationRhythmComponent.h"
#include "../MelodiaIntegrationConfig.h"
#include "MelodiaIntegrationTestSink.h"
#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "UObject/Package.h"
#include "Serialization/MemoryWriter.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/ObjectAndNameAsStringProxyArchive.h"

// ---------------------------------------------------------------------------
// Save-schema migration (Decision 013)
//
// This is the highest-value test in the file. RestoreNarrativeRecord RESETS any
// record it cannot migrate, so a broken migration path silently destroys player
// saves rather than failing loudly.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaNarrativeRecordMigrationTest,
	"Melodia.Integration.NarrativeRecord.Migration",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaNarrativeRecordMigrationTest::RunTest(const FString& Parameters)
{
	// A record already at the current version migrates trivially and is untouched.
	{
		FMelodiaNarrativeRecord Current;
		Current.Version = FMelodiaNarrativeRecord::CurrentVersion;
		Current.Flags.Add(TEXT("melodia_test_flag"), true);

		TestTrue(TEXT("Current-version record migrates"), UMelodiaNarrativeSubsystem::MigrateRecord(Current));
		TestEqual(TEXT("Version unchanged"), Current.Version, FMelodiaNarrativeRecord::CurrentVersion);
		TestEqual(TEXT("Existing flags preserved"), Current.Flags.Num(), 1);
	}

	// v1 -> v2: the real upgrade path. Pre-v2 saves carried no stats, so empty
	// maps are the truthful result -- but nothing that DID exist may be lost.
	{
		FMelodiaNarrativeRecord Legacy;
		Legacy.Version = 1;
		Legacy.Flags.Add(TEXT("melodia_opening_complete"), true);
		Legacy.ConsumedRewardIds.Add(TEXT("melodia_first_reward"));
		Legacy.ActiveQuestIds.Add(TEXT("melodia_quest_01"));
		Legacy.ScriptCheckpoint = TEXT("melodia_checkpoint_a");

		TestTrue(TEXT("v1 record migrates"), UMelodiaNarrativeSubsystem::MigrateRecord(Legacy));
		TestEqual(TEXT("v1 upgrades to CurrentVersion"), Legacy.Version, FMelodiaNarrativeRecord::CurrentVersion);

		// Nothing pre-existing may be dropped by a migration.
		TestTrue(TEXT("v1 flags survive migration"), Legacy.Flags.Contains(TEXT("melodia_opening_complete")));
		TestTrue(TEXT("v1 consumed rewards survive"), Legacy.ConsumedRewardIds.Contains(TEXT("melodia_first_reward")));
		TestTrue(TEXT("v1 active quests survive"), Legacy.ActiveQuestIds.Contains(TEXT("melodia_quest_01")));
		TestEqual(TEXT("v1 checkpoint survives"), Legacy.ScriptCheckpoint, FName(TEXT("melodia_checkpoint_a")));

		// v2 additions arrive empty, which is correct: they were never persisted before.
		TestEqual(TEXT("SocialStats start empty after upgrade"), Legacy.SocialStats.Num(), 0);
		TestEqual(TEXT("BondRanks start empty after upgrade"), Legacy.BondRanks.Num(), 0);
		TestEqual(TEXT("PhaseIndex starts at 0 after upgrade"), Legacy.PhaseIndex, 0);
		TestEqual(TEXT("SpawnContext starts empty after upgrade"), Legacy.SpawnContext.Num(), 0);
	}

	// v2 -> v3: the wardrobe bump (Decision 043). Pre-v3 saves carried no
	// wardrobe state, so empty containers are the truthful result -- but
	// nothing that DID exist may be lost.
	{
		FMelodiaNarrativeRecord WardrobeLegacy;
		WardrobeLegacy.Version = 2;
		WardrobeLegacy.Flags.Add(TEXT("melodia_opening_complete"), true);
		WardrobeLegacy.SocialStats.Add(TEXT("Harmony"), 4);

		TestTrue(TEXT("v2 record migrates to v3"), UMelodiaNarrativeSubsystem::MigrateRecord(WardrobeLegacy));
		TestEqual(TEXT("v2 upgrades to CurrentVersion"), WardrobeLegacy.Version, FMelodiaNarrativeRecord::CurrentVersion);

		// Nothing pre-existing may be dropped.
		TestTrue(TEXT("v2 flags survive v3 migration"), WardrobeLegacy.Flags.Contains(TEXT("melodia_opening_complete")));
		TestEqual(TEXT("v2 social stats survive v3 migration"), WardrobeLegacy.SocialStats.FindRef(TEXT("Harmony")), 4);

		// v3 additions arrive empty, which is correct: they were never persisted before.
		TestEqual(TEXT("OwnedCosmeticIds start empty after upgrade"), WardrobeLegacy.OwnedCosmeticIds.Num(), 0);
		TestEqual(TEXT("EquippedCosmeticIds start empty after upgrade"), WardrobeLegacy.EquippedCosmeticIds.Num(), 0);
		TestEqual(TEXT("LastPullUnixSeconds starts at 0 after upgrade"), WardrobeLegacy.LastPullUnixSeconds, 0);
	}

	// A record from a NEWER build must be refused, not partially loaded. Silently
	// accepting it would drop fields this build cannot represent.
	{
		FMelodiaNarrativeRecord FromFuture;
		FromFuture.Version = FMelodiaNarrativeRecord::CurrentVersion + 1;

		TestFalse(TEXT("Newer-than-build record is refused"), UMelodiaNarrativeSubsystem::MigrateRecord(FromFuture));
	}

	// Version 0 / uninitialised has no migration path and must be refused rather
	// than guessed at.
	{
		FMelodiaNarrativeRecord Unknown;
		Unknown.Version = 0;

		TestFalse(TEXT("Version 0 record is refused"), UMelodiaNarrativeSubsystem::MigrateRecord(Unknown));
	}

	return true;
}

// ---------------------------------------------------------------------------
// Record schema shape
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaNarrativeRecordDefaultsTest,
	"Melodia.Integration.NarrativeRecord.Defaults",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaNarrativeRecordDefaultsTest::RunTest(const FString& Parameters)
{
	const FMelodiaNarrativeRecord Fresh;

	TestEqual(TEXT("Fresh record is at CurrentVersion"), Fresh.Version, FMelodiaNarrativeRecord::CurrentVersion);
	TestEqual(TEXT("CurrentVersion is 4 (Decision 013/043 + PCG water state)"), FMelodiaNarrativeRecord::CurrentVersion, 4);
	TestEqual(TEXT("Fresh record has no flags"), Fresh.Flags.Num(), 0);
	TestEqual(TEXT("Fresh record has no social stats"), Fresh.SocialStats.Num(), 0);
	TestEqual(TEXT("Fresh record phase index is 0"), Fresh.PhaseIndex, 0);
	TestEqual(TEXT("Fresh record has no consumed intents"), Fresh.ConsumedIntentIds.Num(), 0);
	TestEqual(TEXT("Fresh record has no owned cosmetics"), Fresh.OwnedCosmeticIds.Num(), 0);
	TestEqual(TEXT("Fresh record has no equipped cosmetics"), Fresh.EquippedCosmeticIds.Num(), 0);
	TestEqual(TEXT("Fresh record last pull is 0"), Fresh.LastPullUnixSeconds, 0);

	// Guards the migration contract: bumping CurrentVersion without adding a
	// MigrateRecord case makes every existing save unloadable. If this fails,
	// add the case in MigrateRecord before changing this number.
	FMelodiaNarrativeRecord Previous;
	Previous.Version = FMelodiaNarrativeRecord::CurrentVersion - 1;
	TestTrue(
		TEXT("Every version below CurrentVersion has a migration path"),
		UMelodiaNarrativeSubsystem::MigrateRecord(Previous));

	return true;
}

// ---------------------------------------------------------------------------
// Save-flag round trip
//
// A UPROPERTY missing its SaveGame flag serializes fine in the editor and then
// silently vanishes on load -- which is exactly how SocialStats stayed transient
// while looking correct. This drives the record through a SaveGame-only archive,
// the same filtering the real save path uses, so a dropped flag fails here
// instead of in a playtest three weeks later.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaNarrativeRecordSaveFlagsTest,
	"Melodia.Integration.NarrativeRecord.SaveFlags",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaNarrativeRecordSaveFlagsTest::RunTest(const FString& Parameters)
{
	FMelodiaNarrativeRecord Source;
	Source.Flags.Add(TEXT("melodia_flag_a"), true);
	Source.Flags.Add(TEXT("melodia_flag_b"), false);
	Source.ScriptCheckpoint = TEXT("melodia_checkpoint_z");
	Source.ConsumedIntentIds.Add(TEXT("social-stat:priestess_first_echo"));
	Source.ConsumedRewardIds.Add(TEXT("melodia_reward_01"));
	Source.ActiveQuestIds.Add(TEXT("melodia_quest_02"));
	Source.SocialStats.Add(TEXT("melodia_harmony"), 3);
	Source.SocialStats.Add(TEXT("melodia_tempo"), 5);
	Source.BondRanks.Add(TEXT("melodia_bond_sir"), 2);
	Source.PhaseIndex = 7;
	Source.SpawnContext.Add(TEXT("ZenForestTest"), TEXT("SpawnTag_Clearing"));

	// Serialize through a SaveGame-filtered archive, mirroring the real save path.
	TArray<uint8> Bytes;
	{
		FMemoryWriter Writer(Bytes, /*bIsPersistent=*/true);
		FObjectAndNameAsStringProxyArchive Ar(Writer, /*bLoadIfFindFails=*/false);
		Ar.ArIsSaveGame = true;
		FMelodiaNarrativeRecord::StaticStruct()->SerializeItem(Ar, &Source, nullptr);
	}
	TestTrue(TEXT("Record produced save bytes"), Bytes.Num() > 0);

	FMelodiaNarrativeRecord Loaded;
	{
		FMemoryReader Reader(Bytes, /*bIsPersistent=*/true);
		FObjectAndNameAsStringProxyArchive Ar(Reader, /*bLoadIfFindFails=*/false);
		Ar.ArIsSaveGame = true;
		FMelodiaNarrativeRecord::StaticStruct()->SerializeItem(Ar, &Loaded, nullptr);
	}

	TestEqual(TEXT("Version round-trips"), Loaded.Version, Source.Version);
	TestEqual(TEXT("Flags round-trip"), Loaded.Flags.Num(), 2);
	TestTrue(TEXT("Flag value preserved"), Loaded.Flags.FindRef(TEXT("melodia_flag_a")));
	TestEqual(TEXT("Checkpoint round-trips"), Loaded.ScriptCheckpoint, Source.ScriptCheckpoint);
	TestTrue(TEXT("Consumed intents round-trip"), Loaded.ConsumedIntentIds.Num() == 1);
	TestTrue(TEXT("Consumed rewards round-trip"), Loaded.ConsumedRewardIds.Num() == 1);
	TestTrue(TEXT("Active quests round-trip"), Loaded.ActiveQuestIds.Num() == 1);

	// The version 2 additions. These are the ones most likely to be added without
	// the SaveGame flag, because they look correct in the editor either way.
	TestEqual(TEXT("SocialStats survive save"), Loaded.SocialStats.Num(), 2);
	TestEqual(TEXT("SocialStats value preserved"), Loaded.SocialStats.FindRef(TEXT("melodia_harmony")), 3);
	TestEqual(TEXT("BondRanks survive save"), Loaded.BondRanks.Num(), 1);
	TestEqual(TEXT("PhaseIndex survives save"), Loaded.PhaseIndex, 7);
	TestEqual(TEXT("SpawnContext survives save"), Loaded.SpawnContext.Num(), 1);
	TestEqual(TEXT("SpawnContext value preserved"),
		Loaded.SpawnContext.FindRef(TEXT("ZenForestTest")), FName(TEXT("SpawnTag_Clearing")));

	// The version 3 additions (Decision 043): wardrobe owned + equipped sets
	// must round-trip through the SaveGame-filtered archive or a wardrobe pull
	// would silently vanish across a process restart -- the exact failure mode
	// the test was written to catch for SocialStats originally.
	Source.OwnedCosmeticIds.Add(TEXT("Cos_Dress_Melusina"));
	Source.OwnedCosmeticIds.Add(TEXT("Cos_Gloves_Melusina"));
	Source.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Body, TEXT("Cos_Dress_Melusina"));
	Source.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Gloves, TEXT("Cos_Gloves_Melusina"));
	Source.LastPullUnixSeconds = 1234567890;
	{
		// Re-serialize with the wardrobe fields populated, then re-load.
		TArray<uint8> RoundTrip;
		{
			FMemoryWriter Writer(RoundTrip, true);
			FObjectAndNameAsStringProxyArchive Ar(Writer, false);
			Ar.ArIsSaveGame = true;
			FMelodiaNarrativeRecord::StaticStruct()->SerializeItem(Ar, &Source, nullptr);
		}
		FMelodiaNarrativeRecord Reloaded;
		{
			FMemoryReader Reader(RoundTrip, true);
			FObjectAndNameAsStringProxyArchive Ar(Reader, false);
			Ar.ArIsSaveGame = true;
			FMelodiaNarrativeRecord::StaticStruct()->SerializeItem(Ar, &Reloaded, nullptr);
		}
		TestEqual(TEXT("OwnedCosmeticIds survive save"), Reloaded.OwnedCosmeticIds.Num(), 2);
		TestTrue(TEXT("OwnedCosmeticIds value preserved"),
			Reloaded.OwnedCosmeticIds.Contains(TEXT("Cos_Dress_Melusina")));
		TestEqual(TEXT("EquippedCosmeticIds survive save"), Reloaded.EquippedCosmeticIds.Num(), 2);
		TestEqual(TEXT("EquippedCosmeticIds Body value preserved"),
			Reloaded.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Body), FName(TEXT("Cos_Dress_Melusina")));
		TestEqual(TEXT("EquippedCosmeticIds Gloves value preserved"),
			Reloaded.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Gloves), FName(TEXT("Cos_Gloves_Melusina")));
		TestEqual(TEXT("LastPullUnixSeconds survives save"), Reloaded.LastPullUnixSeconds, 1234567890);
	}

	// A migrated v1 record must still serialize cleanly at v2.
	FMelodiaNarrativeRecord Legacy;
	Legacy.Version = 1;
	Legacy.Flags.Add(TEXT("melodia_legacy"), true);
	TestTrue(TEXT("Legacy record migrates"), UMelodiaNarrativeSubsystem::MigrateRecord(Legacy));

	TArray<uint8> LegacyBytes;
	{
		FMemoryWriter Writer(LegacyBytes, true);
		FObjectAndNameAsStringProxyArchive Ar(Writer, false);
		Ar.ArIsSaveGame = true;
		FMelodiaNarrativeRecord::StaticStruct()->SerializeItem(Ar, &Legacy, nullptr);
	}
	TestTrue(TEXT("Migrated record serializes"), LegacyBytes.Num() > 0);

	return true;
}

// ---------------------------------------------------------------------------
// Music clock: the no-clock guards (Decision 012)
//
// Every one of these returns 0 by design. A caller that delays by these values
// degrades to "act immediately" instead of waiting forever for a beat that will
// never arrive. If any of these ever returns non-zero without a clock, turn
// transitions can deadlock.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaMusicTimeDefaultsTest,
	"Melodia.Integration.MusicClock.NoClockGuards",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaMusicTimeDefaultsTest::RunTest(const FString& Parameters)
{
	const FMelodiaMusicTime Silent;

	TestFalse(TEXT("Default music time is invalid"), Silent.bValid);
	TestEqual(TEXT("Default source is None"), Silent.Source, EMelodiaMusicClockSource::None);
	TestEqual(TEXT("Default beat phase is 0"), Silent.BeatPhase, 0.0f);
	TestEqual(TEXT("Default beat-in-bar is 0"), Silent.BeatInBar, 0.0f);
	TestEqual(TEXT("Default tempo is 0"), Silent.TempoBPM, 0.0f);
	TestEqual(TEXT("Default seconds-per-beat is 0"), Silent.SecondsPerBeat, 0.0f);
	TestEqual(TEXT("Default bar is 0"), Silent.Bar, 0);

	// Static accessors must be safe with a null world context -- they are called
	// from ambient presentation code that may run before any clock exists.
	TestEqual(TEXT("GetMusicBeatPhase(null) is 0"), UMelodiaMusicClockSubsystem::GetMusicBeatPhase(nullptr), 0.0f);
	TestEqual(TEXT("GetMusicPulse(null) is 0"), UMelodiaMusicClockSubsystem::GetMusicPulse(nullptr), 0.0f);
	TestNull(TEXT("Get(null) returns null rather than crashing"), UMelodiaMusicClockSubsystem::Get(nullptr));

	// Timebase discipline: input scoring and visuals must not share a timebase.
	TestNotEqual(
		TEXT("Input and visual timebases are distinct"),
		UMelodiaMusicClockSubsystem::InputTimebase,
		UMelodiaMusicClockSubsystem::VisualTimebase);
	TestEqual(
		TEXT("Input timebase is ExperiencedTime"),
		UMelodiaMusicClockSubsystem::InputTimebase,
		ECalibratedMusicTimebase::ExperiencedTime);
	TestEqual(
		TEXT("Visual timebase is VideoRenderTime"),
		UMelodiaMusicClockSubsystem::VisualTimebase,
		ECalibratedMusicTimebase::VideoRenderTime);

	return true;
}

// ---------------------------------------------------------------------------
// Presentation rhythm grading (Decisions 011, 016)
//
// This component grades timing for FLOURISH ONLY. It must never be wired into a
// damage path. These tests pin the boundaries and, critically, pin that a Miss
// still produces a usable result rather than a penalty.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaPresentationRhythmTest,
	"Melodia.Integration.PresentationRhythm.Grading",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaPresentationRhythmTest::RunTest(const FString& Parameters)
{
	UMelodiaJRPGPresentationRhythmComponent* Rhythm =
		NewObject<UMelodiaJRPGPresentationRhythmComponent>(GetTransientPackage());
	if (!Rhythm)
	{
		AddError(TEXT("Failed to construct UMelodiaJRPGPresentationRhythmComponent"));
		return false;
	}

	// Default windows: Perfect +/-90ms, Great +/-120ms, Good +/-160ms.
	const FJRPGPresentationRhythmResult Perfect = Rhythm->EvaluateTimingError(20.0f);
	TestEqual(TEXT("20 ms grades Perfect"), Perfect.Grade, EMelodiaRhythmGrade::Perfect);
	TestTrue(TEXT("Perfect counts as a hit"), Perfect.HitCount == 1);
	TestEqual(TEXT("Perfect records no miss"), Perfect.MissCount, 0);

	const FJRPGPresentationRhythmResult Miss = Rhythm->EvaluateTimingError(400.0f);
	TestEqual(TEXT("400 ms grades Miss"), Miss.Grade, EMelodiaRhythmGrade::Miss);
	TestEqual(TEXT("Miss records no hit"), Miss.HitCount, 0);

	// Decision 016: the rhythm layer never reduces an outcome. The presentation
	// scalar is a flourish weight, so it must stay in [0,1] and never go negative
	// -- a negative or >1 value here would be a damage-shaped signal.
	TestTrue(TEXT("Miss scalar is not negative"), Miss.PresentationScalar >= 0.0f);
	TestTrue(TEXT("Perfect scalar does not exceed 1"), Perfect.PresentationScalar <= 1.0f);
	TestTrue(TEXT("Perfect scalar exceeds Miss scalar"), Perfect.PresentationScalar > Miss.PresentationScalar);

	// Early and late must grade identically -- the component takes the absolute
	// value, so a negative error is not "extra bad".
	TestEqual(
		TEXT("Early and late grade symmetrically"),
		Rhythm->EvaluateTimingError(-100.0f).Grade,
		Rhythm->EvaluateTimingError(100.0f).Grade);

	// No world -> no music clock -> the skill must still resolve, silently and
	// without decoration, rather than blocking or erroring.
	const FJRPGPresentationRhythmResult NoClock = Rhythm->RecordInputNow();
	TestEqual(TEXT("RecordInputNow with no clock yields zero scalar"), NoClock.PresentationScalar, 0.0f);

	return true;
}

// ---------------------------------------------------------------------------
// Narrative Intent Dispatch (Decision 016, 018)
//
// Verifies that the map-based command dispatcher correctly routes Quill
// notifications to their handlers and respects the allowlist.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaNarrativeIntentTest,
	"Melodia.Integration.NarrativeIntent.Dispatch",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaNarrativeIntentTest::RunTest(const FString& Parameters)
{
	// UGameInstanceSubsystem declares ClassWithin = UGameInstance, so constructing
	// one on the transient package trips the ClassWithin ensure in
	// StaticAllocateObject (UObjectGlobals.cpp:3313). The test still ran and its
	// assertions still evaluated, but the ensure marked the whole test failed --
	// which is why this looked broken while real PIE battles worked fine.
	// A bare GameInstance is a valid outer and needs no world.
	UGameInstance* OwningGameInstance = NewObject<UGameInstance>(GetTransientPackage());
	UMelodiaNarrativeSubsystem* Subsystem = NewObject<UMelodiaNarrativeSubsystem>(OwningGameInstance);
	UMelodiaIntegrationConfig* Config = NewObject<UMelodiaIntegrationConfig>(Subsystem);
	UMelodiaIntegrationTestSink* Sink = NewObject<UMelodiaIntegrationTestSink>(GetTransientPackage());
	
	// Setup allowlist
	Config->EncounterIds.Add(TEXT("ZenForestTest"));
	Config->TravelLevelIds.Add(TEXT("L_KaleidoNave"));
	Config->NarrativeFlagIds.Add(TEXT("melodia_test_flag"));
	Config->SocialStatIds.Add(TEXT("Harmony"));
	Config->SocialStatIds.Add(TEXT("melodia_harmony"));
	Config->bStrictAiValidation = false;

	// Test SHIPPING allowlist semantics, not editor-relaxed ones. With relaxed mode
	// on (its default), unregistered ids pass silently in PIE and only hard-fail in
	// a packaged build -- so a test that leaves it on cannot prove the allowlist
	// rejects anything. This suite is the only place that difference is visible.
	Config->bRelaxedAllowlistInEditor = false;
	
	Subsystem->Config = Config;

	// Test Battle Dispatch
	{
		Subsystem->OnBattleRequested.AddDynamic(Sink, &UMelodiaIntegrationTestSink::HandleBattleRequested);
		Subsystem->OnIntentRejected.AddDynamic(Sink, &UMelodiaIntegrationTestSink::HandleIntentRejected);

		// StartBattle requires a live Quill interpreter (ActiveInterpreter) because it
		// stops the script before broadcasting. This suite is deliberately world-free,
		// so there is no interpreter to bind -- an allowlisted encounter therefore
		// reaches StartBattle and is rejected as MissingRuntime rather than dispatched.
		//
		// That distinction is the whole point: MissingRuntime proves the verb ROUTED
		// and PASSED the allowlist, which is what this dispatcher test exists to prove.
		// It previously asserted a successful broadcast, which stopped being reachable
		// when the interpreter guard was added -- the assertion was never updated.
		// Battle actually dispatching needs a PIE run, not a unit test.
		Subsystem->HandleQuillNotification(TEXT("melodia:battle:ZenForestTest"));
		TestTrue(TEXT("Allowlisted battle intent routes to StartBattle"), Sink->bBattleRejected);
		TestEqual(
			TEXT("Allowlisted battle intent fails only for want of a runtime interpreter"),
			Sink->LastRejectionReason, EMelodiaIntentFailure::MissingRuntime);
		TestFalse(
			TEXT("No battle is broadcast without an interpreter"),
			Sink->bBattleRequested);

		// An unallowlisted encounter must fail EARLIER, on the allowlist, and must
		// never reach the interpreter check.
		Sink->bBattleRejected = false;
		Subsystem->HandleQuillNotification(TEXT("melodia:battle:UnknownEncounter"));
		TestTrue(TEXT("Unallowed battle intent rejected"), Sink->bBattleRejected);
		TestEqual(
			TEXT("Unallowed battle intent is rejected by the allowlist, not the runtime check"),
			Sink->LastRejectionReason, EMelodiaIntentFailure::UnknownIdentifier);
	}

	// Test Travel Dispatch
	{
		Subsystem->OnTravelRequested.AddDynamic(Sink, &UMelodiaIntegrationTestSink::HandleTravelRequested);
		
		Subsystem->HandleQuillNotification(TEXT("melodia:travel:L_KaleidoNave"));
		TestTrue(TEXT("Allowed travel intent dispatched"), Sink->bTravelRequested);
		TestEqual(TEXT("Travel intent carries the level id"), Sink->TravelLevelId, FName(TEXT("L_KaleidoNave")));
	}

	// Test Stat Dispatch
	{
		Subsystem->OnSocialStatRequested.AddDynamic(Sink, &UMelodiaIntegrationTestSink::HandleSocialStatRequested);
		
		// Five-part authored form: melodia:stat:<IntentId>:<StatId>:<Delta>.
		// The four-part form was deleted -- nothing in Content/ ever authored it.
		Subsystem->HandleQuillNotification(TEXT("melodia:stat:test_intent:Harmony:5"));
		TestEqual(TEXT("Allowed stat intent dispatched"), Sink->StatDelta, 5);
		TestEqual(TEXT("Stat intent carries the stat id"), Sink->StatId, FName(TEXT("Harmony")));

		// The exact string authored in MelodiaQuillPetalPriestess.qsc:51. The old
		// test called AddSocialStat directly and never crossed this boundary, which
		// is why an arity mismatch here went unnoticed while a handoff doc recorded
		// the intent as "wired end-to-end (tested)". Keep this literal in sync with
		// the .qsc, and never assert the boundary by calling past it.
		Sink->StatDelta = 0;
		Subsystem->HandleQuillNotification(TEXT("melodia:stat:priestess_first_echo:melodia_harmony:1"));
		TestEqual(TEXT("Authored Priestess stat string dispatches"), Sink->StatDelta, 1);
		TestEqual(TEXT("Authored stat string carries melodia_harmony"), Sink->StatId, FName(TEXT("melodia_harmony")));

		// GrantDialogueSocialStat consumes per IntentId, so a replay must not
		// re-apply. This is what stops a Quill resume or save reload inflating
		// Harmony every time the beat is revisited.
		Sink->StatDelta = 0;
		Subsystem->HandleQuillNotification(TEXT("melodia:stat:priestess_first_echo:melodia_harmony:1"));
		TestEqual(TEXT("Repeated stat intent is consumed once"), Sink->StatDelta, 0);
	}

	// Test World State Injection
	{
		Subsystem->AddSocialStat(TEXT("Tempo"), 42);
		FString State = Subsystem->GetWorldStateForValidation();
		TestTrue(TEXT("State contains social stats"), State.Contains(TEXT("Tempo:42")));
	}

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
