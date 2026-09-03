// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "InterpreterState.h"
#include "ScriptSettings.h"
#include "SoundState.h"

#include "CoreMinimal.h"
#include "SaveState.generated.h"

/**
 * Freezes a script play state, in time.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FSaveState
{
	GENERATED_BODY()

	/// Global

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Global")
	TMap<FName, FText> Variables;


	/// Interpreter

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interpreter")
	FName LabelName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interpreter")
	FInterpreterState InterpreterState;


	/// Script

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Script")
	FScriptSettings ScriptSettings;


	/// Widgets

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Widgets")
	FSoftObjectPath BackgroundImagePath;


	/// Scenario

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Scenario")
	TArray<FSoundState> Sounds;
};