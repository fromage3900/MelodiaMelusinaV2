// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Base/ScriptSettings.h"
#include "Base/VerbosityMode.h"

#include "CoreMinimal.h"
#include "Base/MultiplayerMode.h"
#include "Base/MultiplayerSelectionMode.h"
#include "Engine/DeveloperSettings.h"
#include "QuillscriptSettings.generated.h"

/**
 * Quillscript plugin settings.
 */
UCLASS(config = Game, defaultconfig, meta = ( DisplayName = "Quillscript" ))
class QUILLSCRIPT_API UQuillscriptSettings final : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	virtual void PostInitProperties() override;


	/// Editor
	#if WITH_EDITOR

	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
	virtual FName GetCategoryName() const override;

	#endif


	/// Asset
	#pragma region Asset

	/**
	 * Get the current in use settings asset or plugin settings.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Settings", DisplayName = "Quillscript Settings", meta = ( CompactNodeTitle = "Quillscript Current Settings" ))
	static const UQuillscriptSettings* Get();

	/**
	 * Get the default settings in the plugin's settings.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Settings", DisplayName = "Quillscript Default Settings", meta = ( CompactNodeTitle = "Quillscript Default Settings" ))
	static const UQuillscriptSettings* Default();

	/**
	 * Get the current in use settings asset.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Settings", DisplayName = "Quillscript Asset Settings", meta = ( CompactNodeTitle = "Quillscript Asset Settings" ))
	static const UQuillscriptSettings* Asset();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings", meta = ( WorldContext = "WorldContextObject" ))
	static void UseSettingsAsset(const UObject* WorldContextObject, UQuillscriptSettings* NewSettingsAsset);

	/**
	 * Stop using any Settings Asset and use the plugin settings instead.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings", meta = ( WorldContext = "WorldContextObject" ))
	static void ClearSettingsAsset();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings")
	static UQuillscriptSettings* GetSettingsAssetByPath(FString Path);


	// TODO: Deprecated
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Settings", meta = ( WorldContext = "WorldContextObject", DeprecatedFunction, DeprecationMessage = "Use 'Use Settings Asset' instead. This method will be remove in future version." ))
	static void SetSettingsAsset(const UObject* WorldContextObject, UQuillscriptSettings* Value);

	#pragma endregion Asset


	/// Data
	#pragma region Data

	UFUNCTION(BlueprintPure, Category = "Quillscript|Settings", meta = ( CompactNodeTitle = "Has Multiplayer" ))
	bool HasMultiplayer() const;

	#pragma endregion Data


	/// Getters and Setters
	#pragma region GetSet

	UFUNCTION(BlueprintGetter)
	FORCEINLINE FScriptSettings GetScriptSettings() const { return this->ScriptSettings; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TMap<FName, FSoftObjectPath> GetDefaultScriptReferences() const { return this->DefaultScriptReferences; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TArray<FDirectoryPath> GetReferencesSearchPaths() const { return this->ReferencesSearchPaths; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetPreserveSettingsOnReimport() const { return this->bPreserveSettingsOnReimport; }


	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetCanRollback() const { return this->bCanRollback; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetAutoPlayOptionStatements() const { return this->bAutoPlayOptionStatements; }


	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetBackgroundBoxLayer() const { return this->BackgroundBoxLayer; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetDialogBoxLayer() const { return this->DialogBoxLayer; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetSelectionBoxLayer() const { return this->SelectionBoxLayer; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetManageDialogueBox() const { return this->ManageDialogueBox; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetManageSelectionBox() const { return this->ManageSelectionBox; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetManageBackgroundBox() const { return this->ManageBackgroundBox; }


	UFUNCTION(BlueprintGetter)
	FORCEINLINE TMap<FName, FText> GetDefaultVariables() const { return this->DefaultVariables; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetKeepVisitedStatements() const { return this->bKeepVisitedStatements; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetKeepVisitedLabels() const { return this->bKeepVisitedLabels; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetKeepSelectedOptions() const { return this->bKeepSelectedOptions; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetKeepLastSelectedOptionText() const { return this->bKeepLastSelectedOptionText; }


	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetMaxHistoryEntries() const { return this->MaxHistoryEntries; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetKeepHistory() const { return this->bKeepHistory; }


	// UFUNCTION(BlueprintGetter)
	// FORCEINLINE EMultiplayerMode GetMultiplayerMode() const  { return this->MultiplayerMode; }
	//
	// UFUNCTION(BlueprintGetter)
	// FORCEINLINE int32 GetAutoJoinRadius() const  { return this->AutoJoinRadius; }
	//
	// UFUNCTION(BlueprintGetter)
	// FORCEINLINE EMultiplayerSelectionMode GetMultiplayerSelectionMode() const  { return this->MultiplayerSelectionMode; }
	//
	// UFUNCTION(BlueprintGetter)
	// FORCEINLINE uint8 GetPoolTimer() const  { return this->PoolTimer; }


	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetRepeatedTags() const { return this->bRepeatedTags; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetStoreSourceCode() const { return this->bStoreSourceCode; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetStoreSourceLine() const { return this->bStoreSourceLine; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetStoreInlineComment() const { return this->bStoreInlineComment; }


	UFUNCTION(BlueprintGetter)
	FORCEINLINE EVerbosityMode GetVerbosity() const { return this->Verbosity; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetAlwaysPrintLog() const { return this->bAlwaysPrintLog; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetAutoReimportScripts() const { return this->bAutoReimportScripts; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetUpdateAtRuntime() const { return this->bUpdateAtRuntime; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE FString GetScriptEditorCommand() const { return this->ScriptEditorCommand; }

	#pragma endregion GetSet


private:
	/// Script
	#pragma region Script

	/** Default settings to use for all scripts if specific settings aren't provided on play. */
	UPROPERTY(config, BlueprintGetter = GetScriptSettings, EditAnywhere, Category = "Script")
	FScriptSettings ScriptSettings{
		nullptr,
		nullptr,
		nullptr,
		nullptr,
		nullptr,
		EPicker::Yes,
		EPicker::No,
		EPicker::No,
		EPicker::Yes,
		EInputMode::GameAndUI,
		EInputMode::GameAndUI
	};

	/**
	 * Default script references to use in all scripts.
	 * {&Name}
	 */
	UPROPERTY(config, BlueprintGetter = GetDefaultScriptReferences, EditAnywhere, Category = "Script")
	TMap<FName, FSoftObjectPath> DefaultScriptReferences;

	/**
	 * Default script paths to use in all scripts. Used to search for assets and assets' classes references.
	 * {&AssetName}
	 */
	UPROPERTY(config, BlueprintGetter = GetReferencesSearchPaths, EditAnywhere, Category = "Script", meta = ( LongPackageName ))
	TArray<FDirectoryPath> ReferencesSearchPaths;

	/**
	 * Preserve this script settings on reimport and replace just script content.
	 * ! If enabled, the reimport process may be slow on large projects.
	 */
	UPROPERTY(config, BlueprintGetter = GetPreserveSettingsOnReimport, EditAnywhere, Category = "Script")
	bool bPreserveSettingsOnReimport{ true };

	#pragma endregion Script


	/// Interpreter
	#pragma region Interpreter

	/** Can rollback to the previous statement and reload it's saved state. */
	UPROPERTY(config, BlueprintGetter = GetCanRollback, EditAnywhere, Category = "Interpreter")
	bool bCanRollback{ false };

	/** If the next statement after a dialogue one is an option statement, plays it automatically. */
	UPROPERTY(config, BlueprintGetter = GetAutoPlayOptionStatements, EditAnywhere, Category = "Interpreter")
	bool bAutoPlayOptionStatements{ false };

	#pragma endregion Interpreter


	/// User Interface
	#pragma region UI

	/** Default user interface layer to render the Background Box widget. */
	UPROPERTY(config, BlueprintGetter = GetBackgroundBoxLayer, EditAnywhere, Category = "User Interface")
	int32 BackgroundBoxLayer{ 5 };

	/** Default user interface layer to render the Dialog Box widget. */
	UPROPERTY(config, BlueprintGetter = GetDialogBoxLayer, EditAnywhere, Category = "User Interface")
	int32 DialogBoxLayer{ 10 };

	/** Default user interface layer to render the Selection Box widget. */
	UPROPERTY(config, BlueprintGetter = GetSelectionBoxLayer, EditAnywhere, Category = "User Interface")
	int32 SelectionBoxLayer{ 15 };

	/**
	 * If disabled, the Interpreter will not manage the lifecycle of the Dialogue Box,
	 * and its up to you to create, update, delete, etc. your own dialogue widget.
	 * Assign to the Interpreter's OnPlayDialogueBox event.
	 */
	UPROPERTY(config, BlueprintGetter = GetManageDialogueBox, EditAnywhere, Category = "User Interface", AdvancedDisplay)
	bool ManageDialogueBox{ true };

	/**
	 * If disabled, the Interpreter will not manage the lifecycle of the Selection Box,
	 * and its up to you to create, update, delete, etc. your own player selection widget.
	 * Assign to the Interpreter's OnPlaySelectionBox event.
	 */
	UPROPERTY(config, BlueprintGetter = GetManageSelectionBox, EditAnywhere, Category = "User Interface", AdvancedDisplay)
	bool ManageSelectionBox{ true };

	/**
	 * If disabled, the Interpreter will not manage the lifecycle of the Background Box,
	 * and its up to you to create, update, delete, etc. your own background widget.
	 * Assign your widget to the Interpreter's OnPlayBackgroundBox event.
	 */
	UPROPERTY(config, BlueprintGetter = GetManageBackgroundBox, EditAnywhere, Category = "User Interface", AdvancedDisplay)
	bool ManageBackgroundBox{ true };

	#pragma endregion UI


	/// Variables
	#pragma region Variables

	/** Default Quillscript variables. */
	UPROPERTY(config,  BlueprintGetter = GetDefaultVariables, EditAnywhere, Category = "Variables")
	TMap<FName, FText> DefaultVariables;

	/**
	 * Create a global Quillscript variable counter for each played statement with label name.
	 * {ScriptId.LabelName}
	 */
	UPROPERTY(config,  BlueprintGetter = GetKeepVisitedStatements, EditAnywhere, Category = "Variables")
	bool bKeepVisitedStatements{ false };

	/**
	 * Create a global Quillscript variable counter for each played label statement.
	 * {ScriptId.LabelName}
	 *
	 * ! If 'Keep Visited Statements' is on, the value of this setting is irrelevant.
	 */
	UPROPERTY(config,  BlueprintGetter = GetKeepVisitedLabels, EditAnywhere, Category = "Variables", meta = ( EditCondition = "!bKeepVisitedStatements" ))
	bool bKeepVisitedLabels{ false };

	/**
	 * Create a global Quillscript variable counter for each selected option statement that has a label name.
	 * {ScriptId.LabelName}
	 */
	UPROPERTY(config,  BlueprintGetter = GetKeepSelectedOptions, EditAnywhere, Category = "Variables")
	bool bKeepSelectedOptions{ false };

	/**
	 * Create a system Quillscript variable holding the last selected option text.
	 * {$option}
	 */
	UPROPERTY(config,  BlueprintGetter = GetKeepLastSelectedOptionText, EditAnywhere, Category = "Variables")
	bool bKeepLastSelectedOptionText{ false };

	#pragma endregion Variables


	/// History
	#pragma region History

	/** Maximum number of entries in the script flow history. (N <= 0 = Infinity entries) */
	UPROPERTY(config, BlueprintGetter = GetMaxHistoryEntries, EditAnywhere, Category = "History")
	int32 MaxHistoryEntries{ 100 };

	/**
	 * Keep script history after the script ends. By default, script history is cleaned after script's end.
	 *
	 * This is required in order for the UScene::Rollback() and UScene::GetVisitedLabels() functions to work.
	 *
	 * ! Disable this feature if your game wont use it, to avoid unnecessary memory and storage usage.
	 * ! Also, it is recommended to disable this feature in games with authoritative multiplayer mode, to prevent variables' value conflict.
	 */
	UPROPERTY(config, BlueprintGetter = GetKeepHistory, EditAnywhere, Category = "History")
	bool bKeepHistory{ false };

	#pragma endregion History


	/// Multiplayer
	#pragma region Multiplayer

	// /** Set how a script play behaves in multiplayer sessions. */
	// UPROPERTY(config, BlueprintGetter = GetMultiplayerMode, EditAnywhere, Category = "Multiplayer")
	// EMultiplayerMode MultiplayerMode{ EMultiplayerMode::None };
	//
	// /**
	//  * The distance radius other players Pawns/Characters must be to automatically joins a script play started by other player.
	//  *
	//  * -1 = Disable auto-join.
	//  * 0 = All players are auto-joined.
	//  * N = Only players within this radius are auto-joined.
	//  */
	// UPROPERTY(config, BlueprintGetter = GetAutoJoinRadius, EditAnywhere, Category = "Multiplayer", meta = ( EditCondition = "MultiplayerMode != EMultiplayerMode::None" ))
	// int32 AutoJoinRadius{ -1 };
	//
	// /** Set how an option is selected in multiplayer sessions. */
	// UPROPERTY(config, BlueprintGetter = GetMultiplayerSelectionMode, EditAnywhere, Category = "Multiplayer", meta = ( EditCondition = "MultiplayerMode != EMultiplayerMode::None" ))
	// EMultiplayerSelectionMode MultiplayerSelectionMode{ EMultiplayerSelectionMode::Host };
	//
	// /**
	//  * The time in seconds the players have to select an option when the 'Multiplayer Selection Mode' is set to 'Pool'.
	//  * Set to 0 to disable (Not recommended).
	//  */
	// UPROPERTY(config, BlueprintGetter = GetPoolTimer, EditAnywhere, Category = "Multiplayer", meta = ( EditCondition = "MultiplayerMode != EMultiplayerMode::None && MultiplayerSelectionMode == EMultiplayerSelectionMode::Poll" ))
	// uint8 PoolTimer{ 5 };

	#pragma endregion Multiplayer


	/// Lexer
	#pragma region Lexer

	/** Allow the parser to let repeated tags in the tags string array. */
	UPROPERTY(config, BlueprintGetter = GetRepeatedTags, EditAnywhere, Category = "Lexer")
	bool bRepeatedTags{ false };

	/**
	 * Store the source Quillscript text used to created that script asset.
	 * QuillscriptAssetRef.SourceText
	 */
	UPROPERTY(config, BlueprintGetter = GetStoreSourceCode, EditAnywhere, Category = "Lexer")
	bool bStoreSourceCode{ true };

	/**
	 * Store the source Quillscript line in that statement structure.
	 * Statement.SourceLine
	 */
	UPROPERTY(config, BlueprintGetter = GetStoreSourceLine, EditAnywhere, Category = "Lexer")
	bool bStoreSourceLine{ true };

	/**
	 * Store the source Quillscript inline comment in that statement structure.
	 * Statement.Comment
	 */
	UPROPERTY(config, BlueprintGetter = GetStoreInlineComment, EditAnywhere, Category = "Lexer")
	bool bStoreInlineComment{ true };

	#pragma endregion Lexer


	/// Editor
	#pragma region Editor

	/** Show plugin help messages. */
	UPROPERTY(config, BlueprintGetter = GetVerbosity, EditAnywhere, Category = "Editor")
	EVerbosityMode Verbosity{ EVerbosityMode::Full };

	/** Show plugin help messages in any playing mode. (By default, it only show while playing in editor) */
	UPROPERTY(config, BlueprintGetter = GetAlwaysPrintLog, EditAnywhere, Category = "Editor")
	bool bAlwaysPrintLog{ false };

	/** If the Editor should listen to changes in '.qsc' files in this project's folder and auto-update their respective 'Script Assets'. */
	UPROPERTY(config, BlueprintGetter = GetAutoReimportScripts, EditAnywhere, Category = "Editor")
	bool bAutoReimportScripts{ true };

	/** If the script asset should be reloaded from disk everytime a script line is played. (Requires 'Auto Reimport Scripts' setting enabled.) */
	UPROPERTY(config, BlueprintGetter = GetUpdateAtRuntime, EditAnywhere, Category = "Editor", meta = ( EditCondition = "bAutoReimportScripts" ))
	bool bUpdateAtRuntime{ true };

	/**
	 * System command for opening a 'Quillscript Script Asset' source file in a text editor.
	 * For example, if the OS is Windows and the editor is VSCode, this command should be something like:
	 *
	 *		start "C:\Users\<user>\AppData\Local\Programs\Microsoft VS Code\Code.exe"
	 */
	UPROPERTY(config, BlueprintGetter = GetScriptEditorCommand, EditAnywhere, Category = "Editor", AdvancedDisplay)
	FString ScriptEditorCommand;

	#pragma endregion Editor


	/// Internal Use
	#pragma region Internal

	// Current settings asset in use.
	static inline UQuillscriptSettings* SettingsAsset{ nullptr };

	/**
	 * Change any script setting set to 'Default' to its equivalent default value.
	 */
	void EnforceDefaults(FString ChangedPropertyName = "");

	#pragma endregion Internal
};