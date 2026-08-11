#include "ProceduralModelingToolkitBasicModifiers.h"

#include "GeometryScript/GeometryScriptSelectionTypes.h"
#include "GeometryScript/GeometryScriptTypes.h"
#include "GeometryScript/MeshBooleanFunctions.h"
#include "GeometryScript/MeshDeformFunctions.h"
#include "GeometryScript/MeshNormalsFunctions.h"
#include "GeometryScript/MeshTransformFunctions.h"
#include "UDynamicMesh.h"

namespace ProceduralModelingToolkit::ModifierParams
{
	static const FName Translation(TEXT("Translation"));
	static const FName Rotation(TEXT("Rotation"));
	static const FName Origin(TEXT("Origin"));
	static const FName Scale(TEXT("Scale"));
	static const FName PlaneOrigin(TEXT("PlaneOrigin"));
	static const FName PlaneRotation(TEXT("PlaneRotation"));
	static const FName ApplyPlaneCut(TEXT("ApplyPlaneCut"));
	static const FName FlipCutSide(TEXT("FlipCutSide"));
	static const FName WeldAlongPlane(TEXT("WeldAlongPlane"));
	static const FName Magnitude(TEXT("Magnitude"));
	static const FName Frequency(TEXT("Frequency"));
	static const FName FrequencyShift(TEXT("FrequencyShift"));
	static const FName Seed(TEXT("Seed"));
	static const FName ApplyAlongNormal(TEXT("ApplyAlongNormal"));
	static const FName Iterations(TEXT("Iterations"));
	static const FName Alpha(TEXT("Alpha"));
	static const FName AngleWeighted(TEXT("AngleWeighted"));
	static const FName AreaWeighted(TEXT("AreaWeighted"));

	static FProceduralModelingToolkitModifierResult ValidateMesh(UDynamicMesh* TargetMesh, const TCHAR* ModifierName)
	{
		if (!TargetMesh)
		{
			return FProceduralModelingToolkitModifierResult::Failure(FString::Printf(TEXT("%s failed: target Dynamic Mesh is null."), ModifierName));
		}

		if (TargetMesh->IsEmpty())
		{
			return FProceduralModelingToolkitModifierResult::Failure(FString::Printf(TEXT("%s failed: target Dynamic Mesh is empty."), ModifierName));
		}

		return FProceduralModelingToolkitModifierResult::Success();
	}
}

UProceduralModelingToolkitTranslateModifier::UProceduralModelingToolkitTranslateModifier()
{
	ModifierId = TEXT("Translate");
	DisplayName = FText::FromString(TEXT("Translate"));
	Parameters.AddVector(ProceduralModelingToolkit::ModifierParams::Translation, FVector(10.0, 0.0, 0.0));
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitTranslateModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::ModifierParams::ValidateMesh(TargetMesh, TEXT("Translate"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	UGeometryScriptLibrary_MeshTransformFunctions::TranslateMesh(
		TargetMesh,
		Parameters.GetVector(ProceduralModelingToolkit::ModifierParams::Translation, FVector::ZeroVector)
	);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Translate modifier applied."));
}

UProceduralModelingToolkitRotateModifier::UProceduralModelingToolkitRotateModifier()
{
	ModifierId = TEXT("Rotate");
	DisplayName = FText::FromString(TEXT("Rotate"));
	Parameters.AddRotator(ProceduralModelingToolkit::ModifierParams::Rotation, FRotator(0.0, 45.0, 0.0));
	Parameters.AddVector(ProceduralModelingToolkit::ModifierParams::Origin, FVector::ZeroVector);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitRotateModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::ModifierParams::ValidateMesh(TargetMesh, TEXT("Rotate"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	UGeometryScriptLibrary_MeshTransformFunctions::RotateMesh(
		TargetMesh,
		Parameters.GetRotator(ProceduralModelingToolkit::ModifierParams::Rotation, FRotator::ZeroRotator),
		Parameters.GetVector(ProceduralModelingToolkit::ModifierParams::Origin, FVector::ZeroVector)
	);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Rotate modifier applied."));
}

UProceduralModelingToolkitScaleModifier::UProceduralModelingToolkitScaleModifier()
{
	ModifierId = TEXT("Scale");
	DisplayName = FText::FromString(TEXT("Scale"));
	Parameters.AddVector(ProceduralModelingToolkit::ModifierParams::Scale, FVector(1.25, 1.25, 1.25));
	Parameters.AddVector(ProceduralModelingToolkit::ModifierParams::Origin, FVector::ZeroVector);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitScaleModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::ModifierParams::ValidateMesh(TargetMesh, TEXT("Scale"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	UGeometryScriptLibrary_MeshTransformFunctions::ScaleMesh(
		TargetMesh,
		Parameters.GetVector(ProceduralModelingToolkit::ModifierParams::Scale, FVector::OneVector),
		Parameters.GetVector(ProceduralModelingToolkit::ModifierParams::Origin, FVector::ZeroVector),
		/*bFixOrientationForNegativeScale=*/true
	);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Scale modifier applied."));
}

UProceduralModelingToolkitMirrorModifier::UProceduralModelingToolkitMirrorModifier()
{
	ModifierId = TEXT("Mirror");
	DisplayName = FText::FromString(TEXT("Mirror"));
	Parameters.AddVector(ProceduralModelingToolkit::ModifierParams::PlaneOrigin, FVector::ZeroVector);
	Parameters.AddRotator(ProceduralModelingToolkit::ModifierParams::PlaneRotation, FRotator::ZeroRotator);
	Parameters.AddBool(ProceduralModelingToolkit::ModifierParams::ApplyPlaneCut, true);
	Parameters.AddBool(ProceduralModelingToolkit::ModifierParams::FlipCutSide, false);
	Parameters.AddBool(ProceduralModelingToolkit::ModifierParams::WeldAlongPlane, true);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitMirrorModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::ModifierParams::ValidateMesh(TargetMesh, TEXT("Mirror"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptMeshMirrorOptions Options;
	Options.bApplyPlaneCut = Parameters.GetBool(ProceduralModelingToolkit::ModifierParams::ApplyPlaneCut, true);
	Options.bFlipCutSide = Parameters.GetBool(ProceduralModelingToolkit::ModifierParams::FlipCutSide, false);
	Options.bWeldAlongPlane = Parameters.GetBool(ProceduralModelingToolkit::ModifierParams::WeldAlongPlane, true);

	const FTransform MirrorFrame(
		Parameters.GetRotator(ProceduralModelingToolkit::ModifierParams::PlaneRotation, FRotator::ZeroRotator),
		Parameters.GetVector(ProceduralModelingToolkit::ModifierParams::PlaneOrigin, FVector::ZeroVector)
	);

	UGeometryScriptLibrary_MeshBooleanFunctions::ApplyMeshMirror(TargetMesh, MirrorFrame, Options);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Mirror modifier applied."));
}

UProceduralModelingToolkitNoiseModifier::UProceduralModelingToolkitNoiseModifier()
{
	ModifierId = TEXT("Noise");
	DisplayName = FText::FromString(TEXT("Noise"));
	Parameters.AddFloat(ProceduralModelingToolkit::ModifierParams::Magnitude, 5.0);
	Parameters.AddFloat(ProceduralModelingToolkit::ModifierParams::Frequency, 0.05);
	Parameters.AddVector(ProceduralModelingToolkit::ModifierParams::FrequencyShift, FVector::ZeroVector);
	Parameters.AddInt(ProceduralModelingToolkit::ModifierParams::Seed, 1337);
	Parameters.AddBool(ProceduralModelingToolkit::ModifierParams::ApplyAlongNormal, true);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitNoiseModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::ModifierParams::ValidateMesh(TargetMesh, TEXT("Noise"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptPerlinNoiseOptions Options;
	Options.BaseLayer.Magnitude = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::ModifierParams::Magnitude, 5.0));
	Options.BaseLayer.Frequency = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::ModifierParams::Frequency, 0.05));
	Options.BaseLayer.FrequencyShift = Parameters.GetVector(ProceduralModelingToolkit::ModifierParams::FrequencyShift, FVector::ZeroVector);
	Options.BaseLayer.RandomSeed = Parameters.GetInt(ProceduralModelingToolkit::ModifierParams::Seed, 1337);
	Options.bApplyAlongNormal = Parameters.GetBool(ProceduralModelingToolkit::ModifierParams::ApplyAlongNormal, true);

	UGeometryScriptLibrary_MeshDeformFunctions::ApplyPerlinNoiseToMesh2(
		TargetMesh,
		FGeometryScriptMeshSelection(),
		Options
	);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Noise modifier applied."));
}

UProceduralModelingToolkitSmoothModifier::UProceduralModelingToolkitSmoothModifier()
{
	ModifierId = TEXT("Smooth");
	DisplayName = FText::FromString(TEXT("Smooth"));
	Parameters.AddInt(ProceduralModelingToolkit::ModifierParams::Iterations, 2);
	Parameters.AddFloat(ProceduralModelingToolkit::ModifierParams::Alpha, 0.2);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitSmoothModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::ModifierParams::ValidateMesh(TargetMesh, TEXT("Smooth"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptIterativeMeshSmoothingOptions Options;
	Options.NumIterations = FMath::Max(0, Parameters.GetInt(ProceduralModelingToolkit::ModifierParams::Iterations, 2));
	Options.Alpha = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::ModifierParams::Alpha, 0.2));

	UGeometryScriptLibrary_MeshDeformFunctions::ApplyIterativeSmoothingToMesh(
		TargetMesh,
		FGeometryScriptMeshSelection(),
		Options
	);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Smooth modifier applied."));
}

UProceduralModelingToolkitRecomputeNormalsModifier::UProceduralModelingToolkitRecomputeNormalsModifier()
{
	ModifierId = TEXT("RecomputeNormals");
	DisplayName = FText::FromString(TEXT("Recompute Normals"));
	Parameters.AddBool(ProceduralModelingToolkit::ModifierParams::AngleWeighted, true);
	Parameters.AddBool(ProceduralModelingToolkit::ModifierParams::AreaWeighted, true);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitRecomputeNormalsModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::ModifierParams::ValidateMesh(TargetMesh, TEXT("Recompute Normals"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptCalculateNormalsOptions Options;
	Options.bAngleWeighted = Parameters.GetBool(ProceduralModelingToolkit::ModifierParams::AngleWeighted, true);
	Options.bAreaWeighted = Parameters.GetBool(ProceduralModelingToolkit::ModifierParams::AreaWeighted, true);

	UGeometryScriptLibrary_MeshNormalsFunctions::RecomputeNormals(TargetMesh, Options);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Recompute Normals modifier applied."));
}
