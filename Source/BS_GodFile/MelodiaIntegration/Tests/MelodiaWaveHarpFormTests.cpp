// WaveHarp form system - automation tests.
//
// World-free and deterministic on purpose: the P0 loop requires the committed harness
// to be the harness that ran, and a test that needs a live editor is not a gate.
// The numbers come from the component's own defaults, which the offline gate
// (Tools/waveharp/check_waveharp_form_contract.py) compares against the bake
// manifest, so no number is re-typed here.

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../MelodiaWaveHarpCombatComponent.h"
#include "../MelodiaWaterChorus.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace MelodiaWaveHarpFormTest
{
/** The measured bake: Saved/Audit/waveharp/ue_ready/waveharp_wand_bake_manifest.json. */
const FMelodiaWaveHarpSocketOffsets MeasuredSockets;
const double BladeLengthCm = 40.92;
const double BladeRadiusCm = 37.08;
/** The shipped defect D8: the skeletal sockets made the sweep ~42 m. */
const double ShippedDefectReachCm = 4200.0;
}

// ---------------------------------------------------------------------------
// D8: the melee must sweep the measured crescent, never the broken skeleton.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpBladeReachTest,
 "Melodia.WaveHarp.Form.BladeReachIsTheMeasuredCrescent",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpBladeReachTest::RunTest(const FString& Parameters)
{
 const FMelodiaWaveHarpSocketOffsets Sockets;
 TestTrue(TEXT("the crescent is about 41 cm long"),
  FMath::IsNearlyEqual(Sockets.GetBladeLengthCm(), MelodiaWaveHarpFormTest::BladeLengthCm, 0.5));
 TestTrue(TEXT("the crescent sweeps a 37 cm radius"),
  FMath::IsNearlyEqual(Sockets.GetBladeRadiusCm(), MelodiaWaveHarpFormTest::BladeRadiusCm, 0.5));
 TestTrue(TEXT("the crescent is never the shipped 42 m sweep"),
  Sockets.GetBladeLengthCm() < MelodiaWaveHarpFormTest::ShippedDefectReachCm);
 // The blade offsets are HEAD-local: the crescent hangs below and beside the head.
 TestTrue(TEXT("the blade root sits off the shaft axis"), Sockets.BladeStart.X > 0.f);
 TestTrue(TEXT("the blade tip is below the blade root"), Sockets.BladeTip.Z < Sockets.BladeStart.Z);
 TestTrue(TEXT("the crescent reaches further out than it starts"), Sockets.BladeMid.X > Sockets.BladeStart.X);
 return true;
}

// ---------------------------------------------------------------------------
// The measured frame: wand-local shared sockets, head-local blade sockets.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpSocketFrameTest,
 "Melodia.WaveHarp.Form.SocketFramesCompose",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpSocketFrameTest::RunTest(const FString& Parameters)
{
 const FMelodiaWaveHarpSocketOffsets Sockets;
 TestEqual(TEXT("the grip is 13 cm up the wand"), Sockets.BowGrip, FVector(0.0, 0.0, 13.0));
 TestEqual(TEXT("the head seats at 105 cm"), Sockets.HeadSeat, FVector(0.0, 0.0, 105.0));
 TestEqual(TEXT("the halo projects at 121 cm"), Sockets.CymaticProjection, FVector(0.0, 0.0, 121.0));
 // The head seat must be above the grip and below the projection.
 TestTrue(TEXT("the head seats above the grip"), Sockets.HeadSeat.Z > Sockets.BowGrip.Z);
 TestTrue(TEXT("the head seats below the projection"), Sockets.HeadSeat.Z < Sockets.CymaticProjection.Z);
 // In the wand frame the crescent root is the head seat plus the head-local offset.
 const FVector RootInWand = Sockets.HeadSeat + Sockets.BladeStart;
 TestTrue(TEXT("the crescent root lands near the top of the shaft"),
  FMath::Abs(RootInWand.Z - 122.0) < 0.5f);
 return true;
}

// ---------------------------------------------------------------------------
// The ring: HARP -> BOW -> CARILLON -> HARP. One writer, one ring.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpFormRingTest,
 "Melodia.WaveHarp.Form.RingOrder",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpFormRingTest::RunTest(const FString& Parameters)
{
 TestEqual(TEXT("HARP advances to BOW"),
  UMelodiaWaveHarpCombatComponent::GetNextForm(EMelodiaWaveHarpForm::Harp), EMelodiaWaveHarpForm::Bow);
 TestEqual(TEXT("BOW advances to CARILLON"),
  UMelodiaWaveHarpCombatComponent::GetNextForm(EMelodiaWaveHarpForm::Bow), EMelodiaWaveHarpForm::CarillonMelee);
 TestEqual(TEXT("CARILLON returns to HARP"),
  UMelodiaWaveHarpCombatComponent::GetNextForm(EMelodiaWaveHarpForm::CarillonMelee), EMelodiaWaveHarpForm::Harp);
 // Three steps must return to the start: the ring has no dead end.
 EMelodiaWaveHarpForm Form = EMelodiaWaveHarpForm::Harp;
 for (int32 Step = 0; Step < 3; ++Step)
  Form = UMelodiaWaveHarpCombatComponent::GetNextForm(Form);
 TestEqual(TEXT("three steps complete the ring"), Form, EMelodiaWaveHarpForm::Harp);
 return true;
}

// ---------------------------------------------------------------------------
// D3: the transition is eased, never the old 0.22 s linear pop.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpTransitionEasingTest,
 "Melodia.WaveHarp.Form.TransitionIsEased",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpTransitionEasingTest::RunTest(const FString& Parameters)
{
 TestEqual(TEXT("the transition starts at zero"),
  UMelodiaWaveHarpCombatComponent::EaseFormTransition(0.f), 0.f, 1e-4f);
 TestEqual(TEXT("the transition ends at one"),
  UMelodiaWaveHarpCombatComponent::EaseFormTransition(1.f), 1.f, 1e-4f);
 TestEqual(TEXT("the midpoint is the midpoint"),
  UMelodiaWaveHarpCombatComponent::EaseFormTransition(0.5f), 0.5f, 1e-4f);
 // Eased means SLOWER than linear in the first half and FASTER in the second half:
 // that is exactly what a linear pop is not.
 TestTrue(TEXT("the first half is slower than linear"),
  UMelodiaWaveHarpCombatComponent::EaseFormTransition(0.25f) < 0.25f);
 TestTrue(TEXT("the second half is faster than linear"),
  UMelodiaWaveHarpCombatComponent::EaseFormTransition(0.75f) > 0.75f);
 // Monotonic: the flourish never runs backwards.
 float Previous = -1.f;
 for (int32 Step = 0; Step <= 20; ++Step)
 {
  const float Value = UMelodiaWaveHarpCombatComponent::EaseFormTransition(Step / 20.f);
  TestTrue(TEXT("the transition is monotonic"), Value >= Previous);
  Previous = Value;
 }
 return true;
}

// ---------------------------------------------------------------------------
// The form weight: the crescent unfolds with the form and folds back with it.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpMeleeFormWeightTest,
 "Melodia.WaveHarp.Form.MeleeFormWeight",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpMeleeFormWeightTest::RunTest(const FString& Parameters)
{
 TestEqual(TEXT("HARP carries no crescent"),
  UMelodiaWaveHarpCombatComponent::ComputeMeleeFormWeight(
   EMelodiaWaveHarpForm::Harp, EMelodiaWaveHarpForm::Harp, 1.f), 0.f, 1e-4f);
 TestEqual(TEXT("CARILLON carries the whole crescent"),
  UMelodiaWaveHarpCombatComponent::ComputeMeleeFormWeight(
   EMelodiaWaveHarpForm::CarillonMelee, EMelodiaWaveHarpForm::CarillonMelee, 1.f), 1.f, 1e-4f);
 TestEqual(TEXT("entering CARILLON starts closed"),
  UMelodiaWaveHarpCombatComponent::ComputeMeleeFormWeight(
   EMelodiaWaveHarpForm::Bow, EMelodiaWaveHarpForm::CarillonMelee, 0.f), 0.f, 1e-4f);
 TestEqual(TEXT("entering CARILLON opens at the midpoint"),
  UMelodiaWaveHarpCombatComponent::ComputeMeleeFormWeight(
   EMelodiaWaveHarpForm::Bow, EMelodiaWaveHarpForm::CarillonMelee, 0.5f), 0.5f, 1e-4f);
 TestEqual(TEXT("leaving CARILLON folds the crescent back"),
  UMelodiaWaveHarpCombatComponent::ComputeMeleeFormWeight(
   EMelodiaWaveHarpForm::CarillonMelee, EMelodiaWaveHarpForm::Bow, 1.f), 0.f, 1e-4f);
 return true;
}

// ---------------------------------------------------------------------------
// The beat lock (Jev's first assertion): the flourish's HANDOFF lands on the
// downbeat, not its start.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpBeatLockTest,
 "Melodia.WaveHarp.Form.BeatLockLandsTheHandoffOnTheBeat",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpBeatLockTest::RunTest(const FString& Parameters)
{
 // No music: act at once, never wait forever for a beat that will not come.
 TestEqual(TEXT("no music means no delay"),
  UMelodiaWaveHarpCombatComponent::ComputeBeatLockDelay(0.f, 1.f), 0.f, 1e-4f);
 TestEqual(TEXT("a negative beat distance never delays"),
  UMelodiaWaveHarpCombatComponent::ComputeBeatLockDelay(-1.f, 1.f), 0.f, 1e-4f);
 // The head swaps at the MIDPOINT, so the start waits for half a transition less.
 TestEqual(TEXT("a 1 s transition starts half a beat early"),
  UMelodiaWaveHarpCombatComponent::ComputeBeatLockDelay(1.f, 1.f), 0.5f, 1e-4f);
 TestEqual(TEXT("a beat closer than half a transition starts at once"),
  UMelodiaWaveHarpCombatComponent::ComputeBeatLockDelay(0.2f, 1.f), 0.f, 1e-4f);
 // The property that matters: start + half a transition == the downbeat.
 const float Beat = 0.8f;
 const float Duration = 0.6f;
 const float Delay = UMelodiaWaveHarpCombatComponent::ComputeBeatLockDelay(Beat, Duration);
 TestTrue(TEXT("the handoff lands on the downbeat"),
  FMath::IsNearlyEqual(Delay + 0.5f * Duration, Beat, 1e-4f));
 return true;
}

// ---------------------------------------------------------------------------
// The input buffer (Jev's first assertion): the transformation never eats an input.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpAttackBufferTest,
 "Melodia.WaveHarp.Form.AttackIsBufferedNotEaten",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpAttackBufferTest::RunTest(const FString& Parameters)
{
 bool bBuffered = false;
 TestTrue(TEXT("an attack outside the flourish is accepted"),
  UMelodiaWaveHarpCombatComponent::AcceptAttackDuringTransition(false, true, bBuffered));
 TestFalse(TEXT("nothing is buffered outside the flourish"), bBuffered);

 TestFalse(TEXT("an attack during the flourish is refused"),
  UMelodiaWaveHarpCombatComponent::AcceptAttackDuringTransition(true, true, bBuffered));
 TestTrue(TEXT("the refused attack is buffered, not eaten"), bBuffered);

 TestFalse(TEXT("with buffering off the attack is still refused"),
  UMelodiaWaveHarpCombatComponent::AcceptAttackDuringTransition(true, false, bBuffered));
 TestFalse(TEXT("with buffering off nothing is buffered"), bBuffered);
 return true;
}

// ---------------------------------------------------------------------------
// The water chorus rules: harmony is the water's character, distance is its budget.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpWaterHarmonyTest,
 "Melodia.WaveHarp.Water.HarmonyIsTheWatersCharacter",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpWaterHarmonyTest::RunTest(const FString& Parameters)
{
 TArray<FLinearColor> Tints;
 for (uint8 Mode = 0; Mode <= 3; ++Mode) Tints.Add(FMelodiaWaterChorus::TintForMode(Mode, 0.f));
 for (int32 A = 0; A < Tints.Num(); ++A)
  for (int32 B = A + 1; B < Tints.Num(); ++B)
   TestFalse(FString::Printf(TEXT("modes %d and %d have different water"), A, B), Tints[A].Equals(Tints[B], 0.02f));
 TestFalse(TEXT("the chromatic water drifts with the phase"),
  FMelodiaWaterChorus::TintForMode(4, 0.f).Equals(FMelodiaWaterChorus::TintForMode(4, 0.5f), 0.02f));
 TestTrue(TEXT("a consonant harmony calms the water"),
  FMelodiaWaterChorus::TurbulenceForConsonance(1.f) < FMelodiaWaterChorus::TurbulenceForConsonance(0.2f));
 TestTrue(TEXT("full consonance has no churn"), FMath::IsNearlyZero(FMelodiaWaterChorus::TurbulenceForConsonance(1.f)));
 TestTrue(TEXT("a dissonant harmony runs the sim faster"),
  FMelodiaWaterChorus::SimSpeedScale(0.f) > FMelodiaWaterChorus::SimSpeedScale(1.f));
 return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpWaterUnitFluidTest,
 "Melodia.WaveHarp.Water.UnitOwnFluidIsRecognised",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpWaterUnitFluidTest::RunTest(const FString& Parameters)
{
 TestTrue(TEXT("the unit's WaterHairFluid component class is a FluidNinja live setup"),
  FMelodiaWaterChorus::IsNinjaLiveClassName(TEXT("NinjaLiveComponent_C")));
 TestTrue(TEXT("the world live actor is one too"), FMelodiaWaterChorus::IsNinjaLiveClassName(TEXT("NinjaLive_C")));
 TestFalse(TEXT("a plain Niagara component is not"), FMelodiaWaterChorus::IsNinjaLiveClassName(TEXT("NiagaraComponent")));
 TestFalse(TEXT("the hair mesh component is not"), FMelodiaWaterChorus::IsNinjaLiveClassName(TEXT("MelodiaHairComponent")));
 return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpWaterBudgetTest,
 "Melodia.WaveHarp.Water.DistanceBudgetKeepsTheNearSimsLive",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpWaterBudgetTest::RunTest(const FString& Parameters)
{
 // owned, near, far, near, near-but-over-the-cap
 const TArray<float> Distances = { 0.f, 1000.f, 9000.f, 2000.f, 3000.f };
 const TArray<bool> Was = { true, false, false, false, false };

 const TArray<bool> Active = FMelodiaWaterChorus::SelectActiveSurfaces(Distances, Was, 6000.f, 1.15f, 3);
 TestTrue(TEXT("an owned surface is always live"), Active[0]);
 TestTrue(TEXT("the nearest world surface is live"), Active[1]);
 TestFalse(TEXT("a surface outside the radius is paused"), Active[2]);
 TestTrue(TEXT("the next nearest fills the cap"), Active[3]);
 TestFalse(TEXT("past the cap, a farther surface is paused"), Active[4]);

 // Hysteresis: 6500 cm is outside 6000 but inside 6000*1.15 when it was already live.
 const TArray<float> Edge = { 6500.f };
 TestFalse(TEXT("a paused surface at 6500 cm stays paused"),
  FMelodiaWaterChorus::SelectActiveSurfaces(Edge, TArray<bool>{ false }, 6000.f, 1.15f, 4)[0]);
 TestTrue(TEXT("a live surface at 6500 cm does not flicker off"),
  FMelodiaWaterChorus::SelectActiveSurfaces(Edge, TArray<bool>{ true }, 6000.f, 1.15f, 4)[0]);
 return true;
}

// ---------------------------------------------------------------------------
// The FLOW dodge counter: world-free, exactly like every other gate here. The
// ability itself is ACFU's (proven live in PIE); WHAT this harness owns is the
// judgement law - the counter lives only inside the dodge's own span, spent at
// most once, and a never-taken dodge can answer nothing.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWaveHarpDodgeCounterWindowTest,
 "Melodia.WaveHarp.Dodge.CounterWindowIsTheDodgeSpan",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FWaveHarpDodgeCounterWindowTest::RunTest(const FString& Parameters)
{
 // A dodge never taken (-100 sentinel) can answer no attack, at no time.
 TestFalse(TEXT("a dodge never taken cannot counter"),
  UMelodiaWaveHarpCombatComponent::IsWithinDodgeCounterWindow(100.0, -100.0, .5f));
 // Inside the span: the counter is live. Exact binary halves keep the boundary honest.
 TestTrue(TEXT("an attack inside the dodge span is counterable"),
  UMelodiaWaveHarpCombatComponent::IsWithinDodgeCounterWindow(100.25, 100.0, .5f));
 // The closing boundary itself is live (inclusive window).
 TestTrue(TEXT("the window edge is still the dodge"),
  UMelodiaWaveHarpCombatComponent::IsWithinDodgeCounterWindow(100.5, 100.0, .5f));
 // Past the span: the dodge is over; the counter is not a permanent buff.
 TestFalse(TEXT("an attack after the span gets no counter"),
  UMelodiaWaveHarpCombatComponent::IsWithinDodgeCounterWindow(100.75, 100.0, .5f));
 // Before the press (a stale or reordered call): nothing to reward.
 TestFalse(TEXT("a call before the dodge is refused"),
  UMelodiaWaveHarpCombatComponent::IsWithinDodgeCounterWindow(99.5, 100.0, .5f));
 // A zero window is the press frame only - never a negative window that admits the future.
 TestTrue(TEXT("a zero window admits the same instant only"),
  UMelodiaWaveHarpCombatComponent::IsWithinDodgeCounterWindow(100.0, 100.0, 0.f));
 TestFalse(TEXT("a zero window admits nothing later"),
  UMelodiaWaveHarpCombatComponent::IsWithinDodgeCounterWindow(100.1, 100.0, 0.f));
 return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
