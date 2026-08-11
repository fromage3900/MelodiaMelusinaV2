#if WITH_DEV_AUTOMATION_TESTS

#include "ProceduralModelingToolkitModifier.h"
#include "ProceduralModelingToolkitSurfaceEffectModifiers.h"

#include "Misc/AutomationTest.h"
#include "UDynamicMesh.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FProceduralModelingToolkitSurfaceEffectsTest,
	"ProceduralModelingToolkit.SurfaceEffects.ExecuteIndependently",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FProceduralModelingToolkitSurfaceEffectsTest::RunTest(const FString& Parameters)
{
	const TArray<UClass*> ModifierClasses = {
		UProceduralModelingToolkitCracksModifier::StaticClass(),
		UProceduralModelingToolkitDamageModifier::StaticClass(),
		UProceduralModelingToolkitEdgeWearModifier::StaticClass(),
		UProceduralModelingToolkitDirtModifier::StaticClass(),
		UProceduralModelingToolkitMossModifier::StaticClass(),
		UProceduralModelingToolkitRustModifier::StaticClass(),
		UProceduralModelingToolkitSnowModifier::StaticClass(),
		UProceduralModelingToolkitVertexPaintModifier::StaticClass()
	};

	for (UClass* ModifierClass : ModifierClasses)
	{
		const FString ModifierClassName = ModifierClass ? ModifierClass->GetName() : TEXT("None");

		UDynamicMesh* DynamicMesh = NewObject<UDynamicMesh>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
		DynamicMesh->ResetToCube();

		UProceduralModelingToolkitModifier* Modifier = NewObject<UProceduralModelingToolkitModifier>(GetTransientPackageAsObject(), ModifierClass, NAME_None, RF_Transient);
		TestNotNull(FString::Printf(TEXT("Surface effect created: %s"), *ModifierClassName), Modifier);

		FProceduralModelingToolkitModifierExecutionContext Context;
		Context.SourceAssetPath = TEXT("/Temp/SurfaceEffectSource");
		Context.OutputAssetPath = TEXT("/Temp/SurfaceEffectOutput");

		const FProceduralModelingToolkitModifierResult Result = Modifier->Execute(DynamicMesh, Context);
		TestTrue(FString::Printf(TEXT("Surface effect execution succeeded: %s"), *ModifierClassName), Result.bSuccess);
		TestFalse(FString::Printf(TEXT("Surface effect output mesh is not empty: %s"), *ModifierClassName), DynamicMesh->IsEmpty());
	}

	return true;
}

#endif
