// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptAssetActions.h"

// #include "EditorFramework/AssetImportData.h"
// #include "Framework/MultiBox/MultiBoxBuilder.h"
#include "DesktopPlatformModule.h"
#include "EditorFramework/AssetImportData.h"
#include "Misc/FileHelper.h"

#include "Core/QuillscriptAsset.h"


FQuillscriptAssetActions::FQuillscriptAssetActions(const uint32 InAssetCategory)
{
	this->AssetCategory = InAssetCategory;
}

uint32 FQuillscriptAssetActions::GetCategories()
{
	return this->AssetCategory;
}

FText FQuillscriptAssetActions::GetName() const
{
	return FText::FromString("Script");
}

UClass* FQuillscriptAssetActions::GetSupportedClass() const
{
	return UQuillscriptAsset::StaticClass();
}

FColor FQuillscriptAssetActions::GetTypeColor() const
{
	return FColor(255, 201, 31);
}

bool FQuillscriptAssetActions::HasActions(const TArray<UObject*>& InObjects) const
{
	return true;
}

void FQuillscriptAssetActions::GetActions(const TArray<UObject*>& InObjects, FMenuBuilder& MenuBuilder)
{
	const auto Data{ GetTypedWeakObjectPtrs<UQuillscriptAsset>(InObjects) };

	// Menu Entries

	// Reimport
	MenuBuilder.AddMenuEntry(
		FText::FromString("Reimport"),
		FText::FromString("Reimport script asset from source file."),
		FSlateIcon(
			FAppStyle::GetAppStyleSetName(),
			"Icons.Toolbar.Import",
			"Themes.Import"
		),
		FUIAction(
			FExecuteAction::CreateSP(this, &FQuillscriptAssetActions::Reimport, Data),
			FCanExecuteAction()
		)
	);

	// Export
	MenuBuilder.AddMenuEntry(
		FText::FromString("Export"),
		FText::FromString("Export the source script asset file used to create this script."),
		FSlateIcon(
			FAppStyle::GetAppStyleSetName(),
			"Icons.Toolbar.Export",
			"Themes.Export"
		),
		FUIAction(
			FExecuteAction::CreateSP(this, &FQuillscriptAssetActions::Export, Data),
			FCanExecuteAction()
		)
	);

	// Open in Text Editor
	// MenuBuilder.AddMenuEntry(
	// 	FText::FromString("Open with Text Editor"),
	// 	FText::FromString("Open this asset source file in Visual Studio Code."),
	// 	FSlateIcon(
	// 		FEditorStyle::GetStyleSetName(),
	// 		"ClassIcon.PaperFlipbook",
	// 		"ClassIcon.PaperFlipbook.Small"
	// 	),
	// 	FUIAction(
	// 		FExecuteAction::CreateSP(this, &FQuillscriptAssetActions::OpenWithVSCode, Data),
	// 		FCanExecuteAction()
	// 	)
	// );
}

void FQuillscriptAssetActions::OpenWithVSCode(const TArray<TWeakObjectPtr<UQuillscriptAsset>> Objects)
{
	// for (auto ObjIt = Objects.CreateConstIterator(); ObjIt; ++ObjIt)
	// {
	// 	const auto Object{ (*ObjIt).Get() };
	// 	const FString ScriptEditorCommand{ UQuillscriptSettings::GetScriptEditorCommand() };
	//
	// 	if (
	// 		!ScriptEditorCommand.IsEmpty() &&
	// 		Object &&
	// 		Object->AssetImportData &&
	// 		system(nullptr))
	// 	{
	//
	// 		const FString Path{ UQuillscriptSettings::GetScriptEditorCommand() +  " \"" + Object->AssetImportData->ExtractFilenames()[0] + "\"" };
	// 		system(TCHAR_TO_ANSI(*Path));
	// 	}
	// }
}

void FQuillscriptAssetActions::Reimport(const TArray<TWeakObjectPtr<UQuillscriptAsset>> Objects)
{
	for (auto ObjIt{ Objects.CreateConstIterator() }; ObjIt; ++ObjIt)
		if (const auto Object{ (*ObjIt).Get() })
			Object->ReimportScript();
}

void FQuillscriptAssetActions::Export(const TArray<TWeakObjectPtr<UQuillscriptAsset>> Objects)
{
	for (auto ObjIt{ Objects.CreateConstIterator() }; ObjIt; ++ObjIt)
	{
		if (const auto Object{ (*ObjIt).Get() })
		{
			FString FileName{ Object->GetName() };
			FString Folder{ FPaths::ProjectSavedDir() };
			TArray<FString> FilePaths;

			// Get file original name and location.
			if (Object->AssetImportData->ExtractFilenames().IsValidIndex(0))
			{
				FileName = FPaths::GetBaseFilename(Object->AssetImportData->ExtractFilenames()[0]);
				Folder = FPaths::GetPath(Object->AssetImportData->ExtractFilenames()[0]);
			}

			// Open save file dialog.
			if (FDesktopPlatformModule::Get()->SaveFileDialog(
				0,
				"Save Script",
				Folder,
				FileName,
				"Text Files|*.qsc",
				EFileDialogFlags::None,
				FilePaths
			))
			{
				// Save file to selected folders.
				for (auto& FilePath : FilePaths)
				{
					FFileHelper::SaveStringToFile(
						Object->GetSourceCode(),
						*FPaths::ConvertRelativePathToFull(FilePath),
						FFileHelper::EEncodingOptions::AutoDetect,
						&IFileManager::Get(),
						FILEWRITE_Append
					);
				}
			}
		}
	}
}