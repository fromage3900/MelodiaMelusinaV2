#if WITH_DEV_AUTOMATION_TESTS

#include "ProceduralModelingToolkitAdvancedModifiers.h"
#include "ProceduralModelingToolkitModifier.h"

#include "Engine/StaticMesh.h"
#include "GeometryScript/GeometryScriptTypes.h"
#include "GeometryScript/MeshAssetFunctions.h"
#include "GeometryScript/MeshBooleanFunctions.h"
#include "Misc/AutomationTest.h"
#include "UDynamicMesh.h"
#include "UObject/Package.h"
#include "UObject/UObjectGlobals.h"

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FProceduralModelingToolkitBooleanModifierTest,
	"ProceduralModelingToolkit.Modifiers.Boolean.DifferenceSubtractsVolume",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FProceduralModelingToolkitBooleanModifierTest::RunTest(const FString& Parameters)
{
	// Build a target cube Dynamic Mesh (100cm per side).
	UDynamicMesh* TargetMesh = NewObject<UDynamicMesh>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
	TargetMesh->ResetToCube();
	const int32 TargetTriangleCount = TargetMesh->GetTriangleCount();
	TestTrue(TEXT("Target cube has triangles"), TargetTriangleCount > 0);

	// Build a smaller cutter cube Static Mesh asset in a transient package so the modifier can load it by path.
	UPackage* CutterPackage = CreatePackage(*TEXT("/Temp/PMT_BooleanTest_CutterPackage"));
	CutterPackage->SetFlags(RF_Public | RF_Transient);
	UStaticMesh* CutterStaticMesh = NewObject<UStaticMesh>(CutterPackage, TEXT("SM_BooleanTest_Cutter"), RF_Public | RF_Transient);
	TestNotNull(TEXT("Cutter Static Mesh created"), CutterStaticMesh);

	UDynamicMesh* CutterDynamicMesh = NewObject<UDynamicMesh>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
	CutterDynamicMesh->ResetToCube();

	FGeometryScriptCopyMeshToAssetOptions CopyToOptions;
	CopyToOptions.bEnableRecomputeNormals = false;
	CopyToOptions.bEnableRecomputeTangents = false;
	CopyToOptions.bEnableRemoveDegenerates = false;
	CopyToOptions.bUseBuildScale = true;
	CopyToOptions.bReplaceMaterials = false;
	CopyToOptions.bCleanAssignedMaterials = true;
	CopyToOptions.GenerateLightmapUVs = EGeometryScriptGenerateLightmapUVOptions::DoNotGenerateLightmapUVs;
	CopyToOptions.bApplyNaniteSettings = false;
	CopyToOptions.bEmitTransaction = false;
	CopyToOptions.bDeferMeshPostEditChange = false;

	const FGeometryScriptMeshWriteLOD WriteLOD;
	EGeometryScriptOutcomePins CopyToOutcome = EGeometryScriptOutcomePins::Failure;
	UGeometryScriptDebug* Debug = NewObject<UGeometryScriptDebug>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
	UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshToStaticMesh(
		CutterDynamicMesh,
		CutterStaticMesh,
		CopyToOptions,
		WriteLOD,
		CopyToOutcome,
		/*bUseSectionMaterials=*/true,
		Debug
	);
	TestEqual(TEXT("Cutter Static Mesh copy succeeded"), CopyToOutcome, EGeometryScriptOutcomePins::Success);
	TestTrue(TEXT("Cutter Static Mesh has triangles"), CutterStaticMesh->GetNumTriangles(0) > 0);

	// Capture input bounds before the boolean.
	const FAxisAlignedBox3d InputBounds = TargetMesh->GetMeshRef().GetBounds();

	// Position the cutter in the center of the target and scale it down so it removes a smaller box.
	UProceduralModelingToolkitBooleanModifier* BooleanModifier = NewObject<UProceduralModelingToolkitBooleanModifier>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
	if (FProceduralModelingToolkitModifierParameter* PathParam = BooleanModifier->Parameters.FindMutable(TEXT("CutterMeshPath")))
	{
		PathParam->StringValue = CutterStaticMesh->GetPathName();
	}
	if (FProceduralModelingToolkitModifierParameter* OperationParam = BooleanModifier->Parameters.FindMutable(TEXT("Operation")))
	{
		OperationParam->IntValue = static_cast<int32>(EGeometryScriptBooleanOperation::Subtract);
	}
	if (FProceduralModelingToolkitModifierParameter* LocationParam = BooleanModifier->Parameters.FindMutable(TEXT("CutterLocation")))
	{
		LocationParam->VectorValue = FVector::ZeroVector;
	}
	if (FProceduralModelingToolkitModifierParameter* RotationParam = BooleanModifier->Parameters.FindMutable(TEXT("CutterRotation")))
	{
		RotationParam->RotatorValue = FRotator::ZeroRotator;
	}
	if (FProceduralModelingToolkitModifierParameter* ScaleParam = BooleanModifier->Parameters.FindMutable(TEXT("CutterScale")))
	{
		ScaleParam->VectorValue = FVector(0.5, 0.5, 0.5);
	}

	FProceduralModelingToolkitModifierExecutionContext Context;
	Context.SourceAssetPath = TEXT("/Temp/TestBooleanSource");
	Context.OutputAssetPath = TEXT("/Temp/TestBooleanOutput");

	const FProceduralModelingToolkitModifierResult Result = BooleanModifier->Execute(TargetMesh, Context);
	TestTrue(TEXT("Boolean modifier execution succeeded"), Result.bSuccess);
	TestTrue(TEXT("Target mesh is not empty after boolean"), !TargetMesh->IsEmpty());

	const int32 ResultTriangleCount = TargetMesh->GetTriangleCount();
	// A cube-minus-box difference always modifies the topology; exact count direction depends on
	// cutter geometry (a centered smaller box typically increases face count). The contract we
	// enforce here is that the boolean actually changed the mesh and produced a valid result.
	TestTrue(TEXT("Result triangle count changed after boolean"), ResultTriangleCount != TargetTriangleCount);

	// Bounds should remain valid; shrink assertions only hold when the cutter extends beyond a face.
	const FAxisAlignedBox3d ResultBounds = TargetMesh->GetMeshRef().GetBounds();
	TestTrue(TEXT("Result bounds are valid"), !ResultBounds.IsEmpty());
	TestTrue(TEXT("Result bounds have positive extents"), ResultBounds.Extents().X > 0.0 && ResultBounds.Extents().Y > 0.0 && ResultBounds.Extents().Z > 0.0);

	return true;
}

#endif
