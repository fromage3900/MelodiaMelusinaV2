// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "InterpreterState.generated.h"

/**
 * Interpreter's state.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FInterpreterState
{
	GENERATED_BODY()

	/** Current Statement index in use. */
	UPROPERTY(BlueprintReadWrite, VisibleDefaultsOnly, Category = "Data")
	int32 CurrentIndex{ 0 };

	/** Currently state of the story flow. */
	UPROPERTY(BlueprintReadWrite, VisibleDefaultsOnly, Category = "Data")
	bool bCanProceed{ true };

	/** List all Router statement and instructions executed in order. */
	UPROPERTY(BlueprintReadWrite, VisibleDefaultsOnly, Category = "Data")
	TArray<int32> RouterIndexes;

	/** Name of the direct called label, from a channel. */
	UPROPERTY(BlueprintReadWrite, VisibleDefaultsOnly, Category = "Data")
	FName ChannelCalledLabel;

	/** Name of the direct called label, from a template. */
	UPROPERTY(BlueprintReadWrite, VisibleDefaultsOnly, Category = "Data")
	FName TemplateCalledLabel;
};