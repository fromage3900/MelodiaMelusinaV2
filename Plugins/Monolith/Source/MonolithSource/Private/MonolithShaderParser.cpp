#include "MonolithShaderParser.h"
#include "MonolithSourceDatabase.h"
#include "Misc/FileHelper.h"
#include "Internationalization/Regex.h"

// Keywords that are never valid HLSL function return types or names
static const TSet<FString> NonFunctionKeywords = {
	TEXT("struct"), TEXT("class"), TEXT("enum"), TEXT("namespace"), TEXT("return"),
	TEXT("if"), TEXT("else"), TEXT("for"), TEXT("while"), TEXT("switch"),
	TEXT("case"), TEXT("do")
};

// ============================================================
// ParseFile — main entry point
// ============================================================

FParsedFileResult FMonolithShaderParser::ParseFile(const FString& FilePath)
{
	FParsedFileResult Result;
	Result.FilePath = FilePath;

	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *FilePath))
	{
		UE_LOG(LogMonolithSource, Warning, TEXT("ShaderParser: Failed to read file: %s"), *FilePath);
		return Result;
	}

	// Store source lines (required by indexing pipeline for InsertSourceChunks)
	Text.ParseIntoArray(Result.SourceLines, TEXT("\n"), false);

	// Extraction passes (same order as Python)
	ExtractIncludes(Text, Result.SourceLines, Result);
	ExtractDefines(Text, Result.SourceLines, Result);
	ExtractStructs(Text, Result.SourceLines, Result);
	ExtractFunctions(Text, Result.SourceLines, Result);

	return Result;
}

// ============================================================
// ExtractIncludes
// Port of Python: _RE_INCLUDE = re.compile(r'^\s*#include\s+["<]([^">]+)[">]', re.MULTILINE)
// ============================================================

void FMonolithShaderParser::ExtractIncludes(const FString& Text, const TArray<FString>& Lines, FParsedFileResult& Result)
{
	FRegexPattern Pattern(TEXT("^\\s*#include\\s+[\"<]([^\">]+)[\">]"));

	for (int32 i = 0; i < Lines.Num(); ++i)
	{
		FRegexMatcher Matcher(Pattern, Lines[i]);
		if (!Matcher.FindNext())
		{
			continue;
		}

		FString IncludeName = Matcher.GetCaptureGroup(1);
		Result.Includes.Add(IncludeName);

		FParsedSourceSymbol Sym;
		Sym.Kind = TEXT("include");
		Sym.Name = IncludeName;
		Sym.LineStart = i + 1; // 1-based
		Sym.LineEnd = i + 1;
		Sym.Signature = Lines[i].TrimStartAndEnd();
		Result.Symbols.Add(MoveTemp(Sym));
	}
}

// ============================================================
// ExtractDefines
// Port of Python: _RE_DEFINE = re.compile(r"^\s*#define\s+(\w+)\s*(.*?)$", re.MULTILINE)
// ============================================================

void FMonolithShaderParser::ExtractDefines(const FString& Text, const TArray<FString>& Lines, FParsedFileResult& Result)
{
	// Capture group 1 = macro name, group 2 = value (rest of line)
	FRegexPattern Pattern(TEXT("^\\s*#define\\s+(\\w+)\\s*(.*?)\\s*$"));

	for (int32 i = 0; i < Lines.Num(); ++i)
	{
		FRegexMatcher Matcher(Pattern, Lines[i]);
		if (!Matcher.FindNext())
		{
			continue;
		}

		FString Name = Matcher.GetCaptureGroup(1);
		FString Value = Matcher.GetCaptureGroup(2).TrimStartAndEnd();

		FParsedSourceSymbol Sym;
		Sym.Kind = TEXT("define");
		Sym.Name = Name;
		Sym.LineStart = i + 1;
		Sym.LineEnd = i + 1;

		// Build signature: "#define NAME VALUE" or "#define NAME" if no value
		if (!Value.IsEmpty())
		{
			Sym.Signature = FString::Printf(TEXT("#define %s %s"), *Name, *Value);
		}
		else
		{
			Sym.Signature = FString::Printf(TEXT("#define %s"), *Name);
		}

		Result.Symbols.Add(MoveTemp(Sym));
	}
}

// ============================================================
// ExtractStructs
// Port of Python: _RE_STRUCT = re.compile(r"^\s*struct\s+(\w+)\s*\{", re.MULTILINE)
// ============================================================

void FMonolithShaderParser::ExtractStructs(const FString& Text, const TArray<FString>& Lines, FParsedFileResult& Result)
{
	// Requires opening brace on the same line (matches Python pattern)
	FRegexPattern Pattern(TEXT("^\\s*struct\\s+(\\w+)\\s*\\{"));

	for (int32 i = 0; i < Lines.Num(); ++i)
	{
		FRegexMatcher Matcher(Pattern, Lines[i]);
		if (!Matcher.FindNext())
		{
			continue;
		}

		FString Name = Matcher.GetCaptureGroup(1);

		// FindClosingBrace takes 0-based index of the line that contains '{'
		int32 EndLine = FindClosingBrace(Lines, i);

		FParsedSourceSymbol Sym;
		Sym.Kind = TEXT("struct");
		Sym.Name = Name;
		Sym.LineStart = i + 1; // 1-based
		Sym.LineEnd = EndLine;
		Sym.Signature = FString::Printf(TEXT("struct %s"), *Name);
		Result.Symbols.Add(MoveTemp(Sym));
	}
}

// ============================================================
// ExtractFunctions
// Port of Python _RE_FUNCTION — per-line approach with multi-line param scanning.
//
// Python regex (re.MULTILINE):
//   ^[ \t]*([\w:]+(?:\s*<[^>]*>)?)   <- return type (possibly templated)
//   \s+(\w+)                           <- function name
//   \s*\(((?:[^)]*\n?)*?)\)           <- params (may span lines)
//
// C++ approach: match header line, then scan forward for closing ')' and '{'.
// ============================================================

void FMonolithShaderParser::ExtractFunctions(const FString& Text, const TArray<FString>& Lines, FParsedFileResult& Result)
{
	const int32 NumLines = Lines.Num();

	// Match: optional leading whitespace, return type (word chars + optional template),
	// whitespace, function name, optional whitespace, opening paren.
	// Capture group 1 = return type, group 2 = function name.
	FRegexPattern HeaderPattern(TEXT("^[ \\t]*([\\w:]+(?:\\s*<[^>]*>)?)\\s+(\\w+)\\s*\\("));

	for (int32 i = 0; i < NumLines; ++i)
	{
		FRegexMatcher Matcher(HeaderPattern, Lines[i]);
		if (!Matcher.FindNext())
		{
			continue;
		}

		FString ReturnType = Matcher.GetCaptureGroup(1).TrimStartAndEnd();
		FString FuncName = Matcher.GetCaptureGroup(2);

		// Filter out non-function keywords
		if (NonFunctionKeywords.Contains(ReturnType) || NonFunctionKeywords.Contains(FuncName))
		{
			continue;
		}

		// ---- Find closing ')' for parameter list ----
		// Start scanning from the '(' on line i. The match ends at the position
		// just before the paren — we need to find the character position of '(' first.
		// Since FRegexMatcher doesn't expose char positions, we just look from line i onward.

		int32 ParenDepth = 0;
		int32 ParenCloseLineIdx = -1;
		FString ParamsAccumulated;
		bool bFoundOpen = false;

		for (int32 j = i; j < NumLines && j < i + 64; ++j)
		{
			const FString& ScanLine = Lines[j];
			int32 StartChar = (j == i) ? 0 : 0; // full line for j>i

			for (int32 k = StartChar; k < ScanLine.Len(); ++k)
			{
				TCHAR Ch = ScanLine[k];
				if (Ch == TEXT('('))
				{
					if (!bFoundOpen)
					{
						// First '(' — only start tracking if it's past the function name position
						// We already matched line i, so for j==i we need to find the first '('
						bFoundOpen = true;
						ParenDepth = 1;
					}
					else
					{
						++ParenDepth;
					}
				}
				else if (Ch == TEXT(')') && bFoundOpen)
				{
					--ParenDepth;
					if (ParenDepth == 0)
					{
						// Collect params from open paren through here
						// (we don't need the exact text for signature, just line index)
						ParenCloseLineIdx = j;
						goto FoundCloseParen;
					}
				}
				else if (bFoundOpen)
				{
					// Collect all chars inside the outermost parens (including nested paren contents)
					ParamsAccumulated.AppendChar(Ch);
				}
			}
			if (bFoundOpen && j > i)
			{
				// Add newline between lines when accumulating params
				ParamsAccumulated.AppendChar(TEXT('\n'));
			}
		}

		// No closing paren found within scan range — skip
		continue;

	FoundCloseParen:

		// ---- Check that a '{' follows ')' without an intervening ';' ----
		// (definition, not declaration)
		int32 BraceLineIdx = -1;
		bool bFoundSemicolon = false;

		for (int32 j = ParenCloseLineIdx; j < NumLines && j < ParenCloseLineIdx + 8; ++j)
		{
			const FString& ScanLine = Lines[j];
			// For ParenCloseLineIdx, start scanning from after the ')'
			// For simplicity we scan the full line — false positives are rare in HLSL
			for (TCHAR Ch : ScanLine)
			{
				if (Ch == TEXT('{'))
				{
					BraceLineIdx = j;
					goto FoundOpenBrace;
				}
				if (Ch == TEXT(';'))
				{
					bFoundSemicolon = true;
					goto NoBrace;
				}
			}
		}
		goto NoBrace;

	FoundOpenBrace:
		{
			// Build cleaned params string (collapse whitespace, strip newlines)
			FString ParamsClean = ParamsAccumulated.Replace(TEXT("\n"), TEXT(" "));
			// Collapse multiple spaces
			while (ParamsClean.Contains(TEXT("  ")))
			{
				ParamsClean = ParamsClean.Replace(TEXT("  "), TEXT(" "));
			}
			ParamsClean.TrimStartAndEndInline();

			FString Signature = FString::Printf(TEXT("%s %s(%s)"), *ReturnType, *FuncName, *ParamsClean);
			FString Docstring = FindDocstring(Lines, i);
			int32 EndLine = FindClosingBrace(Lines, BraceLineIdx);

			FParsedSourceSymbol Sym;
			Sym.Kind = TEXT("function");
			Sym.Name = FuncName;
			Sym.LineStart = i + 1; // 1-based
			Sym.LineEnd = EndLine;
			Sym.Signature = Signature;
			Sym.Docstring = Docstring;
			Result.Symbols.Add(MoveTemp(Sym));
		}

	NoBrace:
		(void)bFoundSemicolon; // suppress unused-label warning in some compilers
		continue;
	}
}

// ============================================================
// FindClosingBrace
// OpenLineIdx is 0-based. Returns 1-based line number of closing '}'.
// ============================================================

int32 FMonolithShaderParser::FindClosingBrace(const TArray<FString>& Lines, int32 OpenLineIdx)
{
	int32 Depth = 0;

	for (int32 i = OpenLineIdx; i < Lines.Num(); ++i)
	{
		for (TCHAR Ch : Lines[i])
		{
			if (Ch == TEXT('{'))
			{
				++Depth;
			}
			else if (Ch == TEXT('}'))
			{
				--Depth;
				if (Depth == 0)
				{
					return i + 1; // 1-based
				}
			}
		}
	}

	// No matching brace found — return last line (matches Python fallback)
	return Lines.Num();
}

// ============================================================
// FindDocstring
// Port of Python _find_docstring — look backward from FuncLineIdx (0-based)
// for /** ... */ block comments or // line comments.
// ============================================================

FString FMonolithShaderParser::FindDocstring(const TArray<FString>& Lines, int32 FuncLineIdx)
{
	// Scan backward from the line immediately above the function
	int32 ScanIdx = FuncLineIdx - 1;

	// Skip any blank lines between comment and function
	while (ScanIdx >= 0 && Lines[ScanIdx].TrimStartAndEnd().IsEmpty())
	{
		--ScanIdx;
	}

	if (ScanIdx < 0)
	{
		return FString();
	}

	FString TopLine = Lines[ScanIdx].TrimStartAndEnd();

	// ---- Case A: block comment ending with '*/' ----
	if (TopLine.EndsWith(TEXT("*/")))
	{
		TArray<FString> CommentLines;

		// Strip trailing '*/'
		FString Current = TopLine.LeftChop(2).TrimStartAndEnd();
		if (!Current.IsEmpty())
		{
			CommentLines.Insert(Current, 0);
		}
		--ScanIdx;

		while (ScanIdx >= 0)
		{
			FString BlockLine = Lines[ScanIdx].TrimStartAndEnd();

			if (BlockLine.StartsWith(TEXT("/**")))
			{
				// Opening of block comment — extract any inline text after '/**'
				FString Content = BlockLine.Mid(3).TrimStart();
				// Strip trailing '*/' if it's a single-line block comment
				if (Content.EndsWith(TEXT("*/")))
				{
					Content = Content.LeftChop(2).TrimStartAndEnd();
				}
				if (!Content.IsEmpty())
				{
					CommentLines.Insert(Content, 0);
				}
				break;
			}
			else if (BlockLine.StartsWith(TEXT("/*")))
			{
				// Non-doc block comment opener — still valid
				FString Content = BlockLine.Mid(2).TrimStart();
				if (!Content.IsEmpty())
				{
					CommentLines.Insert(Content, 0);
				}
				break;
			}
			else if (BlockLine.StartsWith(TEXT("*")))
			{
				// Middle line of block comment — strip leading '* '
				FString Content = BlockLine.Mid(1).TrimStart();
				if (!Content.IsEmpty())
				{
					CommentLines.Insert(Content, 0);
				}
			}
			else
			{
				// Something else — end of block comment search
				break;
			}

			--ScanIdx;
		}

		if (CommentLines.Num() > 0)
		{
			return FString::Join(CommentLines, TEXT("\n"));
		}
		return FString();
	}

	// ---- Case B: consecutive '//' line comments ----
	if (TopLine.StartsWith(TEXT("//")))
	{
		TArray<FString> CommentLines;

		int32 j = ScanIdx;
		while (j >= 0)
		{
			FString Line = Lines[j].TrimStartAndEnd();
			if (Line.StartsWith(TEXT("//")))
			{
				// Strip leading '//' and any extra '/' (handles /// too)
				FString Content = Line;
				while (Content.StartsWith(TEXT("/")))
				{
					Content = Content.Mid(1);
				}
				Content.TrimStartInline();
				CommentLines.Insert(Content, 0);
				--j;
			}
			else
			{
				break;
			}
		}

		if (CommentLines.Num() > 0)
		{
			return FString::Join(CommentLines, TEXT("\n"));
		}
	}

	return FString();
}
