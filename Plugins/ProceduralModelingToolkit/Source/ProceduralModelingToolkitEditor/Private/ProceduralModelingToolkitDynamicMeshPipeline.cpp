#include "ProceduralModelingToolkitDynamicMeshPipeline.h"

#include "ProceduralModelingToolkitEditorModule.h"
#include "ProceduralModelingToolkitModifierStack.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "Editor.h"
#include "EditorAssetLibrary.h"
#include "Engine/Selection.h"
#include "Engine/StaticMesh.h"
#include "GeometryScript/GeometryScriptTypes.h"
#include "GeometryScript/MeshAssetFunctions.h"
#include "IAssetTools.h"
#include "Misc/PackageName.h"
#include "UDynamicMesh.h"

namespace ProceduralModelingToolkit::DynamicMeshPipeline
{
	static constexpr const TCHAR* OutputRootPath = TEXT("/Game/EnvSandbox/Procedural/Meshes/Processed");
	static constexpr const TCHAR* OutputSuffix = TEXT("_PMT_DynMesh");

	static FString ObjectPathToPackagePath(const UObject* Object)
	{
		return Object ? Object->GetPathName().Split(TEXT("."), nullptr, nullptr, ESearchCase::IgnoreCase, ESearchDir::FromEnd) ? Object->GetPathName().Left(Object->GetPathName().Find(TEXT("."), ESearchCase::IgnoreCase, ESearchDir::FromEnd)) : Object->GetPathName() : FString();
	}
}

TArray<UStaticMesh*> FProceduralModelingToolkitDynamicMeshPipeline::GetSelectedStaticMeshAssets()
{
	TArray<UStaticMesh*> StaticMeshes;

	if (!GEditor)
	{
		return StaticMeshes;
	}

	USelection* SelectedObjects = GEditor->GetSelectedObjects();
	if (!SelectedObjects)
	{
		return StaticMeshes;
	}

	TArray<UObject*> Selected;
	SelectedObjects->GetSelectedObjects(Selected);
	for (UObject* Object : Selected)
	{
		if (UStaticMesh* StaticMesh = Cast<UStaticMesh>(Object))
		{
			StaticMeshes.AddUnique(StaticMesh);
		}
	}

	return StaticMeshes;
}

TArray<FProceduralModelingToolkitMeshPipelineResult> FProceduralModelingToolkitDynamicMeshPipeline::ProcessSelectedStaticMeshes()
{
	TArray<FProceduralModelingToolkitMeshPipelineResult> Results;
	const TArray<UStaticMesh*> StaticMeshes = GetSelectedStaticMeshAssets();

	if (StaticMeshes.IsEmpty())
	{
		FProceduralModelingToolkitMeshPipelineResult Result;
		Result.Message = TEXT("No Static Mesh assets selected in the Content Browser.");
		Results.Add(MoveTemp(Result));
		UE_LOG(LogProceduralModelingToolkit, Warning, TEXT("%s"), *Results.Last().Message);
		return Results;
	}

	for (UStaticMesh* StaticMesh : StaticMeshes)
	{
		Results.Add(ProcessStaticMesh(StaticMesh));
	}

	return Results;
}

FProceduralModelingToolkitMeshPipelineResult FProceduralModelingToolkitDynamicMeshPipeline::ProcessStaticMesh(UStaticMesh* SourceMesh)
{
	return ProcessStaticMesh(SourceMesh, nullptr);
}

FProceduralModelingToolkitMeshPipelineResult FProceduralModelingToolkitDynamicMeshPipeline::ProcessStaticMesh(UStaticMesh* SourceMesh, UProceduralModelingToolkitModifierStack* ModifierStack)
{
	FProceduralModelingToolkitMeshPipelineResult Result;
	Result.SourcePath = ProceduralModelingToolkit::DynamicMeshPipeline::ObjectPathToPackagePath(SourceMesh);

	if (!ValidateSourceMesh(SourceMesh, Result))
	{
		UE_LOG(LogProceduralModelingToolkit, Warning, TEXT("Dynamic Mesh pipeline skipped source '%s': %s"), *Result.SourcePath, *Result.Message);
		return Result;
	}

	FString OutputPath;
	UStaticMesh* OutputMesh = DuplicateSourceMesh(SourceMesh, OutputPath, Result);
	if (!OutputMesh)
	{
		UE_LOG(LogProceduralModelingToolkit, Error, TEXT("Dynamic Mesh pipeline duplicate failed for '%s': %s"), *Result.SourcePath, *Result.Message);
		return Result;
	}

	Result.OutputPath = OutputPath;

	UDynamicMesh* DynamicMesh = NewObject<UDynamicMesh>(GetTransientPackage(), NAME_None, RF_Transient);
	DynamicMesh->Reset();

	FGeometryScriptCopyMeshFromAssetOptions CopyFromOptions;
	CopyFromOptions.bApplyBuildSettings = true;
	CopyFromOptions.bRequestTangents = true;
	CopyFromOptions.bIgnoreRemoveDegenerates = true;
	CopyFromOptions.bUseBuildScale = true;

	const FGeometryScriptMeshReadLOD ReadLOD(EGeometryScriptLODType::SourceModel, 0);
	EGeometryScriptOutcomePins CopyFromOutcome = EGeometryScriptOutcomePins::Failure;
	UGeometryScriptDebug* Debug = NewObject<UGeometryScriptDebug>(GetTransientPackage(), NAME_None, RF_Transient);

	UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshFromStaticMeshV2(
		SourceMesh,
		DynamicMesh,
		CopyFromOptions,
		ReadLOD,
		CopyFromOutcome,
		/*bUseSectionMaterials=*/true,
		Debug
	);

	Result.DynamicMeshTriangleCount = DynamicMesh ? DynamicMesh->GetTriangleCount() : 0;
	if (CopyFromOutcome == EGeometryScriptOutcomePins::Failure || !DynamicMesh || DynamicMesh->IsEmpty())
	{
		Result.Message = TEXT("Copy Mesh From Static Mesh failed or produced an empty Dynamic Mesh.");
		UEditorAssetLibrary::DeleteAsset(OutputPath);
		UE_LOG(LogProceduralModelingToolkit, Error, TEXT("Dynamic Mesh pipeline conversion failed for '%s'."), *Result.SourcePath);
		return Result;
	}

	UProceduralModelingToolkitModifierStack* StackToExecute = ModifierStack ? ModifierStack : NewObject<UProceduralModelingToolkitModifierStack>(GetTransientPackage(), NAME_None, RF_Transient);
	FProceduralModelingToolkitModifierExecutionContext ModifierContext;
	ModifierContext.SourceAssetPath = Result.SourcePath;
	ModifierContext.OutputAssetPath = Result.OutputPath;
	ModifierContext.StackVersion = StackToExecute->Version;

	const FProceduralModelingToolkitModifierStackResult ModifierStackResult = StackToExecute->Execute(DynamicMesh, ModifierContext);
	if (!ModifierStackResult.bSuccess)
	{
		Result.Message = TEXT("Modifier stack execution failed.");
		UEditorAssetLibrary::DeleteAsset(OutputPath);
		UE_LOG(LogProceduralModelingToolkit, Error, TEXT("Dynamic Mesh pipeline modifier stack failed for '%s'."), *Result.SourcePath);
		return Result;
	}

	Result.DynamicMeshTriangleCount = DynamicMesh->GetTriangleCount();

	FGeometryScriptCopyMeshToAssetOptions CopyToOptions;
	CopyToOptions.bEnableRecomputeNormals = false;
	CopyToOptions.bEnableRecomputeTangents = false;
	CopyToOptions.bEnableRemoveDegenerates = false;
	CopyToOptions.bUseBuildScale = true;
	CopyToOptions.bReplaceMaterials = false;
	CopyToOptions.bCleanAssignedMaterials = true;
	CopyToOptions.GenerateLightmapUVs = EGeometryScriptGenerateLightmapUVOptions::MatchTargetLODSetting;
	CopyToOptions.bApplyNaniteSettings = false;
	CopyToOptions.bEmitTransaction = true;
	CopyToOptions.bDeferMeshPostEditChange = false;

	const FGeometryScriptMeshWriteLOD WriteLOD;
	EGeometryScriptOutcomePins CopyToOutcome = EGeometryScriptOutcomePins::Failure;
	UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshToStaticMesh(
		DynamicMesh,
		OutputMesh,
		CopyToOptions,
		WriteLOD,
		CopyToOutcome,
		/*bUseSectionMaterials=*/true,
		Debug
	);

	if (CopyToOutcome == EGeometryScriptOutcomePins::Failure)
	{
		Result.Message = TEXT("Copy Mesh To Static Mesh failed.");
		UEditorAssetLibrary::DeleteAsset(OutputPath);
		UE_LOG(LogProceduralModelingToolkit, Error, TEXT("Dynamic Mesh pipeline save-back failed for '%s'."), *Result.SourcePath);
		return Result;
	}

	OutputMesh->MarkPackageDirty();
	FAssetRegistryModule::AssetCreated(OutputMesh);
	UEditorAssetLibrary::SaveLoadedAsset(OutputMesh, /*bOnlyIfIsDirty=*/false);

	if (!ValidateOutputMesh(SourceMesh, OutputMesh, OutputPath, Result))
	{
		UE_LOG(LogProceduralModelingToolkit, Error, TEXT("Dynamic Mesh pipeline validation failed for '%s': %s"), *Result.SourcePath, *Result.Message);
		return Result;
	}

	Result.bSuccess = true;
	Result.Message = FString::Printf(
		TEXT("Created '%s' via Static Mesh -> Dynamic Mesh -> Static Mesh round trip."),
		*OutputPath
	);

	UE_LOG(
		LogProceduralModelingToolkit,
		Log,
		TEXT("Dynamic Mesh pipeline succeeded: source='%s', output='%s', source_tris=%d, dynamic_tris=%d, output_tris=%d"),
		*Result.SourcePath,
		*Result.OutputPath,
		Result.SourceTriangleCount,
		Result.DynamicMeshTriangleCount,
		Result.OutputTriangleCount
	);

	return Result;
}

bool FProceduralModelingToolkitDynamicMeshPipeline::ValidateSourceMesh(UStaticMesh* SourceMesh, FProceduralModelingToolkitMeshPipelineResult& Result)
{
	if (!SourceMesh)
	{
		Result.Message = TEXT("Source asset is not a Static Mesh.");
		return false;
	}

	if (SourceMesh->GetPackage() && SourceMesh->GetPackage()->HasAnyPackageFlags(PKG_CompiledIn))
	{
		Result.Message = TEXT("Compiled-in engine assets are not valid pipeline sources.");
		return false;
	}

	if (SourceMesh->GetNumSourceModels() <= 0)
	{
		Result.Message = TEXT("Source Static Mesh has no source model LODs.");
		return false;
	}

	Result.SourceTriangleCount = SourceMesh->GetNumTriangles(0);
	if (Result.SourceTriangleCount <= 0)
	{
		Result.Message = TEXT("Source Static Mesh LOD0 has no triangles.");
		return false;
	}

	EGeometryScriptSearchOutcomePins LODOutcome = EGeometryScriptSearchOutcomePins::NotFound;
	const bool bHasLOD = UGeometryScriptLibrary_StaticMeshFunctions::CheckStaticMeshHasAvailableLOD(
		SourceMesh,
		FGeometryScriptMeshReadLOD(EGeometryScriptLODType::SourceModel, 0),
		LODOutcome
	);

	if (!bHasLOD || LODOutcome == EGeometryScriptSearchOutcomePins::NotFound)
	{
		Result.Message = TEXT("Geometry Script cannot read SourceModel LOD0 from the selected Static Mesh.");
		return false;
	}

	return true;
}

bool FProceduralModelingToolkitDynamicMeshPipeline::ValidateOutputMesh(UStaticMesh* SourceMesh, UStaticMesh* OutputMesh, const FString& OutputPath, FProceduralModelingToolkitMeshPipelineResult& Result)
{
	if (!OutputMesh)
	{
		Result.Message = TEXT("Output Static Mesh was not created.");
		return false;
	}

	if (OutputMesh == SourceMesh)
	{
		Result.Message = TEXT("Output mesh aliases the source mesh. Source preservation check failed.");
		return false;
	}

	if (OutputPath == Result.SourcePath)
	{
		Result.Message = TEXT("Output path matches source path. Source preservation check failed.");
		return false;
	}

	if (!UEditorAssetLibrary::DoesAssetExist(OutputPath))
	{
		Result.Message = TEXT("Output asset was not saved to disk.");
		return false;
	}

	Result.OutputTriangleCount = OutputMesh->GetNumTriangles(0);
	if (Result.OutputTriangleCount <= 0)
	{
		Result.Message = TEXT("Output Static Mesh LOD0 has no triangles.");
		return false;
	}

	if (Result.DynamicMeshTriangleCount <= 0)
	{
		Result.Message = TEXT("Dynamic Mesh validation count is empty.");
		return false;
	}

	if (Result.OutputTriangleCount != Result.DynamicMeshTriangleCount)
	{
		Result.Message = FString::Printf(
			TEXT("Triangle count mismatch after save-back. Dynamic=%d Output=%d"),
			Result.DynamicMeshTriangleCount,
			Result.OutputTriangleCount
		);
		return false;
	}

	return true;
}

UStaticMesh* FProceduralModelingToolkitDynamicMeshPipeline::DuplicateSourceMesh(UStaticMesh* SourceMesh, FString& OutOutputPath, FProceduralModelingToolkitMeshPipelineResult& Result)
{
	if (!UEditorAssetLibrary::DoesDirectoryExist(GetOutputRootPath()))
	{
		UEditorAssetLibrary::MakeDirectory(GetOutputRootPath());
	}

	IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();

	const FString BasePackagePath = GetOutputRootPath() / (SourceMesh->GetName() + ProceduralModelingToolkit::DynamicMeshPipeline::OutputSuffix);
	FString UniquePackageName;
	FString UniqueAssetName;
	AssetTools.CreateUniqueAssetName(BasePackagePath, TEXT(""), UniquePackageName, UniqueAssetName);

	UObject* DuplicatedObject = AssetTools.DuplicateAsset(UniqueAssetName, GetOutputRootPath(), SourceMesh);
	UStaticMesh* DuplicatedMesh = Cast<UStaticMesh>(DuplicatedObject);
	if (!DuplicatedMesh)
	{
		Result.Message = TEXT("Static Mesh duplication failed.");
		return nullptr;
	}

	OutOutputPath = GetOutputRootPath() / UniqueAssetName;
	return DuplicatedMesh;
}

FString FProceduralModelingToolkitDynamicMeshPipeline::GetOutputRootPath()
{
	return ProceduralModelingToolkit::DynamicMeshPipeline::OutputRootPath;
}
