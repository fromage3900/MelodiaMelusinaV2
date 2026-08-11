#if WITH_DEV_AUTOMATION_TESTS

#include "../MelodiaNarrativeSubsystem.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaNarrativeSubsystemSanityTest,
	"Melodia.Integration.Narrative.Sanity",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaNarrativeSubsystemSanityTest::RunTest(const FString& Parameters)
{
	// Test that we can create a record and it has the correct default version.
	// This mirrors part of FMelodiaNarrativeRecordDefaultsTest but is a standalone sanity check
	// for the purpose of demonstrating the testing process to developers.
	FMelodiaNarrativeRecord Record;
	TestEqual(TEXT("Record version matches CurrentVersion"), Record.Version, FMelodiaNarrativeRecord::CurrentVersion);
	
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
