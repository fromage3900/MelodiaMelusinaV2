#pragma once

#include "CoreMinimal.h"

class UStaticMesh;
class UProceduralModelingToolkitModifierStack;

struct FProceduralModelingToolkitMeshPipelineResult
{
	bool bSuccess = false;
	FString SourcePath;
	FString OutputPath;
	FString Message;
	int32 SourceTriangleCount = 0;
	int32 DynamicMeshTriangleCount = 0;
	int32 OutputTriangleCount = 0;
};

class FProceduralModelingToolkitDynamicMeshPipeline
{
public:
	static TArray<UStaticMesh*> GetSelectedStaticMeshAssets();
	static TArray<FProceduralModelingToolkitMeshPipelineResult> ProcessSelectedStaticMeshes();
	static FProceduralModelingToolkitMeshPipelineResult ProcessStaticMesh(UStaticMesh* SourceMesh);
	static FProceduralModelingToolkitMeshPipelineResult ProcessStaticMesh(UStaticMesh* SourceMesh, UProceduralModelingToolkitModifierStack* ModifierStack);

private:
	static bool ValidateSourceMesh(UStaticMesh* SourceMesh, FProceduralModelingToolkitMeshPipelineResult& Result);
	static bool ValidateOutputMesh(UStaticMesh* SourceMesh, UStaticMesh* OutputMesh, const FString& OutputPath, FProceduralModelingToolkitMeshPipelineResult& Result);
	static UStaticMesh* DuplicateSourceMesh(UStaticMesh* SourceMesh, FString& OutOutputPath, FProceduralModelingToolkitMeshPipelineResult& Result);
	static FString GetOutputRootPath();
};
