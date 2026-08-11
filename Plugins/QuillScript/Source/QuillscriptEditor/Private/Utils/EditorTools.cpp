// Copyright Bruno Caxito. All Rights Reserved.

#include "Utils/EditorTools.h"

#include "DesktopPlatformModule.h"
#include "EditorUtilityWidgetBlueprint.h"
#include "IBlutilityModule.h"
#include "LevelEditor.h"
#include "Misc/FileHelper.h"
#include "Utils/Tools.h"


#pragma region Widgets

void UEditorTools::SpawnTab(const FText TabTitle, const FString& WidgetPath)
{
	SpawnTab(TabTitle, WidgetPath, FSlateIcon());
}

void UEditorTools::SpawnTab(const FText& TabTitle, const FString& WidgetPath, const FSlateIcon& TabIcon)
{
	if (const TObjectPtr<UWidgetBlueprint> Blueprint{ LoadObject<UWidgetBlueprint>(nullptr, *WidgetPath) })
	{
		if (Blueprint->GeneratedClass->IsChildOf(UEditorUtilityWidget::StaticClass())) {
			if (const TObjectPtr<UEditorUtilityWidget> CDO = Cast<UEditorUtilityWidget>(Blueprint->GeneratedClass->GetDefaultObject()); CDO->ShouldAutoRunDefaultAction())
			{
				// This is an instant-run blueprint, execute it.
				const TObjectPtr<UEditorUtilityWidget> Instance{ NewObject<UEditorUtilityWidget>(GetTransientPackage(), Blueprint->GeneratedClass) };
				Instance->ExecuteDefaultAction();
			}
			else
			{
				// Register and spawn tab.
				const FName RegistrationName{ FName(*(Blueprint->GetPathName() + "_ActiveTab")) };
				const TSharedPtr LevelEditorTabManager{ FModuleManager::GetModuleChecked<FLevelEditorModule>("LevelEditor").GetLevelEditorTabManager() };

				// Register tab.
				if (!LevelEditorTabManager->HasTabSpawner(RegistrationName))
				{
					IBlutilityModule* BlutilityModule{ FModuleManager::GetModulePtr<IBlutilityModule>("Blutility") };
					const TObjectPtr<UEditorUtilityWidgetBlueprint> WidgetBlueprint{ Cast<UEditorUtilityWidgetBlueprint>(Blueprint) };
					WidgetBlueprint->SetRegistrationName(RegistrationName);

					LevelEditorTabManager->RegisterTabSpawner(RegistrationName, FOnSpawnTab::CreateUObject(WidgetBlueprint, &UEditorUtilityWidgetBlueprint::SpawnEditorUITab))
						.SetDisplayName(TabTitle)
						.SetGroup(BlutilityModule->GetMenuGroup().ToSharedRef())
						.SetIcon(TabIcon);

					BlutilityModule->AddLoadedScriptUI(WidgetBlueprint);
				}

				// Spawn tab.
				auto NewDockTab{ LevelEditorTabManager->TryInvokeTab(RegistrationName) };
			}
		}
	}
}

#pragma endregion Widgets


#pragma region Files

bool UEditorTools::PromptSaveToTextFile(const FString FileContent, FString FileName, const EDirectory BaseDirectory, const FString FileType)
{
	FString Subfolder{ UTools::DirectoryToString(BaseDirectory) };

	// Split subfolder path from file name.
	if (FileName.Contains("/"))
	{
		FileName.Split(TEXT("/"), &Subfolder, &FileName, ESearchCase::IgnoreCase, ESearchDir::FromEnd);
		Subfolder = UTools::DirectoryToString(BaseDirectory) + Subfolder;
	}

	// Open the save file dialog.
	if (TArray<FString> FilePaths; FDesktopPlatformModule::Get()->SaveFileDialog(
		nullptr,
		"Save File(s)",
		Subfolder,
		FileName,
		FileType,
		EFileDialogFlags::None,
		FilePaths
	))
	{
		// Save file to selected folders.
		for (auto& FilePath : FilePaths)
		{
			FFileHelper::SaveStringToFile(
				FileContent,
				*FPaths::ConvertRelativePathToFull(FilePath),
				FFileHelper::EEncodingOptions::AutoDetect,
				&IFileManager::Get(),
				FILEWRITE_Append
			);
		}

		return true;
	}

	return false;
}

bool UEditorTools::PromptLoadTextFile(TArray<FString>& FilesContents, const FString SubFolderPath, const EDirectory BaseDirectory, const FString FileType, EFileSelection FileDialogFlags)
{
	// Open file selection dialog.
	if (TArray<FString> FilePaths; FDesktopPlatformModule::Get()->OpenFileDialog(
		nullptr,
		"Select File(s)",
		UTools::DirectoryToString(BaseDirectory) + SubFolderPath,
		"",
		FileType,
		StaticCast<uint8>(FileDialogFlags),
		FilePaths
	))
	{
		// Return selected files content.
		for (auto& FilePath : FilePaths)
			FFileHelper::LoadFileToString(FilesContents[FilesContents.Add("")], *FPaths::ConvertRelativePathToFull(FilePath));

		return true;
	}

	return false;
}

#pragma endregion Files