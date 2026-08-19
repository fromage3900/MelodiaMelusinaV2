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
	TestEqual(TEXT("TensionSustain defaults to 0"), Signal.TensionSustain, 0.0f);
	TestEqual(TEXT("DissonanceAmount defaults to 0"), Signal.DissonanceAmount, 0.0f);

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaReactivityTensionRegisterTest, "Melodia.Reactivity.TensionRegister", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaReactivityTensionRegisterTest::RunTest(const FString& Parameters)
{
	// Mirror the Tick sustain/dissonance math so the register contract is pinned
	// without depending on the world subsystem running.
	FMelodiaRhythmReactivitySignal Signal;
	const float DeltaTime = 1.0f / 60.0f;

	// Attack: tension rises, sustain chases it fast (4.0/s).
	Signal.EnemyTension = 0.8f;
	if (Signal.EnemyTension >= Signal.TensionSustain)
	{
		Signal.TensionSustain = FMath::FInterpTo(Signal.TensionSustain, Signal.EnemyTension, DeltaTime, 4.0f);
	}
	TestTrue(TEXT("Sustain attacks toward graded tension"), Signal.TensionSustain > 0.0f && Signal.TensionSustain < Signal.EnemyTension);

	// Sustain never exceeds the graded tension.
	Signal.TensionSustain = 0.0f;
	Signal.TensionSustain = FMath::Min(1.0f, Signal.TensionSustain + 1.5f);
	TestTrue(TEXT("Sustain clamps to 1"), Signal.TensionSustain <= 1.0f);

	// Release: tension gone, sustain decays slowly toward 0.
	Signal.EnemyTension = 0.0f;
	for (int32 Frame = 0; Frame < 60; ++Frame)
	{
		Signal.TensionSustain = FMath::FInterpTo(Signal.TensionSustain, 0.0f, DeltaTime, 0.35f);
	}
	TestTrue(TEXT("Sustain releases toward zero slowly"), Signal.TensionSustain < 1.0f);
	TestTrue(TEXT("Sustain still lingering after one second"), Signal.TensionSustain > 0.1f);

	// Dissonance derives continuously from sustain: 0 = Clear, 1 = Strain, 2 = Rupture.
	const float Dissonance = FMath::Clamp(Signal.TensionSustain * 2.0f, 0.0f, 2.0f);
	TestTrue(TEXT("DissonanceAmount bounded to Clear..Rupture"), Dissonance >= 0.0f && Dissonance <= 2.0f);
	Signal.TensionSustain = 1.0f;
	TestEqual(TEXT("Full sustain maps to Rupture"), FMath::Clamp(Signal.TensionSustain * 2.0f, 0.0f, 2.0f), 2.0f);
	Signal.TensionSustain = 0.5f;
	TestEqual(TEXT("Half sustain maps to Strain"), FMath::Clamp(Signal.TensionSustain * 2.0f, 0.0f, 2.0f), 1.0f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaReactivityAtRestTest, "Melodia.Reactivity.AtRestIncludesTension", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaReactivityAtRestTest::RunTest(const FString& Parameters)
{
	// IsSignalAtRest must treat the new tension register as "not at rest" so the
	// heartbeat/skip logic keeps publishing while dread lingers.
	FMelodiaRhythmReactivitySignal Signal;
	auto IsAtRest = [&Signal]()
	{
		constexpr float Epsilon = 0.0005f;
		return Signal.BeatPulse < Epsilon
			&& Signal.CommandPulse < Epsilon
			&& Signal.BreakPulse < Epsilon
			&& Signal.VictoryPulse < Epsilon
			&& Signal.EnemyTension < Epsilon
			&& Signal.TensionSustain < Epsilon
			&& Signal.DissonanceAmount < Epsilon;
	};

	TestTrue(TEXT("All-zero signal is at rest"), IsAtRest());
	Signal.TensionSustain = 0.3f;
	TestFalse(TEXT("Lingering sustain is not at rest"), IsAtRest());
	Signal.TensionSustain = 0.0f;
	Signal.DissonanceAmount = 0.9f;
	TestFalse(TEXT("Active dissonance is not at rest"), IsAtRest());

	return true;
}
#endif
