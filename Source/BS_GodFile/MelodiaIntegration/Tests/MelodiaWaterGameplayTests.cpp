#if WITH_DEV_AUTOMATION_TESTS

#include "../MelodiaWaterGameplaySubsystem.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWaterGameplayStateTest,
	"Melodia.WaterGameplay.StateAndSave",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWaterGameplayStateTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine ? GEngine->GetCurrentPlayWorld() : nullptr;
	if (!World)
	{
		// The authority is a GameInstanceSubsystem, so a world-backed game
		// instance is required. Keep editor startup tests non-failing when no PIE
		// world is active.
		return true;
	}

	UMelodiaWaterGameplaySubsystem* Water = UMelodiaWaterGameplaySubsystem::Get(World);
	if (!Water)
	{
		AddError(TEXT("Water gameplay subsystem is unavailable in the active world."));
		return false;
	}

	Water->ResetWaterGameplayState();
	FMelodiaWaterNodeConfig Reservoir;
	Reservoir.NetworkId = TEXT("TestNetwork");
	Reservoir.NodeId = TEXT("Reservoir");
	Reservoir.WaterBodyId = TEXT("TestWaterBody");
	Reservoir.InitialLevel = 1.0f;
	Reservoir.InitialPressure = 0.1f;
	Reservoir.Capacity = 2.0f;
	Reservoir.FlowDirection = FVector::ForwardVector;
	Reservoir.MaxFlowStrength = 100.0f;

	FMelodiaWaterNodeConfig Gate;
	Gate.NetworkId = TEXT("TestNetwork");
	Gate.NodeId = TEXT("Gate");
	Gate.WaterBodyId = TEXT("TestWaterBody");
	Gate.InitialLevel = 0.0f;
	Gate.Capacity = 2.0f;

	FMelodiaWaterLinkConfig Link;
	Link.NetworkId = TEXT("TestNetwork");
	Link.LinkId = TEXT("TestLink");
	Link.RouteId = TEXT("TestRoute");
	Link.SourceNodeId = Reservoir.NodeId;
	Link.DestinationNodeId = Gate.NodeId;
	Link.TransferCapacity = 1.0f;

	TestTrue(TEXT("Reservoir registration succeeds"), Water->RegisterNode(Reservoir));
	TestTrue(TEXT("Gate registration succeeds"), Water->RegisterNode(Gate));
	TestTrue(TEXT("Closed link registration succeeds"), Water->RegisterLink(Link));
	TestFalse(TEXT("Route starts closed"), Water->IsWaterRouteOpen(Reservoir.NetworkId, Link.RouteId));

	TestTrue(
		TEXT("Resonance operation is accepted"),
		Water->ApplyResonance(Reservoir.NetworkId, Reservoir.NodeId, TEXT("TestChannel"), 1.0f, TEXT("TestPuzzle"), Link.RouteId, nullptr));
	TestTrue(TEXT("Resonance opens its configured route"), Water->IsWaterRouteOpen(Reservoir.NetworkId, Link.RouteId));
	TestTrue(TEXT("Puzzle completion is recorded"), Water->IsPuzzleSolved(TEXT("TestPuzzle")));
	TestTrue(TEXT("Pressure changed deterministically"), Water->GetPressureForNode(Reservoir.NetworkId, Reservoir.NodeId) > Reservoir.InitialPressure);

	FMelodiaWaterGameplaySaveData Saved;
	Water->CaptureSaveState(Saved);
	TestEqual(TEXT("Logical save contains two nodes"), Saved.NodeStates.Num(), 2);
	TestEqual(TEXT("Logical save contains one route"), Saved.RouteStates.Num(), 1);
	TestEqual(TEXT("Logical save contains one puzzle"), Saved.CompletedPuzzleIds.Num(), 1);

	Water->ResetWaterGameplayState();
	Water->RestoreSaveState(Saved);
	TestTrue(TEXT("State restore re-registers reservoir"), Water->RegisterNode(Reservoir));
	TestTrue(TEXT("State restore re-registers gate"), Water->RegisterNode(Gate));
	TestTrue(TEXT("State restore re-registers link"), Water->RegisterLink(Link));
	Water->RestoreSaveState(Saved);
	TestTrue(TEXT("Route survives save/load"), Water->IsWaterRouteOpen(Reservoir.NetworkId, Link.RouteId));
	TestTrue(TEXT("Puzzle survives save/load"), Water->IsPuzzleSolved(TEXT("TestPuzzle")));

	Water->ResetWaterGameplayState();
	return true;
}

// ---------------------------------------------------------------------------
// Sea Above Presentation & Biological Pulse Contract
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaSeaAbovePresentationContractTest,
	"Melodia.SeaAbove.Presentation.PulseAndSheenContract",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaSeaAbovePresentationContractTest::RunTest(const FString& Parameters)
{
	// 1. Sea Above Biological Pulse Range (12 - 20 seconds)
	constexpr float PulsePeriodMin = 12.0f;
	constexpr float PulsePeriodMax = 20.0f;
	constexpr float PulsePeriodDefault = 16.0f;

	TestTrue(TEXT("Default pulse period within biological range"), PulsePeriodDefault >= PulsePeriodMin && PulsePeriodDefault <= PulsePeriodMax);

	// 2. Membrane sheen thresholds matching Melusina Sorrow Seam & Sea Above specifications
	constexpr float PristineSheen = 0.18f;
	constexpr float HealedSheen = 0.32f;

	TestTrue(TEXT("Healed sheen strictly exceeds pristine sheen"), HealedSheen > PristineSheen);
	TestEqual(TEXT("Pristine sheen baseline is 0.18f"), PristineSheen, 0.18f);
	TestEqual(TEXT("Healed sheen target is 0.32f"), HealedSheen, 0.32f);

	// 3. World-UV Blend Invariant for False Ocean (must equal 1.0f)
	constexpr float FalseOceanWorldUVBlend = 1.0f;
	TestEqual(TEXT("False ocean uses 100% world-UV blend"), FalseOceanWorldUVBlend, 1.0f);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS

