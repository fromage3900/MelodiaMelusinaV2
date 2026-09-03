#include "Indexers/ConfigIndexer.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"

bool FConfigIndexer::IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId)
{
	// Collect .ini files from the project Config directory
	TArray<FString> IniFiles;
	FString ProjectConfigDir = FPaths::ProjectConfigDir();
	IFileManager::Get().FindFilesRecursive(IniFiles, *ProjectConfigDir, TEXT("*.ini"), true, false);

	// Also include Engine config directory
	FString EngineConfigDir = FPaths::EngineConfigDir();
	IFileManager::Get().FindFilesRecursive(IniFiles, *EngineConfigDir, TEXT("*.ini"), true, false);

	int32 TotalEntries = 0;

	for (const FString& IniFile : IniFiles)
	{
		TotalEntries += ParseAndInsertIniFile(IniFile, DB);
	}

	UE_LOG(LogMonolithIndex, Log, TEXT("ConfigIndexer: indexed %d entries from %d .ini files"), TotalEntries, IniFiles.Num());
	return true;
}

FString FConfigIndexer::ClassifyLayer(const FString& FilePath)
{
	FString Filename = FPaths::GetCleanFilename(FilePath);

	if (FilePath.Contains(TEXT("/Saved/")) || FilePath.Contains(TEXT("\\Saved\\")))
	{
		return TEXT("User");
	}
	if (FilePath.Contains(TEXT("/Platform/")) || FilePath.Contains(TEXT("\\Platform\\")))
	{
		return TEXT("Platform");
	}
	if (Filename.StartsWith(TEXT("Base")))
	{
		return TEXT("Base");
	}
	if (Filename.StartsWith(TEXT("Default")))
	{
		return TEXT("Default");
	}
	// Engine configs that don't match other patterns
	if (FilePath.Contains(TEXT("/Engine/")) || FilePath.Contains(TEXT("\\Engine\\")))
	{
		return TEXT("Base");
	}

	return TEXT("Default");
}

int32 FConfigIndexer::ParseAndInsertIniFile(const FString& FilePath, FMonolithIndexDatabase& DB)
{
	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *FilePath))
	{
		return 0;
	}

	// Make the path relative to the project root for cleaner storage
	FString RelativePath = FilePath;
	FPaths::MakePathRelativeTo(RelativePath, *FPaths::ProjectDir());

	FString CurrentSection;
	int32 Inserted = 0;

	for (const FString& RawLine : Lines)
	{
		FString Line = RawLine.TrimStartAndEnd();

		// Skip empty lines and comments
		if (Line.IsEmpty() || Line.StartsWith(TEXT(";")) || Line.StartsWith(TEXT("#")))
		{
			continue;
		}

		// Section header: [SectionName]
		if (Line.StartsWith(TEXT("[")) && Line.EndsWith(TEXT("]")))
		{
			CurrentSection = Line.Mid(1, Line.Len() - 2);
			continue;
		}

		// Key=Value pair (handle +Key, -Key, .Key, !Key prefixes used by UE config system)
		FString Key;
		FString Value;
		int32 EqualsIdx;
		if (Line.FindChar(TEXT('='), EqualsIdx))
		{
			Key = Line.Left(EqualsIdx).TrimStartAndEnd();
			Value = Line.Mid(EqualsIdx + 1).TrimStartAndEnd();

			if (!Key.IsEmpty() && !CurrentSection.IsEmpty())
			{
				FIndexedConfig Entry;
				Entry.FilePath = RelativePath;
				Entry.Section = CurrentSection;
				Entry.Key = Key;
				Entry.Value = Value;
				DB.InsertConfig(Entry);
				Inserted++;
			}
		}
	}

	return Inserted;
}
