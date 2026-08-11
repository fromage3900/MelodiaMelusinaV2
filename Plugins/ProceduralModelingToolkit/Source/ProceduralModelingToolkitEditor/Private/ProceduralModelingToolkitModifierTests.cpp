#if WITH_DEV_AUTOMATION_TESTS

#include "ProceduralModelingToolkitBasicModifiers.h"
#include "ProceduralModelingToolkitModifier.h"

#include "Misc/AutomationTest.h"
#include "UDynamicMesh.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FProceduralModelingToolkitPhase4ModifiersTest,
	"ProceduralModelingToolkit.Modifiers.Phase4.ExecuteIndependently",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FProceduralModelingToolkitPhase4ModifiersTest::RunTest(const FString& Parameters)
{
	const TArray<UClass*> ModifierClasses = {
		UProceduralModelingToolkitTranslateModifier::StaticClass(),
		UProceduralModelingToolkitRotateModifier::StaticClass(),
		UProceduralModelingToolkitScaleModifier::StaticClass(),
		UProceduralModelingToolkitMirrorModifier::StaticClass(),
		UProceduralModelingToolkitNoiseModifier::StaticClass(),
		UProceduralModelingToolkitSmoothModifier::StaticClass(),
		UProceduralModelingToolkitRecomputeNormalsModifier::StaticClass()
	};

	for (UClass* ModifierClass : ModifierClasses)
	{
		const FString ModifierClassName = ModifierClass ? ModifierClass->GetName() : TEXT("None");

		UDynamicMesh* DynamicMesh = NewObject<UDynamicMesh>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
		DynamicMesh->ResetToCube();
		const int32 InitialTriangleCount = DynamicMesh->GetTriangleCount();

		UProceduralModelingToolkitModifier* Modifier = NewObject<UProceduralModelingToolkitModifier>(GetTransientPackageAsObject(), ModifierClass, NAME_None, RF_Transient);
		TestNotNull(FString::Printf(TEXT("Modifier created: %s"), *ModifierClassName), Modifier);

		FProceduralModelingToolkitModifierExecutionContext Context;
		Context.SourceAssetPath = TEXT("/Temp/TestSource");
		Context.OutputAssetPath = TEXT("/Temp/TestOutput");

		const FProceduralModelingToolkitModifierResult Result = Modifier->Execute(DynamicMesh, Context);
		TestTrue(FString::Printf(TEXT("Modifier execution succeeded: %s"), *ModifierClassName), Result.bSuccess);
		TestFalse(FString::Printf(TEXT("Dynamic mesh is not empty after modifier: %s"), *ModifierClassName), DynamicMesh->IsEmpty());
		TestTrue(FString::Printf(TEXT("Triangle count remains valid after modifier: %s"), *ModifierClassName), DynamicMesh->GetTriangleCount() > 0);

		if (!ModifierClass->IsChildOf(UProceduralModelingToolkitMirrorModifier::StaticClass()))
		{
			TestEqual(FString::Printf(TEXT("Triangle count stable for non-topology modifier: %s"), *ModifierClassName), DynamicMesh->GetTriangleCount(), InitialTriangleCount);
		}
	}

	return true;
}

#endif
