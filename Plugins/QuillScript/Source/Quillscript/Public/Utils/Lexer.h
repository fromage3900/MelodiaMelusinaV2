// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Base/InstructionType.h"

#include "CoreMinimal.h"

struct FExpression;
struct FStatement;
enum class EStatementType : uint8;

#define SYMBOL(Value)	FLexer::Symbols[#Value].Key

/**
 * Static object responsible for parsing, lexing, transpiling, and other conversion functions to handle Quillscript language source text.
 */
class FLexer final
{
public:
	/**
	 * Parse a Quillscript text into a list of statements.
	 */
	static TArray<FStatement> Parse(const FString& SourceScriptText);


	/// Quillscript Language Symbols, Reserved Words, and Keywords

	inline static const TMap<FName, TPair<FString, FString>> Symbols{
		// Statements.
		{ "Dialogue",			{ "-",		"__TKN_DLG__" } },
		{ "Option",			{ "*",		"__TKN_SLC__" } },
		{ "Label",			{ "@",		"__TKN_LBL__" } },
		{ "Router",			{ "->",		"__TKN_ROT__" } },
		{ "Command",			{ "$",		"__TKN_CMD__" } },
		{ "Condition",		{ "?",		"__TKN_CDT__" } },
		{ "Directive",		{ "~",		"__TKN_DTV__" } },
		{ "Comment",			{ "//",		"__TKN_CMT__" } },

		{ "Covert",			{ "<@>",		"__TKN_CVL__" } },
		{ "Channel",			{ "<->",		"__TKN_CHN__" } },
		{ "If",				{ "if:",		"__TKN_IFF__" } },
		{ "ElseIf",			{ "elseif:",	"__TKN_ELF__" } },
		{ "Else",				{ "else:",	"__TKN_ELS__" } },
		{ "EndIf",			{ "endif",	"__TKN_ENF__" } },

		// Syntax.
		{ "Tag",				{ "#",		"__TKN_TAG__" } },
		{ "Concatenation",	{ "|",		"__TKN_CNT__" } },
		{ "Functor",			{ ".",		"__TKN_FUN__" } },
		{ "Separator",		{ ",",		"__TKN_SEP__" } },
		{ "Repeat",			{ "...",		"__TKN_RPT__" } },
		{ "Gate",				{ "---",		"__TKN_GTE__" } },
		{ "Map",				{ "::",		"__TKN_MAP__" } },

		// Brackets.
		{ "CurlyOpen",		{ "{",		"__TKN_CLY__" } },
		{ "CurlyClose",		{ "}",		"__TKN_CLC__" } },
		{ "SquareOpen",		{ "[",		"__TKN_SQR__" } },
		{ "SquareClose",		{ "]",		"__TKN_SQC__" } },
		{ "RoundOpen",		{ "(",		"__TKN_RND__" } },
		{ "RoundClose",		{ ")",		"__TKN_RDC__" } },

		// Quotations.
		{ "DoubleQuote",		{ "\"",		"__TKN_DQT__" } },
		{ "SingleQuote",		{ "'",		"__TKN_SQT__" } },
		{ "Backtick",			{ "`",		"__TKN_BTK__" } },

		// Operators.
		{ "Assignment",		{ "=",		"__TKN_ASG__" } },
		{ "Constructor",		{ ":",		"__TKN_CTR__" } },
		{ "Splitter",			{ ":",		"__TKN_SPL__" } },

		{ "And",				{ "and",		"__TKN_AND__" } },
		{ "Or",				{ "or",		"__TKN_ORR__" } },
		{ "Equal",			{ "==",		"__TKN_EQL__" } },
		{ "StrictEqual",		{ "===",		"__TKN_SEQ__" } },
		{ "NotEqual",			{ "!=",		"__TKN_NQL__" } },
		{ "StrictNotEqual",	{ "!==",		"__TKN_SNQ__" } },
		{ "Less",				{ "<",		"__TKN_SML__" } },
		{ "LessEqual",		{ "<=",		"__TKN_SMQ__" } },
		{ "Greater",			{ ">",		"__TKN_GTR__" } },
		{ "GreaterEqual",		{ ">=",		"__TKN_GTQ__" } },

		{ "Addition",			{ "+",		"__TKN_PLS__" } },
		{ "Subtraction",		{ "-",		"__TKN_MIN__" } },
		{ "Multiplication",	{ "*",		"__TKN_MLT__" } },
		{ "Division",			{ "/",		"__TKN_DIV__" } },
		{ "Remainder",		{ "%",		"__TKN_RMD__" } },
		{ "Power",			{ "^",		"__TKN_POW__" } },

		{ "Self",				{ "{&}",		"__TKN_SLF__" } },

		// Call Method.
		{ "Reference",		{ "&",		"__TKN_REF__" } },
		{ "Class",			{ "^",		"__TKN_CLS__" } },
		{ "ByTag",			{ "%",		"__TKN_UET__" } },

		// Variables.
		{ "Temp",				{ ":",		"__TKN_TMP__" } },
		{ "Out",				{ "$",		"__TKN_OUT__" } },
		{ "Arg",				{ "@",		"__TKN_ARG__" } },

		// Reserved words.
		{ "On",				{ "on",		"__TKN_ONN__" } },
		{ "Off",				{ "off",		"__TKN_OFF__" } }
	};

	inline static const FString DirectiveDefine		= "define";
	inline static const FString DirectiveReplace	= "replace";
	inline static const FString DirectiveImport		= "import";
	inline static const FString DirectiveInclude	= "include";
	inline static const FString DirectiveInject		= "inject";
	inline static const FString DirectiveStart		= "start";
	inline static const FString DirectiveCheckpoint	= "checkpoint";

	inline static const FString EscapeCharacter = "\\";

	static TArray<FString> StringToArrayOfSymbols(FString String);
	static TArray<FString> InfixToPostfix(TArray<FString> InfixExpression);
	static TArray<FText> StringToParameters(const FString& String, const FString& Separator = " ");

	static void TurnOffLocalization(FText& Value);

	static FString GetFromArrayString(FString String, const int32 Index);
	static FString GetFromMapString(FString String, const FString& Key);


private:
	/// Data

	static EStatementType GetStatementType(FString Statement);
	static FString GetStatementSymbol(const EStatementType Statement);
	static EInstructionType GetInstructionType(FString Instruction, const FStatement& Statement);
	static TArray<FString> GetOperators();
	static int32 GetOperatorPrecedence(const FString& Operator);


	/// Transpile

	static TArray<FString> BreakLineIntoInstructions(const FString& Line);

	static FName CreateLabelInstruction(FString SourceString, FStatement& Statement);
	static FString CreateMainInstruction(FString SourceString, FStatement& Statement);
	static FExpression CreateConditionInstruction(FString SourceString);
	static FExpression CreateCommandInstruction(FString SourceString);
	static FName CreateTargetInstruction(FString SourceString, FStatement& Statement);
	static TArray<FString> CreateTagInstruction(FString SourceString);

	static TPair<FName, TArray<FText>> GetTemplateData(FString SourceString);


	/// Parsing Time Directives and Special Tags

	static TArray<FString> ResolvePreDirectives(TArray<FString> Statements);
	static FStatement ResolvePostDirectives(FStatement Statement);

	static TArray<FString> GetAllDefinitionsInString(const FString& Definition);
	static TTuple<FString, TArray<FString>> BreakDefinition(const FString& Definition);

	static void Localize(FStatement& Statement);


	/// Pipes

	static FString Tokenize(FString Text);
	static FStatement Detokenize(FStatement Statement);
};