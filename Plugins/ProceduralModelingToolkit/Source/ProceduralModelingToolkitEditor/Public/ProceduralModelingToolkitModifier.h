#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectPtr.h"
#include "ProceduralModelingToolkitModifier.generated.h"

class UDynamicMesh;

UENUM(BlueprintType)
enum class EProceduralModelingToolkitModifierParameterType : uint8
{
	Boolean,
	Integer,
	Float,
	Vector,
	Rotator,
	String
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitModifierParameter
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	FName Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	EProceduralModelingToolkitModifierParameterType Type = EProceduralModelingToolkitModifierParameterType::Float;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	bool BoolValue = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	int32 IntValue = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	double FloatValue = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	FVector VectorValue = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	FRotator RotatorValue = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	FString StringValue;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitModifierParameters
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	int32 Version = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	TArray<FProceduralModelingToolkitModifierParameter> Values;

	const FProceduralModelingToolkitModifierParameter* Find(FName Name) const;
	FProceduralModelingToolkitModifierParameter* FindMutable(FName Name);
	void AddBool(FName Name, bool Value);
	void AddInt(FName Name, int32 Value);
	void AddFloat(FName Name, double Value);
	void AddVector(FName Name, FVector Value);
	void AddRotator(FName Name, FRotator Value);
	void AddString(FName Name, const FString& Value);
	bool GetBool(FName Name, bool DefaultValue = false) const;
	int32 GetInt(FName Name, int32 DefaultValue = 0) const;
	double GetFloat(FName Name, double DefaultValue = 0.0) const;
	FVector GetVector(FName Name, FVector DefaultValue = FVector::ZeroVector) const;
	FRotator GetRotator(FName Name, FRotator DefaultValue = FRotator::ZeroRotator) const;
	FString GetString(FName Name, const FString& DefaultValue = FString()) const;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitModifierExecutionContext
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Modifier")
	FString SourceAssetPath;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Modifier")
	FString OutputAssetPath;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Modifier")
	int32 StackVersion = 1;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitModifierResult
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Modifier")
	bool bSuccess = true;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Modifier")
	FString Message;

	static FProceduralModelingToolkitModifierResult Success(const FString& Message = FString());
	static FProceduralModelingToolkitModifierResult Failure(const FString& Message);
};

UCLASS(Abstract, BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitModifier : public UObject
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitModifier();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	bool bEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	FName ModifierId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier")
	FProceduralModelingToolkitModifierParameters Parameters;

	virtual FProceduralModelingToolkitModifierResult Execute(
		UDynamicMesh* TargetMesh,
		const FProceduralModelingToolkitModifierExecutionContext& Context
	);

	virtual void Serialize(FArchive& Ar) override;

	UFUNCTION(BlueprintCallable, Category = "Procedural Modifier")
	void SetEnabled(bool bInEnabled);

	UFUNCTION(BlueprintCallable, Category = "Procedural Modifier")
	bool IsEnabled() const;
};
