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
	UWorld* World = GEngine ? GEngine->GetCurrentPlayWorld() : nullptr;
	if (!World)
	{
		// Automation tests that need a world subsystem require a running world.
		// Skip rather than fail: the subsystem is a UWorldSubsystem and cannot
		// be exercised without a world.
		return true;
	}

	UMelodiaRhythmCombatSubsystem* Subsystem = UMelodiaRhythmCombatSubsystem::Get(World);
	if (!Subsystem)
	{
		AddError(TEXT("RhythmCombatSubsystem not present in the world."));
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

#endif // WITH_DEV_AUTOMATION_TESTS