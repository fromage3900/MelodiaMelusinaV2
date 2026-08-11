// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Expression.generated.h"

/**
 * Quillscript language's expression structure.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FExpression
{
	GENERATED_BODY()

	/**
	 * Assignment:		variable name
	 * Function Call:	function name
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data")
	FString Symbol;

	/**
	 * Assignment:		math expression
	 * Function Call:	parameters
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data")
	TArray<FText> Parameters;


	bool IsAssignment() const
	{
		return Symbol.StartsWith("=") || Symbol.StartsWith(":=");
	}

	bool IsFunctionCall() const
	{
		return !IsAssignment();
	}

	FString GetVariableName() const
	{
		FString VariableName;

		if (IsAssignment())
		{
			VariableName = Symbol;
			VariableName.RemoveFromStart(":");
			VariableName.RemoveFromStart("=");
		}

		return VariableName;
	}

	TArray<FString> GetParametersAsStrings() const
	{
		TArray<FString> ParametersAsString;

		for (FText Parameter : this->Parameters)
			ParametersAsString.Add(Parameter.ToString());

		return ParametersAsString;
	}
};