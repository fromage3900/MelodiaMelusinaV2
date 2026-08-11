// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// FModuleDepRealityAdapter — implementation.
//
// Catches the bug class documented in `feedback_softptr_uproperty_needs_module_dep.md`:
// when a header references `UClassFromOtherModule` (e.g. `TSoftObjectPtr<UMyClass>`)
// but the module's Build.cs does NOT list the owning module in
// PrivateDependencyModuleNames, UHT emits valid generated code but LINK fails
// with LNK2019 against Z_Construct_UClass_UMyClass_NoRegister. The audit
// surfaces these mismatches BEFORE the link step.
//
// Heuristic catch-rate is intentional — exact catch requires UHT-driven full
// reflection traversal (Phase 3 work). Phase 2's regex sweep catches the common
// case: a header's class-name identifier that resolves to a known engine /
// project module.

#include "SourceAudit/FModuleDepRealityAdapter.h"
#include "MonolithReflectionIntelModule.h"
#include "MonolithSourceSubsystem.h"
#include "MonolithSourceDatabase.h"
#include "Shared/RICursorCodec.h"
#include "Shared/RIPathUtils.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "Internationalization/Regex.h"
#include "Misc/Base64.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "SQLiteDatabase.h"
#include "Templates/TypeHash.h"

namespace
{
	// Cursor codec hoisted to Private/Shared/RICursorCodec.{h,cpp} to avoid
	// unity-build collisions across the six query adapters. See that header for
	// rationale. Wire format / behaviour unchanged. (This adapter never defined
	// a ComputeFilterHash.)

	/** Implicit-in-every-UE-module deps that never need to be listed explicitly. */
	const TSet<FString>& ImplicitModules()
	{
		static const TSet<FString> Set = {
			TEXT("Core"), TEXT("CoreUObject"), TEXT("Engine"),
			TEXT("Projects"),     // IPluginManager / IPlugin — used by this audit module itself
			TEXT("RHI"),          // FRHICommandList et al — near-universal in render-touching code
			TEXT("RenderCore"),   // FRenderResource et al — near-universal companion to RHI
			// Self-reference is not a dep — handled separately.
		};
		return Set;
	}

	/** Visitor that collects file paths whose name matches a predicate. */
	class FMatchingFileVisitor : public IPlatformFile::FDirectoryVisitor
	{
	public:
		TArray<FString>& Out;
		TFunction<bool(const FString&)> Pred;
		FMatchingFileVisitor(TArray<FString>& InOut, TFunction<bool(const FString&)> InPred)
			: Out(InOut), Pred(MoveTemp(InPred)) {}
		virtual bool Visit(const TCHAR* FilenameOrDirectory, bool bIsDirectory) override
		{
			if (!bIsDirectory)
			{
				const FString Path(FilenameOrDirectory);
				if (Pred(Path)) { Out.Add(Path); }
			}
			return true;
		}
	};

	struct FBuildCsModule
	{
		FString ModuleName;     // Build.cs class name (== module name)
		FString ModuleDir;      // Source/<Module>/ — root dir we walk for .h/.cpp
		FString BuildCsPath;    // full path to <Module>.Build.cs
		TSet<FString> DeclaredDeps;   // Public + Private DependencyModuleNames union
	};

	// ToProjectRelative hoisted to Private/Shared/RIPathUtils.{h,cpp}
	// (RIToProjectRelative) to avoid unity-build collisions across the three
	// indexers that carried a byte-identical copy. Behaviour unchanged.

	/**
	 * Replace C# `//` line comments and `/* ... *​/` block comments with a single
	 * space each (preserving overall token boundaries), so a later regex sweep over
	 * the dependency arrays is not derailed by parentheses / quoted strings that
	 * appear INSIDE comments. String-literal aware: a `//` or `/*` inside a "..."
	 * string is NOT treated as a comment. Newlines inside replaced regions collapse
	 * to a space — line numbers are not needed by the dep sweep.
	 */
	FString StripCSharpComments(const FString& In)
	{
		FString Out;
		Out.Reserve(In.Len());
		const int32 N = In.Len();
		bool bInString = false;   // inside "..."
		bool bInChar = false;     // inside '...'
		for (int32 i = 0; i < N; ++i)
		{
			const TCHAR C = In[i];
			const TCHAR Next = (i + 1 < N) ? In[i + 1] : TEXT('\0');

			if (bInString)
			{
				Out.AppendChar(C);
				if (C == TEXT('\\') && Next != TEXT('\0')) { Out.AppendChar(Next); ++i; }
				else if (C == TEXT('"')) { bInString = false; }
				continue;
			}
			if (bInChar)
			{
				Out.AppendChar(C);
				if (C == TEXT('\\') && Next != TEXT('\0')) { Out.AppendChar(Next); ++i; }
				else if (C == TEXT('\'')) { bInChar = false; }
				continue;
			}

			// Line comment — skip to end of line, emit one space.
			if (C == TEXT('/') && Next == TEXT('/'))
			{
				while (i < N && In[i] != TEXT('\n')) { ++i; }
				Out.AppendChar(TEXT(' '));
				if (i < N) { Out.AppendChar(TEXT('\n')); } // keep the newline boundary
				continue;
			}
			// Block comment — skip to closing, emit one space.
			if (C == TEXT('/') && Next == TEXT('*'))
			{
				i += 2;
				while (i + 1 < N && !(In[i] == TEXT('*') && In[i + 1] == TEXT('/'))) { ++i; }
				i += 1; // land on the '/'; loop's ++i steps past it
				Out.AppendChar(TEXT(' '));
				continue;
			}

			if (C == TEXT('"'))  { bInString = true; Out.AppendChar(C); continue; }
			if (C == TEXT('\'')) { bInChar = true;   Out.AppendChar(C); continue; }
			Out.AppendChar(C);
		}
		return Out;
	}

	/**
	 * Parse a `.Build.cs` file and extract:
	 *   - The module name (from the class name: `public class <Name> : ModuleRules`).
	 *   - The union of identifiers passed to PublicDependencyModuleNames.Add /
	 *     .AddRange and PrivateDependencyModuleNames.Add / .AddRange.
	 *
	 * Both Add("X") and AddRange(new string[] { "X", "Y" }) forms are matched.
	 * Whitespace + line breaks inside AddRange arrays are accepted.
	 */
	bool ParseBuildCs(const FString& AbsPath, FBuildCsModule& Out,
		const FRegexPattern& ClassPattern,
		const FRegexPattern& DepStringPattern)
	{
		FString Text;
		if (!FFileHelper::LoadFileToString(Text, *AbsPath)) { return false; }

		// Module name — `public class <Name> : ModuleRules`
		{
			FRegexMatcher M(ClassPattern, Text);
			if (M.FindNext())
			{
				Out.ModuleName = M.GetCaptureGroup(1);
			}
		}
		if (Out.ModuleName.IsEmpty())
		{
			// Fallback: filename basename strips `.Build`.
			FString Base = FPaths::GetBaseFilename(AbsPath);
			Base.RemoveFromEnd(TEXT(".Build"), ESearchCase::IgnoreCase);
			Out.ModuleName = Base;
		}

		Out.BuildCsPath = AbsPath;
		Out.ModuleDir = FPaths::GetPath(AbsPath);

		// STRIP C# comments before the dep sweep. A `//` or `/* */` comment inside
		// the AddRange array legitimately contains parentheses — e.g.
		//   // (AIMODULE_API). Stock-engine module...
		// The non-greedy `(...)` site capture below terminates at the FIRST `)`,
		// so an un-stripped comment-paren truncated the captured body and silently
		// dropped every dependency declared AFTER it (observed: EnhancedInput / UMG /
		// MaterialEditor reported missing though declared). Removing comments first
		// makes the first `)` the array's real terminator AND prevents commented-out
		// `"FakeDep"` strings from counting as declared. Replace each comment with a
		// single space so token boundaries + the `(Public|Private)...` keyword stay
		// intact. Build.cs files contain no `//`-in-string-literal cases that matter.
		const FString CommentFreeText = StripCSharpComments(Text);

		// Sweep all "Public|PrivateDependencyModuleNames" sites and extract the
		// quoted-string-literal arguments contained within. The DepStringPattern
		// is intentionally permissive — it matches every `"Identifier"` quoted
		// string that appears between the relevant `.Add(`/`.AddRange(` keyword
		// and the next `)`. Two regex passes: first locate each dep-name-list site,
		// then extract quoted strings from its body.
		const FRegexPattern SitePattern(
			TEXT("(Public|Private)DependencyModuleNames\\s*\\.\\s*(?:Add|AddRange)\\s*\\(([\\s\\S]*?)\\)"));
		FRegexMatcher SiteM(SitePattern, CommentFreeText);
		while (SiteM.FindNext())
		{
			const FString Body = SiteM.GetCaptureGroup(2);
			FRegexMatcher StringM(DepStringPattern, Body);
			while (StringM.FindNext())
			{
				const FString Captured = StringM.GetCaptureGroup(1).TrimStartAndEnd();
				if (!Captured.IsEmpty() && Captured.Len() < 128)
				{
					Out.DeclaredDeps.Add(Captured);
				}
			}
		}

		return true;
	}

	/** True if `Path` is `<x>.Build.cs`. */
	bool IsBuildCs(const FString& Path)
	{
		return Path.EndsWith(TEXT(".Build.cs"), ESearchCase::IgnoreCase);
	}

	/**
	 * Path-first declaring-module resolution (item 6). Parse `Source/<Module>/...`
	 * out of a file path (handles both `Source/<Module>/` and
	 * `Plugins/<X>/Source/<Module>/` — the LAST `/Source/` wins, so the innermost
	 * module dir is taken). Returns the module name + the `Source/<Module>/` dir.
	 * Does NOT touch the DB — works on uncommitted/unindexed files.
	 */
	bool DeriveDeclaringModule(const FString& FilePath, FString& OutModuleName, FString& OutModuleDir)
	{
		OutModuleName.Empty();
		OutModuleDir.Empty();

		FString Norm = FilePath;
		Norm.ReplaceInline(TEXT("\\"), TEXT("/"));

		const int32 SrcIdx = Norm.Find(TEXT("/Source/"), ESearchCase::IgnoreCase, ESearchDir::FromEnd);
		if (SrcIdx == INDEX_NONE) { return false; }

		const int32 AfterSrc = SrcIdx + 8; // past "/Source/"
		FString Rest = Norm.Mid(AfterSrc);
		int32 NextSlash = INDEX_NONE;
		if (!Rest.FindChar(TEXT('/'), NextSlash)) { return false; }

		OutModuleName = Rest.Left(NextSlash);
		if (OutModuleName.IsEmpty()) { return false; }

		// Module dir is the native form up through `Source/<Module>`.
		OutModuleDir = FilePath.Left(AfterSrc + NextSlash);
		return true;
	}

	/**
	 * Locate the `<Module>.Build.cs` for a declaring module dir. Prefer the exact
	 * `<ModuleDir>/<Module>.Build.cs`; fall back to a recursive search under the
	 * module dir (some modules keep the .Build.cs in a subfolder). Returns empty
	 * when not found (an uncommitted module with no Build.cs yet).
	 */
	FString FindBuildCsForModule(const FString& ModuleDir, const FString& ModuleName)
	{
		const FString Direct = ModuleDir / (ModuleName + TEXT(".Build.cs"));
		if (FPaths::FileExists(Direct)) { return Direct; }

		IPlatformFile& Pf = FPlatformFileManager::Get().GetPlatformFile();
		if (!Pf.DirectoryExists(*ModuleDir)) { return FString(); }

		TArray<FString> Found;
		const FString Target = ModuleName + TEXT(".Build.cs");
		FMatchingFileVisitor V(Found, [&Target](const FString& P)
		{
			return FPaths::GetCleanFilename(P).Equals(Target, ESearchCase::IgnoreCase);
		});
		IFileManager::Get().IterateDirectoryRecursively(*ModuleDir, V);
		return Found.Num() > 0 ? Found[0] : FString();
	}

	/** True if `Path` is a C++ source / header file under a module dir. */
	bool IsCppSource(const FString& Path)
	{
		const FString Lower = Path.ToLower();
		return Lower.EndsWith(TEXT(".h")) || Lower.EndsWith(TEXT(".hpp")) ||
			   Lower.EndsWith(TEXT(".cpp")) || Lower.EndsWith(TEXT(".inl"));
	}
}

// ============================================================================
// Registration
// ============================================================================

void FModuleDepRealityAdapter::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("source"), TEXT("audit_module_dep_reality"),
		TEXT("Audit: find UE type references in .h/.cpp files whose declaring "
		     "module is NOT listed in the file's owning module's Build.cs "
		     "PrivateDependencyModuleNames/PublicDependencyModuleNames. Catches "
		     "the `softptr_uproperty_needs_module_dep` bug class — UPROPERTY "
		     "edits referencing a cross-module class without the corresponding "
		     "Build.cs dep, which UHT accepts but linker rejects with LNK2019. "
		     "Heuristic regex sweep; misses macro-typedef cases. Read-only. "
		     "Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FModuleDepRealityAdapter::HandleAuditModuleDepReality),
		FParamSchemaBuilder()
			.OptionalDiskPath(TEXT("scan_root"),
				TEXT("Optional directory to limit scan (default: project Source/ + Plugins/*/Source/)"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// Item 6 (Phase 2): forward direction — given a file (uncommitted-OK) or a
	// symbol list, report the modules the file/symbols require + which are missing
	// from the declaring module's Build.cs deps.
	Registry.RegisterAction(TEXT("source"), TEXT("suggest_build_cs_deps"),
		TEXT("Suggest Build.cs PrivateDependencyModuleNames for a file (or symbol list). "
		     "Resolves the declaring module path-first from `file_path` "
		     "(Source/<Module>/... or Plugins/<X>/Source/<Module>/...), reads its "
		     "<Module>.Build.cs from DISK (works on uncommitted files), extracts the "
		     "UE types used, resolves each type's owning module via the source index, "
		     "and returns required_modules[] + missing[] (deps not yet declared). "
		     "Forward direction of audit_module_dep_reality; same regex heuristic + "
		     "implicit Core/CoreUObject/Engine whitelist. Read-only."),
		FMonolithActionHandler::CreateStatic(&FModuleDepRealityAdapter::HandleSuggestBuildCsDeps),
		FParamSchemaBuilder()
			// `file_path` is `Other` (a plain string), NOT DiskPath, on purpose. The
			// DiskPath kind emits a "paths in this index are stored with forward
			// slashes, so a query for '<x>' will likely return ZERO results" warning —
			// correct for actions that key the SQLite index BY PATH, but FALSE here:
			// this handler uses file_path only for (1) on-disk reads (the file + its
			// <Module>.Build.cs, which accept backslashes fine on Windows) and (2)
			// path-string module derivation. The DB is queried by TYPE NAME, never by
			// path — so a backslash path resolves perfectly and the DiskPath warning
			// was spurious. `Other` passes the value through untouched (no rewrite,
			// no false warning); the handler normalises internally as needed.
			.Optional(TEXT("file_path"), TEXT("string"),
				TEXT("Path to a .h/.cpp file whose declaring module's Build.cs deps to audit (forward or back slashes both work)"))
			.Optional(TEXT("symbols"), TEXT("array"),
				TEXT("Optional explicit list of UE type names (used instead of/with file extraction)"))
			.Build());

	Registry.SetActionAnnotations(TEXT("source"), TEXT("suggest_build_cs_deps"),
		/*bReadOnly=*/true, /*bDestructive=*/false, /*bIdempotent=*/true, TEXT("Suggest Build.cs deps"));

	// We do NOT re-set the `source` dispatcher annotation here — MonolithSource
	// owns the dispatcher-level read-only/idempotent flags. Adding this action
	// preserves the existing annotation because it's set by SetDispatcherAnnotations
	// on the namespace as a whole.
}

// ============================================================================
// DB accessor
// ============================================================================

FSQLiteDatabase* FModuleDepRealityAdapter::GetRawDB()
{
	FMonolithReflectionIntelModule* Module =
		FModuleManager::GetModulePtr<FMonolithReflectionIntelModule>(
			TEXT("MonolithReflectionIntel"));
	if (!Module) { return nullptr; }
	return Module->GetOrOpenCachedQueryDb();
}

FMonolithSourceDatabase* FModuleDepRealityAdapter::GetSharedSourceDb()
{
	// Game-thread only — GEditor + editor subsystems must be touched on the game
	// thread (the handlers all ensure(IsInGameThread())). Mirrors the module's own
	// GetSharedSourceDatabase() resolution path.
	if (!GEditor) { return nullptr; }
	UMonolithSourceSubsystem* SourceSS = GEditor->GetEditorSubsystem<UMonolithSourceSubsystem>();
	return SourceSS ? SourceSS->GetDatabase() : nullptr;
}

// ============================================================================
// Handler
// ============================================================================

FMonolithActionResult FModuleDepRealityAdapter::HandleAuditModuleDepReality(const TSharedPtr<FJsonObject>& Params)
{
	ensure(IsInGameThread());

	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString ScanRoot = Params->HasField(TEXT("scan_root"))
		? Params->GetStringField(TEXT("scan_root")) : FString();
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = HashCombine(GetTypeHash(ScanRoot), GetTypeHash(Limit));

	int32 Page = 0;
	if (!CursorIn.IsEmpty())
	{
		FRICursorState State;
		if (!DecodeRICursor(CursorIn, State))
		{
			return RIInvalidCursorError(TEXT("Cursor decode failed; restart pagination without `cursor`."));
		}
		if (State.QueryHash != FilterHash)
		{
			return RIInvalidCursorError(TEXT("Cursor filter mismatch; restart pagination without `cursor`."));
		}
		Page = State.Page;
	}

	const FString ProjectRoot =
		FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());

	// ----------------------------------------------------------------
	// Stage 1: locate all Build.cs files under the scan root(s).
	// ----------------------------------------------------------------
	TArray<FString> ScanRoots;
	if (!ScanRoot.IsEmpty())
	{
		FString Abs = ScanRoot;
		if (FPaths::IsRelative(Abs)) { Abs = FPaths::ConvertRelativePathToFull(ProjectRoot / Abs); }
		ScanRoots.Add(Abs);
	}
	else
	{
		ScanRoots.Add(ProjectRoot / TEXT("Source"));
		ScanRoots.Add(ProjectRoot / TEXT("Plugins"));
	}

	TArray<FString> AllBuildCs;
	{
		IPlatformFile& Pf = FPlatformFileManager::Get().GetPlatformFile();
		for (const FString& Root : ScanRoots)
		{
			if (!Pf.DirectoryExists(*Root)) { continue; }
			FMatchingFileVisitor V(AllBuildCs, IsBuildCs);
			IFileManager::Get().IterateDirectoryRecursively(*Root, V);
		}
	}

	// ----------------------------------------------------------------
	// Stage 2: parse each Build.cs.
	// Patterns hoisted out of the per-file loop — Phase 2 code-quality item 4.
	// ----------------------------------------------------------------
	const FRegexPattern ClassPattern(
		TEXT("public\\s+class\\s+(\\w+)\\s*:\\s*ModuleRules"));
	// Captures a quoted string literal — `"Identifier"`.
	const FRegexPattern DepStringPattern(
		TEXT("\"([A-Za-z_][A-Za-z0-9_]*)\""));
	// UE-prefixed identifier patterns. Captures `FFoo` / `UFoo` / `AFoo` / `IFoo` / `EFoo`.
	const FRegexPattern UeIdentPattern(
		TEXT("\\b([FUAEI][A-Z][A-Za-z0-9_]{2,})\\b"));

	TArray<FBuildCsModule> Modules;
	Modules.Reserve(AllBuildCs.Num());
	for (const FString& Path : AllBuildCs)
	{
		FBuildCsModule M;
		if (ParseBuildCs(Path, M, ClassPattern, DepStringPattern))
		{
			Modules.Add(MoveTemp(M));
		}
	}

	// ----------------------------------------------------------------
	// Stage 3: for each module, collect candidate symbols from its .h/.cpp.
	// ----------------------------------------------------------------
	struct FViolationRow
	{
		FString File;
		int32 Line = 0;
		FString Symbol;
		FString ExpectedModule;
		TArray<FString> CurrentlyListedModules;
	};
	TArray<FViolationRow> Violations;

	const TSet<FString>& Implicit = ImplicitModules();

	// Prepared statement for symbol → module lookup. Reused across the loop —
	// Phase 2 code-quality item 4 (statement reuse).
	FSQLitePreparedStatement SymStmt;
	if (!SymStmt.Create(*DB, TEXT(
		"SELECT m.name FROM symbols s "
		"JOIN files f ON f.id = s.file_id "
		"JOIN modules m ON m.id = f.module_id "
		"WHERE s.name = ? "
		"GROUP BY m.name;")))
	{
		return FMonolithActionResult::Error(
			TEXT("Symbol-resolution query prepare failed (symbols / files / modules tables absent?)."));
	}

	for (const FBuildCsModule& Mod : Modules)
	{
		IPlatformFile& Pf = FPlatformFileManager::Get().GetPlatformFile();
		if (!Pf.DirectoryExists(*Mod.ModuleDir)) { continue; }

		TArray<FString> SrcFiles;
		FMatchingFileVisitor V(SrcFiles, IsCppSource);
		IFileManager::Get().IterateDirectoryRecursively(*Mod.ModuleDir, V);

		// Sort for deterministic results — same files in same order across runs.
		SrcFiles.Sort();

		for (const FString& SrcFile : SrcFiles)
		{
			FString FileText;
			if (!FFileHelper::LoadFileToString(FileText, *SrcFile)) { continue; }

			TArray<FString> Lines;
			FileText.ParseIntoArrayLines(Lines, /*InCullEmpty=*/false);

			// Per-file dedup so a symbol used many times in one file only
			// reports once.
			TSet<FString> SeenInFile;

			for (int32 i = 0; i < Lines.Num(); ++i)
			{
				const FString& Line = Lines[i];
				// Skip lines that obviously cannot contribute a cross-module
				// type reference — comments and includes are noisy. This is
				// best-effort filtering, not a parser.
				const FString Trimmed = Line.TrimStartAndEnd();
				if (Trimmed.StartsWith(TEXT("//"))) { continue; }
				if (Trimmed.StartsWith(TEXT("#include"))) { continue; }

				FRegexMatcher M(UeIdentPattern, Line);
				while (M.FindNext())
				{
					const FString Candidate = M.GetCaptureGroup(1);
					if (Candidate.Len() < 4) { continue; }
					if (SeenInFile.Contains(Candidate)) { continue; }
					SeenInFile.Add(Candidate);

					// Resolve to a module via the symbols table.
					SymStmt.Reset();
					SymStmt.ClearBindings();
					SymStmt.SetBindingValueByIndex(1, Candidate);

					TArray<FString> ResolvedModules;
					while (SymStmt.Step() == ESQLitePreparedStatementStepResult::Row)
					{
						FString ModName;
						SymStmt.GetColumnValueByIndex(0, ModName);
						if (!ModName.IsEmpty()) { ResolvedModules.AddUnique(ModName); }
					}

					if (ResolvedModules.Num() == 0)
					{
						// Symbol unknown to the index — could be a local type,
						// an engine type the indexer missed, or a typo. Skip
						// to keep false-positive count low.
						continue;
					}
					if (ResolvedModules.Num() > 1)
					{
						// Ambiguous (e.g. a name colliding across modules) —
						// skip, false-positive risk too high without context.
						continue;
					}

					const FString& OwningModule = ResolvedModules[0];

					// Self-reference: not a cross-module dep.
					if (OwningModule == Mod.ModuleName) { continue; }

					// Implicit dep (Core / CoreUObject / Engine) — not a violation.
					if (Implicit.Contains(OwningModule)) { continue; }

					// Module's Build.cs declares the dep — not a violation.
					if (Mod.DeclaredDeps.Contains(OwningModule)) { continue; }

					FViolationRow V2;
					V2.File = RIToProjectRelative(SrcFile, ProjectRoot);
					V2.Line = i + 1;
					V2.Symbol = Candidate;
					V2.ExpectedModule = OwningModule;
					V2.CurrentlyListedModules = Mod.DeclaredDeps.Array();
					V2.CurrentlyListedModules.Sort();
					Violations.Add(MoveTemp(V2));
				}
			}
		}
	}

	// Stable ordering for cursor-based paging.
	Violations.Sort([](const FViolationRow& A, const FViolationRow& B)
	{
		if (A.File != B.File) { return A.File < B.File; }
		if (A.Line != B.Line) { return A.Line < B.Line; }
		return A.Symbol < B.Symbol;
	});

	// ----------------------------------------------------------------
	// Stage 4: page + envelope.
	// ----------------------------------------------------------------
	const int32 Total = Violations.Num();
	const int32 StartIdx = Page * Limit;
	const int32 EndIdxExcl = FMath::Min(StartIdx + Limit, Total);

	TArray<TSharedPtr<FJsonValue>> Rows;
	for (int32 i = StartIdx; i < EndIdxExcl; ++i)
	{
		const FViolationRow& V = Violations[i];
		TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
		Row->SetStringField(TEXT("file"), V.File);
		Row->SetNumberField(TEXT("line"), V.Line);
		Row->SetStringField(TEXT("symbol"), V.Symbol);
		Row->SetStringField(TEXT("expected_module"), V.ExpectedModule);
		TArray<TSharedPtr<FJsonValue>> Mods;
		for (const FString& M : V.CurrentlyListedModules)
		{
			Mods.Add(MakeShared<FJsonValueString>(M));
		}
		Row->SetArrayField(TEXT("currently_listed_modules"), Mods);
		Rows.Add(MakeShared<FJsonValueObject>(Row));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("violations"), Rows);
	Out->SetNumberField(TEXT("total_estimate"), Total);

	if (EndIdxExcl < Total)
	{
		FRICursorState OutCursor;
		OutCursor.QueryHash = FilterHash;
		OutCursor.Page = Page + 1;
		OutCursor.CachedTotalEstimate = Total;
		Out->SetStringField(TEXT("next_cursor"), EncodeRICursor(OutCursor));
	}
	return FMonolithActionResult::Success(Out);
}

// ============================================================================
// Item 6 (Phase 2): suggest_build_cs_deps — forward direction.
// ============================================================================

FMonolithActionResult FModuleDepRealityAdapter::HandleSuggestBuildCsDeps(const TSharedPtr<FJsonObject>& Params)
{
	ensure(IsInGameThread());

	// Resolve the FMonolithSourceDatabase wrapper (NOT the raw handle yet) so we can
	// hold its lock for the duration of the borrow per the GetRawHandle contract
	// (MonolithSourceDatabase.h:116-120). The raw handle is fetched under the lock
	// in Stage 3, where the only statement prepare/step/finalize happens.
	FMonolithSourceDatabase* SharedDb = GetSharedSourceDb();
	if (!SharedDb || !SharedDb->GetRawHandle())
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString FilePath = Params->HasField(TEXT("file_path"))
		? Params->GetStringField(TEXT("file_path")) : FString();

	// Optional explicit symbol list.
	TArray<FString> ExplicitSymbols;
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
		if (Params->TryGetArrayField(TEXT("symbols"), Arr) && Arr)
		{
			for (const TSharedPtr<FJsonValue>& V : *Arr)
			{
				FString S;
				if (V.IsValid() && V->TryGetString(S) && !S.IsEmpty()) { ExplicitSymbols.Add(S); }
			}
		}
	}

	if (FilePath.IsEmpty() && ExplicitSymbols.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Provide `file_path` and/or a non-empty `symbols` array."));
	}

	// ----------------------------------------------------------------
	// Stage 1: resolve the declaring module (path-first) + read its Build.cs.
	// ----------------------------------------------------------------
	FString DeclaringModule;
	FString ModuleDir;
	FString BuildCsPath;
	TSet<FString> DeclaredDeps;

	if (!FilePath.IsEmpty())
	{
		FString AbsFile = FilePath;
		if (FPaths::IsRelative(AbsFile))
		{
			AbsFile = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir() / FilePath);
		}

		if (!DeriveDeclaringModule(AbsFile, DeclaringModule, ModuleDir))
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Could not derive a declaring module from '%s' (expected a Source/<Module>/ path)."), *FilePath));
		}

		BuildCsPath = FindBuildCsForModule(ModuleDir, DeclaringModule);
		if (!BuildCsPath.IsEmpty())
		{
			const FRegexPattern ClassPattern(TEXT("public\\s+class\\s+(\\w+)\\s*:\\s*ModuleRules"));
			const FRegexPattern DepStringPattern(TEXT("\"([A-Za-z_][A-Za-z0-9_]*)\""));
			FBuildCsModule M;
			if (ParseBuildCs(BuildCsPath, M, ClassPattern, DepStringPattern))
			{
				DeclaredDeps = M.DeclaredDeps;
				if (!M.ModuleName.IsEmpty()) { DeclaringModule = M.ModuleName; }
			}
		}
	}

	// ----------------------------------------------------------------
	// Stage 2: collect candidate UE types.
	//   - from the supplied file (regex-extract UE-prefixed identifiers), and/or
	//   - the explicit `symbols[]`.
	// ----------------------------------------------------------------
	TSet<FString> Candidates;
	for (const FString& S : ExplicitSymbols)
	{
		// Strip any Class:: scope — resolve the leading type name.
		FString Name = S;
		int32 ScopeIdx = INDEX_NONE;
		if (Name.FindChar(TEXT(':'), ScopeIdx) && ScopeIdx != INDEX_NONE)
		{
			Name = Name.Left(ScopeIdx);
		}
		if (!Name.IsEmpty()) { Candidates.Add(Name); }
	}

	if (!FilePath.IsEmpty())
	{
		FString AbsFile = FilePath;
		if (FPaths::IsRelative(AbsFile))
		{
			AbsFile = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir() / FilePath);
		}
		FString FileText;
		if (FFileHelper::LoadFileToString(FileText, *AbsFile))
		{
			const FRegexPattern UeIdentPattern(TEXT("\\b([FUAEI][A-Z][A-Za-z0-9_]{2,})\\b"));
			TArray<FString> Lines;
			FileText.ParseIntoArrayLines(Lines, /*InCullEmpty=*/false);
			for (const FString& Line : Lines)
			{
				const FString Trimmed = Line.TrimStartAndEnd();
				if (Trimmed.StartsWith(TEXT("//")) || Trimmed.StartsWith(TEXT("#include"))) { continue; }
				FRegexMatcher Mt(UeIdentPattern, Line);
				while (Mt.FindNext())
				{
					const FString Cand = Mt.GetCaptureGroup(1);
					if (Cand.Len() >= 4) { Candidates.Add(Cand); }
				}
			}
		}
	}

	// ----------------------------------------------------------------
	// Stage 3: resolve each candidate to its owning module via the DB.
	//
	// BORROW CONTRACT (MonolithSourceDatabase.h:116-120): the raw handle is not
	// self-synchronising; we must hold the shared DB's lock for the FULL borrow —
	// handle fetch through the last Step()/Destroy(). Take it once and run the whole
	// resolution loop under it; the statement is Destroy()'d before the lock leaves
	// scope. Stages 1-2 (disk + regex only) ran lock-free above.
	// ----------------------------------------------------------------
	const TSet<FString>& Implicit = ImplicitModules();
	TSet<FString> RequiredModules;
	bool bStmtPrepareFailed = false;

	{
		FScopeLock Lock(&SharedDb->GetLock());
		FSQLiteDatabase* DB = SharedDb->GetRawHandle();
		if (!DB)
		{
			// Handle went away between the entry null-check and the lock (reindex
			// closed it). Surface the clean not-available state.
			return FMonolithActionResult::Error(
				TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
		}

		FSQLitePreparedStatement SymStmt;
		if (!SymStmt.Create(*DB, TEXT(
			"SELECT m.name FROM symbols s "
			"JOIN files f ON f.id = s.file_id "
			"JOIN modules m ON m.id = f.module_id "
			"WHERE s.name = ? "
			"GROUP BY m.name;")))
		{
			bStmtPrepareFailed = true;
		}
		else
		{
			for (const FString& Cand : Candidates)
			{
				SymStmt.Reset();
				SymStmt.ClearBindings();
				SymStmt.SetBindingValueByIndex(1, Cand);

				TArray<FString> ResolvedModules;
				while (SymStmt.Step() == ESQLitePreparedStatementStepResult::Row)
				{
					FString ModName;
					SymStmt.GetColumnValueByIndex(0, ModName);
					if (!ModName.IsEmpty()) { ResolvedModules.AddUnique(ModName); }
				}

				if (ResolvedModules.Num() != 1) { continue; } // unknown or ambiguous — skip

				const FString& Owning = ResolvedModules[0];
				if (Owning == DeclaringModule) { continue; }   // own-module use
				if (Implicit.Contains(Owning)) { continue; }   // implicit dep
				RequiredModules.Add(Owning);
			}
			// Finalize the statement BEFORE the lock releases (borrow-contract end).
			SymStmt.Destroy();
		}
	} // lock released here

	if (bStmtPrepareFailed)
	{
		return FMonolithActionResult::Error(
			TEXT("Symbol-resolution query prepare failed (symbols / files / modules tables absent?)."));
	}

	// ----------------------------------------------------------------
	// Stage 4: diff vs declared deps + envelope.
	// ----------------------------------------------------------------
	TArray<FString> RequiredArr = RequiredModules.Array();
	RequiredArr.Sort();

	TArray<FString> MissingArr;
	for (const FString& M : RequiredArr)
	{
		if (!DeclaredDeps.Contains(M)) { MissingArr.Add(M); }
	}
	MissingArr.Sort();

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	if (!DeclaringModule.IsEmpty()) { Out->SetStringField(TEXT("declaring_module"), DeclaringModule); }
	if (!BuildCsPath.IsEmpty())
	{
		Out->SetStringField(TEXT("build_cs"), FPaths::GetCleanFilename(BuildCsPath));
	}
	else if (!FilePath.IsEmpty())
	{
		Out->SetStringField(TEXT("build_cs_note"),
			TEXT("No <Module>.Build.cs found on disk — all required modules reported as missing."));
	}

	auto ToJsonArray = [](const TArray<FString>& In)
	{
		TArray<TSharedPtr<FJsonValue>> A;
		for (const FString& S : In) { A.Add(MakeShared<FJsonValueString>(S)); }
		return A;
	};

	Out->SetArrayField(TEXT("required_modules"), ToJsonArray(RequiredArr));
	Out->SetArrayField(TEXT("missing"), ToJsonArray(MissingArr));

	// Text envelope.
	FString Text;
	if (!DeclaringModule.IsEmpty()) { Text += FString::Printf(TEXT("Declaring module: %s\n"), *DeclaringModule); }
	Text += FString::Printf(TEXT("Required modules: %s\n"),
		RequiredArr.Num() > 0 ? *FString::Join(RequiredArr, TEXT(", ")) : TEXT("(none)"));
	Text += FString::Printf(TEXT("Missing from Build.cs: %s"),
		MissingArr.Num() > 0 ? *FString::Join(MissingArr, TEXT(", ")) : TEXT("(none)"));

	TArray<TSharedPtr<FJsonValue>> ContentArr;
	TSharedPtr<FJsonObject> ContentItem = MakeShared<FJsonObject>();
	ContentItem->SetStringField(TEXT("type"), TEXT("text"));
	ContentItem->SetStringField(TEXT("text"), Text);
	ContentArr.Add(MakeShared<FJsonValueObject>(ContentItem));
	Out->SetArrayField(TEXT("content"), ContentArr);

	return FMonolithActionResult::Success(Out);
}
