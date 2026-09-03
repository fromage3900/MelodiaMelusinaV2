#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ProceduralModelingToolkitOrnamentGenerator.generated.h"

UENUM(BlueprintType)
enum class EProceduralModelingToolkitOrnamentKind : uint8
{
	Spiral,
	Curve,
	SymmetricalCurls,
	Vine
};

UENUM(BlueprintType)
enum class EProceduralModelingToolkitSymmetryMode : uint8
{
	None,
	MirrorX,
	MirrorY,
	Radial
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitSplinePath
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	FName Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	TArray<FVector> Points;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	bool bClosed = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float Thickness = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float Bevel = 0.25f;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitOrnamentSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	EProceduralModelingToolkitOrnamentKind Kind = EProceduralModelingToolkitOrnamentKind::Spiral;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	int32 Seed = 1337;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	int32 PointCount = 64;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float Radius = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float Length = 300.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float Turns = 2.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float Amplitude = 50.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	int32 BranchCount = 4;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float BranchLength = 80.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	EProceduralModelingToolkitSymmetryMode SymmetryMode = EProceduralModelingToolkitSymmetryMode::None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	int32 RadialSymmetryCount = 4;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float Thickness = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ornament")
	float Bevel = 0.25f;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitFiligreeSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	int32 Seed = 1337;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	int32 VineCount = 2;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	int32 BranchCount = 6;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	int32 LeafCount = 10;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	int32 FloralMotifCount = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	float Radius = 120.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	float Length = 360.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	float BranchLength = 75.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	EProceduralModelingToolkitSymmetryMode SymmetryMode = EProceduralModelingToolkitSymmetryMode::MirrorX;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	int32 RadialSymmetryCount = 4;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	float Thickness = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Filigree")
	float Bevel = 0.25f;
};

UCLASS()
class UProceduralModelingToolkitOrnamentGenerator : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Procedural Ornament")
	static TArray<FProceduralModelingToolkitSplinePath> GenerateOrnament(const FProceduralModelingToolkitOrnamentSettings& Settings);

	UFUNCTION(BlueprintCallable, Category = "Procedural Filigree")
	static TArray<FProceduralModelingToolkitSplinePath> GenerateFiligree(const FProceduralModelingToolkitFiligreeSettings& Settings);

private:
	static FProceduralModelingToolkitSplinePath MakeSpiral(const FProceduralModelingToolkitOrnamentSettings& Settings, FName Name, float PhaseOffset);
	static FProceduralModelingToolkitSplinePath MakeCurve(const FProceduralModelingToolkitOrnamentSettings& Settings, FName Name, float PhaseOffset);
	static TArray<FProceduralModelingToolkitSplinePath> MakeVine(const FProceduralModelingToolkitOrnamentSettings& Settings, FRandomStream& RandomStream, FName Prefix);
	static FProceduralModelingToolkitSplinePath MakeLeaf(FVector Center, float AngleRadians, float Length, float Width, float Thickness, float Bevel, FName Name);
	static FProceduralModelingToolkitSplinePath MakePetal(FVector Center, float AngleRadians, float Length, float Width, float Thickness, float Bevel, FName Name);
	static void ApplySymmetry(const FProceduralModelingToolkitOrnamentSettings& Settings, TArray<FProceduralModelingToolkitSplinePath>& Paths);
	static void ApplySymmetry(EProceduralModelingToolkitSymmetryMode SymmetryMode, int32 RadialSymmetryCount, TArray<FProceduralModelingToolkitSplinePath>& Paths);
	static FProceduralModelingToolkitSplinePath TransformPath(const FProceduralModelingToolkitSplinePath& Source, const FTransform& Transform, FName Name);
};
