#pragma once

#include "CoreMinimal.h"

class FMonolithSourceDatabase;

/**
 * Second-pass reference extractor. Scans source files for:
 * - Function call sites (call references)
 * - Type usage (type references)
 *
 * Uses regex heuristics, NOT tree-sitter ASTs.
 * Less accurate than the Python version but functional for search indexing.
 *
 * What's NOT ported from Python:
 * - _resolve_local_var_type (obj.Method() → ClassName::Method resolution)
 * - Class-scope field type references
 * - Global-scope declaration references
 */
class FMonolithReferenceBuilder
{
public:
	FMonolithReferenceBuilder(FMonolithSourceDatabase& InDB, const TMap<FString, int64>& InSymbolMap);

	/** Extract references from a single file. Returns count of refs inserted. */
	int32 ExtractReferences(const FString& FilePath, int64 FileId);

private:
	/** Strip comments and string literals to avoid false positives. */
	FString StripCommentsAndStrings(const FString& Source);

	/** Find function bodies and extract call references within them. */
	int32 ExtractCallReferences(const TArray<FString>& Lines, int64 FileId);

	/** Find type identifiers in declarations. */
	int32 ExtractTypeReferences(const TArray<FString>& Lines, int64 FileId);

	/** Resolve a symbol name to its DB id. Tries exact match, then short name for qualified names. */
	int64 ResolveSymbol(const FString& Name) const;

	FMonolithSourceDatabase& DB;
	const TMap<FString, int64>& SymbolMap;
};
