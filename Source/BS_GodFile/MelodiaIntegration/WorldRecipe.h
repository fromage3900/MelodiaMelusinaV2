#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Engine/World.h"
#include "WorldRecipe.generated.h"

/**
 * Editor bookmark for a World Compiler recipe JSON.
 * Canonical source remains recipes/*.json; this asset does not compile worlds.
 */
UCLASS(BlueprintType)
class BS_GODFILE_API UWorldRecipe final : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	virtual FPrimaryAssetId GetPrimaryAssetId() const override
	{
		return FPrimaryAssetId(FPrimaryAssetType(TEXT("WorldRecipe")), GetFName());
	}

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WorldCompiler")
	FName RecipeId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WorldCompiler")
	int32 WorldSeed = 0;

	/** Repo-relative path, e.g. recipes/morning_rainbow_bloom.v1.json */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WorldCompiler")
	FString RecipeRelPath;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WorldCompiler")
	TSoftObjectPtr<UWorld> Level;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WorldCompiler|LastApply")
	FString LastBundleRelPath;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WorldCompiler|LastApply")
	FString LastProofRelPath;
};
