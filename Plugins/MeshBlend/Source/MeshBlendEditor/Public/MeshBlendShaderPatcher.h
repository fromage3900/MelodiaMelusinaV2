// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MeshBlendShaderPatcher.generated.h"

UCLASS(BlueprintType)
class MESHBLENDEDITOR_API UShaderPatchItem : public UObject
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "MeshBlend")
	FString FilePath = FString();

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "MeshBlend")
	FString Description = FString();

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "MeshBlend")
	FString SearchLine = FString();

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "MeshBlend")
	FString ReplaceLine = FString();

	static UShaderPatchItem* Create(const FString& InFilePath, const FString& InDescription, const FString& InSearchLine, const FString& InReplaceLine)
	{
		UShaderPatchItem* NewItem = NewObject<UShaderPatchItem>();
		NewItem->FilePath = InFilePath;
		NewItem->Description = InDescription;
		NewItem->SearchLine = InSearchLine;
		NewItem->ReplaceLine = InReplaceLine;
		return NewItem;
	}
};

UCLASS()
class MESHBLENDEDITOR_API UMeshBlendShaderPatcher : public UBlueprintFunctionLibrary
{
	GENERATED_UCLASS_BODY()
	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Get Lines In File"), Category = "MeshBlend Shader Patcher")
	static int32 GetLinesInFile(const FString& FilePath, const FString& SearchLine);
	static bool EnsureFileIsWriteable(const FString& FullPath, FString& OutErrorMessage);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Replace Content In File"), Category = "MeshBlend Shader Patcher")
	static bool ReplaceContentInFile(const FString& FilePath, const FString& SearchLine, const FString& ReplaceLine, FString& OutErrorMessage);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Restart Editor"), Category = "MeshBlend Shader Patcher")
	static void RestartEditor();

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Get Shader Patch Items"), Category = "MeshBlend Shader Patcher")
	static TArray<UShaderPatchItem*> GetShaderPatchItems();

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Needs to Patch Shaders"), Category = "MeshBlend Shader Patcher")
	static bool NeedsToPatchShaders();

private:
	static FString GetFullShaderPath(const FString& FilePath);
};
