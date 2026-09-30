#if WITH_DEV_AUTOMATION_TESTS

// Relative includes: this file lives in a Tests/ subdirectory, which UBT does not
// add to the module include path -- only the module root is on it.
#include "../MelodiaHybridEncounterComponent.h"
#include "../MelodiaExternalJRPGBridgeSubsystem.h"
#include "../MelodiaNarrativeSubsystem.h"
#include "../MelodiaIntegrationConfig.h"
#include "../MelodiaMusicClockSubsystem.h"
#include <limits>
#include "../MelodiaInputContextSubsystem.h"
#include "../MelodiaRhythmCombatSubsystem.h"
#include "../MelodiaRhythmSkillDefinition.h"
#include "../MelodiaWorldSlimeNode.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/SaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"
#include "UObject/ObjectMacros.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/UnrealType.h"
#if WITH_EDITOR
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "K2Node_CallFunction.h"
#include "K2Node_VariableSet.h"
#include "Kismet/KismetMathLibrary.h"
#endif

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
// The stock integration and save-codec tests below exercise the existing assets.
// Player input, presentation and process-restart proof remain live runtime gates.

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

	bool Build(FAutomationTestBase& Test, const FMelodiaNarrativeRecord* RestoredRecord = nullptr)
	{
		// Always own a standalone world. Reusing the current PIE world would let
		// this test register a skill and spawn a permanent actor in the owner's
		// live session.
		if (GEngine)
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

		UMelodiaNarrativeSubsystem* Narrative = GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>();
		if (!Test.TestNotNull(TEXT("Canonical narrative outcome authority"), Narrative)) return false;
		// Owned allowlist fixture, never mutate the project's loaded config asset.
		Narrative->Config = NewObject<UMelodiaIntegrationConfig>(GameInstance);
		Narrative->Config->EncounterIds.Add(EncounterId);
		Narrative->Config->NarrativeFlagIds.Add(TEXT("melodia_battle_won"));
		if (RestoredRecord && !Narrative->RestoreNarrativeRecord(*RestoredRecord)) return false;

		// Only a Damage/Crit skill is accepted by EnterSequence. BaseMagnitude is
		// deliberately > 1 so a compounded grade cannot pass for a single one.
		UMelodiaRhythmSkillDefinition* Definition = NewObject<UMelodiaRhythmSkillDefinition>(World);
		Definition->SkillId = SkillId;
		Definition->EffectType = EMelodiaRhythmEffectType::Damage;
		Definition->BaseMagnitude = 2.0f;
		Rhythm->RegisterSkill(Definition);
		World->InitializeActorsForPlay(FURL());

		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Slime = World->SpawnActor<AMelodiaWorldSlimeNode>(
			AMelodiaWorldSlimeNode::StaticClass(), FTransform::Identity, SpawnParams);
		if (!Test.TestTrue(TEXT("World slime spawns"), Slime != nullptr))
		{
			return false;
		}

		Slime->HybridEncounter->EncounterId = EncounterId;
		// InitializeStandalone creates a Game world but does not begin play for
		// actors spawned into this test world. Route the normal actor lifecycle so
		// the component binds to the authoritative rhythm-complete delegate.
		if (!Slime->HasActorBegunPlay())
		{
			Slime->DispatchBeginPlay();
		}
		if (!Test.TestTrue(TEXT("World slime and encounter component begin play"),
			Slime->HasActorBegunPlay() && Slime->HybridEncounter->HasBegunPlay()))
		{
			return false;
		}
		// DestroyActor routes EndPlay only for a begun world. Match that normal
		// lifecycle after assigning the authored identity and beginning the actor.
		World->SetBegunPlay(true);
		return true;
	}

	void Teardown()
	{
		if (bOwnsWorld && GameInstance && World)
		{
			UWorld* const StandaloneWorld = World;
			StandaloneWorld->EndPlay(EEndPlayReason::Quit);
			GameInstance->Shutdown();
			if (GEngine)
			{
				GEngine->DestroyWorldContext(StandaloneWorld);
			}
			StandaloneWorld->DestroyWorld(false);
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

	// World outcome stays in Narrative even without an active Quill interpreter.
	// --- FLOW finishes the encounter, exactly once --------------------------
	TestTrue(TEXT("Flow can finish the enemy"), Bridge->ApplyResolvedFlowDamage(HPAfterSequence));
	TestEqual(TEXT("The encounter reaches zero on its single HP"), Encounter->CurrentHP, 0.0f, 0.001f);
	TestTrue(TEXT("The encounter is dead"), Encounter->bIsDead);
	TestEqual(TEXT("Exactly one death transition is recorded"), Encounter->KillCount, 1);
	UMelodiaNarrativeSubsystem* Narrative = Sandbox.GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>();
	TestTrue(TEXT("One durable outcome recorded by Narrative"), Narrative->IsWorldEncounterCompleted(Identity));
	TestEqual(TEXT("Exactly one durable intent"), Narrative->GetNarrativeRecord().ConsumedIntentIds.Num(), 1);

	Bridge->ApplyResolvedFlowDamage(5.0f);
	TestEqual(TEXT("Damage after death is a no-op"), Encounter->CurrentHP, 0.0f, 0.001f);
	TestEqual(TEXT("...and it cannot produce a second outcome"), Encounter->KillCount, 1);
	TestEqual(TEXT("No second durable intent after death"), Narrative->GetNarrativeRecord().ConsumedIntentIds.Num(), 1);

	Sandbox.Teardown();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaHybridCancellationTest,
	"Melodia.Hybrid.CancelZeroAndStaleSession",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaHybridCancellationTest::RunTest(const FString& Parameters)
{
	MelodiaHybridTest::FHybridSandbox Sandbox;
	if (!Sandbox.Build(*this)) { Sandbox.Teardown(); return false; }
	UMelodiaHybridEncounterComponent* Encounter = Sandbox.Slime->HybridEncounter;
	const int32 InputDepth = Sandbox.Input->GetContextDepth();
	const float HP = Sandbox.Slime->CurrentHP;
	TestTrue(TEXT("Enter cancellable phrase"), Encounter->EnterSequence(Sandbox.SkillId));
	const int32 CancelledSession = Encounter->GetSequenceSessionId();
	TestTrue(TEXT("Cancel restores Flow"), Encounter->CancelSequence());
	TestEqual(TEXT("Cancelled input returns"), Sandbox.Input->GetContextDepth(), InputDepth);
	TestEqual(TEXT("Cancelled rhythm identity invalidated"), Sandbox.Rhythm->GetActiveSessionId(), 0);
	TestFalse(TEXT("Late cancelled damage refused"), Encounter->ApplyResolvedSequenceDamage(9.f, CancelledSession));
	TestTrue(TEXT("Re-entry after cancellation succeeds"), Encounter->EnterSequence(Sandbox.SkillId));
	const int32 NewSession = Encounter->GetSequenceSessionId();
	TestTrue(TEXT("Re-entry gets a new session"), NewSession != CancelledSession);
	TestTrue(TEXT("Phrase finishes"), Encounter->FinishSequencePhrase());
	TestFalse(TEXT("Old session cannot spend new effect"), Encounter->ApplyResolvedSequenceDamage(9.f, CancelledSession));
	TestFalse(TEXT("NaN cannot spend effect"), Encounter->ApplyResolvedSequenceDamage(std::numeric_limits<float>::quiet_NaN(), NewSession));
	TestFalse(TEXT("Pending effect still prevents exit"), Encounter->ExitSequence());
	TestTrue(TEXT("Stock zero damage consumes the matching effect"), Encounter->ApplyResolvedSequenceDamage(0.f, NewSession));
	TestFalse(TEXT("Zero effect cannot later damage"), Encounter->ApplyResolvedSequenceDamage(9.f, NewSession));
	TestTrue(TEXT("Zero result permits Flow"), Encounter->ExitSequence());
	TestEqual(TEXT("No cancellation/miss HP mutation"), Sandbox.Slime->CurrentHP, HP);
	TestEqual(TEXT("Input restored after zero result"), Sandbox.Input->GetContextDepth(), InputDepth);
	TestTrue(TEXT("Enter externally invalidated phrase"), Encounter->EnterSequence(Sandbox.SkillId));
	const int32 InvalidatedSession = Encounter->GetSequenceSessionId();
	TestTrue(TEXT("Phrase has a pending effect"), Encounter->FinishSequencePhrase());
	Sandbox.Rhythm->InvalidateSession();
	TestFalse(TEXT("Global rhythm invalidation makes old final result stale"),
		Encounter->ApplyResolvedSequenceDamage(9.f, InvalidatedSession));
	TestTrue(TEXT("Defined cancellation recovers invalidated phrase"), Encounter->CancelSequence());
	TestEqual(TEXT("Recovered input depth"), Sandbox.Input->GetContextDepth(), InputDepth);
	TestTrue(TEXT("Enter interruption phrase"), Encounter->EnterSequence(Sandbox.SkillId));
	Sandbox.Slime->Destroy();
	TestEqual(TEXT("Destruction invalidates phrase"), Sandbox.Rhythm->GetActiveSessionId(), 0);
	TestEqual(TEXT("Destruction releases input"), Sandbox.Input->GetContextDepth(), InputDepth);
	Sandbox.Teardown();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaHybridStockResolverTest,
	"Melodia.Hybrid.StockResolverReturnsToWorldHP",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaHybridStockResolverTest::RunTest(const FString& Parameters)
{
	MelodiaHybridTest::FHybridSandbox Sandbox;
	if (!Sandbox.Build(*this)) { Sandbox.Teardown(); return false; }
	UMelodiaExternalJRPGBridgeSubsystem* Bridge = Sandbox.GameInstance->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>();
	UClass* UnitClass = LoadClass<UObject>(nullptr,
		TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_UnitBase.BP_UnitBase_C"));
	UObject* Profile = UnitClass ? UnitClass->GetDefaultObject() : nullptr;
	if (!TestNotNull(TEXT("Real stock unit definition"), Profile) || !TestNotNull(TEXT("JRPG bridge"), Bridge))
	{ Sandbox.Teardown(); return false; }
	// Scoped fixture data only. Restore every authored stat before teardown;
	// production passes its existing stock definitions/live stat objects intact.
	struct FScopedStats
	{
		UObject* Object;
		TArray<TPair<FIntProperty*, int32>> Saved;
		bool Set(const TCHAR* Name, int32 Value)
		{
			FIntProperty* Property = FindFProperty<FIntProperty>(Object->GetClass(), Name);
			if (!Property) return false;
			Saved.Emplace(Property, Property->GetPropertyValue_InContainer(Object));
			Property->SetPropertyValue_InContainer(Object, Value);
			return true;
		}
		~FScopedStats() { for (const auto& Pair : Saved) Pair.Key->SetPropertyValue_InContainer(Object, Pair.Value); }
	} Stats{Profile};
	if (!Stats.Set(TEXT("minAttack"), 100) || !Stats.Set(TEXT("maxAttack"), 100)
		|| !Stats.Set(TEXT("defense"), 0) || !Stats.Set(TEXT("hit"), 100) || !Stats.Set(TEXT("speed"), 0))
	{ AddError(TEXT("Stock stat schema changed")); Sandbox.Teardown(); return false; }
	Sandbox.Slime->MaxHP = Sandbox.Slime->CurrentHP = 1000.f;
	FIntProperty* ProfileHP = FindFProperty<FIntProperty>(Profile->GetClass(), TEXT("currentHP"));
	if (!TestNotNull(TEXT("Stock stat profile retains its existing HP property"), ProfileHP))
	{ Sandbox.Teardown(); return false; }
	const int32 ProfileHPBefore = ProfileHP->GetPropertyValue_InContainer(Profile);
	UClass* CalculatorClass = LoadClass<UObject>(nullptr,
		TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.BP_BattleController_C"));
	UObject* Calculator = CalculatorClass ? CalculatorClass->GetDefaultObject() : nullptr;
	if (!TestNotNull(TEXT("Existing stock function context, no controller spawned"), Calculator))
	{ Sandbox.Teardown(); return false; }
	TArray<TPair<FObjectPropertyBase*, UObject*>> ContextBefore;
	for (const TCHAR* Name : { TEXT("currentAttackingUnit"), TEXT("currentTargetUnit"), TEXT("currentSkill") })
	{
		FObjectPropertyBase* Property = FindFProperty<FObjectPropertyBase>(CalculatorClass, Name);
		if (!Property) { AddError(TEXT("Stock context schema changed")); Sandbox.Teardown(); return false; }
		ContextBefore.Emplace(Property, Property->GetObjectPropertyValue_InContainer(Calculator));
	}
	UMelodiaHybridEncounterComponent* Encounter = Sandbox.Slime->HybridEncounter;
	const int32 Depth = Sandbox.Input->GetContextDepth();
	TestTrue(TEXT("Bind real stock calculation listener"), Bridge->BindWorldDamageResolver(Encounter, Profile, Profile, nullptr));
	TestTrue(TEXT("FLOW invokes stock resolver"), Bridge->ResolveWorldFlowAttack(Encounter));
	TestEqual(TEXT("Stock result changes single world HP"), Sandbox.Slime->CurrentHP, 900.f);
	TestTrue(TEXT("Enter authored phrase"), Encounter->EnterSequence(Sandbox.SkillId));
	const int32 Session = Encounter->GetSequenceSessionId();
	TestFalse(TEXT("Cannot replace stat inputs during phrase"), Bridge->BindWorldDamageResolver(Encounter, Profile, Profile, nullptr));
	// Current authored defaults grade an unplayed phrase Miss at 0.70.
	// BaseMagnitude=2 therefore yields 140 through stock, never 98.
	TestTrue(TEXT("Rhythm authority completes phrase"), Encounter->FinishSequencePhrase());
	TestFalse(TEXT("Production listener consumed its typed effect"), Encounter->HasPendingSequenceEffect());
	TestEqual(TEXT("Stock SEQUENCE result uses same HP"), Sandbox.Slime->CurrentHP, 760.f);
	TestFalse(TEXT("Duplicate stock callback rejected"), Encounter->ApplyResolvedSequenceDamage(200.f, Session));
	TestEqual(TEXT("Spent rhythm multiplier cleared"), Sandbox.Rhythm->GetPendingDamageMultiplier(), 1.f);
	TestTrue(TEXT("Return to Flow after real stock result"), Encounter->ExitSequence());
	TestEqual(TEXT("Input returned"), Sandbox.Input->GetContextDepth(), Depth);
	TestTrue(TEXT("Same encounter target"), Encounter->GetEncounterTarget() == Sandbox.Slime);
	TestTrue(TEXT("Subsequent Flow stock attack"), Bridge->ResolveWorldFlowAttack(Encounter));
	TestEqual(TEXT("HP persists across both modes"), Sandbox.Slime->CurrentHP, 660.f);
	UMelodiaMusicClockSubsystem* Clock = UMelodiaMusicClockSubsystem::Get(Sandbox.World);
	TestTrue(TEXT("Start the existing Harmonix clock, not a synthetic grade"), Clock && Clock->EnsureBattleControllerMusicClock());
	TestTrue(TEXT("Enter second authored phrase"), Encounter->EnterSequence(Sandbox.SkillId));
	TestTrue(TEXT("Sole rhythm grader judges a real clock lane press Perfect"),
		Encounter->RegisterSequenceLaneHit(0) == EMelodiaSkillGrade::Perfect);
	TestTrue(TEXT("Perfect phrase resolves through stock"), Encounter->FinishSequencePhrase());
	// Stock ceils its double calculation; promoted float 2*1.45 is slightly
	// greater than 2.9, so this current Blueprint returns 291, not 290 or 422.
	TestEqual(TEXT("100 * base 2 * current Perfect 1.45 exactly once, stock rounding"), Sandbox.Slime->CurrentHP, 369.f);
	TestTrue(TEXT("Return after graded result"), Encounter->ExitSequence());
	for (int32 Attack = 0; Attack < 4; ++Attack)
	{
		TestTrue(TEXT("Stock FLOW attack finishes this same encounter"), Bridge->ResolveWorldFlowAttack(Encounter));
	}
	TestEqual(TEXT("One stock-resolved death"), Sandbox.Slime->KillCount, 1);
	TestEqual(TEXT("Stock-resolved HP reaches zero"), Sandbox.Slime->CurrentHP, 0.f);
	UMelodiaNarrativeSubsystem* Narrative = Sandbox.GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>();
	TestTrue(TEXT("Stock result reached canonical durable outcome"), Narrative->IsWorldEncounterCompleted(Sandbox.EncounterId));
	TestEqual(TEXT("One durable outcome intent"), Narrative->GetNarrativeRecord().ConsumedIntentIds.Num(), 1);
	TestFalse(TEXT("No stock attack after death"), Bridge->ResolveWorldFlowAttack(Encounter));
	TestFalse(TEXT("No duplicate outcome through bridge"), Bridge->CompleteWorldEncounter(Encounter, EMelodiaBattleResult::Victory));
	TestEqual(TEXT("Duplicate leaves durable record unchanged"), Narrative->GetNarrativeRecord().ConsumedIntentIds.Num(), 1);
	TestEqual(TEXT("Stock stat profile HP was never a damage sink"), ProfileHP->GetPropertyValue_InContainer(Profile), ProfileHPBefore);
	for (const auto& Pair : ContextBefore)
	{
		TestTrue(TEXT("Borrowed stock calculation context restored after every result"),
			Pair.Key->GetObjectPropertyValue_InContainer(Calculator) == Pair.Value);
	}
	Sandbox.Teardown();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaHybridDurableReloadTest,
	"Melodia.Hybrid.DurableOutcomeSurvivesCanonicalSaveReload",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaHybridDurableReloadTest::RunTest(const FString& Parameters)
{
	MelodiaHybridTest::FHybridSandbox First;
	if (!First.Build(*this)) { First.Teardown(); return false; }
	First.Slime->HybridEncounter->ApplyResolvedFlowDamage(First.Slime->CurrentHP);
	UMelodiaNarrativeSubsystem* Narrative = First.GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>();
	UClass* SaveClass = LoadClass<USaveGame>(nullptr,
		TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGSaveGame.BP_JRPGSaveGame_C"));
	USaveGame* Save = SaveClass ? UGameplayStatics::CreateSaveGameObject(SaveClass) : nullptr;
	if (!TestNotNull(TEXT("Existing canonical JRPG save object"), Save)) { First.Teardown(); return false; }
	TestTrue(TEXT("Sync through existing Narrative/stock save adapter"), Narrative->SyncNarrativeRecordToSave(Save));
	TArray<uint8> Bytes;
	TestTrue(TEXT("Serialize with stock Unreal save codec"), UGameplayStatics::SaveGameToMemory(Save, Bytes));
	USaveGame* Loaded = UGameplayStatics::LoadGameFromMemory(Bytes);
	TestNotNull(TEXT("Stock save codec reloads object"), Loaded);
	TestTrue(TEXT("Restore through existing Narrative adapter"), Narrative->RestoreNarrativeRecordFromSave(Loaded));
	const FMelodiaNarrativeRecord Restored = Narrative->GetNarrativeRecord();
	TestEqual(TEXT("Durable outcome intent survived codec"), Restored.ConsumedIntentIds.Num(), 1);
	First.Teardown();

	MelodiaHybridTest::FHybridSandbox Reloaded;
	if (!Reloaded.Build(*this, &Restored)) { Reloaded.Teardown(); return false; }
	Narrative = Reloaded.GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>();
	TestTrue(TEXT("Fresh world restores defeated encounter"), Reloaded.Slime->bIsDead);
	TestEqual(TEXT("Single world HP restored from durable result"), Reloaded.Slime->CurrentHP, 0.f);
	TestEqual(TEXT("Restore does not emit another death"), Reloaded.Slime->KillCount, 0);
	TestFalse(TEXT("Defeated encounter cannot enter Sequence"), Reloaded.Slime->HybridEncounter->EnterSequence(Reloaded.SkillId));
	TestFalse(TEXT("Restored outcome cannot be committed again"), Narrative->CompleteWorldEncounterOutcome(Reloaded.EncounterId, EMelodiaBattleResult::Victory));
	TestEqual(TEXT("Exactly one durable intent after reload"), Narrative->GetNarrativeRecord().ConsumedIntentIds.Num(), 1);
	Reloaded.Teardown();
	return true;
}

#if WITH_EDITOR
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaHybridStockCalculationContractTest,
	"Melodia.Hybrid.StockCalculationHasNoHPWriter",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaHybridStockCalculationContractTest::RunTest(const FString& Parameters)
{
	UBlueprint* Blueprint = LoadObject<UBlueprint>(nullptr,
		TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.BP_BattleController"));
	if (!TestNotNull(TEXT("Canonical stock resolver asset"), Blueprint)) return false;
	int32 GraphsChecked = 0;
	for (UEdGraph* Graph : Blueprint->FunctionGraphs)
	{
		if (!Graph || (Graph->GetFName() != TEXT("CalculateDamage") && Graph->GetFName() != TEXT("IsHit"))) continue;
		++GraphsChecked;
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (const UK2Node_VariableSet* Write = Cast<UK2Node_VariableSet>(Node))
			{
				TestTrue(TEXT("Stock calculation writes function locals only"), Write->VariableReference.IsLocalScope());
			}
			if (const UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Node))
			{
				const UFunction* Function = Call->GetTargetFunction();
				TestTrue(TEXT("Stock calculation calls only math or stock IsHit; never HP, delegates or latent gameplay"),
					Function && (Function->GetOuterUClass() == UKismetMathLibrary::StaticClass()
						|| Function->GetFName() == TEXT("IsHit")));
			}
		}
	}
	TestEqual(TEXT("Both canonical calculation graphs checked"), GraphsChecked, 2);
	return true;
}
#endif

#endif // WITH_DEV_AUTOMATION_TESTS
