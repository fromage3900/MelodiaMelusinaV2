#if WITH_DEV_AUTOMATION_TESTS

#include "ProceduralModelingToolkitKitbashGenerator.h"

#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FProceduralModelingToolkitKitbashGenerationTest,
	"ProceduralModelingToolkit.Kitbash.GeneratePlacements",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FProceduralModelingToolkitKitbashGenerationTest::RunTest(const FString& Parameters)
{
	FProceduralModelingToolkitKitbashSocket WallSocket;
	WallSocket.Name = TEXT("Wall_A");
	WallSocket.Type = TEXT("Wall");
	WallSocket.CompatibleTypes.Add(TEXT("Arch"));

	FProceduralModelingToolkitKitbashSocket ArchSocket;
	ArchSocket.Name = TEXT("Arch_A");
	ArchSocket.Type = TEXT("Arch");
	ArchSocket.CompatibleTypes.Add(TEXT("Wall"));

	FProceduralModelingToolkitKitbashPart RootPart;
	RootPart.PartId = TEXT("RootWall");
	RootPart.Metadata.Style = EProceduralModelingToolkitArchitecturalStyle::Surreal;
	RootPart.Metadata.Weight = 1.0f;
	RootPart.Sockets.Add(WallSocket);

	FProceduralModelingToolkitKitbashPart ArchPart;
	ArchPart.PartId = TEXT("FloatingArch");
	ArchPart.Metadata.Style = EProceduralModelingToolkitArchitecturalStyle::Surreal;
	ArchPart.Metadata.Tags.Add(TEXT("Ornate"));
	ArchPart.Metadata.Weight = 2.0f;
	ArchPart.Sockets.Add(ArchSocket);

	FProceduralModelingToolkitKitbashRule Rule;
	Rule.FromSocketType = TEXT("Wall");
	Rule.ToSocketType = TEXT("Arch");
	Rule.RequiredStyle = EProceduralModelingToolkitArchitecturalStyle::Surreal;
	Rule.RequiredTags.Add(TEXT("Ornate"));
	Rule.MaxPlacements = 2;
	Rule.RotationRule = EProceduralModelingToolkitKitbashRotationRule::RandomYaw;
	Rule.ScaleRange = FVector2D(0.9, 1.1);

	FProceduralModelingToolkitKitbashSettings Settings;
	Settings.Seed = 99;
	Settings.MaxParts = 3;
	Settings.RootPartId = RootPart.PartId;
	Settings.Parts = { RootPart, ArchPart };
	Settings.Rules.Add(Rule);

	const FProceduralModelingToolkitKitbashResult Result = UProceduralModelingToolkitKitbashGenerator::GenerateKitbash(Settings);
	TestTrue(TEXT("Kitbash generation succeeded"), Result.bSuccess);
	TestEqual(TEXT("Kitbash placement count respects max parts"), Result.Placements.Num(), 3);
	TestEqual(TEXT("Root placement is first"), Result.Placements[0].PartId, RootPart.PartId);
	TestEqual(TEXT("Weighted candidate placed"), Result.Placements[1].PartId, ArchPart.PartId);

	return true;
}

#endif
