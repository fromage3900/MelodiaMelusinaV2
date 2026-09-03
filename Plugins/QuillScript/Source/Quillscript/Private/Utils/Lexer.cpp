// Copyright Bruno Caxito. All Rights Reserved.

#include "Utils/Lexer.h"

#include "Base/Statement.h"
#include "Core/QuillscriptSettings.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Utils/Tools.h"


TArray<FStatement> FLexer::Parse(const FString& SourceScriptText)
{
	TArray<FStatement> Statements;

	// Tokenize and break the script into lines (statements).
	TArray<FString> Lines;
	Tokenize(SourceScriptText).ParseIntoArrayLines(Lines);

	// Handle directives that must be resolved before creating the statements' arrays.
	Lines = ResolvePreDirectives(Lines);

	// Create statements.
	for (FString& Line : Lines)
	{
		// Remove indentation.
		Line.TrimStartAndEndInline();

		// Remove inline comment.
		FString Sentence, Comment;
		Line.Split(SYMBOL(Comment), &Sentence, &Comment);

		if (!Sentence.IsEmpty())
			Line = Sentence;

		// Get the statement type.
		FStatement Statement;
		Statement.Type = GetStatementType(Line);

		if (Statement.Type != EStatementType::Comment && Statement.Type != EStatementType::FreeText)
		{
			// Save source line.
			if (UQuillscriptSettings::Get()->GetStoreSourceLine())
				Statement.SourceLine = Line;

			if (UQuillscriptSettings::Get()->GetStoreInlineComment())
				Statement.Comment = Comment;

			// Remove statement symbol.
			Line.RemoveFromStart(GetStatementSymbol(Statement.Type));
			Line.TrimStartInline();

			// Condition statement special cases
			if (Line.RemoveFromStart(SYMBOL(If)))
				Statement.Main = SYMBOL(If);
			else if (Line.RemoveFromStart(SYMBOL(ElseIf)))
				Statement.Main = SYMBOL(ElseIf);
			else if (Line.RemoveFromStart(SYMBOL(Else)))
				Statement.Main = SYMBOL(Else);
			else if (Line.RemoveFromStart(SYMBOL(EndIf)))
				Statement.Main = SYMBOL(EndIf);

			// Copy the last line if 'Repeat'
			if (Line == SYMBOL(Repeat) && !Statements.IsEmpty())
			{
				Statement.Main = Statements.Last().Main;
				Statement.Conditions = Statements.Last().Conditions;
				Statement.Tags = Statements.Last().Tags;
			}
			else
			{
				// Get instructions.
				TArray Instructions{ BreakLineIntoInstructions(Line) };

				for (const FString& Instruction : Instructions)
				{
					switch (GetInstructionType(Instruction, Statement))
					{
					case LabelName:	Statement.Label = CreateLabelInstruction(Instruction, Statement);	break;
					case Main:		Statement.Main = CreateMainInstruction(Instruction, Statement);		break;
					case Condition: Statement.Conditions.Add(CreateConditionInstruction(Instruction));	break;
					case Command:	Statement.Commands.Add(CreateCommandInstruction(Instruction));		break;
					case Target:	Statement.Target = CreateTargetInstruction(Instruction, Statement);	break;
					case Tag:		Statement.Tags.Append(CreateTagInstruction(Instruction));			break;
					default: break;
					}
				}
			}

			// Add statement to the list.
			Statements.Add(Statement);
		}

		// Statement is actually a free text line.
		else if (Statement.Type == EStatementType::FreeText && !Statements.IsEmpty())
		{
			// Add free text to the last statement.
			FString Text{ Statements.Last().Text.ToString() };

			if (!Text.IsEmpty())
				Text.Append(LINE_TERMINATOR);

			Text.Append(Line);

			Statements.Last().Text = FText::FromString(Text);
		}
	}

	// Polish.
	TMap<FString, int32> Counter;
	for (FStatement& Statement : Statements)
	{
		// Remove repeated tags.
		if (!UQuillscriptSettings::Get()->GetRepeatedTags())
			Statement.Tags = UTools::RemoveRepeatedValues(Statement.Tags);

		// Detokenize.
		Statement = Detokenize(Statement);

		// Parsing time directives.
		Statement = ResolvePostDirectives(Statement);

		// Parsing time special tags.
		Localize(Statement);

		// Fix multiline assignment.
		if (Statement.Type == EStatementType::Command && !Statement.Text.IsEmpty() && !Statement.Commands.IsEmpty())
		{
			if (Statement.Commands.Last().Parameters.IsEmpty())
				Statement.Commands.Last().Parameters.Add(FText());

			FText& LastParameter{ Statement.Commands.Last().Parameters.Last() };
			FString LastParameterString{ LastParameter.ToString() };

			LastParameterString.Append(Statement.Text.ToString());
			LastParameterString.ReplaceInline(LINE_TERMINATOR, TEXT(""));
			LastParameterString.RemoveFromStart(SYMBOL(SingleQuote));
			LastParameterString.RemoveFromStart(SYMBOL(DoubleQuote));
			LastParameterString.RemoveFromEnd(SYMBOL(SingleQuote));
			LastParameterString.RemoveFromEnd(SYMBOL(DoubleQuote));

			LastParameter = FText::FromString(LastParameterString);
			Statement.Text = FText();
		}

		// Assign an automatic label (Statement ID).
		if (Statement.Label.IsNone())
		{
			// Get hash source string.
			FString Source;

			if (Statement.Type == EStatementType::Dialogue || Statement.Type == EStatementType::Option)
				Source = Statement.Text.ToString();
			else
				Source = Statement.SourceLine;

			// Make hash.
			const FString Hex{ UTools::ToHex(FCString::Atoi64(*UTools::ToHash(Source))) };
			Counter.FindOrAdd(Hex)++;

			Statement.Label = FName(Hex + FString::FromInt(Counter[Hex]));
		}
	}

	return Statements;
}


TArray<FString> FLexer::StringToArrayOfSymbols(FString String)
{
	// Create array and add the first element to append at.
	TArray<FString> SymbolsList;
	SymbolsList.Add("");

	// Get valid expression operators.
	TArray Operators{ GetOperators() };
	FString Quote;

	// Run string looking for operators.
	while (!String.IsEmpty())
	{
		bool Concat{ true };

		// Check if it's a quotation closing.
		if (String.StartsWith(Quote))
			Quote.Empty();

		// Check if it's a quotation opening.
		else if (Quote.IsEmpty())
		{
			if (String.StartsWith(SYMBOL(DoubleQuote)))
				Quote = SYMBOL(DoubleQuote);
			else if (String.StartsWith(SYMBOL(SingleQuote)))
				Quote = SYMBOL(SingleQuote);
			else if (String.StartsWith(SYMBOL(Backtick)))
				Quote = SYMBOL(Backtick);
		}

		// Check if it's an operator.
		if (Quote.IsEmpty())
		{
			for (FString& Operator : Operators)
			{
				if (String.RemoveFromStart(Operator))
				{
					SymbolsList.Add(Operator);
					SymbolsList.Add("");
					Concat = false;
					break;
				}
			}
		}

		// Add character to the last element.
		if (Concat)
		{
			SymbolsList.Last().Append(String.Left(1));
			String.RemoveAt(0);
		}
	}

	// Remove unnecessary remaining whitespaces.
	for (int32 I{ 0 }; I < SymbolsList.Num(); I++)
	{
		SymbolsList[I].TrimStartAndEndInline();

		if (SymbolsList[I].IsEmpty())
		{
			SymbolsList.RemoveAt(I);
			I--;
		}
	}

	return SymbolsList;
}

TArray<FString> FLexer::InfixToPostfix(TArray<FString> InfixExpression) {
	TArray<FString> Stack;

	// Add some extra character to avoid underflow.
	Stack.Add("#");

	TArray<FString> Postfix;
	Postfix.Add(FString());

	for (int32 I{ 0 }; I < InfixExpression.Num(); I++)
	{
		const FString Char{ InfixExpression[I] };

		if(Char == SYMBOL(RoundOpen))
			Stack.Add(SYMBOL(RoundOpen));
		else if(Char == SYMBOL(RoundClose))
		{
			while(Stack.Last() != "#" && Stack.Last() != SYMBOL(RoundOpen))
			{
				Postfix.Add(Stack.Last()); //store and pop until '(' is found
				Stack.Pop();
			}

			Stack.Pop();          //remove the '(' from stack
		}
		else if (GetOperators().Contains(Char) || Char.Equals(SYMBOL(And)) || Char.Equals(SYMBOL(Or)))
		{
			if(GetOperatorPrecedence(Char) > GetOperatorPrecedence(Stack.Last()))
				Stack.Add(Char); //Add if precedence is high
			else
			{
				while(Stack.Last() != "#" && GetOperatorPrecedence(Char) <= GetOperatorPrecedence(Stack.Last()))
				{
					Postfix.Add(Stack.Last());       //store and pop until higher precedence is found
					Stack.Pop();
				}

				Stack.Add(Char);
			}
		}
		else
			Postfix.Add(Char);      //add to postfix when character is a letter or number
	}

	// Store and pop until the stack is not empty.
	if (!Stack.IsEmpty())
	{
		while (Stack.Last() != FString("#"))
		{
			Postfix.Add(Stack.Last());
			Stack.Pop();
		}
	}

	// Remove unnecessary remaining whitespaces.
	for (int32 I{ 0 }; I < Postfix.Num(); I++)
	{
		Postfix[I].TrimStartAndEndInline();

		if (Postfix[I].IsEmpty())
			Postfix.RemoveAt(I);
		else
			Postfix[I].TrimStartAndEndInline();
	}

	return Postfix;
}

TArray<FText> FLexer::StringToParameters(const FString& String, const FString& Separator)
{
	TArray<FString> Parameters;
	FString Parameter, Quote, Tabulation;

	if (Separator == " ")
		Tabulation = "\t";

	// Iterate each character.
	for (int32 I{ 0 }; I < String.Len(); I++)
	{
		FString Char{ String.Mid(I, 1) };

		// Check if it's a quotation closing.
		if (Char == Quote)
		{
			Quote.Empty();
			Parameter.Append(Char);
			continue;
		}

		// Check if it's a quotation opening.
		if (
			Quote.IsEmpty() &&
			( Char == SYMBOL(DoubleQuote) || Char == SYMBOL(SingleQuote) || Char == SYMBOL(Backtick) )
		)
		{
			Quote = Char;
			Parameter.Append(Char);
			continue;
		}

		// Break parameters.
		if (Quote.IsEmpty() && ( Char == Separator || Char == Tabulation ))
		{
			Parameters.Add(Parameter);
			Parameter.Empty();
		}
		else
			Parameter.Append(Char);
	}

	// Add the last bunch.
	Parameters.Add(Parameter);

	// Convert to FText array.
	TArray<FText> Texts;

	for (FString TempParam : Parameters)
		if (!TempParam.IsEmpty())
			Texts.Add(FText::FromString(TempParam.TrimStartAndEnd()));

	return Texts;
}


void FLexer::TurnOffLocalization(FText& Value)
{
	// Do NOT localize numbers.
	if (Value.IsNumeric())
	{
		Value = FText::AsCultureInvariant(Value);
		return;
	}

	// Do NOT localize variables.
	FString String{ Value.ToString() };

	if (String.StartsWith(SYMBOL(CurlyOpen)) && String.EndsWith(SYMBOL(CurlyClose)))
	{
		if (String.ReplaceInline(*SYMBOL(CurlyOpen), TEXT("")) == 1)
		{
			Value = FText::AsCultureInvariant(Value);
			return;
		}
	}

	// Do NOT localize replaces.
	if (String.StartsWith(SYMBOL(SquareOpen)) && String.EndsWith(SYMBOL(SquareClose)))
	{
		if (String.ReplaceInline(*SYMBOL(SquareOpen), TEXT("")) == 1)
		{
			Value = FText::AsCultureInvariant(Value);
			return;
		}
	}

	// Do NOT localize Quillscript syntax symbols and reserved words.
	for (TPair<FName, TPair<FString, FString>> Symbol : Symbols)
	{
		if (Value.EqualTo(FText::FromString(Symbol.Value.Key)))
		{
			Value = FText::AsCultureInvariant(Value);
			return;
		}
	}
}


FString FLexer::GetFromArrayString(FString String, const int32 Index)
{
	// TODO: A general use function that can find the element in any array type. (Currently not supported: FText, UObject, UStruct, UEnum)

	String = String.Replace(TEXT("("), TEXT("[")).Replace(TEXT(")"), TEXT("]"));

	TSharedPtr<FJsonValue> JsonParsed;
	const TSharedRef JsonReader{ TJsonReaderFactory<TCHAR>::Create(String) };

	if (FJsonSerializer::Deserialize(JsonReader, JsonParsed) && JsonParsed.IsValid())
	{
		TArray<TSharedPtr<FJsonValue>> JsonArray{ JsonParsed->AsArray() };

		if (JsonArray.IsValidIndex(Index))
			return JsonArray[Index].Get()->AsString();
	}

	return String;
}

FString FLexer::GetFromMapString(FString String, const FString& Key)
{
	// TODO: A general use function that can find the kay->value pair in any map type. (Currently not supported: FText, UObject, UStruct)

	TMap<FString, FString> Pairs;
	TArray<FString> Buffer;
	FString TempKey;

	String.RemoveFromStart("(");
	String.RemoveFromEnd(")");
	String.ParseIntoArray(Buffer, *SYMBOL(Separator));

	for (int32 J{ 0 }; J < Buffer.Num(); J++)
	{
		Buffer[J].TrimStartAndEndInline();

		// Key.
		if (J % 2 == 0)
		{
			Buffer[J].RemoveFromStart(SYMBOL(RoundOpen));
			TempKey = Buffer[J].TrimQuotes();
		}

		// Value.
		else
		{
			Buffer[J].RemoveFromEnd(SYMBOL(RoundClose));
			Pairs.Add(TempKey, Buffer[J].TrimQuotes());
		}
	}

	if (Pairs.Contains(Key))
		return Pairs[Key].TrimQuotes();

	return FString();
}


EStatementType FLexer::GetStatementType(FString Statement)
{
	Statement.TrimStartAndEndInline();

	if (
		Statement.StartsWith(SYMBOL(Router)) || // Must be before dialogue, because they start with the same character.
		Statement.StartsWith(SYMBOL(Channel))
	)
		return EStatementType::Router;

	if (Statement.StartsWith(SYMBOL(Dialogue)) && !Statement.StartsWith(SYMBOL(Gate)))
		return EStatementType::Dialogue;

	if (Statement.StartsWith(SYMBOL(Option)))
		return EStatementType::Option;

	if (Statement.StartsWith(SYMBOL(Command)))
		return EStatementType::Command;

	if (
		Statement.StartsWith(SYMBOL(Covert)) ||
		Statement.StartsWith(SYMBOL(Label))
	)
		return EStatementType::Label;

	if (
		Statement.StartsWith(SYMBOL(Condition)) ||
		Statement.StartsWith(SYMBOL(If)) ||
		Statement.StartsWith(SYMBOL(ElseIf)) ||
		Statement.StartsWith(SYMBOL(Else)) ||
		Statement.StartsWith(SYMBOL(EndIf))
	)
		return EStatementType::Condition;

	if (Statement.StartsWith(SYMBOL(Directive)))
		return EStatementType::Directive;

	if (
		Statement.StartsWith(SYMBOL(Comment)) ||
		Statement == SYMBOL(CurlyOpen) ||
		Statement == SYMBOL(CurlyClose)
	)
		return EStatementType::Comment;

	// Is either a header comment, or a free text line.
	return EStatementType::FreeText;
}

FString FLexer::GetStatementSymbol(const EStatementType Statement)
{
	switch (Statement)
	{
	case EStatementType::Label: 	return SYMBOL(Label);
	case EStatementType::Dialogue: 	return SYMBOL(Dialogue);
	case EStatementType::Option: 	return SYMBOL(Option);
	case EStatementType::Command: 	return SYMBOL(Command);
	case EStatementType::Router: 	return SYMBOL(Router);
	case EStatementType::Condition: return SYMBOL(Condition);
	case EStatementType::Directive: return SYMBOL(Directive);
	case EStatementType::Comment: 	return SYMBOL(Comment);
	default: return "";
	}
}

EInstructionType FLexer::GetInstructionType(FString Instruction, const FStatement& Statement)
{
	Instruction.TrimStartAndEndInline();

	// Default syntax.
	if (
		Instruction.StartsWith(SYMBOL(Covert)) ||
		Instruction.StartsWith(SYMBOL(Label))
	)
		return LabelName;

	if (Instruction.StartsWith(SYMBOL(Condition)))
		return Condition;

	if (Instruction.StartsWith(SYMBOL(Command)))
		return Command;

	if (Instruction.StartsWith(SYMBOL(Tag)))
		return Tag;

	if (
		Instruction.StartsWith(SYMBOL(Router)) ||
		Instruction.StartsWith(SYMBOL(Channel))
	)
		return Target;

	// Custom Cases.
	if (Statement.Type == EStatementType::Label)
		return LabelName;

	if (Statement.Type == EStatementType::Command)
		return Command;

	if (Statement.Type == EStatementType::Router)
		return Target;

	if (Statement.Type == EStatementType::Condition)
		return Condition;

	// Non-marked instructions.
	if (!Statement.Main.IsEmpty())
		return Command;

	// Otherwise.
	return Main;
}

TArray<FString> FLexer::GetOperators()
{
	return TArray {
		// Parenthesis used to group priority
		SYMBOL(RoundClose),
		SYMBOL(RoundOpen),

		// These operators can't be used unless they are isolated by whitespaces.
		" " + SYMBOL(And) + " ",
		" " + SYMBOL(Or) + " ",

		// Other operators.
		SYMBOL(StrictEqual),
		SYMBOL(StrictNotEqual),
		SYMBOL(Equal),
		SYMBOL(NotEqual),
		SYMBOL(LessEqual),
		SYMBOL(Less),
		SYMBOL(GreaterEqual),
		SYMBOL(Greater),
		SYMBOL(Addition),
		SYMBOL(Subtraction),
		SYMBOL(Multiplication),
		SYMBOL(Division),
		SYMBOL(Remainder),
		SYMBOL(Power)
	};
}

int32 FLexer::GetOperatorPrecedence(const FString& Operator)
{
	if(Operator == SYMBOL(Or))
		return 1;

	if(Operator == SYMBOL(And))
		return 2;

	if(Operator == SYMBOL(Equal) || Operator == SYMBOL(StrictEqual) || Operator == SYMBOL(NotEqual) || Operator == SYMBOL(StrictNotEqual))
		return 3;

	if(Operator == SYMBOL(Less) || Operator == SYMBOL(LessEqual) || Operator == SYMBOL(Greater) || Operator == SYMBOL(GreaterEqual))
		return 4;

	if(Operator == SYMBOL(Addition) || Operator == SYMBOL(Subtraction))
		return 5;

	if(Operator == SYMBOL(Multiplication) || Operator == SYMBOL(Division) || Operator == SYMBOL(Remainder))
		return 6;

	if(Operator == SYMBOL(Power))
		return 7;

	return 0;
}


TArray<FString> FLexer::BreakLineIntoInstructions(const FString& Line)
{
	TArray<FString> Instructions;
	Line.ParseIntoArray(Instructions, *SYMBOL(Concatenation));

	for (FString& Instruction : Instructions)
		Instruction.TrimStartAndEndInline();

	return Instructions;
}


FName FLexer::CreateLabelInstruction(FString SourceString, FStatement& Statement)
{
	// Covert.
	if (SourceString.RemoveFromStart(SYMBOL(Covert)))
		Statement.bCovert = true;
	else
		SourceString.RemoveFromStart(SYMBOL(Label));

	SourceString.TrimStartAndEndInline();

	TPair<FName, TArray<FText>> TemplateData{ GetTemplateData(SourceString) };

	TArray<FString> Arguments;
	for (FText& Argument : TemplateData.Value)
		Arguments.Add(Argument.ToString());

	Statement.Arguments = Arguments;
	return TemplateData.Key;
}

FString FLexer::CreateMainInstruction(FString SourceString, FStatement& Statement)
{
	SourceString.TrimStartAndEndInline();

	// Move main to text if it's a single line option.
	if (Statement.Type == EStatementType::Option)
	{
		if (!SourceString.Equals(SYMBOL(Option)))
			Statement.Text = FText::FromString(SourceString);

		SourceString = "*";
	}

	return SourceString;
}

FExpression FLexer::CreateConditionInstruction(FString SourceString)
{
	SourceString.TrimStartAndEndInline();
	SourceString.RemoveFromStart(SYMBOL(Condition));
	SourceString.TrimStartInline();

	TArray AsString{ InfixToPostfix(StringToArrayOfSymbols(SourceString)) };
	TArray<FText> AsText;

	for (FString String : AsString)
		AsText.Add(FText::FromString(String));

	return FExpression{
		FString(),
		AsText
	};
}

FExpression FLexer::CreateCommandInstruction(FString SourceString)
{
	SourceString.TrimStartAndEndInline();
	SourceString.RemoveFromStart(SYMBOL(Command));
	SourceString.TrimStartInline();

	bool bVariableAssignment{ false };
	FString Name, Expression, AssignmentType;
	TArray<FText> Parameters;

	// Check if it's a variable assignment. It's a function call for all other cases.
	if (SourceString.Contains(SYMBOL(Assignment)))
	{
		SourceString.Split(SYMBOL(Assignment), &Name, &Expression);

		if (!Name.IsEmpty())
		{
			// Get the assignment type.
			FString Last{ Name.Right(1) };

			const FString ValidAssignNameChars{
				SYMBOL(Constructor) + SYMBOL(Addition) + SYMBOL(Subtraction) + SYMBOL(Multiplication) +
				SYMBOL(Division) + SYMBOL(Remainder) + SYMBOL(Power)
			};

			if (ValidAssignNameChars.Contains(Last))
			{
				AssignmentType = Last;
				Name.RemoveFromEnd(AssignmentType);
			}

			// Check if variable has a valid name.
			Name.TrimStartAndEndInline();

			const FString ValidVarNameChars{
				"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_?" +
				SYMBOL(Temp) + SYMBOL(Out) + SYMBOL(Arg) + SYMBOL(Reference) + SYMBOL(Functor)
			};

			int32 I;
			for (I = 0; I < Name.Len(); I++)
				if (!ValidVarNameChars.Contains(Name.Mid(I, 1)))
					break;

			if (I == Name.Len() && I > 0)
				bVariableAssignment = true;
		}
	}

	// It's a variable assignment.
	if (bVariableAssignment)
	{
		// Replace all self-references.
		Expression.ReplaceInline(*SYMBOL(Self), *(SYMBOL(CurlyOpen) + Name + SYMBOL(CurlyClose)));

		// Convert string expression to an array of symbols.
		TArray ArrayOfSymbols{ StringToArrayOfSymbols(Expression) };

		// Complete expression if it's a reduced assignment form.
		if (AssignmentType.IsEmpty())
			Name = SYMBOL(Assignment) + Name;

		else if (AssignmentType == SYMBOL(Constructor))
			Name = SYMBOL(Constructor) + SYMBOL(Assignment) + Name;

		else
		{
			ArrayOfSymbols.Insert({ SYMBOL(CurlyOpen) + Name + SYMBOL(CurlyClose), AssignmentType, SYMBOL(RoundOpen) }, 0);
			ArrayOfSymbols.Append({ SYMBOL(RoundClose) });

			Name = SYMBOL(Assignment) + Name;
		}

		// Convert expression to postfix.
		ArrayOfSymbols = InfixToPostfix(ArrayOfSymbols);

		// Change the array type.
		for (FString& Symbol : ArrayOfSymbols)
			Parameters.Add(FText::FromString(Symbol));
	}

	// It's a function call.
	else
	{
		// Check if the first break is a space or tab.
		int32 Space, Tab;
		SourceString.FindChar(*(" "), Space);
		SourceString.FindChar(*("\t"), Tab);

		FString Breaker = " ";

		if (Space == INDEX_NONE && Tab != INDEX_NONE)
			Breaker = "\t";
		else if (Space != INDEX_NONE && Tab != INDEX_NONE && Tab < Space)
			Breaker = "\t";

		// Split.
		SourceString.Split(Breaker, &Name, &Expression);
		Parameters = StringToParameters(Expression);

		if (Name.IsEmpty())
			Name = SourceString;

		Name.RemoveSpacesInline();
	}

	return FExpression{ Name, Parameters };
}

TArray<FString> FLexer::CreateTagInstruction(FString SourceString)
{
	SourceString.RemoveSpacesInline();

	TArray<FString> Tags;
	SourceString.ParseIntoArray(Tags, *SYMBOL(Tag));

	return Tags;
}

FName FLexer::CreateTargetInstruction(FString SourceString, FStatement& Statement)
{
	// Channel.
	if (SourceString.RemoveFromStart(SYMBOL(Channel)))
		Statement.bChannel = true;
	else
		SourceString.RemoveFromStart(SYMBOL(Router));

	SourceString.TrimStartAndEndInline();

	const TPair<FName, TArray<FText>> TemplateData{ GetTemplateData(SourceString) };

	// Success.
	if (Statement.Type == EStatementType::Router && Statement.Main.IsEmpty())
	{
		Statement.Main = TemplateData.Key.ToString();
		Statement.ExtraParameters = TemplateData.Value;
		return FName();
	}

	// Failure.
	Statement.TargetArguments = TemplateData.Value;
	return TemplateData.Key;
}


TPair<FName, TArray<FText>> FLexer::GetTemplateData(FString SourceString)
{
	TPair<FName, TArray<FText>> TemplateData;
	SourceString.TrimStartAndEndInline();

	// If template, extract its arguments.
	if (SourceString.RemoveFromEnd(SYMBOL(RoundClose)) && SourceString.Contains(SYMBOL(RoundOpen)))
	{
		FString TargetLabel, TemplateArguments;
		SourceString.Split(SYMBOL(RoundOpen), &TargetLabel, &TemplateArguments);

		TargetLabel.RemoveSpacesInline();
		TemplateData.Key = FName(TargetLabel);
		TemplateData.Value = StringToParameters(TemplateArguments, SYMBOL(Separator));
	}
	else
	{
		SourceString.RemoveSpacesInline();
		TemplateData.Key = FName(SourceString);
	}

	return TemplateData;
}


TArray<FString> FLexer::ResolvePreDirectives(TArray<FString> Statements)
{
    for (int32 I{ 0 }; I < Statements.Num(); I++)
    {
        // Define.
        if (Statements[I].RemoveFromStart(SYMBOL(Directive) + " " + DirectiveDefine + " "))
        {
        	// Break this definition into usable parts.
        	FString Declaration, DefinitionValue;
        	Statements[I].Split(" ", &Declaration, &DefinitionValue);
        	auto [DefinitionName, DefinitionParameters] = BreakDefinition(Declaration);

        	// Perform replacement only on following statements.
        	for (int32 J{ I + 1 }; J < Statements.Num(); J++)
        	{
        		// Get all definitions to be replaced in this string.
        		TArray Definitions{ GetAllDefinitionsInString(Statements[J]) };

				for (FString Definition : Definitions)
				{
				    // Break this replacement into usable parts.
				    auto [ReplaceableName, ReplaceableParameters] = BreakDefinition(Definition);

				    if (ReplaceableName == DefinitionName)
				    {
					    // No parameters.
					    if (DefinitionParameters.IsEmpty())
	      					Statements[J].ReplaceInline(*(SYMBOL(SquareOpen) + Definition + SYMBOL(SquareClose)), *DefinitionValue);

      					// With parameters
				        else
				        {
							FString ReplacementValue{ DefinitionValue };

							for (int32 K{ 0 }; K < DefinitionParameters.Num() && K < ReplaceableParameters.Num(); K++)
								ReplacementValue.ReplaceInline(*DefinitionParameters[K], *ReplaceableParameters[K]);

							Statements[J].ReplaceInline(*(SYMBOL(SquareOpen) + Definition + SYMBOL(SquareClose)), *ReplacementValue);
						}
				    }
				}
        	}

        	Statements.RemoveAt(I);
        	I--;
        }
    }

	return Statements;
}

FStatement FLexer::ResolvePostDirectives(FStatement Statement)
{
	return Statement;
}


TArray<FString> FLexer::GetAllDefinitionsInString(const FString& Definition)
{
	TArray<FString> Buffer;
	Buffer.Add("");

	bool bToBuffer{ false };

	// Iterate each character.
	for (int32 I{ 0 }; I < Definition.Len(); I++)
	{
		FString Char{ Definition.Mid(I, 1) };

		// Get previous char.
		FString PreviousChar;
		if (I > 0)
			PreviousChar = Definition.Mid(I - 1, 1);

		// It is a definition opening.
		if (Char == SYMBOL(SquareOpen) && PreviousChar != EscapeCharacter)
			bToBuffer = true;

		// It is a definition closing.
		else if (Char == SYMBOL(SquareClose) && PreviousChar != EscapeCharacter && bToBuffer)
		{
			bToBuffer = false;
			Buffer.Add("");
		}

		// Add to buffer.
		else if (bToBuffer)
			Buffer.Last().Append(Char);
	}

	// Clear empty entries.
	TArray<FString> CleanBuffer;

	for (FString Buff : Buffer)
		if (!Buff.IsEmpty())
			CleanBuffer.Add(Buff);

	return CleanBuffer;
}

TTuple<FString, TArray<FString>> FLexer::BreakDefinition(const FString& Definition)
{
	FString Name{ Definition };
	TArray<FString> Parameters;

	if (Name.Contains(":"))
	{
		FString ParametersString;
		Name.Split(":", &Name, &ParametersString);

		if (ParametersString.Contains(";"))
			ParametersString.ParseIntoArray(Parameters, TEXT(";"));
		else
			Parameters.Add(ParametersString);
	}

	return MakeTuple(Name, Parameters);
}


void FLexer::Localize(FStatement& Statement)
{
	auto Locale = [](FText& Text)
	{
		FString String{ Text.ToString() };

		// If starts and ends with `, try to localize.
		if (String.StartsWith(SYMBOL(Backtick)) && String.EndsWith(SYMBOL(Backtick)))
		{
			String.RemoveFromStart(SYMBOL(Backtick));
			String.RemoveFromEnd(SYMBOL(Backtick));
			Text = FText::FromString(String);
			TurnOffLocalization(Text);
			return;
		}

		// If the text does NOT start and ends with `, it is always culture invariant.
		if (String.StartsWith(SYMBOL(DoubleQuote)) && String.EndsWith(SYMBOL(DoubleQuote)))
		{
			String.RemoveFromStart(SYMBOL(DoubleQuote));
			String.RemoveFromEnd(SYMBOL(DoubleQuote));
			Text = FText::AsCultureInvariant(String);
			return;
		}

		if (String.StartsWith(SYMBOL(SingleQuote)) && String.EndsWith(SYMBOL(SingleQuote)))
		{
			String.RemoveFromStart(SYMBOL(SingleQuote));
			String.RemoveFromEnd(SYMBOL(SingleQuote));
			Text = FText::AsCultureInvariant(String);
			return;
		}

		Text = FText::AsCultureInvariant(Text);
	};

	for (auto& [Symbol, Parameters] : Statement.Conditions)
		for (FText& Text : Parameters)
			Locale(Text);

	for (auto& [Symbol, Parameters] : Statement.Commands)
		for (FText& Text : Parameters)
			Locale(Text);

	for (FText& Text : Statement.TargetArguments)
		Locale(Text);

	for (FText& Text : Statement.ExtraParameters)
		Locale(Text);
}


FString FLexer::Tokenize(FString Text)
{
	for (TPair<FName, TPair<FString, FString>> Token : Symbols)
	{
		TArray<TCHAR> CharArray = ( EscapeCharacter + Token.Value.Key ).GetCharArray();
		Text.ReplaceInline(CharArray.GetData(), *Token.Value.Value);
	}

	return Text;
}

FStatement FLexer::Detokenize(FStatement Statement)
{
	/* Replace 'Token' by 'Symbol'. */
	const auto Replace = [](FString Text) -> FString
	{
		for (TPair<FName, TPair<FString, FString>> Token : Symbols)
			Text.ReplaceInline(*Token.Value.Value, *Token.Value.Key);

		return Text;
	};
	const auto ReplaceName = [Replace](const FName& Text) -> FName { return FName(Replace(Text.ToString())); };
	const auto ReplaceText = [Replace](const FText& Text) -> FText { return FText::FromString(Replace(Text.ToString())); };

	Statement.Label = ReplaceName(Statement.Label);

	for (FString& Text : Statement.Arguments)
		Text = Replace(Text);

	Statement.Main = Replace(Statement.Main);
	Statement.Text = ReplaceText(Statement.Text);

	for (auto& [Symbol, Parameters] : Statement.Conditions)
		for (FText& Text : Parameters)
			Text = ReplaceText(Text);

	for (auto& [Symbol, Parameters] : Statement.Commands)
		for (FText& Text : Parameters)
			Text = ReplaceText(Text);

	for (FString& Tag : Statement.Tags)
		Tag = Replace(Tag);

	Statement.Target = ReplaceName(Statement.Target);

	for (FText& Text : Statement.TargetArguments)
    	Text = ReplaceText(Text);

	for (FText& Text : Statement.ExtraParameters)
		Text = ReplaceText(Text);

	Statement.SourceLine = Replace(Statement.SourceLine);
	Statement.Comment = Replace(Statement.Comment);

	return Statement;
}