#include "ProceduralModelingToolkitBatchProcessor.h"

#include "ProceduralModelingToolkitDynamicMeshPipeline.h"
#include "ProceduralModelingToolkitEditorModule.h"
#include "ProceduralModelingToolkitModifierStack.h"

#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "CollectionManagerModule.h"
#include "CollectionManagerTypes.h"
#include "Engine/StaticMesh.h"
#include "ICollectionContainer.h"
#include "ICollectionManager.h"
#include "Misc/ScopedSlowTask.h"

FProceduralModelingToolkitBatchResult UProceduralModelingToolkitBatchProcessor::ProcessSelectedAssets(UProceduralModelingToolkitModifierStack* ModifierStack)
{
	FProceduralModelingToolkitBatchSettings Settings;
	Settings.ModifierStack = ModifierStack;
	for (UStaticMesh* StaticMesh : FProceduralModelingToolkitDynamicMeshPipeline::GetSelectedStaticMeshAssets())
	{
		Settings.StaticMeshAssets.Add(StaticMesh);
	}
	return ProcessBatch(Settings);
}

FProceduralModelingToolkitBatchResult UProceduralModelingToolkitBatchProcessor::ProcessFolders(const TArray<FString>& SourceFolders, UProceduralModelingToolkitModifierStack* ModifierStack, bool bRecursiveFolders, const FString& NameContains)
{
	FProceduralModelingToolkitBatchSettings Settings;
	Settings.SourceFolders = SourceFolders;
	Settings.ModifierStack = ModifierStack;
	Settings.bRecursiveFolders = bRecursiveFolders;
	Settings.NameContains = NameContains;
	return ProcessBatch(Settings);
}

FProceduralModelingToolkitBatchResult UProceduralModelingToolkitBatchProcessor::ProcessCollections(const TArray<FString>& CollectionNames, UProceduralModelingToolkitModifierStack* ModifierStack, const FString& NameContains)
{
	FProceduralModelingToolkitBatchSettings Settings;
	Settings.CollectionNames = CollectionNames;
	Settings.ModifierStack = ModifierStack;
	Settings.NameContains = NameContains;
	return ProcessBatch(Settings);
}

FProceduralModelingToolkitBatchResult UProceduralModelingToolkitBatchProcessor::ProcessBatch(const FProceduralModelingToolkitBatchSettings& Settings)
{
	FProceduralModelingToolkitBatchResult BatchResult;

	TArray<UStaticMesh*> Meshes;
	for (UStaticMesh* StaticMesh : Settings.StaticMeshAssets)
	{
		AddMeshIfAccepted(StaticMesh, Settings.NameContains, Meshes);
	}

	GatherMeshesFromFolders(Settings.SourceFolders, Settings.bRecursiveFolders, Settings.NameContains, Meshes);
	GatherMeshesFromCollections(Settings.CollectionNames, Settings.NameContains, Meshes);

	BatchResult.TotalAssets = Meshes.Num();
	if (Meshes.IsEmpty())
	{
		UE_LOG(LogProceduralModelingToolkit, Warning, TEXT("Batch processor found no Static Mesh assets to process."));
		return BatchResult;
	}

	FScopedSlowTask SlowTask(static_cast<float>(Meshes.Num()), FText::FromString(TEXT("Processing procedural mesh batch")));
	if (Settings.bAllowCancel)
	{
		SlowTask.MakeDialog(true);
	}

	for (UStaticMesh* StaticMesh : Meshes)
	{
		if (Settings.bAllowCancel && SlowTask.ShouldCancel())
		{
			BatchResult.bCancelled = true;
			UE_LOG(LogProceduralModelingToolkit, Warning, TEXT("Batch processor cancelled after %d of %d assets."), BatchResult.ProcessedAssets, BatchResult.TotalAssets);
			break;
		}

		const FString MeshName = StaticMesh ? StaticMesh->GetName() : TEXT("Invalid Static Mesh");
		SlowTask.EnterProgressFrame(1.0f, FText::FromString(FString::Printf(TEXT("Processing %s"), *MeshName)));

		const FProceduralModelingToolkitMeshPipelineResult PipelineResult =
			FProceduralModelingToolkitDynamicMeshPipeline::ProcessStaticMesh(StaticMesh, Settings.ModifierStack);

		FProceduralModelingToolkitBatchAssetResult AssetResult;
		AssetResult.bSuccess = PipelineResult.bSuccess;
		AssetResult.SourcePath = PipelineResult.SourcePath;
		AssetResult.OutputPath = PipelineResult.OutputPath;
		AssetResult.Message = PipelineResult.Message;
		BatchResult.AssetResults.Add(AssetResult);

		BatchResult.ProcessedAssets++;
		if (PipelineResult.bSuccess)
		{
			BatchResult.SucceededAssets++;
		}
		else
		{
			BatchResult.FailedAssets++;
		}
	}

	UE_LOG(
		LogProceduralModelingToolkit,
		Log,
		TEXT("Batch processor finished. Total=%d Processed=%d Succeeded=%d Failed=%d Cancelled=%s"),
		BatchResult.TotalAssets,
		BatchResult.ProcessedAssets,
		BatchResult.SucceededAssets,
		BatchResult.FailedAssets,
		BatchResult.bCancelled ? TEXT("true") : TEXT("false")
	);

	return BatchResult;
}

void UProceduralModelingToolkitBatchProcessor::GatherMeshesFromFolders(const TArray<FString>& SourceFolders, bool bRecursiveFolders, const FString& NameContains, TArray<UStaticMesh*>& OutMeshes)
{
	if (SourceFolders.IsEmpty())
	{
		return;
	}

	FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");

	FARFilter Filter;
	Filter.bRecursivePaths = bRecursiveFolders;
	Filter.ClassPaths.Add(UStaticMesh::StaticClass()->GetClassPathName());

	for (const FString& SourceFolder : SourceFolders)
	{
		if (!SourceFolder.IsEmpty())
		{
			Filter.PackagePaths.Add(*SourceFolder);
		}
	}

	TArray<FAssetData> Assets;
	AssetRegistryModule.Get().GetAssets(Filter, Assets);
	for (const FAssetData& Asset : Assets)
	{
		AddMeshIfAccepted(Cast<UStaticMesh>(Asset.GetAsset()), NameContains, OutMeshes);
	}
}

void UProceduralModelingToolkitBatchProcessor::GatherMeshesFromCollections(const TArray<FString>& CollectionNames, const FString& NameContains, TArray<UStaticMesh*>& OutMeshes)
{
	if (CollectionNames.IsEmpty())
	{
		return;
	}

	ICollectionManager& CollectionManager = FCollectionManagerModule::GetModule().Get();
	const TSharedRef<ICollectionContainer>& CollectionContainer = CollectionManager.GetProjectCollectionContainer();
	const ECollectionShareType::Type ShareTypes[] = {
		ECollectionShareType::CST_Local,
		ECollectionShareType::CST_Private,
		ECollectionShareType::CST_Shared
	};

	for (const FString& CollectionNameString : CollectionNames)
	{
		if (CollectionNameString.IsEmpty())
		{
			continue;
		}

		const FName CollectionName(*CollectionNameString);
		for (const ECollectionShareType::Type ShareType : ShareTypes)
		{
			TArray<FSoftObjectPath> AssetPaths;
			if (!CollectionContainer->GetAssetsInCollection(CollectionName, ShareType, AssetPaths, ECollectionRecursionFlags::SelfAndChildren))
			{
				continue;
			}

			for (const FSoftObjectPath& AssetPath : AssetPaths)
			{
				AddMeshIfAccepted(Cast<UStaticMesh>(AssetPath.TryLoad()), NameContains, OutMeshes);
			}
		}
	}
}

void UProceduralModelingToolkitBatchProcessor::AddMeshIfAccepted(UStaticMesh* StaticMesh, const FString& NameContains, TArray<UStaticMesh*>& OutMeshes)
{
	if (!StaticMesh)
	{
		return;
	}

	if (!NameContains.IsEmpty() && !StaticMesh->GetName().Contains(NameContains, ESearchCase::IgnoreCase))
	{
		return;
	}

	OutMeshes.AddUnique(StaticMesh);
}
