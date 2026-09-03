#pragma once

#include "CoreMinimal.h"
#include "Engine/StaticMesh.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ProceduralModelingToolkitKitbashGenerator.generated.h"

UENUM(BlueprintType)
enum class EProceduralModelingToolkitKitbashRotationRule : uint8
{
	SocketForward,
	RandomYaw,
	FixedRotation,
	RandomFull
};

UENUM(BlueprintType)
enum class EProceduralModelingToolkitArchitecturalStyle : uint8
{
	Any,
	Gothic,
	Brutalist,
	Baroque,
	ArtNouveau,
	Surreal,
	Industrial,
	Ancient
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitKitbashSocket
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FName Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FName Type;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	TArray<FName> CompatibleTypes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FTransform LocalTransform = FTransform::Identity;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitKitbashMetadata
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	EProceduralModelingToolkitArchitecturalStyle Style = EProceduralModelingToolkitArchitecturalStyle::Any;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	TArray<FName> Tags;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	int32 Complexity = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	float Weight = 1.0f;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitKitbashPart
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FName PartId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	TSoftObjectPtr<UStaticMesh> Mesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FProceduralModelingToolkitKitbashMetadata Metadata;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	TArray<FProceduralModelingToolkitKitbashSocket> Sockets;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitKitbashRule
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FName FromSocketType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FName ToSocketType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	EProceduralModelingToolkitArchitecturalStyle RequiredStyle = EProceduralModelingToolkitArchitecturalStyle::Any;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	TArray<FName> RequiredTags;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	EProceduralModelingToolkitKitbashRotationRule RotationRule = EProceduralModelingToolkitKitbashRotationRule::SocketForward;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FRotator FixedRotation = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FVector2D ScaleRange = FVector2D(1.0, 1.0);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	int32 MaxPlacements = 1;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitKitbashSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	int32 Seed = 1337;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	int32 MaxParts = 32;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	FName RootPartId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	TArray<FProceduralModelingToolkitKitbashPart> Parts;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Kitbash")
	TArray<FProceduralModelingToolkitKitbashRule> Rules;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitKitbashPlacement
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	FName PartId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	TSoftObjectPtr<UStaticMesh> Mesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	FTransform Transform = FTransform::Identity;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	FName SourceSocket;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	FName TargetSocket;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	FProceduralModelingToolkitKitbashMetadata Metadata;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitKitbashResult
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	bool bSuccess = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	FString Message;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Kitbash")
	TArray<FProceduralModelingToolkitKitbashPlacement> Placements;
};

UCLASS()
class UProceduralModelingToolkitKitbashGenerator : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Procedural Kitbash")
	static FProceduralModelingToolkitKitbashResult GenerateKitbash(const FProceduralModelingToolkitKitbashSettings& Settings);

	UFUNCTION(BlueprintCallable, Category = "Procedural Kitbash")
	static bool AreSocketsCompatible(const FProceduralModelingToolkitKitbashSocket& SourceSocket, const FProceduralModelingToolkitKitbashSocket& CandidateSocket);

private:
	static const FProceduralModelingToolkitKitbashPart* FindPartById(const FProceduralModelingToolkitKitbashSettings& Settings, FName PartId);
	static const FProceduralModelingToolkitKitbashPart* SelectWeightedPart(const TArray<const FProceduralModelingToolkitKitbashPart*>& Candidates, FRandomStream& RandomStream);
	static bool PartMatchesRule(const FProceduralModelingToolkitKitbashPart& Part, const FProceduralModelingToolkitKitbashRule& Rule);
	static FTransform MakePlacementTransform(const FTransform& SourceWorldTransform, const FProceduralModelingToolkitKitbashSocket& TargetSocket, const FProceduralModelingToolkitKitbashRule& Rule, FRandomStream& RandomStream);
};
