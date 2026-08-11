#include "Actions/ProjectRefreshAssetsAction.h"
#include "MonolithParamSchema.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Misc/PackageName.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"

namespace
{
	// Resolve a /Game/... package path to its on-disk .uasset/.umap filename, if any.
	bool ResolveDiskFile(const FString& PackagePath, FString& OutFilename)
	{
		FString Filename;
		if (FPackageName::TryConvertLongPackageNameToFilename(PackagePath, Filename, FPackageName::GetAssetPackageExtension())
			&& IFileManager::Get().FileExists(*Filename))
		{
			OutFilename = Filename;
			return true;
		}
		if (FPackageName::TryConvertLongPackageNameToFilename(PackagePath, Filename, FPackageName::GetMapPackageExtension())
			&& IFileManager::Get().FileExists(*Filename))
		{
			OutFilename = Filename;
			return true;
		}
		return false;
	}
}

FMonolithActionResult FProjectRefreshAssetsAction::Execute(const TSharedPtr<FJsonObject>& Params)
{
	const TArray<TSharedPtr<FJsonValue>>* PathsArray = nullptr;
	if (!Params->TryGetArrayField(TEXT("asset_paths"), PathsArray) || !PathsArray || PathsArray->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("'asset_paths' array parameter is required (at least one /Game/... path)"), -32602);
	}

	const bool bWaitForRegistry = !Params->HasField(TEXT("wait_for_asset_registry")) || Params->GetBoolField(TEXT("wait_for_asset_registry"));
	const bool bWaitForDisk = Params->HasField(TEXT("wait_for_disk")) && Params->GetBoolField(TEXT("wait_for_disk"));

	IAssetRegistry& AR = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();

	// Split requested paths into directory scans vs individual package scans.
	TArray<FString> DirectoryPaths;
	TArray<FString> PackagePaths;
	for (const TSharedPtr<FJsonValue>& Value : *PathsArray)
	{
		FString Path;
		if (!Value.IsValid() || !Value->TryGetString(Path) || Path.IsEmpty())
		{
			continue;
		}
		Path.TrimStartAndEndInline();

		// A package path that resolves to a disk file is a single-package scan;
		// otherwise treat it as a directory (recursive) scan.
		if (FPackageName::IsValidLongPackageName(Path, /*bIncludeReadOnlyRoots=*/true))
		{
			FString DiskFile;
			if (ResolveDiskFile(Path, DiskFile))
			{
				PackagePaths.Add(Path);
			}
			else
			{
				DirectoryPaths.Add(Path);
			}
		}
		else
		{
			DirectoryPaths.Add(Path);
		}
	}

	if (DirectoryPaths.Num() == 0 && PackagePaths.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("No valid /Game/... paths were supplied in 'asset_paths'"), -32602);
	}

	// bForceRescan=true so a freshly-saved package is re-read rather than served stale.
	if (DirectoryPaths.Num() > 0)
	{
		AR.ScanPathsSynchronous(DirectoryPaths, /*bForceRescan=*/true);
	}
	if (PackagePaths.Num() > 0)
	{
		// Convert package paths to on-disk filenames for the file-level scan, and
		// also notify the registry of modified files so it re-reads cached tags.
		TArray<FString> Filenames;
		for (const FString& Pkg : PackagePaths)
		{
			FString DiskFile;
			if (ResolveDiskFile(Pkg, DiskFile))
			{
				Filenames.Add(DiskFile);
			}
		}
		if (Filenames.Num() > 0)
		{
			AR.ScanModifiedAssetFiles(Filenames);
			AR.ScanFilesSynchronous(Filenames, /*bForceRescan=*/true);
		}
	}

	if (bWaitForRegistry)
	{
		// Drain any queued background registry work so subsequent queries see fresh state.
		AR.WaitForCompletion();
	}

	// Optional bounded disk-presence poll: confirm each package's backing file exists with size > 0.
	TArray<TSharedPtr<FJsonValue>> ScannedJson;
	TArray<TSharedPtr<FJsonValue>> MissingOnDiskJson;
	if (bWaitForDisk)
	{
		const double DeadlineSeconds = FPlatformTime::Seconds() + 5.0; // hard upper bound to avoid game-thread stalls
		TArray<FString> Pending = PackagePaths;
		while (Pending.Num() > 0 && FPlatformTime::Seconds() < DeadlineSeconds)
		{
			for (int32 Index = Pending.Num() - 1; Index >= 0; --Index)
			{
				FString DiskFile;
				if (ResolveDiskFile(Pending[Index], DiskFile) && IFileManager::Get().FileSize(*DiskFile) > 0)
				{
					Pending.RemoveAt(Index);
				}
			}
			if (Pending.Num() > 0)
			{
				FPlatformProcess::Sleep(0.05f);
			}
		}
		for (const FString& Still : Pending)
		{
			MissingOnDiskJson.Add(MakeShared<FJsonValueString>(Still));
		}
	}

	for (const FString& Pkg : PackagePaths)
	{
		ScannedJson.Add(MakeShared<FJsonValueString>(Pkg));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetBoolField(TEXT("success"), true);
	Result->SetNumberField(TEXT("directories_scanned"), DirectoryPaths.Num());
	Result->SetNumberField(TEXT("packages_scanned"), PackagePaths.Num());

	TArray<TSharedPtr<FJsonValue>> DirJson;
	for (const FString& Dir : DirectoryPaths)
	{
		DirJson.Add(MakeShared<FJsonValueString>(Dir));
	}
	Result->SetArrayField(TEXT("scanned_directories"), DirJson);
	Result->SetArrayField(TEXT("scanned_packages"), ScannedJson);
	Result->SetBoolField(TEXT("waited_for_asset_registry"), bWaitForRegistry);
	Result->SetBoolField(TEXT("waited_for_disk"), bWaitForDisk);
	if (bWaitForDisk)
	{
		Result->SetArrayField(TEXT("missing_on_disk"), MissingOnDiskJson);
	}
	return FMonolithActionResult::Success(Result);
}

TSharedPtr<FJsonObject> FProjectRefreshAssetsAction::GetSchema()
{
	return FParamSchemaBuilder()
		.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of /Game/... package or directory paths to rescan (e.g. [\"/Game/Tests/Monolith/Foo\"])"))
		.Optional(TEXT("wait_for_asset_registry"), TEXT("boolean"), TEXT("Drain pending registry work after scanning so subsequent queries see fresh state (default true)"))
		.Optional(TEXT("wait_for_disk"), TEXT("boolean"), TEXT("Bounded poll until each package's backing file exists with size > 0 (default false)"))
		.Build();
}
