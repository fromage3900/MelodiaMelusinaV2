// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Base/Directory.h"
#include "Base/PrintType.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Misc/Timecode.h"
#include "Text/SmartTypewriter.h"
#include "Tools.generated.h"

class UWidget;

#pragma region Macros

#define STR(Value)			UTools::ToString(Value)
#define TXT(Value)			FText::FromString(STR(Value))

#define PRINT(Message)		UTools::Print(STR(Message), this)
#define SUCCESS(Message)	UTools::Success(STR(Message), this)
#define WARNING(Message)	UTools::Warning(STR(Message), this)
#define ERROR(Message)		UTools::Error(STR(Message), this)

#define LOAD				UTools::LoadAssetByPath
#define HAS_AUTHORITY		UTools::HasAuthority(WorldContextObject)

#pragma endregion


/**
 * Collection of useful functions.
 */
UCLASS()
class QUILLSCRIPT_API UTools final : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/// Print and Log Message
	#pragma region Print

	/**
	 * Print a log message in the editor.
	 *
	 * @param	Message
	 * @param	Owner		Object that called this function. Can be null.
	 * @param	PrintType	Message type, to change text color accordingly.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Development|Print", meta = ( AdvancedDisplay = 1, Keywords = "Debug, Display, Print, Log, Show, Dev, Console" ))
	static void Log(FString Message, const UObject* Owner = nullptr, const EPrintType PrintType = EPrintType::Log);

	/**
	 * Print a debug message in the editor.
	 *
	 * @param	Message
	 * @param	Owner	Object that called this function. Can be left blank.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Development|Print", meta = ( AdvancedDisplay = 1, Keywords = "Debug, Display, Print, Log, Show, Dev, Console" ))
	static void Print(const FString Message, const UObject* Owner = nullptr);

	/**
	 * Print a success message in the editor.
	 *
	 * @param	Message
	 * @param	Owner	Object that called this function. Can be left blank.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Development|Print", meta = ( AdvancedDisplay = 1, Keywords = "Debug, Display, Print, Log, Show, Dev, Console" ))
	static void Success(const FString Message, const UObject* Owner = nullptr);

	/**
	 * Print a warning message in the editor.
	 *
	 * @param	Message
	 * @param	Owner	Object that called this function. Can be left blank.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Development|Print", meta = ( AdvancedDisplay = 1, Keywords = "Debug, Display, Print, Log, Show, Dev, Console" ))
	static void Warning(const FString Message, const UObject* Owner = nullptr);

	/**
	 * Print an error message in the editor.
	 *
	 * @param	Message
	 * @param	Owner	Object that called this function. Can be left blank.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Development|Print", meta = ( AdvancedDisplay = 1, Keywords = "Debug, Display, Print, Log, Show, Dev, Console" ))
	static void Error(const FString Message, const UObject* Owner = nullptr);

	#pragma endregion Print


	/// Tools
	#pragma region Utilities

	/**
	 * Rename a given object.
	 * Whitespaces will be removed.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static void RenameObject(UObject* Object, FString NewName);

	/**
	 * Try to find a class by path.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static UClass* FindClassByPath(FString Path);

	UFUNCTION(BlueprintPure, Category = "Quillscript|Utilities", meta = ( DeterminesOutputType = "Class", CompactNodeTitle = "Default Obj" ))
	static UObject* GetClassDefaultObject(const UClass* Class);

	/**
	 * Check if an object has a property with the given name.
	 *
	 * @param Object		Object that owns the property.
	 * @param PropertyName	Name of the property to find.
	 * @param Type			Outer parameter to store the property type. Stores 'undefined' if the property is not found.
	 * @return	Return true if a property with the given name is found.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static bool PropertyExists(UObject* Object, const FName PropertyName, FString& Type);

	/**
	 * Get the value as a string, of an object's property.
	 *
	 * @param Object		Object that owns the property.
	 * @param PropertyName	Name of the property to find.
	 * @param Type			Outer parameter to store the property type. Stores 'undefined' if the property is not found.
	 * @return	Return value as a string.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static FString GetPropertyByName(UObject* Object, const FName PropertyName, FString& Type);

	/**
	 * Set the value as a string of an object's property.
	 *
	 * @param Object		Object that owns the property.
	 * @param PropertyName	Name of the property to find.
	 * @param ValueAsString	Value to set, in string format.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static void SetPropertyByName(UObject* Object, const FName PropertyName, const FString ValueAsString);

	/**
	 * Get the value as a string, of an object's property.
	 * To Use the property later, it can be converted to the desired type or used as a void*.
	 *		Ex.: FString Type;
	 *			 void* Ptr{ UTools::FindPropertyByName(Object, "PropertyName", Type) };
	 *
	 *			 (Primitive) int32* VarPtr{ StaticCast<int32*>(Ptr);
	 *			 (Struct)    TMap<FName, FText>* VarPtr{ StaticCast<TMap<FName, FText>*>(Ptr);
	 *			 (Pointer)   if (UObject** BasePtr{ StaticCast<UObject**>(Ptr) }) { UObject* DefPtr{ *BasePtr }; }
	 *
	 * @param Object		Object that owns the property.
	 * @param PropertyName	Name of the property to find.
	 * @param Type			Outer parameter to store the property type. Stores 'undefined' if the property is not found.
	 * @return	Return value as a pointer.
	 */
	static void* FindPropertyByName(UObject* Object, const FName PropertyName, FString& Type);

	/**
	 * Set the value as a string of an object's property.
	 *
	 * @param Object		Object that owns the property.
	 * @param PropertyName	Name of the property to find.
	 * @param ValuePtr		Value as a void pointer.
		 `UTools::InsertPropertyByName(Object, "PropertyName", &AnyDataType);`
		 or
		 `const void* ValuePtr{ &AnyDataType };`
		 `UTools::InsertPropertyByName(Object, "PropertyName", ValuePtr);`
	 */
	static void InsertPropertyByName(UObject* Object, const FName PropertyName, const void* ValuePtr);

	/**
	 * Call a Target's function by name.
	 * This is a simplified general usage version of 'Interpreter.CallFunctionOnTarget'
	 * that does not create Quillscript variables and script references.
	 *
	 * @param WorldContextObject
	 * @param Target		Object to call the function from.
	 * @param FunctionName	Name of the function to call.
	 * @param Parameters	Function entry parameters to pass as strings. The parameters must be in the same order they are declared.
	 * @return	Return value and outer parameters of the function.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities", meta = ( WorldContext = "WorldContextObject" ))
	static TMap<FName, FString> CallFunctionByName(UObject* WorldContextObject, UObject* Target, const FName FunctionName, const TArray<FString>& Parameters);

	/**
	 * Shortcut function to be used inside static methods that have a 'WorldContextObject' parameter.
	 * If your function has access to 'HasAuthority()' by other means, use those instead.
	 *
	 * Can also be used with the macro 'HAS_AUTHORITY'.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Utilities", meta = ( WorldContext = "WorldContextObject" ))
	static bool HasAuthority(const UObject* WorldContextObject);

	/**
	 * Check if a module/plugin is loaded.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static bool IsModuleLoaded(const FName ModuleName);

	/**
	 * Generate a random string of characters including numbers and symbols.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Utilities", meta = ( AdvancedDisplay = 2 ))
	static FString GenerateRandomString(const uint8 Size = 8, const bool bLetters = true, const bool bNumbers = true, const bool bSymbols = false);

	/**
	 * Get a Level transition option.
	 *
	 * @param	WorldContextObject
	 * @param	Key					Option key.
	 * @param	Value				Receive option value.
	 *
	 * @return	True, if the option key exists.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Utilities", meta = ( WorldContext = "WorldContextObject" ))
	static bool RetrieveOption(const UObject* WorldContextObject, const FString& Key, FString& Value);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static TArray<FString> SortStringsAlphabetically(TArray<FString> Strings);

	/**
	 * Load a String Table if it is not.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static void RegisterStringTable(const FName StringTablePath);

	/**
	 * Find the String Table key of a given Text variable.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static FString FindStringTableKey(const FText& Text, FName& StringTableId);

	/**
	 * Create a list with all variable names in a string.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static TArray<FString> GetVariablesInString(FString String);

	/**
	 * Check if the given string table contains the given key.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static bool StringTableContains(const FName StringTableName, const FString Key, FString& OutSourceString);

	UFUNCTION(BlueprintPure, Category = "Quillscript|Utilities")
	static FString GetWorldTypeAsString();

	/**
	 * Get the length of a container as string (Array, Set, Map).
	 * This is useful to get the length of an array in a Quillscript script, use the engine methods for all other cases.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static int32 Length(FString ContainerAsString);

	/**
	 * Search a string using a regular expression pattern.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities", meta = ( Keywords = "Regex, Regular Expression, Search, Match, Find", AdvancedDisplay = "bCaseInsensitive" ))
	static TArray<FString> RegexMatch(const FString& SourceString, const FString& Pattern, const bool bCaseInsensitive = false);

	#pragma endregion Utilities


	/// Metadata
	#pragma region Metadata

	/**
	 * Return the project name set in the 'Edit > Project Settings > Project > Description > Project Name' field.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Metadata", meta = ( CompactNodeTitle = "Project" ))
	static FString GetProjectName();

	/**
	 * Return the project version set in the 'Edit > Project Settings > Project > Description > Project Version' field.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Metadata", meta = ( CompactNodeTitle = "Version" ))
	static FString GetProjectVersion();

	/**
	 * Return the company name set in the 'Edit > Project Settings > Project > Description > Company Name' field.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Metadata", meta = ( CompactNodeTitle = "Company" ))
	static FString GetCompanyName();

	#pragma endregion Metadata


    /// Assets
	#pragma region Assets

	/**
	 * Mark the given asset as dirty.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Assets")
    static void MarkAssetDirty(const UObject* Asset);

	/**
	 * Save the given asset to disk, overriding the previous asset data.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Assets")
    static void SaveAsset(UObject* Asset);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Assets")
	static bool AssetExists(const FString& AssetPath);

	/**
	 * Load an asset using a soft object path.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Utilities")
	static UObject* LoadAssetByPath(const FString& Path);

	template<typename T>
	static T* LoadAssetByPath(const FString& Path)
	{
		if (const TObjectPtr<T> Asset{ Cast<T>(FSoftObjectPath(Path).TryLoad()) })
			return Asset;

		Warning("UTools::LoadAssetByPath() -> Asset not found: " + Path);
		return nullptr;
	}

	#pragma endregion Assets


	/// Files
	#pragma region Files

	/**
	 * Get all save games' slot names in '/Saved/SaveGames' folder, without the '.sav' extension (filename only).
	 *
	 * @return List of found save games' slot names.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Files")
	static TArray<FString> GetAllSaveGameSlotNames();

	/**
	 * Save content to a text file.
	 *
	 * @param	FileName		File name to save. Ex.: "Notes.txt", "Folder/SubFolder/MyTextFile.ini"
	 * @param	FileContent		Text content to save
	 * @param	BaseDirectory	Base directory to save the file.
	 *
	 * @return	Did saved
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files")
	static bool SaveToTextFile(const FString FileName, const FString FileContent, const EDirectory BaseDirectory = EDirectory::Custom);

	/**
	 * Load a text file content.
	 *
	 * @param	FileContent		Variable to store the loaded text.
	 * @param	FileName		File name to save. Ex.: "Notes.txt", "Folder/SubFolder/MyTextFile.ini"
	 * @param	BaseDirectory	Base directory to search for the file.
	 *
	 * @return	True, if file loaded successfully.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files")
	static bool LoadTextFile(FString& FileContent, const FString FileName, const EDirectory BaseDirectory = EDirectory::Custom);

	/**
	 * Load a PNG image file into a Texture object.
	 *
	 * @param	FileName		Image file name. Ex.: "Screenshot.png", "Folder/SubFolder/Screenshot.jpg"
	 * @param	BaseDirectory	Base directory to search for the image file.
	 *
	 * @return	Texture object.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files")
	static UTexture2D* LoadImage(const FString FileName, const EDirectory BaseDirectory = EDirectory::Custom);

	/**
	 * Take a screenshot and save it as PNG, in engine's default screenshots folder.
	 *
	 * @param	BaseDirectory	Base directory to save the screenshot.
	 * @param	FileName		Screenshot file name. Ex.: "Screenshot.png", "Folder/SubFolder/Screenshot.jpg"
	 * @param	bCaptureUI		Should Widgets be captured too.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files")
	static void TakeScreenshot(const EDirectory BaseDirectory = EDirectory::ScreenShot, const FString FileName = "screenshot", const bool bCaptureUI = true);

	/**
	 * Convert from Directory enum to String.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Files", meta = ( CompactNodeTitle = "Directory" ))
	static FString DirectoryToString(const EDirectory Directory);

	/**
	 * List all files in the given directory.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files", meta = ( AutoCreateRefTerm = "FileExtensionFilter", AdvancedDisplay = "bRecursively" ))
	static TArray<FString> ListFiles(FString Directory, const TArray<FString> FileExtensionFilter, const EDirectory BaseDirectory = EDirectory::Project, const bool bRecursively = false);

	/**
	 * List all subdirectories in the given directory.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files", meta = ( AdvancedDisplay = "bRecursively" ))
	static TArray<FString> ListDirectories(FString Directory, const EDirectory BaseDirectory = EDirectory::Project, const bool bRecursively = false);

	/**
	 * Launch a file in the system's default application.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Files")
	static void LaunchFile(FString FilePath, const EDirectory BaseDirectory = EDirectory::Project);

	#pragma endregion Files


	/// Settings
	#pragma region Settings

	/**
	 * Load a boolean setting from a '.ini' setting file.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings")
	static bool GetBoolSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, bool& SettingValue);

	/**
	 * Write a boolean setting value to existing a '.ini' setting file.
	 * The results is stored at "<YourGameDir>\Saved\Config\Windows"
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings", meta = ( AdvancedDisplay = "CustomFile" ))
	static void SetBoolSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, const bool Value, const FString CustomFile = "");

	/**
	 * Load a string setting from a '.ini' setting file.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings")
	static bool GetStringSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, FString& SettingValue);

	/**
	 * Write a string setting value to existing a '.ini' setting file.
	 * The results is stored at "<YourGameDir>\Saved\Config\Windows"
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings", meta = ( AdvancedDisplay = "CustomFile" ))
	static void SetStringSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, const FString Value, const FString CustomFile = "");

	/**
	 * Load a integer setting from a '.ini' setting file.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings")
	static bool GetIntSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, int32& SettingValue);

	/**
	 * Write a integer setting value to existing a '.ini' setting file.
	 * The results is stored at "<YourGameDir>\Saved\Config\Windows"
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings", meta = ( AdvancedDisplay = "CustomFile" ))
	static void SetIntSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, const int32 Value, const FString CustomFile = "");

	/**
	 * Load a float setting from a '.ini' setting file.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings")
	static bool GetFloatSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, float& SettingValue);

	/**
	 * Write a float setting value to existing a '.ini' setting file.
	 * The results is stored at "<YourGameDir>\Saved\Config\Windows"
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings", meta = ( AdvancedDisplay = "CustomFile" ))
	static void SetFloatSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, const float Value, const FString CustomFile = "");

	/**
	 * Convert from Setting File enum to object.
	 */
	static FString SettingFileToString(const ESettingsFile SettingFile);

	#pragma endregion Settings


	/// User Interface
	#pragma region UI

	/**
	 * Remove the widget from memory.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	static void DestroyWidget(UWidget* Widget);

	/**
	 * Encapsulates this Widget in a combination of Scale and Size boxes to keep this widget in a given aspect ratio, and add it to viewport.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface", meta = ( AdvancedDisplay = 1 ))
	static void AddToConstraintViewport(UUserWidget* Widget, const int32 ZOrder = 0, const FVector2D Ratio = FVector2D(1920, 1080));

	/**
	 * Take a picture of a widget and return it as a texture.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	static UTexture2D* CaptureWidget(UUserWidget* UserWidget, const FVector2D DrawSize = FVector2D(512, 512));

	/**
	 * Get all children, children of children and so on from the root widget.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	static TArray<UWidget*> GetNestedWidgets(UWidget* RootWidget);

	/**
	 * Get all children, children of children and so on, of class, from the root widget.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	static TArray<UWidget*> GetNestedWidgetsOfClass(UWidget* RootWidget, const TArray<TSubclassOf<UWidget>> Classes);

	/**
	 * Add the given widget as a child of the parent widget at the given index.
	 * Add as last if the index is invalid.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	static void AddChildWidgetAt(UWidget* Parent, UWidget* Child, const int32 Index);

	/**
	 * Remove all Visible, HitTestInvisible or SelfHitTestInvisible widgets from the list.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	static TArray<UWidget*> RemoveVisibleWidgets(TArray<UWidget*> Widgets);

	/**
	 * Remove all Hidden or Collapsed widgets from the list.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	static TArray<UWidget*> RemoveHiddenWidgets(TArray<UWidget*> Widgets);

	/**
	 * Return the given string in the 'On Printed Event' character-by-character in the given interval.
	 *
	 * @param WorldContextObject
	 * @param Text				Text to typewrite.
	 * @param PrintedDelegate	Callback event to be called each time a character is printed.
	 * @param CompletedDelegate Callback event to be called when the typewriting is completed.
	 * @param Interval			Interval between each character print.
	 * @param Sound				Sound to play when printing.
	 * @param bOverlapSound		Play each key sound in an individual Audio Component or use the same Audio Component.
	 * @param bSanitize			Remove trailing whitespaces.
	 *
	 * @return Timer handle to control the effect.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface", meta = ( WorldContext = "WorldContextObject", AdvancedDisplay = "Sound, bOverlapSound, bSanitize" ))
	static ASmartTypewriter* PlayTypewriterEffect(UObject* WorldContextObject, const FText Text,
		UPARAM(DisplayName = "On Printed Event") const FTextPrintedDelegate& PrintedDelegate,
		UPARAM(DisplayName = "On Completed Event") const FTextCompletedDelegate& CompletedDelegate,
		const float Interval = 0.02, USoundBase* Sound = nullptr, const bool bOverlapSound = false, const bool bSanitize = true);

	#pragma endregion UI


	/// Pipes
	#pragma region Pipes

	/**
	 * Replace in given string, occurrences of substrings with {var} format, for its value in a 'String Map' and 'String Tables'.
	 *
	 * @param WorldContextObject
	 * @param String		String to replace.
	 * @param VariablesMap	Variables map to search in.
	 * @param StringTables	String tables to search in.
	 * @param Escape		Replace not found variables with this string. Leave empty to do not replace.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Pipes", meta = ( WorldContext = "WorldContextObject", AutoCreateRefTerm = "VariablesMap,StringTables", AdvancedDisplay = "Escape" ))
	static FString ReplaceVariables(const UObject* WorldContextObject, const FString String, const TMap<FName, FString> VariablesMap, const TArray<UStringTable*> StringTables, FString Escape = "");

	/**
	 * Converts from float to signed number string.
	 * N > 0 = +N; N == 0 = 0; N < 0 = -N;
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes", meta = ( CompactNodeTitle = "Signed" ))
    static FText ToSignedNumber(const float Number);

	/**
	 * Convert from pascal case to a user displayable text.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes", meta = ( CompactNodeTitle = "To Display", AdvancedDisplay = "bIsBool" ))
    static FText ToDisplayText(const FString& String, const bool bIsBool = false);

	/**
	 * Change first character from this string to upper case.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes", meta = ( CompactNodeTitle = "Capital" ))
    static FString UpperFirstLetter(const FString& String);

	/**
	 * Change first character from this text to upper case.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes", meta = ( CompactNodeTitle = "Capital" ))
	static FText TextUpperFirstLetter(const FText& Text);

	/**
	 * Replace accentuated characters.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes", meta = ( CompactNodeTitle = "No Accent" ))
	static FString RemoveAccentuation(FString String);

	/**
	 * Remove rich text tags.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes", meta = ( CompactNodeTitle = "No Rich Text" ))
	static FString RemoveRichTextTags(FString String);

	/**
	 * Convert the given string to a decimal hash with 10 numbers.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Pipes")
	static FString ToHash(const FString String);

	/**
	 * Convert from decimal to hexadecimal string.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Pipes")
	static FString ToHex(int64 Decimal);

	/**
	 * Encrypt the given string with AES.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Pipes")
    static FString Encrypt(FString InputString, FString Key);

	/**
	 * Decrypt the given string with AES.
	 */
    UFUNCTION(BlueprintCallable, Category = "Quillscript|Pipes")
	static FString Decrypt(FString InputString, FString Key);

	/**
	 * Check if a string contains a : (Colon).
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes")
    static bool IsKeyValuePair(const FString& Pair);

	/**
	 * Split a string into two parts, separated by : (Colon).
	 * Ex.: "Key:Value" -> "Key", "Value"
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes", meta = ( CompactNodeTitle = "Key:Value" ))
    static void ToKeyValuePair(const FString& Pair, FString& Key, FString& Value);

	/**
	 * Check if an array of strings contains a given key in the patter 'key:value'.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes", meta = ( CompactNodeTitle = "Has Key" ))
	static bool HasKeyValueTag(const TArray<FString>& Tags, const FString& Key, FString& Value);

	/**
	 * Create a new array equal to the given one, but with all repeated values removed.
	 */
	template <class T>
	static TArray<T> RemoveRepeatedValues(TArray<T> Array)
	{
		TArray<T> NewArray;

		for (T Element : Array)
			NewArray.AddUnique(Element);

		return NewArray;
	}


	/**
	 * Overload functions to convert data types to string.
	 *
	 * ! Will not compile if the type is a child class of it 'UObject' or custom class.
	 *		Use the appropriated 'UObject' member functions instead.
	 *		Ex.: Object->GetName(), Object->GetPathName(), etc.
	 *
	 * Similar to LexToString(Value), but with more types.
	 */
	FORCEINLINE static FString ToString(const bool& Value)			{	return LexToString(Value);							}
	FORCEINLINE static FString ToString(const char* Value)			{	return Value;										}
	FORCEINLINE static FString ToString(const FName& Value)			{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FString& Value)		{	return Value;										}
	FORCEINLINE static FString ToString(const FText& Value)			{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const uint8& Value)			{	return FString::FromInt(Value);						}
	FORCEINLINE static FString ToString(const int32& Value)			{	return FString::FromInt(Value);						}
	FORCEINLINE static FString ToString(const int64& Value)			{	return FString::Printf(TEXT("%lld"), Value);	}
	FORCEINLINE static FString ToString(const float& Value)			{	return FString::SanitizeFloat(Value);				}
	FORCEINLINE static FString ToString(const double& Value)		{	return FString::Printf(TEXT("%f"), Value);	}
	FORCEINLINE static FString ToString(const FGuid& Value)			{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FDateTime& Value)		{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FTimespan& Value)		{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FTimecode& Value)		{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FVector& Value)		{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FVector2D& Value)		{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FRotator& Value)		{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FTransform& Value)	{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FGameplayTag& Value)	{	return Value.ToString();							}
	FORCEINLINE static FString ToString(const FGameplayTagContainer& Value)	{ return Value.ToString();						}

	template<typename T>
	static FString ToString(const TArray<T>& Array)
	{
		FString Result = TEXT("(");

		for (int i = 0; i < Array.Num(); ++i)
		{
			Result += (i != 0 ? TEXT(", ") : TEXT("")) + LexToString("\"" + Array[i] + "\"");
		}

		Result += TEXT(")");
		return Result;
	}

	template<typename T>
	static FString ToString(const TSet<T>& Set)
	{
		FString Result = TEXT("(");

		int i = 0;
		for (const T& Element : Set)
		{
			Result += (i++ != 0 ? TEXT(", ") : TEXT("")) + LexToString("\"" + Element + "\"");
		}

		Result += TEXT(")");
		return Result;
	}

	template<typename K, typename V>
	static FString ToString(const TMap<K, V>& Map)
	{
		FString Result = TEXT("(");

		int i = 0;
		for (const TPair<K, V>& Pair : Map)
		{
			Result += (i++ != 0 ? TEXT(", ") : TEXT("")) + FString::Printf(TEXT("(\"%s\", \"%s\")"), *LexToString(Pair.Key), *LexToString(Pair.Value));
		}

		Result += TEXT(")");
		return Result;
	}

	template<typename EnumType>
	static typename TEnableIf<TIsEnum<EnumType>::Value, FString>::Type ToString(const EnumType& EnumValue)
	{
		// Pattern: EEnumClass::EnumValue
		// if constexpr (TIsEnum<Type>::Value)
		// {
			const TObjectPtr<UEnum> EnumClass{ StaticEnum<EnumType>() };
			return EnumClass ? EnumClass->GetNameByValue(static_cast<int64>(EnumValue)).ToString() : "Invalid Enum";
		// }

		// Pattern: EnumValue
		// return LexToString(Enum);
		// return LexToString(static_cast<int64>(Enum));
	}

	/**
	 * Convert from FString to Enum
	 */
	template <typename TEnum>
	static TEnum StringToEnum(const FString& EnumNameAsString)
	{
		// Find the UEnum
		const UEnum* EnumPtr{ StaticEnum<TEnum>() };

		if (!EnumPtr)
		{
			Warning("UTools::StringToEnum() -> Enum not found: " + EnumNameAsString);
			return TEnum(0);
		}

		// Find the index of the value
		const int32 EnumIndex{ EnumPtr->GetIndexByName(*EnumNameAsString) };

		if (EnumIndex == INDEX_NONE)
		{
			Warning("UTools::StringToEnum() -> Invalid Enum value '" + EnumNameAsString + "' for '" + EnumPtr->GetName() + "'");
			return TEnum(0);
		}

		return static_cast<TEnum>(EnumIndex);
	}

	#pragma endregion Pipes


	/// Operators
	#pragma region Operators

	/**
	 * Returns the first non-null operand in the given parameters list.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Operators", meta = ( CompactNodeTitle = "??", CommutativeAssociativeBinaryOperator = "true" ))
	static UObject* NullCoalescingOperator(UObject* A, UObject* B);

	/**
	 * Evaluate the given valid math expression.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Operators")
	static double SolveMathExpression(const FString Expression);

	/**
	 * Check if two players are the same using their 'Unique Net ID'.
	 *
	 * A 'Unique Net ID' is a system-designed identifier that uniquely represents a player's account across multiple sessions and devices.
	 * In a multiplayer game, each player would be assigned a 'Unique Net ID'.
	 * This ID remains consistent regardless of the device or platform the player is using.
	 * Please note that the specific implementation of the Unique Net ID might vary depending on the online subsystem being used, like Steam, Xbox Live, PlayStation Network, or Epic Online Services, etc.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Operators", meta = ( CompactNodeTitle = "==", Keywords = "Equal, Not, Compare" ))
	static bool IsSameUniqueNetId(const FUniqueNetIdRepl& UniqueIdA, const FUniqueNetIdRepl& UniqueIdB);

	/**
	 * Check if the given player state belongs to the host or a client.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Operators")
	static bool IsHost(const APlayerState* PlayerState);

	#pragma endregion Operators
};