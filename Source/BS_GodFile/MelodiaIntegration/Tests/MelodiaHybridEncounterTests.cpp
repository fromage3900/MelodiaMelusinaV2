#if WITH_DEV_AUTOMATION_TESTS

// Relative includes: this file lives in a Tests/ subdirectory, which UBT does not
// add to the module include path -- only the module root is on it.
#include "../MelodiaHybridEncounterComponent.h"
#include "../MelodiaInputContextSubsystem.h"
#include "../MelodiaRhythmCombatSubsystem.h"
#include "../MelodiaRhythmSkillDefinition.h"
#include "../MelodiaWorldSlimeNode.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"
#include "UObject/ObjectMacros.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/UnrealType.h"

// The convergence contract, asserted rather than described:
//
//   one encounter, two presentations, no second authority.
//
// The architectural claim is that the SAME actor survives
// Flow -> Sequence -> Flow without duplicating combat state. These tests hold
// that claim to three things that are cheap to check and expensive to get wrong:
//
//   1. the presentation component owns no combat state at all (structural);
//   2. an encounter identity and its HP survive both transitions (behavioural);
//   3. the sequence effect resolves exactly once, and the exit refuses while an
//      effect is still unresolved (idempotency).
//
// What these tests deliberately do NOT cover, because it needs a live world:
// input feel, montage presentation, and the stock resolver producing the damage
// number in the first place. Those stay owner-verified.

namespace MelodiaHybridTest
{
/** One encounter arrangement, kept alive across the whole test. */
struct FHybridSandbox
{
	UGameInstance* GameInstance = nullptr;
	UWorld* World = nullptr;
	bool bOwnsWorld = false;
	UMelodiaRhythmCombatSubsystem* Rhythm = nullptr;
	UMelodiaInputContextSubsystem* Input = nullptr;
	AMelodiaWorldSlimeNode* Slime = nullptr;
	FName EncounterId = TEXT("ENC_Test_SlimeSandbox");
	FName SkillId = TEXT("Test_HybridSequenceStrike");

	bool Build(FAutomationTestBase& Test)
	{
		World = GEngine ? GEngine->GetCurrentPlayWorld() : nullptr;
		if (!World && GEngine)
		{
			GameInstance = NewObject<UGameInstance>(GEngine);
			GameInstance->InitializeStandalone(TEXT("MelodiaHybridEncounterTestWorld"));
			World = GameInstance->GetWorld();
			bOwnsWorld = World != nullptr;
		}
		if (!World)
		{
			return false;
		}

		Rhythm = UMelodiaRhythmCombatSubsystem::Get(World);
		Input = UMelodiaInputContextSubsystem::Get(World);
		if (!Test.TestTrue(TEXT("Rhythm subsystem is present"), Rhythm != nullptr)
			|| !Test.TestTrue(TEXT("Input context subsystem is present"), Input != nullptr))
		{
			return false;
		}

		// Only a Damage/Crit skill is accepted by EnterSequence. BaseMagnitude is
		// deliberately > 1 so a compounded grade cannot pass for a single one.
		UMelodiaRhythmSkillDefinition* Definition = NewObject<UMelodiaRhythmSkillDefinition>(World);
		Definition->SkillId = SkillId;
		Definition->EffectType = EMelodiaRhythmEffectType::Damage;
		Definition->BaseMagnitude = 2.0f;
		Rhythm->RegisterSkill(Definition);

		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Slime = World->SpawnActor<AMelodiaWorldSlimeNode>(
			AMelodiaWorldSlimeNode::StaticClass(), FTransform::Identity, SpawnParams);
		if (!Test.TestTrue(TEXT("World slime spawns"), Slime != nullptr))
		{
			return false;
		}

		Slime->HybridEncounter->EncounterId = EncounterId;
		return true;
	}

	void Teardown()
	{
		if (bOwnsWorld && GameInstance && World)
		{
			GameInstance->Shutdown();
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}
		GameInstance = nullptr;
		World = nullptr;
		Rhythm = nullptr;
		Input = nullptr;
		Slime = nullptr;
	}
};
} // namespace MelodiaHybridTest

// ---------------------------------------------------------------------------
// One owner of mutable encounter state.
//
// The seductive wrong shape for a two-presentation encounter is a Flow HP and a
// Sequence HP kept in step by hand. It survives the first playtest and drifts a
// week later. This asserts the shape that cannot drift: the presentation seam
// carries no combat state, and the encounter actor carries exactly one HP.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaHybridSingleStateOwnerTest,
	"Melodia.Hybrid.SingleEncounterStateOwner",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaHybridSingleStateOwnerTest::RunTest(const FString& Parameters)
{
	UClass* Component = UMelodiaHybridEncounterComponent::StaticClass();
	if (!TestTrue(TEXT("Hybrid encounter component class resolves"), Component != nullptr))
	{
		return false;
	}

	// A mirrored HP on the presentation seam is exactly the defect this guards.
	const TCHAR* ForbiddenOnComponent[] = {
		TEXT("CurrentHP"), TEXT("MaxHP"), TEXT("HP"), TEXT("Health"), TEXT("bIsDead")
	};
	for (const TCHAR* Name : ForbiddenOnComponent)
	{
		TestTrue(
			FString::Printf(
				TEXT("Presentation seam owns no '%s' -- a mode change must not create a "
					 "second copy of combat state"), Name),
			FindFProperty<FProperty>(Component, Name) == nullptr);
	}

	// ...and it must not grade, resolve, or apply anything itself.
	const TCHAR* ForbiddenFunctions[] = {
		TEXT("SubmitResult"), TEXT("SubmitRatedInput"), TEXT("RegisterLaneHit"),
		TEXT("FinishSession"), TEXT("DealDamage")
	};
	for (const TCHAR* Name : ForbiddenFunctions)
	{
		TestTrue(
			FString::Printf(
				TEXT("Presentation seam does not implement '%s' -- it delegates rather "
					 "than becoming a second rhythm or damage authority"), Name),
			Component->FindFunctionByName(Name) == nullptr);
	}

	// No save authority either: nothing on this seam may be persisted.
	int32 SavedProperties = 0;
	for (TFieldIterator<FProperty> It(Component); It; ++It)
	{
		if (It->HasAnyPropertyFlags(CPF_SaveGame))
		{
			++SavedProperties;
		}
	}
	TestEqual(
		TEXT("Presentation seam persists nothing (no CPF_SaveGame state)"),
		SavedProperties, 0);

	// The bridge surface exists, and the transition is deliberate rather than a
	// bare mode set -- "slime means turn based" is the failure mode to avoid.
	TestTrue(
		TEXT("EnterSequence is the deliberate phrase transition"),
		Component->FindFunctionByName(TEXT("EnterSequence")) != nullptr);
	TestTrue(
		TEXT("ExitSequence restores continuous movement"),
		Component->FindFunctionByName(TEXT("ExitSequence")) != nullptr);

	// The encounter actor is the one owner, and the spike stub is gone.
	UClass* SlimeClass = AMelodiaWorldSlimeNode::StaticClass();
	TestTrue(
		TEXT("Encounter actor owns CurrentHP"),
		FindFProperty<FFloatProperty>(SlimeClass, TEXT("CurrentHP")) != nullptr);
	TestTrue(
		TEXT("Encounter actor owns MaxHP"),
		FindFProperty<FFloatProperty>(SlimeClass, TEXT("MaxHP")) != nullptr);
	TestTrue(
		TEXT("The spike's SpikeScalarStub is gone -- it stood in for a damage number "
			 "the stock resolver must supply, not a formula the world actor may own"),
		FindFProperty<FProperty>(SlimeClass, TEXT("SpikeScalarStub")) == nullptr);

	return true;
}

// ---------------------------------------------------------------------------
// The acceptance test for the whole spike.
//
// Can the same encounter survive Flow -> Sequence -> Flow without duplicating
// combat state? Damage taken in Flow, then damage resolved in Sequence, then the
// kill back in Flow -- on one actor, with one HP, one identity, one outcome.
//
// Two details are worth reading before changing this test:
//
//   * the exit is REFUSED while a sequence effect is still unresolved. That is
//     the guard that stops a mode change from stranding an authoritative result,
//     so the test asserts the refusal rather than working around it;
//   * the resolved-damage sink accepts exactly one number per session id. The
//     second call must fail, or a re-entered callback could double-hit.
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaHybridFlowSequenceFlowTest,
	"Melodia.Hybrid.FlowSequenceFlowPreservesEncounter",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaHybridFlowSequenceFlowTest::RunTest(const FString& Parameters)
{
	using namespace MelodiaHybridTest;

	FHybridSandbox Sandbox;
	if (!Sandbox.Build(*this))
	{
		Sandbox.Teardown();
		return false;
	}

	AMelodiaWorldSlimeNode* const Encounter = Sandbox.Slime;
	UMelodiaHybridEncounterComponent* const Bridge = Encounter->HybridEncounter;
	const float MaxHP = Encounter->MaxHP;
	const int32 InputDepthBefore = Sandbox.Input->GetContextDepth();

	// --- FLOW: continuous combat, one action resolves a final number ---------
	TestTrue(TEXT("Encounter starts in Flow"),
		Bridge->GetPresentationMode() == EMelodiaHybridPresentationMode::Flow);
	TestTrue(TEXT("Flow damage resolves through the sink"), Bridge->ApplyResolvedFlowDamage(3.0f));
	TestEqual(TEXT("Flow damage lands on the encounter's one HP"),
		Encounter->CurrentHP, MaxHP - 3.0f, 0.001f);

	const float HPAfterFlow = Encounter->CurrentHP;
	const FName Identity = Bridge->GetEncounterId();
	TestTrue(TEXT("The encounter carries its authored identity"), !Identity.IsNone());

	// --- FLOW -> SEQUENCE ---------------------------------------------------
	TestTrue(TEXT("The encounter enters a deliberate sequence"), Bridge->EnterSequence(Sandbox.SkillId));
	TestTrue(TEXT("Presentation is now Sequence"),
		Bridge->GetPresentationMode() == EMelodiaHybridPresentationMode::Sequence);
	TestTrue(TEXT("Entering Sequence does not create or replace the target"),
		Bridge->GetEncounterTarget() == Encounter);
	TestTrue(TEXT("Entering Sequence does not change the encounter identity"),
		Bridge->GetEncounterId() == Identity);
	TestEqual(TEXT("Entering Sequence does not reset HP"), Encounter->CurrentHP, HPAfterFlow, 0.001f);
	TestTrue(TEXT("Sequence owns input while it is live"),
		Sandbox.Input->GetContextDepth() > InputDepthBefore);
	TestTrue(TEXT("The rhythm authority is the one running the phrase"),
		Sandbox.Rhythm->GetActiveSessionId() != 0);

	// --- SEQUENCE resolves through the existing authorities ------------------
	TestTrue(TEXT("The phrase closes through the rhythm subsystem"), Bridge->FinishSequencePhrase());
	TestTrue(
		TEXT("The rhythm subsystem produced a typed effect request for this session. "
			 "If this is the only failure, the sequence path resolved without an "
			 "authoritative result, and the bridge must not apply anything."),
		Bridge->HasPendingSequenceEffect());

	TestFalse(
		TEXT("Sequence refuses to exit while its resolved effect is still pending -- "
			 "a mode change must not strand an authoritative result"),
		Bridge->ExitSequence());
	TestTrue(TEXT("...and the encounter is still in Sequence"),
		Bridge->GetPresentationMode() == EMelodiaHybridPresentationMode::Sequence);

	const int32 SequenceSessionId = Sandbox.Rhythm->GetActiveSessionId();
	TestTrue(TEXT("Sequence damage is accepted for its own session"),
		Bridge->ApplyResolvedSequenceDamage(4.0f, SequenceSessionId));
	TestEqual(TEXT("Sequence damage accumulates on the same HP"),
		Encounter->CurrentHP, HPAfterFlow - 4.0f, 0.001f);
	TestFalse(
		TEXT("A second resolved number for the same session is refused -- one grade "
			 "resolves once, however the callback is re-entered"),
		Bridge->ApplyResolvedSequenceDamage(4.0f, SequenceSessionId));
	TestEqual(TEXT("The refused duplicate changed nothing"),
		Encounter->CurrentHP, HPAfterFlow - 4.0f, 0.001f);

	// --- SEQUENCE -> FLOW ---------------------------------------------------
	const float HPAfterSequence = Encounter->CurrentHP;
	TestTrue(TEXT("The encounter returns to Flow"), Bridge->ExitSequence());
	TestTrue(TEXT("Presentation is Flow again"),
		Bridge->GetPresentationMode() == EMelodiaHybridPresentationMode::Flow);
	TestEqual(TEXT("Input is handed back"), Sandbox.Input->GetContextDepth(), InputDepthBefore);
	TestTrue(TEXT("The encounter is the same actor after two transitions"),
		Bridge->GetEncounterTarget() == Encounter);
	TestTrue(TEXT("The encounter identity survived both transitions"),
		Bridge->GetEncounterId() == Identity);
	TestEqual(TEXT("Damage taken in Flow was not restored by the mode change"),
		HPAfterSequence, HPAfterFlow - 4.0f, 0.001f);
	TestEqual(TEXT("Damage taken in Sequence survived the return to Flow"),
		Encounter->CurrentHP, HPAfterSequence, 0.001f);
	TestEqual(TEXT("Nothing rewrote the encounter definition"),
		Encounter->MaxHP, MaxHP, 0.001f);

	// --- FLOW finishes the encounter, exactly once --------------------------
	TestTrue(TEXT("Flow can finish the enemy"), Bridge->ApplyResolvedFlowDamage(HPAfterSequence));
	TestEqual(TEXT("The encounter reaches zero on its single HP"), Encounter->CurrentHP, 0.0f, 0.001f);
	TestTrue(TEXT("The encounter is dead"), Encounter->bIsDead);
	TestEqual(TEXT("Exactly one outcome is produced"), Encounter->KillCount, 1);

	Bridge->ApplyResolvedFlowDamage(5.0f);
	TestEqual(TEXT("Damage after death is a no-op"), Encounter->CurrentHP, 0.0f, 0.001f);
	TestEqual(TEXT("...and it cannot produce a second outcome"), Encounter->KillCount, 1);

	Sandbox.Teardown();
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS