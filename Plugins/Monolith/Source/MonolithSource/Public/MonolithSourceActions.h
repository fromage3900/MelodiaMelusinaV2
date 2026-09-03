#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithSourceDatabase;

/**
 * 9 engine source intelligence actions + 1 reindex trigger.
 * Ports the Python unreal-source-mcp server tools to native C++.
 */
class FMonolithSourceActions
{
public:
	static void RegisterAll();

	// Public for unit testing (MonolithCppErgonomicsTest.cpp) — pure, stateless helpers.
	/**
	 * Derive the canonical #include form from an indexed file path. A path under
	 * Public/ | Classes/ | Internal/ strips that prefix and returns an includable
	 * cross-module form (bOutIncludable = true). A Private/ path is NOT includable
	 * from another module: bOutIncludable = false, the same-module relative form is
	 * returned, and OutWarning carries the not-includable note. No recognised prefix
	 * (e.g. an engine header outside the Public/Private convention) -> basename
	 * fallback. Always forward-slashed.
	 */
	static FString DeriveIncludePath(const FString& IndexedFilePath, bool& bOutIncludable, FString& OutWarning);

	/**
	 * Compact a (possibly multi-line) declaration into a single-line signature:
	 * accumulates from StartIdx forward to the closing of the parameter list and
	 * the terminating `;` or opening `{`, strips trailing macro `\` continuations
	 * and any inline body, and collapses whitespace. Used by get_signature
	 * (item 2) for the declaration-read path and exposed for unit testing.
	 */
	static FString CompactDeclaration(const TArray<FString>& Lines, int32 StartIdx);

	// --- Phase 2 shared composition helpers (item 4 calls these, NOT the JSON
	//     handlers; public for unit testing — see MonolithCppErgonomicsTest.cpp).

	/**
	 * Resolve a symbol's canonical include + owning module from the DB. Mirrors the
	 * item-1 (get_include_path) resolution: resolves Class::Method via the owning
	 * class row, prefers a header among same-name rows, derives the includable form.
	 * Returns false when no class row + no FTS hit resolve it.
	 */
	static bool ResolveIncludeForSymbol(FMonolithSourceDatabase* DB, const FString& Symbol,
		FString& OutInclude, bool& OutIncludable, FString& OutModule, FString& OutWarning);

	/**
	 * Resolve the first declaration signature for a symbol. Mirrors the item-2
	 * (get_signature) resolution: body-free `signature` column fast path, else
	 * declaration-read over source_fts. OutSource is "column" | "declaration_read".
	 * Returns false when no signature is found (does NOT by itself imply
	 * non-existence — an existing class with no resolvable method signature still
	 * has a class row).
	 */
	static bool ResolveFirstSignature(FMonolithSourceDatabase* DB, const FString& Symbol,
		FString& OutSignature, FString& OutSource);

	/**
	 * Decide whether a Class::Method (or plain symbol) EXISTS in the indexed source.
	 * Per Step-0 finding: existence is class-row presence (for Class::Method, the
	 * owning class) OR a source_fts declaration hit for `Name(` — NEVER symbols-table
	 * presence of the method itself. Engine class-body methods have no symbols row.
	 */
	static bool SymbolExists(FMonolithSourceDatabase* DB, const FString& Symbol);

	// --- Phase 3 pure helpers (items 7, 9; public for unit testing) ---

	/** One lint finding (item 7). */
	struct FLintFinding
	{
		FString RuleId;
		int32 Line = 0;       // 1-based; 0 when file-level (no specific line)
		FString Message;
		FString Severity;     // "error" | "warning"
	};

	/**
	 * Run the deterministic header-lint rule table over an already-loaded set of
	 * lines (item 7). MUST work on UNINDEXED files — no DB read. The expected
	 * <MODULE>_API token is derived PRIMARILY from the file path (Source/<Module>/
	 * or Plugins/<X>/Source/<Module>/). ValidSpecifiers, when non-empty, enables
	 * the invalid-specifier cross-check (degrade gracefully: empty = rule skipped).
	 * Locals-only FRegexMatcher. A clean header yields an empty array.
	 */
	static TArray<FLintFinding> LintHeaderLines(const FString& FilePath, const TArray<FString>& Lines,
		const TSet<FString>& ValidSpecifiers);

	/**
	 * Template a UCLASS-derived .h/.cpp pair (item 9, TEXT-RETURN-ONLY — never writes).
	 * ParentHeaderInclude is the parent's canonical include (e.g. "Components/ActorComponent.h");
	 * empty when unresolved (caller should reject). bParentNeedsObjectInitializer emits the
	 * FObjectInitializer& constructor overload instead of the plain default form.
	 */
	static void GenerateClassStubText(const FString& ParentClass, const FString& ClassName, const FString& Module,
		const FString& ParentHeaderInclude, bool bParentNeedsObjectInitializer,
		FString& OutHeaderText, FString& OutCppText);

private:
	// Action handlers
	static FMonolithActionResult HandleReadSource(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindReferences(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindCallers(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindCallees(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSearchSource(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetClassHierarchy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetModuleInfo(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetSymbolContext(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleReadFile(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleTriggerReindex(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleTriggerProjectReindex(const TSharedPtr<FJsonObject>& Params);

	// Phase 1 — demand-proven lookups (LLM C++ authoring ergonomics)
	static FMonolithActionResult HandleGetIncludePath(const TSharedPtr<FJsonObject>& Params);    // item 1
	static FMonolithActionResult HandleGetSignature(const TSharedPtr<FJsonObject>& Params);      // item 2
	static FMonolithActionResult HandleCheckDeprecations(const TSharedPtr<FJsonObject>& Params); // item 3

	// Phase 2 — round-trip compression
	static FMonolithActionResult HandleVerifySymbols(const TSharedPtr<FJsonObject>& Params);     // item 4
	static FMonolithActionResult HandleFindExampleUsage(const TSharedPtr<FJsonObject>& Params);  // item 5

	// Phase 3 — pre-flight lint + stub gen
	static FMonolithActionResult HandleLintHeader(const TSharedPtr<FJsonObject>& Params);        // item 7
	static FMonolithActionResult HandleGenerateClassStub(const TSharedPtr<FJsonObject>& Params); // item 9

	// Helpers
	static FMonolithSourceDatabase* GetDB();
	static FString ShortPath(const FString& FullPath);

	/** Resolve the owning module name (+ Build.cs note) for a symbol via the source DB (files->modules join). */
	static bool ResolveOwningModule(FMonolithSourceDatabase* DB, const FString& Symbol, FString& OutModule, FString& OutBuildCsNote);

	static FString ReadFileLines(const FString& FilePath, int32 StartLine, int32 EndLine);
	static bool IsForwardDeclaration(const FString& FilePath, int32 LineStart, int32 LineEnd);
	static FString ExtractMembers(const FString& FilePath, int32 StartLine, int32 EndLine);

	static FString MakeTextResult(const FString& Text);

	// Hierarchy walk helpers
	struct FHierarchyCounter
	{
		int32 Shown = 0;
		int32 Truncated = 0;
		int32 Limit = 80;
	};
	static void WalkAncestors(FMonolithSourceDatabase* DB, int64 SymId, TArray<FString>& Lines, int32 Indent, int32 MaxDepth, FHierarchyCounter& Counter, TSet<int64>& Visited);
	static void WalkDescendants(FMonolithSourceDatabase* DB, int64 SymId, TArray<FString>& Lines, int32 Indent, int32 MaxDepth, FHierarchyCounter& Counter, TSet<int64>& Visited);
};
