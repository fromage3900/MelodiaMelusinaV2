// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

enum class EOperator : uint8;

/**
 * Handles Quillscript postfix expressions.
 */
class FEvaluator final
{
public:
	/**
	 * Solve expression.
	 * This function expects a postfix expression.
	 */
	static FString Solve(const TArray<FString>& Expression);

	/**
	 * Solve an expression and return if its result is true or false.
	 * This function expects a postfix expression.
	 */
	static bool Evaluate(const TArray<FString>& Expression);


	/// Pipes

	static bool OperandToBoolean(const FString& Operand);
	static FString BooleanToOperand(const bool Boolean);

	static double OperandToNumber(const FString& Operand);
	static FString NumberToOperand(const double Number);

	static EOperator StringToOperator(const FString& Operator);

	static bool IsOperable(const FString& Operand);


private:
	static FString PerformOperation(const EOperator Operator, const FString& RightOperand, const FString& LeftOperand);


	/// Operations.

	static FString SolveOr(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveAnd(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveEqual(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveStrictEqual(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveNotEqual(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveStrictNotEqual(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveLess(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveLessEqual(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveGreater(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveGreaterEqual(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveAddition(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveSubtraction(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveMultiplication(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveDivision(const FString& LeftOperand, const FString& RightOperand);
	static FString SolveRemainder(const FString& LeftOperand, const FString& RightOperand);
	static FString SolvePower(const FString& LeftOperand, const FString& RightOperand);
};