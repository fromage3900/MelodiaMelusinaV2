// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Base/Permission.h"

#include "CoreMinimal.h"
#include "Core/QuillscriptSubsystem.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Quill.generated.h"

enum class EPicker : uint8;
struct FScriptSettings;
class USaveGame;
class UQuillscriptAsset;
class AQuillscriptInterpreter;
class UQuillscriptSubsystem;

#pragma region Macros

/** Get the value of the named Quillscript variable. */
#define VAR(Name)				UQuill::GetQuillscriptVariable(this, Name)

/** Set the value of the named Quillscript variable. */
#define SET_VAR(Name, Value)	UQuill::SetQuillscriptVariable(this, Name, Value)

/** Set the value of the named Quillscript outer variable. */
#define SET_OUT(Name, Value)	UQuill::SetQuillscriptVariable(this, FName(SYMBOL(Out) + Name), Value)

/** Set the value of the named Quillscript template variable. */
#define SET_ARG(Name, Value)	UQuill::SetQuillscriptVariable(this, FName(SYMBOL(Arg) + Name), Value)

/** Replace all variables in string. */
#define REPLACE(Text)			UQuill::ReplaceQuillscriptVariables(this, Text)

/** Replace all variables in text. */
#define TEXT_REPLACE(Text)		FText::FromString(UQuill::ReplaceQuillscriptVariables(this, Text.ToString()))

/** Replace all variables in name. */
#define NAME_REPLACE(Text)		FName(UQuill::ReplaceQuillscriptVariables(this, Text.ToString()))

#pragma endregion Macros


/**
 * Collection of Quillscript related functions.
 */
UCLASS()
class QUILLSCRIPT_API UQuill final : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/// Script
	#pragma region Script

	/**
	 * Play the given Quillscript script asset.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject", AdvancedDisplay = 2 ))
	static AQuillscriptInterpreter* PlayScript(const UObject* WorldContextObject, UQuillscriptAsset* Script, const FName StartingLabel = NAME_None, UObject* Target = nullptr);

	/**
	 * Play script from start using custom settings instead of script settings.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject", AdvancedDisplay = 3 ))
	static AQuillscriptInterpreter* PlayScriptUsingCustomSettings(const UObject* WorldContextObject, UQuillscriptAsset* Script, FScriptSettings Settings, const FName StartingLabel = NAME_None, UObject* Target = nullptr);

	/**
	 * Play script from start. Delete any previous script history.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject", AdvancedDisplay = 2 ))
	static AQuillscriptInterpreter* StartScript(const UObject* WorldContextObject, UQuillscriptAsset* Script, const FName StartingLabel = NAME_None, UObject* Target = nullptr);

	/**
	 * Play script from start using custom settings instead of script settings. Delete any previous script history.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject", AdvancedDisplay = 3 ))
	static AQuillscriptInterpreter* StartScriptUsingCustomSettings(const UObject* WorldContextObject, UQuillscriptAsset* Script, FScriptSettings Settings, const FName StartingLabel = NAME_None, UObject* Target = nullptr);

	/**
	 * Play script from last history's save state entry.
	 * Used when the game was saved during a script play, and resume from that saved point.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject", AdvancedDisplay = 2 ))
	static AQuillscriptInterpreter* ResumeScript(const UObject* WorldContextObject, UQuillscriptAsset* Script);

	/**
	 * Parse a Quillscript text into a script object.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script", meta = ( AdvancedDisplay = "Permission" ))
	static UQuillscriptAsset* ParseScript(const FString Text, const EPermissionMode Permission = EPermissionMode::Safe);

	/**
	 * Get a list of all Quillscript script assets.
	 */
	UFUNCTION(BlueprintPure, Category="Quillscript|Script")
	static TArray<UQuillscriptAsset*> GetScripts();

	/**
	 * Get a Quillscript asset by path. (/Game/Folder/MyScript.MyScript)
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Script")
	static UQuillscriptAsset* GetScriptByPath(const FString& Path);

	/**
	 * Get a Quillscript asset by it's Id.
	 * ! This function may be slow on large project with thousands of assets.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Script")
	static UQuillscriptAsset* GetScriptById(const FName Id);

	/**
	 * Get a Quillscript asset
	 *
	 * By Id:				@MyScript
	 * By Path:				/Game/Folder/MyScript.MyScript
	 * By Script Reference: {&/Game/Folder/MyScript.MyScript}
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Script")
	static UQuillscriptAsset* FindScript(FString ScriptRef);

	/**
	 * Check if the given Quillscript script is currently playing.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject" ))
	static bool IsScriptPlaying(const UObject* WorldContextObject, const UQuillscriptAsset* Script);

	/**
	 * Check if any Quillscript script is currently playing.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject" ))
	static bool IsAnyScriptPlaying(const UObject* WorldContextObject);

	/**
	 * Make a list with all script permissions.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script")
	static TArray<EPermission> MakePermissionsList(const EPermissionMode PermissionMode);

	/**
	 * Reset the script 'Times Played' counter.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject" ))
	static void SetScriptPlayCounter(const UObject* WorldContextObject, const UQuillscriptAsset* Script, const int32 TimesPlayed);

	/**
	 * Set the script 'Times Played' counter.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Script", meta = ( WorldContext = "WorldContextObject" ))
	static void ResetScriptPlayCounter(const UObject* WorldContextObject, const UQuillscriptAsset* Script);

	#pragma endregion Script


	/// Interpreter
	#pragma region Interpreter

	/**
	 * Spawn an interpreter actor.
	 * Use this method instead of spawning it manually.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Interpreter", meta = ( WorldContext = "WorldContextObject", AdvancedDisplay = "InterpreterClass" ))
	static AQuillscriptInterpreter* CreateInterpreter(const UObject* WorldContextObject, TSubclassOf<AQuillscriptInterpreter> InterpreterClass = nullptr);

	/**
	 * Get all instantiated interpreter objects.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Interpreter", meta = ( WorldContext = "WorldContextObject" ))
	static TArray<AQuillscriptInterpreter*> GetInterpreters(const UObject* WorldContextObject);

	/**
	 * Get player owned Network object.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Interpreter", meta = ( WorldContext = "WorldContextObject" ))
	static AQuillscriptNetwork* GetNetwork(const UObject* WorldContextObject);

	#pragma endregion Interpreter


	/// Variables
	#pragma region Variables

	UFUNCTION(BlueprintPure, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static bool QuillscriptVariableExists(const UObject* WorldContextObject, const FName VariableName);

	/**
	 * Get the value of a Quillscript variable. Return "off" if does not it exists.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject", CompactNodeTitle = "Script Var" ))
	static FString GetQuillscriptVariable(const UObject* WorldContextObject, const FName VariableName);

	/**
	 * Get the value of a Quillscript variable as number.
	 * ! on = 1; off = 0; Text = 0
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject", CompactNodeTitle = "Script Var" ))
	static double GetQuillscriptNumber(const UObject* WorldContextObject, const FName VariableName);

	/**
	 * Get the value of a Quillscript variable as switch.
	 * ! on = on; true = on; 1 = on; everything else = off
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject", CompactNodeTitle = "Script Var" ))
	static bool GetQuillscriptSwitch(const UObject* WorldContextObject, const FName VariableName);

	/**
	 * Set the value of a Quillscript variable. Create it if it does not exists.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject", CompactNodeTitle = "Script Var" ))
	static void SetQuillscriptVariable(const UObject* WorldContextObject, const FName VariableName, FText Value);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject", CompactNodeTitle = "Script Var" ))
	static void SetQuillscriptVariables(const UObject* WorldContextObject, const TMap<FName, FText> Variables);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject", CompactNodeTitle = "++" ))
	static void IncrementQuillscriptVariable(const UObject* WorldContextObject, const FName VariableName);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static bool DeleteQuillscriptVariable(const UObject* WorldContextObject, const FName Name);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static FString ReplaceQuillscriptVariables(const UObject* WorldContextObject, const FString String);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static void SetTemporaryVariables(const UObject* WorldContextObject, const TMap<FName, FText> Variables);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static bool RenameQuillscriptVariable(const UObject* WorldContextObject, const FName OldName, const FName NewName);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static bool IsConstant(const UObject* WorldContextObject, const FName Name);

	/**
	 * Find all global variables and constants declarations in script assets.
	 * ! This function can be slow if too many script lines to check.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables")
	static TArray<FName> GetAllProjectGlobals();


	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static void AddScriptReference(const UObject* WorldContextObject, const FName Name, UObject* Reference);

	/**
	 * Remove all occurrences of the given pointer from script references map.
	 * ! Not efficient with big reference maps.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static bool RemoveScriptReference(const UObject* WorldContextObject, const UObject* Reference);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static bool RemoveScriptReferenceByName(const UObject* WorldContextObject, const FName Name);

	/**
	 * Remove all null pointer from script references map.
	 * ! Not efficient with big reference maps.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static void ClearNullScriptReferences(const UObject* WorldContextObject);

	/**
	 * ! It is not required for the variable to exist for a modifier to work.
	 *
	 * @param WorldContextObject
	 * @param VariableName			Name of the variable to be registered.
	 * @param Delegate				Delegate to be called when the variable is accessed.
	 * @param InitializeVariable	If the variable does not exists, it will be created with this value. Leave empty to not create it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject", AdvancedDisplay = "InitializeVariable" ))
	static void RegisterVariableModifier(const UObject* WorldContextObject, const FName VariableName, const FVariableGetDelegate& Delegate, const FText InitializeVariable = FText());

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Variables", meta = ( WorldContext = "WorldContextObject" ))
	static void UnregisterVariableModifier(const UObject* WorldContextObject, const FName VariableName);

	#pragma endregion Variables


	/// Save and Load
	#pragma region Save

	/**
	 * Clear all Quillscript variables, script history, script references, variable modifiers and injected options.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Save", meta = ( WorldContext = "WorldContextObject" ))
	static void RefreshQuillscript(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Save", meta = ( WorldContext = "WorldContextObject" ))
	static bool SaveGameAndStoryToSlot(const UObject* WorldContextObject, USaveGame* SaveGameObject, const FString SlotName, const int32 UserIndex);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Save", meta = ( WorldContext = "WorldContextObject" ))
	static USaveGame* LoadGameAndStoryFromSlot(const UObject* WorldContextObject, const FString SlotName, const int32 UserIndex);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Save", meta = ( WorldContext = "WorldContextObject" ))
	static USaveGame* ResumeGameAndStoryFromSlot(const UObject* WorldContextObject, const FString SlotName, const int32 UserIndex);

	#pragma endregion Save


	/// Pipes
	#pragma region Pipes

	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes")
	static FString EvaluateQuillscriptExpression(const FString& Expression);

	UFUNCTION(BlueprintPure, Category = "Quillscript|Pipes")
	static bool PickerToBoolean(const EPicker Picker);

	#pragma endregion Pipes
};