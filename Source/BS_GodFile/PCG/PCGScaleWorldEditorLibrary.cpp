#include "PCGScaleWorldEditorLibrary.h"

#if WITH_EDITOR
#include "PCGAssetExporter.h"
#include "PCGLevelToAsset.h"
#include "UObject/Package.h"
#include "UObject/SoftObjectPath.h"
#include "UObject/UObjectGlobals.h"
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
