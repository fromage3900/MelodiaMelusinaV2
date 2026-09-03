// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Operator.generated.h"

/**
 * Valid expression operator enumerator.
 */
UENUM(BlueprintType)
enum class EOperator : uint8
{
	/// Assignment

	Assignment		UMETA(DisplayName = "="),


	/// Logical

	Or				UMETA(DisplayName = "or"),
	And				UMETA(DisplayName = "and"),


	/// Equality

	Equal			UMETA(DisplayName = "=="),
	NotEqual		UMETA(DisplayName = "==="),
	StrictEqual		UMETA(DisplayName = "!="),
	StrictNotEqual	UMETA(DisplayName = "!=="),


	/// Relational

	Less			UMETA(DisplayName = "<"),
	LessEqual		UMETA(DisplayName = "<="),
	Greater			UMETA(DisplayName = ">"),
	GreaterEqual	UMETA(DisplayName = ">="),


	/// Additive

	Addition		UMETA(DisplayName = "+"),
	Subtraction		UMETA(DisplayName = "-"),


	/// Multiplicative

	Multiplication	UMETA(DisplayName = "*"),
	Division		UMETA(DisplayName = "/"),
	Remainder		UMETA(DisplayName = "%"),
	Power			UMETA(DisplayName = "^")
};