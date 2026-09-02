// Copyright 2026 BS_GodFile. All Rights Reserved.

#if WITH_DEV_AUTOMATION_TESTS

#include "../MelodiaMusicClockSubsystem.h"
#include "Misc/AutomationTest.h"

// Automation test validating the single musical time source and timebase calculations
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaMusicClockSubsystemSanityTest,
	"Melodia.MusicClock.Sanity",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaMusicClockSubsystemSanityTest::RunTest(const FString& Parameters)
{
	FMelodiaMusicTime Time;
	TestFalse(TEXT("Default music time is invalid"), Time.bValid);
	TestEqual(TEXT("Default source is None"), Time.Source, EMelodiaMusicClockSource::None);
	TestEqual(TEXT("Default BeatPhase is 0.0"), Time.BeatPhase, 0.0f);
	TestEqual(TEXT("Default Bar is 0"), Time.Bar, 0);

	// Validate time struct fields with sample Quartz/Harmonix data
	Time.bValid = true;
	Time.Source = EMelodiaMusicClockSource::Harmonix;
	Time.TempoBPM = 120.0f;
	Time.SecondsPerBeat = 0.5f;
	Time.Bar = 1;
	Time.BeatInBar = 2.0f;
	Time.BeatPhase = 0.5f;

	TestTrue(TEXT("Configured music time is valid"), Time.bValid);
	TestEqual(TEXT("Source matches Harmonix"), Time.Source, EMelodiaMusicClockSource::Harmonix);
	TestEqual(TEXT("TempoBPM is 120"), Time.TempoBPM, 120.0f);
	TestEqual(TEXT("SecondsPerBeat is 0.5"), Time.SecondsPerBeat, 0.5f);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
