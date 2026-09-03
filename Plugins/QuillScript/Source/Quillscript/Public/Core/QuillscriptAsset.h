// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Base/Permission.h"
#include "Base/ScriptIdMethod.h"
#include "Base/ScriptSettings.h"
#include "Base/Statement.h"
#include "UObject/Object.h"
#include "QuillscriptAsset.generated.h"

struct FSaveState;
struct FHistory;

/**
 * Asset to store and organize Quillscript's script related data.
 */
UCLASS(BlueprintType)
class QUILLSCRIPT_API UQuillscriptAsset final : public UObject
{
	GENERATED_BODY()

public:
	UQuillscriptAsset();

	/** Settings used for this scene. */
	UPROPERTY(EditDefaultsOnly, Category = "Quillscript|Settings")
	FScriptSettings Settings;


	/// Editor data
	#if WITH_EDITORONLY_DATA

	UPROPERTY(VisibleAnywhere, Instanced, DisplayName = "Source File", Category = ImportSettings)
	UAssetImportData* AssetImportData;

	#endif


	/// Editor
	#if WITH_EDITOR

	virtual void PostInitProperties() override;
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
	void ReimportScript();

	#endif


	/// Data
	#pragma region Data

	/**
	 * Create a ready to use copy of this script. Resolving directives, settings, and other setup tasks.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Data")
	UQuillscriptAsset* CreateReadyToPlayCopy();

	/**
	 * Look for start directives, or return 0 otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Data", meta = ( WorldContext = "WorldContextObject" ))
	int32 GetStartingIndex(const UObject* WorldContextObject) const;

	/**
	 * Check if this script was created during runtime (transient).
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Data")
	bool IsCreatedDuringRuntime() const;

	/**
	 * Find a script reference like '{&/Folder/AssetName.AssetName}' or using search paths.
	 */
	UObject* FindScriptReference(const FString& ReferencePath) const;

	/**
	 * Update this script's packaging references.
	 */
	void UpdatePackagingReferences();

	#pragma endregion Data


	/// Statements
	#pragma region Statements

	/**
	 * Fill statements array.
	 *
	 * @param	InSourceCode	Valid Quillscript language text.
	 */
	void SetContent(const FString& InSourceCode);

	/**
	 * Find if there is a Quillscript variable called ScriptId.LabelName for the given statement.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Statements")
	FName GetStatementVariableName(const int32 StatementIndex) const;

	FName MakeStatementVariableName(const FName LabelName) const;

	/**
	 * Check there is a Quillscript variable for this statement, meaning that it was executed at least once.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Statements", meta = ( WorldContext = "WorldContextObject" ))
	bool IsStatementVisited(const UObject* WorldContextObject, const int32 StatementIndex) const;

	/**
	 * Check if a Label have a variable with its name, meaning that it was executed at least once.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Statements", meta = ( WorldContext = "WorldContextObject" ))
	void IncrementStatementVisitCounter(const UObject* WorldContextObject, const int32 StatementIndex) const;

	/**
	 * Delete all Quillscript variables starting with "ScriptId.".
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Statements", meta = ( WorldContext = "WorldContextObject" ))
	void DeleteAllStatementVisitVariables(const UObject* WorldContextObject) const;

	UFUNCTION(BlueprintPure, Category = "Quillscript|Statements")
	int32 GetStatementIndexByLabel(const FName Label) const;

	UFUNCTION(BlueprintPure, Category = "Quillscript|Statements")
	FStatement GetStatementByLabel(const FName Label) const;

	/**
	 * Check if the given label name exists somewhere in this script.
	 * @see GetStatementIndexByLabel
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Statements")
	bool IsLabelName(const FName LabelName) const;

	#pragma endregion Statements


	/// History
	#pragma region History

	UFUNCTION(BlueprintPure, Category = "Quillscript|History", meta = ( WorldContext = "WorldContextObject" ))
	bool HistoryExists(const UObject* WorldContextObject) const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|History", meta = ( WorldContext = "WorldContextObject" ))
	void CreateHistory(const UObject* WorldContextObject) const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|History", meta = ( WorldContext = "WorldContextObject" ))
	FHistory& FindHistory(const UObject* WorldContextObject) const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|History", meta = ( WorldContext = "WorldContextObject" ))
	void PushToHistory(const UObject* WorldContextObject, const FSaveState NewEntry) const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|History", meta = ( WorldContext = "WorldContextObject" ))
	void DeleteHistory(const UObject* WorldContextObject) const;

	#pragma endregion History


	/// Getters and Setters
	#pragma region GetSet

	UFUNCTION(BlueprintGetter)
	FORCEINLINE EScriptIdMethod GetIdMethod() const { return this->IdMethod; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE FName GetId() const { return this->Id; }

	UFUNCTION(BlueprintSetter)
	FORCEINLINE void SetSettings(const FScriptSettings& Value) { this->Settings = Value; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetMaxHistoryEntries() const { return this->MaxHistoryEntries; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE UObject* GetTarget() const { return this->Target.Get(); }

	UFUNCTION(BlueprintSetter)
	FORCEINLINE void SetTarget(UObject* Value) { this->Target = Value; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TArray<FStatement> GetStatements() const { return this->Statements; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TArray<FDirectoryPath> GetReferencePaths() const { return this->ReferencePaths; }

	FORCEINLINE TArray<EPermission> GetPermissions() const { return this->Permissions; }
	FORCEINLINE void SetPermissions(const TArray<EPermission>& Value) { this->Permissions = Value; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE FString GetSourceCode() const { return this->SourceCode; }

	#pragma endregion GetSet


private:
	/// Editor
	#if WITH_EDITOR

	/**
	 * Update this script ID according to ID method.
	 */
	void UpdateId();

	/**
	 * Format 'Original Path' to be a script id.
	 * Ex.: /Game/Folder/Asset.Asset -> Game/Folder/Asset
	 */
	FName GetScriptIdAsPath() const;

	#endif


	/// Settings
	#pragma region Settings

	/** Id method used to reference this script in other scripts and by the interpreter. */
	UPROPERTY(EditDefaultsOnly, BlueprintGetter = GetIdMethod, Category = "Quillscript|Settings")
	EScriptIdMethod IdMethod{ EScriptIdMethod::Name };

	/** Use this to set a custom Id */
	UPROPERTY(EditDefaultsOnly, BlueprintGetter = GetId, Category = "Quillscript|Settings", meta = ( EditCondition = "IdMethod == EScriptIdMethod::Custom" ))
	FName Id;

	/** Override maximum number of entries in the script history, for this script. (N <= 0 = Use Quillscript default value) */
	UPROPERTY(EditDefaultsOnly, BlueprintGetter = GetMaxHistoryEntries, Category = "Quillscript|Settings")
	int32 MaxHistoryEntries{ 0 };

	UPROPERTY(EditDefaultsOnly, Category = "Quillscript|Settings")
	TWeakObjectPtr<UObject> Target;

	/** List of allowed tasks this script can perform. */
	UPROPERTY(EditDefaultsOnly, Category = "Quillscript|Settings", meta = ( LongPackageName ))
	TArray<FDirectoryPath> ReferencePaths;

	/** List of allowed tasks this script can perform. */
	TArray<EPermission> Permissions;

	/**
	 * Merge script local settings with default settings.
	 */
	void MergeSettings();

	#pragma endregion Settings


	/// Data
	#pragma region Data

	UPROPERTY(VisibleDefaultsOnly, BlueprintGetter = GetStatements, Category = "Quillscript|Data")
	TArray<FStatement> Statements;

	/**
	 * Resolve all ~Directives in this script and overrides its 'Statements' property with the resulting script.
	 */
	void ResolveDirectives();

	void AddToReplacementMap(const FString& Directive);
	void ResolveIncludeDirective(FString ScriptPath, const int32 Index);
	void ResolveImportDirective(FString ScriptPath);
	void ResolveInjectDirective(FString ScriptPath, const int32 Index);

	TArray<FString> IncludedScripts;
	TMap<FString, FString> ReplacementMap;
	FStatement ReplaceInStatement(FStatement Statement) const;

	#pragma endregion Data


	/// Metadata
	#pragma region Metadata

	/** Source Quillscript language text used to set this script. (Must be UProperty)  */
	UPROPERTY(BlueprintGetter = GetSourceCode, Category = "Quillscript|Metadata")
	FString SourceCode;

	/**
	 * List all references directly linked by this script like '{&/Folder/AssetName.AssetName}' or using search paths.
	 * This is useful for the packaging process to know which assets are referenced by this script text and package them.
	 */
	UPROPERTY()
	TArray<FSoftObjectPath> PackagingReferences;

	#pragma endregion Metadata
};