#include "Actions/ProjectCleanupGeneratedAssetsAction.h"
#include "MonolithParamSchema.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "EditorAssetLibrary.h"

namespace
{
	// HARD GUARD: nothing outside this prefix may ever be deleted by this action.
	// Production content lives elsewhere; cleanup is scoped to disposable test assets only.
	const TCHAR* GTestsAllowlistPrefix = TEXT("/Game/Tests/Monolith/");

	bool IsUnderAllowlist(const FString& Path)
	{
		return Path.StartsWith(GTestsAllowlistPrefix);
	}

	// Reduce a package path to its containing folder (strip trailing /AssetName).
	FString FolderOfPackage(const FString& PackagePath)
	{
		int32 SlashIndex = INDEX_NONE;
		if (PackagePath.FindLastChar(TEXT('/'), SlashIndex) && SlashIndex > 0)
		{
			return PackagePath.Left(SlashIndex);
		}
		return PackagePath;
	}
}

FMonolithActionResult FProjectCleanupGeneratedAssetsAction::Execute(const TSharedPtr<FJsonObject>& Params)
{
	const TArray<TSharedPtr<FJsonValue>>* PathsArray = nullptr;
	if (!Params->TryGetArrayField(TEXT("paths"), PathsArray) || !PathsArray || PathsArray->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("'paths' array parameter is required (at least one /Game/Tests/Monolith/... path)"), -32602);
	}

	// dry_run defaults TRUE -- destructive deletion is strictly opt-in.
	const bool bDryRun = !Params->HasField(TEXT("dry_run")) || Params->GetBoolField(TEXT("dry_run"));
	const bool bRequireNoReferencers = !Params->HasField(TEXT("require_no_referencers")) || Params->GetBoolField(TEXT("require_no_referencers"));
	const bool bRemoveEmptyFolders = Params->HasField(TEXT("remove_empty_folders")) && Params->GetBoolField(TEXT("remove_empty_folders"));

	// Normalise + validate the request set first; refuse the whole call if anything
	// targets outside the allowlist, so a single bad path cannot half-delete.
	TArray<FString> RequestedPaths;
	TSet<FString> RequestSet;
	for (const TSharedPtr<FJsonValue>& Value : *PathsArray)
	{
		FString Path;
		if (!Value.IsValid() || !Value->TryGetString(Path) || Path.IsEmpty())
		{
			continue;
		}
		Path.TrimStartAndEndInline();
		if (!IsUnderAllowlist(Path))
		{
			return FMonolithActionResult::Error(
				FString::Printf(TEXT("Refused: '%s' is outside the deletion allowlist '%s'. cleanup_generated_assets only removes disposable test assets."),
					*Path, GTestsAllowlistPrefix), -32602);
		}
		RequestedPaths.AddUnique(Path);
		RequestSet.Add(Path);
	}

	if (RequestedPaths.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("No valid paths supplied in 'paths'"), -32602);
	}

	IAssetRegistry& AR = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();

	TArray<TSharedPtr<FJsonValue>> DeletedJson;
	TArray<TSharedPtr<FJsonValue>> SkippedJson;
	TSet<FString> CandidateFolders;

	for (const FString& PackagePath : RequestedPaths)
	{
		CandidateFolders.Add(FolderOfPackage(PackagePath));

		// External referencers = referencers not themselves part of this request set.
		TArray<FName> Referencers;
		AR.GetReferencers(FName(*PackagePath), Referencers, UE::AssetRegistry::EDependencyCategory::Package);

		TArray<FString> ExternalReferencers;
		for (const FName& Ref : Referencers)
		{
			const FString RefStr = Ref.ToString();
			if (!RequestSet.Contains(RefStr))
			{
				ExternalReferencers.Add(RefStr);
			}
		}

		if (bRequireNoReferencers && ExternalReferencers.Num() > 0)
		{
			auto SkipEntry = MakeShared<FJsonObject>();
			SkipEntry->SetStringField(TEXT("path"), PackagePath);
			TArray<TSharedPtr<FJsonValue>> RefJson;
			for (const FString& Ref : ExternalReferencers)
			{
				RefJson.Add(MakeShared<FJsonValueString>(Ref));
			}
			SkipEntry->SetArrayField(TEXT("referencers"), RefJson);
			SkippedJson.Add(MakeShared<FJsonValueObject>(SkipEntry));
			continue;
		}

		if (!UEditorAssetLibrary::DoesAssetExist(PackagePath))
		{
			// Already gone -- report as deleted (idempotent) without touching disk.
			auto Entry = MakeShared<FJsonObject>();
			Entry->SetStringField(TEXT("path"), PackagePath);
			Entry->SetBoolField(TEXT("already_absent"), true);
			DeletedJson.Add(MakeShared<FJsonValueObject>(Entry));
			continue;
		}

		bool bDeleted = false;
		if (!bDryRun)
		{
			bDeleted = UEditorAssetLibrary::DeleteAsset(PackagePath);
		}

		auto Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("path"), PackagePath);
		Entry->SetBoolField(TEXT("deleted"), bDeleted);
		Entry->SetBoolField(TEXT("dry_run"), bDryRun);
		DeletedJson.Add(MakeShared<FJsonValueObject>(Entry));
	}

	// Empty-folder removal: only folders under the allowlist that now hold no assets.
	TArray<TSharedPtr<FJsonValue>> FoldersRemovedJson;
	if (bRemoveEmptyFolders)
	{
		for (const FString& Folder : CandidateFolders)
		{
			if (!IsUnderAllowlist(Folder + TEXT("/")) && !IsUnderAllowlist(Folder))
			{
				continue;
			}
			if (UEditorAssetLibrary::DoesDirectoryExist(Folder)
				&& !UEditorAssetLibrary::DoesDirectoryHaveAssets(Folder, /*bRecursive=*/true))
			{
				bool bRemoved = false;
				if (!bDryRun)
				{
					bRemoved = UEditorAssetLibrary::DeleteDirectory(Folder);
				}
				auto Entry = MakeShared<FJsonObject>();
				Entry->SetStringField(TEXT("path"), Folder);
				Entry->SetBoolField(TEXT("removed"), bRemoved);
				Entry->SetBoolField(TEXT("dry_run"), bDryRun);
				FoldersRemovedJson.Add(MakeShared<FJsonValueObject>(Entry));
			}
		}
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetBoolField(TEXT("success"), true);
	Result->SetBoolField(TEXT("dry_run"), bDryRun);
	Result->SetArrayField(TEXT("deleted"), DeletedJson);
	Result->SetArrayField(TEXT("skipped_with_referencers"), SkippedJson);
	Result->SetArrayField(TEXT("folders_removed"), FoldersRemovedJson);
	return FMonolithActionResult::Success(Result);
}

TSharedPtr<FJsonObject> FProjectCleanupGeneratedAssetsAction::GetSchema()
{
	return FParamSchemaBuilder()
		.Required(TEXT("paths"), TEXT("array"), TEXT("Array of /Game/Tests/Monolith/... asset package paths to delete (allowlist-enforced)"))
		.Optional(TEXT("dry_run"), TEXT("boolean"), TEXT("Report what would be deleted without touching disk (default true)"))
		.Optional(TEXT("require_no_referencers"), TEXT("boolean"), TEXT("Skip any asset still referenced by something outside the request set (default true)"))
		.Optional(TEXT("remove_empty_folders"), TEXT("boolean"), TEXT("After deletes, remove now-empty folders under the allowlist (default false)"))
		.Build();
}
