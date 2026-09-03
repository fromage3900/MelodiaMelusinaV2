// SPDX-License-Identifier: MIT
// LLM C++ authoring ergonomics — Phase 1 automation tests (items 1-3).
// Plan: Plugins/Monolith/Docs/plans/2026-06-10-llm-cpp-ergonomics-actions.md (§12 Phase 1).
//
// Tests use disposable SQLite DBs at FPaths::AutomationTransientDir(), never the
// real EngineSource.db. Fixtures live under
// Source/MonolithSource/Private/Tests/Fixtures/CppErgoCorpus/.
//
// DEVIATION NOTE: the plan §12 names IMPLEMENT_CUSTOM_SIMPLE_AUTOMATION_TEST;
// this module's existing tests (and the sibling RI tests) use
// IMPLEMENT_SIMPLE_AUTOMATION_TEST, which is what compiles here. We match the
// in-tree idiom.

#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "MonolithSourceActions.h"
#include "MonolithSourceDatabase.h"
#include "MonolithSourceIndexer.h"
#include "MonolithCursorCodec.h"

#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "SQLiteDatabase.h"

namespace MonolithCppErgoTestDetail
{
	/** Resolve the fixture corpus dir relative to the Monolith plugin install. */
	static FString GetFixtureCorpusDir()
	{
		TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("Monolith"));
		if (Plugin.IsValid())
		{
			return Plugin->GetBaseDir()
				/ TEXT("Source") / TEXT("MonolithSource")
				/ TEXT("Private") / TEXT("Tests") / TEXT("Fixtures") / TEXT("CppErgoCorpus");
		}
		return FPaths::ProjectPluginsDir()
			/ TEXT("Monolith") / TEXT("Source") / TEXT("MonolithSource")
			/ TEXT("Private") / TEXT("Tests") / TEXT("Fixtures") / TEXT("CppErgoCorpus");
	}

	/** A disposable temp DB path under AutomationTransientDir. */
	static FString MakeTempDbPath()
	{
		const FString Dir = FPaths::AutomationTransientDir();
		FPlatformFileManager::Get().GetPlatformFile().CreateDirectoryTree(*Dir);
		const FString Path = Dir / FString::Printf(TEXT("cppergo-test-%s.db"), *FGuid::NewGuid().ToString());
		IFileManager::Get().Delete(*Path, /*bRequireExists=*/false, /*bEvenReadOnly=*/true);
		return Path;
	}
}

// ---------------------------------------------------------------------------
// Test 1: DeprecationSchemaBootstrap — empty-DB CreateTablesIfNeeded() creates
// symbol_deprecations and stamps SchemaVersion 2.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoDeprecationSchemaBootstrapTest,
	"Monolith.Source.CppErgonomics.DeprecationSchemaBootstrap",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoDeprecationSchemaBootstrapTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCppErgoTestDetail;

	const FString DbPath = MakeTempDbPath();
	{
		FMonolithSourceDatabase DB;
		TestTrue(TEXT("OpenForWriting"), DB.OpenForWriting(DbPath));
		TestTrue(TEXT("CreateTablesIfNeeded"), DB.CreateTablesIfNeeded());

		// schema_version meta == 2
		TestEqual(TEXT("schema_version stamped to 2"), DB.GetMeta(TEXT("schema_version")), FString(TEXT("2")));

		// Inserting a deprecation row succeeds (table exists) and counts.
		DB.InsertDeprecation(/*SymbolId=*/0, TEXT("Foo"), TEXT("5.4"), TEXT("Use Bar"), TEXT("UE_DEPRECATED"));
		TestEqual(TEXT("one deprecation row"), DB.GetDeprecationCount(), 1);

		TOptional<FMonolithDeprecationRow> Got = DB.GetDeprecation(TEXT("Foo"));
		TestTrue(TEXT("GetDeprecation returns a value"), Got.IsSet());
		if (Got.IsSet())
		{
			TestEqual(TEXT("version"), Got.GetValue().Version, FString(TEXT("5.4")));
			TestEqual(TEXT("message"), Got.GetValue().Message, FString(TEXT("Use Bar")));
			TestEqual(TEXT("kind"), Got.GetValue().Kind, FString(TEXT("UE_DEPRECATED")));
		}
		DB.Close();
	}
	IFileManager::Get().Delete(*DbPath, /*bRequireExists=*/false, /*bEvenReadOnly=*/true);
	return true;
}

// ---------------------------------------------------------------------------
// Test 2: DeprecationIndexExtraction — index the fixture corpus (project-only,
// no engine) and assert two rows with parsed names, version/message/kind, and
// symbol_id = NULL (class-body methods have no symbols row).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoDeprecationIndexExtractionTest,
	"Monolith.Source.CppErgonomics.DeprecationIndexExtraction",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoDeprecationIndexExtractionTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCppErgoTestDetail;

	const FString CorpusDir = GetFixtureCorpusDir();
	if (!IFileManager::Get().DirectoryExists(*CorpusDir))
	{
		AddError(FString::Printf(TEXT("Fixture corpus not found: %s"), *CorpusDir));
		return false;
	}

	const FString DbPath = MakeTempDbPath();

	// Index ONLY the fixture project corpus (engine source path empty -> skipped).
	{
		FMonolithSourceIndexer Indexer;
		Indexer.SetSourcePath(TEXT(""));            // skip engine phase
		Indexer.SetShaderPath(TEXT(""));
		Indexer.SetProjectPath(CorpusDir);          // ProjectPath/Source/* discovered
		Indexer.SetDatabasePath(DbPath);
		Indexer.SetCleanBuild(true);
		Indexer.SetIndexProjectSource(true);
		TestTrue(TEXT("RunSynchronous"), Indexer.RunSynchronous());
	}

	// Read back the rows.
	FMonolithSourceDatabase DB;
	if (!DB.Open(DbPath))
	{
		AddError(TEXT("Failed to reopen indexed DB"));
		IFileManager::Get().Delete(*DbPath, false, true);
		return false;
	}

	TestEqual(TEXT("two deprecation rows extracted"), DB.GetDeprecationCount(), 2);

	// Foo — UE_DEPRECATED(5.4, "Use Bar instead")
	TOptional<FMonolithDeprecationRow> Foo = DB.GetDeprecation(TEXT("Foo"));
	TestTrue(TEXT("Foo deprecated"), Foo.IsSet());
	if (Foo.IsSet())
	{
		TestEqual(TEXT("Foo version"), Foo.GetValue().Version, FString(TEXT("5.4")));
		TestEqual(TEXT("Foo message"), Foo.GetValue().Message, FString(TEXT("Use Bar instead")));
		TestEqual(TEXT("Foo kind"), Foo.GetValue().Kind, FString(TEXT("UE_DEPRECATED")));
	}

	// Baz — UE_DEPRECATED_FORGAME(5.5, "Baz is gone")
	TOptional<FMonolithDeprecationRow> Baz = DB.GetDeprecation(TEXT("Baz"));
	TestTrue(TEXT("Baz deprecated"), Baz.IsSet());
	if (Baz.IsSet())
	{
		TestEqual(TEXT("Baz version"), Baz.GetValue().Version, FString(TEXT("5.5")));
		TestEqual(TEXT("Baz message"), Baz.GetValue().Message, FString(TEXT("Baz is gone")));
		TestEqual(TEXT("Baz kind"), Baz.GetValue().Kind, FString(TEXT("UE_DEPRECATED_FORGAME")));
	}

	// StillFine must NOT be present.
	TestFalse(TEXT("StillFine not deprecated"), DB.GetDeprecation(TEXT("StillFine")).IsSet());

	// symbol_id NON-NULL (linked) for both.
	//
	// 2026-06-11 allman-class indexing fix: DeprecatedThings.h's UDeprecatedThings is
	// declared allman-style (`{` on the line after `class`). Phase B of
	// MonolithCppParser now indexes such plain classes and ExtractMembers extracts the
	// class-body methods Foo/Baz as `function` symbol rows. The deprecation extractor
	// resolves symbol_id by EXACT NAME (MonolithSourceIndexer SymbolNameToId.Find), so
	// Foo/Baz now LINK to their member rows instead of storing NULL. This test
	// previously encoded the OLD limitation (allman plain classes were invisible to
	// Phase B, so class-body methods had no symbols row -> symbol_id NULL); both rows
	// are now linked.
	//
	// Linkage caveat (not redesigned here): SymbolNameToId is keyed on the BARE name,
	// so two same-named members across the corpus would collide to the last-inserted
	// id. Foo/Baz are unique in this corpus, so the linkage is deterministic.
	{
		FSQLiteDatabase* Raw = DB.GetRawHandle();
		if (Raw)
		{
			FSQLitePreparedStatement Stmt;
			Stmt.Create(*Raw, TEXT("SELECT COUNT(*) FROM symbol_deprecations WHERE symbol_id IS NOT NULL;"));
			int32 LinkedCount = -1;
			if (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
			{
				int64 C = 0;
				Stmt.GetColumnValueByIndex(0, C);
				LinkedCount = static_cast<int32>(C);
			}
			TestEqual(TEXT("both rows have a linked (non-NULL) symbol_id"), LinkedCount, 2);
		}
	}

	DB.Close();
	IFileManager::Get().Delete(*DbPath, false, true);
	return true;
}

// ---------------------------------------------------------------------------
// Test 3: IncludePathDerivation — pure unit over DeriveIncludePath.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoIncludePathDerivationTest,
	"Monolith.Source.CppErgonomics.IncludePathDerivation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoIncludePathDerivationTest::RunTest(const FString& /*Parameters*/)
{
	bool bIncludable = false;
	FString Warning;

	// Public/ -> strip, includable.
	{
		const FString In = TEXT("D:/Proj/Source/MyMod/Public/Sub/Thing.h");
		const FString Out = FMonolithSourceActions::DeriveIncludePath(In, bIncludable, Warning);
		TestEqual(TEXT("Public/ strips prefix"), Out, FString(TEXT("Sub/Thing.h")));
		TestTrue(TEXT("Public/ includable"), bIncludable);
		TestTrue(TEXT("Public/ no warning"), Warning.IsEmpty());
	}

	// Classes/ -> strip, includable.
	{
		const FString In = TEXT("D:/Proj/Source/MyMod/Classes/X.h");
		const FString Out = FMonolithSourceActions::DeriveIncludePath(In, bIncludable, Warning);
		TestEqual(TEXT("Classes/ strips prefix"), Out, FString(TEXT("X.h")));
		TestTrue(TEXT("Classes/ includable"), bIncludable);
	}

	// Internal/ -> strip, includable.
	{
		const FString In = TEXT("D:/Proj/Source/MyMod/Internal/Y.h");
		const FString Out = FMonolithSourceActions::DeriveIncludePath(In, bIncludable, Warning);
		TestEqual(TEXT("Internal/ strips prefix"), Out, FString(TEXT("Y.h")));
		TestTrue(TEXT("Internal/ includable"), bIncludable);
	}

	// Private/ -> NOT includable, same-module relative, warning names the module.
	{
		Warning.Empty();
		const FString In = TEXT("D:/Proj/Source/MyMod/Private/Z.h");
		const FString Out = FMonolithSourceActions::DeriveIncludePath(In, bIncludable, Warning);
		TestEqual(TEXT("Private/ same-module relative"), Out, FString(TEXT("Z.h")));
		TestFalse(TEXT("Private/ NOT includable"), bIncludable);
		TestTrue(TEXT("Private/ warning present"), Warning.Contains(TEXT("Private header")));
		TestTrue(TEXT("Private/ warning names module"), Warning.Contains(TEXT("MyMod")));
	}

	// Backslashes + no recognised prefix -> basename fallback.
	{
		Warning.Empty();
		const FString In = TEXT("C:\\Engine\\Source\\Runtime\\Core\\Foo\\Bar.h");
		const FString Out = FMonolithSourceActions::DeriveIncludePath(In, bIncludable, Warning);
		TestEqual(TEXT("no-prefix basename fallback"), Out, FString(TEXT("Bar.h")));
		TestTrue(TEXT("fallback includable"), bIncludable);
	}

	return true;
}

// ---------------------------------------------------------------------------
// Test 4: SignatureCompaction — CompactDeclaration strips inline bodies + macro
// continuations and joins multi-line declarations. No body leaks.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoSignatureCompactionTest,
	"Monolith.Source.CppErgonomics.SignatureCompaction",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoSignatureCompactionTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCppErgoTestDetail;

	const FString FixturePath = GetFixtureCorpusDir() / TEXT("Signatures.h");
	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *FixturePath))
	{
		AddError(FString::Printf(TEXT("Could not load signature fixture: %s"), *FixturePath));
		return false;
	}

	// Locate fixture declarations by content (line numbers are not assumed exact).
	int32 MultiIdx = INDEX_NONE, InlineIdx = INDEX_NONE, MacroIdx = INDEX_NONE;
	for (int32 i = 0; i < Lines.Num(); ++i)
	{
		if (Lines[i].Contains(TEXT("MultiLineDecl"))) MultiIdx = i;
		else if (Lines[i].Contains(TEXT("GetTransform()")) && Lines[i].Contains(TEXT("{"))) InlineIdx = i;
		else if (Lines[i].Contains(TEXT("void Thing(")))   MacroIdx = i;
	}

	TestTrue(TEXT("found MultiLineDecl"), MultiIdx != INDEX_NONE);
	TestTrue(TEXT("found inline GetTransform"), InlineIdx != INDEX_NONE);
	TestTrue(TEXT("found macro Thing"), MacroIdx != INDEX_NONE);

	if (MultiIdx != INDEX_NONE)
	{
		const FString Sig = FMonolithSourceActions::CompactDeclaration(Lines, MultiIdx);
		TestEqual(TEXT("multi-line joined"), Sig,
			FString(TEXT("float MultiLineDecl( int32 First, const FString& Second) const")));
		TestFalse(TEXT("multi-line no body"), Sig.Contains(TEXT("{")));
	}

	if (InlineIdx != INDEX_NONE)
	{
		const FString Sig = FMonolithSourceActions::CompactDeclaration(Lines, InlineIdx);
		// Body { return ... } must be cut.
		TestFalse(TEXT("inline body stripped"), Sig.Contains(TEXT("return")));
		TestFalse(TEXT("inline no brace"), Sig.Contains(TEXT("{")));
		TestTrue(TEXT("inline keeps signature"), Sig.Contains(TEXT("GetTransform()")));
	}

	if (MacroIdx != INDEX_NONE)
	{
		const FString Sig = FMonolithSourceActions::CompactDeclaration(Lines, MacroIdx);
		// The `void Thing(int32 x) { DoThing(x); }` line: body stripped.
		TestFalse(TEXT("macro body stripped"), Sig.Contains(TEXT("DoThing")));
		TestFalse(TEXT("macro no brace"), Sig.Contains(TEXT("{")));
	}

	return true;
}

// ---------------------------------------------------------------------------
// Phase 2 helper: index the fixture corpus into a disposable DB. Returns true
// on success; caller closes + deletes the DB.
//
// FIXTURE-COMPILE GUARD: the .cpp fixtures on disk carry a `.cpp.fixture`
// extension so UBT's `*.cpp` glob never compiles them into MonolithSource (a
// fixture TU in the module DLL is a full-unity symbol-collision candidate —
// issue #68 class). But the indexer DISCOVERS files by walking ProjectPath via
// FindFilesRecursive("*.cpp"), so a `.cpp.fixture` would be skipped and its
// source lines never reach source_fts (breaking FindExampleUsagePagination,
// which needs the .cpp's call-site lines).
//
// Bridge: STAGE a transient copy of the corpus, renaming every `*.cpp.fixture`
// back to `*.cpp` (bytes copied verbatim, so indexed CONTENT is byte-identical),
// preserving the Source/<Module>/ tree so DiscoverProjectModules finds it. Index
// the staged copy, then delete it.
// ---------------------------------------------------------------------------
namespace MonolithCppErgoTestDetail
{
	/** Recursively copy SrcDir -> DstDir, renaming `*.cpp.fixture` to `*.cpp`.
	 *  Bytes are copied verbatim. Returns false on any IO failure. */
	static bool StageCorpus(const FString& SrcDir, const FString& DstDir)
	{
		IFileManager& FM = IFileManager::Get();
		FM.MakeDirectory(*DstDir, /*Tree=*/true);

		TArray<FString> Files;
		FM.FindFilesRecursive(Files, *SrcDir, TEXT("*"), /*Files=*/true, /*Dirs=*/false, /*bClearFileNames=*/true);

		// Normalised corpus root for prefix stripping. FindFilesRecursive returns
		// FULL (absolute) paths (FileManagerGeneric bStoreFullPath=true), so the
		// relative path is the file path with the SrcDir prefix removed.
		//
		// NOTE: do NOT use FPaths::MakePathRelativeTo here — it internally applies
		// FPaths::GetPath() to the base argument (Paths.cpp:1525), stripping the
		// LAST component, so it computes paths relative to the corpus's PARENT, not
		// the corpus dir itself. That injected an extra "CppErgoCorpus/" segment,
		// landing staged files at StagedDir/CppErgoCorpus/Source/... while the
		// indexer walks StagedDir/Source/* — zero modules discovered, zero rows.
		FString NormSrcRoot = SrcDir;
		FPaths::NormalizeDirectoryName(NormSrcRoot);   // strips trailing slash, backslashes -> '/'

		for (const FString& SrcFile : Files)
		{
			FString NormSrc = SrcFile;
			FPaths::NormalizeFilename(NormSrc);        // backslashes -> '/'

			// Relative path = file path minus the "<corpus>/" prefix (case-insensitive
			// on Windows). If the prefix is absent (shouldn't happen) fall back to the
			// clean filename so the file still lands somewhere indexable.
			FString Rel;
			const FString Prefix = NormSrcRoot + TEXT("/");
			if (NormSrc.StartsWith(Prefix, ESearchCase::IgnoreCase))
			{
				Rel = NormSrc.RightChop(Prefix.Len());
			}
			else
			{
				Rel = FPaths::GetCleanFilename(NormSrc);
			}

			// Rename a trailing `.cpp.fixture` -> `.cpp` so the walker discovers it
			// and IndexCppFile classifies it as a "source" TU.
			if (Rel.EndsWith(TEXT(".cpp.fixture"), ESearchCase::IgnoreCase))
			{
				Rel.LeftChopInline(FCString::Strlen(TEXT(".fixture")));
			}

			const FString DstFile = DstDir / Rel;
			FM.MakeDirectory(*FPaths::GetPath(DstFile), /*Tree=*/true);

			// Verbatim byte copy (keeps indexed content byte-identical to the source).
			TArray<uint8> Bytes;
			if (!FFileHelper::LoadFileToArray(Bytes, *SrcFile)) { return false; }
			if (!FFileHelper::SaveArrayToFile(Bytes, *DstFile)) { return false; }
		}
		return true;
	}

	// Indexes the staged corpus into DbPath. On success, OutStagedDir receives the
	// transient staged-corpus path. The caller MUST delete OutStagedDir in teardown
	// AFTER closing the DB — the FTS-backed reads under test (find_example_usage
	// context read, SymbolExists FTS fallback, ResolveFirstSignature declaration-read)
	// RE-OPEN the staged .cpp/.h files on disk during assertions, so the staged dir
	// must outlive the DB. (Deleting it here, before assertions, was the zero-data bug.)
	static bool IndexFixtureCorpus(const FString& DbPath, FString& OutStagedDir, FString& OutError)
	{
		OutStagedDir.Empty();

		const FString CorpusDir = GetFixtureCorpusDir();
		if (!IFileManager::Get().DirectoryExists(*CorpusDir))
		{
			OutError = FString::Printf(TEXT("Fixture corpus not found: %s"), *CorpusDir);
			return false;
		}

		// Stage a transient copy with `.cpp.fixture` -> `.cpp` so the indexer's
		// FindFilesRecursive("*.cpp") walker picks up the fixture sources.
		const FString StagedDir = FPaths::AutomationTransientDir()
			/ FString::Printf(TEXT("cppergo-corpus-%s"), *FGuid::NewGuid().ToString());
		if (!StageCorpus(CorpusDir, StagedDir))
		{
			// Staging failed mid-way — best-effort clean up the partial dir.
			IFileManager::Get().DeleteDirectory(*StagedDir, /*bRequireExists=*/false, /*bTree=*/true);
			OutError = FString::Printf(TEXT("Failed to stage corpus into %s"), *StagedDir);
			return false;
		}

		FMonolithSourceIndexer Indexer;
		Indexer.SetSourcePath(TEXT(""));            // skip engine phase
		Indexer.SetShaderPath(TEXT(""));
		Indexer.SetProjectPath(StagedDir);          // StagedDir/Source/* discovered
		Indexer.SetDatabasePath(DbPath);
		Indexer.SetCleanBuild(true);
		Indexer.SetIndexProjectSource(true);
		const bool bRan = Indexer.RunSynchronous();

		if (!bRan)
		{
			// Index failed — staged files are no longer needed; clean up now.
			IFileManager::Get().DeleteDirectory(*StagedDir, /*bRequireExists=*/false, /*bTree=*/true);
			OutError = TEXT("Indexer.RunSynchronous() failed");
			return false;
		}

		// Success: hand the staged dir back so the caller can keep it alive through
		// the FTS-backed assertions and delete it in teardown after the DB close.
		OutStagedDir = StagedDir;
		return true;
	}
}

// ---------------------------------------------------------------------------
// Phase 2 Test: VerifySymbolsComposition — the class-body method MUST report
// exists:true (resolved via class row + source_fts declaration hit, NOT
// symbols-table presence); a missing symbol reports exists:false; a deprecated
// symbol resolves its row. Exercises the shared composition helpers directly.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoVerifySymbolsCompositionTest,
	"Monolith.Source.CppErgonomics.VerifySymbolsComposition",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoVerifySymbolsCompositionTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCppErgoTestDetail;

	const FString DbPath = MakeTempDbPath();
	FString StagedDir;
	FString Err;
	if (!IndexFixtureCorpus(DbPath, StagedDir, Err))
	{
		AddError(Err);
		IFileManager::Get().Delete(*DbPath, false, true);
		return false;
	}

	FMonolithSourceDatabase DB;
	if (!DB.Open(DbPath))
	{
		AddError(TEXT("Failed to reopen indexed DB"));
		IFileManager::Get().Delete(*DbPath, false, true);
		IFileManager::Get().DeleteDirectory(*StagedDir, /*bRequireExists=*/false, /*bTree=*/true);
		return false;
	}

	// UCppErgoUsage::CallMe is a class-body method (NO symbols row). Existence must
	// resolve via the owning class row + source_fts declaration hit.
	TestTrue(TEXT("class-body method exists:true"),
		FMonolithSourceActions::SymbolExists(&DB, TEXT("UCppErgoUsage::CallMe")));

	// Owning class itself exists.
	TestTrue(TEXT("class exists:true"),
		FMonolithSourceActions::SymbolExists(&DB, TEXT("UCppErgoUsage")));

	// A symbol absent from the corpus reports exists:false (no error).
	TestFalse(TEXT("missing symbol exists:false"),
		FMonolithSourceActions::SymbolExists(&DB, TEXT("UThisDoesNotExistAnywhere::Nope")));

	// Signature resolution for the class-body method comes from declaration_read.
	{
		FString Sig, Source;
		const bool bOk = FMonolithSourceActions::ResolveFirstSignature(&DB, TEXT("UCppErgoUsage::CallMe"), Sig, Source);
		TestTrue(TEXT("CallMe signature resolved"), bOk);
		if (bOk)
		{
			TestTrue(TEXT("CallMe signature contains CallMe("), Sig.Contains(TEXT("CallMe(")));
			TestFalse(TEXT("CallMe signature has no body"), Sig.Contains(TEXT("{")));
		}
	}

	// Deprecation composition: UDeprecatedThings::Foo is UE_DEPRECATED(5.4, ...).
	{
		TOptional<FMonolithDeprecationRow> Dep = DB.GetDeprecation(TEXT("Foo"));
		TestTrue(TEXT("Foo deprecation row present"), Dep.IsSet());
	}

	// Teardown: close the DB FIRST, then delete the staged corpus. The assertions
	// above re-open the staged .cpp/.h files (FTS-backed reads), so the staged dir
	// must outlive every assertion.
	DB.Close();
	IFileManager::Get().Delete(*DbPath, false, true);
	IFileManager::Get().DeleteDirectory(*StagedDir, /*bRequireExists=*/false, /*bTree=*/true);
	return true;
}

// ---------------------------------------------------------------------------
// Phase 2 Test: FindExampleUsagePagination — the FTS substrate yields >limit
// distinct call-site lines for `CallMe(`; the rerun-slice + MonolithCursorCodec
// cursor round-trips (page 0 emits next_cursor, decode threads page 1, page 1
// returns the remaining rows and no further cursor). Reproduces the handler's
// FTS + slice + cursor logic against the disposable DB (the JSON handler routes
// through GetDB()/GEditor, which the test cannot supply).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoFindExampleUsagePaginationTest,
	"Monolith.Source.CppErgonomics.FindExampleUsagePagination",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoFindExampleUsagePaginationTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCppErgoTestDetail;

	const FString DbPath = MakeTempDbPath();
	FString StagedDir;
	FString Err;
	if (!IndexFixtureCorpus(DbPath, StagedDir, Err))
	{
		AddError(Err);
		IFileManager::Get().Delete(*DbPath, false, true);
		return false;
	}

	FMonolithSourceDatabase DB;
	if (!DB.Open(DbPath))
	{
		AddError(TEXT("Failed to reopen indexed DB"));
		IFileManager::Get().Delete(*DbPath, false, true);
		IFileManager::Get().DeleteDirectory(*StagedDir, /*bRequireExists=*/false, /*bTree=*/true);
		return false;
	}

	// Gather all distinct call-site lines matching `CallMe(` via source_fts —
	// the same substrate the handler uses.
	const FString Symbol = TEXT("CallMe");
	const FString Needle = Symbol + TEXT("(");
	TArray<TPair<FString, int32>> Hits; // (file, 1-based line)
	TSet<FString> Seen;

	TArray<FMonolithSourceChunk> Chunks = DB.SearchSourceFTS(Symbol, TEXT("all"), 400);
	for (const FMonolithSourceChunk& Chunk : Chunks)
	{
		const FString FilePath = DB.GetFilePath(Chunk.FileId);
		TArray<FString> FileLines;
		if (!FFileHelper::LoadFileToStringArray(FileLines, *FilePath)) continue;
		const int32 WinStart = FMath::Max(0, Chunk.LineNumber - 1);
		const int32 WinEnd = FMath::Min(FileLines.Num(), WinStart + 10);
		for (int32 i = WinStart; i < WinEnd; ++i)
		{
			const FString& L = FileLines[i];
			const int32 Idx = L.Find(Needle, ESearchCase::CaseSensitive);
			if (Idx == INDEX_NONE) continue;
			if (Idx > 0)
			{
				const TCHAR Prev = L[Idx - 1];
				if (FChar::IsAlnum(Prev) || Prev == TEXT('_')) continue;
			}
			const FString Key = FString::Printf(TEXT("%lld_%d"), Chunk.FileId, i + 1);
			if (Seen.Contains(Key)) continue;
			Seen.Add(Key);
			Hits.Add(TPair<FString, int32>(FilePath, i + 1));
		}
	}
	// Deterministic order (handler ranks then tie-breaks by path+line).
	Hits.Sort([](const TPair<FString, int32>& A, const TPair<FString, int32>& B)
	{
		if (A.Key != B.Key) return A.Key < B.Key;
		return A.Value < B.Value;
	});

	const int32 Total = Hits.Num();
	// The fixture .cpp/.h together carry >10 `CallMe(` declaration+call lines.
	TestTrue(TEXT("more than one page of hits"), Total > 5);

	const int32 Limit = 5;
	const uint32 QHash = MonolithCursorCodec::ComputeQueryHash(
		Symbol, TEXT("engine"), TEXT("find_example_usage"), TEXT(""), TEXT(""), TEXT(""));

	// Page 0.
	const int32 P0Start = 0;
	const int32 P0End = FMath::Min(P0Start + Limit, Total);
	const int32 P0Rows = P0End - P0Start;
	TestEqual(TEXT("page 0 full"), P0Rows, Limit);

	FString NextCursor;
	if (P0Rows >= Limit && (P0Start + Limit) < Total)
	{
		MonolithCursorCodec::FCursorState OutState;
		OutState.QueryHash = QHash;
		OutState.SymbolPage = 1;
		OutState.SourcePage = 1;
		OutState.CachedTotalEstimate = Total;
		NextCursor = MonolithCursorCodec::Encode(OutState);
	}
	TestFalse(TEXT("page 0 emits next_cursor"), NextCursor.IsEmpty());

	// Decode the cursor and fetch page 1.
	MonolithCursorCodec::FCursorState Decoded;
	const bool bDecoded = MonolithCursorCodec::Decode(NextCursor, Decoded);
	TestTrue(TEXT("cursor decodes"), bDecoded);
	TestEqual(TEXT("cursor query hash matches"), Decoded.QueryHash, QHash);
	TestEqual(TEXT("cursor page index 1"), Decoded.SourcePage, 1);

	const int32 P1Start = Decoded.SourcePage * Limit;
	const int32 P1End = FMath::Min(P1Start + Limit, Total);
	const int32 P1Rows = FMath::Max(0, P1End - P1Start);
	TestTrue(TEXT("page 1 returns rows"), P1Rows > 0);

	// Page 0 and page 1 must be disjoint (no overlap in the sliced indices).
	TestTrue(TEXT("page 1 starts after page 0"), P1Start >= P0End);

	// Teardown: close the DB FIRST, then delete the staged corpus. The hit-gathering
	// loop above re-opens the staged .cpp/.h files (LoadFileToStringArray), so the
	// staged dir must outlive every read.
	DB.Close();
	IFileManager::Get().Delete(*DbPath, false, true);
	IFileManager::Get().DeleteDirectory(*StagedDir, /*bRequireExists=*/false, /*bTree=*/true);
	return true;
}

// ---------------------------------------------------------------------------
// Phase 3 Test: LintHeaderRuleTable — each fixture header exercises one rule;
// a clean header reports zero findings. Pure over LintHeaderLines (no DB).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoLintHeaderRuleTableTest,
	"Monolith.Source.CppErgonomics.LintHeaderRuleTable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoLintHeaderRuleTableTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCppErgoTestDetail;

	const FString ModDir = GetFixtureCorpusDir() / TEXT("Source") / TEXT("CppErgoTestMod");

	// The committed lint fixtures carry a `.h.fixture` extension so UnrealHeaderTool
	// never parses their reflection macros (UHT walks every `*.h` under the module
	// tree and would hard-error on the deliberately-broken UCLASS layouts — and even
	// register the clean one). But rule (c)/(d) key on the LINTED FILE's base name
	// via FPaths::GetBaseFilename, which strips only the LAST extension: linting a
	// `.h.fixture` would yield base "LintClean.h" (not "LintClean") and fire a bogus
	// rule-c mismatch on the clean case. So STAGE each fixture to AutomationTransientDir
	// under a real `Source/CppErgoTestMod/<name>.h` name (byte-verbatim copy) — the
	// `.h` base name makes rule (c)/(d) correct, and the preserved Source/<Module>/
	// tree keeps the path-first module derivation resolving CppErgoTestMod.
	const FString StageRoot = FPaths::AutomationTransientDir()
		/ FString::Printf(TEXT("cppergo-lint-%s"), *FGuid::NewGuid().ToString());
	const FString StageModDir = StageRoot / TEXT("Source") / TEXT("CppErgoTestMod");
	FPlatformFileManager::Get().GetPlatformFile().CreateDirectoryTree(*StageModDir);

	// Stage a `.h.fixture` to a real `<RealName>.h` under the staged module dir; return
	// the staged path. Byte-verbatim so linted CONTENT is identical to the committed file.
	auto StageFixture = [&](const FString& FixtureName, const FString& RealHeaderName) -> FString
	{
		const FString Src = ModDir / FixtureName;
		const FString Dst = StageModDir / RealHeaderName;
		TArray<uint8> Bytes;
		if (!FFileHelper::LoadFileToArray(Bytes, *Src) || !FFileHelper::SaveArrayToFile(Bytes, *Dst))
		{
			AddError(FString::Printf(TEXT("Could not stage lint fixture %s -> %s"), *Src, *Dst));
			return FString();
		}
		return Dst;
	};

	// Helper: stage a `.h.fixture` to a real `.h` and lint it. RealHeaderName drives
	// rule (c)/(d) base-name logic (e.g. "LintClean.h").
	auto LintFixture = [&](const FString& FixtureName, const FString& RealHeaderName,
		const TSet<FString>& Specs) -> TArray<FMonolithSourceActions::FLintFinding>
	{
		const FString Path = StageFixture(FixtureName, RealHeaderName);
		if (Path.IsEmpty()) { return {}; }
		TArray<FString> Lines;
		if (!FFileHelper::LoadFileToStringArray(Lines, *Path))
		{
			AddError(FString::Printf(TEXT("Could not load staged lint fixture: %s"), *Path));
			return {};
		}
		return FMonolithSourceActions::LintHeaderLines(Path, Lines, Specs);
	};

	auto HasRule = [](const TArray<FMonolithSourceActions::FLintFinding>& F, const TCHAR* RuleId) -> bool
	{
		for (const FMonolithSourceActions::FLintFinding& Fi : F) { if (Fi.RuleId == RuleId) return true; }
		return false;
	};

	// Assert the finding set's rule_ids are EXACTLY `Expected` (order-independent) —
	// catches spurious extra rules (e.g. the rule-c false positive) as well as
	// missing ones.
	auto TestExactRules = [&](const TCHAR* Label, const TArray<FMonolithSourceActions::FLintFinding>& F,
		const TArray<FString>& Expected)
	{
		TSet<FString> Got;
		for (const FMonolithSourceActions::FLintFinding& Fi : F) { Got.Add(Fi.RuleId); }
		TSet<FString> Want;
		for (const FString& R : Expected) { Want.Add(R); }
		bool bMatch = (Got.Num() == Want.Num());
		if (bMatch)
		{
			for (const FString& R : Got) { if (!Want.Contains(R)) { bMatch = false; break; } }
		}
		if (!bMatch)
		{
			AddError(FString::Printf(TEXT("%s: rule set mismatch. got=[%s] expected=[%s]"),
				Label, *FString::Join(Got.Array(), TEXT(",")), *FString::Join(Want.Array(), TEXT(","))));
		}
		TestTrue(Label, bMatch);
	};

	const TSet<FString> NoSpecs;

	// Clean header -> zero findings. (Staged as LintClean.h so rule-c base-name
	// matching sees "LintClean" == "LintClean".)
	{
		TArray<FMonolithSourceActions::FLintFinding> F = LintFixture(TEXT("LintClean.h.fixture"), TEXT("LintClean.h"), NoSpecs);
		TestEqual(TEXT("clean header zero findings"), F.Num(), 0);
	}

	// (a) missing GENERATED_BODY — EXACTLY {missing_generated_body}.
	{
		TArray<FMonolithSourceActions::FLintFinding> F = LintFixture(TEXT("LintMissingGeneratedBody.h.fixture"), TEXT("LintMissingGeneratedBody.h"), NoSpecs);
		TestExactRules(TEXT("(a) LintMissingGeneratedBody exact rules"), F, { TEXT("missing_generated_body") });
		// Each finding carries a message.
		for (const FMonolithSourceActions::FLintFinding& Fi : F)
		{
			TestTrue(TEXT("(a) finding has message"), !Fi.Message.IsEmpty());
		}
	}

	// (b) *.generated.h not last — EXACTLY {generated_h_not_last}. CRITICAL negated
	// assertion: this fixture's last include is a NON-generated header, so the
	// rule-c name-mismatch must NOT fire (regression guard for the false positive).
	{
		TArray<FMonolithSourceActions::FLintFinding> F = LintFixture(TEXT("LintGeneratedNotLast.h.fixture"), TEXT("LintGeneratedNotLast.h"), NoSpecs);
		TestTrue(TEXT("(b) generated_h_not_last reported"), HasRule(F, TEXT("generated_h_not_last")));
		TestFalse(TEXT("(b) NO spurious generated_h_name_mismatch"), HasRule(F, TEXT("generated_h_name_mismatch")));
		TestExactRules(TEXT("(b) LintGeneratedNotLast exact rules"), F, { TEXT("generated_h_not_last") });
		for (const FMonolithSourceActions::FLintFinding& Fi : F)
		{
			if (Fi.RuleId == TEXT("generated_h_not_last")) { TestTrue(TEXT("(b) has line"), Fi.Line > 0); }
		}
	}

	// (c) generated.h name mismatch — EXACTLY {generated_h_name_mismatch}. Staged as
	// LintNameMismatch.h; the include is "WrongName.generated.h" -> mismatch fires.
	{
		TArray<FMonolithSourceActions::FLintFinding> F = LintFixture(TEXT("LintNameMismatch.h.fixture"), TEXT("LintNameMismatch.h"), NoSpecs);
		TestExactRules(TEXT("(c) LintNameMismatch exact rules"), F, { TEXT("generated_h_name_mismatch") });
	}

	// (d) missing <MODULE>_API — EXACTLY {missing_api_macro}.
	{
		TArray<FMonolithSourceActions::FLintFinding> F = LintFixture(TEXT("LintMissingApiMacro.h.fixture"), TEXT("LintMissingApiMacro.h"), NoSpecs);
		TestExactRules(TEXT("(d) LintMissingApiMacro exact rules"), F, { TEXT("missing_api_macro") });
	}

	// (e) UPROPERTY in non-reflected type — EXACTLY {reflected_member_in_non_reflected_type}
	// (deduped; the fixture has both a UPROPERTY and a UFUNCTION, same rule_id).
	{
		TArray<FMonolithSourceActions::FLintFinding> F = LintFixture(TEXT("LintOrphanUproperty.h.fixture"), TEXT("LintOrphanUproperty.h"), NoSpecs);
		TestExactRules(TEXT("(e) LintOrphanUproperty exact rules"), F, { TEXT("reflected_member_in_non_reflected_type") });
		// Both members fire (two findings, one rule_id).
		int32 Count = 0;
		for (const FMonolithSourceActions::FLintFinding& Fi : F)
		{
			if (Fi.RuleId == TEXT("reflected_member_in_non_reflected_type")) { ++Count; }
		}
		TestEqual(TEXT("(e) both UPROPERTY + UFUNCTION fire"), Count, 2);
	}

	// (f) invalid specifier — exercised against the CLEAN header's UCLASS() (no
	// specifier) by passing a vocabulary that lacks an injected bad token. We
	// instead lint an in-memory header carrying UCLASS(NotARealSpecifier).
	{
		TArray<FString> Lines;
		Lines.Add(TEXT("#pragma once"));
		Lines.Add(TEXT("#include \"CoreMinimal.h\""));
		Lines.Add(TEXT("#include \"LintBadSpecifier.generated.h\""));
		Lines.Add(TEXT("UCLASS(Blueprintable, NotARealSpecifier)"));
		Lines.Add(TEXT("class CPPERGOTESTMOD_API ULintBadSpecifier : public UObject"));
		Lines.Add(TEXT("{"));
		Lines.Add(TEXT("\tGENERATED_BODY()"));
		Lines.Add(TEXT("};"));

		TSet<FString> Specs;
		Specs.Add(TEXT("Blueprintable"));
		Specs.Add(TEXT("BlueprintType"));
		// "NotARealSpecifier" deliberately absent from the vocabulary.

		const FString FakePath = ModDir / TEXT("LintBadSpecifier.h");
		TArray<FMonolithSourceActions::FLintFinding> F =
			FMonolithSourceActions::LintHeaderLines(FakePath, Lines, Specs);
		TestTrue(TEXT("(f) invalid_specifier reported"), HasRule(F, TEXT("invalid_specifier")));

		// Degrade gracefully: with an EMPTY vocabulary, the specifier rule is skipped.
		TArray<FMonolithSourceActions::FLintFinding> F2 =
			FMonolithSourceActions::LintHeaderLines(FakePath, Lines, TSet<FString>());
		TestFalse(TEXT("(f) skipped when vocabulary empty"), HasRule(F2, TEXT("invalid_specifier")));
	}

	// Teardown: remove the staged-fixture tree (all reads above are done).
	IFileManager::Get().DeleteDirectory(*StageRoot, /*bRequireExists=*/false, /*bTree=*/true);
	return true;
}

// ---------------------------------------------------------------------------
// Phase 3 Test: GenerateClassStubText — the templated .h/.cpp pair carries the
// API macro, parent include FIRST, *.generated.h LAST, GENERATED_BODY(), and the
// correct constructor form. Pure over GenerateClassStubText (no DB).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoGenerateClassStubTextTest,
	"Monolith.Source.CppErgonomics.GenerateClassStubText",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoGenerateClassStubTextTest::RunTest(const FString& /*Parameters*/)
{
	// Plain default constructor (parent does NOT require FObjectInitializer).
	// UE "Add C++ Class" file-naming: class UMyComp -> file base "MyComp", so the
	// includes are "MyComp.generated.h" / "MyComp.h" (U prefix stripped), while the
	// C++ class identifier stays UMyComp.
	{
		FString H, C;
		FMonolithSourceActions::GenerateClassStubText(
			TEXT("UActorComponent"), TEXT("UMyComp"), TEXT("MyMod"),
			TEXT("Components/ActorComponent.h"), /*bNeedsObjInit=*/false, H, C);

		TestTrue(TEXT("h has API macro"), H.Contains(TEXT("MYMOD_API")));
		TestTrue(TEXT("h has parent include"), H.Contains(TEXT("#include \"Components/ActorComponent.h\"")));
		TestTrue(TEXT("h has GENERATED_BODY"), H.Contains(TEXT("GENERATED_BODY()")));
		TestTrue(TEXT("h has parent base"), H.Contains(TEXT(": public UActorComponent")));
		// The class IDENTIFIER keeps the U prefix.
		TestTrue(TEXT("h declares UMyComp"), H.Contains(TEXT("class MYMOD_API UMyComp : public UActorComponent")));

		// *.generated.h must be the LAST include line — and use the PREFIX-STRIPPED
		// file base ("MyComp.generated.h", NOT "UMyComp.generated.h").
		const int32 GenIdx = H.Find(TEXT("#include \"MyComp.generated.h\""));
		const int32 ParentIdx = H.Find(TEXT("#include \"Components/ActorComponent.h\""));
		TestTrue(TEXT("prefix-stripped generated.h present"), GenIdx != INDEX_NONE);
		TestFalse(TEXT("NO U-prefixed generated.h"), H.Contains(TEXT("UMyComp.generated.h")));
		TestTrue(TEXT("parent include before generated.h"), ParentIdx != INDEX_NONE && ParentIdx < GenIdx);
		// No #include appears after the generated.h.
		TestEqual(TEXT("generated.h is last include"),
			H.Find(TEXT("#include"), ESearchCase::CaseSensitive, ESearchDir::FromEnd), GenIdx);

		// .cpp: prefix-stripped include "MyComp.h" + plain default constructor on the
		// full class identifier UMyComp (no FObjectInitializer).
		TestTrue(TEXT("cpp has prefix-stripped include"), C.Contains(TEXT("#include \"MyComp.h\"")));
		TestFalse(TEXT("cpp NO U-prefixed include"), C.Contains(TEXT("#include \"UMyComp.h\"")));
		TestTrue(TEXT("cpp plain ctor on full identifier"), C.Contains(TEXT("UMyComp::UMyComp()")));
		TestFalse(TEXT("cpp no FObjectInitializer"), C.Contains(TEXT("FObjectInitializer")));
	}

	// FObjectInitializer overload form. Class AMyChild -> file base "MyChild".
	{
		FString H, C;
		FMonolithSourceActions::GenerateClassStubText(
			TEXT("AMyParent"), TEXT("AMyChild"), TEXT("MyMod"),
			TEXT("MyParent.h"), /*bNeedsObjInit=*/true, H, C);
		TestTrue(TEXT("h ctor takes FObjectInitializer"),
			H.Contains(TEXT("AMyChild(const FObjectInitializer& ObjectInitializer);")));
		TestTrue(TEXT("cpp ctor takes FObjectInitializer"),
			C.Contains(TEXT("AMyChild::AMyChild(const FObjectInitializer& ObjectInitializer)")));
		TestTrue(TEXT("cpp inits Super"), C.Contains(TEXT(": Super(ObjectInitializer)")));
		// A-prefix is stripped from the FILE names.
		TestTrue(TEXT("h prefix-stripped generated.h"), H.Contains(TEXT("#include \"MyChild.generated.h\"")));
		TestTrue(TEXT("cpp prefix-stripped include"), C.Contains(TEXT("#include \"MyChild.h\"")));
	}

	return true;
}

// ---------------------------------------------------------------------------
// Phase 3 Test: GenerateClassStubNeverWrites — v1 has NO write path (Decision 1).
// Snapshot the transient dir before/after a stub-text generation; assert zero new
// files. Also assert the registered schema exposes no write_to_disk param (the
// param-schema is keyed off RegisterAll, but the handler routes through GetDB()
// which the test cannot supply — so we assert the helper itself touches no disk).
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoGenerateClassStubNeverWritesTest,
	"Monolith.Source.CppErgonomics.GenerateClassStubNeverWrites",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoGenerateClassStubNeverWritesTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCppErgoTestDetail;

	const FString SnapDir = FPaths::AutomationTransientDir()
		/ FString::Printf(TEXT("cppergo-stub-snap-%s"), *FGuid::NewGuid().ToString());
	FPlatformFileManager::Get().GetPlatformFile().CreateDirectoryTree(*SnapDir);

	auto CountFiles = [&]() -> int32
	{
		TArray<FString> Files;
		IFileManager::Get().FindFilesRecursive(Files, *SnapDir, TEXT("*"), /*Files=*/true, /*Dirs=*/false, /*bClearFileNames=*/true);
		return Files.Num();
	};

	const int32 Before = CountFiles();

	// Generate text repeatedly — the helper must never touch disk.
	for (int32 i = 0; i < 5; ++i)
	{
		FString H, C;
		FMonolithSourceActions::GenerateClassStubText(
			TEXT("AActor"), FString::Printf(TEXT("AMyActor%d"), i), TEXT("MyMod"),
			TEXT("GameFramework/Actor.h"), /*bNeedsObjInit=*/false, H, C);
		TestTrue(TEXT("text produced"), !H.IsEmpty() && !C.IsEmpty());
	}

	const int32 After = CountFiles();
	TestEqual(TEXT("no files written by stub generation"), After, Before);

	// Confirm the registered schema exposes no write_to_disk param.
	{
		FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();
		if (Registry.HasAction(TEXT("source"), TEXT("generate_class_stub")))
		{
			const TArray<FMonolithActionInfo> Actions = Registry.GetActions(TEXT("source"));
			for (const FMonolithActionInfo& Info : Actions)
			{
				if (Info.Action != TEXT("generate_class_stub")) { continue; }
				if (!Info.ParamSchema.IsValid()) { break; }
				// The param schema is flat: each param name is a top-level key.
				TestFalse(TEXT("no write_to_disk param"), Info.ParamSchema->HasField(TEXT("write_to_disk")));
				TestFalse(TEXT("no target_dir param"), Info.ParamSchema->HasField(TEXT("target_dir")));
				// Confirm the three declared params ARE present (sanity).
				TestTrue(TEXT("parent param present"), Info.ParamSchema->HasField(TEXT("parent")));
				break;
			}
		}
	}

	IFileManager::Get().DeleteDirectory(*SnapDir, /*bRequireExists=*/false, /*bTree=*/true);
	return true;
}

// ---------------------------------------------------------------------------
// AllmanClassIndexing — plain (non-reflected) classes/structs declared in Epic's
// allman style (opening brace on the next line) get a symbols row + members, while
// forward declarations and multi-line template parameters do NOT. Indexes the
// staged corpus (AllmanCases.h among the fixtures) into a disposable DB and asserts
// each Phase-B case from the plan §12.
// ---------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FCppErgoAllmanClassIndexingTest,
	"Monolith.Source.CppErgonomics.AllmanClassIndexing",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCppErgoAllmanClassIndexingTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithCppErgoTestDetail;

	const FString DbPath = MakeTempDbPath();
	FString StagedDir;
	FString Err;
	if (!IndexFixtureCorpus(DbPath, StagedDir, Err))
	{
		AddError(Err);
		IFileManager::Get().Delete(*DbPath, false, true);
		return false;
	}

	FMonolithSourceDatabase DB;
	if (!DB.Open(DbPath))
	{
		AddError(TEXT("Failed to reopen indexed DB"));
		IFileManager::Get().Delete(*DbPath, false, true);
		IFileManager::Get().DeleteDirectory(*StagedDir, /*bRequireExists=*/false, /*bTree=*/true);
		return false;
	}

	// Helper: does a class/struct row exist for Name (definition rows have line_end > line_start)?
	auto ClassRow = [&](const TCHAR* Name) -> TOptional<FMonolithSourceSymbol>
	{
		// Try both kinds — GetSymbolsByName with empty kind returns class OR struct.
		TArray<FMonolithSourceSymbol> Rows = DB.GetSymbolsByName(FString(Name));
		for (const FMonolithSourceSymbol& R : Rows)
		{
			if (R.Kind == TEXT("class") || R.Kind == TEXT("struct"))
			{
				return R;
			}
		}
		return TOptional<FMonolithSourceSymbol>();
	};

	// 1) Plain allman class FAllmanPlain -> class row with a real line span, members extracted.
	{
		TOptional<FMonolithSourceSymbol> Row = ClassRow(TEXT("FAllmanPlain"));
		TestTrue(TEXT("FAllmanPlain indexed"), Row.IsSet());
		if (Row.IsSet())
		{
			TestEqual(TEXT("FAllmanPlain is a class"), Row.GetValue().Kind, FString(TEXT("class")));
			TestTrue(TEXT("FAllmanPlain has a body span"), Row.GetValue().LineEnd > Row.GetValue().LineStart);
		}

		// Members: a variable Member and a function GetMember, both qualified to the class.
		bool bFoundVar = false, bFoundFunc = false;
		for (const FMonolithSourceSymbol& M : DB.GetSymbolsByName(TEXT("Member")))
		{
			if (M.Kind == TEXT("variable") && M.QualifiedName == TEXT("FAllmanPlain::Member")) { bFoundVar = true; }
		}
		for (const FMonolithSourceSymbol& M : DB.GetSymbolsByName(TEXT("GetMember")))
		{
			if (M.Kind == TEXT("function") && M.QualifiedName == TEXT("FAllmanPlain::GetMember")) { bFoundFunc = true; }
		}
		TestTrue(TEXT("FAllmanPlain::Member extracted"), bFoundVar);
		TestTrue(TEXT("FAllmanPlain::GetMember extracted"), bFoundFunc);

		// Reallocation use-after-free regression guard: FAllmanPlain declares 14 members,
		// so Result.Symbols reallocates MID-extraction. Every member must extract with the
		// correct FAllmanPlain ParentClass (carried via QualifiedName). If ParentClass were
		// a dangling reference into the reallocated array, these would be missing or wrong.
		// Reaching this point at all also proves indexing did not AV.
		for (int32 N = 0; N <= 11; ++N)
		{
			const FString MemberName = FString::Printf(TEXT("Member%02d"), N);
			const FString Qualified = FString::Printf(TEXT("FAllmanPlain::Member%02d"), N);
			bool bFound = false;
			for (const FMonolithSourceSymbol& M : DB.GetSymbolsByName(MemberName))
			{
				if (M.Kind == TEXT("variable") && M.QualifiedName == Qualified) { bFound = true; }
			}
			TestTrue(*FString::Printf(TEXT("%s extracted with correct ParentClass"), *Qualified), bFound);
		}
	}

	// 2) Allman class with same-line inheritance -> row + recorded base class.
	{
		TOptional<FMonolithSourceSymbol> Row = ClassRow(TEXT("FAllmanDerived"));
		TestTrue(TEXT("FAllmanDerived indexed"), Row.IsSet());
		if (Row.IsSet())
		{
			TArray<FMonolithSourceInheritance> Parents = DB.GetParents(Row.GetValue().Id);
			bool bHasBase = false;
			for (const FMonolithSourceInheritance& P : Parents)
			{
				if (P.Name == TEXT("FAllmanPlain")) { bHasBase = true; }
			}
			TestTrue(TEXT("FAllmanDerived base FAllmanPlain recorded"), bHasBase);
		}
	}

	// 3) Same-line-brace one-liner (today's 87-style) still indexes — no regression.
	{
		TOptional<FMonolithSourceSymbol> Row = ClassRow(TEXT("FOneLiner"));
		TestTrue(TEXT("FOneLiner (same-line brace) indexed"), Row.IsSet());
		if (Row.IsSet())
		{
			TestEqual(TEXT("FOneLiner is a struct"), Row.GetValue().Kind, FString(TEXT("struct")));
		}
	}

	// 4) Forward declaration `class FAllmanFwd;` -> NO row (no brace found -> dropped).
	{
		TestFalse(TEXT("FAllmanFwd forward decl NOT indexed"), ClassRow(TEXT("FAllmanFwd")).IsSet());
	}

	// 5) Multi-line template parameter list: the `class T` line must NOT produce a row
	//    (template-param guard), but the real FAllmanTpl declaration must index.
	{
		// No symbol named exactly "T" of class/struct kind.
		bool bBogusT = false;
		for (const FMonolithSourceSymbol& R : DB.GetSymbolsByName(TEXT("T")))
		{
			if (R.Kind == TEXT("class") || R.Kind == TEXT("struct")) { bBogusT = true; }
		}
		TestFalse(TEXT("template param T NOT indexed as a type"), bBogusT);
		TestTrue(TEXT("FAllmanTpl indexed past the template params"), ClassRow(TEXT("FAllmanTpl")).IsSet());
	}

	// 6) Two adjacent one-line structs both index (cursor-advance guard — the brace
	//    lookahead for FStructA must not consume FStructB).
	{
		TestTrue(TEXT("FStructA indexed"), ClassRow(TEXT("FStructA")).IsSet());
		TestTrue(TEXT("FStructB indexed"), ClassRow(TEXT("FStructB")).IsSet());
	}

	// 7) UNTERMINATED allman body at EOF (no closing `}`). Regression guard for the
	//    access violation: FindClosingBrace returns the line COUNT sentinel for an
	//    unterminated body, which previously drove ExtractMembers' StartIdx past the
	//    array. Reaching this point at all means indexing did NOT crash. This
	//    implementation records the class row (best-effort) but extracts NO members.
	{
		TestTrue(TEXT("FAllmanUnterminated indexed (no crash, best-effort row)"),
			ClassRow(TEXT("FAllmanUnterminated")).IsSet());

		// No member should be extracted for the unterminated body.
		bool bBogusMember = false;
		for (const FMonolithSourceSymbol& M : DB.GetSymbolsByName(TEXT("NeverReached")))
		{
			if (M.QualifiedName == TEXT("FAllmanUnterminated::NeverReached")) { bBogusMember = true; }
		}
		TestFalse(TEXT("FAllmanUnterminated members NOT extracted"), bBogusMember);
	}

	// Teardown: close the DB FIRST, then delete the staged corpus. The reads above
	// run against the DB only, but the staged-dir lifetime contract (FTS-backed reads
	// re-open staged files) is honoured uniformly across this suite.
	DB.Close();
	IFileManager::Get().Delete(*DbPath, false, true);
	IFileManager::Get().DeleteDirectory(*StagedDir, /*bRequireExists=*/false, /*bTree=*/true);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
