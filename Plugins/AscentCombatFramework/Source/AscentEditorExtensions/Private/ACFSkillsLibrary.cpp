// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFSkillsLibrary.h"

#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "GenericPlatform/GenericPlatformFile.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"

#include "Logging.h"

namespace {
	static const TCHAR* GACFPluginName = TEXT("AscentCombatFramework");
}

FString UACFSkillsLibrary::GetPluginSkillsSourceDir()
{
	const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(GACFPluginName);
	if (!Plugin.IsValid()) {
		return FString();
	}

	return FPaths::ConvertRelativePathToFull(
		FPaths::Combine(Plugin->GetBaseDir(), TEXT("Resources"), TEXT("Skills")));
}

FString UACFSkillsLibrary::GetProjectClaudeSkillsDir()
{
	return FPaths::ConvertRelativePathToFull(
		FPaths::Combine(FPaths::ProjectDir(), TEXT(".claude"), TEXT("skills")));
}

bool UACFSkillsLibrary::CopyPluginSkillsToClaude(int32& OutCopiedSkills, bool bOverwriteExisting)
{
	OutCopiedSkills = 0;

	const FString SourceDir = GetPluginSkillsSourceDir();
	if (SourceDir.IsEmpty()) {
		UE_LOG(ACFEditorExtensions, Error,
			TEXT("CopyPluginSkillsToClaude: plugin '%s' was not found, cannot resolve skills source folder."),
			GACFPluginName);
		return false;
	}

	const FString DestDir = GetProjectClaudeSkillsDir();

	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();

	if (!PlatformFile.DirectoryExists(*SourceDir)) {
		UE_LOG(ACFEditorExtensions, Error,
			TEXT("CopyPluginSkillsToClaude: source skills directory does not exist: %s"), *SourceDir);
		return false;
	}

	if (!PlatformFile.DirectoryExists(*DestDir) && !PlatformFile.CreateDirectoryTree(*DestDir)) {
		UE_LOG(ACFEditorExtensions, Error,
			TEXT("CopyPluginSkillsToClaude: failed to create destination directory: %s"), *DestDir);
		return false;
	}

	// Each top-level folder under Resources/Skills is treated as one skill, so we can copy them
	// individually, report a count, and keep going even if a single skill fails.
	TArray<FString> SkillFolders;
	IFileManager::Get().FindFiles(SkillFolders, *(SourceDir / TEXT("*")), /*Files*/ false, /*Directories*/ true);

	if (SkillFolders.Num() == 0) {
		UE_LOG(ACFEditorExtensions, Warning,
			TEXT("CopyPluginSkillsToClaude: no skill folders found under %s"), *SourceDir);
		return false;
	}

	bool bAllOk = true;
	for (const FString& SkillName : SkillFolders) {
		const FString SrcSkill = SourceDir / SkillName;
		const FString DstSkill = DestDir / SkillName;

		if (PlatformFile.CopyDirectoryTree(*DstSkill, *SrcSkill, bOverwriteExisting)) {
			++OutCopiedSkills;
			UE_LOG(ACFEditorExtensions, Log, TEXT("Copied skill '%s' -> %s"), *SkillName, *DstSkill);
		} else {
			bAllOk = false;
			UE_LOG(ACFEditorExtensions, Warning,
				TEXT("CopyPluginSkillsToClaude: failed to copy skill '%s' to %s"), *SkillName, *DstSkill);
		}
	}

	UE_LOG(ACFEditorExtensions, Log,
		TEXT("CopyPluginSkillsToClaude: copied %d/%d skill(s) from %s to %s"),
		OutCopiedSkills, SkillFolders.Num(), *SourceDir, *DestDir);

	return bAllOk && OutCopiedSkills > 0;
}
