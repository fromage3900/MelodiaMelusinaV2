// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Expression.h"
#include "StatementType.h"

#include "CoreMinimal.h"
#include "Statement.generated.h"

/**
 * Quillscript statement as a struct.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FStatement
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data")
	EStatementType Type{ EStatementType::Comment };

	/**
	 * Label:		label name
	 * Dialogue:	label name
	 * Option:		label name
	 * Command:		label name
	 * Router:		label name
	 * Condition:	label name
	 * Directive:	nothing
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data")
	FName Label;

	/**
	 * Label:		label arguments
	 * Dialogue:	label arguments
	 * Option:		label arguments
	 * Command:		label arguments
	 * Router:		label arguments
	 * Condition:	label arguments
	 * Directive:	nothing
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", AdvancedDisplay)
	TArray<FString> Arguments;

	/**
	 * Label:		nothing
	 * Dialogue:	speaker name
	 * Option:		nothing
	 * Command:		nothing
	 * Router:		target label
	 * Condition:	nothing
	 * Directive:	name
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data")
	FString Main;

	/**
	 * Label:		display name
	 * Dialogue:	text
	 * Option:		text
	 * Command:		nothing
	 * Router:		nothing
	 * Condition:	nothing
	 * Directive:	nothing
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", meta = ( Multiline = true ))
	FText Text;

	/**
	 * Label:		conditions
	 * Dialogue:	conditions
	 * Option:		conditions
	 * Command:		conditions
	 * Router:		conditions
	 * Condition:	conditions
	 * Directive:	nothing
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data")
	TArray<FExpression> Conditions;

	/**
	 * Label:		nothing
	 * Dialogue:	commands
	 * Option:		commands
	 * Command:		commands
	 * Router:		nothing
	 * Condition:	nothing
	 * Directive:	nothing
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data")
	TArray<FExpression> Commands;

	/**
	 * Label:		tags
	 * Dialogue:	tags
	 * Option:		tags
	 * Command:		tags
	 * Router:		tags
	 * Condition:	tags
	 * Directive:	tags
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data")
	TArray<FString> Tags;

	/**
	 * Label:		target label on failure
	 * Dialogue:	target label on failure
	 * Option:		target label on selected
	 * Command:		target label on failure
	 * Router:		target label on failure
	 * Condition:	nothing
	 * Directive:	nothing
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", AdvancedDisplay)
	FName Target;

	/**
	 * Label:		target arguments
	 * Dialogue:	target arguments
	 * Option:		target arguments
	 * Command:		target arguments
	 * Router:		target arguments on failure
	 * Condition:	nothing
	 * Directive:	nothing
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", AdvancedDisplay)
	TArray<FText> TargetArguments;

	/**
	 * Label:		nothing
	 * Dialogue:	nothing
	 * Option:		nothing
	 * Command:		nothing
	 * Router:		target arguments on success
	 * Condition:	nothing
	 * Directive:	parameters
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", AdvancedDisplay)
	TArray<FText> ExtraParameters;

	/**
	 * Label:		is covert
	 * Dialogue:	is covert
	 * Option:		is covert
	 * Command:		is covert
	 * Router:		is covert
	 * Condition:	is covert
	 * Directive:	is covert
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", AdvancedDisplay)
	bool bCovert{ false };

	/**
	 * Label:		is channel
	 * Dialogue:	is channel
	 * Option:		is channel
	 * Command:		is channel
	 * Router:		is channel
	 * Condition:	is channel
	 * Directive:	is channel
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", AdvancedDisplay)
	bool bChannel{ false };

	/** Source script line. */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", AdvancedDisplay)
	FString SourceLine;

	/** Inline comment. */
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Data", AdvancedDisplay)
	FString Comment;


	/// State

	bool HasLabel() const
	{
		return !Label.IsNone();
	}

	bool HasLabelArguments() const
	{
		return !Arguments.IsEmpty();
	}

	bool HasTarget() const
	{
		return !Target.IsNone();
	}

	bool HasTargetArguments() const
	{
		return !TargetArguments.IsEmpty();
	}

	bool HasTag(const FString& Tag) const
	{
		return Tags.Contains(Tag);
	}

	bool IsChannel() const
	{
		return bChannel && (
			Type == EStatementType::Dialogue ||
			Type == EStatementType::Label ||
			Type == EStatementType::Router ||
			Type == EStatementType::Command
		);
	}

	bool IsCovert() const
	{
		return bCovert || HasLabelArguments();
	}


	/// Condition

	bool IsIf() const
	{
		return Type == EStatementType::Condition &&
			(
				Main.Equals("if:") ||
				( !IsElseIf() && !IsElse() && !IsEndIf() )
			);
	}

	bool IsElseIf() const
	{
		return Type == EStatementType::Condition && Main.Equals("elseif:");
	}

	bool IsElse() const
	{
		return Type == EStatementType::Condition && Main.Equals("else:");
	}

	bool IsEndIf() const
	{
		return Type == EStatementType::Condition && Main.Equals("endif");
	}


	/// Special Tags

	// #once
	bool IsPlayOnce() const
	{
		return HasTag("once");
	}

	// #mark
	bool IsMarked() const
	{
		return HasTag("mark");
	}
};