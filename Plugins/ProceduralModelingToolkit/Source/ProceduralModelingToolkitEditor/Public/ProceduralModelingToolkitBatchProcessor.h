#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ProceduralModelingToolkitBatchProcessor.generated.h"

class UProceduralModelingToolkitModifierStack;
class UStaticMesh;

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitBatchSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Batch")
	TArray<TObjectPtr<UStaticMesh>> StaticMeshAssets;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Batch")
	TArray<FString> SourceFolders;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Batch")
	TArray<FString> CollectionNames;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Batch")
	FString NameContains;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Batch")
	bool bRecursiveFolders = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Batch")
	bool bAllowCancel = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Batch")
	TObjectPtr<UProceduralModelingToolkitModifierStack> ModifierStack;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitBatchAssetResult
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	bool bSuccess = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	FString SourcePath;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	FString OutputPath;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	FString Message;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitBatchResult
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	bool bCancelled = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	int32 TotalAssets = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	int32 ProcessedAssets = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	int32 SucceededAssets = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	int32 FailedAssets = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Batch")
	TArray<FProceduralModelingToolkitBatchAssetResult> AssetResults;
};

UCLASS()
class UProceduralModelingToolkitBatchProcessor : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Procedural Batch")
	static FProceduralModelingToolkitBatchResult ProcessSelectedAssets(UProceduralModelingToolkitModifierStack* ModifierStack);

	UFUNCTION(BlueprintCallable, Category = "Procedural Batch")
	static FProceduralModelingToolkitBatchResult ProcessFolders(const TArray<FString>& SourceFolders, UProceduralModelingToolkitModifierStack* ModifierStack, bool bRecursiveFolders = true, const FString& NameContains = FString());

	UFUNCTION(BlueprintCallable, Category = "Procedural Batch")
	static FProceduralModelingToolkitBatchResult ProcessCollections(const TArray<FString>& CollectionNames, UProceduralModelingToolkitModifierStack* ModifierStack, const FString& NameContains = FString());

	UFUNCTION(BlueprintCallable, Category = "Procedural Batch")
	static FProceduralModelingToolkitBatchResult ProcessBatch(const FProceduralModelingToolkitBatchSettings& Settings);

private:
	static void GatherMeshesFromFolders(const TArray<FString>& SourceFolders, bool bRecursiveFolders, const FString& NameContains, TArray<UStaticMesh*>& OutMeshes);
	static void GatherMeshesFromCollections(const TArray<FString>& CollectionNames, const FString& NameContains, TArray<UStaticMesh*>& OutMeshes);
	static void AddMeshIfAccepted(UStaticMesh* StaticMesh, const FString& NameContains, TArray<UStaticMesh*>& OutMeshes);
};
