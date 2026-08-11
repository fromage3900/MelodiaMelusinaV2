// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Base/Directory.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "EditorTools.generated.h"

/**
 * Collection of useful editor functions.
 */
UCLASS()
class QUILLSCRIPTEDITOR_API UEditorTools final : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/// Widgets
	#pragma region Widgets

	/**
	 * Spawn Editor Utility Widget tab.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Editor")
	static void SpawnTab(const FText TabTitle, const FString& WidgetPath);
	static void SpawnTab(const FText& TabTitle, const FString& WidgetPath, const FSlateIcon& TabIcon);

	#pragma endregion Widgets


	/// Files
	#pragma region Files

	/**
	 * Prompt user to save content to a text file.
	 *
	 * @param	FileContent		Text content to save
	 * @param	FileName		File name to save. Ex.: "filename", "Notes.txt", "Folder/SubFolder/MyTextFile.ini"
	 * @param	BaseDirectory	Base directory to save the file.
	 * @param	FileType		File filter.
	 *
	 * @return	Did saved
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files", meta = ( AdvancedDisplay = "FileType" ))
	static bool PromptSaveToTextFile(const FString FileContent, FString FileName = "filename",
		const EDirectory BaseDirectory = EDirectory::Custom, const FString FileType = "Text File|*.txt");

	/**
	 * Prompt user to load text file(s) content.
	 *
	 * @param	FilesContents	Variable to store the loaded texts.
	 * @param	SubFolderPath	Sub folder to look at. Ex.: "Folder", "Folder/SubFolder"
	 * @param	BaseDirectory	Base directory to search for the files.
	 * @param	FileType		File type filter.
	 * @param	FileDialogFlags	File dialog flag.
	 *
	 * @return	True, if file loaded successfully.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files", meta = ( AdvancedDisplay = 3 ))
	static bool PromptLoadTextFile(TArray<FString>& FilesContents, const FString SubFolderPath = "",
		const EDirectory BaseDirectory = EDirectory::Custom, const FString FileType = "Text Files|*.txt", EFileSelection FileDialogFlags = EFileSelection::Single);

	#pragma endregion Files
};