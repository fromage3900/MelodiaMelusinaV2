#include "MonolithReferenceBuilder.h"
#include "MonolithSourceDatabase.h"
#include "MonolithUEPreprocessor.h"
#include "Misc/FileHelper.h"
#include "Internationalization/Regex.h"

// ============================================================
// Constructor
// ============================================================

FMonolithReferenceBuilder::FMonolithReferenceBuilder(FMonolithSourceDatabase& InDB, const TMap<FString, int64>& InSymbolMap)
	: DB(InDB)
	, SymbolMap(InSymbolMap)
{
}

// ============================================================
// ExtractReferences — main entry point
// ============================================================

int32 FMonolithReferenceBuilder::ExtractReferences(const FString& FilePath, int64 FileId)
{
	FString Source;
	if (!FFileHelper::LoadFileToString(Source, *FilePath))
	{
		UE_LOG(LogMonolithSource, Warning, TEXT("ReferenceBuilder: failed to read %s"), *FilePath);
		return 0;
	}

	// Strip UE macros first, then comments/strings — same pipeline as the first-pass parser
	FString Clean = MonolithUEPreprocessor::PreprocessSource(Source);
	Clean = StripCommentsAndStrings(Clean);

	TArray<FString> Lines;
	Clean.ParseIntoArray(Lines, TEXT("\n"), false);

	const int32 CallCount = ExtractCallReferences(Lines, FileId);
	const int32 TypeCount = ExtractTypeReferences(Lines, FileId);

	return CallCount + TypeCount;
}

// ============================================================
// StripCommentsAndStrings
// ============================================================
//
// Walks character-by-character and replaces comment/string content with spaces.
// Newline positions are preserved so line numbers remain correct — same invariant
// as MonolithUEPreprocessor::PreprocessSource().
//
// Handles:
//   //  line comments  → spaces to end of line (newline kept)
//   /* */  block comments → spaces (newlines kept)
//   "..."  string literals → spaces (including escaped-quote inside: \")
// ============================================================

FString FMonolithReferenceBuilder::StripCommentsAndStrings(const FString& Source)
{
	TArray<TCHAR> Buf = TArray<TCHAR>(Source.GetCharArray());
	// Ensure null terminator present (GetCharArray includes it)
	const int32 Len = Buf.Num() > 0 ? Buf.Num() - 1 : 0; // exclude null terminator

	int32 i = 0;
	while (i < Len)
	{
		const TCHAR C  = Buf[i];
		const TCHAR C1 = (i + 1 < Len) ? Buf[i + 1] : TEXT('\0');

		if (C == TEXT('/') && C1 == TEXT('/'))
		{
			// Line comment — blank to end of line
			Buf[i]     = TEXT(' ');
			Buf[i + 1] = TEXT(' ');
			i += 2;
			while (i < Len && Buf[i] != TEXT('\n'))
			{
				Buf[i] = TEXT(' ');
				++i;
			}
			// Leave the newline itself intact
		}
		else if (C == TEXT('/') && C1 == TEXT('*'))
		{
			// Block comment — blank until closing */
			Buf[i]     = TEXT(' ');
			Buf[i + 1] = TEXT(' ');
			i += 2;
			while (i < Len)
			{
				if (Buf[i] == TEXT('*') && i + 1 < Len && Buf[i + 1] == TEXT('/'))
				{
					Buf[i]     = TEXT(' ');
					Buf[i + 1] = TEXT(' ');
					i += 2;
					break;
				}
				if (Buf[i] != TEXT('\n'))
				{
					Buf[i] = TEXT(' ');
				}
				++i;
			}
		}
		else if (C == TEXT('"'))
		{
			// String literal — blank contents (handle \" escapes)
			Buf[i] = TEXT(' ');
			++i;
			while (i < Len)
			{
				if (Buf[i] == TEXT('\\') && i + 1 < Len)
				{
					// Escaped character — blank both
					Buf[i]     = TEXT(' ');
					Buf[i + 1] = TEXT(' ');
					i += 2;
				}
				else if (Buf[i] == TEXT('"'))
				{
					Buf[i] = TEXT(' ');
					++i;
					break;
				}
				else
				{
					if (Buf[i] != TEXT('\n'))
					{
						Buf[i] = TEXT(' ');
					}
					++i;
				}
			}
		}
		else
		{
			++i;
		}
	}

	return FString(Buf.GetData());
}

// ============================================================
// Keyword skip set — things that look like function calls but aren't
// ============================================================

static bool IsSkippedKeyword(const FString& Name)
{
	static const TSet<FString> Keywords = {
		TEXT("if"),
		TEXT("for"),
		TEXT("while"),
		TEXT("switch"),
		TEXT("return"),
		TEXT("sizeof"),
		TEXT("alignof"),
		TEXT("decltype"),
		TEXT("static_cast"),
		TEXT("dynamic_cast"),
		TEXT("reinterpret_cast"),
		TEXT("const_cast"),
		TEXT("new"),
		TEXT("delete"),
		TEXT("throw"),
		TEXT("catch"),
		TEXT("else"),
		TEXT("do"),
	};
	return Keywords.Contains(Name);
}

// ============================================================
// ExtractCallReferences
// ============================================================
//
// Strategy:
//   1. Scan lines for function *definition* headers (name followed by { on same or
//      subsequent line). Track the caller symbol id.
//   2. Walk the brace-delimited body, collecting call expressions: word(
//   3. Resolve caller + callee in SymbolMap, insert "call" references.
//
// Line numbers are 1-based throughout.
// ============================================================

int32 FMonolithReferenceBuilder::ExtractCallReferences(const TArray<FString>& Lines, int64 FileId)
{
	int32 TotalInserted = 0;
	const int32 NumLines = Lines.Num();

	// Pattern: function definition header ending with optional modifiers and {
	// Group 1 = qualified function name (may include ClassName::)
	// We require { on the same line to anchor the body start.
	FRegexPattern FuncDefPattern(
		TEXT("\\b(\\w+(?:::\\w+)*)\\s*\\([^;]*\\)\\s*(?:const\\s*)?(?:override\\s*)?(?:final\\s*)?(?:noexcept\\s*)?\\{"));

	// Pattern: call expression  word(  or  word::word(
	FRegexPattern CallPattern(TEXT("\\b(\\w+(?:::\\w+)*)\\s*\\("));

	for (int32 LineIdx = 0; LineIdx < NumLines; ++LineIdx)
	{
		const FString& Line = Lines[LineIdx];

		FRegexMatcher FuncMatcher(FuncDefPattern, Line);
		if (!FuncMatcher.FindNext())
		{
			continue;
		}

		// Found a function definition on this line
		const FString CallerName = FuncMatcher.GetCaptureGroup(1);

		// Skip obvious non-function matches: control flow, casts, etc.
		if (IsSkippedKeyword(CallerName))
		{
			continue;
		}

		const int64 CallerId = ResolveSymbol(CallerName);

		// Determine brace depth — the opening { is on LineIdx.
		// Walk forward tracking depth until we find the matching close.
		int32 BraceDepth  = 0;
		int32 BodyEndLine = LineIdx; // will be updated

		// Count braces on the definition line itself first
		for (TCHAR Ch : Line)
		{
			if      (Ch == TEXT('{')) ++BraceDepth;
			else if (Ch == TEXT('}')) --BraceDepth;
		}

		// If already balanced (rare: empty inline function), body is just this line
		if (BraceDepth <= 0)
		{
			BodyEndLine = LineIdx;
		}
		else
		{
			// Walk subsequent lines to find closing brace
			int32 ScanLine = LineIdx + 1;
			while (ScanLine < NumLines && BraceDepth > 0)
			{
				for (TCHAR Ch : Lines[ScanLine])
				{
					if      (Ch == TEXT('{')) ++BraceDepth;
					else if (Ch == TEXT('}')) --BraceDepth;
				}
				++ScanLine;
			}
			BodyEndLine = ScanLine - 1;
		}

		// Now scan the body lines for call expressions
		TSet<int64> SeenCallees;

		for (int32 BodyLine = LineIdx + 1; BodyLine <= BodyEndLine && BodyLine < NumLines; ++BodyLine)
		{
			FRegexMatcher CallMatcher(CallPattern, Lines[BodyLine]);
			while (CallMatcher.FindNext())
			{
				const FString CalleeName = CallMatcher.GetCaptureGroup(1);

				if (IsSkippedKeyword(CalleeName))
				{
					continue;
				}

				const int64 CalleeId = ResolveSymbol(CalleeName);
				if (CalleeId == 0)
				{
					continue;
				}
				if (CalleeId == CallerId)
				{
					continue; // Skip self-reference
				}
				if (SeenCallees.Contains(CalleeId))
				{
					continue; // Deduplicate within this function body
				}

				SeenCallees.Add(CalleeId);
				DB.InsertReference(CallerId, CalleeId, TEXT("call"), FileId, BodyLine + 1); // 1-based
				++TotalInserted;
			}
		}

		// Skip past the body so we don't re-enter it as a new function search
		LineIdx = BodyEndLine;
	}

	return TotalInserted;
}

// ============================================================
// ExtractTypeReferences
// ============================================================
//
// Broad scan: find all uppercase-leading identifiers on each line that exist in
// the SymbolMap. Deduplicate per file. Insert as "type" refs with from_symbol_id=0
// (scope not tracked).
//
// This catches types wherever they appear (declarations, templates, casts, etc.)
// without trying to parse declaration grammar — simpler and more robust.
// ============================================================

int32 FMonolithReferenceBuilder::ExtractTypeReferences(const TArray<FString>& Lines, int64 FileId)
{
	// Match bare identifiers that start with an uppercase letter (UE convention)
	FRegexPattern TypePattern(TEXT("\\b([A-Z]\\w+)\\b"));

	TSet<int64> SeenTypes;
	int32 TotalInserted = 0;

	for (int32 LineIdx = 0; LineIdx < Lines.Num(); ++LineIdx)
	{
		FRegexMatcher Matcher(TypePattern, Lines[LineIdx]);
		while (Matcher.FindNext())
		{
			const FString TypeName = Matcher.GetCaptureGroup(1);
			const int64 TypeId = ResolveSymbol(TypeName);
			if (TypeId == 0)
			{
				continue;
			}
			if (SeenTypes.Contains(TypeId))
			{
				continue;
			}

			SeenTypes.Add(TypeId);
			DB.InsertReference(0, TypeId, TEXT("type"), FileId, LineIdx + 1); // 1-based
			++TotalInserted;
		}
	}

	return TotalInserted;
}

// ============================================================
// ResolveSymbol
// ============================================================

int64 FMonolithReferenceBuilder::ResolveSymbol(const FString& Name) const
{
	if (Name.IsEmpty())
	{
		return 0;
	}

	const int64* Found = SymbolMap.Find(Name);
	if (Found)
	{
		return *Found;
	}

	// Try short name for qualified names like "ClassName::Method"
	int32 ColonIdx = INDEX_NONE;
	if (Name.FindLastChar(TEXT(':'), ColonIdx) && ColonIdx + 1 < Name.Len())
	{
		const FString ShortName = Name.Mid(ColonIdx + 1);
		Found = SymbolMap.Find(ShortName);
		if (Found)
		{
			return *Found;
		}
	}

	return 0;
}
