// Copyright Bruno Caxito. All Rights Reserved.

#include "Quillscript.h"

#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Core/QuillscriptInterpreter.h"
#include "Core/QuillscriptSubsystem.h"
#include "Engine/GameInstance.h"
#include "Modules/ModuleManager.h"
#include "Utils/Quill.h"
#include "Utils/Tools.h"


void FQuillscriptModule::StartupModule()
{
	// Add console commands.
	if (!IsRunningCommandlet())
	{
		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Next"),
			TEXT("Foward script play if it is not stopped"),
			FConsoleCommandDelegate::CreateStatic(Cmd_Next),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Rollback"),
			TEXT("Backward script play if it is not stopped"),
			FConsoleCommandDelegate::CreateStatic(Cmd_Rollback),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.End"),
			TEXT("Terminate script play"),
			FConsoleCommandDelegate::CreateStatic(Cmd_End),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Stop"),
			TEXT("Stop script play"),
			FConsoleCommandDelegate::CreateStatic(Cmd_Stop),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Restore"),
			TEXT("Restore script play"),
			FConsoleCommandDelegate::CreateStatic(Cmd_Restore),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Play"),
			TEXT("Play statement by index.\n")
			TEXT("  Index: positive integer. (0 if empty)"),
			FConsoleCommandWithArgsDelegate::CreateStatic(Cmd_Play),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.PlayByLabel"),
			TEXT("Play Statement by label.\n")
			TEXT("  LabelName: string"),
			FConsoleCommandWithArgsDelegate::CreateStatic(Cmd_PlayByLabel),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Var"),
			TEXT("Set the value of a variable.\n")
			TEXT("  Name: string")
			TEXT("  Value: string"),
			FConsoleCommandWithArgsDelegate::CreateStatic(Cmd_Var),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Del"),
			TEXT("Delete a variable.\n")
			TEXT("  Variable: string"),
			FConsoleCommandWithArgsDelegate::CreateStatic(Cmd_Del),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Eval"),
			TEXT("Evaluate a Quillscript expression.\n")
			TEXT("  Expression: string"),
			FConsoleCommandWithArgsDelegate::CreateStatic(Cmd_Eval),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Bypass"),
			TEXT("Evaluate all conditions as true."),
			FConsoleCommandDelegate::CreateStatic(Cmd_Bypass),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.NotBypass"),
			TEXT("Evaluate all conditions as expected."),
			FConsoleCommandDelegate::CreateStatic(Cmd_NotBypass),
			ECVF_Default
		);

		IConsoleManager::Get().RegisterConsoleCommand(
			TEXT("qsc.Debug"),
			TEXT("Show Quillscript debugging panel."),
			FConsoleCommandDelegate::CreateStatic(Cmd_ToggleDebugger),
			ECVF_Default
		);
	}
}

void FQuillscriptModule::ShutdownModule()
{
	// ~
}

void FQuillscriptModule::Cmd_Next()
{
	for (const TObjectPtr<AQuillscriptInterpreter> Interpreter : UQuill::GetInterpreters(UQuillscriptSubsystem::World()))
		Interpreter->Next();
}

void FQuillscriptModule::Cmd_Rollback()
{
	for (const TObjectPtr<AQuillscriptInterpreter> Interpreter : UQuill::GetInterpreters(UQuillscriptSubsystem::World()))
		Interpreter->Rollback();
}

void FQuillscriptModule::Cmd_End()
{
	for (const TObjectPtr<AQuillscriptInterpreter> Interpreter : UQuill::GetInterpreters(UQuillscriptSubsystem::World()))
		Interpreter->End();
}

void FQuillscriptModule::Cmd_Stop()
{
	for (const TObjectPtr<AQuillscriptInterpreter> Interpreter : UQuill::GetInterpreters(UQuillscriptSubsystem::World()))
		Interpreter->Stop();
}

void FQuillscriptModule::Cmd_Restore()
{
	for (const TObjectPtr<AQuillscriptInterpreter> Interpreter : UQuill::GetInterpreters(UQuillscriptSubsystem::World()))
		Interpreter->Restore();
}

void FQuillscriptModule::Cmd_Play(const TArray<FString>& Args)
{
	if (Args.IsValidIndex(0))
		for (const TObjectPtr<AQuillscriptInterpreter> Interpreter : UQuill::GetInterpreters(UQuillscriptSubsystem::World()))
			Interpreter->Play(FCString::Atoi(*Args[0]));
}

void FQuillscriptModule::Cmd_PlayByLabel(const TArray<FString>& Args)
{
	if (Args.IsValidIndex(0))
		for (const TObjectPtr<AQuillscriptInterpreter> Interpreter : UQuill::GetInterpreters(UQuillscriptSubsystem::World()))
			Interpreter->PlayByLabel(*Args[0]);
}

void FQuillscriptModule::Cmd_Var(const TArray<FString>& Args)
{
	if (Args.IsValidIndex(0) && Args.IsValidIndex(1))
		UQuill::SetQuillscriptVariable(UQuillscriptSubsystem::World(), FName(*Args[0]), FText::FromString(*Args[1]));
}

void FQuillscriptModule::Cmd_Del(const TArray<FString>& Args)
{
	if (Args.IsValidIndex(0))
		UQuill::DeleteQuillscriptVariable(UQuillscriptSubsystem::World(), FName(*Args[0]));
}

void FQuillscriptModule::Cmd_Eval(const TArray<FString>& Args)
{
	FString Expression;

	for (FString Arg : Args)
		Expression.Append(Arg);

	UTools::Print(UQuill::EvaluateQuillscriptExpression(Expression));
}

void FQuillscriptModule::Cmd_Bypass()
{
	if (const TObjectPtr<UQuillscriptSubsystem> QuillscriptSubsystem{ UQuillscriptSubsystem::World()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		QuillscriptSubsystem->SetBypassConditions(true);
}

void FQuillscriptModule::Cmd_NotBypass()
{
	if (const TObjectPtr<UQuillscriptSubsystem> QuillscriptSubsystem{ UQuillscriptSubsystem::World()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		QuillscriptSubsystem->SetBypassConditions(false);
}

void FQuillscriptModule::Cmd_ToggleDebugger()
{
	const FSoftClassPath MyWidgetClassRef{ "/Script/UMGEditor.WidgetBlueprint'/Quillscript/Editor/Debugger/QuillscriptDebuggerBP.QuillscriptDebuggerBP_C'" };

	if (const TSubclassOf<UUserWidget> MyWidgetClass{ MyWidgetClassRef.TryLoadClass<UUserWidget>() })
	{
		TArray<UUserWidget*> Widgets;

		// Check if it is already open.
		UWidgetBlueprintLibrary::GetAllWidgetsOfClass(
			UQuillscriptSubsystem::World(),
			Widgets,
			MyWidgetClass,
			true
		);

		if (Widgets.Num() > 0)
		{
			for (const TObjectPtr<UUserWidget> Widget : Widgets)
			{
				// Close all open debugger widgets.
				Widget->RemoveFromParent();
				Widget->ConditionalBeginDestroy();
			}
		}
		else if (const TObjectPtr<UUserWidget> MyWidget{ CreateWidget<UUserWidget>(UQuillscriptSubsystem::World(), MyWidgetClass) })
			MyWidget->AddToViewport(1000);
	}
}

IMPLEMENT_MODULE( FQuillscriptModule, Quillscript )