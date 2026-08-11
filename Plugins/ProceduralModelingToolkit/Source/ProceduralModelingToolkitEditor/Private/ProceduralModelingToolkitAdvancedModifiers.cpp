#include "ProceduralModelingToolkitAdvancedModifiers.h"

#include "GeometryScript/GeometryScriptSelectionTypes.h"
#include "GeometryScript/MeshDeformFunctions.h"
#include "GeometryScript/MeshModelingFunctions.h"
#include "GeometryScript/MeshRemeshFunctions.h"
#include "GeometryScript/MeshSimplifyFunctions.h"
#include "UDynamicMesh.h"

namespace ProceduralModelingToolkit::AdvancedModifierParams
{
	static const FName Distance(TEXT("Distance"));
	static const FName Direction(TEXT("Direction"));
	static const FName UseAverageNormal(TEXT("UseAverageNormal"));
	static const FName UVScale(TEXT("UVScale"));
	static const FName SolidsToShells(TEXT("SolidsToShells"));
	static const FName Reproject(TEXT("Reproject"));
	static const FName BoundaryOnly(TEXT("BoundaryOnly"));
	static const FName Softness(TEXT("Softness"));
	static const FName AreaScale(TEXT("AreaScale"));
	static const FName TargetTriangleCount(TEXT("TargetTriangleCount"));
	static const FName TargetEdgeLength(TEXT("TargetEdgeLength"));
	static const FName UseTargetEdgeLength(TEXT("UseTargetEdgeLength"));
	static const FName RemeshIterations(TEXT("RemeshIterations"));
	static const FName SmoothingRate(TEXT("SmoothingRate"));
	static const FName ReprojectToInputMesh(TEXT("ReprojectToInputMesh"));
	static const FName DiscardAttributes(TEXT("DiscardAttributes"));
	static const FName Angle(TEXT("Angle"));
	static const FName Extent(TEXT("Extent"));
	static const FName Origin(TEXT("Origin"));
	static const FName Orientation(TEXT("Orientation"));
	static const FName SymmetricExtents(TEXT("SymmetricExtents"));
	static const FName LowerExtent(TEXT("LowerExtent"));
	static const FName Bidirectional(TEXT("Bidirectional"));
	static const FName SolveSteps(TEXT("SolveSteps"));
	static const FName SmoothAlpha(TEXT("SmoothAlpha"));
	static const FName FixedBoundary(TEXT("FixedBoundary"));

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

	static FTransform GetOrientationTransform(const FProceduralModelingToolkitModifierParameters& Parameters)
	{
		return FTransform(
			Parameters.GetRotator(Orientation, FRotator::ZeroRotator),
			Parameters.GetVector(Origin, FVector::ZeroVector)
		);
	}
}

UProceduralModelingToolkitExtrudeModifier::UProceduralModelingToolkitExtrudeModifier()
{
	ModifierId = TEXT("Extrude");
	DisplayName = FText::FromString(TEXT("Extrude"));
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::Distance, 10.0);
	Parameters.AddVector(ProceduralModelingToolkit::AdvancedModifierParams::Direction, FVector(0.0, 0.0, 1.0));
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::UseAverageNormal, false);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::UVScale, 1.0);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::SolidsToShells, true);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitExtrudeModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::AdvancedModifierParams::ValidateMesh(TargetMesh, TEXT("Extrude"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptMeshLinearExtrudeOptions Options;
	Options.Distance = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::Distance, 10.0));
	Options.Direction = Parameters.GetVector(ProceduralModelingToolkit::AdvancedModifierParams::Direction, FVector::UpVector);
	Options.DirectionMode = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::UseAverageNormal, false)
		? EGeometryScriptLinearExtrudeDirection::AverageFaceNormal
		: EGeometryScriptLinearExtrudeDirection::FixedDirection;
	Options.AreaMode = EGeometryScriptPolyOperationArea::EntireSelection;
	Options.UVScale = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::UVScale, 1.0));
	Options.bSolidsToShells = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::SolidsToShells, true);

	UGeometryScriptLibrary_MeshModelingFunctions::ApplyMeshLinearExtrudeFaces(TargetMesh, Options, FGeometryScriptMeshSelection());
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Extrude modifier applied."));
}

UProceduralModelingToolkitInsetModifier::UProceduralModelingToolkitInsetModifier()
{
	ModifierId = TEXT("Inset");
	DisplayName = FText::FromString(TEXT("Inset"));
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::Distance, 2.0);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::Reproject, true);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::BoundaryOnly, false);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::Softness, 0.0);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::AreaScale, 1.0);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::UVScale, 1.0);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitInsetModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::AdvancedModifierParams::ValidateMesh(TargetMesh, TEXT("Inset"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptMeshInsetOutsetFacesOptions Options;
	Options.Distance = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::Distance, 2.0));
	Options.bReproject = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::Reproject, true);
	Options.bBoundaryOnly = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::BoundaryOnly, false);
	Options.Softness = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::Softness, 0.0));
	Options.AreaScale = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::AreaScale, 1.0));
	Options.AreaMode = EGeometryScriptPolyOperationArea::EntireSelection;
	Options.UVScale = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::UVScale, 1.0));

	UGeometryScriptLibrary_MeshModelingFunctions::ApplyMeshInsetOutsetFaces(TargetMesh, Options, FGeometryScriptMeshSelection());
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Inset modifier applied."));
}

UProceduralModelingToolkitRemeshModifier::UProceduralModelingToolkitRemeshModifier()
{
	ModifierId = TEXT("Remesh");
	DisplayName = FText::FromString(TEXT("Remesh"));
	Parameters.AddInt(ProceduralModelingToolkit::AdvancedModifierParams::TargetTriangleCount, 5000);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::TargetEdgeLength, 10.0);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::UseTargetEdgeLength, false);
	Parameters.AddInt(ProceduralModelingToolkit::AdvancedModifierParams::RemeshIterations, 20);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::SmoothingRate, 0.25);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::ReprojectToInputMesh, true);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::DiscardAttributes, false);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitRemeshModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::AdvancedModifierParams::ValidateMesh(TargetMesh, TEXT("Remesh"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptRemeshOptions RemeshOptions;
	RemeshOptions.RemeshIterations = FMath::Max(0, Parameters.GetInt(ProceduralModelingToolkit::AdvancedModifierParams::RemeshIterations, 20));
	RemeshOptions.SmoothingRate = FMath::Clamp(static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::SmoothingRate, 0.25)), 0.0f, 1.0f);
	RemeshOptions.bReprojectToInputMesh = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::ReprojectToInputMesh, true);
	RemeshOptions.bDiscardAttributes = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::DiscardAttributes, false);

	FGeometryScriptUniformRemeshOptions UniformOptions;
	UniformOptions.TargetType = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::UseTargetEdgeLength, false)
		? EGeometryScriptUniformRemeshTargetType::TargetEdgeLength
		: EGeometryScriptUniformRemeshTargetType::TriangleCount;
	UniformOptions.TargetTriangleCount = FMath::Max(1, Parameters.GetInt(ProceduralModelingToolkit::AdvancedModifierParams::TargetTriangleCount, 5000));
	UniformOptions.TargetEdgeLength = FMath::Max(0.001f, static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::TargetEdgeLength, 10.0)));

	UGeometryScriptLibrary_RemeshingFunctions::ApplyUniformRemesh(TargetMesh, RemeshOptions, UniformOptions);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Remesh modifier applied."));
}

UProceduralModelingToolkitSimplifyModifier::UProceduralModelingToolkitSimplifyModifier()
{
	ModifierId = TEXT("Simplify");
	DisplayName = FText::FromString(TEXT("Simplify"));
	Parameters.AddInt(ProceduralModelingToolkit::AdvancedModifierParams::TargetTriangleCount, 500);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitSimplifyModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::AdvancedModifierParams::ValidateMesh(TargetMesh, TEXT("Simplify"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptSimplifyMeshOptions Options;
	Options.bAutoCompact = true;

	const int32 TriangleCount = FMath::Max(1, Parameters.GetInt(ProceduralModelingToolkit::AdvancedModifierParams::TargetTriangleCount, 500));
	UGeometryScriptLibrary_MeshSimplifyFunctions::ApplySimplifyToTriangleCount(TargetMesh, TriangleCount, Options);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Simplify modifier applied."));
}

UProceduralModelingToolkitTwistModifier::UProceduralModelingToolkitTwistModifier()
{
	ModifierId = TEXT("Twist");
	DisplayName = FText::FromString(TEXT("Twist"));
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::Angle, 45.0);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::Extent, 50.0);
	Parameters.AddVector(ProceduralModelingToolkit::AdvancedModifierParams::Origin, FVector::ZeroVector);
	Parameters.AddRotator(ProceduralModelingToolkit::AdvancedModifierParams::Orientation, FRotator::ZeroRotator);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::SymmetricExtents, true);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::LowerExtent, 10.0);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::Bidirectional, true);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitTwistModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::AdvancedModifierParams::ValidateMesh(TargetMesh, TEXT("Twist"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptTwistWarpOptions Options;
	Options.bSymmetricExtents = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::SymmetricExtents, true);
	Options.LowerExtent = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::LowerExtent, 10.0));
	Options.bBidirectional = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::Bidirectional, true);

	UGeometryScriptLibrary_MeshDeformFunctions::ApplyTwistWarpToMesh(
		TargetMesh,
		Options,
		ProceduralModelingToolkit::AdvancedModifierParams::GetOrientationTransform(Parameters),
		static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::Angle, 45.0)),
		static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::Extent, 50.0))
	);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Twist modifier applied."));
}

UProceduralModelingToolkitBendModifier::UProceduralModelingToolkitBendModifier()
{
	ModifierId = TEXT("Bend");
	DisplayName = FText::FromString(TEXT("Bend"));
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::Angle, 45.0);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::Extent, 50.0);
	Parameters.AddVector(ProceduralModelingToolkit::AdvancedModifierParams::Origin, FVector::ZeroVector);
	Parameters.AddRotator(ProceduralModelingToolkit::AdvancedModifierParams::Orientation, FRotator::ZeroRotator);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::SymmetricExtents, true);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::LowerExtent, 10.0);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::Bidirectional, true);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitBendModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::AdvancedModifierParams::ValidateMesh(TargetMesh, TEXT("Bend"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptBendWarpOptions Options;
	Options.bSymmetricExtents = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::SymmetricExtents, true);
	Options.LowerExtent = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::LowerExtent, 10.0));
	Options.bBidirectional = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::Bidirectional, true);

	UGeometryScriptLibrary_MeshDeformFunctions::ApplyBendWarpToMesh(
		TargetMesh,
		Options,
		ProceduralModelingToolkit::AdvancedModifierParams::GetOrientationTransform(Parameters),
		static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::Angle, 45.0)),
		static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::Extent, 50.0))
	);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Bend modifier applied."));
}

UProceduralModelingToolkitInflateModifier::UProceduralModelingToolkitInflateModifier()
{
	ModifierId = TEXT("Inflate");
	DisplayName = FText::FromString(TEXT("Inflate"));
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::Distance, 2.0);
	Parameters.AddBool(ProceduralModelingToolkit::AdvancedModifierParams::FixedBoundary, false);
	Parameters.AddInt(ProceduralModelingToolkit::AdvancedModifierParams::SolveSteps, 5);
	Parameters.AddFloat(ProceduralModelingToolkit::AdvancedModifierParams::SmoothAlpha, 0.1);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitInflateModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::AdvancedModifierParams::ValidateMesh(TargetMesh, TEXT("Inflate"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	FGeometryScriptMeshOffsetOptions Options;
	Options.OffsetDistance = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::Distance, 2.0));
	Options.bFixedBoundary = Parameters.GetBool(ProceduralModelingToolkit::AdvancedModifierParams::FixedBoundary, false);
	Options.SolveSteps = FMath::Max(0, Parameters.GetInt(ProceduralModelingToolkit::AdvancedModifierParams::SolveSteps, 5));
	Options.SmoothAlpha = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::AdvancedModifierParams::SmoothAlpha, 0.1));

	UGeometryScriptLibrary_MeshModelingFunctions::ApplyMeshOffset(TargetMesh, Options);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Inflate modifier applied."));
}
