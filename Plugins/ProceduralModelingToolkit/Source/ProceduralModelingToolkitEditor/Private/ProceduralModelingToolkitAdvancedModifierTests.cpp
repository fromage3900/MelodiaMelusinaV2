#if WITH_DEV_AUTOMATION_TESTS

#include "ProceduralModelingToolkitAdvancedModifiers.h"
#include "ProceduralModelingToolkitModifier.h"

#include "Misc/AutomationTest.h"
#include "UDynamicMesh.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FProceduralModelingToolkitPhase5ModifiersTest,
	"ProceduralModelingToolkit.Modifiers.Phase5.ExecuteIndependently",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FProceduralModelingToolkitPhase5ModifiersTest::RunTest(const FString& Parameters)
{
	const TArray<UClass*> ModifierClasses = {
		UProceduralModelingToolkitExtrudeModifier::StaticClass(),
		UProceduralModelingToolkitInsetModifier::StaticClass(),
		UProceduralModelingToolkitRemeshModifier::StaticClass(),
		UProceduralModelingToolkitSimplifyModifier::StaticClass(),
		UProceduralModelingToolkitTwistModifier::StaticClass(),
		UProceduralModelingToolkitBendModifier::StaticClass(),
		UProceduralModelingToolkitInflateModifier::StaticClass()
	};

	for (UClass* ModifierClass : ModifierClasses)
	{
		const FString ModifierClassName = ModifierClass ? ModifierClass->GetName() : TEXT("None");

		UDynamicMesh* DynamicMesh = NewObject<UDynamicMesh>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
		DynamicMesh->ResetToCube();

		UProceduralModelingToolkitModifier* Modifier = NewObject<UProceduralModelingToolkitModifier>(GetTransientPackageAsObject(), ModifierClass, NAME_None, RF_Transient);
		TestNotNull(FString::Printf(TEXT("Modifier created: %s"), *ModifierClassName), Modifier);

		FProceduralModelingToolkitModifierExecutionContext Context;
		Context.SourceAssetPath = TEXT("/Temp/TestSource");
		Context.OutputAssetPath = TEXT("/Temp/TestOutput");

		const FProceduralModelingToolkitModifierResult Result = Modifier->Execute(DynamicMesh, Context);
		TestTrue(FString::Printf(TEXT("Modifier execution succeeded: %s"), *ModifierClassName), Result.bSuccess);
		TestFalse(FString::Printf(TEXT("Dynamic mesh is not empty after modifier: %s"), *ModifierClassName), DynamicMesh->IsEmpty());
		TestTrue(FString::Printf(TEXT("Triangle count remains valid after modifier: %s"), *ModifierClassName), DynamicMesh->GetTriangleCount() > 0);
	}

	return true;
}

#endif
