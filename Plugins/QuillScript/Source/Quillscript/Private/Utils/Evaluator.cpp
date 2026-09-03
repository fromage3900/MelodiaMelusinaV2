// Copyright Bruno Caxito. All Rights Reserved.

#include "Utils/Evaluator.h"

#include "Base/Operator.h"
#include "Utils/Lexer.h"
#include "Utils/Tools.h"

FString FEvaluator::Solve(const TArray<FString>& Expression)
{
	TArray<FString> Stack;

	for (FString Symbol : Expression)
	{
		if (const EOperator Operator{ StringToOperator(Symbol) }; Operator == EOperator::Assignment)
			Stack.Push(Symbol);
		else
		{
			if (Stack.Num() >= 2)
				Stack.Push(PerformOperation(Operator, Stack.Pop(), Stack.Pop()));
			else
			{
				UTools::Error("FEvaluator::Calculate() -> Malformed expression. Check if your condition or math expression.");
				return FString();
			}
		}
	}

	if (Stack.IsEmpty())
	{ UTools::Error("FEvaluator::Calculate() -> Malformed expression"); return FString(); }

	// Sanitize and return the result.
	FString Result{ Stack.Pop() };
	Result.RemoveFromEnd(".0");
	return Result;
}

bool FEvaluator::Evaluate(const TArray<FString>& Expression)
{
	return OperandToBoolean(Solve(Expression));
}

FString FEvaluator::PerformOperation(const EOperator Operator, const FString& RightOperand, const FString& LeftOperand)
{
	switch (Operator)
	{
		case EOperator::Or: 			return SolveOr(RightOperand, LeftOperand);
		case EOperator::And: 			return SolveAnd(RightOperand, LeftOperand);
		case EOperator::Equal: 			return SolveEqual(RightOperand, LeftOperand);
		case EOperator::StrictEqual: 	return SolveStrictEqual(RightOperand, LeftOperand);
		case EOperator::NotEqual: 		return SolveNotEqual(RightOperand, LeftOperand);
		case EOperator::StrictNotEqual: return SolveStrictNotEqual(RightOperand, LeftOperand);
		case EOperator::Less: 			return SolveLess(RightOperand, LeftOperand);
		case EOperator::LessEqual: 		return SolveLessEqual(RightOperand, LeftOperand);
		case EOperator::Greater: 		return SolveGreater(RightOperand, LeftOperand);
		case EOperator::GreaterEqual: 	return SolveGreaterEqual(RightOperand, LeftOperand);
		case EOperator::Addition: 		return SolveAddition(RightOperand, LeftOperand);
		case EOperator::Subtraction: 	return SolveSubtraction(RightOperand, LeftOperand);
		case EOperator::Multiplication: return SolveMultiplication(RightOperand, LeftOperand);
		case EOperator::Division: 		return SolveDivision(RightOperand, LeftOperand);
		case EOperator::Remainder: 		return SolveRemainder(RightOperand, LeftOperand);
		case EOperator::Power: 			return SolvePower(RightOperand, LeftOperand);
		default: return FString();
	}
}

FString FEvaluator::SolveOr(const FString& LeftOperand, const FString& RightOperand)
{
	return BooleanToOperand(OperandToBoolean(LeftOperand) || OperandToBoolean(RightOperand));
}

FString FEvaluator::SolveAnd(const FString& LeftOperand, const FString& RightOperand)
{
	return BooleanToOperand(OperandToBoolean(LeftOperand) && OperandToBoolean(RightOperand));
}

FString FEvaluator::SolveEqual(const FString& LeftOperand, const FString& RightOperand)
{
	// If one of the operands is operable.
	if (IsOperable(LeftOperand) || IsOperable(RightOperand))
		return BooleanToOperand(OperandToNumber(LeftOperand) == OperandToNumber(RightOperand));

	// Text type.
	return LeftOperand.Equals(RightOperand, ESearchCase::IgnoreCase) ? SYMBOL(On) : SYMBOL(Off);
}

FString FEvaluator::SolveStrictEqual(const FString& LeftOperand, const FString& RightOperand)
{
	return LeftOperand.Equals(RightOperand, ESearchCase::CaseSensitive) ? SYMBOL(On) : SYMBOL(Off);
}

FString FEvaluator::SolveNotEqual(const FString& LeftOperand, const FString& RightOperand)
{
	return SolveEqual(LeftOperand, RightOperand) == SYMBOL(On) ? SYMBOL(Off) : SYMBOL(On);
}

FString FEvaluator::SolveStrictNotEqual(const FString& LeftOperand, const FString& RightOperand)
{
	return SolveStrictEqual(LeftOperand, RightOperand) == SYMBOL(On) ? SYMBOL(Off) : SYMBOL(On);
}

FString FEvaluator::SolveLess(const FString& LeftOperand, const FString& RightOperand)
{
	return BooleanToOperand(OperandToNumber(LeftOperand) < OperandToNumber(RightOperand));
}

FString FEvaluator::SolveLessEqual(const FString& LeftOperand, const FString& RightOperand)
{
	return BooleanToOperand(OperandToNumber(LeftOperand) <= OperandToNumber(RightOperand));
}

FString FEvaluator::SolveGreater(const FString& LeftOperand, const FString& RightOperand)
{
	return BooleanToOperand(OperandToNumber(LeftOperand) > OperandToNumber(RightOperand));
}

FString FEvaluator::SolveGreaterEqual(const FString& LeftOperand, const FString& RightOperand)
{
	return BooleanToOperand(OperandToNumber(LeftOperand) >= OperandToNumber(RightOperand));
}

FString FEvaluator::SolveAddition(const FString& LeftOperand, const FString& RightOperand)
{
	return NumberToOperand(OperandToNumber(LeftOperand) + OperandToNumber(RightOperand));
}

FString FEvaluator::SolveSubtraction(const FString& LeftOperand, const FString& RightOperand)
{
	return NumberToOperand(OperandToNumber(LeftOperand) - OperandToNumber(RightOperand));
}

FString FEvaluator::SolveMultiplication(const FString& LeftOperand, const FString& RightOperand)
{
	return NumberToOperand(OperandToNumber(LeftOperand) * OperandToNumber(RightOperand));
}

FString FEvaluator::SolveDivision(const FString& LeftOperand, const FString& RightOperand)
{
	return NumberToOperand(OperandToNumber(LeftOperand) / OperandToNumber(RightOperand));
}

FString FEvaluator::SolveRemainder(const FString& LeftOperand, const FString& RightOperand)
{
	return NumberToOperand(StaticCast<int64>(OperandToNumber(LeftOperand)) % StaticCast<int64>(OperandToNumber(RightOperand)));
}

FString FEvaluator::SolvePower(const FString& LeftOperand, const FString& RightOperand)
{
	return NumberToOperand(FMath::Pow(OperandToNumber(LeftOperand), OperandToNumber(RightOperand)));
}

bool FEvaluator::OperandToBoolean(const FString& Operand)
{
	return
		Operand.Equals(SYMBOL(On)) ||
		Operand.Equals("true", ESearchCase::IgnoreCase) ||
		Operand.Equals("1");
}

FString FEvaluator::BooleanToOperand(const bool Boolean)
{
	return Boolean ? SYMBOL(On) : SYMBOL(Off);
}

double FEvaluator::OperandToNumber(const FString& Operand)
{
	if (Operand.IsNumeric())
		return FCString::Atod(*Operand);

	if (Operand.Equals(SYMBOL(on)) || Operand.Equals("true", ESearchCase::IgnoreCase))
		return 1;

	return 0;
}

FString FEvaluator::NumberToOperand(const double Number)
{
	return FString::SanitizeFloat(Number);
}

EOperator FEvaluator::StringToOperator(const FString& Operator)
{
	if (Operator.Equals("or"))
		return EOperator::Or;

	if (Operator.Equals("and"))
		return EOperator::And;

	if (Operator.Equals("==="))
		return EOperator::StrictEqual;

	if (Operator.Equals("!=="))
		return EOperator::StrictNotEqual;

	if (Operator.Equals("=="))
		return EOperator::Equal;

	if (Operator.Equals("!="))
		return EOperator::NotEqual;

	if (Operator.Equals("<"))
		return EOperator::Less;

	if (Operator.Equals("<="))
		return EOperator::LessEqual;

	if (Operator.Equals(">"))
		return EOperator::Greater;

	if (Operator.Equals(">="))
		return EOperator::GreaterEqual;

	if (Operator.Equals("+"))
		return EOperator::Addition;

	if (Operator.Equals("-"))
		return EOperator::Subtraction;

	if (Operator.Equals("*"))
		return EOperator::Multiplication;

	if (Operator.Equals("/"))
		return EOperator::Division;

	if (Operator.Equals("%"))
		return EOperator::Remainder;

	if (Operator.Equals("^"))
		return EOperator::Power;

	return EOperator::Assignment;
}

bool FEvaluator::IsOperable(const FString& Operand)
{
	return
		Operand.Equals(SYMBOL(On), ESearchCase::IgnoreCase) ||
		Operand.Equals(SYMBOL(Off), ESearchCase::IgnoreCase) ||
		Operand.Equals("true", ESearchCase::IgnoreCase) ||
		Operand.Equals("false", ESearchCase::IgnoreCase) ||
		Operand.IsNumeric();
}