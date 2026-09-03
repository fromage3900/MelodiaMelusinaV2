#include "MonolithSourceActions.h"
#include "MonolithSourceDatabase.h"
#include "MonolithSourceSubsystem.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"
#include "MonolithCursorCodec.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Editor.h"
#include "Internationalization/Regex.h"

// ============================================================================
// Registration
// ============================================================================

void FMonolithSourceActions::RegisterAll()
{
	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();

	Registry.RegisterAction(TEXT("source"), TEXT("read_source"),
		TEXT("Get the implementation source code for a class, function, or struct"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleReadSource),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Symbol name (class, function, or struct)"))
			.Optional(TEXT("include_header"), TEXT("bool"), TEXT("Include the header declaration"), TEXT("false"))
			.Optional(TEXT("max_lines"), TEXT("integer"), TEXT("Max lines to return"), TEXT("500"))
			.Optional(TEXT("members_only"), TEXT("bool"), TEXT("Only show class members, not full body"), TEXT("false"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("find_references"),
		TEXT("Find all usage sites of a symbol (calls, includes, type references)"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleFindReferences),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Symbol name to find references for"))
			.Optional(TEXT("ref_kind"), TEXT("string"), TEXT("Filter by reference kind"))
			.Optional(TEXT("limit"), TEXT("integer"), TEXT("Max results"), TEXT("50"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("find_callers"),
		TEXT("Find all functions that call the given function"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleFindCallers),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Function name"))
			.Optional(TEXT("limit"), TEXT("integer"), TEXT("Max results"), TEXT("50"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("find_callees"),
		TEXT("Find all functions called by the given function"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleFindCallees),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Function name"))
			.Optional(TEXT("limit"), TEXT("integer"), TEXT("Max results"), TEXT("50"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("search_source"),
		TEXT("Full-text search across Unreal Engine source code and shaders. Supports cursor pagination — pass `cursor` from a prior response's `next_cursor` to fetch the next page."),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleSearchSource),
		FParamSchemaBuilder()
			.Required(TEXT("query"), TEXT("string"), TEXT("Search query"))
			.Optional(TEXT("scope"), TEXT("string"), TEXT("Search scope (all, engine, shaders)"))
			.Optional(TEXT("limit"), TEXT("integer"), TEXT("Max results"), TEXT("50"))
			.Optional(TEXT("mode"), TEXT("string"), TEXT("Search mode (fts, regex, exact)"))
			.Optional(TEXT("module"), TEXT("string"), TEXT("Filter to a specific module"))
			.Optional(TEXT("path_filter"), TEXT("string"), TEXT("Filter by file path pattern"))
			.Optional(TEXT("symbol_kind"), TEXT("string"), TEXT("Filter by symbol kind (class, function, enum, etc.)"))
			// Survivor E (plan §3.E): opaque base64+JSON cursor from a prior
			// response's `next_cursor`. Omit on the first call.
			.Optional(TEXT("cursor"), TEXT("string"), TEXT("Opaque pagination cursor from a prior next_cursor (Survivor E)"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("get_class_hierarchy"),
		TEXT("Show the inheritance tree for a class"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleGetClassHierarchy),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Class name"))
			.Optional(TEXT("direction"), TEXT("string"), TEXT("Direction: up (parents) or down (children)"), TEXT("both"))
			.Optional(TEXT("depth"), TEXT("integer"), TEXT("Max hierarchy depth"), TEXT("5"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("get_module_info"),
		TEXT("Get module statistics: file count, symbol counts by kind, and key classes"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleGetModuleInfo),
		FParamSchemaBuilder()
			.Required(TEXT("module_name"), TEXT("string"), TEXT("Module name"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("get_symbol_context"),
		TEXT("Get a symbol definition with surrounding context lines"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleGetSymbolContext),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Symbol name"))
			.Optional(TEXT("context_lines"), TEXT("integer"), TEXT("Lines of context around the definition"), TEXT("10"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("read_file"),
		TEXT("Read source lines from a file by path"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleReadFile),
		FParamSchemaBuilder()
			.RequiredDiskPath(TEXT("file_path"), TEXT("Source file path"))
			.Optional(TEXT("start_line"), TEXT("integer"), TEXT("First line to read"), TEXT("1"))
			.Optional(TEXT("end_line"), TEXT("integer"), TEXT("Last line to read"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("trigger_reindex"),
		TEXT("Trigger C++ indexer to rebuild the engine source DB (full clean build: engine + shaders + project)"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleTriggerReindex),
		MakeShared<FJsonObject>());

	Registry.RegisterAction(TEXT("source"), TEXT("trigger_project_reindex"),
		TEXT("Trigger incremental project-only C++ source indexing (loads existing engine symbols, indexes project Source/ and Plugins/)"),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleTriggerProjectReindex),
		MakeShared<FJsonObject>());

	// --- Phase 1: LLM C++ authoring ergonomics (items 1-3) ---

	Registry.RegisterAction(TEXT("source"), TEXT("get_include_path"),
		TEXT("Get the canonical #include path for a symbol (resolves via the owning class header). Public/Classes/Internal headers are includable cross-module; Private headers return includable:false with a same-module note."),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleGetIncludePath),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Symbol name (class, struct, or Class::Method)"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("get_signature"),
		TEXT("Get the declaration signature(s) for a symbol or Class::Method. Reads the declaration line(s) from source (engine class-body methods are not indexed as symbols); strips inline bodies and macro line-continuations. Overloads returned as separate entries."),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleGetSignature),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Symbol name or Class::Method"))
			.Optional(TEXT("limit"), TEXT("integer"), TEXT("Max overloads to return"), TEXT("10"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("check_deprecations"),
		TEXT("Batch-check whether symbols are UE_DEPRECATED. Returns per-symbol {deprecated, version, message, kind}. If the deprecation index is empty (schema v2 landed but no reindex yet), returns index_state:\"empty\" with a hint to run source.trigger_reindex."),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleCheckDeprecations),
		FParamSchemaBuilder()
			.Required(TEXT("symbols"), TEXT("array"), TEXT("Array of symbol names to check"))
			.Build());

	// Survivor A (plan §3.A) — annotate the `source_query` namespace dispatcher
	// as read-only + idempotent. The `trigger_reindex` / `trigger_project_reindex`
	// actions are conservatively non-destructive (they kick a background sweep
	// that yields identical results when re-run); every other source action is
	// pure read. Annotating at the DISPATCHER level (not per-action) per plan
	// §3.A — the dispatcher tool is what `tools/list` advertises.
	FMonolithDispatcherAnnotations SourceAnnotations;
	SourceAnnotations.bReadOnlyHint = true;
	SourceAnnotations.bDestructiveHint = false;
	SourceAnnotations.bIdempotentHint = true;
	SourceAnnotations.Title = TEXT("Source-index query");
	Registry.SetDispatcherAnnotations(TEXT("source"), SourceAnnotations);

	// Phase 1 actions are pure reads — mark each read-only + idempotent + non-destructive.
	Registry.SetActionAnnotations(TEXT("source"), TEXT("get_include_path"),  /*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true, TEXT("Get include path"));
	Registry.SetActionAnnotations(TEXT("source"), TEXT("get_signature"),     /*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true, TEXT("Get signature"));
	Registry.SetActionAnnotations(TEXT("source"), TEXT("check_deprecations"),/*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true, TEXT("Check deprecations"));

	// --- Phase 2: round-trip compression (items 4-5) ---

	Registry.RegisterAction(TEXT("source"), TEXT("verify_symbols"),
		TEXT("Batch pre-flight verdict for a list of symbols. Per symbol composes include path, declaration signature, deprecation status, and existence into one record. `exists` for a Class::Method is decided by the owning class row + a source-line declaration hit (engine class-body methods are not indexed as symbols), NOT by symbols-table presence; a missing symbol reports exists:false with no error."),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleVerifySymbols),
		FParamSchemaBuilder()
			.Required(TEXT("symbols"), TEXT("array"), TEXT("Array of symbol names or Class::Method strings to verify"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("find_example_usage"),
		TEXT("Find real call-site examples of a symbol via full-text search over indexed source lines (pattern `SymbolName(`). Returns ranked snippets with ~3 lines of context. `prefer`: \"engine\" (default — engine Runtime first, then other engine, then project) or \"project\" (flips project ahead). Supports cursor pagination — pass `cursor` from a prior response's `next_cursor`."),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleFindExampleUsage),
		FParamSchemaBuilder()
			.Required(TEXT("symbol"), TEXT("string"), TEXT("Symbol name or Class::Method to find usage examples for"))
			.Optional(TEXT("prefer"), TEXT("string"), TEXT("Ranking preference: engine (default) or project"), TEXT("engine"))
			.Optional(TEXT("limit"), TEXT("integer"), TEXT("Max examples per page"), TEXT("10"))
			.Optional(TEXT("cursor"), TEXT("string"), TEXT("Opaque pagination cursor from a prior next_cursor"))
			.Build());

	Registry.SetActionAnnotations(TEXT("source"), TEXT("verify_symbols"),     /*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true, TEXT("Verify symbols"));
	Registry.SetActionAnnotations(TEXT("source"), TEXT("find_example_usage"), /*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true, TEXT("Find example usage"));

	// --- Phase 3: pre-flight lint + stub gen (items 7, 9) ---

	Registry.RegisterAction(TEXT("source"), TEXT("lint_header"),
		TEXT("Regex-level UHT-gotcha lint of a single header file. Works on UNINDEXED files (a header you just wrote). Deterministic rule table: GENERATED_BODY presence/position, *.generated.h last-include, UCLASS/class-name match, missing <MODULE>_API, UPROPERTY/UFUNCTION in a non-reflected type, invalid specifier token. Returns structured findings {rule_id, line, message, severity}; a clean header returns zero findings."),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleLintHeader),
		FParamSchemaBuilder()
			.RequiredDiskPath(TEXT("file_path"), TEXT("Header file path to lint"))
			.Build());

	Registry.RegisterAction(TEXT("source"), TEXT("generate_class_stub"),
		TEXT("Generate a UCLASS-derived .h/.cpp stub pair as TEXT (never writes to disk). Resolves the parent header + owning module via the source DB, emits <MODULE>_API, parent header include FIRST, \"<Class>.generated.h\" LAST, GENERATED_BODY(), and a plain default constructor (the FObjectInitializer& overload only when the parent requires it). UCLASS-derived parents only; other parents are rejected cleanly."),
		FMonolithActionHandler::CreateStatic(&FMonolithSourceActions::HandleGenerateClassStub),
		FParamSchemaBuilder()
			.Required(TEXT("parent"), TEXT("string"), TEXT("Parent class name (must be UCLASS-derived, e.g. AActor, UActorComponent)"))
			.Required(TEXT("class_name"), TEXT("string"), TEXT("New class name (with U/A prefix, e.g. UMyComp, AMyActor)"))
			.Required(TEXT("module"), TEXT("string"), TEXT("Owning module name (used to derive the <MODULE>_API export macro)"))
			.Build());

	Registry.SetActionAnnotations(TEXT("source"), TEXT("lint_header"),          /*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true, TEXT("Lint header"));
	Registry.SetActionAnnotations(TEXT("source"), TEXT("generate_class_stub"),  /*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true, TEXT("Generate class stub"));
}

// ============================================================================
// Helpers
// ============================================================================

FMonolithSourceDatabase* FMonolithSourceActions::GetDB()
{
	if (!GEditor) return nullptr;
	UMonolithSourceSubsystem* Subsystem = Cast<UMonolithSourceSubsystem>(GEditor->GetEditorSubsystemBase(UMonolithSourceSubsystem::StaticClass()));
	if (!Subsystem) return nullptr;
	return Subsystem->GetDatabase();
}

FString FMonolithSourceActions::ShortPath(const FString& FullPath)
{
	// Shorten to Engine/... relative path
	FString EngineDir = FPaths::EngineDir();
	FString ParentDir = FPaths::GetPath(EngineDir); // Parent of Engine/
	if (!ParentDir.IsEmpty() && FullPath.StartsWith(ParentDir))
	{
		FString Relative = FullPath.Mid(ParentDir.Len());
		Relative.ReplaceInline(TEXT("\\"), TEXT("/"));
		if (Relative.StartsWith(TEXT("/")))
		{
			Relative = Relative.Mid(1);
		}
		return Relative;
	}
	return FullPath;
}

FString FMonolithSourceActions::DeriveIncludePath(const FString& IndexedFilePath, bool& bOutIncludable, FString& OutWarning)
{
	bOutIncludable = true;
	OutWarning.Empty();

	// Normalize to forward slashes for prefix scanning + canonical include form.
	FString Path = IndexedFilePath;
	Path.ReplaceInline(TEXT("\\"), TEXT("/"));

	// Derive the owning module name from the .../Source/<Module>/ segment, used
	// only for the Private-header warning text.
	FString ModuleName;
	{
		int32 SrcIdx = Path.Find(TEXT("/Source/"), ESearchCase::IgnoreCase, ESearchDir::FromEnd);
		if (SrcIdx != INDEX_NONE)
		{
			FString AfterSrc = Path.Mid(SrcIdx + 8); // skip "/Source/"
			int32 Slash = INDEX_NONE;
			if (AfterSrc.FindChar(TEXT('/'), Slash))
			{
				ModuleName = AfterSrc.Left(Slash);
			}
		}
	}

	// Find a recognised header-root prefix and return the path relative to it.
	// Order matters only in that each is checked independently; the LAST occurrence
	// is used so nested module trees resolve to the innermost root.
	static const TCHAR* IncludableRoots[] = { TEXT("/Public/"), TEXT("/Classes/"), TEXT("/Internal/") };
	for (const TCHAR* Root : IncludableRoots)
	{
		int32 Idx = Path.Find(Root, ESearchCase::IgnoreCase, ESearchDir::FromEnd);
		if (Idx != INDEX_NONE)
		{
			FString Rel = Path.Mid(Idx + FCString::Strlen(Root));
			bOutIncludable = true;
			return Rel;
		}
	}

	// Private/ — NOT includable from another module. Return the same-module
	// relative form (after Private/) and flag it.
	{
		int32 Idx = Path.Find(TEXT("/Private/"), ESearchCase::IgnoreCase, ESearchDir::FromEnd);
		if (Idx != INDEX_NONE)
		{
			FString Rel = Path.Mid(Idx + 9); // skip "/Private/"
			bOutIncludable = false;
			OutWarning = FString::Printf(
				TEXT("Private header — not includable outside %s; same-module include shown"),
				ModuleName.IsEmpty() ? TEXT("its module") : *ModuleName);
			return Rel;
		}
	}

	// No recognised prefix (e.g. engine headers outside the Public/Private layout)
	// -> basename fallback.
	bOutIncludable = true;
	return FPaths::GetCleanFilename(Path);
}

bool FMonolithSourceActions::ResolveOwningModule(FMonolithSourceDatabase* DB, const FString& Symbol, FString& OutModule, FString& OutBuildCsNote)
{
	OutModule.Empty();
	OutBuildCsNote.Empty();
	if (!DB) return false;

	// Resolve the symbol's owning file. For a Class::Method input the method
	// itself need not be a symbol row — resolve via the owning class.
	FString LookupName = Symbol;
	int32 ScopeIdx = Symbol.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
	if (ScopeIdx != INDEX_NONE)
	{
		LookupName = Symbol.Left(ScopeIdx); // the class/struct
	}

	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(LookupName);
	if (Symbols.Num() == 0) Symbols = DB->SearchSymbolsFTS(LookupName, 5);
	if (Symbols.Num() == 0) return false;

	FString BuildCsPath;
	if (!DB->GetFileModuleInfo(Symbols[0].FileId, OutModule, BuildCsPath))
	{
		return false;
	}

	if (!BuildCsPath.IsEmpty())
	{
		OutBuildCsNote = FString::Printf(TEXT("Module '%s' — add to your Build.cs deps (%s)"),
			*OutModule, *FPaths::GetCleanFilename(BuildCsPath));
	}
	else
	{
		OutBuildCsNote = FString::Printf(TEXT("Module '%s' — add to your Build.cs deps"), *OutModule);
	}
	return true;
}

// --- Phase 2 shared composition helpers (item 4 calls these, NOT the JSON handlers) ---

bool FMonolithSourceActions::ResolveIncludeForSymbol(FMonolithSourceDatabase* DB, const FString& Symbol,
	FString& OutInclude, bool& OutIncludable, FString& OutModule, FString& OutWarning)
{
	OutInclude.Empty();
	OutIncludable = true;
	OutModule.Empty();
	OutWarning.Empty();
	if (!DB) return false;

	// For a Class::Method input resolve via the OWNING CLASS row.
	FString LookupName = Symbol;
	const int32 ScopeIdx = Symbol.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
	if (ScopeIdx != INDEX_NONE)
	{
		LookupName = Symbol.Left(ScopeIdx);
	}

	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(LookupName);
	if (Symbols.Num() == 0) Symbols = DB->SearchSymbolsFTS(LookupName, 5);
	if (Symbols.Num() == 0) return false;

	// Prefer a header among same-name rows (decl + def).
	const FMonolithSourceSymbol* Chosen = &Symbols[0];
	for (const FMonolithSourceSymbol& S : Symbols)
	{
		if (DB->GetFilePath(S.FileId).EndsWith(TEXT(".h"))) { Chosen = &S; break; }
	}

	const FString FilePath = DB->GetFilePath(Chosen->FileId);
	OutInclude = DeriveIncludePath(FilePath, OutIncludable, OutWarning);

	FString BuildCsPath;
	DB->GetFileModuleInfo(Chosen->FileId, OutModule, BuildCsPath);
	return true;
}

bool FMonolithSourceActions::ResolveFirstSignature(FMonolithSourceDatabase* DB, const FString& Symbol,
	FString& OutSignature, FString& OutSource)
{
	OutSignature.Empty();
	OutSource.Empty();
	if (!DB) return false;

	// Method name = trailing identifier.
	FString MethodName = Symbol;
	const int32 ScopeIdx = Symbol.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
	if (ScopeIdx != INDEX_NONE)
	{
		MethodName = Symbol.Mid(ScopeIdx + 2);
	}

	// Fast path: body-free signature column.
	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(MethodName, TEXT("function"));
	for (const FMonolithSourceSymbol& S : Symbols)
	{
		if (S.Signature.IsEmpty()) continue;
		if (S.Signature.Contains(TEXT("{")) || S.Signature.Contains(TEXT("\\"))) continue;
		OutSignature = S.Signature.TrimStartAndEnd();
		OutSource = TEXT("column");
		return true;
	}

	// Primary: declaration-read over source_fts.
	const FString NeedlePattern = MethodName + TEXT("(");
	TArray<FMonolithSourceChunk> Chunks = DB->SearchSourceFTS(Symbol, TEXT("all"), 50);
	for (const FMonolithSourceChunk& Chunk : Chunks)
	{
		const FString FilePath = DB->GetFilePath(Chunk.FileId);
		TArray<FString> FileLines;
		if (!FFileHelper::LoadFileToStringArray(FileLines, *FilePath)) continue;

		const int32 WinStart = FMath::Max(0, Chunk.LineNumber - 1);
		const int32 WinEnd = FMath::Min(FileLines.Num(), WinStart + 10);
		for (int32 i = WinStart; i < WinEnd; ++i)
		{
			const FString& L = FileLines[i];
			const int32 DeclIdx = L.Find(NeedlePattern, ESearchCase::CaseSensitive);
			if (DeclIdx == INDEX_NONE) continue;
			if (DeclIdx > 0)
			{
				const TCHAR Prev = L[DeclIdx - 1];
				if (FChar::IsAlnum(Prev) || Prev == TEXT('_')) continue;
			}
			const FString Sig = CompactDeclaration(FileLines, i);
			if (Sig.IsEmpty() || !Sig.Contains(NeedlePattern)) continue;
			OutSignature = Sig;
			OutSource = TEXT("declaration_read");
			return true;
		}
	}
	return false;
}

bool FMonolithSourceActions::SymbolExists(FMonolithSourceDatabase* DB, const FString& Symbol)
{
	if (!DB) return false;

	// Class-row presence: for Class::Method, the OWNING class; for a plain symbol,
	// the symbol itself. NEVER the method's own symbols-table row (Step-0: engine
	// class-body methods have no row).
	FString LookupName = Symbol;
	const int32 ScopeIdx = Symbol.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
	if (ScopeIdx != INDEX_NONE)
	{
		LookupName = Symbol.Left(ScopeIdx);
	}
	if (DB->GetSymbolsByName(LookupName).Num() > 0) return true;
	if (DB->SearchSymbolsFTS(LookupName, 1).Num() > 0) return true;

	// Source-line FTS declaration hit for `Name(` — covers free functions / methods
	// the class-row lookup missed.
	FString MethodName = Symbol;
	if (ScopeIdx != INDEX_NONE)
	{
		MethodName = Symbol.Mid(ScopeIdx + 2);
	}
	const FString NeedlePattern = MethodName + TEXT("(");
	TArray<FMonolithSourceChunk> Chunks = DB->SearchSourceFTS(Symbol, TEXT("all"), 25);
	for (const FMonolithSourceChunk& Chunk : Chunks)
	{
		const FString FilePath = DB->GetFilePath(Chunk.FileId);
		TArray<FString> FileLines;
		if (!FFileHelper::LoadFileToStringArray(FileLines, *FilePath)) continue;
		const int32 WinStart = FMath::Max(0, Chunk.LineNumber - 1);
		const int32 WinEnd = FMath::Min(FileLines.Num(), WinStart + 10);
		for (int32 i = WinStart; i < WinEnd; ++i)
		{
			const FString& L = FileLines[i];
			const int32 DeclIdx = L.Find(NeedlePattern, ESearchCase::CaseSensitive);
			if (DeclIdx == INDEX_NONE) continue;
			if (DeclIdx > 0)
			{
				const TCHAR Prev = L[DeclIdx - 1];
				if (FChar::IsAlnum(Prev) || Prev == TEXT('_')) continue;
			}
			return true;
		}
	}
	return false;
}

FString FMonolithSourceActions::ReadFileLines(const FString& FilePath, int32 StartLine, int32 EndLine)
{
	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *FilePath))
	{
		return FString::Printf(TEXT("[File not found: %s]"), *FilePath);
	}

	StartLine = FMath::Max(1, StartLine);
	EndLine = FMath::Min(Lines.Num(), EndLine);

	FString Result;
	for (int32 i = StartLine; i <= EndLine; ++i)
	{
		Result += FString::Printf(TEXT("%5d | %s\n"), i, *Lines[i - 1]);
	}
	return Result;
}

bool FMonolithSourceActions::IsForwardDeclaration(const FString& FilePath, int32 LineStart, int32 LineEnd)
{
	if (LineEnd - LineStart > 1)
	{
		return false;
	}

	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *FilePath))
	{
		return false;
	}

	if (LineStart <= Lines.Num())
	{
		const FString& Line = Lines[LineStart - 1];
		FRegexPattern Pattern(TEXT("^\\s*(class|struct|enum)\\s+\\w[\\w:]*\\s*;"));
		FRegexMatcher Matcher(Pattern, Line);
		return Matcher.FindNext();
	}
	return false;
}

FString FMonolithSourceActions::ExtractMembers(const FString& FilePath, int32 StartLine, int32 EndLine)
{
	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *FilePath))
	{
		return FString::Printf(TEXT("[Error reading %s]"), *FilePath);
	}

	StartLine = FMath::Max(1, StartLine);
	EndLine = FMath::Min(Lines.Num(), EndLine);

	FString Result;
	int32 BraceDepth = 0;
	bool bInBlockComment = false;
	int32 SignatureLineIdx = -1; // Track pending function signature for Allman-style bodies

	for (int32 i = StartLine - 1; i < EndLine; ++i)
	{
		const FString& Line = Lines[i];
		FString Stripped = Line.TrimStartAndEnd();

		// --- Count braces, respecting comments and string/char literals ---
		int32 PrevDepth = BraceDepth;
		for (int32 c = 0; c < Stripped.Len(); ++c)
		{
			TCHAR Ch = Stripped[c];
			TCHAR Next = (c + 1 < Stripped.Len()) ? Stripped[c + 1] : 0;

			if (bInBlockComment)
			{
				if (Ch == TEXT('*') && Next == TEXT('/'))
				{
					bInBlockComment = false;
					c++; // skip '/'
				}
				continue;
			}

			// Line comment — skip rest of line
			if (Ch == TEXT('/') && Next == TEXT('/')) break;

			// Block comment start
			if (Ch == TEXT('/') && Next == TEXT('*'))
			{
				bInBlockComment = true;
				c++; // skip '*'
				continue;
			}

			// String literal — skip to closing quote
			if (Ch == TEXT('"'))
			{
				for (++c; c < Stripped.Len(); ++c)
				{
					if (Stripped[c] == TEXT('\\')) { c++; }
					else if (Stripped[c] == TEXT('"')) break;
				}
				continue;
			}

			// Char literal — skip to closing quote
			if (Ch == TEXT('\''))
			{
				for (++c; c < Stripped.Len(); ++c)
				{
					if (Stripped[c] == TEXT('\\')) { c++; }
					else if (Stripped[c] == TEXT('\'')) break;
				}
				continue;
			}

			if (Ch == TEXT('{')) BraceDepth++;
			else if (Ch == TEXT('}')) BraceDepth--;
		}

		// --- Depth >= 2 at start OR transitioning 1→2+: inside function body ---
		if (PrevDepth >= 2)
		{
			// Still inside a function body — skip
			continue;
		}

		if (PrevDepth <= 1 && BraceDepth >= 2)
		{
			// Transitioning into a function body on this line
			if (SignatureLineIdx >= 0)
			{
				// Allman style: signature was on a previous line, emit with annotation
				Result += FString::Printf(TEXT("%5d | %s  // [body omitted]\n"), SignatureLineIdx + 1, *Lines[SignatureLineIdx]);
				SignatureLineIdx = -1;
			}
			else if (Stripped != TEXT("{"))
			{
				// K&R style: brace on the same line as the signature
				FString SigPart = Stripped;
				int32 BraceIdx;
				if (SigPart.FindChar(TEXT('{'), BraceIdx))
				{
					SigPart = SigPart.Left(BraceIdx).TrimEnd();
				}
				if (!SigPart.IsEmpty())
				{
					Result += FString::Printf(TEXT("%5d | %s  // [body omitted]\n"), i + 1, *SigPart);
				}
			}
			continue;
		}

		// --- Depth 0-1: class-level declarations ---

		// Keep class-level braces (class opening/closing)
		if (Stripped == TEXT("{") || Stripped == TEXT("}"))
		{
			if (SignatureLineIdx >= 0)
			{
				Result += FString::Printf(TEXT("%5d | %s\n"), SignatureLineIdx + 1, *Lines[SignatureLineIdx]);
				SignatureLineIdx = -1;
			}
			Result += FString::Printf(TEXT("%5d | %s\n"), i + 1, *Line);
			continue;
		}

		bool bKeep = Stripped.StartsWith(TEXT("public:")) || Stripped.StartsWith(TEXT("protected:")) || Stripped.StartsWith(TEXT("private:"))
			|| Stripped.StartsWith(TEXT("GENERATED")) || Stripped.StartsWith(TEXT("UFUNCTION")) || Stripped.StartsWith(TEXT("UPROPERTY"))
			|| Stripped.StartsWith(TEXT("UENUM")) || Stripped.StartsWith(TEXT("USTRUCT"))
			|| Stripped.StartsWith(TEXT("//")) || Stripped.StartsWith(TEXT("/**")) || Stripped.StartsWith(TEXT("*")) || Stripped.StartsWith(TEXT("*/"))
			|| Stripped.IsEmpty()
			|| Stripped.Contains(TEXT(";"));

		if (bKeep)
		{
			if (SignatureLineIdx >= 0)
			{
				Result += FString::Printf(TEXT("%5d | %s\n"), SignatureLineIdx + 1, *Lines[SignatureLineIdx]);
				SignatureLineIdx = -1;
			}
			Result += FString::Printf(TEXT("%5d | %s\n"), i + 1, *Line);
		}
		else
		{
			// Unrecognized line at class level — could be a function signature (Allman style)
			// Remember it; if next line opens a body (depth→2), emit with [body omitted]
			if (SignatureLineIdx >= 0)
			{
				// Previous pending signature wasn't followed by a body — emit it normally
				Result += FString::Printf(TEXT("%5d | %s\n"), SignatureLineIdx + 1, *Lines[SignatureLineIdx]);
			}
			SignatureLineIdx = i;
		}
	}

	// Flush any remaining pending signature
	if (SignatureLineIdx >= 0)
	{
		Result += FString::Printf(TEXT("%5d | %s\n"), SignatureLineIdx + 1, *Lines[SignatureLineIdx]);
	}

	return Result;
}

FString FMonolithSourceActions::MakeTextResult(const FString& Text)
{
	// Return text as a JSON result with a "text" field
	// (But the registry expects FMonolithActionResult with a JSON object)
	// We'll put it in content[0].text per MCP tool result convention
	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), Text);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return Text; // Unused, but we return the text
}

// ============================================================================
// Tool 1: read_source
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleReadSource(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available. Run source.trigger_reindex first."));
	}

	FString Symbol = Params->GetStringField(TEXT("symbol"));
	bool bIncludeHeader = true;
	if (Params->HasField(TEXT("include_header")))
	{
		bIncludeHeader = Params->GetBoolField(TEXT("include_header"));
	}
	int32 MaxLines = 0;
	if (Params->HasField(TEXT("max_lines")))
	{
		MaxLines = static_cast<int32>(Params->GetNumberField(TEXT("max_lines")));
	}
	bool bMembersOnly = false;
	if (Params->HasField(TEXT("members_only")))
	{
		bMembersOnly = Params->GetBoolField(TEXT("members_only"));
	}

	// Look up by exact name first, then FTS fallback
	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(Symbol);
	if (Symbols.Num() == 0)
	{
		Symbols = DB->SearchSymbolsFTS(Symbol, 5);
	}
	if (Symbols.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No symbol found matching '%s'."), *Symbol));
	}

	// Filter out forward declarations when a real definition exists
	bool bHasDefinition = false;
	for (const auto& Sym : Symbols)
	{
		if (Sym.LineEnd - Sym.LineStart > 1) { bHasDefinition = true; break; }
	}

	if (bHasDefinition)
	{
		TArray<FMonolithSourceSymbol> Filtered;
		for (const auto& Sym : Symbols)
		{
			FString FilePath = DB->GetFilePath(Sym.FileId);
			if (!IsForwardDeclaration(FilePath, Sym.LineStart, Sym.LineEnd))
			{
				Filtered.Add(Sym);
			}
		}
		if (Filtered.Num() > 0) Symbols = Filtered;
	}

	TArray<FString> Parts;
	TSet<FString> SeenFiles;

	for (const auto& Sym : Symbols)
	{
		FString Key = FString::Printf(TEXT("%lld_%d_%d"), Sym.FileId, Sym.LineStart, Sym.LineEnd);
		if (SeenFiles.Contains(Key)) continue;
		SeenFiles.Add(Key);

		FString FilePath = DB->GetFilePath(Sym.FileId);

		if (!bIncludeHeader && FilePath.EndsWith(TEXT(".h")))
		{
			continue;
		}

		FString Header = FString::Printf(TEXT("--- %s (lines %d-%d) ---"), *ShortPath(FilePath), Sym.LineStart, Sym.LineEnd);
		FString Doc;
		if (!Sym.Docstring.IsEmpty())
		{
			Doc = FString::Printf(TEXT("// %s\n"), *Sym.Docstring);
		}

		FString Source;
		if (bMembersOnly && (Sym.Kind == TEXT("class") || Sym.Kind == TEXT("struct")))
		{
			Source = ExtractMembers(FilePath, Sym.LineStart, Sym.LineEnd);
		}
		else
		{
			Source = ReadFileLines(FilePath, Sym.LineStart, Sym.LineEnd);
		}
		Parts.Add(Header + TEXT("\n") + Doc + Source);
	}

	FString ResultText = Parts.Num() > 0
		? FString::Join(Parts, TEXT("\n"))
		: FString::Printf(TEXT("Found symbol '%s' but could not read source files."), *Symbol);

	if (MaxLines > 0)
	{
		TArray<FString> ResultLines;
		ResultText.ParseIntoArrayLines(ResultLines);
		if (ResultLines.Num() > MaxLines)
		{
			int32 Remaining = ResultLines.Num() - MaxLines;
			ResultLines.SetNum(MaxLines);
			ResultText = FString::Join(ResultLines, TEXT("\n"));
			ResultText += FString::Printf(TEXT("\n[...truncated, %d more lines]"), Remaining);
		}
	}

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Tool 2: find_references
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleFindReferences(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available."));
	}

	FString Symbol = Params->GetStringField(TEXT("symbol"));
	FString RefKind = Params->HasField(TEXT("ref_kind")) ? Params->GetStringField(TEXT("ref_kind")) : TEXT("");
	int32 Limit = Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;

	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(Symbol);
	if (Symbols.Num() == 0) Symbols = DB->SearchSymbolsFTS(Symbol, 5);
	if (Symbols.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No symbol found matching '%s'."), *Symbol));
	}

	TArray<FString> Lines;
	for (const auto& Sym : Symbols)
	{
		TArray<FMonolithSourceReference> Refs = DB->GetReferencesTo(Sym.Id, RefKind, Limit);
		for (const auto& Ref : Refs)
		{
			Lines.Add(FString::Printf(TEXT("[%s] %s:%d (from %s)"),
				*Ref.RefKind, *ShortPath(Ref.Path), Ref.Line, *Ref.FromName));
		}
	}

	FString ResultText = Lines.Num() > 0
		? FString::Join(Lines, TEXT("\n"))
		: FString::Printf(TEXT("No references found for '%s'."), *Symbol);

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Tool 3: find_callers
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleFindCallers(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available."));
	}

	FString Function = Params->GetStringField(TEXT("symbol"));
	int32 Limit = Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;

	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(Function, TEXT("function"));
	if (Symbols.Num() == 0)
	{
		TArray<FMonolithSourceSymbol> AllSyms = DB->SearchSymbolsFTS(Function, 5);
		for (const auto& S : AllSyms)
		{
			if (S.Kind == TEXT("function")) Symbols.Add(S);
		}
	}
	if (Symbols.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No function found matching '%s'."), *Function));
	}

	TArray<FString> Lines;
	for (const auto& Sym : Symbols)
	{
		TArray<FMonolithSourceReference> Refs = DB->GetReferencesTo(Sym.Id, TEXT("call"), Limit);
		for (const auto& Ref : Refs)
		{
			Lines.Add(FString::Printf(TEXT("%s \u2014 %s:%d"), *Ref.FromName, *ShortPath(Ref.Path), Ref.Line));
		}
	}

	FString ResultText;
	if (Lines.Num() == 0)
	{
		ResultText = FString::Printf(
			TEXT("No direct C++ callers found for '%s'. This function may be called via delegates, Blueprints, input bindings, or reflection."),
			*Function);
	}
	else
	{
		ResultText = FString::Join(Lines, TEXT("\n"));
	}

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Tool 4: find_callees
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleFindCallees(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available."));
	}

	FString Function = Params->GetStringField(TEXT("symbol"));
	int32 Limit = Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;

	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(Function, TEXT("function"));
	if (Symbols.Num() == 0)
	{
		TArray<FMonolithSourceSymbol> AllSyms = DB->SearchSymbolsFTS(Function, 5);
		for (const auto& S : AllSyms)
		{
			if (S.Kind == TEXT("function")) Symbols.Add(S);
		}
	}
	if (Symbols.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No function found matching '%s'."), *Function));
	}

	TArray<FString> Lines;
	for (const auto& Sym : Symbols)
	{
		TArray<FMonolithSourceReference> Refs = DB->GetReferencesFrom(Sym.Id, TEXT("call"), Limit);
		for (const auto& Ref : Refs)
		{
			Lines.Add(FString::Printf(TEXT("%s \u2014 %s:%d"), *Ref.ToName, *ShortPath(Ref.Path), Ref.Line));
		}
	}

	FString ResultText = Lines.Num() > 0
		? FString::Join(Lines, TEXT("\n"))
		: FString::Printf(TEXT("No callees found for '%s'."), *Function);

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Tool 5: search_source
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleSearchSource(const TSharedPtr<FJsonObject>& Params)
{
	// Survivor E (plan §3.E) — cursor pagination via rerun-slice.
	//
	// FTS5 rank instability rules out keyset cursors (see plan §8). Instead
	// we rerun the full top-N query at `N = (PageIndex + 1) * Limit`, then
	// slice [PageIndex * Limit, (PageIndex + 1) * Limit). Hard cap of 1000
	// rows total — once the slice end exceeds 1000, no more pages.
	//
	// v1 design note: we use ONE symbol page + ONE source page. The source
	// branch issues an interleaved query across N scopes (header/source/inline
	// OR shader/shader_header OR "all"). Per-scope page tracking would let
	// each scope walk independently, but the plan §3.E body explicitly
	// chooses the simpler single-pair scheme for v1. The interleaved
	// de-dup at the slice site continues to use the existing TSet<FString>
	// keyed on (FileId, LineNumber).

	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available."));
	}

	const FString Query = Params->GetStringField(TEXT("query"));
	const FString Scope = Params->HasField(TEXT("scope")) ? Params->GetStringField(TEXT("scope")) : TEXT("all");
	const int32 RequestedLimit = Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 20;
	const FString Mode = Params->HasField(TEXT("mode")) ? Params->GetStringField(TEXT("mode")) : TEXT("fts");
	const FString Module = Params->HasField(TEXT("module")) ? Params->GetStringField(TEXT("module")) : TEXT("");
	const FString PathFilter = Params->HasField(TEXT("path_filter")) ? Params->GetStringField(TEXT("path_filter")) : TEXT("");
	const FString SymbolKind = Params->HasField(TEXT("symbol_kind")) ? Params->GetStringField(TEXT("symbol_kind")) : TEXT("");
	const FString CursorIn = Params->HasField(TEXT("cursor")) ? Params->GetStringField(TEXT("cursor")) : TEXT("");

	// Hard cap (plan §3.E): never page past row 1000. Cumulative cap.
	// When caller asks for `limit > HARD_CAP_ROWS` (e.g. limit=2000), the
	// FTS query is issued with N=1000 and the returned page is implicitly
	// capped — N is clamped to HARD_CAP_ROWS below.
	constexpr int32 HARD_CAP_ROWS = 1000;

	// Minimum-1 guard. Caller may legitimately ask for limit > HARD_CAP_ROWS;
	// the page slice will fall out short. No upper clamp on `Limit` itself
	// (the row count is bounded by N clamp + slice arithmetic).
	const int32 Limit = FMath::Max(1, RequestedLimit);

	const uint32 CurrentHash = MonolithCursorCodec::ComputeQueryHash(
		Query, Scope, Mode, Module, PathFilter, SymbolKind);

	// Decode cursor (if any). Mismatch / corruption → clean INVALID_CURSOR.
	int32 SymbolPage = 0;
	int32 SourcePage = 0;
	int32 CachedTotalEstimate = -1;
	bool bHasCursor = false;

	if (!CursorIn.IsEmpty())
	{
		MonolithCursorCodec::FCursorState State;
		if (!MonolithCursorCodec::Decode(CursorIn, State))
		{
			TSharedPtr<FJsonObject> ErrData = MakeShared<FJsonObject>();
			ErrData->SetStringField(TEXT("error_code"), TEXT("INVALID_CURSOR"));
			return FMonolithActionResult::Error(
				TEXT("Cursor decode failed; restart pagination without `cursor`."),
				FMonolithJsonUtils::ErrInvalidParams
			).WithErrorData(ErrData);
		}
		if (State.QueryHash != CurrentHash)
		{
			TSharedPtr<FJsonObject> ErrData = MakeShared<FJsonObject>();
			ErrData->SetStringField(TEXT("error_code"), TEXT("INVALID_CURSOR"));
			return FMonolithActionResult::Error(
				TEXT("Cursor query mismatch; restart pagination without `cursor`."),
				FMonolithJsonUtils::ErrInvalidParams
			).WithErrorData(ErrData);
		}
		SymbolPage = State.SymbolPage;
		SourcePage = State.SourcePage;
		CachedTotalEstimate = State.CachedTotalEstimate;
		bHasCursor = true;
	}

	const bool bIsPageZero = !bHasCursor;

	// PageIndex shared by both symbol and source rerun (v1 single-pair design).
	const int32 PageIndex = bHasCursor ? FMath::Max(SymbolPage, SourcePage) : 0;

	// N = how many rows we ask the FTS query for, then slice down to the page.
	// Clamp at HARD_CAP_ROWS — once we cross the cap, the next page would be empty.
	const int32 N = FMath::Min((PageIndex + 1) * Limit, HARD_CAP_ROWS);
	const int32 SliceStart = PageIndex * Limit;
	const int32 SliceEnd = FMath::Min(SliceStart + Limit, HARD_CAP_ROWS);

	// Sentinel: if SliceStart is already at/past the cap, return an empty
	// page (terminal). This is the documented overflow path.
	const bool bPastCap = SliceStart >= HARD_CAP_ROWS;

	TArray<FString> Parts;

	// ---------- Symbol FTS rerun-slice ----------
	TArray<FMonolithSourceSymbol> SymResultsAll;
	if (!bPastCap)
	{
		SymResultsAll = DB->SearchSymbolsFTSFiltered(Query, SymbolKind, Module, PathFilter, N);
	}
	const int32 SymSliceStart = FMath::Min(SliceStart, SymResultsAll.Num());
	const int32 SymSliceEnd = FMath::Min(SliceEnd, SymResultsAll.Num());
	const int32 SymRowsThisPage = FMath::Max(0, SymSliceEnd - SymSliceStart);

	if (SymRowsThisPage > 0)
	{
		Parts.Add(TEXT("=== Symbol Matches ==="));
		for (int32 i = SymSliceStart; i < SymSliceEnd; ++i)
		{
			const FMonolithSourceSymbol& Sym = SymResultsAll[i];
			FString FilePath = DB->GetFilePath(Sym.FileId);
			Parts.Add(FString::Printf(TEXT("  [%s] %s (%s:%d)"), *Sym.Kind, *Sym.QualifiedName, *ShortPath(FilePath), Sym.LineStart));
			if (!Sym.Signature.IsEmpty())
			{
				Parts.Add(FString::Printf(TEXT("         %s"), *Sym.Signature));
			}
		}
	}

	// ---------- Source FTS rerun-slice ----------
	TArray<FString> Scopes;
	if (Scope == TEXT("cpp"))
	{
		Scopes = { TEXT("header"), TEXT("source"), TEXT("inline") };
	}
	else if (Scope == TEXT("shaders"))
	{
		Scopes = { TEXT("shader"), TEXT("shader_header") };
	}
	else
	{
		Scopes = { TEXT("all") };
	}

	// Build the full interleaved+de-duped source list at top-N, THEN slice.
	// De-dup happens before slicing so page boundaries land on unique rows.
	TArray<FMonolithSourceChunk> SourceMergedDeduped;
	if (!bPastCap)
	{
		TSet<FString> Seen;
		for (const FString& S : Scopes)
		{
			TArray<FMonolithSourceChunk> ScopeBatch = DB->SearchSourceFTSFiltered(Query, S, Module, PathFilter, N);
			for (const FMonolithSourceChunk& Match : ScopeBatch)
			{
				FString Key = FString::Printf(TEXT("%lld_%d"), Match.FileId, Match.LineNumber);
				if (Seen.Contains(Key)) continue;
				Seen.Add(Key);
				SourceMergedDeduped.Add(Match);
				if (SourceMergedDeduped.Num() >= N)
				{
					break;
				}
			}
			if (SourceMergedDeduped.Num() >= N)
			{
				break;
			}
		}
	}

	const int32 SrcSliceStart = FMath::Min(SliceStart, SourceMergedDeduped.Num());
	const int32 SrcSliceEnd = FMath::Min(SliceEnd, SourceMergedDeduped.Num());
	const int32 SrcRowsThisPage = FMath::Max(0, SrcSliceEnd - SrcSliceStart);

	if (SrcRowsThisPage > 0)
	{
		Parts.Add(TEXT("\n=== Source Line Matches ==="));
		for (int32 i = SrcSliceStart; i < SrcSliceEnd; ++i)
		{
			const FMonolithSourceChunk& Match = SourceMergedDeduped[i];
			FString FilePath = DB->GetFilePath(Match.FileId);
			FString Text = Match.Text.TrimStartAndEnd();
			if (Text.Len() > 120) Text = Text.Left(120) + TEXT("...");
			Parts.Add(FString::Printf(TEXT("  %s:%d"), *ShortPath(FilePath), Match.LineNumber));
			Parts.Add(FString::Printf(TEXT("    %s"), *Text));
		}
	}

	FString ResultText = Parts.Num() > 0
		? FString::Join(Parts, TEXT("\n"))
		: FString::Printf(TEXT("No results found for '%s'."), *Query);

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);

	// ---------- Pagination envelope ----------
	const int32 TotalRowsThisPage = SymRowsThisPage + SrcRowsThisPage;

	// total_estimate is emitted on page 0 ONLY; threaded forward via the cursor.
	if (bIsPageZero)
	{
		const int32 SymCount = DB->CountSymbolsFTSFiltered(Query, SymbolKind, Module, PathFilter);
		// For source COUNT(*) we issue one count per scope and sum — this matches
		// the rerun's union behavior. De-dup may slightly inflate the estimate
		// vs the actual de-duped page count; documented as ESTIMATE, not exact.
		int32 SrcCount = 0;
		for (const FString& S : Scopes)
		{
			SrcCount += DB->CountSourceFTSFiltered(Query, S, Module, PathFilter);
		}
		CachedTotalEstimate = SymCount + SrcCount;
		ResultObj->SetNumberField(TEXT("total_estimate"), CachedTotalEstimate);
	}
	// On pages 1+: omit total_estimate (caller has it from their cursor's tc field).

	// Emit next_cursor unless:
	//  - this page returned fewer than Limit rows (terminal), OR
	//  - the next slice start would meet/exceed HARD_CAP_ROWS.
	const bool bShortPage = TotalRowsThisPage < Limit;
	const int32 NextSliceStart = SliceEnd; // == (PageIndex + 1) * Limit
	const bool bCapReached = NextSliceStart >= HARD_CAP_ROWS;

	if (!bShortPage && !bCapReached)
	{
		MonolithCursorCodec::FCursorState OutState;
		OutState.QueryHash = CurrentHash;
		OutState.SymbolPage = PageIndex + 1;
		OutState.SourcePage = PageIndex + 1;
		OutState.CachedTotalEstimate = CachedTotalEstimate;
		ResultObj->SetStringField(TEXT("next_cursor"), MonolithCursorCodec::Encode(OutState));
	}
	// else: omit `next_cursor` — terminal page.

	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Tool 6: get_class_hierarchy
// ============================================================================

void FMonolithSourceActions::WalkAncestors(FMonolithSourceDatabase* DB, int64 SymId, TArray<FString>& Lines, int32 Indent, int32 MaxDepth, FHierarchyCounter& Counter, TSet<int64>& Visited)
{
	if (Indent > MaxDepth || Visited.Contains(SymId)) return;
	Visited.Add(SymId);

	TArray<FMonolithSourceInheritance> Parents = DB->GetParents(SymId);
	for (const auto& P : Parents)
	{
		if (Counter.Shown >= Counter.Limit) { Counter.Truncated++; continue; }
		FString Prefix;
		for (int32 i = 0; i < Indent; ++i) Prefix += TEXT("  ");
		Lines.Add(FString::Printf(TEXT("%s<- %s"), *Prefix, *P.Name));
		Counter.Shown++;
		WalkAncestors(DB, P.Id, Lines, Indent + 1, MaxDepth, Counter, Visited);
	}
}

void FMonolithSourceActions::WalkDescendants(FMonolithSourceDatabase* DB, int64 SymId, TArray<FString>& Lines, int32 Indent, int32 MaxDepth, FHierarchyCounter& Counter, TSet<int64>& Visited)
{
	if (Indent > MaxDepth || Visited.Contains(SymId)) return;
	Visited.Add(SymId);

	TArray<FMonolithSourceInheritance> Children = DB->GetChildren(SymId);
	if (Indent >= MaxDepth && Children.Num() > 0) { Counter.Truncated += Children.Num(); return; }

	for (const auto& C : Children)
	{
		if (Counter.Shown >= Counter.Limit) { Counter.Truncated++; continue; }
		FString Prefix;
		for (int32 i = 0; i < Indent; ++i) Prefix += TEXT("  ");
		Lines.Add(FString::Printf(TEXT("%s-> %s"), *Prefix, *C.Name));
		Counter.Shown++;
		WalkDescendants(DB, C.Id, Lines, Indent + 1, MaxDepth, Counter, Visited);
	}
}

FMonolithActionResult FMonolithSourceActions::HandleGetClassHierarchy(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available."));
	}

	FString ClassName = Params->HasField(TEXT("symbol")) ? Params->GetStringField(TEXT("symbol")) : Params->GetStringField(TEXT("class_name"));
	FString Direction = Params->HasField(TEXT("direction")) ? Params->GetStringField(TEXT("direction")) : TEXT("both");
	int32 Depth = Params->HasField(TEXT("depth")) ? static_cast<int32>(Params->GetNumberField(TEXT("depth"))) : 1;

	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(ClassName, TEXT("class"));
	if (Symbols.Num() == 0) Symbols = DB->GetSymbolsByName(ClassName, TEXT("struct"));
	if (Symbols.Num() == 0)
	{
		TArray<FMonolithSourceSymbol> AllSyms = DB->SearchSymbolsFTS(ClassName, 5);
		for (const auto& S : AllSyms)
		{
			if (S.Kind == TEXT("class") || S.Kind == TEXT("struct")) Symbols.Add(S);
		}
	}
	if (Symbols.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No class or struct found matching '%s'."), *ClassName));
	}

	// Filter out forward declarations — prefer real definitions
	bool bHasDefinition = false;
	for (const auto& S : Symbols)
	{
		if (S.LineEnd - S.LineStart > 1) { bHasDefinition = true; break; }
	}
	if (bHasDefinition)
	{
		TArray<FMonolithSourceSymbol> Filtered;
		for (const auto& S : Symbols)
		{
			FString SFilePath = DB->GetFilePath(S.FileId);
			if (!IsForwardDeclaration(SFilePath, S.LineStart, S.LineEnd))
			{
				Filtered.Add(S);
			}
		}
		if (Filtered.Num() > 0) Symbols = Filtered;
	}

	const FMonolithSourceSymbol& Sym = Symbols[0];
	FString FilePath = DB->GetFilePath(Sym.FileId);
	TArray<FString> Lines;
	Lines.Add(FString::Printf(TEXT("%s (%s)"), *Sym.Name, *ShortPath(FilePath)));

	FHierarchyCounter Counter;

	if (Direction == TEXT("ancestors") || Direction == TEXT("both"))
	{
		Lines.Add(TEXT("\nAncestors:"));
		TSet<int64> Visited;
		WalkAncestors(DB, Sym.Id, Lines, 1, Depth, Counter, Visited);
		bool bHasAncestors = false;
		for (const FString& L : Lines) { if (L.Contains(TEXT("<-"))) { bHasAncestors = true; break; } }
		if (!bHasAncestors) Lines.Add(TEXT("  (none)"));
	}

	if (Direction == TEXT("descendants") || Direction == TEXT("both"))
	{
		Lines.Add(TEXT("\nDescendants:"));
		TSet<int64> Visited;
		WalkDescendants(DB, Sym.Id, Lines, 1, Depth, Counter, Visited);
		if (Counter.Truncated > 0)
		{
			Lines.Add(FString::Printf(TEXT("\n  ... and %d more (increase depth to see all)"), Counter.Truncated));
		}
	}

	FString ResultText = FString::Join(Lines, TEXT("\n"));

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Tool 7: get_module_info
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleGetModuleInfo(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available."));
	}

	FString ModuleName = Params->GetStringField(TEXT("module_name"));

	TOptional<FMonolithSourceModuleStats> Stats = DB->GetModuleStats(ModuleName);
	if (!Stats.IsSet())
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No module found matching '%s'."), *ModuleName));
	}

	const FMonolithSourceModuleStats& S = Stats.GetValue();
	TArray<FString> Lines;
	Lines.Add(FString::Printf(TEXT("Module: %s"), *S.Name));
	Lines.Add(FString::Printf(TEXT("Path: %s"), *ShortPath(S.Path)));
	Lines.Add(FString::Printf(TEXT("Type: %s"), *S.ModuleType));
	Lines.Add(FString::Printf(TEXT("Files: %d"), S.FileCount));
	Lines.Add(TEXT(""));
	Lines.Add(TEXT("Symbol counts by kind:"));

	TArray<FString> SortedKinds;
	S.SymbolCounts.GetKeys(SortedKinds);
	SortedKinds.Sort();
	for (const FString& Kind : SortedKinds)
	{
		Lines.Add(FString::Printf(TEXT("  %s: %d"), *Kind, S.SymbolCounts[Kind]));
	}

	// Show key classes
	TArray<FMonolithSourceSymbol> KeyClasses = DB->GetSymbolsInModule(ModuleName, TEXT("class"), 20);
	if (KeyClasses.Num() > 0)
	{
		Lines.Add(TEXT(""));
		Lines.Add(TEXT("Key classes:"));
		for (const auto& Cls : KeyClasses)
		{
			Lines.Add(FString::Printf(TEXT("  %s (line %d)"), *Cls.Name, Cls.LineStart));
		}
	}

	FString ResultText = FString::Join(Lines, TEXT("\n"));

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Tool 8: get_symbol_context
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleGetSymbolContext(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available."));
	}

	FString Symbol = Params->GetStringField(TEXT("symbol"));
	int32 ContextLines = Params->HasField(TEXT("context_lines")) ? static_cast<int32>(Params->GetNumberField(TEXT("context_lines"))) : 20;

	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(Symbol);
	if (Symbols.Num() == 0) Symbols = DB->SearchSymbolsFTS(Symbol, 5);
	if (Symbols.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No symbol found matching '%s'."), *Symbol));
	}

	TArray<FString> Parts;
	int32 Shown = 0;
	for (const auto& Sym : Symbols)
	{
		if (Shown >= 3) break;

		FString FilePath = DB->GetFilePath(Sym.FileId);
		int32 CtxStart = FMath::Max(1, Sym.LineStart - ContextLines);
		int32 CtxEnd = Sym.LineEnd + ContextLines;

		FString Header = FString::Printf(TEXT("--- %s ---"), *Sym.QualifiedName);
		TArray<FString> InfoParts;
		if (!Sym.Docstring.IsEmpty())
		{
			InfoParts.Add(FString::Printf(TEXT("Docstring: %s"), *Sym.Docstring));
		}
		if (!Sym.Signature.IsEmpty())
		{
			InfoParts.Add(FString::Printf(TEXT("Signature: %s"), *Sym.Signature));
		}
		InfoParts.Add(FString::Printf(TEXT("File: %s (lines %d-%d)"), *ShortPath(FilePath), Sym.LineStart, Sym.LineEnd));

		FString Source = ReadFileLines(FilePath, CtxStart, CtxEnd);
		Parts.Add(Header + TEXT("\n") + FString::Join(InfoParts, TEXT("\n")) + TEXT("\n\n") + Source);
		Shown++;
	}

	FString ResultText = Parts.Num() > 0
		? FString::Join(Parts, TEXT("\n\n"))
		: FString::Printf(TEXT("Found symbol '%s' but could not read source."), *Symbol);

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Tool 9: read_file
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleReadFile(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available."));
	}

	FString Path = Params->GetStringField(TEXT("file_path"));
	int32 StartLine = Params->HasField(TEXT("start_line")) ? static_cast<int32>(Params->GetNumberField(TEXT("start_line"))) : 1;
	int32 EndLine = Params->HasField(TEXT("end_line")) ? static_cast<int32>(Params->GetNumberField(TEXT("end_line"))) : 0;

	// Resolve path
	FString ResolvedPath;

	// Try as absolute first
	if (FPaths::FileExists(Path))
	{
		ResolvedPath = Path;
	}
	else
	{
		// Normalize separators to backslashes to match DB-stored paths
		FString NormalizedPath = Path;
		NormalizedPath.ReplaceInline(TEXT("/"), TEXT("\\"));

		// Try DB lookup by exact path
		TOptional<FMonolithSourceFile> F = DB->FindFileByPath(NormalizedPath);
		if (F.IsSet())
		{
			ResolvedPath = F->Path;
		}
		else
		{
			// Try suffix match (e.g. "Runtime\Engine\Classes\GameFramework\Actor.h")
			F = DB->FindFileBySuffix(NormalizedPath);
			if (F.IsSet())
			{
				ResolvedPath = F->Path;
			}
		}
	}

	if (ResolvedPath.IsEmpty())
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No file found matching '%s'."), *Path));
	}

	if (EndLine <= 0)
	{
		EndLine = StartLine + 199;
	}

	FString Header = FString::Printf(TEXT("--- %s (lines %d-%d) ---"), *ShortPath(ResolvedPath), StartLine, EndLine);
	FString Source = ReadFileLines(ResolvedPath, StartLine, EndLine);

	FString ResultText = Header + TEXT("\n") + Source;

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Bonus: trigger_reindex
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleTriggerReindex(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor)
	{
		return FMonolithActionResult::Error(TEXT("Editor not available."));
	}

	UMonolithSourceSubsystem* Subsystem = Cast<UMonolithSourceSubsystem>(GEditor->GetEditorSubsystemBase(UMonolithSourceSubsystem::StaticClass()));
	if (!Subsystem)
	{
		return FMonolithActionResult::Error(TEXT("MonolithSourceSubsystem not available."));
	}

	if (Subsystem->IsIndexing())
	{
		return FMonolithActionResult::Error(TEXT("Indexing already in progress."));
	}

	Subsystem->TriggerReindex();

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), TEXT("Full source indexing started (engine + project). This runs in the background — check editor log for progress."));
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// trigger_project_reindex
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleTriggerProjectReindex(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor)
	{
		return FMonolithActionResult::Error(TEXT("Editor not available."));
	}

	UMonolithSourceSubsystem* Subsystem = Cast<UMonolithSourceSubsystem>(GEditor->GetEditorSubsystemBase(UMonolithSourceSubsystem::StaticClass()));
	if (!Subsystem)
	{
		return FMonolithActionResult::Error(TEXT("MonolithSourceSubsystem not available."));
	}

	if (Subsystem->IsIndexing())
	{
		return FMonolithActionResult::Error(TEXT("Indexing already in progress."));
	}

	Subsystem->TriggerProjectReindex();

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), TEXT("Project source indexing started (incremental). This runs in the background — check editor log for progress."));
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Phase 1 — item 1: get_include_path
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleGetIncludePath(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available. Run source.trigger_reindex first."));
	}

	const FString Symbol = Params->GetStringField(TEXT("symbol"));
	if (Symbol.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'symbol' is required."));
	}

	// For a Class::Method input resolve the include via the OWNING CLASS row — the
	// method itself need not be a symbol; the file is the class's header regardless.
	FString LookupName = Symbol;
	int32 ScopeIdx = Symbol.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
	if (ScopeIdx != INDEX_NONE)
	{
		LookupName = Symbol.Left(ScopeIdx);
	}

	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(LookupName);
	if (Symbols.Num() == 0) Symbols = DB->SearchSymbolsFTS(LookupName, 5);
	if (Symbols.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No symbol found matching '%s'."), *Symbol));
	}

	// Prefer a header file when several rows share the name (e.g. decl + def).
	const FMonolithSourceSymbol* Chosen = &Symbols[0];
	for (const FMonolithSourceSymbol& S : Symbols)
	{
		const FString P = DB->GetFilePath(S.FileId);
		if (P.EndsWith(TEXT(".h")))
		{
			Chosen = &S;
			break;
		}
	}

	const FString FilePath = DB->GetFilePath(Chosen->FileId);
	bool bIncludable = true;
	FString Warning;
	const FString Include = DeriveIncludePath(FilePath, bIncludable, Warning);

	FString ModuleName, BuildCsPath;
	DB->GetFileModuleInfo(Chosen->FileId, ModuleName, BuildCsPath);
	FString BuildCsNote;
	if (!ModuleName.IsEmpty())
	{
		BuildCsNote = BuildCsPath.IsEmpty()
			? FString::Printf(TEXT("Module '%s' — add to your Build.cs deps"), *ModuleName)
			: FString::Printf(TEXT("Module '%s' — add to your Build.cs deps (%s)"), *ModuleName, *FPaths::GetCleanFilename(BuildCsPath));
	}

	auto ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("include"), Include);
	ResultObj->SetBoolField(TEXT("includable"), bIncludable);
	if (!ModuleName.IsEmpty()) ResultObj->SetStringField(TEXT("module"), ModuleName);
	if (!BuildCsNote.IsEmpty()) ResultObj->SetStringField(TEXT("build_cs_note"), BuildCsNote);
	if (!Warning.IsEmpty()) ResultObj->SetStringField(TEXT("warning"), Warning);

	// Human-readable content envelope, matching the other source handlers.
	FString Text = FString::Printf(TEXT("#include \"%s\""), *Include);
	if (!ModuleName.IsEmpty()) Text += FString::Printf(TEXT("\nModule: %s"), *ModuleName);
	if (!BuildCsNote.IsEmpty()) Text += FString::Printf(TEXT("\n%s"), *BuildCsNote);
	if (!Warning.IsEmpty()) Text += FString::Printf(TEXT("\nWARNING: %s"), *Warning);

	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), Text);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Phase 1 — item 2: get_signature
//
// Declaration-read is the PRIMARY mechanism (Step-0 finding): class-body method
// declarations are NOT indexed as `symbols`, so we resolve via the owning class
// row + source-line FTS over source_fts, read the declaration line(s) from the
// file (continuation lines forward to the closing paren), and strip the trailing
// macro `\` + any inline body. The `signature` column is an opportunistic fast
// path ONLY when present AND body-free. Reports source: "declaration_read"|"column".
// ============================================================================

FString FMonolithSourceActions::CompactDeclaration(const TArray<FString>& Lines, int32 StartIdx)
{
	// Accumulate from StartIdx forward until we balance the parens that open the
	// parameter list AND reach a `;` or `{`. Strip trailing `\` line continuations
	// and any inline body.
	FString Accum;
	int32 ParenDepth = 0;
	bool bSawOpenParen = false;

	for (int32 i = StartIdx; i < Lines.Num() && i < StartIdx + 12; ++i)
	{
		FString Line = Lines[i];
		// Strip a trailing macro line-continuation backslash.
		Line.TrimEndInline();
		if (Line.EndsWith(TEXT("\\")))
		{
			Line = Line.LeftChop(1).TrimEnd();
		}

		bool bDone = false;
		for (int32 c = 0; c < Line.Len(); ++c)
		{
			const TCHAR Ch = Line[c];
			if (Ch == TEXT('('))      { ParenDepth++; bSawOpenParen = true; }
			else if (Ch == TEXT(')')) { ParenDepth = FMath::Max(0, ParenDepth - 1); }
			else if (ParenDepth == 0 && bSawOpenParen && (Ch == TEXT('{') || Ch == TEXT(';')))
			{
				// End of declaration — everything before this terminator was already
				// appended char-by-char above; just stop (do NOT re-append the prefix
				// — that double-counted the line and duplicated the tail).
				bDone = true;
				break;
			}
			Accum += Ch;
		}

		if (bDone) break;
		Accum += TEXT(" ");
	}

	// Collapse runs of whitespace for a clean one-line signature.
	FString Out;
	bool bPrevSpace = false;
	for (const TCHAR Ch : Accum)
	{
		if (FChar::IsWhitespace(Ch))
		{
			if (!bPrevSpace) Out += TEXT(' ');
			bPrevSpace = true;
		}
		else
		{
			Out += Ch;
			bPrevSpace = false;
		}
	}
	return Out.TrimStartAndEnd();
}

FMonolithActionResult FMonolithSourceActions::HandleGetSignature(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available. Run source.trigger_reindex first."));
	}

	const FString Symbol = Params->GetStringField(TEXT("symbol"));
	if (Symbol.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'symbol' is required."));
	}
	const int32 Limit = Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 10;

	// The method name for FTS / column matching is the trailing identifier.
	FString MethodName = Symbol;
	int32 ScopeIdx = Symbol.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
	if (ScopeIdx != INDEX_NONE)
	{
		MethodName = Symbol.Mid(ScopeIdx + 2);
	}

	struct FOverload { FString Signature; FString Source; FString File; int32 Line = 0; };
	TArray<FOverload> Overloads;

	// --- Fast path: a body-free `signature` column on an indexed symbol row. ---
	TArray<FMonolithSourceSymbol> Symbols = DB->GetSymbolsByName(MethodName, TEXT("function"));
	for (const FMonolithSourceSymbol& S : Symbols)
	{
		if (Overloads.Num() >= Limit) break;
		if (S.Signature.IsEmpty()) continue;
		// Body-free only — reject anything carrying an inline body or continuation.
		if (S.Signature.Contains(TEXT("{")) || S.Signature.Contains(TEXT("\\"))) continue;
		FOverload O;
		O.Signature = S.Signature.TrimStartAndEnd();
		O.Source = TEXT("column");
		O.File = ShortPath(DB->GetFilePath(S.FileId));
		O.Line = S.LineStart;
		Overloads.Add(MoveTemp(O));
	}

	// --- Primary: declaration-read via source-line FTS over source_fts. ---
	if (Overloads.Num() == 0)
	{
		// Search for the call/decl token. EscapeFTS strips the trailing '(' and the
		// `::`, so we query the method name and verify the `Name(` shape per hit.
		const FString FtsQuery = Symbol; // FTS escape handles :: -> space
		TArray<FMonolithSourceChunk> Chunks = DB->SearchSourceFTS(FtsQuery, TEXT("all"), 50);

		TSet<FString> SeenSignatures;
		for (const FMonolithSourceChunk& Chunk : Chunks)
		{
			if (Overloads.Num() >= Limit) break;

			const FString FilePath = DB->GetFilePath(Chunk.FileId);
			TArray<FString> FileLines;
			if (!FFileHelper::LoadFileToStringArray(FileLines, *FilePath)) continue;

			// The chunk's line_number is the 1-based first line of a 10-line batch.
			// Scan the batch window for a declaration line containing `MethodName(`.
			const int32 WinStart = FMath::Max(0, Chunk.LineNumber - 1);
			const int32 WinEnd = FMath::Min(FileLines.Num(), WinStart + 10);
			const FString NeedlePattern = MethodName + TEXT("(");

			for (int32 i = WinStart; i < WinEnd; ++i)
			{
				if (Overloads.Num() >= Limit) break;

				const FString& L = FileLines[i];
				int32 DeclIdx = L.Find(NeedlePattern, ESearchCase::CaseSensitive);
				if (DeclIdx == INDEX_NONE) continue;
				// Require the char before the name to be a non-identifier (so we don't
				// match a substring of a longer identifier).
				if (DeclIdx > 0)
				{
					const TCHAR Prev = L[DeclIdx - 1];
					if (FChar::IsAlnum(Prev) || Prev == TEXT('_')) continue;
				}

				const FString Sig = CompactDeclaration(FileLines, i);
				if (Sig.IsEmpty()) continue;
				// Must look like a declaration: contains the method name and a paren.
				if (!Sig.Contains(NeedlePattern)) continue;
				if (SeenSignatures.Contains(Sig)) continue;
				SeenSignatures.Add(Sig);

				FOverload O;
				O.Signature = Sig;
				O.Source = TEXT("declaration_read");
				O.File = ShortPath(FilePath);
				O.Line = i + 1;
				Overloads.Add(MoveTemp(O));
			}
		}
	}

	if (Overloads.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("No signature found for '%s'."), *Symbol));
	}

	// Structured + text envelope.
	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> OverloadArr;
	TArray<FString> TextLines;
	for (const FOverload& O : Overloads)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("signature"), O.Signature);
		Obj->SetStringField(TEXT("source"), O.Source);
		Obj->SetStringField(TEXT("file"), O.File);
		Obj->SetNumberField(TEXT("line"), O.Line);
		OverloadArr.Add(MakeShared<FJsonValueObject>(Obj));
		TextLines.Add(FString::Printf(TEXT("%s\n  // %s @ %s:%d"), *O.Signature, *O.Source, *O.File, O.Line));
	}
	ResultObj->SetArrayField(TEXT("overloads"), OverloadArr);

	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), FString::Join(TextLines, TEXT("\n")));
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Phase 1 — item 3: check_deprecations
//
// Batch read of symbol_deprecations. Empty-table (schema v2 landed, no reindex
// yet) -> { index_state: "empty", hint: "run source.trigger_reindex" } and OMIT
// per-symbol verdicts (Decision 3) — never a false "no symbol is deprecated".
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleCheckDeprecations(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available. Run source.trigger_reindex first."));
	}

	// Collect the requested symbol names (array of strings).
	TArray<FString> SymbolNames;
	const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
	if (Params->TryGetArrayField(TEXT("symbols"), Arr) && Arr)
	{
		for (const TSharedPtr<FJsonValue>& V : *Arr)
		{
			FString S;
			if (V.IsValid() && V->TryGetString(S) && !S.IsEmpty())
			{
				SymbolNames.Add(S);
			}
		}
	}
	if (SymbolNames.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("'symbols' must be a non-empty array of symbol names."));
	}

	auto ResultObj = MakeShared<FJsonObject>();

	// Decision 3: empty deprecation index -> clean "empty" state, no verdicts.
	if (DB->GetDeprecationCount() == 0)
	{
		ResultObj->SetStringField(TEXT("index_state"), TEXT("empty"));
		ResultObj->SetStringField(TEXT("hint"), TEXT("run source.trigger_reindex"));

		TArray<TSharedPtr<FJsonValue>> ContentArr;
		auto ContentItem = MakeShared<FJsonObject>();
		ContentItem->SetStringField(TEXT("type"), TEXT("text"));
		ContentItem->SetStringField(TEXT("text"),
			TEXT("Deprecation index is empty (schema v2 landed but not yet populated). Run source.trigger_reindex to populate it."));
		ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
		ResultObj->SetArrayField(TEXT("content"), ContentArr);
		return FMonolithActionResult::Success(ResultObj);
	}

	TMap<FString, FMonolithDeprecationRow> Deprecated = DB->GetDeprecationsBatch(SymbolNames);

	TArray<TSharedPtr<FJsonValue>> Verdicts;
	TArray<FString> TextLines;
	for (const FString& Name : SymbolNames)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("symbol"), Name);
		const FMonolithDeprecationRow* Found = Deprecated.Find(Name);
		if (Found)
		{
			Obj->SetBoolField(TEXT("deprecated"), true);
			Obj->SetStringField(TEXT("version"), Found->Version);
			Obj->SetStringField(TEXT("message"), Found->Message);
			Obj->SetStringField(TEXT("kind"), Found->Kind);
			TextLines.Add(FString::Printf(TEXT("%s: DEPRECATED (%s) [%s] %s"), *Name, *Found->Version, *Found->Kind, *Found->Message));
		}
		else
		{
			Obj->SetBoolField(TEXT("deprecated"), false);
			TextLines.Add(FString::Printf(TEXT("%s: not deprecated"), *Name));
		}
		Verdicts.Add(MakeShared<FJsonValueObject>(Obj));
	}
	ResultObj->SetArrayField(TEXT("results"), Verdicts);

	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), FString::Join(TextLines, TEXT("\n")));
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Phase 2 — item 4: verify_symbols
//
// Composes items 1+2+3 via the shared C++ helpers (ResolveIncludeForSymbol /
// ResolveFirstSignature + DB->GetDeprecation + SymbolExists) — NOT by re-parsing
// the JSON handlers. `exists` for a Class::Method is class-row + source_fts
// declaration hit, NEVER symbols-table presence (Step-0 finding). Missing symbol
// -> exists:false, no error.
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleVerifySymbols(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available. Run source.trigger_reindex first."));
	}

	TArray<FString> SymbolNames;
	const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
	if (Params->TryGetArrayField(TEXT("symbols"), Arr) && Arr)
	{
		for (const TSharedPtr<FJsonValue>& V : *Arr)
		{
			FString S;
			if (V.IsValid() && V->TryGetString(S) && !S.IsEmpty())
			{
				SymbolNames.Add(S);
			}
		}
	}
	if (SymbolNames.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("'symbols' must be a non-empty array of symbol names."));
	}

	// Deprecation status is a single batch read (Decision 3 empty-index contract).
	const bool bDeprecationIndexEmpty = (DB->GetDeprecationCount() == 0);
	TMap<FString, FMonolithDeprecationRow> Deprecated;
	if (!bDeprecationIndexEmpty)
	{
		// Key the batch lookup on the trailing identifier (symbol_deprecations stores
		// the parsed method name; Class:: prefixes are not in that column — Step-0).
		TArray<FString> LookupNames;
		LookupNames.Reserve(SymbolNames.Num());
		for (const FString& Name : SymbolNames)
		{
			FString MethodName = Name;
			const int32 ScopeIdx = Name.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
			if (ScopeIdx != INDEX_NONE) MethodName = Name.Mid(ScopeIdx + 2);
			LookupNames.AddUnique(MethodName);
		}
		Deprecated = DB->GetDeprecationsBatch(LookupNames);
	}

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> Records;
	TArray<FString> TextLines;

	for (const FString& Symbol : SymbolNames)
	{
		auto Rec = MakeShared<FJsonObject>();
		Rec->SetStringField(TEXT("symbol"), Symbol);

		const bool bExists = SymbolExists(DB, Symbol);
		Rec->SetBoolField(TEXT("exists"), bExists);

		if (!bExists)
		{
			Records.Add(MakeShared<FJsonValueObject>(Rec));
			TextLines.Add(FString::Printf(TEXT("%s: NOT FOUND"), *Symbol));
			continue;
		}

		// Include path + module (item 1 composition).
		FString Include, Module, Warning;
		bool bIncludable = true;
		if (ResolveIncludeForSymbol(DB, Symbol, Include, bIncludable, Module, Warning))
		{
			if (!Include.IsEmpty()) Rec->SetStringField(TEXT("include"), Include);
			Rec->SetBoolField(TEXT("includable"), bIncludable);
			if (!Module.IsEmpty()) Rec->SetStringField(TEXT("module"), Module);
			if (!Warning.IsEmpty()) Rec->SetStringField(TEXT("warning"), Warning);
		}

		// Signature (item 2 composition).
		FString Signature, SigSource;
		if (ResolveFirstSignature(DB, Symbol, Signature, SigSource))
		{
			Rec->SetStringField(TEXT("signature"), Signature);
			Rec->SetStringField(TEXT("signature_source"), SigSource);
		}

		// Deprecation (item 3 composition).
		FString MethodName = Symbol;
		const int32 ScopeIdx = Symbol.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
		if (ScopeIdx != INDEX_NONE) MethodName = Symbol.Mid(ScopeIdx + 2);

		if (bDeprecationIndexEmpty)
		{
			Rec->SetStringField(TEXT("deprecation_index"), TEXT("empty"));
		}
		else if (const FMonolithDeprecationRow* Dep = Deprecated.Find(MethodName))
		{
			Rec->SetBoolField(TEXT("deprecated"), true);
			Rec->SetStringField(TEXT("deprecation_version"), Dep->Version);
			Rec->SetStringField(TEXT("deprecation_message"), Dep->Message);
			Rec->SetStringField(TEXT("deprecation_kind"), Dep->Kind);
		}
		else
		{
			Rec->SetBoolField(TEXT("deprecated"), false);
		}

		Records.Add(MakeShared<FJsonValueObject>(Rec));

		FString Line = FString::Printf(TEXT("%s: exists"), *Symbol);
		if (!Include.IsEmpty()) Line += FString::Printf(TEXT(" | #include \"%s\"%s"), *Include, bIncludable ? TEXT("") : TEXT(" (NOT includable)"));
		if (!Signature.IsEmpty()) Line += FString::Printf(TEXT(" | %s"), *Signature);
		if (!bDeprecationIndexEmpty && Deprecated.Contains(MethodName)) Line += TEXT(" | DEPRECATED");
		TextLines.Add(Line);
	}

	ResultObj->SetArrayField(TEXT("results"), Records);

	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), FString::Join(TextLines, TEXT("\n")));
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Phase 2 — item 5: find_example_usage
//
// Substrate is source-line FTS over source_fts (NOT the references table, which
// is to_symbol_id-keyed and empty for engine API — Step-0 finding). Query the
// FTS for the symbol, keep hits whose line matches the call pattern `Name(`, read
// +/-3 context lines via LoadFileToStringArray, rank per Decision 4, and
// cursor-paginate via MonolithCursorCodec + the rerun-slice scheme (the same
// moving-FTS-index rationale as search_source).
// ============================================================================

FMonolithActionResult FMonolithSourceActions::HandleFindExampleUsage(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available. Run source.trigger_reindex first."));
	}

	const FString Symbol = Params->GetStringField(TEXT("symbol"));
	if (Symbol.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'symbol' is required."));
	}
	FString Prefer = Params->HasField(TEXT("prefer")) ? Params->GetStringField(TEXT("prefer")) : TEXT("engine");
	Prefer = Prefer.ToLower();
	const bool bPreferProject = (Prefer == TEXT("project"));
	const int32 RequestedLimit = Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 10;
	const FString CursorIn = Params->HasField(TEXT("cursor")) ? Params->GetStringField(TEXT("cursor")) : TEXT("");

	const int32 Limit = FMath::Max(1, RequestedLimit);
	constexpr int32 HARD_CAP_ROWS = 500;
	constexpr int32 FTS_FETCH = 400; // candidate FTS rows to scan before ranking

	// Cursor query-hash: symbol + prefer. (Mode/Module/PathFilter/Kind unused here.)
	const uint32 CurrentHash = MonolithCursorCodec::ComputeQueryHash(
		Symbol, Prefer, TEXT("find_example_usage"), TEXT(""), TEXT(""), TEXT(""));

	int32 PageIndex = 0;
	if (!CursorIn.IsEmpty())
	{
		MonolithCursorCodec::FCursorState State;
		if (!MonolithCursorCodec::Decode(CursorIn, State) || State.QueryHash != CurrentHash)
		{
			TSharedPtr<FJsonObject> ErrData = MakeShared<FJsonObject>();
			ErrData->SetStringField(TEXT("error_code"), TEXT("INVALID_CURSOR"));
			return FMonolithActionResult::Error(
				TEXT("Cursor decode/query mismatch; restart pagination without `cursor`."),
				FMonolithJsonUtils::ErrInvalidParams
			).WithErrorData(ErrData);
		}
		PageIndex = State.SourcePage;
	}

	// Method name = trailing identifier; needle is `Name(`.
	FString MethodName = Symbol;
	const int32 ScopeIdx = Symbol.Find(TEXT("::"), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
	if (ScopeIdx != INDEX_NONE) MethodName = Symbol.Mid(ScopeIdx + 2);
	const FString NeedlePattern = MethodName + TEXT("(");

	struct FUsage
	{
		FString File;       // ShortPath form
		int32 Line = 0;
		FString Context;    // +/-3 lines joined
		int32 RankClass = 3; // 0 = engine Runtime, 1 = other engine, 2 = project
		FString SortPath;   // tie-break (native path)
	};
	TArray<FUsage> Usages;
	TSet<FString> Seen;

	TArray<FMonolithSourceChunk> Chunks = DB->SearchSourceFTS(Symbol, TEXT("all"), FTS_FETCH);
	for (const FMonolithSourceChunk& Chunk : Chunks)
	{
		const FString FilePath = DB->GetFilePath(Chunk.FileId);
		TArray<FString> FileLines;
		if (!FFileHelper::LoadFileToStringArray(FileLines, *FilePath)) continue;

		const int32 WinStart = FMath::Max(0, Chunk.LineNumber - 1);
		const int32 WinEnd = FMath::Min(FileLines.Num(), WinStart + 10);
		for (int32 i = WinStart; i < WinEnd; ++i)
		{
			const FString& L = FileLines[i];
			const int32 HitIdx = L.Find(NeedlePattern, ESearchCase::CaseSensitive);
			if (HitIdx == INDEX_NONE) continue;
			if (HitIdx > 0)
			{
				const TCHAR Prev = L[HitIdx - 1];
				if (FChar::IsAlnum(Prev) || Prev == TEXT('_')) continue;
			}

			const FString Key = FString::Printf(TEXT("%lld_%d"), Chunk.FileId, i + 1);
			if (Seen.Contains(Key)) continue;
			Seen.Add(Key);

			// +/-3 context lines.
			const int32 CtxStart = FMath::Max(0, i - 3);
			const int32 CtxEnd = FMath::Min(FileLines.Num() - 1, i + 3);
			TArray<FString> CtxLines;
			for (int32 c = CtxStart; c <= CtxEnd; ++c)
			{
				CtxLines.Add(FString::Printf(TEXT("%5d | %s"), c + 1, *FileLines[c]));
			}

			// Rank classification (Decision 4). PARITY: classify on the raw
			// DB-stored path (forward-slashed), via the SAME `Engine/Source/`
			// (engine) + `/Source/Runtime/` (runtime) substrings the offline
			// mirrors (monolith_query.cpp / monolith_offline.py) use, so the
			// rank order — and therefore the byte output — is identical across
			// all three tools. Do NOT use FPaths::EngineDir()/ConvertRelativePathToFull
			// here: the offline tools have no such call, and an engine *plugin*
			// path (Engine/Plugins/.../Source/) deliberately classifies as project
			// in all three (it lacks the `Engine/Source/` segment).
			FString NormPath = FilePath; NormPath.ReplaceInline(TEXT("\\"), TEXT("/"));
			const bool bIsEngine = NormPath.Contains(TEXT("Engine/Source/"));
			const bool bIsRuntime = NormPath.Contains(TEXT("/Source/Runtime/"));

			FUsage U;
			U.File = ShortPath(FilePath);
			U.Line = i + 1;
			U.Context = FString::Join(CtxLines, TEXT("\n"));
			U.SortPath = FilePath;
			if (bIsEngine && bIsRuntime)      U.RankClass = 0;
			else if (bIsEngine)               U.RankClass = 1;
			else                              U.RankClass = 2;
			Usages.Add(MoveTemp(U));
		}
	}

	// Decision 4 ordering. For prefer:"project", project (class 2) sorts ahead of
	// engine; otherwise engine Runtime (0) then other engine (1) then project (2).
	Usages.Sort([bPreferProject](const FUsage& A, const FUsage& B)
	{
		auto Key = [bPreferProject](const FUsage& X) -> int32
		{
			if (!bPreferProject) return X.RankClass;          // 0,1,2 as-is
			// prefer project: project first, then engine Runtime, then other engine.
			switch (X.RankClass) { case 2: return 0; case 0: return 1; default: return 2; }
		};
		const int32 Ka = Key(A), Kb = Key(B);
		if (Ka != Kb) return Ka < Kb;
		if (A.SortPath != B.SortPath) return A.SortPath < B.SortPath;
		return A.Line < B.Line;
	});

	// Rerun-slice paging over the ranked list (deterministic order => safe slice).
	const int32 Total = Usages.Num();
	const int32 SliceStart = FMath::Min(PageIndex * Limit, HARD_CAP_ROWS);
	const int32 SliceEnd = FMath::Min(FMath::Min(SliceStart + Limit, Total), HARD_CAP_ROWS);

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> Examples;
	TArray<FString> TextParts;
	for (int32 i = SliceStart; i < SliceEnd; ++i)
	{
		const FUsage& U = Usages[i];
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("file"), U.File);
		Obj->SetNumberField(TEXT("line"), U.Line);
		Obj->SetStringField(TEXT("context"), U.Context);
		Examples.Add(MakeShared<FJsonValueObject>(Obj));
		TextParts.Add(FString::Printf(TEXT("--- %s:%d ---\n%s"), *U.File, U.Line, *U.Context));
	}
	ResultObj->SetArrayField(TEXT("examples"), Examples);
	// Clamp to the cap: paging never returns past HARD_CAP_ROWS, so advertising
	// the raw Total would over-promise rows the pager will never yield. This is a
	// structured-JSON field only — it is NOT part of the content[].text envelope,
	// so it does not enter the offline text byte-compare (same as next_cursor; the
	// offline tools emit plain text without either field, and the live text omits
	// both too — parity stays meaningful on the rendered snippets).
	ResultObj->SetNumberField(TEXT("total_estimate"), FMath::Min(Total, HARD_CAP_ROWS));

	// next_cursor unless terminal (short page or cap reached).
	const int32 RowsThisPage = SliceEnd - SliceStart;
	const int32 NextSliceStart = (PageIndex + 1) * Limit;
	if (RowsThisPage >= Limit && NextSliceStart < Total && NextSliceStart < HARD_CAP_ROWS)
	{
		MonolithCursorCodec::FCursorState OutState;
		OutState.QueryHash = CurrentHash;
		OutState.SymbolPage = PageIndex + 1;
		OutState.SourcePage = PageIndex + 1;
		OutState.CachedTotalEstimate = Total;
		ResultObj->SetStringField(TEXT("next_cursor"), MonolithCursorCodec::Encode(OutState));
	}

	FString ResultText = TextParts.Num() > 0
		? FString::Join(TextParts, TEXT("\n\n"))
		: FString::Printf(TEXT("No call-site examples found for '%s'."), *Symbol);

	TArray<TSharedPtr<FJsonValue>> ContentArr;
	auto ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), ResultText);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	ResultObj->SetArrayField(TEXT("content"), ContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Phase 3 — item 7: lint_header
//
// A self-contained regex lint over a SINGLE header file. MUST work on UNINDEXED
// files (the primary case is a header the agent just wrote, not yet in the DB),
// so the rule table reads only the file lines + the file path. The expected
// <MODULE>_API token is derived PRIMARILY from the path; an optional valid-
// specifier vocabulary cross-check degrades gracefully when empty. FRegexMatcher
// is constructed as a LOCAL only (ICU init contract — Regex.h:41).
// ============================================================================

namespace MonolithLintDetail
{
	// Derive the owning module name from a .../Source/<Module>/ segment (covers
	// both Source/<Module>/ and Plugins/<X>/Source/<Module>/). Returns empty when
	// no recognised layout is present.
	static FString DeriveModuleFromPath(const FString& FilePath)
	{
		FString Path = FilePath;
		Path.ReplaceInline(TEXT("\\"), TEXT("/"));
		const int32 SrcIdx = Path.Find(TEXT("/Source/"), ESearchCase::IgnoreCase, ESearchDir::FromEnd);
		if (SrcIdx == INDEX_NONE) return FString();
		const FString AfterSrc = Path.Mid(SrcIdx + 8); // skip "/Source/"
		int32 Slash = INDEX_NONE;
		if (AfterSrc.FindChar(TEXT('/'), Slash))
		{
			return AfterSrc.Left(Slash);
		}
		return FString();
	}

	// Strip // line comments from a code line so the rule scans don't fire on
	// commented-out macros. Multi-line block comments are handled by the caller.
	static FString StripComment(const FString& Line)
	{
		const int32 LineComment = Line.Find(TEXT("//"), ESearchCase::CaseSensitive);
		return (LineComment != INDEX_NONE) ? Line.Left(LineComment) : Line;
	}

	// Strip block comments from a single source line, threading the multi-line
	// state through bInOutBlock. Avoids the FString::Find start-position overload
	// by chopping the leading already-scanned portion off a working copy each pass.
	static FString StripBlockComments(const FString& Line, bool& bInOutBlock)
	{
		FString Result;
		FString Work = Line;
		while (true)
		{
			if (bInOutBlock)
			{
				const int32 End = Work.Find(TEXT("*/"), ESearchCase::CaseSensitive);
				if (End == INDEX_NONE) { return Result; }  // whole remainder is inside a block
				Work = Work.Mid(End + 2);
				bInOutBlock = false;
			}
			const int32 Open = Work.Find(TEXT("/*"), ESearchCase::CaseSensitive);
			if (Open == INDEX_NONE) { Result += Work; return Result; }
			Result += Work.Left(Open);
			Work = Work.Mid(Open + 2);
			bInOutBlock = true;
		}
	}
}

TArray<FMonolithSourceActions::FLintFinding> FMonolithSourceActions::LintHeaderLines(
	const FString& FilePath, const TArray<FString>& Lines, const TSet<FString>& ValidSpecifiers)
{
	using namespace MonolithLintDetail;

	TArray<FLintFinding> Findings;

	const FString ModuleName = DeriveModuleFromPath(FilePath);
	const FString ExpectedApiMacro = ModuleName.IsEmpty() ? FString() : (ModuleName.ToUpper() + TEXT("_API"));

	bool bInBlockComment = false;
	bool bHasGeneratedBody = false;
	int32 GeneratedBodyLine = 0;

	int32 LastIncludeLine = 0;
	FString LastIncludePath;
	int32 GeneratedHIncludeLine = 0;
	FString GeneratedHIncludePath;   // the ACTUAL *.generated.h include (NOT the last include — fixes rule-c false positive)

	struct FReflectedType { int32 MacroLine = 0; FString MacroKind; FString DeclaredName; int32 DeclLine = 0; bool bHasApiMacro = false; };
	TArray<FReflectedType> ReflectedTypes;
	bool bAnyReflectedMacro = false;

	bool bPendingReflected = false;
	FString PendingKind;
	int32 PendingMacroLine = 0;

	// Regex (LOCALS only — ICU init contract).
	const FRegexPattern IncludePattern(TEXT("^\\s*#\\s*include\\s+[\"<]([^\">]+)[\">]"));
	const FRegexPattern ClassDeclPattern(TEXT("^\\s*(?:class|struct)\\s+(?:[A-Z][A-Z0-9_]*_API\\s+)?([A-Za-z_][A-Za-z0-9_]*)"));
	const FRegexPattern ApiInDeclPattern(TEXT("\\b([A-Z][A-Z0-9_]*_API)\\b"));
	const FRegexPattern UClassSpecifierPattern(TEXT("^\\s*U(?:CLASS|STRUCT|ENUM|INTERFACE|PROPERTY|FUNCTION)\\s*\\(([^)]*)\\)"));

	for (int32 i = 0; i < Lines.Num(); ++i)
	{
		const FString Scan = StripBlockComments(Lines[i], bInBlockComment);
		const FString Line = StripComment(Scan);
		const FString Trimmed = Line.TrimStartAndEnd();
		if (Trimmed.IsEmpty()) { continue; }

		// #include tracking.
		{
			FRegexMatcher Mt(IncludePattern, Line);
			if (Mt.FindNext())
			{
				const FString Inc = Mt.GetCaptureGroup(1);
				LastIncludeLine = i + 1;
				LastIncludePath = Inc;
				if (Inc.EndsWith(TEXT(".generated.h")))
				{
					GeneratedHIncludeLine = i + 1;
					GeneratedHIncludePath = Inc;
				}
				continue;
			}
		}

		if (Trimmed.Contains(TEXT("GENERATED_BODY")) || Trimmed.Contains(TEXT("GENERATED_UCLASS_BODY")))
		{
			bHasGeneratedBody = true;
			if (GeneratedBodyLine == 0) { GeneratedBodyLine = i + 1; }
		}

		if (Trimmed.StartsWith(TEXT("UCLASS")) || Trimmed.StartsWith(TEXT("USTRUCT")) ||
			Trimmed.StartsWith(TEXT("UENUM")) || Trimmed.StartsWith(TEXT("UINTERFACE")))
		{
			bAnyReflectedMacro = true;
			if (Trimmed.StartsWith(TEXT("UCLASS")))
			{
				bPendingReflected = true;
				PendingKind = TEXT("UCLASS");
				PendingMacroLine = i + 1;
			}
		}

		if (bPendingReflected)
		{
			FRegexMatcher Mt(ClassDeclPattern, Line);
			if (Mt.FindNext())
			{
				FReflectedType RT;
				RT.MacroLine = PendingMacroLine;
				RT.MacroKind = PendingKind;
				RT.DeclaredName = Mt.GetCaptureGroup(1);
				RT.DeclLine = i + 1;
				FRegexMatcher ApiMt(ApiInDeclPattern, Line);
				RT.bHasApiMacro = ApiMt.FindNext();
				ReflectedTypes.Add(RT);
				bPendingReflected = false;
			}
		}

		// Invalid-specifier cross-check (rule f) — only when a vocabulary is supplied.
		if (ValidSpecifiers.Num() > 0)
		{
			FRegexMatcher SpecMt(UClassSpecifierPattern, Line);
			if (SpecMt.FindNext())
			{
				const FString SpecBlob = SpecMt.GetCaptureGroup(1);
				TArray<FString> Tokens;
				SpecBlob.ParseIntoArray(Tokens, TEXT(","), /*InCullEmpty=*/true);
				for (FString Tok : Tokens)
				{
					Tok = Tok.TrimStartAndEnd();
					int32 Cut = INDEX_NONE;
					if (Tok.FindChar(TEXT('='), Cut)) Tok = Tok.Left(Cut).TrimStartAndEnd();
					if (Tok.FindChar(TEXT('('), Cut)) Tok = Tok.Left(Cut).TrimStartAndEnd();
					if (Tok.IsEmpty()) continue;
					bool bIdent = true;
					for (const TCHAR C : Tok) { if (!FChar::IsAlnum(C) && C != TEXT('_')) { bIdent = false; break; } }
					if (!bIdent) continue;
					if (!ValidSpecifiers.Contains(Tok))
					{
						FLintFinding F;
						F.RuleId = TEXT("invalid_specifier");
						F.Line = i + 1;
						F.Message = FString::Printf(TEXT("Unknown specifier token '%s' (not in the cppreflect class-specifier vocabulary)."), *Tok);
						F.Severity = TEXT("warning");
						Findings.Add(F);
					}
				}
			}
		}
	}

	// --- Rule (a): GENERATED_BODY presence (only meaningful for a reflected type). ---
	if (bAnyReflectedMacro && !bHasGeneratedBody)
	{
		FLintFinding F;
		F.RuleId = TEXT("missing_generated_body");
		F.Line = ReflectedTypes.Num() > 0 ? ReflectedTypes[0].DeclLine : 0;
		F.Message = TEXT("Reflected type (UCLASS/USTRUCT) is missing a GENERATED_BODY() macro.");
		F.Severity = TEXT("error");
		Findings.Add(F);
	}

	// --- Rule (b): *.generated.h must be the LAST include. ---
	if (GeneratedHIncludeLine != 0 && LastIncludeLine != 0 && GeneratedHIncludeLine != LastIncludeLine)
	{
		FLintFinding F;
		F.RuleId = TEXT("generated_h_not_last");
		F.Line = GeneratedHIncludeLine;
		F.Message = FString::Printf(
			TEXT("'*.generated.h' must be the LAST #include (an include at line %d follows it: \"%s\")."),
			LastIncludeLine, *LastIncludePath);
		F.Severity = TEXT("error");
		Findings.Add(F);
	}
	else if (bAnyReflectedMacro && bHasGeneratedBody && GeneratedHIncludeLine == 0)
	{
		FLintFinding F;
		F.RuleId = TEXT("missing_generated_h_include");
		F.Line = GeneratedBodyLine;
		F.Message = TEXT("Reflected type uses GENERATED_BODY() but no '*.generated.h' include is present (must be last).");
		F.Severity = TEXT("error");
		Findings.Add(F);
	}

	// --- Rule (d): missing <MODULE>_API on each UCLASS-declared type. ---
	const FString HeaderBaseName = FPaths::GetBaseFilename(FilePath);
	for (const FReflectedType& RT : ReflectedTypes)
	{
		if (!ExpectedApiMacro.IsEmpty() && !RT.bHasApiMacro)
		{
			FLintFinding F;
			F.RuleId = TEXT("missing_api_macro");
			F.Line = RT.DeclLine;
			F.Message = FString::Printf(
				TEXT("UCLASS-declared type '%s' is missing the '%s' export macro (class %s ...)."),
				*RT.DeclaredName, *ExpectedApiMacro, *RT.DeclaredName);
			F.Severity = TEXT("warning");
			Findings.Add(F);
		}
	}

	// --- Rule (c): *.generated.h base-name vs header file base-name mismatch. ---
	// Use the ACTUAL generated.h include path (GeneratedHIncludePath), NOT the last
	// include — when generated.h is not last (rule-b case) the last include is some
	// other header and would fire a bogus mismatch. Gate on the captured include
	// actually ending in `.generated.h`.
	if (GeneratedHIncludeLine != 0 && !HeaderBaseName.IsEmpty() &&
		GeneratedHIncludePath.EndsWith(TEXT(".generated.h")))
	{
		FString GenBase = FPaths::GetCleanFilename(GeneratedHIncludePath);
		GenBase.LeftChopInline(FCString::Strlen(TEXT(".generated.h")));
		if (!GenBase.IsEmpty() && GenBase != HeaderBaseName)
		{
			FLintFinding F;
			F.RuleId = TEXT("generated_h_name_mismatch");
			F.Line = GeneratedHIncludeLine;
			F.Message = FString::Printf(
				TEXT("'%s.generated.h' does not match the header file name '%s.h' — the GENERATED_BODY pairing requires \"%s.generated.h\"."),
				*GenBase, *HeaderBaseName, *HeaderBaseName);
			F.Severity = TEXT("error");
			Findings.Add(F);
		}
	}

	// --- Rule (e): UPROPERTY/UFUNCTION in a file with NO reflected type. ---
	if (!bAnyReflectedMacro)
	{
		bInBlockComment = false;
		for (int32 i = 0; i < Lines.Num(); ++i)
		{
			const FString Scan = StripBlockComments(Lines[i], bInBlockComment);
			const FString Trimmed = StripComment(Scan).TrimStartAndEnd();
			if (Trimmed.StartsWith(TEXT("UPROPERTY")) || Trimmed.StartsWith(TEXT("UFUNCTION")))
			{
				FLintFinding F;
				F.RuleId = TEXT("reflected_member_in_non_reflected_type");
				F.Line = i + 1;
				F.Message = TEXT("UPROPERTY/UFUNCTION found but the file declares no reflected type (UCLASS/USTRUCT) — the macro will not be processed by UHT.");
				F.Severity = TEXT("error");
				Findings.Add(F);
			}
		}
	}

	// Stable, deterministic order (tests + offline parity).
	Findings.Sort([](const FLintFinding& A, const FLintFinding& B)
	{
		if (A.Line != B.Line) return A.Line < B.Line;
		return A.RuleId < B.RuleId;
	});
	return Findings;
}

FMonolithActionResult FMonolithSourceActions::HandleLintHeader(const TSharedPtr<FJsonObject>& Params)
{
	const FString FilePath = Params->GetStringField(TEXT("file_path"));
	if (FilePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'file_path' is required."));
	}

	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *FilePath))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Could not read header file: %s"), *FilePath));
	}

	// Optional valid-specifier vocabulary cross-check (rule f). Resolve from the RI
	// cppreflect list_class_specifiers action when registered; degrade gracefully
	// (empty set => the specifier rule is skipped) when RI is unavailable.
	TSet<FString> ValidSpecifiers;
	{
		FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();
		if (Registry.HasAction(TEXT("source"), TEXT("list_class_specifiers")))
		{
			TSharedPtr<FJsonObject> SpecParams = MakeShared<FJsonObject>();
			FMonolithActionResult SpecRes = Registry.ExecuteAction(TEXT("source"), TEXT("list_class_specifiers"), SpecParams);
			if (SpecRes.bSuccess && SpecRes.Result.IsValid())
			{
				const TArray<TSharedPtr<FJsonValue>>* SpecArr = nullptr;
				if (SpecRes.Result->TryGetArrayField(TEXT("specifiers"), SpecArr) && SpecArr)
				{
					for (const TSharedPtr<FJsonValue>& V : *SpecArr)
					{
						if (!V.IsValid()) continue;
						FString S;
						if (V->TryGetString(S)) { if (!S.IsEmpty()) ValidSpecifiers.Add(S); continue; }
						const TSharedPtr<FJsonObject>* Obj = nullptr;
						if (V->TryGetObject(Obj) && Obj && Obj->IsValid())
						{
							FString Name;
							if ((*Obj)->TryGetStringField(TEXT("name"), Name) || (*Obj)->TryGetStringField(TEXT("specifier"), Name))
							{
								if (!Name.IsEmpty()) ValidSpecifiers.Add(Name);
							}
						}
					}
				}
			}
		}
	}

	const TArray<FLintFinding> Findings = LintHeaderLines(FilePath, Lines, ValidSpecifiers);

	auto ResultObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> FindingArr;
	TArray<FString> TextLines;
	for (const FLintFinding& F : Findings)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("rule_id"), F.RuleId);
		Obj->SetNumberField(TEXT("line"), F.Line);
		Obj->SetStringField(TEXT("message"), F.Message);
		Obj->SetStringField(TEXT("severity"), F.Severity);
		FindingArr.Add(MakeShared<FJsonValueObject>(Obj));
		TextLines.Add(FString::Printf(TEXT("[%s] L%d (%s): %s"), *F.Severity, F.Line, *F.RuleId, *F.Message));
	}
	ResultObj->SetArrayField(TEXT("findings"), FindingArr);
	ResultObj->SetNumberField(TEXT("finding_count"), Findings.Num());

	const FString Text = Findings.Num() == 0
		? TEXT("Clean -- no lint findings.")
		: FString::Join(TextLines, TEXT("\n"));

	TArray<TSharedPtr<FJsonValue>> LintContentArr;
	auto LintContentItem = MakeShared<FJsonObject>();
	LintContentItem->SetStringField(TEXT("type"), TEXT("text"));
	LintContentItem->SetStringField(TEXT("text"), Text);
	LintContentArr.Add(MakeShared<FJsonValueObject>(LintContentItem));
	ResultObj->SetArrayField(TEXT("content"), LintContentArr);
	return FMonolithActionResult::Success(ResultObj);
}

// ============================================================================
// Phase 3 — item 9: generate_class_stub
//
// TEXT-RETURN-ONLY (Decision 1): templates a UCLASS-derived .h/.cpp pair and
// NEVER writes to disk. Resolves the parent header + owning module via the DB.
// Plain default constructor unless the parent's indexed constructor signature
// requires FObjectInitializer&. UCLASS-derived parents ONLY (v1).
// ============================================================================

void FMonolithSourceActions::GenerateClassStubText(
	const FString& ParentClass, const FString& ClassName, const FString& Module,
	const FString& ParentHeaderInclude, bool bParentNeedsObjectInitializer,
	FString& OutHeaderText, FString& OutCppText)
{
	const FString ApiMacro = Module.ToUpper() + TEXT("_API");
	// UE "Add C++ Class" file-naming convention: the U/A UCLASS-derived prefix is
	// dropped from the FILE names (class UMyComp -> MyComp.h / MyComp.cpp /
	// MyComp.generated.h). class_name is already validated UCLASS-derived, so only a
	// leading U/A followed by an uppercase letter is stripped; otherwise the raw name
	// is used. The C++ class identifier (ClassName) is unchanged — only file names strip.
	const FString FileBase = (ClassName.Len() >= 2 &&
		(ClassName[0] == TEXT('U') || ClassName[0] == TEXT('A')) && FChar::IsUpper(ClassName[1]))
		? ClassName.RightChop(1)
		: ClassName;
	const FString GeneratedInclude = FileBase + TEXT(".generated.h");

	// --- Header ---
	{
		TArray<FString> H;
		H.Add(TEXT("#pragma once"));
		H.Add(TEXT(""));
		H.Add(TEXT("#include \"CoreMinimal.h\""));
		if (!ParentHeaderInclude.IsEmpty())
		{
			H.Add(FString::Printf(TEXT("#include \"%s\""), *ParentHeaderInclude));
		}
		H.Add(FString::Printf(TEXT("#include \"%s\""), *GeneratedInclude)); // ALWAYS last (prefix-stripped file base)
		H.Add(TEXT(""));
		H.Add(TEXT("UCLASS()"));
		H.Add(FString::Printf(TEXT("class %s %s : public %s"), *ApiMacro, *ClassName, *ParentClass));
		H.Add(TEXT("{"));
		H.Add(TEXT("\tGENERATED_BODY()"));
		H.Add(TEXT(""));
		H.Add(TEXT("public:"));
		if (bParentNeedsObjectInitializer)
		{
			H.Add(FString::Printf(TEXT("\t%s(const FObjectInitializer& ObjectInitializer);"), *ClassName));
		}
		else
		{
			H.Add(FString::Printf(TEXT("\t%s();"), *ClassName));
		}
		H.Add(TEXT("};"));
		H.Add(TEXT(""));
		OutHeaderText = FString::Join(H, TEXT("\n"));
	}

	// --- Cpp ---
	{
		TArray<FString> C;
		C.Add(FString::Printf(TEXT("#include \"%s.h\""), *FileBase)); // prefix-stripped file base
		C.Add(TEXT(""));
		if (bParentNeedsObjectInitializer)
		{
			C.Add(FString::Printf(TEXT("%s::%s(const FObjectInitializer& ObjectInitializer)"), *ClassName, *ClassName));
			C.Add(TEXT("\t: Super(ObjectInitializer)"));
			C.Add(TEXT("{"));
			C.Add(TEXT("}"));
		}
		else
		{
			C.Add(FString::Printf(TEXT("%s::%s()"), *ClassName, *ClassName));
			C.Add(TEXT("{"));
			C.Add(TEXT("}"));
		}
		C.Add(TEXT(""));
		OutCppText = FString::Join(C, TEXT("\n"));
	}
}

FMonolithActionResult FMonolithSourceActions::HandleGenerateClassStub(const TSharedPtr<FJsonObject>& Params)
{
	FMonolithSourceDatabase* DB = GetDB();
	if (!DB || !DB->IsOpen())
	{
		return FMonolithActionResult::Error(TEXT("Engine source DB not available. Run source.trigger_reindex first."));
	}

	const FString ParentClass = Params->GetStringField(TEXT("parent"));
	const FString ClassName = Params->GetStringField(TEXT("class_name"));
	const FString Module = Params->GetStringField(TEXT("module"));
	if (ParentClass.IsEmpty() || ClassName.IsEmpty() || Module.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("'parent', 'class_name', and 'module' are all required."));
	}

	// Resolve the parent's class row. UCLASS-derived parents ONLY (v1).
	TArray<FMonolithSourceSymbol> ParentRows = DB->GetSymbolsByName(ParentClass);
	if (ParentRows.Num() == 0) ParentRows = DB->SearchSymbolsFTS(ParentClass, 5);
	if (ParentRows.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Parent class '%s' not found in the source index. Run source.trigger_reindex if it is a project type."), *ParentClass));
	}

	const FMonolithSourceSymbol* ParentSym = nullptr;
	for (const FMonolithSourceSymbol& S : ParentRows)
	{
		if (S.Kind == TEXT("class") || S.Kind == TEXT("struct")) { ParentSym = &S; break; }
	}
	if (!ParentSym) { ParentSym = &ParentRows[0]; }

	// UCLASS-derived gate: U/A prefix is the engine convention; also accept the
	// indexed is_ue_macro flag.
	const bool bLooksUClass = ParentSym->bIsUEMacro
		|| ParentClass.StartsWith(TEXT("U")) || ParentClass.StartsWith(TEXT("A"));
	if (!bLooksUClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Parent '%s' is not a UCLASS-derived type. generate_class_stub v1 supports UCLASS-derived parents only (no USTRUCT/UENUM/UINTERFACE)."), *ParentClass));
	}

	// Resolve the parent header include via the owning header (prefer a .h row).
	const FMonolithSourceSymbol* HeaderSym = ParentSym;
	for (const FMonolithSourceSymbol& S : ParentRows)
	{
		if (DB->GetFilePath(S.FileId).EndsWith(TEXT(".h"))) { HeaderSym = &S; break; }
	}
	const FString ParentFilePath = DB->GetFilePath(HeaderSym->FileId);
	bool bIncludable = true;
	FString IncWarning;
	const FString ParentInclude = DeriveIncludePath(ParentFilePath, bIncludable, IncWarning);

	// Constructor convention: plain default unless the parent's indexed ctor signature
	// requires FObjectInitializer& (and has no plain alternative).
	bool bParentNeedsObjectInitializer = false;
	{
		TArray<FMonolithSourceSymbol> CtorRows = DB->GetSymbolsByName(ParentClass, TEXT("function"));
		bool bSawAnyCtor = false;
		bool bSawPlainCtor = false;
		bool bSawObjInitCtor = false;
		for (const FMonolithSourceSymbol& S : CtorRows)
		{
			if (S.Signature.IsEmpty()) continue;
			if (!S.Signature.Contains(ParentClass + TEXT("("))) continue;
			bSawAnyCtor = true;
			if (S.Signature.Contains(TEXT("FObjectInitializer"))) bSawObjInitCtor = true;
			else bSawPlainCtor = true;
		}
		bParentNeedsObjectInitializer = bSawAnyCtor && bSawObjInitCtor && !bSawPlainCtor;
	}

	FString HeaderText, CppText;
	GenerateClassStubText(ParentClass, ClassName, Module, ParentInclude, bParentNeedsObjectInitializer, HeaderText, CppText);

	// File-naming convention (mirrors GenerateClassStubText): the U/A UCLASS-derived
	// prefix is dropped from the FILE names. Report the intended file names so callers
	// know what to save the text as, and use them in the content banner.
	const FString FileBase = (ClassName.Len() >= 2 &&
		(ClassName[0] == TEXT('U') || ClassName[0] == TEXT('A')) && FChar::IsUpper(ClassName[1]))
		? ClassName.RightChop(1)
		: ClassName;
	const FString HeaderFile = FileBase + TEXT(".h");
	const FString CppFile = FileBase + TEXT(".cpp");

	auto ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("header"), HeaderText);
	ResultObj->SetStringField(TEXT("cpp"), CppText);
	ResultObj->SetStringField(TEXT("header_file"), HeaderFile);
	ResultObj->SetStringField(TEXT("cpp_file"), CppFile);
	ResultObj->SetStringField(TEXT("parent_include"), ParentInclude);
	ResultObj->SetStringField(TEXT("api_macro"), Module.ToUpper() + TEXT("_API"));
	ResultObj->SetBoolField(TEXT("uses_object_initializer"), bParentNeedsObjectInitializer);

	const FString Text = FString::Printf(
		TEXT("// === %s ===\n%s\n// === %s ===\n%s"),
		*HeaderFile, *HeaderText, *CppFile, *CppText);

	TArray<TSharedPtr<FJsonValue>> StubContentArr;
	auto StubContentItem = MakeShared<FJsonObject>();
	StubContentItem->SetStringField(TEXT("type"), TEXT("text"));
	StubContentItem->SetStringField(TEXT("text"), Text);
	StubContentArr.Add(MakeShared<FJsonValueObject>(StubContentItem));
	ResultObj->SetArrayField(TEXT("content"), StubContentArr);
	return FMonolithActionResult::Success(ResultObj);
}
