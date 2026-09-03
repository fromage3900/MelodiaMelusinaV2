#include "PCGScaleWorldEditorLibrary.h"

#if WITH_EDITOR
#include "PCGAssetExporter.h"
#include "PCGLevelToAsset.h"
#include "Editor.h"
#include "GeometryScript/MeshAssetFunctions.h"
#include "MeshPartition.h"
#include "MeshPartitionDefinition.h"
#include "MeshPartitionEditorComponent.h"
#include "UDynamicMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "FileHelpers.h"
#include "Materials/MaterialInterface.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/SoftObjectPath.h"
#endif

FString UPCGScaleWorldEditorLibrary::ExportLevelToPCGDataAsset(
	const FString& WorldAssetPath,
	const FString& DestinationPath,
	const FString& AssetName)
{
#if WITH_EDITOR
	if (WorldAssetPath.IsEmpty() || DestinationPath.IsEmpty() || AssetName.IsEmpty())
	{
		return TEXT("ERROR:WorldAssetPath, DestinationPath, and AssetName are required");
	}

	UWorld* World = Cast<UWorld>(StaticLoadObject(UWorld::StaticClass(), nullptr, *WorldAssetPath));
	if (!World)
	{
		return FString::Printf(TEXT("ERROR:Unable to load world '%s'"), *WorldAssetPath);
	}

	FPCGAssetExporterParameters Parameters;
	Parameters.bOpenSaveDialog = false;
	Parameters.bSaveOnExportEnded = true;
	Parameters.AssetPath = DestinationPath;
	Parameters.AssetName = AssetName;

	UPackage* Package = UPCGLevelToAsset::CreateOrUpdatePCGAsset(World, Parameters);
	if (!Package)
	{
		return FString::Printf(TEXT("ERROR:PCG Level-to-Asset export failed for '%s'"), *WorldAssetPath);
	}

	return Package->GetName();
#else
	return TEXT("ERROR:PCG Level-to-Asset export requires an editor build");
#endif
}

FString UPCGScaleWorldEditorLibrary::CreateMeshPartitionTerrain(
	const FString& WorldAssetPath,
	const FString& MeshAssetPath,
	const FString& MaterialAssetPath,
	const FString& ActorLabel)
{
#if WITH_EDITOR
	if (WorldAssetPath.IsEmpty() || MeshAssetPath.IsEmpty() || MaterialAssetPath.IsEmpty() || ActorLabel.IsEmpty())
	{
		return TEXT("ERROR:WorldAssetPath, MeshAssetPath, MaterialAssetPath, and ActorLabel are required");
	}

	if (GEditor == nullptr)
	{
		return TEXT("ERROR:Editor is unavailable");
	}

	UWorld* World = GEditor->GetEditorWorldContext().World();
	if (World == nullptr)
	{
		return TEXT("ERROR:No editor world is loaded");
	}

	if (World->GetPackage() == nullptr || World->GetPackage()->GetName() != WorldAssetPath)
	{
		return FString::Printf(TEXT("ERROR:Loaded editor world is '%s', expected '%s'"),
			World->GetPackage() ? *World->GetPackage()->GetName() : TEXT("<none>"), *WorldAssetPath);
	}

	if (World->GetWorldPartition() == nullptr)
	{
		return TEXT("ERROR:MeshPartition terrain requires a World Partition map");
	}

	UStaticMesh* SourceMesh = LoadObject<UStaticMesh>(nullptr, *MeshAssetPath);
	UMaterialInterface* TerrainMaterial = LoadObject<UMaterialInterface>(nullptr, *MaterialAssetPath);
	if (SourceMesh == nullptr || TerrainMaterial == nullptr)
	{
		return FString::Printf(TEXT("ERROR:Unable to load mesh '%s' or material '%s'"), *MeshAssetPath, *MaterialAssetPath);
	}

	using namespace UE::MeshPartition;
	AMeshPartition* MeshPartition = nullptr;
	for (TActorIterator<AMeshPartition> It(World); It; ++It)
	{
		if (It->GetActorLabel() == ActorLabel)
		{
			MeshPartition = *It;
			break;
		}
	}

	if (MeshPartition == nullptr)
	{
		FActorSpawnParameters SpawnParams;
		SpawnParams.Name = MakeUniqueObjectName(World->PersistentLevel, AMeshPartition::StaticClass(), FName(TEXT("MeshTerrain_SakuraTerrace")));
		MeshPartition = World->SpawnActor<AMeshPartition>(AMeshPartition::StaticClass(), FTransform::Identity, SpawnParams);
	}

	if (MeshPartition == nullptr)
	{
		return TEXT("ERROR:Failed to spawn MeshPartition actor");
	}

	MeshPartition->SetActorLabel(ActorLabel, false);
	MeshPartition->SetFolderPath(FName(TEXT("_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace")));

	UMeshPartitionEditorComponent* EditorComponent = Cast<UMeshPartitionEditorComponent>(MeshPartition->GetMeshPartitionComponent());
	if (EditorComponent == nullptr)
	{
		EditorComponent = NewObject<UMeshPartitionEditorComponent>(MeshPartition, UMeshPartitionEditorComponent::StaticClass(), TEXT("MegaMeshEditorComponent"), RF_Transactional);
		MeshPartition->SetMeshPartitionComponent(EditorComponent);
	}

	UMeshPartitionDefinition* Definition = LoadObject<UMeshPartitionDefinition>(nullptr, TEXT("/MeshPartition/DataAssets/MPD_Default.MPD_Default"));
	if (Definition != nullptr)
	{
		MeshPartition->SetMeshPartitionDefinition(Definition);
	}

	EditorComponent->SetForceSynchronousPreviewSectionBuild(true);
	EditorComponent->SetBaseModifiersHidden(true);
	EditorComponent->SetPreviewSectionsVisibility(true);

	// The material is a reflected private property in the UE plugin. Setting it
	// here makes the isolated preview use the same Substrate MI as the source
	// terrain while retaining the plugin's normal definition/channel pipeline.
	if (FObjectProperty* OverrideProperty = FindFProperty<FObjectProperty>(EditorComponent->GetClass(), TEXT("EditorMaterialOverride")))
	{
		OverrideProperty->SetObjectPropertyValue_InContainer(EditorComponent, TerrainMaterial);
	}

	UDynamicMesh* DynamicMesh = NewObject<UDynamicMesh>(GetTransientPackage(), NAME_None, RF_Transient);
	FGeometryScriptCopyMeshFromAssetOptions CopyOptions;
	FGeometryScriptMeshReadLOD ReadLOD;
	EGeometryScriptOutcomePins Outcome = EGeometryScriptOutcomePins::Failure;
	UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshFromStaticMesh(
		SourceMesh, DynamicMesh, CopyOptions, ReadLOD, Outcome, nullptr);

	if (Outcome != EGeometryScriptOutcomePins::Success || DynamicMesh == nullptr || DynamicMesh->IsEmpty())
	{
		return FString::Printf(TEXT("ERROR:StaticMesh to DynamicMesh conversion failed for '%s'"), *MeshAssetPath);
	}

	const int32 TriangleCount = DynamicMesh->GetTriangleCount();
	TUniquePtr<UE::Geometry::FDynamicMesh3> ExtractedMesh = DynamicMesh->ExtractMesh();
	if (!ExtractedMesh.IsValid())
	{
		return TEXT("ERROR:DynamicMesh extraction failed");
	}

	TArray<UMaterialInterface*> Materials;
	Materials.Add(TerrainMaterial);
	AActor* BaseModifier = EditorComponent->SpawnBaseModifier(MoveTemp(*ExtractedMesh), Materials, FTransform::Identity);
	if (BaseModifier == nullptr)
	{
		return TEXT("ERROR:MeshPartition base modifier creation failed");
	}

	EditorComponent->OnModifierAssigned();
	const FBox TerrainBounds = BaseModifier->GetComponentsBoundingBox(true, false);
	if (!TerrainBounds.IsValid)
	{
		return TEXT("ERROR:MeshPartition terrain bounds are invalid");
	}

	EditorComponent->OnBoundsChanged({TerrainBounds}, EChangeType::StateChange);
	EditorComponent->Update();
	EditorComponent->UpdateMaterial();
	EditorComponent->Update();

	World->MarkPackageDirty();
	if (GEditor->GetEditorWorldContext().World() == World)
	{
		FEditorFileUtils::SaveMap(World, World->GetPackage()->GetName());
	}

	return FString::Printf(TEXT("OK:MeshPartitionTerrain actor=%s base=%s triangles=%d bounds=%s material=%s"),
		*MeshPartition->GetName(), *BaseModifier->GetName(), TriangleCount, *TerrainBounds.ToString(), *MaterialAssetPath);
#else
	return TEXT("ERROR:MeshPartition terrain creation requires an editor build");
#endif
}
