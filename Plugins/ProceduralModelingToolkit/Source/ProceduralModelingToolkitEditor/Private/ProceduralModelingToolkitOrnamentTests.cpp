#if WITH_DEV_AUTOMATION_TESTS

#include "ProceduralModelingToolkitOrnamentGenerator.h"

#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FProceduralModelingToolkitOrnamentGenerationTest,
	"ProceduralModelingToolkit.Ornaments.GenerateStableSplines",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FProceduralModelingToolkitOrnamentGenerationTest::RunTest(const FString& Parameters)
{
	FProceduralModelingToolkitOrnamentSettings OrnamentSettings;
	OrnamentSettings.Kind = EProceduralModelingToolkitOrnamentKind::Vine;
	OrnamentSettings.PointCount = 32;
	OrnamentSettings.BranchCount = 3;
	OrnamentSettings.SymmetryMode = EProceduralModelingToolkitSymmetryMode::MirrorX;

	const TArray<FProceduralModelingToolkitSplinePath> OrnamentPaths = UProceduralModelingToolkitOrnamentGenerator::GenerateOrnament(OrnamentSettings);
	TestTrue(TEXT("Ornament generator created spline paths"), OrnamentPaths.Num() > 0);
	for (const FProceduralModelingToolkitSplinePath& Path : OrnamentPaths)
	{
		TestTrue(FString::Printf(TEXT("Path has stable point count: %s"), *Path.Name.ToString()), Path.Points.Num() >= 4);
	}

	FProceduralModelingToolkitFiligreeSettings FiligreeSettings;
	FiligreeSettings.LeafCount = 4;
	FiligreeSettings.FloralMotifCount = 1;

	const TArray<FProceduralModelingToolkitSplinePath> FiligreePaths = UProceduralModelingToolkitOrnamentGenerator::GenerateFiligree(FiligreeSettings);
	TestTrue(TEXT("Filigree generator created spline paths"), FiligreePaths.Num() > OrnamentPaths.Num());

	bool bFoundClosedShape = false;
	for (const FProceduralModelingToolkitSplinePath& Path : FiligreePaths)
	{
		bFoundClosedShape |= Path.bClosed;
		TestTrue(FString::Printf(TEXT("Filigree path has stable point count: %s"), *Path.Name.ToString()), Path.Points.Num() >= 4);
	}

	TestTrue(TEXT("Filigree generator created closed leaf or floral shapes"), bFoundClosedShape);
	return true;
}

#endif
