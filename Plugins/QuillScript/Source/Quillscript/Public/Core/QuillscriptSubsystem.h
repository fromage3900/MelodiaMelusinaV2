// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Base/History.h"

#include "CoreMinimal.h"
#include "Base/Statement.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "QuillscriptSubsystem.generated.h"

class AQuillscriptInterpreter;
class AQuillscriptNetwork;
class FMemoryWriter;
class FMemoryReader;

DECLARE_DYNAMIC_DELEGATE_TwoParams( FVariableGetDelegate, const FName&, VariableName, const FString&, VariableValue );

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam( FScriptPlayDelegate, AQuillscriptInterpreter*, Interpreter );
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam( FScriptEndDelegate, FName, ScriptId );
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam( FNotificationDelegate, FString, Message );
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams( FVariableSetDelegate, FName, VariableName, FText, OldValue, FText, NewValue );

/**
 * Quillscript Game Instance Subsystem.
 */
UCLASS()
class QUILLSCRIPT_API UQuillscriptSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UQuillscriptSubsystem();
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;


	#pragma region References

	/**
	 * Get a non-safe, unreliable, reference to world.
	 * Should only be used when can't get the 'World Context Object' through other means for editor only functions.
	 */
	static UWorld* World(const UObject* WorldContextObject = nullptr);

	#pragma endregion References


	/// Data
	#pragma region Data

	UPROPERTY(BlueprintReadWrite, Category = "Quillscript|Data")
	TArray<FStatement> InjectOptions;

	void AppendDefaultValues(const TMap<FName, FText>& DefaultVariables, TMap<FName, FSoftObjectPath> DefaultScriptReferences);

	#pragma endregion Data


	/// Save and Load
	#pragma region SaveLoad

	void SerializeQuillscriptData(FMemoryWriter& Ar);
	void DeserializeQuillscriptData(FMemoryReader& Ar);

	void InjectQuillscriptDataIntoSaveGame(TArray<uint8>& SaveGameBytesToInjectInto);
	void ExtractQuillscriptDataFromSaveGame(TArray<uint8>& SaveGameBytesToExtractFrom);

	#pragma endregion SaveLoad


	/// Getters and Setters.
	#pragma region GetSet

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TMap<FName, FText>& GetVariables() { return this->Variables; }

	UFUNCTION(BlueprintSetter)
	FORCEINLINE void SetVariables(const TMap<FName, FText>& Value) { this->Variables = Value; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TMap<FName, FHistory>& GetHistory() { return this->History; }

	UFUNCTION(BlueprintSetter)
	FORCEINLINE void SetHistory(const TMap<FName, FHistory>& Value) { this->History = Value; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TMap<FName, UObject*>& GetReferences() { return this->References; }

	FORCEINLINE TMap<FName, FVariableGetDelegate>& GetVariablesModifiers() { return this->VariablesModifiers; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TArray<AQuillscriptNetwork*> GetNetworks() { return this->Networks; }

	FORCEINLINE bool GetBypassConditions() const { return this->bBypassConditions; }
	FORCEINLINE void SetBypassConditions(const bool Value) { this->bBypassConditions = Value; }

	#pragma endregion GetSet


	/// Events
	#pragma region Events

	/** A script is playing. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FScriptPlayDelegate OnScriptPlay;

	/** A script ended playing. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FScriptEndDelegate OnScriptEnd;

	/** Script notification fired. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FNotificationDelegate OnNotified;

	/** Variable changed event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FVariableSetDelegate OnVariableSet;

	#pragma endregion Events


private:
	/// References
	#pragma region References

	inline static TObjectPtr<UQuillscriptSubsystem> Self{ nullptr };

	#pragma endregion References


	/// Data
	#pragma region Data

	/** Quillscript variables. */
	UPROPERTY(BlueprintGetter = GetVariables, BlueprintSetter = SetVariables, Category = "Data")
	TMap<FName, FText> Variables;

	/** Quillscript history. */
	UPROPERTY(BlueprintGetter = GetHistory, BlueprintSetter = SetHistory, Category = "Data")
	TMap<FName, FHistory> History;

	/** Map of object references to be used in script. ( &ReferenceName.MyFunction or {&ReferenceName} ) */
	UPROPERTY(BlueprintGetter = GetReferences, Category = "Data")
	TMap<FName, UObject*> References;

	/** Map of Variables' modifiers delegates. */
	TMap<FName, FVariableGetDelegate> VariablesModifiers;

	/** Container to store History as a string and serialize it to save file. */
	UPROPERTY()
	FString HistoryAsString;
	FString FooData{ "foo" };

	/** Store a Quillscript Network for each connected player. (Host only) */
	UPROPERTY(BlueprintGetter = GetNetworks, Category = "Data")
	TArray<AQuillscriptNetwork*> Networks;

	void CreateNetworksForPlayers();

	#pragma endregion Data


	/// State
	#pragma region State

	/** If Quillscript Statement's conditions should be ignored. */
	bool bBypassConditions{ false };

	#pragma endregion State
};