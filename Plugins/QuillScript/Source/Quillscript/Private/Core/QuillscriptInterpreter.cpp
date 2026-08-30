// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptInterpreter.h"

#include "TimerManager.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Components/AudioComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Core/QuillscriptAsset.h"
#include "Core/QuillscriptSettings.h"
#include "Core/QuillscriptSubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/LevelScriptActor.h"
#include "Engine/Texture.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameState.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "Sound/SoundBase.h"
#include "Text/SmartTextBlockDecorator.h"
#include "Utils/Evaluator.h"
#include "Utils/Lexer.h"
#include "Utils/Quill.h"
#include "Utils/Tools.h"
#include "Widgets/BackgroundBox.h"
#include "Widgets/SpriteBox.h"
#include "Widgets/DialogBox.h"
#include "Widgets/SelectionBox.h"


#pragma region Macros

/** Evaluate the conditions of a statement. */
#define EVAL(Conditions)	this->EvaluateConditions(Conditions)

/** Check if this script play has a permission. */
#define CAN(Permission)		this->Script->GetPermissions().Contains(EPermission::Permission)

/** Broadcast story node executed. */
#define BROADCAST			this->OnStatementPlayed.Broadcast(this, this->State.CurrentIndex, this->GetCurrentStatement());

#pragma endregion


AQuillscriptInterpreter::AQuillscriptInterpreter()
{
	// Settings.
	this->PrimaryActorTick.bCanEverTick = true;
	this->AActor::SetActorHiddenInGame(true);

	// Set root component.
	this->SceneComponent = this->CreateDefaultSubobject<USceneComponent>("Root");
	this->SceneComponent->SetRelativeLocation(FVector::ZeroVector);
	this->SceneComponent->SetMobility(EComponentMobility::Static);
	this->SetRootComponent(SceneComponent);
}

void AQuillscriptInterpreter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Evaluate checkpoint directive every frame.
	if (this->bEvaluateCheckpointDirectiveEveryFrame)
		this->EvaluateCheckpointDirective();
}


#pragma region Flow

void AQuillscriptInterpreter::Start_Implementation(UQuillscriptAsset* ScriptAsset, FName StartingLabel, const bool bResume)
{
	// Stop if this script is already playing.
	if (!this->IsFresh())
	{ ERROR("Start() -> Can't start an interpreter that is already playing"); this->Destroy(); return; }

	// Check if the script is not null.
	if (!ScriptAsset)
	{ ERROR("Start() -> Script can't be null"); this->Destroy(); return; }

	// Check if 'Multiplayer Mode' is 'Host Only'.
	// TODO Add a option to check if its not a 'Join'?
	// if (UQuillscriptSettings::Get()->GetMultiplayerMode() == EMultiplayerMode::HostOnly && !UTools::HasAuthority(this))
	// { PRINT("Start() -> Client players can't start a script"); this->Destroy(); return; }

	// Join other players.
	// if (UQuillscriptSettings::Get()->HasMultiplayer())
        // UQuill::JoinPlayers(this);

	SUCCESS("Script '" + ScriptAsset->GetId().ToString() + "' started.");

	#if WITH_EDITOR

	// Preserve exact source identity for live runtime refresh. Looking up by
	// script ID can select a different asset when Engine and project content
	// intentionally share a human-readable ID.
	this->RuntimeSourceScript = ScriptAsset;

	#endif


	// Create a copy of the given script to prevent the original asset from being modified.
	this->ResetState();
	this->Script = ScriptAsset->CreateReadyToPlayCopy();
	this->Script->Settings.InterpreterClass = this->GetClass();

	// Setup.
	this->ApplyScriptSettingsDuring();
	int32 StartingIndex{ INDEX_NONE };

	// Create widgets.
	this->CreateDialogBox();
	this->CreateSelectionBox();
	this->CreateBackgroundBox();

	// Resume or create history.
	if (this->Script->HistoryExists(this))
	{
		if (bResume)
		{
			FHistory& History{ this->Script->FindHistory(this) };

			if (!History.SaveState.IsEmpty())
			{
				const FSaveState LastState{ History.SaveState.Pop() };
				this->Script->SetSettings(LastState.ScriptSettings);
				this->State = LastState.InterpreterState;

				StartingLabel = LastState.LabelName;
				StartingIndex = LastState.InterpreterState.CurrentIndex;

				// Restore background image.
				if (!LastState.BackgroundImagePath.IsNull())
					for (const auto& CommandStatement : FLexer::Parse(SYMBOL(Command) + " Background {&" + LastState.BackgroundImagePath.ToString() + "} none 0"))
						this->PlayCommand(CommandStatement);

				// Restore background music.
				for (const auto& [Channel, AssetPath, Volume] : LastState.Sounds)
					for (const auto& CommandStatement : FLexer::Parse(SYMBOL(Command) + " PlaySound {&" + AssetPath + "} " + Channel.ToString() + " " + FString::SanitizeFloat(Volume)))
						this->PlayCommand(CommandStatement);
			}
		}
	}
	else
		this->Script->CreateHistory(this);

	this->IncrementTimesPlayed();

	// Notify all.
	if (const TObjectPtr<UQuillscriptSubsystem> QuillscriptSubsystem{ this->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		QuillscriptSubsystem->OnScriptPlay.Broadcast(this);

	this->BeforeStart();
	this->OnStarted.Broadcast(this);

	// Play from starting label.
	if (StartingIndex == INDEX_NONE)
		StartingIndex = this->Script->GetStartingIndex(this);

	StartingLabel.IsNone() ? this->Play(StartingIndex) : this->PlayByLabel(StartingLabel);
}

void AQuillscriptInterpreter::Play_Implementation(const int32 StatementIndex)
{
	// Stop if it can't proceed.
	if (!this->State.bCanProceed)
		return;

	#if WITH_EDITOR

	// Reload script asset from disc for live update during runtime.
	if (UQuillscriptSettings::Get()->GetUpdateAtRuntime())
		this->ReloadScript();

	#endif

	this->BeforePlay();

	if (this->Script->GetStatements().IsValidIndex(StatementIndex))
	{
		// Update state.
		this->State.CurrentIndex = StatementIndex;
		FStatement CurrentStatement{ this->GetCurrentStatement() };

		// Do not play if it is a covert or play once played statement.
		if (
			CurrentStatement.Type != EStatementType::Option &&	// The following rules do not apply to option statements.
			(
				// Do not play covert statements, unless it's a router call.
				( CurrentStatement.IsCovert() && !this->bRouterCall )
			||
				// Do not play if it's a play once statement, already visited.
				( CurrentStatement.IsPlayOnce() && this->Script->IsStatementVisited(this, this->State.CurrentIndex) )
			)
		)
		{
			if (CurrentStatement.Type == EStatementType::Label)
				this->Done();
			else if (CurrentStatement.Type == EStatementType::Condition)
				this->Play(this->GetNextStatementIndexAfterEndIf());
			else
				this->Next();

			return;
		}

		// Delete template variables if template ended.
		if (!this->State.TemplateCalledLabel.IsNone())
		{
			const FStatement CalledStatement{ this->Script->GetStatementByLabel(this->State.TemplateCalledLabel) };

			if (
				( CalledStatement.Type != EStatementType::Label && CurrentStatement.Label != CalledStatement.Label )
				||
				( CalledStatement.Type == EStatementType::Label && CurrentStatement.Label != CalledStatement.Label && CurrentStatement.Type == EStatementType::Label )
			)
			{
				// Delete any template variables from a previous template call.
				this->DeleteTemplateVariables();
				this->State.TemplateCalledLabel = NAME_None;
			}
		}

		// Mark statement.
		CurrentStatement = this->ReplaceVariablesInStatement(this->GetCurrentStatement());
		this->bRouterCall = false;
		this->Script->IncrementStatementVisitCounter(this, this->State.CurrentIndex);

		// Play Statement.
		switch (CurrentStatement.Type)
		{
		case EStatementType::Dialogue:	this->PlayDialogue(CurrentStatement);		return;
		case EStatementType::Label:		this->PlayLabel(CurrentStatement);		return;
		case EStatementType::Command:	this->PlayCommand(CurrentStatement);		return;
		case EStatementType::Router:	this->PlayRouter(CurrentStatement);		return;
		case EStatementType::Condition:	this->PlayCondition(CurrentStatement);	return;
		case EStatementType::Directive:	this->PlayDirective(CurrentStatement);	return;

		case EStatementType::Option:
		{
			// Get all sets of option statements.
			TArray Options{ this->GetOptionsSet(this->State.CurrentIndex) };
			this->State.CurrentIndex += Options.Num() - 1;
			this->PlayOption(Options);

			return;
		}

		default: this->Next();
		}
	}

	// Index is invalid.
	else
	{
		// Return if there are callbacks in stack.
		if (!this->State.ChannelCalledLabel.IsNone())
			this->Return();

		// End script.
		else
			this->End();
	}
}

void AQuillscriptInterpreter::PlayByLabel(const FName Label)
{
	if (const int32 StatementIndex{ this->Script->GetStatementIndexByLabel(Label) }; StatementIndex >= 0)
		this->Play(StatementIndex);
	else
	{
		ERROR("PlayByLabel() -> Script '" + this->Script->GetId().ToString() + "' does not have a label called '" + Label.ToString() + "'. Script ended.");
		this->End();
	}
}

void AQuillscriptInterpreter::Restart_Implementation()
{
	this->ResetState();
	this->Play(this->Script->GetStartingIndex(this));
}

void AQuillscriptInterpreter::Next_Implementation()
{
	this->Play(this->State.CurrentIndex + 1);
}

void AQuillscriptInterpreter::Rollback_Implementation()
{
	if (UQuillscriptSettings::Get()->GetCanRollback())
	{
		if (this->Script->HistoryExists(this))
		{
			if (auto& [ScriptPath, TimesPlayed, bPlaying, Flow]{ this->Script->FindHistory(this) }; !Flow.IsEmpty())
			{
				// Remove the current entry.
				FSaveState PreviousFlow = Flow.Pop();

				// Get previous played statement data.
				if (!Flow.IsEmpty())
					PreviousFlow = Flow.Pop();

				// Restore save state.
				if (UQuillscriptSubsystem* QuillscriptSubsystem{ this->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
					QuillscriptSubsystem->GetVariables() = PreviousFlow.Variables;

				this->Script->SetSettings(PreviousFlow.ScriptSettings);
				this->State = PreviousFlow.InterpreterState;

				// Play the previous statement.
				if (this->Script->IsLabelName(PreviousFlow.LabelName))
					this->PlayByLabel(PreviousFlow.LabelName);
				else
					this->Play(PreviousFlow.InterpreterState.CurrentIndex);
			}
		}
	}
}

void AQuillscriptInterpreter::Repeat()
{
	this->Play(this->GetPreviousStatementIndexOfType(EStatementType::Label));
}

void AQuillscriptInterpreter::Done()
{
	if (const int32 NextLabelStatementIndex{ this->GetNextStatementIndexOfType(EStatementType::Label) }; NextLabelStatementIndex > 0)
		this->Play(NextLabelStatementIndex);
	else
		this->End();
}

void AQuillscriptInterpreter::Return()
{
	this->State.ChannelCalledLabel = NAME_None;
	this->bRouterCall = false;

	if (!this->State.RouterIndexes.IsEmpty())
		this->Play(this->State.RouterIndexes.Pop() + 1);
	else
		this->Next();
}

void AQuillscriptInterpreter::End_Implementation()
{
	this->Kill();

	// Restores player inputs.
	this->ApplyScriptSettingsAfter();
}

void AQuillscriptInterpreter::Kill_Implementation()
{
	this->BeforeEnd();

	// Copy script id.
	FName ScriptId;

	if (IsValid(this->Script))
		ScriptId = this->Script->GetId();

	// Clear references.
	this->ResetScript();
	this->ResetWidgets();
	this->ResetAudioChannels();

	// Clear temporary data.
	this->DeleteTemporaryData();

	// Mark this scene as finished.
	if (UQuillscriptSettings::Get()->GetKeepHistory())
	{
		if (this->Script->HistoryExists(this))
			this->Script->FindHistory(this).bRunning = false;
	}

	// Delete script history.
	else
		this->Script->DeleteHistory(this);

	// Call OnEnded.
	SUCCESS("Script '" + ScriptId.ToString() + "' ended");

	this->OnEnded.Broadcast(this);

	if (const UQuillscriptSubsystem* QuillscriptAsset{ this->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		QuillscriptAsset->OnScriptEnd.Broadcast(ScriptId);

	// Kill.
	this->Destroy();
}

void AQuillscriptInterpreter::Restore_Implementation()
{
	// Disable any checkpoint flags.
	this->bEvaluateCheckpointDirectiveEveryFrame = false;
	this->CheckpointDirective = FStatement();

	// Remove any checkpoint timer.
	if (const UWorld* World{ this->GetWorld() })
		if (World->GetTimerManager().IsTimerActive(TimerHandleRef))
			World->GetTimerManager().ClearTimer(TimerHandleRef);

	// Restore.
	this->State.bCanProceed = true;
}

void AQuillscriptInterpreter::Stop_Implementation()
{
	this->State.bCanProceed = false;
}

void AQuillscriptInterpreter::Sleep_Implementation()
{
	this->Stop();

	// Hide UI.
	this->RemoveDialogBox();
	this->RemoveSelectionBox();
	this->RemoveBackgroundBox();

	// Restores player inputs.
	this->ApplyScriptSettingsAfter();

	SUCCESS("Script is asleep");
}

void AQuillscriptInterpreter::Wakeup_Implementation()
{
	this->Restore();

	// Set player input.
	this->ApplyScriptSettingsDuring();

	// Restore UI.
	// ShowBackgroundBox() was called twice here and ShowSelectionBox() not at all, so a script
	// resumed mid-choice restored its dialog and backdrop but never its selection box.
	this->ShowDialogBox();
	this->ShowBackgroundBox();
	this->ShowSelectionBox();

	SUCCESS("Script is awaken");
}

void AQuillscriptInterpreter::Wait(const float Duration)
{
	if (const UWorld* World{ this->GetWorld() })
	{
		// Stop the script flow.
		this->Stop();

		// Set Timer.
		FTimerHandle TimerHandle;

		World->GetTimerManager().SetTimer(
			TimerHandle,

			// Callback method to restore script flow.
			FTimerDelegate::CreateLambda([this]()
			{
				this->Restore();
				this->Next();
			}),

			Duration,
			false
		);
	}
}

void AQuillscriptInterpreter::Timer(const float Duration, FString Command, const bool bAsync)
{
	if (const UWorld* World{ this->GetWorld() })
	{
		// Synchronous.
		if (!bAsync)
			this->Stop();

		// Set Timer.
		FTimerHandle TimerHandle;

		World->GetTimerManager().SetTimer(
			TimerHandle,

			// Callback method to restore script flow.
			FTimerDelegate::CreateLambda([this, Command, bAsync]()
			{
				// Execute the given callback method.
				for (const auto& CommandStatement : FLexer::Parse(SYMBOL(Command) + " " +  Command))
					this->PlayCommand(CommandStatement);

				// Continue.
				if (!bAsync)
				{
					this->Restore();
					this->Next();
				}
			}),

			Duration,
			false
		);
	}
}

void AQuillscriptInterpreter::Travel(const FString TargetScript, const FName StartingLabel)
{
	if (const TObjectPtr<UQuillscriptAsset> NewScript{ UQuill::FindScript(TargetScript) })
		UQuill::PlayScript(this->GetWorld(), NewScript, StartingLabel);

	this->Kill();
}

void AQuillscriptInterpreter::TravelPass(const FString TargetScript, const FName StartingLabel)
{
	if (const TObjectPtr<UQuillscriptAsset> NewScript{ UQuill::FindScript(TargetScript) })
	{
		if (const TObjectPtr<AQuillscriptInterpreter> NewInterpreter{ this->MakeCopy(true) })
		{
			NewScript->SetSettings(this->Script->Settings);
			NewScript->SetTarget(this->Script->GetTarget());
			NewInterpreter->Start(NewScript, StartingLabel);
		}
	}

	this->Kill();
}

#pragma endregion Flow


#pragma region Statements

void AQuillscriptInterpreter::PlayLabel_Implementation(const FStatement Label)
{
	// Return callback.
	if (!this->State.ChannelCalledLabel.IsNone() && this->State.ChannelCalledLabel != Label.Label)
	{
		this->Return();
		return;
	}

	// Play label.
	if (EVAL(Label.Conditions))
	{
		this->BeforePlayLabel(Label);
		BROADCAST
		this->Next();
	}

	// Conditions fails. Go to target.
	else if (Label.HasTarget())
		this->GoToTarget(Label.Target, Label.TargetArguments, Label.IsChannel());

	// Conditions fails and there is no target. Go to the next label.
	else
		this->Play(this->GetNextStatementIndexOfType(EStatementType::Label));
}

void AQuillscriptInterpreter::PlayDialogue_Implementation(const FStatement Dialogue)
{
	if (!CAN(PlayDialogues)) { this->Next(); return; }

	// Split gate texts.
	FText Text{ Dialogue.Text };

	if (Dialogue.Text.ToString().Contains(SYMBOL(Gate)))
	{
		FString On, Off;
		Dialogue.Text.ToString().Split(SYMBOL(Gate), &On, &Off);
		EVAL(Dialogue.Conditions) ? Text = FText::FromString(On.TrimStartAndEnd()) : Text = FText::FromString(Off.TrimStartAndEnd());
	}
	else if (!EVAL(Dialogue.Conditions))
	{
		// Play Router instruction.
		if (Dialogue.HasTarget())
			this->GoToTarget(Dialogue.Target, Dialogue.TargetArguments, Dialogue.IsChannel());

		// Proceed to the next statement if there is no Router instruction.
		else
			this->Next();

		return;
	}

	this->BeforePlayDialogue(Dialogue);

	// Add an entry to the script history flow, when a dialogue statement is played.
	this->Snapshot();

	// Stop previous voice channel
	if (const auto& VoiceAudioComponent{ this->AudioComponents.FindRef("voice") })
	{
		VoiceAudioComponent->Stop();
		VoiceAudioComponent->Sound = nullptr;
	}

	// Execute pre-dialogue commands.
	this->ExecuteCommands(Dialogue.Commands);

	// Call Dialogue Box.
	FStatement DialogueStatement{ Dialogue };
	DialogueStatement.Text = Text;

	if (UQuillscriptSettings::Get()->GetManageDialogueBox())
		this->PlayDialogueBox(DialogueStatement);
	else
		this->OnPlayDialogueBox.Broadcast(this, DialogueStatement);

	BROADCAST

	// Check if the next statement is an option and auto plays it.
	if (
		UQuillscriptSettings::Get()->GetAutoPlayOptionStatements() &&
		this->Script->GetStatements().IsValidIndex(this->State.CurrentIndex + 1) &&
		this->Script->GetStatements()[this->State.CurrentIndex + 1].Type == EStatementType::Option
	)
		this->Next();
}

void AQuillscriptInterpreter::PlayOption_Implementation(TArray<FStatement>& Options)
{
	// Remove play once options.
	TArray<FStatement> PlayableOptions;

	for (FStatement Option : Options)
	{
		if (
			!Option.IsPlayOnce() ||
			!UQuill::QuillscriptVariableExists(this, this->Script->MakeStatementVariableName(Option.Label))
	    )
	    	PlayableOptions.Add(Option);
	}

	// Check if it can play these options.
	if (!PlayableOptions.IsEmpty() && CAN(PlaySelections))
	{
		this->Stop();
		PlayableOptions = this->CreateDynamicOptionsSet(PlayableOptions);
		this->BeforePlayOption(PlayableOptions);

		// Call Selection Box.
		if (UQuillscriptSettings::Get()->GetManageSelectionBox())
			this->PlaySelectionBox(PlayableOptions);
		else
			this->OnPlaySelectionBox.Broadcast(this, PlayableOptions);

		BROADCAST
	}
	else
		this->Next();
}

void AQuillscriptInterpreter::PlayCommand_Implementation(const FStatement Command)
{
	const int32 TempStatementIndex{ this->State.CurrentIndex };

	// Default play.
	if (EVAL(Command.Conditions))
	{
		this->BeforePlayCommand(Command);
		this->ExecuteCommands(Command.Commands);
	}

	// Conditions fails; Play Router instruction.
	else if (Command.HasTarget())
		this->GoToTarget(Command.Target, Command.TargetArguments, Command.IsChannel());

	BROADCAST

	// Only move to the next statement if these commands haven't changed the current statement index.
	// ! This also prevents a stack overflow when using functions like 'Restart' and 'Play'.
	if (TempStatementIndex == this->State.CurrentIndex)
		this->Next();
}

void AQuillscriptInterpreter::PlayRouter_Implementation(const FStatement Router)
{
	if (CAN(PlayRouters))
	{
		if (EVAL(Router.Conditions))
		{
			this->BeforePlayRouter(Router);
			BROADCAST
			this->GoToTarget(FName(Router.Main), Router.ExtraParameters, Router.IsChannel());
		}
		else if (!Router.Target.IsNone())
		{
			this->BeforePlayRouter(Router);
			BROADCAST
			this->GoToTarget(Router.Target, Router.TargetArguments, Router.IsChannel());
		}
		else
		{
			BROADCAST
			this->Next();
		}
	}
	else
		this->Next();
}

void AQuillscriptInterpreter::PlayCondition_Implementation(const FStatement Condition)
{
	this->BeforePlayCondition(Condition);

	// Mark that a condition is open.
	if (Condition.IsIf())
		this->bConditionOpen = true;

	// Play condition if condition is open.
	if (this->bConditionOpen)
	{
		// If the condition is true, or it's an else case.
		if (Condition.IsElse() || EVAL(Condition.Conditions))
		{
			this->bConditionOpen = false;
			this->Next();
		}

		// Play next 'else if', 'else' or 'end if'.
		else
			this->Play(this->GetNextElseElseIfEndIfIndex());
	}

	// Jump to the next statement after the condition statement sequence end.
	else
		this->Play(this->GetNextStatementIndexAfterEndIf());
}

void AQuillscriptInterpreter::PlayDirective_Implementation(const FStatement Directive)
{
	this->BeforePlayDirective(Directive);

	// Checkpoint.
	if (Directive.Main.StartsWith(FLexer::DirectiveCheckpoint))
	{
		this->ExecuteCheckpointDirective(Directive);
		BROADCAST
	}

	// Others.
	else
	{
		BROADCAST
		this->Next();
	}
}

FStatement AQuillscriptInterpreter::GetCurrentStatement() const
{
	if (TArray Statements{ this->Script->GetStatements() }; Statements.IsValidIndex(this->State.CurrentIndex))
		return Statements[this->State.CurrentIndex];

	return FStatement();
}

FStatement AQuillscriptInterpreter::ReplaceVariablesInStatement(const FStatement Statement) const
{
	FStatement ReplacedStatement{ Statement };

	ReplacedStatement.Main = REPLACE(Statement.Main);
	ReplacedStatement.Text = TEXT_REPLACE(Statement.Text);

	ReplacedStatement.Tags.Empty();
	for (const FString& Tag : Statement.Tags)
		ReplacedStatement.Tags.Add(REPLACE(Tag));

	ReplacedStatement.ExtraParameters.Empty();
	for (const FText& ExtraParameter : Statement.ExtraParameters)
		ReplacedStatement.ExtraParameters.Add(TEXT_REPLACE(ExtraParameter));

	return ReplacedStatement;
}

int32 AQuillscriptInterpreter::GetPreviousStatementIndexOfType(const EStatementType Type) const
{
	TArray Statements{ this->Script->GetStatements() };

	for (int32 I{ this->State.CurrentIndex - 1 }; I >= 0; I--)
		if (Statements[I].Type == Type)
			return I;

	return -1;
}

int32 AQuillscriptInterpreter::GetNextStatementIndexOfType(const EStatementType Type) const
{
	TArray Statements{ this->Script->GetStatements() };

	for (int32 I{ this->State.CurrentIndex + 1 }; I < Statements.Num(); I++)
		if (Statements[I].Type == Type)
			return I;

	return -1;
}

int32 AQuillscriptInterpreter::GetNextElseElseIfEndIfIndex() const
{
	TArray Statements{ this->Script->GetStatements() };
	int32 Nested{ 0 };

	for (int32 I{ this->State.CurrentIndex + 1 }; I < Statements.Num(); I++)
	{
	    if (Statements[I].IsIf())
			Nested++;

		else if (Statements[I].IsElseIf() || Statements[I].IsElse() || Statements[I].IsEndIf())
		{
			if (Nested == 0)
				return I;

			if (Statements[I].IsEndIf())
				Nested--;
		}
	}

	return -1;
}

int32 AQuillscriptInterpreter::GetNextStatementIndexAfterEndIf() const
{
	TArray Statements{ this->Script->GetStatements() };

	for (int32 I{ this->State.CurrentIndex }; I < Statements.Num(); I++)
		if (Statements[I].IsEndIf())
			return I + 1;

	return -1;
}

#pragma endregion Statements


#pragma region State

void AQuillscriptInterpreter::Print(const FName VariableName) const
{
	PRINT(VAR(VariableName));
}

void AQuillscriptInterpreter::Delete(const FName VariableName) const
{
	UQuill::DeleteQuillscriptVariable(this, VariableName);
}

void AQuillscriptInterpreter::Notify(const FString Message) const
{
	if (const UQuillscriptSubsystem* QuillscriptSubsystem{ this->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		QuillscriptSubsystem->OnNotified.Broadcast(Message);
}

TArray<FStatement> AQuillscriptInterpreter::GetOptionsSet(int32 Index) const
{
	// Use the current index if none is given.
	if (Index < 0)
		Index = this->State.CurrentIndex;

	// Find the first option.
	while (this->Script->GetStatements().IsValidIndex(Index) && this->Script->GetStatements()[Index].Type == EStatementType::Option)
		Index--;

	Index++;

	// Get options' set.
	TArray<FStatement> Options;

	while (this->Script->GetStatements().IsValidIndex(Index) && this->Script->GetStatements()[Index].Type == EStatementType::Option)
	{
		Options.Add(this->ReplaceVariablesInStatement(this->Script->GetStatements()[Index]));
		Index++;
	}

	return Options;
}

void AQuillscriptInterpreter::OptionSelected_Implementation(const FStatement Option)
{
	// Executes post-select commands.
	this->ExecuteCommands(Option.Commands);

	// Increment selected option counter if it has a label.
	if (UQuillscriptSettings::Get()->GetKeepSelectedOptions() && Option.HasLabel())
		UQuill::IncrementQuillscriptVariable(this, this->Script->MakeStatementVariableName(Option.Label));

	// Add this option text to variable.
	if (UQuillscriptSettings::Get()->GetKeepLastSelectedOptionText())
		SET_OUT("option", Option.Text);

	// Go to given label, if any.
	this->Restore();

	if (!Option.Target.IsNone())
		this->GoToTarget(Option.Target, Option.TargetArguments, false);
	else
		this->Next();
}

AQuillscriptInterpreter* AQuillscriptInterpreter::MakeCopy(const bool bCopyDelegates) const
{
	const TObjectPtr<AQuillscriptInterpreter> InterpreterCopy{ UQuill::CreateInterpreter(this, this->GetClass()) };

	if (InterpreterCopy)
	{
		// Delegates.
		if (bCopyDelegates)
		{
			InterpreterCopy->OnStatementPlayed = this->OnStatementPlayed;
			InterpreterCopy->OnStarted = this->OnStarted;
			InterpreterCopy->OnResumed = this->OnResumed;
			InterpreterCopy->OnEnded = this->OnEnded;
			InterpreterCopy->OnPlayDialogueBox = this->OnPlayDialogueBox;
			InterpreterCopy->OnPlaySelectionBox = this->OnPlaySelectionBox;
			InterpreterCopy->OnPlayBackgroundBox = this->OnPlayBackgroundBox;
			InterpreterCopy->OnAudioFinished = this->OnAudioFinished;
		}
	}

	return InterpreterCopy;
}

void AQuillscriptInterpreter::HardReset_Implementation()
{
	this->ResetState();
	this->ResetScript();
	this->ResetWidgets();
	this->ResetAudioChannels();
	this->ResetDelegates();

	this->DeleteTemporaryData();
	this->ApplyScriptSettingsDuring();
}

void AQuillscriptInterpreter::ResetState()
{
	this->State = FInterpreterState();
	this->bConditionOpen = false;
	this->bRouterCall = false;
	this->TimerHandleRef = FTimerHandle();
}

void AQuillscriptInterpreter::ResetScript() const
{
	if (IsValid(this->Script))
		this->Script->ConditionalBeginDestroy();
}

void AQuillscriptInterpreter::ResetWidgets()
{
	if (IsValid(this->BackgroundBox))
		this->BackgroundBox->ConditionalBeginDestroy();

	if (IsValid(this->DialogBox))
		this->DialogBox->ConditionalBeginDestroy();

	if (IsValid(this->SelectionBox))
		this->SelectionBox->ConditionalBeginDestroy();

	for (const auto& SpriteBox : this->SpriteBoxes)
		if (IsValid(SpriteBox.Value))
			SpriteBox.Value->ConditionalBeginDestroy();

	this->SpriteBoxes.Empty();
}

void AQuillscriptInterpreter::ResetAudioChannels()
{
	for (const auto& AudioComponent : this->AudioComponents)
	{
		if (IsValid(AudioComponent.Value))
		{
			AudioComponent.Value->Stop();
			AudioComponent.Value->ConditionalBeginDestroy();
		}
	}

	this->AudioComponents.Empty();
}

void AQuillscriptInterpreter::ResetDelegates()
{
	this->OnStatementPlayed.Clear();
	this->OnStarted.Clear();
	this->OnResumed.Clear();
	this->OnEnded.Clear();
	this->OnPlayDialogueBox.Clear();
	this->OnPlaySelectionBox.Clear();
	this->OnPlayBackgroundBox.Clear();
	this->OnAudioFinished.Clear();
}

#pragma endregion State


#pragma region Input

void AQuillscriptInterpreter::SetInputMode(const EInputMode InputMode, const EMouseLockMode MouseLockMode, const bool bHideCursorDuringCapture, UWidget* WidgetToFocus) const
{
	if (const UWorld* World{ this->GetWorld() }; World)
	{
		if (APlayerController* PlayerController{ World->GetFirstPlayerController() })
		{
			switch (InputMode)
			{
			case EInputMode::GameOnly:	UWidgetBlueprintLibrary::SetInputMode_GameOnly(PlayerController); break;
			case EInputMode::GameAndUI:	UWidgetBlueprintLibrary::SetInputMode_GameAndUIEx(PlayerController, WidgetToFocus, MouseLockMode, bHideCursorDuringCapture); break;
			case EInputMode::UIOnly:	UWidgetBlueprintLibrary::SetInputMode_UIOnlyEx(PlayerController, WidgetToFocus, MouseLockMode); break;
			default: break;
			}
		}
	}
}

void AQuillscriptInterpreter::InputEnable() const
{
	if (const UWorld* World{ this->GetWorld() })
	{
		if (APlayerController* PlayerController{ World->GetFirstPlayerController() })
		{
			PlayerController->EnableInput(PlayerController);
			PlayerController->ResetIgnoreMoveInput();
			PlayerController->ResetIgnoreLookInput();
		}
	}
}

void AQuillscriptInterpreter::InputDisable() const
{
	if (const UWorld* World{ this->GetWorld() })
	{
		if (APlayerController* PlayerController{ World->GetFirstPlayerController() })
		{
			PlayerController->DisableInput(PlayerController);
			PlayerController->SetIgnoreMoveInput(true);
			PlayerController->SetIgnoreLookInput(true);
		}
	}
}

void AQuillscriptInterpreter::ShowMouseCursor() const
{
	if (const UWorld* World{ this->GetWorld() })
		if (APlayerController* PlayerController{ World->GetFirstPlayerController() })
			PlayerController->bShowMouseCursor = true;
}

void AQuillscriptInterpreter::HideMouseCursor() const
{
	if (const UWorld* World{ this->GetWorld() }; World)
		if (APlayerController* PlayerController{ World->GetFirstPlayerController() })
			PlayerController->bShowMouseCursor = false;
}

#pragma endregion Input


#pragma region UI

void AQuillscriptInterpreter::CreateDialogBox()
{
	if (!UQuillscriptSettings::Get()->GetManageDialogueBox())
		return;

	// Remove the previous Dialog Box widget if a new class is given.
	if (this->DialogBox && this->DialogBox->GetClass() != this->Script->Settings.DialogBoxClass)
	{
		this->DialogBox->RemoveFromParent();
		this->DialogBox->ConditionalBeginDestroy();
		this->DialogBox = nullptr;
	}

	// Create Dialog Box widget if it doesn't exist.
	if (!this->DialogBox && this->Script->Settings.DialogBoxClass)
	{
		this->DialogBox = Cast<UDialogBox>(
			CreateWidget(
				this->GetWorld(),
				this->Script->Settings.DialogBoxClass,
				FName(FGuid::NewGuid().ToString())
			)
		);

		// Assigns to dialogue events.
		this->DialogBox->OnAdvance.AddDynamic(this, &AQuillscriptInterpreter::Next);
		this->DialogBox->OnRollback.AddDynamic(this, &AQuillscriptInterpreter::Rollback);
	}
	else if (!this->Script->Settings.DialogBoxClass)
		ERROR("AQuillscriptInterpreter::CreateDialogBox() -> Dialog Box class is not set.");
}

void AQuillscriptInterpreter::CreateSelectionBox()
{
	if (!UQuillscriptSettings::Get()->GetManageSelectionBox())
		return;

	// Remove the previous Selection Box widget if a new class is given.
	if (this->SelectionBox && this->SelectionBox->GetClass() != this->Script->Settings.SelectionBoxClass)
	{
		this->SelectionBox->RemoveFromParent();
		this->SelectionBox->ConditionalBeginDestroy();
		this->SelectionBox = nullptr;
	}

	// Create Selection Box widget if it doesn't exist.
	if (!this->SelectionBox && this->Script->Settings.SelectionBoxClass)
	{
		this->SelectionBox = Cast<USelectionBox>(
			CreateWidget(
				this->GetWorld(),
				this->Script->Settings.SelectionBoxClass,
				FName(FGuid::NewGuid().ToString())
			)
		);

		// Assigns to option events.
		this->SelectionBox->OnSelected.AddDynamic(this, &AQuillscriptInterpreter::OptionSelected);
		this->SelectionBox->OnRollback.AddDynamic(this, &AQuillscriptInterpreter::Rollback);
	}
	else if (!this->Script->Settings.SelectionBoxClass)
		ERROR("AQuillscriptInterpreter::CreateSelectionBox() -> Selection Box class is not set.");
}

void AQuillscriptInterpreter::CreateBackgroundBox()
{
	if (!UQuillscriptSettings::Get()->GetManageBackgroundBox())
		return;

	// Remove the previous Background Box widget if a new class is given.
	if (this->BackgroundBox && this->BackgroundBox->GetClass() != this->Script->Settings.BackgroundBoxClass)
	{
		this->BackgroundBox->RemoveFromParent();
		this->BackgroundBox->ConditionalBeginDestroy();
		this->BackgroundBox = nullptr;
	}

	// Create Background Box widget if it doesn't exist.
	if (!this->BackgroundBox && this->Script->Settings.BackgroundBoxClass)
	{
		this->BackgroundBox = Cast<UBackgroundBox>(
			CreateWidget(
				this->GetWorld(),
				this->Script->Settings.BackgroundBoxClass,
				FName(FGuid::NewGuid().ToString())
			)
		);

		// Assigns to background events.
		// this->BackgroundBox->OnImageChanged.AddDynamic(this, &AQuillscriptInterpreter::);
	}
	else if (!this->Script->Settings.BackgroundBoxClass)
		ERROR("AQuillscriptInterpreter::CreateBackgroundBox() -> Background Box class is not set.");
}

void AQuillscriptInterpreter::Use(const FString WidgetClassPath) const
{
	// Reset to default.
	if (WidgetClassPath.Equals("Defaults"))
	{
		this->Script->Settings.DialogBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().DialogBoxClass;
		this->Script->Settings.SelectionBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().SelectionBoxClass;
		this->Script->Settings.BackgroundBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().BackgroundBoxClass;
		this->Script->Settings.SpriteBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().SpriteBoxClass;
		return;
	}

	if (WidgetClassPath.Equals("DialogBox"))
	{ this->Script->Settings.DialogBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().DialogBoxClass; return; }

	if (WidgetClassPath.Equals("SelectionBox"))
	{ this->Script->Settings.SelectionBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().SelectionBoxClass; return; }

	if (WidgetClassPath.Equals("BackgroundBox"))
	{ this->Script->Settings.BackgroundBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().BackgroundBoxClass; return; }

	if (WidgetClassPath.Equals("SpriteBox"))
	{ this->Script->Settings.SpriteBoxClass = UQuillscriptSettings::Get()->GetScriptSettings().SpriteBoxClass; return; }

	// Find class and inheritance.
	if (UClass* Class{ UTools::FindClassByPath(WidgetClassPath) })
	{
		if (const TSubclassOf<UDialogBox> DialogBoxClass{ Class })
		{ this->Script->Settings.DialogBoxClass = DialogBoxClass; return; }

		if (const TSubclassOf<USelectionBox> SelectionBoxClass{ Class })
		{ this->Script->Settings.SelectionBoxClass = SelectionBoxClass; return; }

		if (const TSubclassOf<UBackgroundBox> BackgroundBoxClass{ Class })
		{ this->Script->Settings.BackgroundBoxClass = BackgroundBoxClass; return; }

		if (const TSubclassOf<USpriteBox> SpriteBoxClass{ Class })
		{ this->Script->Settings.SpriteBoxClass = SpriteBoxClass; return; }
	}

	ERROR("Use() -> Class is not a keyword, nor a Quillscript widget class: " + WidgetClassPath);
}

void AQuillscriptInterpreter::ShowDialogBox() const
{
	if (this->DialogBox && !this->DialogBox->IsInViewport() && !this->DialogBox->GetParent())
		this->DialogBox->AddToViewport(UQuillscriptSettings::Get()->GetDialogBoxLayer());
}

void AQuillscriptInterpreter::ShowSelectionBox() const
{
	if (this->SelectionBox && !this->SelectionBox->IsInViewport() && !this->SelectionBox->GetParent())
		this->SelectionBox->AddToViewport(UQuillscriptSettings::Get()->GetSelectionBoxLayer());
}

void AQuillscriptInterpreter::ShowBackgroundBox() const
{
	if (this->BackgroundBox && !this->BackgroundBox->IsInViewport() && !this->BackgroundBox->GetParent())
		this->BackgroundBox->AddToViewport(UQuillscriptSettings::Get()->GetBackgroundBoxLayer());
}

void AQuillscriptInterpreter::RemoveDialogBox() const
{
	if (this->DialogBox && ( this->DialogBox->IsInViewport() || this->DialogBox->GetParent() ))
		this->DialogBox->RemoveFromParent();
}

void AQuillscriptInterpreter::RemoveSelectionBox() const
{
	if (this->SelectionBox && ( this->SelectionBox->IsInViewport() || this->SelectionBox->GetParent() ))
		this->SelectionBox->RemoveFromParent();
}

void AQuillscriptInterpreter::RemoveBackgroundBox() const
{
	if (this->BackgroundBox && ( this->BackgroundBox->IsInViewport() || this->BackgroundBox->GetParent() ))
		this->BackgroundBox->RemoveFromParent();
}

void AQuillscriptInterpreter::Show() const
{
	if (IsValid(this->GetWorld()))
	{
		// Wait 2 frames.
		this->GetWorld()->GetTimerManager().SetTimerForNextTick([this]()
		{
			this->GetWorld()->GetTimerManager().SetTimerForNextTick([this]()
			{
				if (this->DialogBox)
					this->DialogBox->SetVisibility(ESlateVisibility::Visible);

				if (this->SelectionBox)
					this->SelectionBox->SetVisibility(ESlateVisibility::Visible);
			});
		});
	}
}

void AQuillscriptInterpreter::Hide() const
{
	if (this->DialogBox)
		this->DialogBox->SetVisibility(ESlateVisibility::Collapsed);

	if (this->SelectionBox)
		this->SelectionBox->SetVisibility(ESlateVisibility::Collapsed);
}

void AQuillscriptInterpreter::Background(UTexture* Image, const FString Transition, const float Duration)
{
	// Create or update Background Box widget.
	this->CreateBackgroundBox();

	// Call Background Box.
	if (UQuillscriptSettings::Get()->GetManageBackgroundBox() && this->BackgroundBox)
	{
		this->BackgroundBox->Setup(this, Image);
		this->BackgroundBox->Play(Image, Transition, Duration);
	}
	else
		this->OnPlayBackgroundBox.Broadcast(this, Image, Transition, Duration);
}

void AQuillscriptInterpreter::Bg(UTexture* Image, const FString Transition, const float Duration)
{
	this->Background(Image, Transition, Duration);
}

void AQuillscriptInterpreter::Sprite(const FName Name, TSubclassOf<USpriteBox> Class)
{
	// Select Character class.
	if (!Class)
		Class = this->Script->Settings.SpriteBoxClass;

	// Create a new Sprite Box.
	if (!this->SpriteBoxes.Contains(Name) && Class)
	{
		this->SpriteBoxes.Add(Name, Cast<USpriteBox>(
			CreateWidget(
				this->GetWorld(),
				Class,
				FName(FGuid::NewGuid().ToString())
			)
		));

		// Pass references.
		this->SpriteBoxes[Name]->Setup(this);

		// Assigns to Character events.
		// this->SpriteBoxes[Name]->OnAdvance.AddDynamic(this, &AQuillscriptInterpreter::Next);

		// Create a reference to use in the script.
		UQuill::AddScriptReference(this, Name, this->SpriteBoxes[Name]);
	}

	else if (!Class)
		ERROR("AQuillscriptInterpreter::Sprite() -> Sprite Box class is not set.");
}

#pragma endregion UI


#pragma region Media

void AQuillscriptInterpreter::PlaySound(USoundBase* Sound, FName Channel, float Volume, const float FadeDuration)
{
	// Blueprint omitted defaults.
	if (Channel.IsNone() && Volume == 0 && FadeDuration == 0)
	{ Channel = "default"; Volume = 1; }

	if (IsValid(Sound))
	{
		// Add Interpreter's sound channel if it doesn't exist.
		if (!this->AudioComponents.Contains(Channel))
			this->AudioComponents.Add(Channel);

		// Create an Audio Component for Interpreter's sound channel if it wasn't created yet or was destroyed.
		if (!IsValid(this->AudioComponents[Channel]))
		{
			this->AudioComponents[Channel] = UGameplayStatics::CreateSound2D(this, Sound);
			this->AudioComponents[Channel]->bAutoDestroy = false;

			this->AudioComponents[Channel]->OnAudioFinishedNative.AddLambda([this, Channel](UAudioComponent* AudioComponent)
			{
				this->OnAudioFinished.Broadcast(this, Channel, AudioComponent);
			});
		}
		else
			this->AudioComponents[Channel]->SetSound(Sound);

		// Play sound.
		this->AudioComponents[Channel]->FadeIn(FadeDuration, Volume);
	}
	else
		WARNING("Invalid sound asset");
}

void AQuillscriptInterpreter::Voice(USoundBase* Sound, float Volume)
{
	// Blueprint omitted defaults.
	if (Volume == 0) { Volume = 1; }

	this->PlaySound(Sound, "voice", Volume);
}

void AQuillscriptInterpreter::Music(USoundBase* Sound, float Volume, float FadeDuration)
{
	// Blueprint omitted defaults.
	if (Volume == 0 && FadeDuration == 0) { Volume = 0.5; FadeDuration = 3; }

	this->PlaySound(Sound, "music", Volume, FadeDuration);
}

void AQuillscriptInterpreter::SFX(USoundBase* Sound, float Volume)
{
	// Blueprint omitted defaults.
	if (Volume == 0) { Volume = 1; }

	this->PlaySound(Sound, "SFX", Volume);
}

void AQuillscriptInterpreter::StopSound(const FName Channel, const float FadeDuration)
{
	if (this->AudioComponents.Contains(Channel))
		this->AudioComponents[Channel]->FadeOut(FadeDuration, 0);
}

void AQuillscriptInterpreter::StopAllSounds(const float FadeDuration)
{
	for (const auto& AudioComponent : this->AudioComponents)
		AudioComponent.Value->FadeOut(FadeDuration, 0);
}

void AQuillscriptInterpreter::PlayAnimation(USkeletalMeshComponent* SkeletalMeshComponent, UAnimationAsset* Animation, const bool bLoop)
{
	if (SkeletalMeshComponent && Animation)
		SkeletalMeshComponent->PlayAnimation(Animation, bLoop);
}

float AQuillscriptInterpreter::VoiceTypingSpeed(const float DefaultDuration) const
{
	if (const auto& VoiceAudioComponent{ this->AudioComponents.FindRef("voice") })
		if (const auto& VoiceSoundAsset{ VoiceAudioComponent->Sound })
			if (const auto& TextLength{ UTools::RemoveRichTextTags(this->GetCurrentStatement().Text.ToString()).Len() }; TextLength > 1)
				return ( VoiceSoundAsset->Duration + USmartTextBlockDecorator::ConvertDelayToSeconds(this->GetCurrentStatement().Text.ToString()) ) / ( TextLength - 1 );

	return DefaultDuration;
}

#pragma endregion Media


#pragma region Helper

int32 AQuillscriptInterpreter::Roll(const int32 DieSides, int32 Quantity)
{
	int32 Result{ 0 };
	Quantity = Quantity <= 0 ? 1 : Quantity;

	for (int32 I{ 0 }; I < Quantity; ++I)
		Result += UKismetMathLibrary::RandomIntegerInRange(1, DieSides);

	return Result;
}

#pragma endregion Helper


#pragma region Instructions

void AQuillscriptInterpreter::PlayDialogueBox(const FStatement Dialogue)
{
	// Create or update the Dialog Box widget.
	this->CreateDialogBox();

	// Replace variables.
	const FStatement ReplacedDialogue{ this->ReplaceVariablesInStatement(Dialogue) };

	// Initialize.
	if (this->DialogBox)
	{
		this->DialogBox->Setup(this, Dialogue);
		this->DialogBox->Play(ReplacedDialogue.Main, ReplacedDialogue.Text, ReplacedDialogue.Tags);
	}
}

void AQuillscriptInterpreter::PlaySelectionBox(const TArray<FStatement> Options)
{
	// Create or update Selection Box widget.
	this->CreateSelectionBox();

	// Pre-evaluate each option.
	TArray<FEvaluatedOption> EvaluatedOptions;

	for (FStatement Option : Options)
	{
		EvaluatedOptions.Add(
			FEvaluatedOption {
				EVAL(Option.Conditions),
				Option.Text.IsEmpty() ? FText::FromString(Option.Main) : Option.Text,
				Option.Tags
			}
		);
	}

	// Initializes.
	if (this->SelectionBox)
	{
		this->SelectionBox->Setup(this, Options);
		this->SelectionBox->Play(EvaluatedOptions);
	}
}

void AQuillscriptInterpreter::ExecuteCommand(const FExpression CommandInstruction)
{
	// Replace variables.
	TArray Parameters{ CommandInstruction.GetParametersAsStrings() };

	for (FString& Parameter : Parameters)
		Parameter = REPLACE(Parameter);

	// It's a variable assignment.
	if (CommandInstruction.IsAssignment())
	{
		// Stop if it's a new assignment and variable already exists.
		if (
			CommandInstruction.Symbol.StartsWith(SYMBOL(Constructor) + SYMBOL(Assignment)) &&
			UQuill::QuillscriptVariableExists(this, FName(CommandInstruction.GetVariableName()))
		) return;

		// Set variable.
		SET_VAR(
			FName(CommandInstruction.GetVariableName()),
			FText::FromString(FEvaluator::Solve(Parameters))
		);
	}

	// It's a function call.
	else
		this->CallFunction(CommandInstruction.Symbol, Parameters);
}

void AQuillscriptInterpreter::ExecuteCommands(TArray<FExpression> CommandInstructions)
{
	for (const FExpression& CommandInstruction : CommandInstructions)
		this->ExecuteCommand(CommandInstruction);
}

void AQuillscriptInterpreter::GoToTarget(const FName TargetLabel, const TArray<FText> Arguments, const bool bChannel)
{
	// Register Router index, for callback.
	this->State.RouterIndexes.Add(this->State.CurrentIndex);

	// Mark callback.
	if (bChannel)
		this->State.ChannelCalledLabel = TargetLabel;

	// Create template variables.
	if (!Arguments.IsEmpty())
	{
		this->CreateTemplateVariables(TargetLabel, Arguments);
		this->State.TemplateCalledLabel = TargetLabel;
	}

	// Play.
	this->bRouterCall = true;
	this->PlayByLabel(NAME_REPLACE(TargetLabel));
}

#pragma endregion Instructions


#pragma region Evaluation

bool AQuillscriptInterpreter::EvaluateCondition(FExpression Condition) const
{
	// Check god mode.
	if (const UQuillscriptSubsystem* QuillscriptSubsystem{ this->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		if (QuillscriptSubsystem->GetBypassConditions())
			return true;

	// Replace variables.
	Condition.Symbol = REPLACE(Condition.Symbol);

	for (FText& Parameter : Condition.Parameters)
		Parameter =  TEXT_REPLACE(Parameter);

	// Evaluate.
	return FEvaluator::Evaluate(Condition.GetParametersAsStrings());
}

bool AQuillscriptInterpreter::EvaluateConditions(const TArray<FExpression> Conditions) const
{
	for (const FExpression& Condition : Conditions)
		if (!this->EvaluateCondition(Condition))
			return false;

	return true;
}

#pragma endregion Evaluation


#pragma region Directives

void AQuillscriptInterpreter::ExecuteCheckpointDirective(const FStatement& Directive)
{
	if (const UWorld* World{ this->GetWorld() })
	{
		// Stop script flow.
		this->Stop();
		this->CheckpointDirective = Directive;

		// Get evaluations interval.
		float Interval{ 0 };
		FString IntervalString;

		if (Directive.Main.StartsWith(FLexer::DirectiveCheckpoint + " "))
		{
			Directive.Main.Split(" ", nullptr, &IntervalString);
			Interval = FCString::Atof(*IntervalString);
		}

		// Set a timer to evaluate the condition on every given interval.
		if (Interval > 0)
		{
			World->GetTimerManager().SetTimer(
				TimerHandleRef,

				// Callback method to restore script flow.
				FTimerDelegate::CreateLambda([this]()
				{
					this->EvaluateCheckpointDirective();
				}),

				Interval,
				true
			);
		}

		// Set a flag to evaluate condition every frame, in this Interpreter's Tick() method.
		else
			this->bEvaluateCheckpointDirectiveEveryFrame = true;
	}
}

#pragma endregion Directives


#pragma region Tasks

bool AQuillscriptInterpreter::IsFresh() const
{
	return this->Script ? false : true;
}

void AQuillscriptInterpreter::Snapshot() const
{
	FSaveState SaveState;

	// Current global state.
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ this->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		SaveState.Variables = QuillscriptSubsystem->GetVariables();

	// Current interpreter state.
	SaveState.LabelName = this->GetCurrentStatement().Label;
	SaveState.InterpreterState = this->State;

	// Current script state.
	SaveState.ScriptSettings = this->Script->Settings;

	// Current background box image.
	if (this->BackgroundBox && this->BackgroundBox->GetImage())
		SaveState.BackgroundImagePath = this->BackgroundBox->GetImage()->GetPathName();

	// Save any audio playing in loop. (Background music)
	for (const auto& AudioComponent : this->AudioComponents)
	{
		if (
			IsValid(AudioComponent.Value) &&
			AudioComponent.Value->IsPlaying() &&
			AudioComponent.Value->Sound->IsLooping()
		)
		{
			FSoundState Sound;

			Sound.Channel = AudioComponent.Key;
			Sound.AssetPath = AudioComponent.Value->GetPathName();
			Sound.Volume = AudioComponent.Value->VolumeMultiplier;

			SaveState.Sounds.Add(Sound);
		}
	}

	this->Script->PushToHistory(this, SaveState);
}

void AQuillscriptInterpreter::CallFunction(const FString& FunctionAddress, TArray<FString> Parameters)
{
	// Replace a switch type to a boolean type.
	for (FString& Parameter : Parameters)
	{
		if (Parameter.Equals(SYMBOL(On)))
			Parameter = "true";
		else if (Parameter.Equals(SYMBOL(Off)))
			Parameter = "false";
	}

	// Split address into: 'Root Object Name', 'N Properties Names', and 'Function Name'.
	TArray<FString> PropertiesNames;
	FunctionAddress.ParseIntoArray(PropertiesNames, *SYMBOL(Functor));

	const FString MemberName{ PropertiesNames.Pop() };
	FString RootObjectsName;

	if (!PropertiesNames.IsEmpty())
	{
		RootObjectsName = PropertiesNames[0];
		PropertiesNames.RemoveAt(0);
	}

	/// Get root objects.
	TArray<UObject*> RootObjects;

	if (RootObjectsName.RemoveFromStart(SYMBOL(Reference)))						// Named Object.
		RootObjects = this->GetRootObjectsByName(RootObjectsName);
	else if (RootObjectsName.RemoveFromStart(SYMBOL(Class)))					// All objects of class.
	{
		// On a class call, the first property is actually the class name.
		if (PropertiesNames.IsValidIndex(0))
			RootObjectsName = RootObjectsName + SYMBOL(Functor) + PropertiesNames.Pop();

		RootObjects = this->GetRootObjectsByClass(RootObjectsName);
	}
	else if (RootObjectsName.RemoveFromStart(SYMBOL(ByTag)))					// All objects with tag.
		RootObjects = this->GetRootObjectsByTag(RootObjectsName);
	else																		// Local call.
		RootObjects.Add(this);

	if (RootObjects.IsEmpty())
	{ WARNING("Cant find object designated as '" + FunctionAddress + "'."); return; }

	// Get the function owner (Targets) from each root object, using the address remaining properties.
	TArray<UObject*> Targets;
	for (UObject* RootObject : RootObjects)
		Targets.Add(this->GetObjectLastProperty(RootObject, PropertiesNames));

	// Call members.
	for (UObject* Target : Targets)
		this->CallMemberOnTarget(Target, MemberName, Parameters);
}

TArray<FStatement> AQuillscriptInterpreter::CreateDynamicOptionsSet(const TArray<FStatement>& Options)
{
	TArray<FStatement> OptionsSet;

	for (const auto& Option : Options)
	{
		// Dynamic option.
		if (FString OptionTextAsString{ Option.Text.ToString() }; Option.Main == SYMBOL(Option) && OptionTextAsString.RemoveFromStart(SYMBOL(Option)))
		{
			// Get the array names and values.
			TArray ArraysNames{ UTools::GetVariablesInString(OptionTextAsString) };
			TArray<FString> ArraysValues;

			for (auto& ArrayName : ArraysNames)
			{
				if (ArrayName.RemoveFromStart(SYMBOL(Option)))
					ArraysValues.Add(VAR(FName(ArrayName)));
			}

			// Find the smallest array.
			int32 SmallestArrayLength{ MAX_int32 };

			for (auto& ArrayValue : ArraysValues)
				if (const int32 ArrayLength{ UTools::Length(ArrayValue) }; ArrayLength < SmallestArrayLength)
					SmallestArrayLength = ArrayLength;

			// Replace array entries.
			auto ReplaceArrayEntries = [ArraysNames, ArraysValues](FString Value, const int32& Index)
			{
				for (int32 J{ 0 }; J < ArraysNames.Num(); ++J)
					Value = Value.Replace(*(  SYMBOL(CurlyOpen) + SYMBOL(Option) + ArraysNames[J] + SYMBOL(CurlyClose) ), *FLexer::GetFromArrayString(ArraysValues[J], Index), ESearchCase::IgnoreCase);

				return Value;
			};

			for (int32 I{ 0 }; I < SmallestArrayLength; ++I)
			{
				FStatement NewOption{ Option };

				NewOption.Label = "";	// Clear label for safety.

				for (auto& Argument : NewOption.Arguments)
					Argument = ReplaceArrayEntries(Argument, I);

				NewOption.Main = ReplaceArrayEntries(NewOption.Main, I);
				NewOption.Text = TXT(ReplaceArrayEntries(STR(OptionTextAsString), I));

				for (auto& Condition : NewOption.Conditions)
					for (auto& Parameter : Condition.Parameters)
						Parameter = TXT(ReplaceArrayEntries(STR(Parameter), I));

				for (auto& Command : NewOption.Commands)
					for (auto& Parameter : Command.Parameters)
						Parameter = TXT(ReplaceArrayEntries(STR(Parameter), I));

				for (auto& Tag : NewOption.Tags)
					Tag = ReplaceArrayEntries(Tag, I);

				NewOption.Target = FName(ReplaceArrayEntries(STR(NewOption.Target), I));

				for (auto& TargetArgument : NewOption.TargetArguments)
					TargetArgument = TXT(ReplaceArrayEntries(STR(TargetArgument), I));

				for (auto& ExtraParameter : NewOption.ExtraParameters)
					ExtraParameter = TXT(ReplaceArrayEntries(STR(ExtraParameter), I));

				OptionsSet.Add(NewOption);
			}
		}

		// From Command.
		else if (Option.Main == SYMBOL(Option) && OptionTextAsString.IsEmpty())
		{
			this->ExecuteCommands(Option.Commands);

			if (const TObjectPtr<UQuillscriptSubsystem> QuillscriptSubsystem{ UQuillscriptSubsystem::World()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
			{
				OptionsSet.Append(QuillscriptSubsystem->InjectOptions);
				QuillscriptSubsystem->InjectOptions.Empty();
			}
		}

		// Normal option.
		else
			OptionsSet.Add(Option);
	}

	return OptionsSet;
}

#pragma endregion Tasks


#pragma region Internal

void AQuillscriptInterpreter::IncrementTimesPlayed() const
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ this->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		QuillscriptSubsystem->GetHistory()[this->Script->GetId()].TimesPlayed++;
}

void AQuillscriptInterpreter::DeleteTemporaryData() const
{
	// Clear all kinds of temporary variables.
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ this->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		TMap<FName, FText>& Variables{ QuillscriptSubsystem->GetVariables() };
		TArray<FName> VariablesNames;
		Variables.GenerateKeyArray(VariablesNames);

		for (FName VariableName : VariablesNames)
			if (
				VariableName.ToString().StartsWith(SYMBOL(Temp)) ||
				VariableName.ToString().StartsWith(SYMBOL(Out)) ||
				VariableName.ToString().StartsWith(SYMBOL(Arg)) ||
				VariableName.ToString().StartsWith(SYMBOL(Reference))
			)
				Variables.Remove(VariableName);

	}

	// Clear null script references.
	UQuill::ClearNullScriptReferences(this);
}

void AQuillscriptInterpreter::CreateTemplateVariables(const FName Target, TArray<FText> Arguments) const
{
	// Find arguments.
	TArray ArgumentsNames{ this->Script->GetStatementByLabel(Target).Arguments };

	// Create variables.
	for (int32 I = 0 ; I < ArgumentsNames.Num() && I < Arguments.Num(); I++)
		SET_ARG(ArgumentsNames[I], TEXT_REPLACE(Arguments[I]));
}

void AQuillscriptInterpreter::DeleteTemplateVariables() const
{
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ this->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		auto Variables{ QuillscriptSubsystem->GetVariables() };

		for (TPair<FName, FText> Variable : Variables)
			if (Variable.Key.ToString().StartsWith(SYMBOL(Arg)))
				UQuill::DeleteQuillscriptVariable(this, Variable.Key);
	}
}

void AQuillscriptInterpreter::ApplyScriptSettingsDuring() const
{
	// Mouse cursor.
	if (this->Script->Settings.ShowMouseCursorDuring != EPicker::Default)
		UQuill::PickerToBoolean(this->Script->Settings.ShowMouseCursorDuring) ? this->ShowMouseCursor() : this->HideMouseCursor();

	// Input.
	if (this->Script->Settings.EnableInputDuring != EPicker::Default)
		UQuill::PickerToBoolean(this->Script->Settings.EnableInputDuring) ? this->InputEnable() : this->InputDisable();

	// Input mode.
	this->SetInputMode(this->Script->Settings.InputModeDuring);
}

void AQuillscriptInterpreter::ApplyScriptSettingsAfter() const
{
	// Mouse cursor.
	if (this->Script->Settings.ShowMouseCursorAfter != EPicker::Default)
		UQuill::PickerToBoolean(this->Script->Settings.ShowMouseCursorAfter) ? this->ShowMouseCursor() : this->HideMouseCursor();

	// Input.
	if (this->Script->Settings.EnableInputAfter != EPicker::Default)
		UQuill::PickerToBoolean(this->Script->Settings.EnableInputAfter) ? this->InputEnable() : this->InputDisable();

	// Input mode.
	this->SetInputMode(this->Script->Settings.InputModeAfter);
}

void AQuillscriptInterpreter::EvaluateCheckpointDirective()
{
	// Execute all commands before performing the conditions' evaluation.
	this->ExecuteCommands(this->CheckpointDirective.Commands);

	// Evaluate conditions.
	if (this->EvaluateConditions(this->CheckpointDirective.Conditions))
	{
		this->Restore();
		this->Next();
	}
}

#pragma endregion Internal


#pragma region CallFunction

UObject* AQuillscriptInterpreter::GetObjectLastProperty(UObject* RootObject, TArray<FString> PropertiesList) const
{
	if (RootObject)
	{
		for (const FString& PropertyName : PropertiesList)
		{
			if (FProperty* Property{ RootObject->GetClass()->FindPropertyByName(*PropertyName) })
			{
				if (const FObjectProperty* ObjectProperty{ CastField<FObjectProperty>(Property) })
				{
					const void* Pointer{ Property->ContainerPtrToValuePtr<void>(RootObject) };
					RootObject = ObjectProperty->GetObjectPropertyValue(Pointer);
				}
				/*
				else if (const FStructProperty* StructProperty{ CastField<FStructProperty>(Property) })
				{
					const void* Pointer{ StructProperty->ContainerPtrToValuePtr<UStruct>(RootObject) };
					RootObject = StructProperty->Struct;
				}
				*/
				else
					WARNING("GetObjectLastProperty() -> Property '" + PropertyName + "' is not an object.");
			}
			else
				WARNING("GetObjectLastProperty() -> Property '" + PropertyName + "' not found on " + RootObject->GetName() + ".");
		}
	}

	return RootObject;
}

TArray<UObject*> AQuillscriptInterpreter::GetRootObjectsByName(const FString& RootObjectsName)
{
	TArray<UObject*> RootObjects;

	// Script references.
	if (UQuillscriptSubsystem* QuillscriptSubsystem{ this->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
	{
		if (UObject** Reference{ QuillscriptSubsystem->GetReferences().Find(FName(RootObjectsName)) })
		{
			RootObjects.Add(*Reference);
			return RootObjects;
		}
	}

	// Asset path.
	if (UObject* Reference{ this->Script->FindScriptReference(RootObjectsName) })
	{
		RootObjects.Add(Reference);
		return RootObjects;
	}

	// Shortcuts.
	if (RootObjectsName == "GameInstance")
		RootObjects.Add(this->GetGameInstance());
	else if (RootObjectsName == "PlayerController")
		RootObjects.Add(UGameplayStatics::GetPlayerController(this, 0));
	else if (RootObjectsName == "GameMode")
		RootObjects.Add(UGameplayStatics::GetGameMode(this));
	else if (RootObjectsName == "Pawn")
		RootObjects.Add(UGameplayStatics::GetPlayerPawn(this, 0));
	else if (RootObjectsName == "Character")
		RootObjects.Add(UGameplayStatics::GetPlayerCharacter(this, 0));
	else if (RootObjectsName == "GameState")
		RootObjects.Add(UGameplayStatics::GetGameState(this));
	else if (RootObjectsName == "PlayerState")
		RootObjects.Add(UGameplayStatics::GetPlayerState(this, 0));
	else if (RootObjectsName == "PlayerCameraManager")
		RootObjects.Add(UGameplayStatics::GetPlayerCameraManager(this, 0));
	else if (RootObjectsName == "Interpreter" || RootObjectsName == "this")
		RootObjects.Add(this);
	else if (RootObjectsName == "Script")
		RootObjects.Add(this->Script);
	else if (RootObjectsName == "Target")
		RootObjects.Add(this->Script->GetTarget());
	else if (RootObjectsName == "DialogBox")
		RootObjects.Add(this->DialogBox);
	else if (RootObjectsName == "SelectionBox")
		RootObjects.Add(this->SelectionBox);
	else if (RootObjectsName == "BackgroundBox")
		RootObjects.Add(this->BackgroundBox);
	else if (RootObjectsName == "HUD")
	{
		if (const TObjectPtr<AHUD> HUD{ Cast<AHUD>(this->GetWorld()->GetFirstPlayerController()->GetHUD()) })
			RootObjects.Add(HUD);
	}
	else if (RootObjectsName == "Level")
	{
		if (const TObjectPtr<UWorld> World{ this->GetWorld() })
			RootObjects.Add(World->GetLevelScriptActor());
	}
	else if (RootObjectsName == "World")
	{
		if (const TObjectPtr<UWorld> World{ this->GetWorld() })
			RootObjects.Add(World);
	}
	else if (RootObjectsName == "Subsystem")
	{
		if (const TObjectPtr<UQuillscriptSubsystem> Subsystem{ this->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
			RootObjects.Add(Subsystem);
	}

	// Custom named.
	else
	{
		// Actor.
		if (RootObjects.IsEmpty())
		{
			TArray<AActor*> Actors;
			UGameplayStatics::GetAllActorsOfClass(this, AActor::StaticClass(), Actors);

			for (AActor* Actor : Actors)
			{
				if (Actor->GetName() == RootObjectsName || UKismetSystemLibrary::GetDisplayName(Actor) == RootObjectsName)
				{
					RootObjects.Add(Actor);
					break;
				}
			}
		}

		// User widget.
		if (RootObjects.IsEmpty())
		{
			TArray<UUserWidget*> Widgets;
			UWidgetBlueprintLibrary::GetAllWidgetsOfClass(this, Widgets, UUserWidget::StaticClass(), false);

			for (UWidget* Widget : Widgets)
			{
				if (Widget->GetName() == RootObjectsName || UKismetSystemLibrary::GetDisplayName(Widget) == RootObjectsName)
				{
					RootObjects.Add(Widget);
					break;
				}
			}
		}
	}

	return RootObjects;
}

TArray<UObject*> AQuillscriptInterpreter::GetRootObjectsByClass(const FString& RootObjectsClassName)
{
	TObjectPtr<UClass> Class;

	// C++ Class.
	if (RootObjectsClassName.Contains("."))
	{
		FString ClassPath{ RootObjectsClassName };

		if (!ClassPath.StartsWith("/"))
			ClassPath = "/" + ClassPath;

		if (!ClassPath.StartsWith("/Script/"))
			ClassPath = "/Script" + ClassPath;

		// Class = LoadClass<UObject>(this, *ClassPath);
		const FSoftClassPath SoftClassPath{ ClassPath };
		Class = SoftClassPath.TryLoadClass<UObject>();
	}

	// Blueprint Class.
	if (!Class)
	{
		FString ClassPath, ClassName;
		RootObjectsClassName.Split("/", &ClassPath, &ClassName, ESearchCase::CaseSensitive, ESearchDir::FromEnd);
		ClassPath = RootObjectsClassName + "." + ClassName + "_C";

		if (!ClassPath.StartsWith("/"))
			ClassPath = "/" + ClassPath;

		// Class = LoadClass<UObject>(this, *ClassPath);
		const FSoftClassPath SoftClassPath{ ClassPath };
		Class = SoftClassPath.TryLoadClass<UObject>();
	}

	// Get all Objects of the class.
	TArray<UObject*> ObjectsOfClass;

	if (Class)
	{
		// Interface
		if (Class->GetSuperClass() == UInterface::StaticClass() || Class->HasAnyClassFlags(CLASS_Interface))
		{
			// Get all Actors of interface.
			TArray<AActor*> ActorsOfInterface;
			UGameplayStatics::GetAllActorsWithInterface(this, Class, ActorsOfInterface);

			for (AActor* ActorOfInterface : ActorsOfInterface)
				ObjectsOfClass.Add(ActorOfInterface);

			// Get all Widgets of interface.
			TArray<UUserWidget*> WidgetsOfInterface;
			UWidgetBlueprintLibrary::GetAllWidgetsWithInterface(this, WidgetsOfInterface, Class, false);

			for (UUserWidget* WidgetOfInterface : WidgetsOfInterface)
				ObjectsOfClass.Add(WidgetOfInterface);
		}

		// Class
		else if (Class.IsA(UClass::StaticClass()))
		{
			// Get all Actors of class.
			TArray<AActor*> ActorsOfClass;
			UGameplayStatics::GetAllActorsOfClass(this, Class, ActorsOfClass);

			for (AActor* ActorOfClass : ActorsOfClass)
				ObjectsOfClass.Add(ActorOfClass);

			// Get all Widgets of class.
			TArray<UUserWidget*> WidgetsOfClass;
			UWidgetBlueprintLibrary::GetAllWidgetsOfClass(this, WidgetsOfClass, Class);

			for (UUserWidget* WidgetOfClass : WidgetsOfClass)
				ObjectsOfClass.Add(WidgetOfClass);
		}

		// Get Blueprint Function Library of class.
		if (ObjectsOfClass.IsEmpty())
			ObjectsOfClass.Add(Class);
	}
	else
		WARNING("GetRootObjectsByClass() -> Class '" + RootObjectsClassName + "' not found");

	return ObjectsOfClass;
}

TArray<UObject*> AQuillscriptInterpreter::GetRootObjectsByTag(const FString& RootObjectsTag) const
{
	TArray<UObject*> RootObjects;

	TArray<AActor*> ActorsWithTag;
	UGameplayStatics::GetAllActorsWithTag(this, FName(RootObjectsTag), ActorsWithTag);

	for (AActor* ActorWithTag : ActorsWithTag)
		RootObjects.Add(ActorWithTag);

	return RootObjects;
}

void AQuillscriptInterpreter::CallMemberOnTarget(UObject* Target, const FString& MemberName, const TArray<FString>& Parameters)
{
	if (!Target || MemberName.IsEmpty())
	{ ERROR("'Target' and 'FunctionCall' can't be null"); return; }


	// Use Target's class if no one was given.
	const UClass* Class{ Target->GetClass() };

	if (const UClass* TargetAsClass{ Cast<UClass>(Target) })
		Class = TargetAsClass;

	// Call function on Target.
	if (UFunction* Function{ Class->FindFunctionByName(*MemberName) })
		this->CallFunctionOnTarget(Target, Function, Parameters);

	// Call object property value.
	else if (const FProperty* Property{ Target->GetClass()->FindPropertyByName(*MemberName) })
		this->CallPropertyOnTarget(Target, Property);

	/*
	// Call struct property value.
	else if (UStruct* Struct{ Cast<UStruct>(Target) })
	{
		if (const FProperty* StructProperty{ Struct->FindPropertyByName(*MemberName) })
			this->CallPropertyOnTarget(Struct, StructProperty);
	}
	*/

	else
		WARNING("CallMemberOnTarget -> Target '" + Target->GetName() + "' has no member '" + MemberName + "'.");
}

void AQuillscriptInterpreter::CallFunctionOnTarget(UObject* Target, UFunction* Function, TArray<FString> Parameters)
{
	// Allocate parameters' memory.
	uint8* Buffer{ StaticCast<uint8*>(FMemory_Alloca(Function->ParmsSize)) };
	FMemory::Memzero(Buffer, Function->ParmsSize);

	// Set World Context parameter.
	auto SetWorldContext = [this, Buffer](const FProperty* FunctionProperty)
	{
		const FString Name{ FunctionProperty->GetName() };
		const FString Type{ FunctionProperty->GetCPPType() };

		if (
			Type == "UObject*" &&
			(
				Name == "__WorldContext" ||
				Name == "WorldContextObject" ||
				Name == "WorldContext"
			)
		)
		{
			*FunctionProperty->ContainerPtrToValuePtr<UObject*>(Buffer) = this->GetWorld();
			return true;
		}

		return false;
	};

	// Inject parameters.
	auto InjectParam = [this, Function, Buffer, SetWorldContext](const FProperty* FunctionProperty, FString Parameter)
	{
		const FString Type{ FunctionProperty->GetCPPType() };

		// Prevent crashing if the parameter was omitted.
		if (Parameter.IsEmpty())
			Parameter = "0";

		// Script reference (Pointer).
		if (Type.EndsWith("*") || Type.StartsWith("TSubclassOf"))
		{
			FString Name{ Parameter };
			UObject* Pointer{ nullptr };

			// Find in script reference or pass a null pointer otherwise.
			if (Name.RemoveFromStart(SYMBOL(CurlyOpen) + SYMBOL(Reference)) && Name.RemoveFromEnd(SYMBOL(CurlyClose)))
				if (TArray Objects{ GetRootObjectsByName(Name) }; !Objects.IsEmpty())
					Pointer = Objects[0];

			if (!Pointer)
				WARNING("Null pointer passed in function '" + Function->GetName() + "' at parameter: " + Parameter);

			*FunctionProperty->ContainerPtrToValuePtr<UObject*>(Buffer) = Pointer;
		}

		// ImportText treats punctuation in unquoted values as syntax. Quillscript
		// function arguments are already parsed strings, so assign FString
		// parameters directly and preserve payloads such as "melodia:battle:...".
		else if (const FStrProperty* StringProperty = CastField<FStrProperty>(FunctionProperty))
		{
			StringProperty->SetPropertyValue_InContainer(Buffer, Parameter);
		}

		// All other parameters' types.
		else
		{
			FunctionProperty->ImportText_Direct(
				*Parameter,
				FunctionProperty->ContainerPtrToValuePtr<void>(Buffer),
				Function,
				PPF_None
			);
		}
	};

	// Check if all parameters are named.
	bool bAreNamedParameters{ true };

	for (auto Parameter : Parameters)
	{
		if (!Parameter.StartsWith(SYMBOL(Arg)) || !Parameter.Contains(SYMBOL(Splitter)))
		{
			bAreNamedParameters = false;
			break;
		}
	}

	// Inject parameters by name.
	if (bAreNamedParameters)
	{
		TMap<FString, FString> NamedParameters;

		// Remove the argument name from each parameter.
		for (FString Parameter : Parameters)
		{
			Parameter.RemoveFromStart(SYMBOL(Arg));

			FString Key, Value;
			Parameter.Split(SYMBOL(Splitter), &Key, &Value);

			NamedParameters.Add(Key, Value);
		}

		// Inject parameters.
		for (TFieldIterator<FProperty> It{ Function }; It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			const FProperty* FunctionProperty{ *It };

			// Skip World Context parameter.
			if (SetWorldContext(FunctionProperty))
				continue;

			// Find the parameter by name and inject it.
			if (const auto* Parameter{ NamedParameters.Find(FunctionProperty->GetName()) })
				InjectParam(FunctionProperty, *Parameter);
		}
	}

	// Inject parameters in order.
	else
	{
		uint32 I{ 0 };

		for (TFieldIterator<FProperty> It{ Function }; It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			// Skip World Context parameter.
			if (SetWorldContext(*It))
				continue;

			// Inject parameter.
			if (Parameters.IsValidIndex(I))
			{
				InjectParam(*It, Parameters[I]);
				I++;
			}
			else
				break;
		}
	}

	// Call the function with parameters, on target.
	Target->ProcessEvent(Function, Buffer);

	// Get the return value and create a Quillscript variable for each. (Out Parameters)
	for (TFieldIterator<FProperty> It(Function, EFieldIteratorFlags::ExcludeSuper); It; ++It)
	{
		if (const FProperty* OutProperty{ *It }; OutProperty->HasAnyPropertyFlags(CPF_OutParm))
		{
			const FString Type{ OutProperty->GetCPPType() };

			// Script reference. (Pointers)
			if (Type.EndsWith("*"))
			{
				if (UObject* ReturnedPointer{ *OutProperty->ContainerPtrToValuePtr<UObject*>(Buffer) })
					UQuill::AddScriptReference(this, FName(OutProperty->GetName()), ReturnedPointer);
			}

			// All other parameters' types.
			else
			{
				FString Value;

				OutProperty->ExportText_Direct(
					Value,
					OutProperty->ContainerPtrToValuePtr<void>(Buffer),
					nullptr,
					Function,
					PPF_None
				);

				// Fix empty values.
				if (Value.IsEmpty())
				{
					if (Type == "bool")
						Value = "false";
					if (Type == "uint8" || Type == "int32" || Type == "int64" || Type == "float" || Type == "double")
						Value = "0";
				}

				// Create outer Quillscript variables.
				if (!Value.IsEmpty())
					this->CreateOuterQuillscriptVariable(OutProperty->GetName(), Value);
			}
		}
	}
}

void AQuillscriptInterpreter::CallPropertyOnTarget(UObject* Target, const FProperty* Property) const
{
	// Script reference. (Pointers)
	if (const FObjectProperty* ObjectProperty{ CastField<FObjectProperty>(Property) })
	{
		if (UObject* Pointer{ ObjectProperty->GetPropertyValue_InContainer(Target) })
			UQuill::AddScriptReference(this, FName(Property->GetName()), Pointer);
	}

	// Script reference. (Soft Object and Soft Class)
	else if (const FSoftObjectProperty* SoftObjectProperty{ CastField<FSoftObjectProperty>(Property) })
	{
		if (const TSoftObjectPtr Pointer{ SoftObjectProperty->GetObjectPropertyValue_InContainer(Target) })
			UQuill::AddScriptReference(this, FName(Property->GetName()), Pointer.Get());
	}

	// Script reference. (Weak Object)
	else if (const FWeakObjectProperty* WeakObjectProperty{ CastField<FWeakObjectProperty>(Property) })
	{
		if (const FWeakObjectPtr Pointer{ WeakObjectProperty->GetPropertyValue_InContainer(Target) }; Pointer.IsValid())
			UQuill::AddScriptReference(this, FName(Property->GetName()), Pointer.Get());
	}

	// Other types.
	else
	{
		FString Value;

		// Get value.
		Property->ExportText_Direct(
			Value,
			Property->ContainerPtrToValuePtr<void>(Target),
			nullptr,
			Target,
			PPF_None
		);

		// Fix empty values.
		if (Value.IsEmpty())
		{
			const FString Type{ Property->GetCPPType() };

			if (Type == "bool")
				Value = "false";
			if (Type == "uint8" || Type == "int32" || Type == "int64" || Type == "float" || Type == "double")
				Value = "0";
		}

		this->CreateOuterQuillscriptVariable(Property->GetName(), Value);
	}
}

void AQuillscriptInterpreter::CreateOuterQuillscriptVariable(const FString& Name, const FString& Value) const
{
	SET_VAR(FName(SYMBOL(Command) + Name), FText::FromString(Value));
}

#pragma endregion CallFunction


#if WITH_EDITOR

void AQuillscriptInterpreter::ReloadScript()
{
	if (!this->Script->IsCreatedDuringRuntime())
	{
		if (const TObjectPtr<UQuillscriptAsset> UpdatedScript{ this->RuntimeSourceScript })
		{
			// Create clean script object.
			const TObjectPtr<UQuillscriptAsset> TempScriptRef{ NewObject<UQuillscriptAsset>(this, UQuillscriptAsset::StaticClass(), FName(this->Script->GetName()), RF_NoFlags, UpdatedScript) };

			// Copy required data from current script object.
			TempScriptRef->Settings = this->Script->Settings;
			TempScriptRef->SetTarget(this->Script->GetTarget());

			// Set.
			this->Script = TempScriptRef->CreateReadyToPlayCopy();
			TempScriptRef->ConditionalBeginDestroy();
		}
	}
}

#endif
