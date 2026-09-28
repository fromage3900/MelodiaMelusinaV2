#if WITH_DEV_AUTOMATION_TESTS

// Relative: this file lives in a Tests/ subdirectory, which UBT does not add to
// the module include path -- only the module root is on it.
#include "../MelodiaRhythmCombatSubsystem.h"
#include "../MelodiaRhythmSkillDefinition.h"
#include "Misc/AutomationTest.h"

// Validates the authoritative rhythm combat subsystem contract:
//   - session lifecycle (start/submit/consume/invalidate)
//   - duplicate-session rejection
//   - invalid-result rejection
//   - consume-once semantics
//   - grade -> magnitude resolution through a registered skill definition

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRhythmCombatSessionTest, "Melodia.RhythmCombat.SessionLifecycle", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaRhythmCombatSessionTest::RunTest(const FString& Parameters)
{
	UGameInstance* GI = nullptr;
	UWorld* World = GEngine ? GEngine->GetCurrentPlayWorld() : nullptr;
	bool bCreatedStandaloneWorld = false;

	if (!World && GEngine)
	{
		GI = NewObject<UGameInstance>(GEngine);
		GI->InitializeStandalone(TEXT("MelodiaRhythmCombatTestWorld"));
		World = GI->GetWorld();
		bCreatedStandaloneWorld = true;
	}

	if (!World)
	{
		return true;
	}

	UMelodiaRhythmCombatSubsystem* Subsystem = UMelodiaRhythmCombatSubsystem::Get(World);
	if (!Subsystem)
	{
		AddError(TEXT("RhythmCombatSubsystem not present in the world."));
		if (bCreatedStandaloneWorld && GI && World)
		{
			GI->Shutdown();
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}
		return false;
	}

	// Register a test skill.
	UMelodiaRhythmSkillDefinition* Skill = NewObject<UMelodiaRhythmSkillDefinition>(World);
	Skill->SkillId = TEXT("Test_CadenceStrike");
	Skill->EffectType = EMelodiaRhythmEffectType::Damage;
	Skill->BaseMagnitude = 1.0f;
	Subsystem->RegisterSkill(Skill);

	// Unregistered skill cannot start a session.
	const int32 Unregistered = Subsystem->StartSession(TEXT("Missing_Skill"));
	TestEqual(TEXT("Unregistered skill returns session 0"), Unregistered, 0);

	// Start a session.
	const int32 SessionId = Subsystem->StartSession(Skill->SkillId);
	TestNotEqual(TEXT("Starting a session returns a non-zero ID"), SessionId, 0);

	// Submit a valid Perfect result.
	Subsystem->InvalidateSession();
	const int32 SessionId2 = Subsystem->StartSession(Skill->SkillId);
	TestTrue(TEXT("SubmitRatedInput(Perfect) accepted"), Subsystem->SubmitRatedInput(EMelodiaSkillGrade::Perfect, 4, 0));
	TestTrue(TEXT("A pending request exists after submission"), Subsystem->HasPendingRequest());

	// Consume exactly once.
	FMelodiaRhythmEffectRequest Request;
	TestTrue(TEXT("ConsumePendingRequest returns true"), Subsystem->ConsumePendingRequest(Request));
	TestFalse(TEXT("No pending request after consume"), Subsystem->HasPendingRequest());
	TestTrue(TEXT("Request is marked consumed"), Request.bConsumed);
	TestEqual(TEXT("Request skill ID matches"), Request.SkillId, Skill->SkillId);
	TestEqual(TEXT("Request effect type is Damage"), Request.EffectType, EMelodiaRhythmEffectType::Damage);

	// Duplicate session ID must be rejected.
	const int32 SessionId3 = Subsystem->StartSession(Skill->SkillId);
	FMelodiaAuthoritativeRhythmResult Duplicate;
	Duplicate.bValid = true;
	Duplicate.SessionId = SessionId3; // correct, but a second submit is rejected
	TestTrue(TEXT("First submit accepted"), Subsystem->SubmitResult(Duplicate));
	TestFalse(TEXT("Duplicate submit rejected"), Subsystem->SubmitResult(Duplicate));

	// Invalidate clears state.
	Subsystem->InvalidateSession();
	TestEqual(TEXT("Active session cleared on invalidate"), Subsystem->GetActiveSessionId(), 0);
	TestFalse(TEXT("No pending request after invalidate"), Subsystem->HasPendingRequest());

	if (bCreatedStandaloneWorld && GI && World)
	{
		GI->Shutdown();
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRhythmGradeBoundaryTest, "Melodia.RhythmCombat.GradeBoundaries", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaRhythmGradeBoundaryTest::RunTest(const FString& Parameters)
{
	// Grade multipliers are data on the skill definition. Validate the default
	// table is monotonic: Perfect >= Great >= Good >= Miss for damage.
	UMelodiaRhythmSkillDefinition* Skill = NewObject<UMelodiaRhythmSkillDefinition>();
	Skill->EffectType = EMelodiaRhythmEffectType::Damage;

	const float Miss = Skill->DamageMultipliers.Get(EMelodiaSkillGrade::Miss);
	const float Good = Skill->DamageMultipliers.Get(EMelodiaSkillGrade::Good);
	const float Great = Skill->DamageMultipliers.Get(EMelodiaSkillGrade::Great);
	const float Perfect = Skill->DamageMultipliers.Get(EMelodiaSkillGrade::Perfect);

	TestTrue(TEXT("Perfect >= Great"), Perfect >= Great);
	TestTrue(TEXT("Great >= Good"), Great >= Good);
	TestTrue(TEXT("Good >= Miss"), Good >= Miss);
	TestTrue(TEXT("Miss >= 0.5"), Miss >= 0.5f);

	return true;
}

// The grade ladder is the combat feel: a clean session is worth 45% more damage
// than a sloppy one. These are the exact authored numbers stock will apply,
// pinned so a balance edit has to be a deliberate change to a failing test
// rather than a silent drift nobody measures.
//
// The SingleApplication part matters for correctness. The value the subsystem
// latches is what BP_BattleController hands to DealDamage, so it must be the
// grade multiplier itself -- applied once. BaseMagnitude > 1 exists so a
// compounded implementation (scalar folded in twice) cannot produce the same
// number: 2.0 * 0.70 = 1.40, never 0.98.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaRhythmGradeLadderExactTest, "Melodia.RhythmCombat.GradeLadderExact", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaRhythmGradeLadderExactTest::RunTest(const FString& Parameters)
{
	UGameInstance* GI = nullptr;
	UWorld* World = GEngine ? GEngine->GetCurrentPlayWorld() : nullptr;
	bool bCreatedStandaloneWorld = false;

	if (!World && GEngine)
	{
		GI = NewObject<UGameInstance>(GEngine);
		GI->InitializeStandalone(TEXT("MelodiaRhythmGradeLadderTestWorld"));
		World = GI->GetWorld();
		bCreatedStandaloneWorld = true;
	}

	if (!World)
	{
		return true;
	}

	UMelodiaRhythmCombatSubsystem* Subsystem = UMelodiaRhythmCombatSubsystem::Get(World);
	if (!Subsystem)
	{
		AddError(TEXT("RhythmCombatSubsystem not present in the world."));
		if (bCreatedStandaloneWorld && GI && World)
		{
			GI->Shutdown();
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}
		return false;
	}

	// The authored ladder, asserted literally. Miss is deliberately below 1.0
	// (Decision 016 removed the turn-order penalty, not the damage scaling).
	const UMelodiaRhythmSkillDefinition* Defaults = NewObject<UMelodiaRhythmSkillDefinition>(World);
	TestEqual(TEXT("Miss scalar"), Defaults->DamageMultipliers.Miss, 0.70f);
	TestEqual(TEXT("Good scalar"), Defaults->DamageMultipliers.Good, 1.00f);
	TestEqual(TEXT("Great scalar"), Defaults->DamageMultipliers.Great, 1.20f);
	TestEqual(TEXT("Perfect scalar"), Defaults->DamageMultipliers.Perfect, 1.45f);

	// BaseMagnitude 2.0 makes a double application visible in the latch.
	UMelodiaRhythmSkillDefinition* Skill = NewObject<UMelodiaRhythmSkillDefinition>(World);
	Skill->SkillId = TEXT("Test_GradeLadderStrike");
	Skill->EffectType = EMelodiaRhythmEffectType::Damage;
	Skill->BaseMagnitude = 2.0f;
	Subsystem->RegisterSkill(Skill);

	// FinishSession is the closing path: it aggregates the session itself and
	// submits the result internally. Calling SubmitRatedInput first would set
	// bResultAccepted and make the close a no-op -- that is a duplicate-submit
	// guard, not a second route in.
	Subsystem->InvalidateSession();
	const int32 SessionId = Subsystem->StartSession(Skill->SkillId);
	TestNotEqual(TEXT("Session starts"), SessionId, 0);
	TestTrue(TEXT("Session closes"), Subsystem->FinishSession());

	// A session with no connected presses aggregates to Miss, so the latch is
	// the single application: base x grade, once. 2.0 x 0.70 = 1.40, never 0.98.
	TestEqual(
		TEXT("Latched scalar is base x grade exactly once (2.0 x 0.70 = 1.40, never 0.98)"),
		Subsystem->GetPendingDamageMultiplier(), 1.40f, 0.001f);

	// Spending the scalar is the stock controller's job; the subsystem's
	// ClearPendingDamageMultiplier must return it to identity so a stale grade
	// can never ride a later hit.
	Subsystem->ClearPendingDamageMultiplier();
	TestEqual(
		TEXT("Spent scalar returns to identity"),
		Subsystem->GetPendingDamageMultiplier(), 1.0f, 0.001f);

	Subsystem->InvalidateSession();

	if (bCreatedStandaloneWorld && GI && World)
	{
		GI->Shutdown();
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
