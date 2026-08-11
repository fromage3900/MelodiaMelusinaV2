// Copyright Bruno Caxito. All Rights Reserved.

#include "Utils/Quill.h"

#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Core/QuillscriptAsset.h"
#include "Core/QuillscriptInterpreter.h"
#include "Core/QuillscriptNetwork.h"
#include "Core/QuillscriptSettings.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/GameplayStatics.h"
#include "Utils/Evaluator.h"
#include "Utils/Lexer.h"
#include "Utils/Tools.h"


#pragma region Script

AQuillscriptInterpreter* UQuill::PlayScript(const UObject* WorldContextObject, UQuillscriptAsset* Script, const FName StartingLabel, UObject* Target)
{
	if (Script)
	{
		if (AQuillscriptInterpreter* Interpreter{ CreateInterpreter(WorldContextObject, Script->Settings.InterpreterClass) })
		{
			Script->SetTarget(Target);
			Interpreter->Start(Script, StartingLabel);
			return Interpreter;
		}
	}

	return nullptr;
}

AQuillscriptInterpreter* UQuill::PlayScriptUsingCustomSettings(const UObject* WorldContextObject, UQuillscriptAsset* Script, const FScriptSettings Settings, const FName StartingLabel, UObject* Target)
{
	if (Script)
	{
		Script = Script->CreateReadyToPlayCopy();
		Script->SetSettings(Settings);
	}

	return PlayScript(WorldContextObject, Script, StartingLabel, Target);
}

AQuillscriptInterpreter* UQuill::StartScript(const UObject* WorldContextObject, UQuillscriptAsset* Script, const FName StartingLabel, UObject* Target)
{
	if (Script)
	{
		Script->DeleteHistory(WorldContextObject);
		return PlayScript(WorldContextObject, Script, StartingLabel, Target);
	}

	return nullptr;
}

AQuillscriptInterpreter* UQuill::StartScriptUsingCustomSettings(const UObject* WorldContextObject, UQuillscriptAsset* Script, const FScriptSettings Settings, const FName StartingLabel, UObject* Target)
{
	if (Script)
	{
		Script = Script->CreateReadyToPlayCopy();
		Script->SetSettings(Settings);
	}

	return StartScript(WorldContextObject, Script, StartingLabel, Target);
}

AQuillscriptInterpreter* UQuill::ResumeScript(const UObject* WorldContextObject, UQuillscriptAsset* Script)
{
	if (Script)
	{
		if (AQuillscriptInterpreter* Interpreter{ CreateInterpreter(WorldContextObject, Script->Settings.InterpreterClass) })
		{
			Interpreter->Start(Script, NAME_None, true);
			return Interpreter;
		}
	}

	return nullptr;
}

UQuillscriptAsset* UQuill::ParseScript(const FString Text, const EPermissionMode Permission)
{
	UQuillscriptAsset* Script{ NewObject<UQuillscriptAsset>() };

	if (Script)
	{
		Script->SetPermissions(MakePermissionsList(Permission));
		Script->SetContent(Text);
	}

	return Script;
}

TArray<UQuillscriptAsset*> UQuill::GetScripts()
{
	TArray<UQuillscriptAsset*> List;

	// Get all script assets by class.
	const FAssetRegistryModule& AssetRegistryModule{ FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry") };
	const FTopLevelAssetPath AssetPath{ UQuillscriptAsset::StaticClass()->GetPathName() };

	TArray<FAssetData> AssetsData;
	AssetRegistryModule.Get().GetAssetsByClass(AssetPath, AssetsData);

	// Populate list.
	for (FAssetData AssetData : AssetsData)
		List.Add(Cast<UQuillscriptAsset>(AssetData.GetAsset()));

	return List;
}

UQuillscriptAsset* UQuill::GetScriptByPath(const FString& Path)
{
	const FAssetRegistryModule& AssetRegistryModule{ FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry") };
	const FSoftObjectPath AssetPath{ Path };

	if (const FAssetData AssetData{ AssetRegistryModule.Get().GetAssetByObjectPath(AssetPath, true) }; AssetData.GetAsset())
		if (UQuillscriptAsset* Script{ Cast<UQuillscriptAsset>(AssetData.GetAsset()) })
			return Script;

	UTools::Error("Invalid script path: '" + Path + "'; Check if the path is right or script was saved after first creation.");
	return nullptr;
}

UQuillscriptAsset* UQuill::GetScriptById(const FName Id)
{
	const FAssetRegistryModule& AssetRegistryModule{ FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry") };
	const FTopLevelAssetPath AssetPath{ UQuillscriptAsset::StaticClass()->GetPathName() };

	TArray<FAssetData> OutAssetData;
	AssetRegistryModule.Get().GetAssetsByClass(AssetPath, OutAssetData, true);

	for (FAssetData AssetData : OutAssetData)
		if (UQuillscriptAsset* Script{ Cast<UQuillscriptAsset>(AssetData.GetAsset()) })
			if (Script->GetId() == Id)
				return Script;

	UTools::Error("Invalid script ID: '" + Id.ToString() + "'; Check if the ID is correct or script was saved after created.");
	return nullptr;
}

UQuillscriptAsset* UQuill::FindScript(FString ScriptRef)
{
	// Find Script by id.
	if (ScriptRef.RemoveFromStart(SYMBOL(Label)))
		if (const TObjectPtr<UQuillscriptAsset> Script{ GetScriptById(FName(ScriptRef)) })
			return  Script;

	// Clean Script Reference symbols.
	ScriptRef.RemoveFromStart(SYMBOL(CurlyOpen) + SYMBOL(Reference));
	ScriptRef.RemoveFromEnd(SYMBOL(CurlyClose));

	// Find Script by path.
	if (const TObjectPtr<UQuillscriptAsset> Script{ GetScriptByPath(ScriptRef) })
		return Script;


	UTools::Error("UQuill::GetScript() -> Script not found: " + ScriptRef);
	return nullptr;
}

bool UQuill::IsScriptPlaying(const UObject* WorldContextObject, const UQuillscriptAsset* Script)
{
	if (Script)
		for (const auto& Interpreter : GetInterpreters(WorldContextObject))
			if (Interpreter->GetScript()->GetId() == Script->GetId())
				return true;

	return false;
}

bool UQuill::IsAnyScriptPlaying(const UObject* WorldContextObject)
{
	return !GetInterpreters(WorldContextObject).IsEmpty();
}

TArray<EPermission> UQuill::MakePermissionsList(const EPermissionMode PermissionMode)
{
	switch (PermissionMode)
	{
	case EPermissionMode::All:
		{
			TArray<EPermission> AllPermissions;
			for (EPermission Permission : TEnumRange<EPermission>())
				AllPermissions.Add(Permission);

			return AllPermissions;
		}

	case EPermissionMode::Safe:
		return TArray{
			EPermission::PlayDialogues,
			EPermission::PlaySelections,
			EPermission::PlayRouters,
			EPermission::PlayDirectives
		};

	case EPermissionMode::Sandbox:
		return TArray{
			EPermission::CallBuiltInFunctions,
			EPermission::CreateTemporaryVariables,
			EPermission::ModifyTemporaryVariables,
			EPermission::DeleteTemporaryVariables,
			EPermission::PlayDialogues,
			EPermission::PlaySelections,
			EPermission::PlayRouters,
			EPermission::PlayDirectives
		};

	default: return TArray<EPermission>();
	}
}

void UQuill::SetScriptPlayCounter(const UObject* WorldContextObject, const UQuillscriptAsset* Script, const int32 TimesPlayed)
{
	if (WorldContextObject && Script)
	{
		if (const TObjectPtr<UQuillscriptSubsystem> QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		{
			// Update existent variable.
			if (TMap<FName, FHistory>& History{ QuillscriptSubsystem->GetHistory() }; History.Contains(Script->GetId()))
				History[Script->GetId()].TimesPlayed = TimesPlayed;

			// Create a new history entry.
			else if (TimesPlayed > 0)
			{
				FHistory NewEntry;
				NewEntry.ScriptId = Script->GetId();
				NewEntry.TimesPlayed = TimesPlayed;

				History.Add(Script->GetId(), NewEntry);
			}

			UTools::Success("UQuill::SetScriptPlayCounter() -> Script Times Played set: [ " + Script->GetId().ToString() + " = " + FString::FromInt(TimesPlayed) + " ]");
		}
	}
}

void UQuill::ResetScriptPlayCounter(const UObject* WorldContextObject, const UQuillscriptAsset* Script)
{
	SetScriptPlayCounter(WorldContextObject, Script, 0);
}

#pragma endregion Script


#pragma region Interpreter

AQuillscriptInterpreter* UQuill::CreateInterpreter(const UObject* WorldContextObject, TSubclassOf<AQuillscriptInterpreter> InterpreterClass)
{
	if (!WorldContextObject)
	{ UTools::Error("UQuill::CreateInterpreter() -> World Context Object can't be null."); return nullptr; }


	// Set interpreter class.
	if (!InterpreterClass)
		InterpreterClass = UQuillscriptSettings::Get()->GetScriptSettings().InterpreterClass;

	// Spawn interpreter actor.
	return WorldContextObject->GetWorld()->SpawnActor<AQuillscriptInterpreter>(InterpreterClass);
}

TArray<AQuillscriptInterpreter*> UQuill::GetInterpreters(const UObject* WorldContextObject)
{
	TArray<AQuillscriptInterpreter*> Interpreters;

	if (WorldContextObject)
	{
		TArray<AActor*> Actors;
		UGameplayStatics::GetAllActorsOfClass(WorldContextObject, AQuillscriptInterpreter::StaticClass(), Actors);

		for (AActor* Actor : Actors)
			Interpreters.Add(Cast<AQuillscriptInterpreter>(Actor));
	}

	return Interpreters;
}

AQuillscriptNetwork* UQuill::GetNetwork(const UObject* WorldContextObject)
{
	// Get network by player state.
	if (WorldContextObject && WorldContextObject->GetWorld())
	{
		TArray<AActor*> Networks;
		UGameplayStatics::GetAllActorsOfClass(WorldContextObject, AQuillscriptNetwork::StaticClass(), Networks);

		if (const auto* PlayerState{ UGameplayStatics::GetPlayerController(WorldContextObject, 0)->GetPlayerState<APlayerState>() })
			for (auto* Actor : Networks)
				if (AQuillscriptNetwork* Network{ Cast<AQuillscriptNetwork>(Actor) })
					if (Network->GetOwner() == PlayerState)
						return Network;
	}

	return nullptr;
}

#pragma endregion Interpreter


#pragma region Variables

bool UQuill::QuillscriptVariableExists(const UObject* WorldContextObject, const FName VariableName)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		return QuillscriptSubsystem->GetVariables().Contains(VariableName);

	return false;
}

FString UQuill::GetQuillscriptVariable(const UObject* WorldContextObject, const FName VariableName)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		// Call variable modifier.
		if (const auto* Delegate{ QuillscriptSubsystem->GetVariablesModifiers().Find(VariableName) })
		{
			FString Value;

			if (const FText* Text{ QuillscriptSubsystem->GetVariables().Find(VariableName) })
				Value = Text->ToString();

			Delegate->Execute(VariableName, Value);
		}

		// Find variable.
		if (const FText* Variable{ QuillscriptSubsystem->GetVariables().Find(VariableName) })
			return Variable->ToString();
	}

	// Nonexistent variable
	UTools::Warning("Nonexistent variable: '" + VariableName.ToString() + "'");
	return SYMBOL(Off);
}

double UQuill::GetQuillscriptNumber(const UObject* WorldContextObject, const FName VariableName)
{
	return FEvaluator::OperandToNumber(GetQuillscriptVariable(WorldContextObject, VariableName));
}

bool UQuill::GetQuillscriptSwitch(const UObject* WorldContextObject, const FName VariableName)
{
	return FEvaluator::OperandToBoolean(GetQuillscriptVariable(WorldContextObject, VariableName));
}

void UQuill::SetQuillscriptVariable(const UObject* WorldContextObject, const FName VariableName, FText Value)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		if (VariableName.IsNone() || Value.IsEmpty())
		{ UTools::Error("'Variable Name' and 'Value' can't be empty."); return; }

		// Get current value.
		FText OldValue;

		if (const FText* ValuePtr{ QuillscriptSubsystem->GetVariables().Find(VariableName) })
			OldValue = *ValuePtr;

		// Remove decimal.
		FString String{ Value.ToString() };
		String.RemoveFromEnd(".0");
		String.RemoveFromEnd(".000000");
		Value = FText::FromString(String);

		// Update existent variable.
		TMap<FName, FText>& Variables{ QuillscriptSubsystem->GetVariables() };

		if (FText* Variable{ Variables.Find(VariableName) })
		{
			// Stop if is actually a constant.
			if (IsConstant(WorldContextObject, VariableName))
			{
				UTools::Warning("Can't change a constant: '" + VariableName.ToString().ToUpper() + "'");
				return;
			}

			*Variable = Value;
		}

		// Create new variable.
		else
			Variables.Add(VariableName, Value);

		// Broadcast event.
		if (const TObjectPtr<UQuillscriptSubsystem> Subsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
			Subsystem->OnVariableSet.Broadcast(VariableName, OldValue, Value);

		UTools::Success("Variable set: [ " + VariableName.ToString() + " = " + Value.ToString() + " ]");
	}
}

void UQuill::SetQuillscriptVariables(const UObject* WorldContextObject, const TMap<FName, FText> Variables)
{
	for (const TPair<FName, FText>& Variable : Variables)
		SetQuillscriptVariable(WorldContextObject, Variable.Key, Variable.Value);
}

void UQuill::IncrementQuillscriptVariable(const UObject* WorldContextObject, const FName VariableName)
{
	double Value{ 1 };

	if (QuillscriptVariableExists(WorldContextObject, VariableName))
		Value = GetQuillscriptNumber(WorldContextObject, VariableName) + 1;

	SetQuillscriptVariable(
		WorldContextObject,
		VariableName,
		FText::FromString(FString::SanitizeFloat(Value))
	);
}

bool UQuill::DeleteQuillscriptVariable(const UObject* WorldContextObject, const FName Name)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		// Get current value.
		const FText OldValue{ *QuillscriptSubsystem->GetVariables().Find(Name) };

		// Delete.
		const int32 Deleted{ QuillscriptSubsystem->GetVariables().Remove(Name) };

		// Broadcast.
		if (const TObjectPtr<UQuillscriptSubsystem> Subsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
			Subsystem->OnVariableSet.Broadcast(Name, OldValue, FText());

		return Deleted > 0;
	}

	return false;
}

FString UQuill::ReplaceQuillscriptVariables(const UObject* WorldContextObject, const FString String)
{
	TMap<FName, FString> QuillscriptVariables;

	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		for (TMap<FName, FText>& Variables{ QuillscriptSubsystem->GetVariables() }; TTuple<FName, FText>& Variable : Variables)
			QuillscriptVariables.Add(Variable.Key, Variable.Value.ToString());

	return UTools::ReplaceVariables(WorldContextObject, String, QuillscriptVariables, TArray<UStringTable*>(), SYMBOL(Off));
}

void UQuill::SetTemporaryVariables(const UObject* WorldContextObject, const TMap<FName, FText> Variables)
{
	for (const TPair<FName, FText>& Variable : Variables)
		SetQuillscriptVariable(WorldContextObject, FName(SYMBOL(Temp) + Variable.Key.ToString()), Variable.Value);
}

bool UQuill::RenameQuillscriptVariable(const UObject* WorldContextObject, const FName OldName, const FName NewName)
{
	if (!OldName.IsEqual(NewName, ENameCase::CaseSensitive))
	{
		if (QuillscriptVariableExists(WorldContextObject, OldName))
		{
			SetQuillscriptVariable(WorldContextObject, NewName, FText::FromString(GetQuillscriptVariable(WorldContextObject, OldName)));
			DeleteQuillscriptVariable(WorldContextObject, OldName);

			return true;
		}

		UTools::Warning("Variable doesn't exist: '" + OldName.ToString() + "'");
	}

	return false;
}

bool UQuill::IsConstant(const UObject* WorldContextObject, const FName Name)
{
	if (QuillscriptVariableExists(WorldContextObject, Name))
	{
		if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		{
			TArray<FName> Keys;
			QuillscriptSubsystem->GetVariables().GenerateKeyArray(Keys);

			const FString String{ Keys[Keys.Find(Name)].ToString() };
			const FString UpperString{ String.ToUpper() };

			if (String.Equals(UpperString, ESearchCase::CaseSensitive))
				return true;
		}
	}

	return false;
}

TArray<FName> UQuill::GetAllProjectGlobals()
{
	TArray<FName> Variables;

	for (const UQuillscriptAsset* Script : GetScripts())
		for (const FStatement& Statement : Script->GetStatements())
			for (const FExpression& Command : Statement.Commands)
				if (Command.IsAssignment())
					Variables.AddUnique(FName(Command.GetVariableName()));

	return Variables;
}

void UQuill::AddScriptReference(const UObject* WorldContextObject, const FName Name, UObject* Reference)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		// Remove previous script reference of the same name, if any.
		RemoveScriptReferenceByName(WorldContextObject, Name);

		// Add new script reference.
		QuillscriptSubsystem->GetReferences().Add(Name, Reference);
		UTools::Success("Script Reference added: " + Name.ToString() + " -> " + Reference->GetName());
	}
}

bool UQuill::RemoveScriptReference(const UObject* WorldContextObject, const UObject* Reference)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		TMap<FName, UObject*>& References{ QuillscriptSubsystem->GetReferences() };
		TArray<FName> ReferencesNames;
		References.GenerateKeyArray(ReferencesNames);

		for (FName ReferenceName : ReferencesNames)
		{
			if (const UObject* TempReference{ *References.Find(ReferenceName) })
			{
				if (TempReference == Reference)
				{
					if (References.Remove(ReferenceName) > 0)
					{
						UTools::Success("Script Reference removed: " + Reference->GetName());
						return true;
					}
				}
			}
		}
	}

	return false;
}

bool UQuill::RemoveScriptReferenceByName(const UObject* WorldContextObject, const FName Name)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		if (QuillscriptSubsystem->GetReferences().Remove(Name) > 0)
		{
			UTools::Success("Script Reference removed: " + Name.ToString());
			return true;
		}
	}

	return false;
}

void UQuill::ClearNullScriptReferences(const UObject* WorldContextObject)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		TMap<FName, UObject*>& References{ QuillscriptSubsystem->GetReferences() };
		TArray<FName> ReferencesNames;
		References.GenerateKeyArray(ReferencesNames);

		for (FName ReferenceName : ReferencesNames)
			if (!*References.Find(ReferenceName))
				References.Remove(ReferenceName);
	}
}

void UQuill::RegisterVariableModifier(const UObject* WorldContextObject, const FName VariableName, const FVariableGetDelegate& Delegate, const FText InitializeVariable)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		// Create a variable if it doesn't exist.
		if (!InitializeVariable.IsEmpty() && !QuillscriptSubsystem->GetVariables().Contains(VariableName))
			SetQuillscriptVariable(WorldContextObject, VariableName, InitializeVariable);

		// Add variable modifier.
		QuillscriptSubsystem->GetVariablesModifiers().Add(VariableName, Delegate);
	}
}

void UQuill::UnregisterVariableModifier(const UObject* WorldContextObject, const FName VariableName)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		QuillscriptSubsystem->GetVariablesModifiers().Remove(VariableName);
}

#pragma endregion Variables


#pragma region Save

void UQuill::RefreshQuillscript(const UObject* WorldContextObject)
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		QuillscriptSubsystem->GetVariables().Empty();
		QuillscriptSubsystem->GetHistory().Empty();
		QuillscriptSubsystem->GetReferences().Empty();
		QuillscriptSubsystem->GetVariablesModifiers().Empty();
		QuillscriptSubsystem->InjectOptions.Empty();
	}
}

bool UQuill::SaveGameAndStoryToSlot(const UObject* WorldContextObject, USaveGame* SaveGameObject, const FString SlotName, const int32 UserIndex)
{
	if (TArray<uint8> SaveGameBytes; WorldContextObject && UGameplayStatics::SaveGameToMemory(SaveGameObject, SaveGameBytes))
	{
		WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>()->InjectQuillscriptDataIntoSaveGame(SaveGameBytes);
		return UGameplayStatics::SaveDataToSlot(SaveGameBytes, SlotName, UserIndex);
	}

	return false;
}

USaveGame* UQuill::LoadGameAndStoryFromSlot(const UObject* WorldContextObject, const FString SlotName, const int32 UserIndex)
{
	if (TArray<uint8> SaveGameBytes; WorldContextObject && UGameplayStatics::LoadDataFromSlot(SaveGameBytes, SlotName, UserIndex))
	{
		WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>()->ExtractQuillscriptDataFromSaveGame(SaveGameBytes);
		return UGameplayStatics::LoadGameFromMemory(SaveGameBytes);
	}

	return nullptr;
}

USaveGame* UQuill::ResumeGameAndStoryFromSlot(const UObject* WorldContextObject, const FString SlotName, const int32 UserIndex)
{
	USaveGame* SaveGame{ LoadGameAndStoryFromSlot(WorldContextObject, SlotName, UserIndex) };

	// Resume running scripts.
	if (SaveGame)
		if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
			for (const auto& History : QuillscriptSubsystem->GetHistory())
				if (History.Value.bRunning)
					ResumeScript(WorldContextObject, GetScriptById(History.Value.ScriptId));

	return SaveGame;
}

#pragma endregion Save


#pragma region Pipes

FString UQuill::EvaluateQuillscriptExpression(const FString& Expression)
{
	return FEvaluator::Solve(FLexer::InfixToPostfix(FLexer::StringToArrayOfSymbols(Expression)));
}

bool UQuill::PickerToBoolean(const EPicker Picker)
{
	if (Picker == EPicker::Yes)
		return true;

	return false;
}

#pragma endregion Pipes