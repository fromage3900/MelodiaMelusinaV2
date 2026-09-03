#include "ProceduralModelingToolkitOrnamentGenerator.h"

#include "Math/RandomStream.h"

namespace ProceduralModelingToolkit::Ornaments
{
	static constexpr float TwoPi = UE_TWO_PI;

	static int32 SafePointCount(int32 PointCount)
	{
		return FMath::Max(4, PointCount);
	}

	static FVector Rotate2D(const FVector& Point, float AngleRadians)
	{
		const float CosAngle = FMath::Cos(AngleRadians);
		const float SinAngle = FMath::Sin(AngleRadians);
		return FVector(
			Point.X * CosAngle - Point.Y * SinAngle,
			Point.X * SinAngle + Point.Y * CosAngle,
			Point.Z
		);
	}
}

TArray<FProceduralModelingToolkitSplinePath> UProceduralModelingToolkitOrnamentGenerator::GenerateOrnament(const FProceduralModelingToolkitOrnamentSettings& Settings)
{
	FRandomStream RandomStream(Settings.Seed);
	TArray<FProceduralModelingToolkitSplinePath> Paths;

	switch (Settings.Kind)
	{
	case EProceduralModelingToolkitOrnamentKind::Spiral:
		Paths.Add(MakeSpiral(Settings, TEXT("Spiral"), 0.0f));
		break;
	case EProceduralModelingToolkitOrnamentKind::Curve:
		Paths.Add(MakeCurve(Settings, TEXT("Curve"), 0.0f));
		break;
	case EProceduralModelingToolkitOrnamentKind::SymmetricalCurls:
		Paths.Add(MakeSpiral(Settings, TEXT("Curl_A"), 0.0f));
		Paths.Add(TransformPath(Paths[0], FTransform(FQuat::Identity, FVector::ZeroVector, FVector(-1.0, 1.0, 1.0)), TEXT("Curl_B")));
		break;
	case EProceduralModelingToolkitOrnamentKind::Vine:
		Paths.Append(MakeVine(Settings, RandomStream, TEXT("Vine")));
		break;
	default:
		Paths.Add(MakeSpiral(Settings, TEXT("Spiral"), 0.0f));
		break;
	}

	ApplySymmetry(Settings, Paths);
	return Paths;
}

TArray<FProceduralModelingToolkitSplinePath> UProceduralModelingToolkitOrnamentGenerator::GenerateFiligree(const FProceduralModelingToolkitFiligreeSettings& Settings)
{
	FRandomStream RandomStream(Settings.Seed);
	TArray<FProceduralModelingToolkitSplinePath> Paths;

	for (int32 VineIndex = 0; VineIndex < FMath::Max(1, Settings.VineCount); ++VineIndex)
	{
		FProceduralModelingToolkitOrnamentSettings VineSettings;
		VineSettings.Kind = EProceduralModelingToolkitOrnamentKind::Vine;
		VineSettings.Seed = Settings.Seed + VineIndex;
		VineSettings.PointCount = 72;
		VineSettings.Radius = Settings.Radius;
		VineSettings.Length = Settings.Length;
		VineSettings.Turns = 1.0f + 0.35f * VineIndex;
		VineSettings.Amplitude = Settings.Radius * 0.35f;
		VineSettings.BranchCount = Settings.BranchCount;
		VineSettings.BranchLength = Settings.BranchLength;
		VineSettings.Thickness = Settings.Thickness;
		VineSettings.Bevel = Settings.Bevel;

		TArray<FProceduralModelingToolkitSplinePath> VinePaths = MakeVine(VineSettings, RandomStream, FName(*FString::Printf(TEXT("FiligreeVine_%d"), VineIndex)));
		Paths.Append(VinePaths);
	}

	for (int32 LeafIndex = 0; LeafIndex < FMath::Max(0, Settings.LeafCount); ++LeafIndex)
	{
		const float T = (LeafIndex + 0.5f) / FMath::Max(1, Settings.LeafCount);
		const float X = FMath::Lerp(-Settings.Length * 0.45f, Settings.Length * 0.45f, T);
		const float Y = FMath::Sin(T * ProceduralModelingToolkit::Ornaments::TwoPi * 1.5f) * Settings.Radius * 0.45f;
		const float Angle = RandomStream.FRandRange(-0.8f, 0.8f) + (LeafIndex % 2 == 0 ? 0.7f : -0.7f);
		Paths.Add(MakeLeaf(FVector(X, Y, 0.0), Angle, Settings.BranchLength * 0.45f, Settings.BranchLength * 0.18f, Settings.Thickness * 0.65f, Settings.Bevel, FName(*FString::Printf(TEXT("Leaf_%d"), LeafIndex))));
	}

	for (int32 MotifIndex = 0; MotifIndex < FMath::Max(0, Settings.FloralMotifCount); ++MotifIndex)
	{
		const float CenterT = (MotifIndex + 1.0f) / (Settings.FloralMotifCount + 1.0f);
		const FVector Center(
			FMath::Lerp(-Settings.Length * 0.35f, Settings.Length * 0.35f, CenterT),
			FMath::Cos(CenterT * ProceduralModelingToolkit::Ornaments::TwoPi) * Settings.Radius * 0.25f,
			0.0
		);

		const int32 PetalCount = 5;
		for (int32 PetalIndex = 0; PetalIndex < PetalCount; ++PetalIndex)
		{
			const float Angle = ProceduralModelingToolkit::Ornaments::TwoPi * static_cast<float>(PetalIndex) / static_cast<float>(PetalCount);
			Paths.Add(MakePetal(Center, Angle, Settings.BranchLength * 0.35f, Settings.BranchLength * 0.16f, Settings.Thickness * 0.55f, Settings.Bevel, FName(*FString::Printf(TEXT("Flower_%d_Petal_%d"), MotifIndex, PetalIndex))));
		}
	}

	ApplySymmetry(Settings.SymmetryMode, Settings.RadialSymmetryCount, Paths);
	return Paths;
}

FProceduralModelingToolkitSplinePath UProceduralModelingToolkitOrnamentGenerator::MakeSpiral(const FProceduralModelingToolkitOrnamentSettings& Settings, FName Name, float PhaseOffset)
{
	FProceduralModelingToolkitSplinePath Path;
	Path.Name = Name;
	Path.Thickness = Settings.Thickness;
	Path.Bevel = Settings.Bevel;

	const int32 Count = ProceduralModelingToolkit::Ornaments::SafePointCount(Settings.PointCount);
	for (int32 Index = 0; Index < Count; ++Index)
	{
		const float T = static_cast<float>(Index) / static_cast<float>(Count - 1);
		const float Angle = PhaseOffset + Settings.Turns * ProceduralModelingToolkit::Ornaments::TwoPi * T;
		const float Radius = Settings.Radius * T;
		Path.Points.Add(FVector(FMath::Cos(Angle) * Radius, FMath::Sin(Angle) * Radius, 0.0));
	}

	return Path;
}

FProceduralModelingToolkitSplinePath UProceduralModelingToolkitOrnamentGenerator::MakeCurve(const FProceduralModelingToolkitOrnamentSettings& Settings, FName Name, float PhaseOffset)
{
	FProceduralModelingToolkitSplinePath Path;
	Path.Name = Name;
	Path.Thickness = Settings.Thickness;
	Path.Bevel = Settings.Bevel;

	const int32 Count = ProceduralModelingToolkit::Ornaments::SafePointCount(Settings.PointCount);
	for (int32 Index = 0; Index < Count; ++Index)
	{
		const float T = static_cast<float>(Index) / static_cast<float>(Count - 1);
		const float X = FMath::Lerp(-Settings.Length * 0.5f, Settings.Length * 0.5f, T);
		const float Y = FMath::Sin(PhaseOffset + T * Settings.Turns * ProceduralModelingToolkit::Ornaments::TwoPi) * Settings.Amplitude;
		Path.Points.Add(FVector(X, Y, 0.0));
	}

	return Path;
}

TArray<FProceduralModelingToolkitSplinePath> UProceduralModelingToolkitOrnamentGenerator::MakeVine(const FProceduralModelingToolkitOrnamentSettings& Settings, FRandomStream& RandomStream, FName Prefix)
{
	TArray<FProceduralModelingToolkitSplinePath> Paths;
	FProceduralModelingToolkitSplinePath MainCurve = MakeCurve(Settings, FName(*(Prefix.ToString() + TEXT("_Main"))), RandomStream.FRandRange(-0.5f, 0.5f));
	Paths.Add(MainCurve);

	for (int32 BranchIndex = 0; BranchIndex < FMath::Max(0, Settings.BranchCount); ++BranchIndex)
	{
		const float T = (BranchIndex + 1.0f) / (Settings.BranchCount + 1.0f);
		const int32 SourceIndex = FMath::Clamp(FMath::RoundToInt(T * (MainCurve.Points.Num() - 1)), 0, MainCurve.Points.Num() - 1);
		const FVector Start = MainCurve.Points[SourceIndex];
		const float Side = (BranchIndex % 2 == 0) ? 1.0f : -1.0f;
		const float Angle = Side * RandomStream.FRandRange(0.45f, 1.0f);

		FProceduralModelingToolkitSplinePath Branch;
		Branch.Name = FName(*FString::Printf(TEXT("%s_Branch_%d"), *Prefix.ToString(), BranchIndex));
		Branch.Thickness = Settings.Thickness * 0.65f;
		Branch.Bevel = Settings.Bevel;

		const int32 BranchPoints = FMath::Max(6, Settings.PointCount / 5);
		for (int32 PointIndex = 0; PointIndex < BranchPoints; ++PointIndex)
		{
			const float BranchT = static_cast<float>(PointIndex) / static_cast<float>(BranchPoints - 1);
			FVector Local(Settings.BranchLength * BranchT, FMath::Sin(BranchT * UE_PI) * Settings.BranchLength * 0.2f * Side, 0.0);
			Local = ProceduralModelingToolkit::Ornaments::Rotate2D(Local, Angle);
			Branch.Points.Add(Start + Local);
		}

		Paths.Add(Branch);
	}

	return Paths;
}

FProceduralModelingToolkitSplinePath UProceduralModelingToolkitOrnamentGenerator::MakeLeaf(FVector Center, float AngleRadians, float Length, float Width, float Thickness, float Bevel, FName Name)
{
	FProceduralModelingToolkitSplinePath Path;
	Path.Name = Name;
	Path.bClosed = true;
	Path.Thickness = Thickness;
	Path.Bevel = Bevel;

	const int32 Count = 18;
	for (int32 Index = 0; Index < Count; ++Index)
	{
		const float Angle = ProceduralModelingToolkit::Ornaments::TwoPi * static_cast<float>(Index) / static_cast<float>(Count);
		const float X = FMath::Cos(Angle) * Length * 0.5f;
		const float Y = FMath::Sin(Angle) * Width * FMath::Sin(FMath::Max(0.0f, (X / Length + 0.5f)) * UE_PI);
		Path.Points.Add(Center + ProceduralModelingToolkit::Ornaments::Rotate2D(FVector(X, Y, 0.0), AngleRadians));
	}

	return Path;
}

FProceduralModelingToolkitSplinePath UProceduralModelingToolkitOrnamentGenerator::MakePetal(FVector Center, float AngleRadians, float Length, float Width, float Thickness, float Bevel, FName Name)
{
	return MakeLeaf(Center + ProceduralModelingToolkit::Ornaments::Rotate2D(FVector(Length * 0.5f, 0.0, 0.0), AngleRadians), AngleRadians, Length, Width, Thickness, Bevel, Name);
}

void UProceduralModelingToolkitOrnamentGenerator::ApplySymmetry(const FProceduralModelingToolkitOrnamentSettings& Settings, TArray<FProceduralModelingToolkitSplinePath>& Paths)
{
	ApplySymmetry(Settings.SymmetryMode, Settings.RadialSymmetryCount, Paths);
}

void UProceduralModelingToolkitOrnamentGenerator::ApplySymmetry(EProceduralModelingToolkitSymmetryMode SymmetryMode, int32 RadialSymmetryCount, TArray<FProceduralModelingToolkitSplinePath>& Paths)
{
	const TArray<FProceduralModelingToolkitSplinePath> OriginalPaths = Paths;

	if (SymmetryMode == EProceduralModelingToolkitSymmetryMode::MirrorX)
	{
		for (const FProceduralModelingToolkitSplinePath& Path : OriginalPaths)
		{
			Paths.Add(TransformPath(Path, FTransform(FQuat::Identity, FVector::ZeroVector, FVector(-1.0, 1.0, 1.0)), FName(*(Path.Name.ToString() + TEXT("_MirrorX")))));
		}
	}
	else if (SymmetryMode == EProceduralModelingToolkitSymmetryMode::MirrorY)
	{
		for (const FProceduralModelingToolkitSplinePath& Path : OriginalPaths)
		{
			Paths.Add(TransformPath(Path, FTransform(FQuat::Identity, FVector::ZeroVector, FVector(1.0, -1.0, 1.0)), FName(*(Path.Name.ToString() + TEXT("_MirrorY")))));
		}
	}
	else if (SymmetryMode == EProceduralModelingToolkitSymmetryMode::Radial)
	{
		const int32 Count = FMath::Max(2, RadialSymmetryCount);
		for (int32 CopyIndex = 1; CopyIndex < Count; ++CopyIndex)
		{
			const float Angle = ProceduralModelingToolkit::Ornaments::TwoPi * static_cast<float>(CopyIndex) / static_cast<float>(Count);
			const FTransform Rotation(FRotator(0.0f, FMath::RadiansToDegrees(Angle), 0.0f));
			for (const FProceduralModelingToolkitSplinePath& Path : OriginalPaths)
			{
				Paths.Add(TransformPath(Path, Rotation, FName(*FString::Printf(TEXT("%s_Radial_%d"), *Path.Name.ToString(), CopyIndex))));
			}
		}
	}
}

FProceduralModelingToolkitSplinePath UProceduralModelingToolkitOrnamentGenerator::TransformPath(const FProceduralModelingToolkitSplinePath& Source, const FTransform& Transform, FName Name)
{
	FProceduralModelingToolkitSplinePath Result = Source;
	Result.Name = Name;
	Result.Points.Reset();
	for (const FVector& Point : Source.Points)
	{
		Result.Points.Add(Transform.TransformPosition(Point));
	}
	return Result;
}
