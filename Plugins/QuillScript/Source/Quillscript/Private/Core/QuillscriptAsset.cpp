// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptAsset.h"

#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Core/QuillscriptInterpreter.h"
#include "Core/QuillscriptSettings.h"
#include "Core/QuillscriptSubsystem.h"
#include "Engine/GameInstance.h"
#include "Utils/Lexer.h"
#include "Utils/Quill.h"
#include "Utils/Tools.h"
#include "Widgets/BackgroundBox.h"
#include "Widgets/DialogBox.h"
#include "Widgets/SelectionBox.h"
#include "Widgets/SpriteBox.h"

#if WITH_EDITOR

	#include "EditorReimportHandler.h"
	#include "EditorFramework/AssetImportData.h"

#endif


UQuillscriptAsset::UQuillscriptAsset()
{
	// Self give all permissions.
	this->Permissions = UQuill::MakePermissionsList(EPermissionMode::All);
}


#if WITH_EDITOR

void UQuillscriptAsset::PostInitProperties()
{
	Super::PostInitProperties();

	// Create asset import data.
	if (!this->HasAnyFlags(RF_ClassDefaultObject))
		this->AssetImportData = NewObject<UAssetImportData>(this, "AssetImportData");

	// Set Id.
	this->UpdateId();
}

void UQuillscriptAsset::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	UObject::PostEditChangeProperty(PropertyChangedEvent);

	// Force update Id.
	this->UpdateId();
}

void UQuillscriptAsset::ReimportScript()
{
	FReimportManager::Instance()->Reimport(this, true, false);
}

void UQuillscriptAsset::UpdateId()
{
	switch (this->IdMethod)
	{
	case EScriptIdMethod::Name:		this->Id = FName(this->GetName());				break;
	case EScriptIdMethod::Path:		this->Id = this->GetScriptIdAsPath();			break;
	case EScriptIdMethod::Random:	this->Id = FName(FGuid::NewGuid().ToString());	break;
	default: break;
	}
}

FName UQuillscriptAsset::GetScriptIdAsPath() const
{
	FString ReferencePath{ this->GetPathName() };

	ReferencePath.TrimStartAndEndInline();
	ReferencePath.RemoveFromStart("/");

	FString AssetNameExtension;
	FString QuillscriptPath;
	ReferencePath.Split(".", &QuillscriptPath, &AssetNameExtension, ESearchCase::IgnoreCase, ESearchDir::FromEnd);

	return FName(QuillscriptPath);
}

#endif


#pragma region Data

UQuillscriptAsset* UQuillscriptAsset::CreateReadyToPlayCopy()
{
	UQuillscriptAsset* ReadyToPlayCopy{ NewObject<UQuillscriptAsset>(this, this->StaticClass(), FName(this->GetName()), RF_NoFlags, this) };

	if (ReadyToPlayCopy)
	{
		ReadyToPlayCopy->ResolveDirectives();	// Since directives can change settings, it must be done first.
		ReadyToPlayCopy->MergeSettings();
	}

	return ReadyToPlayCopy;
}

void UQuillscriptAsset::ResolveDirectives()
{
	for (int32 I{ 0 }; I < this->Statements.Num(); I++)
	{
		// Execute replace directive.
		this->Statements[I] = this->ReplaceInStatement(this->Statements[I]);

		if (this->Statements[I].Type == EStatementType::Directive)
		{
			FString DirectiveString{ this->Statements[I].Main };

			// Define.
			// Resolved at parsing time

			// Replace.
			if (DirectiveString.RemoveFromStart(FLexer::DirectiveReplace + " "))
				this->AddToReplacementMap(DirectiveString);

			// Include.
			else if (DirectiveString.RemoveFromStart(FLexer::DirectiveInclude + " "))
				this->ResolveIncludeDirective(DirectiveString, I + 1);

			// Import.
			else if (DirectiveString.RemoveFromStart(FLexer::DirectiveImport + " "))
				this->ResolveImportDirective(DirectiveString);

			// Inject.
			else if (DirectiveString.RemoveFromStart(FLexer::DirectiveInject + " "))
				this->ResolveInjectDirective(DirectiveString, I + 1);

			// Start. (Resolved at script start)
			else if (DirectiveString.RemoveFromStart(FLexer::DirectiveStart + " ") || DirectiveString.Equals(FLexer::DirectiveStart))
				continue;

			// Until. (Resolved at play time)
			else if (DirectiveString.RemoveFromStart(FLexer::DirectiveCheckpoint + " ") || DirectiveString.Equals(FLexer::DirectiveCheckpoint))
				continue;

			// Remove directive from statements list. Except '~ start' directives.
			this->Statements.RemoveAt(I);
			I--;
		}
	}
}

void UQuillscriptAsset::AddToReplacementMap(const FString& Directive)
{
	// TODO: Accept tabulation and quotation.

	FString Key, Value;
	Directive.Split(" ", &Key, &Value);

	if (!Key.IsEmpty() && !Value.IsEmpty())
		this->ReplacementMap.Add(Key, Value);
}

void UQuillscriptAsset::ResolveIncludeDirective(FString ScriptPath, const int32 Index)
{
	UQuillscriptAsset* IncludedScript;

	if (ScriptPath.RemoveFromStart(SYMBOL(Label)))
		IncludedScript = UQuill::GetScriptById(FName(ScriptPath));
	else
		IncludedScript = UQuill::GetScriptByPath(ScriptPath);

	if (IncludedScript)
	{
		this->IncludedScripts.Add(IncludedScript->GetPathName());
		this->Statements.Insert(IncludedScript->Statements, Index);
	}
	else
		WARNING("Can't find script to include: " + ScriptPath);
}

void UQuillscriptAsset::ResolveImportDirective(FString ScriptPath)
{
	UQuillscriptAsset* ImportedScript;

	if (ScriptPath.RemoveFromStart(SYMBOL(Label)))
		ImportedScript = UQuill::GetScriptById(FName(ScriptPath));
	else
		ImportedScript = UQuill::GetScriptByPath(ScriptPath);

	if (ImportedScript)
	{
		if (this->IncludedScripts.Contains(ImportedScript->GetPathName()))
			return;

		this->IncludedScripts.Add(ImportedScript->GetPathName());
		this->Statements.Append(ImportedScript->Statements);
	}
	else
		WARNING("Can't find script to import: " + ScriptPath);
}

void UQuillscriptAsset::ResolveInjectDirective(FString ScriptPath, const int32 Index)
{
	// Split script path and label.
	FString Label;
	ScriptPath.Split(" ", &ScriptPath, &Label);

	// Get source script.
	UQuillscriptAsset* IncludedScript;

	if (ScriptPath.RemoveFromStart(SYMBOL(Label)))
		IncludedScript = UQuill::GetScriptById(FName(ScriptPath));
	else
		IncludedScript = UQuill::GetScriptByPath(ScriptPath);

	// Inject label into this script.
	if (IncludedScript)
	{
		TArray<FStatement> InjectStatements;

		if (int32 I{ IncludedScript->GetStatementIndexByLabel(FName(Label)) }; I != INDEX_NONE)
		{
			do
			{
				InjectStatements.Add(IncludedScript->Statements[I]);
				I++;
			}
			while (I < IncludedScript->Statements.Num() && IncludedScript->Statements[I].Type != EStatementType::Label);
		}

		this->Statements.Insert(InjectStatements, Index);
	}
	else
		WARNING("Can't find script to inject: " + ScriptPath);
}

FStatement UQuillscriptAsset::ReplaceInStatement(FStatement Statement) const
{
	FStatement ReplacedStatement;

	const auto Replace = [this](FString Text) -> FString
	{
		for (TPair<FString, FString> ReplacementPair : this->ReplacementMap)
			Text = Text.Replace(*("[" + ReplacementPair.Key + "]"), *ReplacementPair.Value);

		return Text;
	};
	const auto ReplaceName = [Replace](const FName Text) -> FName { return FName(Replace(Text.ToString())); };
	const auto ReplaceText = [Replace](const FText& Text) -> FText { return FText::FromString(Replace(Text.ToString())); };

	// Copy values.
	ReplacedStatement.Type = Statement.Type;
	ReplacedStatement.Label = Statement.Label;
	ReplacedStatement.bChannel = Statement.bChannel;
	ReplacedStatement.bCovert = Statement.bCovert;

	// Replace values.
	for (const FString& Argument : Statement.Arguments)
		ReplacedStatement.Arguments.Add(Replace(Argument));

	ReplacedStatement.Main = Replace(Statement.Main);
	ReplacedStatement.Text = ReplaceText(Statement.Text);

	for (FExpression Condition : Statement.Conditions)
	{
		Condition.Symbol = Replace(Condition.Symbol);

		for (FText& Symbol : Condition.Parameters)
			Symbol =  ReplaceText(Symbol);

		ReplacedStatement.Conditions.Add(Condition);
	}

	for (FExpression Command : Statement.Commands)
	{
		Command.Symbol = Replace(Command.Symbol);

		for (FText& Parameter : Command.Parameters)
			Parameter =  ReplaceText(Parameter);

		ReplacedStatement.Commands.Add(Command);
	}

	for (const FString& Tag : Statement.Tags)
		ReplacedStatement.Tags.Add(Replace(Tag));

	ReplacedStatement.Target = ReplaceName(Statement.Target);

	for (const FText& TargetArgument : Statement.TargetArguments)
		ReplacedStatement.TargetArguments.Add(ReplaceText(TargetArgument));

	for (const FText& ExtraParameter : Statement.ExtraParameters)
		ReplacedStatement.ExtraParameters.Add(ReplaceText(ExtraParameter));


	return ReplacedStatement;
}

int32 UQuillscriptAsset::GetStartingIndex(const UObject* WorldContextObject) const
{
	const int32& TimesPlayed{ this->FindHistory(WorldContextObject).TimesPlayed };
	TTuple<int32, int32> StartDirective{ 0, 0 };

	for (int32 I{ 0 }; I < this->Statements.Num(); I++)
	{
		if (this->Statements[I].Type == EStatementType::Directive)
		{
			if (FString Directive{ this->Statements[I].Main }; Directive.Equals(FLexer::DirectiveStart) || Directive.StartsWith(FLexer::DirectiveStart + " "))
		    {
				Directive.RemoveFromStart(FLexer::DirectiveStart);
				Directive.TrimStartAndEndInline();

				int32 StartTime{ 1 };

				if (!Directive.IsEmpty())
					StartTime = FCString::Atoi(*Directive);

				if (TimesPlayed == StartTime)
					return I;

				if (StartTime < TimesPlayed && StartTime > StartDirective.Key)
					StartDirective = { StartTime, I };
		    }
		}
	}

	return StartDirective.Value;
}

bool UQuillscriptAsset::IsCreatedDuringRuntime() const
{
	return
		this->GetFullName().Contains("/Engine/Transient") ||
		this->Id.ToString().StartsWith("QuillscriptAsset_");
}

UObject* UQuillscriptAsset::FindScriptReference(const FString& ReferencePath) const
{
	// Class
	if (ReferencePath.EndsWith("_C"))
		if (UObject* Class{ LoadObject<UObject>(nullptr, *ReferencePath) })
			return Class;

	// Object.
	auto FindAsset = [](const FString& Path) -> UObject*
	{
		const FAssetRegistryModule& AssetRegistryModule{ FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry") };
		const FSoftObjectPath AssetPath{ Path };

		if (const FAssetData AssetData{ AssetRegistryModule.Get().GetAssetByObjectPath(AssetPath, true) }; AssetData.GetAsset())
			return AssetData.GetAsset();

		return nullptr;
	};

	// Pure asset path.
	if (UObject* Asset{ FindAsset(ReferencePath) })
		return Asset;

	// Using search paths.
	TArray SearchPaths{ this->ReferencePaths };
	SearchPaths.Append(UQuillscriptSettings::Get()->GetReferencesSearchPaths());

	for (auto [Path] : SearchPaths)
	{
		if (!Path.StartsWith("/"))
			Path.InsertAt(0, "/");

		if (!Path.EndsWith("/"))
			Path.Append("/");

		if (UObject* Asset{ FindAsset(Path + ReferencePath + "." + ReferencePath) })
			return Asset;
	}

	return nullptr;
}

void UQuillscriptAsset::UpdatePackagingReferences()
{
	TArray<FSoftObjectPath> UpdatedReferences;

	// Find all references
	for (const FStatement& Statement : this->Statements)
	{
		// List script references by path
		for (const FExpression& Command : Statement.Commands)
		{
			for (const FText& Parameter : Command.Parameters)
				if (FString Path{ Parameter.ToString() }; Path.RemoveFromStart("{&") && Path.RemoveFromEnd("}"))
					if (const UObject* Object{ this->FindScriptReference(Path) })
						UpdatedReferences.AddUnique(Object->GetPathName());

			// Link Travel scripts.
			if (Command.Symbol.StartsWith("Travel") && Command.Parameters.IsValidIndex(0))
			{
				FString Path{ Command.Parameters[0].ToString() };
				Path.RemoveFromStart("@");

				if (const TObjectPtr<UQuillscriptAsset> Script{ UQuill::GetScriptById(FName(Path)) })
					UpdatedReferences.AddUnique(Script->GetPathName());
				else if (const TObjectPtr<UQuillscriptAsset> ScriptByPath{ UQuill::GetScriptByPath(Command.Parameters[0].ToString()) })
					UpdatedReferences.AddUnique(ScriptByPath->GetPathName());
			}
		}

		// List include directives.
		TArray Directives{ FLexer::DirectiveImport, FLexer::DirectiveInclude, FLexer::DirectiveInject };

		for (const FString& Directive : Directives)
		{
			if (Statement.Main.StartsWith(Directive + " "))
			{
				FString IncludeDirective{ Statement.Main };
				IncludeDirective.RemoveFromStart(Directive + " ");

				FString LabelName;
				IncludeDirective.Split(" ", &IncludeDirective, &LabelName);

				FString Path{ IncludeDirective };
				Path.RemoveFromStart(SYMBOL(Label));

				if (const TObjectPtr<UQuillscriptAsset> Script{ UQuill::GetScriptById(FName(Path)) })
					UpdatedReferences.AddUnique(Script->GetPathName());
				else if (const TObjectPtr<UQuillscriptAsset> ScriptByPath{ UQuill::GetScriptByPath(IncludeDirective) })
					UpdatedReferences.AddUnique(ScriptByPath->GetPathName());

				break;
			}
		}
	}

	// Compare current references with new references and override if different.
	if (this->PackagingReferences.Num() != UpdatedReferences.Num())
	{
		this->PackagingReferences = UpdatedReferences;
		return;
	}

	for (int32 I{ 0 }; I < this->PackagingReferences.Num(); I++)
	{
		if (this->PackagingReferences[I] != UpdatedReferences[I])
		{
			this->PackagingReferences = UpdatedReferences;
			return;
		}
	}
}

#pragma endregion Data


#pragma region Statements

void UQuillscriptAsset::SetContent(const FString& InSourceCode)
{
	if (UQuillscriptSettings::Get()->GetStoreSourceCode())
		this->SourceCode = InSourceCode;

	this->Statements = FLexer::Parse(InSourceCode);
	this->UpdatePackagingReferences();
}

FName UQuillscriptAsset::GetStatementVariableName(const int32 StatementIndex) const
{
	if (this->Statements.IsValidIndex(StatementIndex))
		return this->MakeStatementVariableName(this->Statements[StatementIndex].Label);

	return NAME_None;
}

FName UQuillscriptAsset::MakeStatementVariableName(const FName LabelName) const
{
	return FName(this->GetId().ToString() + "." + LabelName.ToString());
}

bool UQuillscriptAsset::IsStatementVisited(const UObject* WorldContextObject, const int32 StatementIndex) const
{
	return UQuill::QuillscriptVariableExists(WorldContextObject, this->GetStatementVariableName(StatementIndex));
}

void UQuillscriptAsset::IncrementStatementVisitCounter(const UObject* WorldContextObject, const int32 StatementIndex) const
{
	if (this->Statements.IsValidIndex(StatementIndex))
	{
		// The Statement is marked, or it's a label and 'Keep Visited Labels' setting is on.
		if (
			UQuillscriptSettings::Get()->GetKeepVisitedStatements() ||
			this->Statements[StatementIndex].IsMarked() ||
			( this->Statements[StatementIndex].Type == EStatementType::Label && UQuillscriptSettings::Get()->GetKeepVisitedLabels() )
		)
			UQuill::IncrementQuillscriptVariable(WorldContextObject, this->GetStatementVariableName(StatementIndex));
	}
}

void UQuillscriptAsset::DeleteAllStatementVisitVariables(const UObject* WorldContextObject) const
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		auto Variables{ QuillscriptSubsystem->GetVariables() };

		for (TPair<FName, FText>& Variable : Variables)
			if (Variable.Key.ToString().StartsWith(this->GetId().ToString() + "."))
				QuillscriptSubsystem->GetVariables().Remove(Variable.Key);
	}
}

int32 UQuillscriptAsset::GetStatementIndexByLabel(const FName Label) const
{
	for (int32 I{ 0 }; I < this->Statements.Num(); I++)
		if (this->Statements[I].Label.IsEqual(Label))
			return I;

	WARNING("GetStatementIndexByLabel() -> No statement with label: " + Label.ToString());
	return INDEX_NONE;
}

FStatement UQuillscriptAsset::GetStatementByLabel(const FName Label) const
{
	for (FStatement Statement : this->Statements)
		if (Statement.Label.IsEqual(Label))
			return Statement;

	WARNING("GetStatementByLabel() -> No statement with label: " + Label.ToString());
	return FStatement();
}

bool UQuillscriptAsset::IsLabelName(const FName LabelName) const
{
	return this->GetStatementIndexByLabel(LabelName) != INDEX_NONE;
}

#pragma endregion Statements


#pragma region History

bool UQuillscriptAsset::HistoryExists(const UObject* WorldContextObject) const
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		return QuillscriptSubsystem->GetHistory().Contains(this->GetId());

	return false;
}

void UQuillscriptAsset::CreateHistory(const UObject* WorldContextObject) const
{
	// Do nothing if history already exists.
	if (this->HistoryExists(WorldContextObject))
		return;

	// Create history.
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		FHistory History;
		History.ScriptId = this->Id;
		QuillscriptSubsystem->GetHistory().Add(this->GetId(), History);
	}
}

FHistory& UQuillscriptAsset::FindHistory(const UObject* WorldContextObject) const
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		if (FHistory* TempHistory{ QuillscriptSubsystem->GetHistory().Find(this->GetId()) })
			return *TempHistory;

	UTools::Warning("FindHistory() -> No scene history found for script of id '" + this->GetId().ToString() + "'.");

	FHistory* EmptyHistory{ nullptr };
	return *EmptyHistory;
}

void UQuillscriptAsset::PushToHistory(const UObject* WorldContextObject, const FSaveState NewEntry) const
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		if (FHistory* TempHistory{ QuillscriptSubsystem->GetHistory().Find(this->GetId()) })
		{
			// Add new entry to history flow.
			TempHistory->SaveState.Add(NewEntry);

			// Remove older entries flow history flow, if above the allowed limit of entries.
			if (const int32 TempMaxHistoryEntries{ this->GetMaxHistoryEntries() > 0 ? this->GetMaxHistoryEntries() : UQuillscriptSettings::Get()->GetMaxHistoryEntries() }; TempMaxHistoryEntries > 0)
				while (TempHistory->SaveState.Num() > TempMaxHistoryEntries)
					TempHistory->SaveState.RemoveAt(0);
		}
	}
}

void UQuillscriptAsset::DeleteHistory(const UObject* WorldContextObject) const
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		QuillscriptSubsystem->GetHistory().Remove(this->GetId());
}

#pragma endregion History


#pragma region Settings

void UQuillscriptAsset::MergeSettings()
{
	// Set defaults classes.
	if (!this->Settings.InterpreterClass)
		this->Settings.InterpreterClass = UQuillscriptSettings::Get()->GetScriptSettings().InterpreterClass;

	if (!this->Settings.DialogBoxClass)
		this->Settings.DialogBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().DialogBoxClass;

	if (!this->Settings.SelectionBoxClass)
		this->Settings.SelectionBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().SelectionBoxClass;

	if (!this->Settings.BackgroundBoxClass)
		this->Settings.BackgroundBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().BackgroundBoxClass;

	if (!this->Settings.SpriteBoxClass)
		this->Settings.SpriteBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().SpriteBoxClass;


	// Set default input.
	if (this->Settings.ShowMouseCursorDuring == EPicker::Default)
		this->Settings.ShowMouseCursorDuring = UQuillscriptSettings::Get()->GetScriptSettings().ShowMouseCursorDuring;

	if (this->Settings.ShowMouseCursorAfter == EPicker::Default)
		this->Settings.ShowMouseCursorAfter = UQuillscriptSettings::Get()->GetScriptSettings().ShowMouseCursorAfter;

	if (this->Settings.EnableInputDuring == EPicker::Default)
		this->Settings.EnableInputDuring = UQuillscriptSettings::Get()->GetScriptSettings().EnableInputDuring;

	if (this->Settings.EnableInputAfter == EPicker::Default)
		this->Settings.EnableInputAfter = UQuillscriptSettings::Get()->GetScriptSettings().EnableInputAfter;

	if (this->Settings.InputModeDuring == EInputMode::Default)
		this->Settings.InputModeDuring = UQuillscriptSettings::Get()->GetScriptSettings().InputModeDuring;

	if (this->Settings.InputModeAfter == EInputMode::Default)
		this->Settings.InputModeAfter = UQuillscriptSettings::Get()->GetScriptSettings().InputModeAfter;
}

#pragma endregion Settings