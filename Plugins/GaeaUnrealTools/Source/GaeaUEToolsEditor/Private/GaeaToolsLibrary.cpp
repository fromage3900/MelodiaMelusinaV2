#include "GaeaToolsLibrary.h"

#include "GaeaSubsystem.h"
#include "ImporterPanelSettings.h"
#include "Landscape.h"
#include "LandscapeEditorObject.h"
#include "LandscapeImportHelper.h"
#include "LandscapeSubsystem.h"
#include "Engine/World.h"
#include "Editor.h"
#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "EditorAssetLibrary.h"
#include "Subsystems/EditorActorSubsystem.h"
#include "GaeaLandscapeComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogGaeaTools, Log, All);

FVector UGaeaToolsLibrary::GetGaeaLandscapeScale(float ScaleX, float ScaleY, float Height, int32 Resolution)
{
	if (Resolution <= 0)
	{
		return FVector::OneVector;
	}
	return FVector(ScaleX * 100.0f / Resolution, ScaleY * 100.0f / Resolution, Height * 100.0f / 512.0f);
}

float UGaeaToolsLibrary::GetGaeaLandscapeLocationZ(float Height)
{
	return Height * 100.0f / 2.0f;
}

ALandscape* UGaeaToolsLibrary::CreateLandscapeFromGaeaFiles(
	const FString& HeightmapFile,
	const FString& DefinitionFile,
	const TArray<FString>& WeightmapFiles,
	const TArray<FName>& LayerNames,
	const FString& LayerInfoFolderPath,
	UMaterialInterface* LandscapeMaterial,
	FVector Location,
	bool bFlipYAxis,
	bool bWorldPartition)
{
	// ---- definition.json (world scale is derived from it, never guessed) ----
	bool bStatus = false;
	FString JsonMessage;
	const FGaeaJson GaeaDefinition = UGaeaSubsystem::StaticClass()->GetDefaultObject<UGaeaSubsystem>()->CreateStructFromJson(DefinitionFile, bStatus, JsonMessage);
	if (!bStatus)
	{
		UE_LOG(LogGaeaTools, Error, TEXT("CreateLandscapeFromGaeaFiles: definition.json failed: %s"), *JsonMessage);
		return nullptr;
	}
	UE_LOG(LogGaeaTools, Display, TEXT("ScaleX: %f, ScaleY: %f, Height: %f, Resolution: %d"),
		GaeaDefinition.ScaleX, GaeaDefinition.ScaleY, GaeaDefinition.Height, GaeaDefinition.Resolution);

	const FVector LandscapeScale = FVector(
		GaeaDefinition.ScaleX * 100.0f / GaeaDefinition.Resolution,
		GaeaDefinition.ScaleY * 100.0f / GaeaDefinition.Resolution,
		GaeaDefinition.Height * 100.0f / 512.0f);

	// ---- settings object (same contract as the importer panel) ----
	// WeightmapFiles are FULL paths to the staged W_*.png files.
	UImporterPanelSettings* Settings = NewObject<UImporterPanelSettings>();
	Settings->HeightMapFileName = HeightmapFile;
	Settings->jsonFileName = DefinitionFile;
	Settings->StoredPath = LayerInfoFolderPath;
	Settings->WeightmapFileNames.Reset();
	for (const FString& W : WeightmapFiles)
	{
		Settings->WeightmapFileNames.Add(FPaths::GetCleanFilename(W));
	}
	Settings->WeightmapFilePaths = WeightmapFiles;
	Settings->LandscapeMaterialLayerNames = LayerNames;
	Settings->LayerInfoFolder.Path = LayerInfoFolderPath;
	Settings->LandscapeMaterial = LandscapeMaterial;
	Settings->Scale = LandscapeScale;
	Settings->Location = Location;
	Settings->Rotation = FRotator::ZeroRotator;
	Settings->FlipYAxis = bFlipYAxis;
	Settings->bIsWorldPartition = bWorldPartition;

	// ---- heightmap data ----
	constexpr bool bSingleFile = true;
	FLandscapeImportDescriptor OutImportDescriptor;
	OutImportDescriptor.Scale = LandscapeScale;
	FText OutMessage;

	const ELandscapeImportResult ImportResult =
		FLandscapeImportHelper::GetHeightmapImportDescriptor(Settings->HeightMapFileName, bSingleFile, Settings->FlipYAxis, OutImportDescriptor, OutMessage);

	// Guard: empty ImportResolutions asserted the editor twice on 2026-09-01 (GaeaSubsystem.cpp:813 family).
	if (ImportResult != ELandscapeImportResult::Success || OutImportDescriptor.ImportResolutions.Num() == 0)
	{
		UE_LOG(LogGaeaTools, Error, TEXT("CreateLandscapeFromGaeaFiles: heightmap import failed (%s): %s"),
			*Settings->HeightMapFileName, *OutMessage.ToString());
		return nullptr;
	}

	const int32 DescriptorIndex = OutImportDescriptor.ImportResolutions.Num() / 2;

	ULandscapeEditorObject* DefaultValueObject = ULandscapeEditorObject::StaticClass()->GetDefaultObject<ULandscapeEditorObject>();
	check(DefaultValueObject);

	int32 OutQuadsPerSection = DefaultValueObject->NewLandscape_QuadsPerSection;
	int32 OutSectionsPerComponent = DefaultValueObject->NewLandscape_SectionsPerComponent;
	FIntPoint OutComponentCount = DefaultValueObject->NewLandscape_ComponentCount;

	FLandscapeImportHelper::ChooseBestComponentSizeForImport(
		OutImportDescriptor.ImportResolutions[DescriptorIndex].Width,
		OutImportDescriptor.ImportResolutions[DescriptorIndex].Height,
		OutQuadsPerSection, OutSectionsPerComponent, OutComponentCount);

	TArray<uint16> ImportData;
	FLandscapeImportHelper::GetHeightmapImportData(OutImportDescriptor, DescriptorIndex, ImportData, OutMessage);

	const int32 QuadsPerComponent = OutSectionsPerComponent * OutQuadsPerSection;
	const int32 SizeX = OutComponentCount.X * QuadsPerComponent + 1;
	const int32 SizeY = OutComponentCount.Y * QuadsPerComponent + 1;

	TArray<uint16> FinalHeightData;
	FLandscapeImportHelper::TransformHeightmapImportData(ImportData, FinalHeightData,
		OutImportDescriptor.ImportResolutions[DescriptorIndex],
		FLandscapeImportResolution(SizeX, SizeY), ELandscapeImportTransformType::ExpandCentered);

	// ---- weightmaps ----
	bool bImportWeightmaps = false;
	const FString PackagePath = Settings->LayerInfoFolder.Path;
	const bool PathExists = !PackagePath.IsEmpty() && UEditorAssetLibrary::DoesDirectoryExist(PackagePath);
	if (!Settings->LandscapeMaterialLayerNames.IsEmpty() && PathExists
		&& Settings->LandscapeMaterialLayerNames.Num() >= 2
		&& Settings->WeightmapFileNames.Num() == Settings->LandscapeMaterialLayerNames.Num() - 1)
	{
		bImportWeightmaps = true;
	}

	TArray<FLandscapeImportLayerInfo> MaterialImportLayers;
	TArray<ULandscapeLayerInfoObject*> LayerInfoObjects;

	if (bImportWeightmaps)
	{
		FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
		for (int32 i = 0; i < Settings->LandscapeMaterialLayerNames.Num(); i++)
		{
			FString Name = Settings->LandscapeMaterialLayerNames[i].ToString();
			Name = Name.Replace(TEXT(" "), TEXT(""));
			FString NewAssetName;
			FString DummyPackageName;
			AssetToolsModule.Get().CreateUniqueAssetName(PackagePath / Name, TEXT(""), DummyPackageName, NewAssetName);
			UObject* CreatedAsset = AssetToolsModule.Get().CreateAsset(NewAssetName, PackagePath, ULandscapeLayerInfoObject::StaticClass(), nullptr);
			ULandscapeLayerInfoObject* LayerInfoObj = Cast<ULandscapeLayerInfoObject>(CreatedAsset);
			if (LayerInfoObj)
			{
				LayerInfoObj->SetLayerName(Settings->LandscapeMaterialLayerNames[i], true);
				LayerInfoObj->SetBlendMethod(ELandscapeTargetLayerBlendMethod::PremultipliedAlphaBlending, true);
			}
			LayerInfoObjects.Add(LayerInfoObj);
		}

		for (int32 i = 0; i < Settings->LandscapeMaterialLayerNames.Num(); i++)
		{
			FLandscapeImportLayerInfo LayerInfo;
			LayerInfo.LayerName = Settings->LandscapeMaterialLayerNames[i];
			MaterialImportLayers.Add(LayerInfo);
		}

		MaterialImportLayers[0].LayerData = TArray<uint8>();
		MaterialImportLayers[0].SourceFilePath = "";
		MaterialImportLayers[0].LayerInfo = LayerInfoObjects[0];
		const int32 DataSize = SizeX * SizeY;
		MaterialImportLayers[0].LayerData.AddUninitialized(DataSize);
		FMemory::Memset(MaterialImportLayers[0].LayerData.GetData(), 255, DataSize);

		TArray<FLandscapeImportDescriptor> WeightOutImportDescriptors;
		TArray<FText> WeightOutMessage;
		WeightOutImportDescriptors.AddDefaulted(Settings->LandscapeMaterialLayerNames.Num());
		WeightOutMessage.AddDefaulted(Settings->LandscapeMaterialLayerNames.Num());

		for (int32 i = 1; i < Settings->LandscapeMaterialLayerNames.Num(); i++)
		{
			const int32 WeightmapIndex = i - 1;
			if (WeightmapIndex < Settings->WeightmapFilePaths.Num())
			{
				FLandscapeImportHelper::GetWeightmapImportDescriptor(Settings->WeightmapFilePaths[WeightmapIndex], bSingleFile, Settings->FlipYAxis,
					Settings->LandscapeMaterialLayerNames[i], WeightOutImportDescriptors[i], WeightOutMessage[i]);

				TArray<uint8> WeightOutData;
				FLandscapeImportHelper::GetWeightmapImportData(WeightOutImportDescriptors[i], DescriptorIndex, Settings->LandscapeMaterialLayerNames[i], WeightOutData, WeightOutMessage[i]);

				TArray<uint8> FinalWeightOutData;
				FLandscapeImportHelper::TransformWeightmapImportData(WeightOutData, FinalWeightOutData,
					OutImportDescriptor.ImportResolutions[DescriptorIndex],
					FLandscapeImportResolution(SizeX, SizeY), ELandscapeImportTransformType::ExpandCentered);

				MaterialImportLayers[i].LayerName = Settings->LandscapeMaterialLayerNames[i];
				MaterialImportLayers[i].LayerInfo = LayerInfoObjects[i];
				MaterialImportLayers[i].LayerData = MoveTemp(FinalWeightOutData);
			}
		}
	}

	// ---- spawn + import (same core call as the plugin) ----
	UWorld* World = nullptr;
	{
		FWorldContext& EditorWorldContext = GEditor->GetEditorWorldContext();
		World = EditorWorldContext.World();
	}

	const FVector Offset = FTransform(Settings->Rotation, FVector::ZeroVector, Settings->Scale)
		.TransformVector(FVector(-OutComponentCount.X * QuadsPerComponent / 2.0, -OutComponentCount.Y * QuadsPerComponent / 2.0, 0.0));

	ALandscape* Landscape = World->SpawnActor<ALandscape>(Settings->Location + Offset, Settings->Rotation);
	if (!Landscape)
	{
		UE_LOG(LogGaeaTools, Error, TEXT("CreateLandscapeFromGaeaFiles: failed to spawn ALandscape"));
		return nullptr;
	}
	Landscape->LandscapeMaterial = Settings->LandscapeMaterial;
	Landscape->SetActorRelativeScale3D(Settings->Scale);

	UGaeaLandscapeComponent* GaeaComponent = NewObject<UGaeaLandscapeComponent>(Landscape, UGaeaLandscapeComponent::StaticClass(), TEXT("Gaea Landscape Component"));
	if (GaeaComponent)
	{
		GaeaComponent->RegisterComponent();
		Landscape->AddInstanceComponent(GaeaComponent);
		Landscape->AddOwnedComponent(GaeaComponent);
		GaeaComponent->HeightmapFilepath.FilePath = Settings->HeightMapFileName;
		GaeaComponent->DefinitionFilepath.FilePath = Settings->jsonFileName;
		GaeaComponent->WeightmapFilepaths.SetNum(Settings->WeightmapFilePaths.Num());
		for (int32 i = 0; i < Settings->WeightmapFilePaths.Num(); i++)
		{
			GaeaComponent->WeightmapFilepaths[i].FilePath = Settings->WeightmapFilePaths[i];
		}
	}

	TMap<FGuid, TArray<uint16>> HeightmapDataPerLayers;
	HeightmapDataPerLayers.Add(FGuid(), MoveTemp(FinalHeightData));
	TMap<FGuid, TArray<FLandscapeImportLayerInfo>> MaterialLayerDataPerLayers;
	if (!bImportWeightmaps)
	{
		MaterialLayerDataPerLayers.Add(FGuid(), TArray<FLandscapeImportLayerInfo>());
	}
	else
	{
		MaterialLayerDataPerLayers.Add(FGuid(), MaterialImportLayers);
	}

	Landscape->Import(FGuid::NewGuid(), 0, 0, SizeX - 1, SizeY - 1, OutSectionsPerComponent, OutQuadsPerSection,
		HeightmapDataPerLayers, *Settings->HeightMapFileName, MaterialLayerDataPerLayers,
		ELandscapeImportAlphamapType::Additive, TArrayView<const FLandscapeLayer>());

	Landscape->StaticLightingLOD = FMath::DivideAndRoundUp(FMath::CeilLogTwo((SizeX * SizeY) / (2048 * 2048) + 1), (uint32)2);

	ULandscapeInfo* LandscapeInfo = Landscape->GetLandscapeInfo();
	if (LandscapeInfo)
	{
		LandscapeInfo->UpdateLayerInfoMap(Landscape);
	}
	Landscape->RegisterAllComponents();

	if (bImportWeightmaps)
	{
		for (int32 i = 0; i < Settings->LandscapeMaterialLayerNames.Num(); i++)
		{
			if (MaterialImportLayers[i].LayerInfo != nullptr)
			{
				Landscape->AddTargetLayer(MaterialImportLayers[i].LayerName,
					FLandscapeTargetLayerSettings(MaterialImportLayers[i].LayerInfo, MaterialImportLayers[i].SourceFilePath));
			}
		}
	}

	UE_LOG(LogGaeaTools, Display, TEXT("CreateLandscapeFromGaeaFiles: landscape created (%d x %d components grid %d x %d)"),
		OutComponentCount.X, OutComponentCount.Y, QuadsPerComponent, QuadsPerComponent);
	return Landscape;
}
