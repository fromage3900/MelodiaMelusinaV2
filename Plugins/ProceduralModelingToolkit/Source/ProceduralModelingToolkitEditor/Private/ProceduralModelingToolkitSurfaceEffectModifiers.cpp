#include "ProceduralModelingToolkitSurfaceEffectModifiers.h"

#include "GeometryScript/GeometryScriptSelectionTypes.h"
#include "GeometryScript/GeometryScriptTypes.h"
#include "GeometryScript/MeshDeformFunctions.h"
#include "GeometryScript/MeshVertexColorFunctions.h"
#include "UDynamicMesh.h"

namespace ProceduralModelingToolkit::SurfaceEffectParams
{
	static const FName Intensity(TEXT("Intensity"));
	static const FName Magnitude(TEXT("Magnitude"));
	static const FName Frequency(TEXT("Frequency"));
	static const FName Seed(TEXT("Seed"));
	static const FName Color(TEXT("Color"));
	static const FName Alpha(TEXT("Alpha"));
	static const FName BlurIterations(TEXT("BlurIterations"));
	static const FName ApplyDisplacement(TEXT("ApplyDisplacement"));

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

	static FLinearColor ReadColor(const FProceduralModelingToolkitModifierParameters& Parameters, const FLinearColor& DefaultColor)
	{
		const FVector ColorValue = Parameters.GetVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(DefaultColor.R, DefaultColor.G, DefaultColor.B));
		const float AlphaValue = static_cast<float>(Parameters.GetFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, DefaultColor.A));
		return FLinearColor(static_cast<float>(ColorValue.X), static_cast<float>(ColorValue.Y), static_cast<float>(ColorValue.Z), AlphaValue);
	}

	static void PaintVertexColor(UDynamicMesh* TargetMesh, const FLinearColor& PaintColor, int32 InBlurIterations)
	{
		FGeometryScriptColorFlags Flags;
		Flags.bRed = true;
		Flags.bGreen = true;
		Flags.bBlue = true;
		Flags.bAlpha = true;

		UGeometryScriptLibrary_MeshVertexColorFunctions::SetMeshConstantVertexColor(TargetMesh, PaintColor, Flags, /*bClearExisting=*/false);

		if (InBlurIterations > 0)
		{
			FGeometryScriptBlurMeshVertexColorsOptions BlurOptions;
			UGeometryScriptLibrary_MeshVertexColorFunctions::BlurMeshVertexColors(
				TargetMesh,
				FGeometryScriptMeshSelection(),
				InBlurIterations,
				0.5,
				EGeometryScriptBlurColorMode::Uniform,
				BlurOptions
			);
		}
	}

	static void ApplyNoiseDisplacement(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierParameters& Parameters, double DefaultMagnitude, double DefaultFrequency, int32 DefaultSeed)
	{
		FGeometryScriptPerlinNoiseOptions NoiseOptions;
		NoiseOptions.BaseLayer.Magnitude = static_cast<float>(Parameters.GetFloat(Magnitude, DefaultMagnitude));
		NoiseOptions.BaseLayer.Frequency = static_cast<float>(Parameters.GetFloat(Frequency, DefaultFrequency));
		NoiseOptions.BaseLayer.RandomSeed = Parameters.GetInt(Seed, DefaultSeed);
		NoiseOptions.bApplyAlongNormal = true;

		UGeometryScriptLibrary_MeshDeformFunctions::ApplyPerlinNoiseToMesh2(
			TargetMesh,
			FGeometryScriptMeshSelection(),
			NoiseOptions
		);
	}
}

UProceduralModelingToolkitCracksModifier::UProceduralModelingToolkitCracksModifier()
{
	ModifierId = TEXT("Cracks");
	DisplayName = FText::FromString(TEXT("Cracks"));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Intensity, 1.0);
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Magnitude, -2.0);
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Frequency, 0.12);
	Parameters.AddInt(ProceduralModelingToolkit::SurfaceEffectParams::Seed, 401);
	Parameters.AddVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(0.02, 0.02, 0.018));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, 1.0);
	Parameters.AddBool(ProceduralModelingToolkit::SurfaceEffectParams::ApplyDisplacement, true);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitCracksModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::SurfaceEffectParams::ValidateMesh(TargetMesh, TEXT("Cracks"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	if (Parameters.GetBool(ProceduralModelingToolkit::SurfaceEffectParams::ApplyDisplacement, true))
	{
		ProceduralModelingToolkit::SurfaceEffectParams::ApplyNoiseDisplacement(TargetMesh, Parameters, -2.0, 0.12, 401);
	}
	ProceduralModelingToolkit::SurfaceEffectParams::PaintVertexColor(TargetMesh, ProceduralModelingToolkit::SurfaceEffectParams::ReadColor(Parameters, FLinearColor(0.02f, 0.02f, 0.018f, 1.0f)), 0);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Cracks surface effect applied."));
}

UProceduralModelingToolkitDamageModifier::UProceduralModelingToolkitDamageModifier()
{
	ModifierId = TEXT("Damage");
	DisplayName = FText::FromString(TEXT("Damage"));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Magnitude, -4.0);
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Frequency, 0.06);
	Parameters.AddInt(ProceduralModelingToolkit::SurfaceEffectParams::Seed, 402);
	Parameters.AddVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(0.18, 0.14, 0.11));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, 1.0);
	Parameters.AddBool(ProceduralModelingToolkit::SurfaceEffectParams::ApplyDisplacement, true);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitDamageModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::SurfaceEffectParams::ValidateMesh(TargetMesh, TEXT("Damage"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	if (Parameters.GetBool(ProceduralModelingToolkit::SurfaceEffectParams::ApplyDisplacement, true))
	{
		ProceduralModelingToolkit::SurfaceEffectParams::ApplyNoiseDisplacement(TargetMesh, Parameters, -4.0, 0.06, 402);
	}
	ProceduralModelingToolkit::SurfaceEffectParams::PaintVertexColor(TargetMesh, ProceduralModelingToolkit::SurfaceEffectParams::ReadColor(Parameters, FLinearColor(0.18f, 0.14f, 0.11f, 1.0f)), 1);
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Damage surface effect applied."));
}

UProceduralModelingToolkitEdgeWearModifier::UProceduralModelingToolkitEdgeWearModifier()
{
	ModifierId = TEXT("EdgeWear");
	DisplayName = FText::FromString(TEXT("Edge Wear"));
	Parameters.AddVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(0.72, 0.68, 0.58));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, 1.0);
	Parameters.AddInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 1);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitEdgeWearModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::SurfaceEffectParams::ValidateMesh(TargetMesh, TEXT("Edge Wear"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	ProceduralModelingToolkit::SurfaceEffectParams::PaintVertexColor(TargetMesh, ProceduralModelingToolkit::SurfaceEffectParams::ReadColor(Parameters, FLinearColor(0.72f, 0.68f, 0.58f, 1.0f)), Parameters.GetInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 1));
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Edge Wear surface effect applied."));
}

UProceduralModelingToolkitDirtModifier::UProceduralModelingToolkitDirtModifier()
{
	ModifierId = TEXT("Dirt");
	DisplayName = FText::FromString(TEXT("Dirt"));
	Parameters.AddVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(0.12, 0.09, 0.06));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, 1.0);
	Parameters.AddInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 2);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitDirtModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::SurfaceEffectParams::ValidateMesh(TargetMesh, TEXT("Dirt"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	ProceduralModelingToolkit::SurfaceEffectParams::PaintVertexColor(TargetMesh, ProceduralModelingToolkit::SurfaceEffectParams::ReadColor(Parameters, FLinearColor(0.12f, 0.09f, 0.06f, 1.0f)), Parameters.GetInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 2));
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Dirt surface effect applied."));
}

UProceduralModelingToolkitMossModifier::UProceduralModelingToolkitMossModifier()
{
	ModifierId = TEXT("Moss");
	DisplayName = FText::FromString(TEXT("Moss"));
	Parameters.AddVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(0.08, 0.24, 0.07));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, 1.0);
	Parameters.AddInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 2);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitMossModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::SurfaceEffectParams::ValidateMesh(TargetMesh, TEXT("Moss"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	ProceduralModelingToolkit::SurfaceEffectParams::PaintVertexColor(TargetMesh, ProceduralModelingToolkit::SurfaceEffectParams::ReadColor(Parameters, FLinearColor(0.08f, 0.24f, 0.07f, 1.0f)), Parameters.GetInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 2));
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Moss surface effect applied."));
}

UProceduralModelingToolkitRustModifier::UProceduralModelingToolkitRustModifier()
{
	ModifierId = TEXT("Rust");
	DisplayName = FText::FromString(TEXT("Rust"));
	Parameters.AddVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(0.58, 0.18, 0.05));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, 1.0);
	Parameters.AddInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 1);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitRustModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::SurfaceEffectParams::ValidateMesh(TargetMesh, TEXT("Rust"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	ProceduralModelingToolkit::SurfaceEffectParams::PaintVertexColor(TargetMesh, ProceduralModelingToolkit::SurfaceEffectParams::ReadColor(Parameters, FLinearColor(0.58f, 0.18f, 0.05f, 1.0f)), Parameters.GetInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 1));
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Rust surface effect applied."));
}

UProceduralModelingToolkitSnowModifier::UProceduralModelingToolkitSnowModifier()
{
	ModifierId = TEXT("Snow");
	DisplayName = FText::FromString(TEXT("Snow"));
	Parameters.AddVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(0.9, 0.94, 1.0));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, 1.0);
	Parameters.AddInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 2);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitSnowModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::SurfaceEffectParams::ValidateMesh(TargetMesh, TEXT("Snow"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	ProceduralModelingToolkit::SurfaceEffectParams::PaintVertexColor(TargetMesh, ProceduralModelingToolkit::SurfaceEffectParams::ReadColor(Parameters, FLinearColor(0.9f, 0.94f, 1.0f, 1.0f)), Parameters.GetInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 2));
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Snow surface effect applied."));
}

UProceduralModelingToolkitVertexPaintModifier::UProceduralModelingToolkitVertexPaintModifier()
{
	ModifierId = TEXT("VertexPaint");
	DisplayName = FText::FromString(TEXT("Vertex Paint"));
	Parameters.AddVector(ProceduralModelingToolkit::SurfaceEffectParams::Color, FVector(1.0, 1.0, 1.0));
	Parameters.AddFloat(ProceduralModelingToolkit::SurfaceEffectParams::Alpha, 1.0);
	Parameters.AddInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 0);
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitVertexPaintModifier::Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context)
{
	const FProceduralModelingToolkitModifierResult Validation = ProceduralModelingToolkit::SurfaceEffectParams::ValidateMesh(TargetMesh, TEXT("Vertex Paint"));
	if (!Validation.bSuccess)
	{
		return Validation;
	}

	ProceduralModelingToolkit::SurfaceEffectParams::PaintVertexColor(TargetMesh, ProceduralModelingToolkit::SurfaceEffectParams::ReadColor(Parameters, FLinearColor::White), Parameters.GetInt(ProceduralModelingToolkit::SurfaceEffectParams::BlurIterations, 0));
	return FProceduralModelingToolkitModifierResult::Success(TEXT("Vertex Paint surface effect applied."));
}
