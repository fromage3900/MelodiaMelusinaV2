#pragma once

#include "CoreMinimal.h"
#include "PCGSettings.h"
#include "ProceduralModelingToolkitOrnamentGenerator.h"
#include "ProceduralModelingToolkitPCGNodes.generated.h"

class UProceduralModelingToolkitModifierStack;
class UStaticMesh;

UCLASS(BlueprintType, ClassGroup = (Procedural))
class UProceduralModelingToolkitPCGGenerateOrnamentsSettings : public UPCGSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit")
	bool bUseFiligree = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit", meta = (EditCondition = "!bUseFiligree"))
	FProceduralModelingToolkitOrnamentSettings OrnamentSettings;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit", meta = (EditCondition = "bUseFiligree"))
	FProceduralModelingToolkitFiligreeSettings FiligreeSettings;

	virtual bool UseSeed() const override { return true; }
	virtual TArray<FPCGPinProperties> InputPinProperties() const override;
	virtual TArray<FPCGPinProperties> OutputPinProperties() const override;

#if WITH_EDITOR
	virtual FName GetDefaultNodeName() const override;
	virtual FText GetDefaultNodeTitle() const override;
	virtual FText GetNodeTooltipText() const override;
	virtual EPCGSettingsType GetType() const override { return EPCGSettingsType::Generic; }
#endif

protected:
	virtual FPCGElementPtr CreateElement() const override;
};

UCLASS(BlueprintType, ClassGroup = (Procedural))
class UProceduralModelingToolkitPCGModifyMeshesSettings : public UPCGSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit")
	TObjectPtr<UStaticMesh> SourceMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit")
	TObjectPtr<UProceduralModelingToolkitModifierStack> ModifierStack;

	virtual TArray<FPCGPinProperties> InputPinProperties() const override;
	virtual TArray<FPCGPinProperties> OutputPinProperties() const override;

#if WITH_EDITOR
	virtual FName GetDefaultNodeName() const override;
	virtual FText GetDefaultNodeTitle() const override;
	virtual FText GetNodeTooltipText() const override;
	virtual EPCGSettingsType GetType() const override { return EPCGSettingsType::DynamicMesh; }
#endif

protected:
	virtual FPCGElementPtr CreateElement() const override;
};

UCLASS(BlueprintType, ClassGroup = (Procedural))
class UProceduralModelingToolkitPCGProcessSplinesSettings : public UPCGSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit")
	FProceduralModelingToolkitOrnamentSettings OrnamentSettings;

	virtual bool UseSeed() const override { return true; }
	virtual TArray<FPCGPinProperties> InputPinProperties() const override;
	virtual TArray<FPCGPinProperties> OutputPinProperties() const override;

#if WITH_EDITOR
	virtual FName GetDefaultNodeName() const override;
	virtual FText GetDefaultNodeTitle() const override;
	virtual FText GetNodeTooltipText() const override;
	virtual EPCGSettingsType GetType() const override { return EPCGSettingsType::Generic; }
#endif

protected:
	virtual FPCGElementPtr CreateElement() const override;
};

UCLASS(BlueprintType, ClassGroup = (Procedural))
class UProceduralModelingToolkitPCGGenerateDynamicMeshSettings : public UPCGSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit")
	TObjectPtr<UProceduralModelingToolkitModifierStack> ModifierStack;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit")
	bool bGeneratePreviewCube = true;

	virtual TArray<FPCGPinProperties> InputPinProperties() const override;
	virtual TArray<FPCGPinProperties> OutputPinProperties() const override;

#if WITH_EDITOR
	virtual FName GetDefaultNodeName() const override;
	virtual FText GetDefaultNodeTitle() const override;
	virtual FText GetNodeTooltipText() const override;
	virtual EPCGSettingsType GetType() const override { return EPCGSettingsType::DynamicMesh; }
#endif

protected:
	virtual FPCGElementPtr CreateElement() const override;
};

UCLASS(BlueprintType, ClassGroup = (Procedural))
class UProceduralModelingToolkitPCGOutputStaticMeshSettings : public UPCGSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit")
	TObjectPtr<UStaticMesh> SourceMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Toolkit")
	TObjectPtr<UProceduralModelingToolkitModifierStack> ModifierStack;

	virtual TArray<FPCGPinProperties> InputPinProperties() const override;
	virtual TArray<FPCGPinProperties> OutputPinProperties() const override;

#if WITH_EDITOR
	virtual FName GetDefaultNodeName() const override;
	virtual FText GetDefaultNodeTitle() const override;
	virtual FText GetNodeTooltipText() const override;
	virtual EPCGSettingsType GetType() const override { return EPCGSettingsType::Resource; }
#endif

protected:
	virtual FPCGElementPtr CreateElement() const override;
};
