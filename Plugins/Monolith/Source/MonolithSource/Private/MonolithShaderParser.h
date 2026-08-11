#pragma once

#include "MonolithCppParser.h" // Reuses FParsedSourceSymbol, FParsedFileResult

/**
 * Regex-based parser for HLSL shader files (.usf / .ush).
 * Extracts includes, defines, structs, and functions.
 * Direct port of Python shader_parser.py.
 */
class FMonolithShaderParser
{
public:
	/** Parse an HLSL shader file and extract symbols. Thread-safe (stateless). */
	FParsedFileResult ParseFile(const FString& FilePath);

private:
	void ExtractIncludes(const FString& Text, const TArray<FString>& Lines, FParsedFileResult& Result);
	void ExtractDefines(const FString& Text, const TArray<FString>& Lines, FParsedFileResult& Result);
	void ExtractStructs(const FString& Text, const TArray<FString>& Lines, FParsedFileResult& Result);
	void ExtractFunctions(const FString& Text, const TArray<FString>& Lines, FParsedFileResult& Result);

	int32 FindClosingBrace(const TArray<FString>& Lines, int32 OpenLineIdx);
	FString FindDocstring(const TArray<FString>& Lines, int32 FuncLineIdx);
};
