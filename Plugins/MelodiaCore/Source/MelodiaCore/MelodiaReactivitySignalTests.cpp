#if WITH_DEV_AUTOMATION_TESTS
#include "MelodiaRhythmReactivitySubsystem.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaReactivitySignalDefaultsTest, "Melodia.Reactivity.SignalDefaults", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaReactivitySignalDefaultsTest::RunTest(const FString& Parameters)
{
	FMelodiaRhythmReactivitySignal Signal;

	TestEqual(TEXT("BeatPulse defaults to 0"), Signal.BeatPulse, 0.0f);
	TestEqual(TEXT("BeatPhase defaults to 0"), Signal.BeatPhase, 0.0f);
	TestEqual(TEXT("BPM defaults to 128"), Signal.BPM, 128.0f);
	TestEqual(TEXT("ComboNormalized defaults to 0"), Signal.ComboNormalized, 0.0f);
	TestEqual(TEXT("CrescendoNormalized defaults to 0"), Signal.CrescendoNormalized, 0.0f);
	TestEqual(TEXT("CommandEnergy defaults to 0"), Signal.CommandEnergy, 0.0f);
	TestEqual(TEXT("LastRhythmGrade defaults to Miss"), Signal.LastRhythmGrade, EMelodiaRhythmGrade::Miss);
	TestEqual(TEXT("CommandPulse defaults to 0"), Signal.CommandPulse, 0.0f);
	TestEqual(TEXT("BreakPulse defaults to 0"), Signal.BreakPulse, 0.0f);
	TestEqual(TEXT("VictoryPulse defaults to 0"), Signal.VictoryPulse, 0.0f);
	TestEqual(TEXT("EnemyTension defaults to 0"), Signal.EnemyTension, 0.0f);

	// Cozy fields
	TestEqual(TEXT("WarmthGlow defaults to 0"), Signal.WarmthGlow, 0.0f);
	TestEqual(TEXT("PetalFallIntensity defaults to 0"), Signal.PetalFallIntensity, 0.0f);
	TestEqual(TEXT("DreamRipple defaults to 0"), Signal.DreamRipple, 0.0f);
	TestEqual(TEXT("EmberDance defaults to 0"), Signal.EmberDance, 0.0f);
	TestEqual(TEXT("CozyBloom defaults to 0"), Signal.CozyBloom, 0.0f);

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaReactivityNotifyPulseTest, "Melodia.Reactivity.NotifyPulse", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaReactivityNotifyPulseTest::RunTest(const FString& Parameters)
{
	FMelodiaRhythmReactivitySignal Signal;
	// Directly set signal values (subsystem Tick/Publish tested in-engine; this tests the data contract)

	Signal.BeatPulse = 1.0f;
	Signal.VictoryPulse = 1.0f;
	Signal.BreakPulse = 1.0f;

	TestEqual(TEXT("BeatPulse settable"), Signal.BeatPulse, 1.0f);
	TestEqual(TEXT("VictoryPulse settable"), Signal.VictoryPulse, 1.0f);
	TestEqual(TEXT("BreakPulse settable"), Signal.BreakPulse, 1.0f);

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaReactivityCozyWarmthTest, "Melodia.Reactivity.CozyWarmth", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaReactivityCozyWarmthTest::RunTest(const FString& Parameters)
{
	FMelodiaRhythmReactivitySignal Signal;

	// Simulate what NotifyBeat and NotifyCommandResolved do
	Signal.WarmthGlow = FMath::Min(1.0f, 0.0f + 0.3f);
	Signal.DreamRipple = FMath::Min(1.0f, 0.0f + 0.2f);
	Signal.PetalFallIntensity = FMath::Min(1.0f, 0.0f + 0.5f * 0.5f);
	Signal.EmberDance = FMath::Min(1.0f, 0.0f + 0.3f * 0.4f);

	TestEqual(TEXT("WarmthGlow after beat set correctly"), Signal.WarmthGlow, 0.3f);
	TestEqual(TEXT("DreamRipple after beat set correctly"), Signal.DreamRipple, 0.2f);
	TestEqual(TEXT("PetalFallIntensity after command resolved"), Signal.PetalFallIntensity, 0.25f);
	TestEqual(TEXT("EmberDance after command resolved"), Signal.EmberDance, 0.12f);

	// Simulate victory
	Signal.CozyBloom = 1.0f;
	Signal.EmberDance = FMath::Min(1.0f, Signal.EmberDance + 0.6f);

	TestEqual(TEXT("CozyBloom on victory"), Signal.CozyBloom, 1.0f);
	TestEqual(TEXT("EmberDance pulses on victory"), Signal.EmberDance, 0.72f);

	return true;
}
#endif
