#pragma once

#include "CoreMinimal.h"

// ============================================================
// Parsed symbol — one per class/struct/enum/function/variable/macro/typedef
// ============================================================

struct FParsedSourceSymbol
{
	FString Name;
	FString Kind;           // class, struct, enum, function, variable, macro, typedef
	int32 LineStart = 0;    // 1-based
	int32 LineEnd = 0;      // 1-based
	FString Signature;
	FString Docstring;
	FString Access;         // public, protected, private
	bool bIsUEMacro = false;
	TArray<FString> BaseClasses;
	FString ParentClass;    // Enclosing class name (for members)
};

// ============================================================
// Parsed file result — all symbols + metadata from one source file
// ============================================================

struct FParsedFileResult
{
	FString FilePath;
	TArray<FParsedSourceSymbol> Symbols;
	TArray<FString> Includes;
	TArray<FString> SourceLines;
};

// ============================================================
// C++ parser — regex-based symbol extraction (stateless, thread-safe)
// ============================================================

class FMonolithCppParser
{
public:
	/** Parse a C++ file and extract symbols. Thread-safe (stateless). */
	FParsedFileResult ParseFile(const FString& FilePath);

private:
	// Extraction passes
	void ExtractIncludes(const FString& Source, FParsedFileResult& Result);
	void ExtractClassesAndStructs(const TArray<FString>& OrigLines, const TArray<FString>& CleanLines, FParsedFileResult& Result);
	void ExtractEnums(const TArray<FString>& OrigLines, const TArray<FString>& CleanLines, FParsedFileResult& Result);
	void ExtractFreeFunctions(const TArray<FString>& OrigLines, const TArray<FString>& CleanLines, FParsedFileResult& Result);
	void ExtractMacrosAndTypedefs(const TArray<FString>& OrigLines, FParsedFileResult& Result);
	// ParentClass is BY VALUE — ExtractMembers Adds to Result.Symbols, so a reference into
	// that array's backing store would dangle after a reallocation (see definition comment).
	void ExtractMembers(const TArray<FString>& OrigLines, int32 BodyStartLine, int32 BodyEndLine,
		FString ParentClass, const FString& DefaultAccess, FParsedFileResult& Result);

	// Helpers
	FString ExtractDocstring(const TArray<FString>& Lines, int32 TargetLine, bool bSkipUEMacro = false);
	int32 FindClosingBrace(const TArray<FString>& Lines, int32 OpenBraceLine);
	bool IsUEMacroLine(const FString& Line);
	void ParseBaseClasses(const FString& InheritanceClause, TArray<FString>& OutBases);
};
