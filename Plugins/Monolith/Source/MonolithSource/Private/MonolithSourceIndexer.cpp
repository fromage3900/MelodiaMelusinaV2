#include "MonolithSourceIndexer.h"
#include "MonolithSourceDatabase.h"
#include "MonolithCppParser.h"
#include "MonolithShaderParser.h"
#include "MonolithReferenceBuilder.h"
#include "HAL/RunnableThread.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"
#include "Internationalization/Regex.h"

namespace MonolithSourceIndexerDetail
{
	// Decision 2: derive a module's <Module>.Build.cs path from its Source/<Module>/
	// dir. Tries <ModulePath>/<ModuleName>.Build.cs first (the common convention);
	// falls back to the first *.Build.cs found in the dir (module name != dir name).
	// Returns empty when no Build.cs exists (e.g. the Shaders pseudo-module).
	static FString DeriveBuildCsPath(const FString& ModulePath, const FString& ModuleName)
	{
		const FString Candidate = ModulePath / (ModuleName + TEXT(".Build.cs"));
		if (IFileManager::Get().FileExists(*Candidate))
		{
			return Candidate;
		}

		TArray<FString> Found;
		IFileManager::Get().FindFiles(Found, *(ModulePath / TEXT("*.Build.cs")), /*Files=*/true, /*Directories=*/false);
		if (Found.Num() > 0)
		{
			return ModulePath / Found[0];
		}
		return FString();
	}
}

// ============================================================
// Construction / Destruction
// ============================================================

FMonolithSourceIndexer::FMonolithSourceIndexer()
{
}

FMonolithSourceIndexer::~FMonolithSourceIndexer()
{
	RequestStop();
	if (Thread)
	{
		Thread->WaitForCompletion();
		delete Thread;
		Thread = nullptr;
	}
}

// ============================================================
// Configuration setters
// ============================================================

void FMonolithSourceIndexer::SetSourcePath(const FString& InPath)   { SourcePath = InPath; }
void FMonolithSourceIndexer::SetShaderPath(const FString& InPath)   { ShaderPath = InPath; }
void FMonolithSourceIndexer::SetProjectPath(const FString& InPath)  { ProjectPath = InPath; }
void FMonolithSourceIndexer::SetDatabasePath(const FString& InPath) { DbPath = InPath; }
void FMonolithSourceIndexer::SetCleanBuild(bool bClean)             { bCleanBuild = bClean; }
void FMonolithSourceIndexer::SetIndexProjectSource(bool bIndex)     { bIndexProjectSource = bIndex; }

// ============================================================
// Thread control
// ============================================================

bool FMonolithSourceIndexer::StartAsync()
{
	if (bIsRunning) return false;
	Thread = FRunnableThread::Create(this, TEXT("MonolithSourceIndexer"), 0, TPri_BelowNormal);
	return Thread != nullptr;
}

bool FMonolithSourceIndexer::RunSynchronous()
{
	if (bIsRunning) return false;
	Init();
	Run();
	return true;
}

void FMonolithSourceIndexer::RequestStop()
{
	bShouldStop = true;
}

bool FMonolithSourceIndexer::IsRunning() const
{
	return bIsRunning;
}

FSourceIndexDiagnostics FMonolithSourceIndexer::GetDiagnostics() const
{
	FScopeLock Lock(&DiagLock);
	return Diagnostics;
}

// ============================================================
// FRunnable interface
// ============================================================

bool FMonolithSourceIndexer::Init()
{
	return true;
}

void FMonolithSourceIndexer::Stop()
{
	bShouldStop = true;
}

uint32 FMonolithSourceIndexer::Run()
{
	bIsRunning = true;

	FMonolithSourceDatabase DB;
	if (!DB.OpenForWriting(DbPath))
	{
		UE_LOG(LogMonolithSource, Error, TEXT("Indexer: Failed to open DB for writing: %s"), *DbPath);
		bIsRunning = false;
		return 1;
	}

	if (bCleanBuild)
	{
		DB.ResetDatabase();
	}
	else
	{
		DB.CreateTablesIfNeeded();
	}

	// --- Engine phase ---
	if (!SourcePath.IsEmpty())
	{
		TArray<FModuleEntry> EngineModules;
		DiscoverEngineModules(EngineModules);

		UE_LOG(LogMonolithSource, Log, TEXT("Indexer: Found %d engine modules"), EngineModules.Num());

		for (int32 i = 0; i < EngineModules.Num() && !bShouldStop; ++i)
		{
			IndexModule(EngineModules[i], DB);
			OnProgress.Broadcast(EngineModules[i].Name, i + 1, EngineModules.Num(),
				TotalFilesProcessed.Load(), TotalSymbolsExtracted.Load());
		}
	}

	// --- Project phase ---
	if (bIndexProjectSource && !ProjectPath.IsEmpty() && !bShouldStop)
	{
		// If NOT clean build, load existing engine symbols for cross-reference resolution
		if (!bCleanBuild)
		{
			UE_LOG(LogMonolithSource, Log, TEXT("Indexer: Loading existing symbols for incremental indexing..."));
			DB.LoadExistingSymbols(SymbolNameToId, ClassNameToId, SymbolSpans, ClassSpans);
		}

		TArray<FModuleEntry> ProjectModules;
		DiscoverProjectModules(ProjectModules);

		UE_LOG(LogMonolithSource, Log, TEXT("Indexer: Found %d project modules"), ProjectModules.Num());

		for (int32 i = 0; i < ProjectModules.Num() && !bShouldStop; ++i)
		{
			IndexModule(ProjectModules[i], DB);
			OnProgress.Broadcast(ProjectModules[i].Name, i + 1, ProjectModules.Num(),
				TotalFilesProcessed.Load(), TotalSymbolsExtracted.Load());
		}
	}

	// --- Finalize ---
	if (!bShouldStop)
	{
		Finalize(DB);
	}

	DB.Close();
	bIsRunning = false;

	const int32 Files = TotalFilesProcessed.Load();
	const int32 Symbols = TotalSymbolsExtracted.Load();
	const int32 Errors = TotalErrors.Load();

	UE_LOG(LogMonolithSource, Log, TEXT("Indexer complete: %d files, %d symbols, %d errors"), Files, Symbols, Errors);
	OnComplete.Broadcast(Files, Symbols, Errors);

	return 0;
}

// ============================================================
// Module discovery
// ============================================================

void FMonolithSourceIndexer::DiscoverEngineModules(TArray<FModuleEntry>& OutModules)
{
	// Runtime, Editor, Developer, Programs categories
	const TArray<FString> Categories = { TEXT("Runtime"), TEXT("Editor"), TEXT("Developer"), TEXT("Programs") };

	for (const FString& Category : Categories)
	{
		FString CategoryDir = SourcePath / Category;
		IFileManager::Get().IterateDirectory(*CategoryDir, [&](const TCHAR* Path, bool bIsDir) -> bool
		{
			if (bIsDir)
			{
				FString DirName = FPaths::GetCleanFilename(Path);
				OutModules.Add({ FString(Path), DirName, Category,
					MonolithSourceIndexerDetail::DeriveBuildCsPath(FString(Path), DirName) });
			}
			return true; // continue iteration
		});
	}

	// Engine plugins — find Source dirs under Engine/Plugins/
	// SourcePath is Engine/Source, parent is Engine/
	FString PluginsDir = FPaths::GetPath(SourcePath) / TEXT("Plugins");

	IFileManager::Get().IterateDirectoryRecursively(*PluginsDir, [&](const TCHAR* Path, bool bIsDir) -> bool
	{
		if (bIsDir)
		{
			FString DirName = FPaths::GetCleanFilename(Path);
			if (DirName == TEXT("Source"))
			{
				FString ParentDir = FPaths::GetPath(FString(Path));
				FString ModuleName = FPaths::GetCleanFilename(ParentDir);
				OutModules.Add({ FString(Path), ModuleName, TEXT("Plugin"),
					MonolithSourceIndexerDetail::DeriveBuildCsPath(FString(Path), ModuleName) });
			}
		}
		return true;
	});

	// Shaders — no Build.cs
	if (!ShaderPath.IsEmpty())
	{
		OutModules.Add({ ShaderPath, TEXT("Shaders"), TEXT("Shaders"), FString() });
	}
}

void FMonolithSourceIndexer::DiscoverProjectModules(TArray<FModuleEntry>& OutModules)
{
	// Top-level project modules: ProjectPath/Source/*/
	FString ProjectSourceDir = ProjectPath / TEXT("Source");
	IFileManager::Get().IterateDirectory(*ProjectSourceDir, [&](const TCHAR* Path, bool bIsDir) -> bool
	{
		if (bIsDir)
		{
			FString DirName = FPaths::GetCleanFilename(Path);
			OutModules.Add({ FString(Path), DirName, TEXT("Project"),
				MonolithSourceIndexerDetail::DeriveBuildCsPath(FString(Path), DirName) });
		}
		return true;
	});

	// Plugin modules: ProjectPath/Plugins/**/Source/
	FString ProjectPluginsDir = ProjectPath / TEXT("Plugins");
	IFileManager::Get().IterateDirectoryRecursively(*ProjectPluginsDir, [&](const TCHAR* Path, bool bIsDir) -> bool
	{
		if (bIsDir)
		{
			FString DirName = FPaths::GetCleanFilename(Path);
			if (DirName == TEXT("Source"))
			{
				FString ParentDir = FPaths::GetPath(FString(Path));
				FString ModuleName = FPaths::GetCleanFilename(ParentDir);
				FString FullPath = FString(Path);

				// Detect GameFeature plugins
				FString ModuleType = FullPath.Contains(TEXT("GameFeatures")) ? TEXT("GameFeature") : TEXT("Plugin");
				OutModules.Add({ FullPath, ModuleName, ModuleType,
					MonolithSourceIndexerDetail::DeriveBuildCsPath(FullPath, ModuleName) });
			}
		}
		return true;
	});
}

// ============================================================
// Module indexing
// ============================================================

void FMonolithSourceIndexer::IndexModule(const FModuleEntry& Module, FMonolithSourceDatabase& DB)
{
	int64 ModuleId = DB.InsertModule(Module.Name, Module.Path, Module.Type, Module.BuildCsPath);

	// Collect all source files for this module
	TArray<FString> Files;

	if (Module.Type == TEXT("Shaders"))
	{
		// Shader module — only shader files
		IFileManager::Get().FindFilesRecursive(Files, *Module.Path, TEXT("*.usf"), true, false, true);
		IFileManager::Get().FindFilesRecursive(Files, *Module.Path, TEXT("*.ush"), true, false, false); // bClearFileNames=false!
	}
	else
	{
		// C++ module — headers, source, inline files
		IFileManager::Get().FindFilesRecursive(Files, *Module.Path, TEXT("*.h"), true, false, true);
		IFileManager::Get().FindFilesRecursive(Files, *Module.Path, TEXT("*.cpp"), true, false, false); // bClearFileNames=false!
		IFileManager::Get().FindFilesRecursive(Files, *Module.Path, TEXT("*.inl"), true, false, false); // bClearFileNames=false!
	}

	DB.BeginTransaction();

	for (const FString& FilePath : Files)
	{
		if (bShouldStop) break;

		FString Ext = FPaths::GetExtension(FilePath).ToLower();
		int32 SymbolCount = 0;

		if (Ext == TEXT("usf") || Ext == TEXT("ush"))
		{
			SymbolCount = IndexShaderFile(FilePath, ModuleId, DB);
		}
		else
		{
			SymbolCount = IndexCppFile(FilePath, ModuleId, DB);
		}

		TotalFilesProcessed++;
		TotalSymbolsExtracted += SymbolCount;
	}

	DB.CommitTransaction();
}

// ============================================================
// File indexing
// ============================================================

int32 FMonolithSourceIndexer::IndexCppFile(const FString& FilePath, int64 ModuleId, FMonolithSourceDatabase& DB)
{
	FMonolithCppParser Parser;
	FParsedFileResult ParseResult = Parser.ParseFile(FilePath);

	FString Ext = FPaths::GetExtension(FilePath).ToLower();
	FString FileType;
	if (Ext == TEXT("h"))        FileType = TEXT("header");
	else if (Ext == TEXT("cpp")) FileType = TEXT("source");
	else                         FileType = TEXT("inline"); // .inl

	// Get file modification time
	FDateTime ModTime = IFileManager::Get().GetTimeStamp(*FilePath);
	double LastModified = static_cast<double>(ModTime.ToUnixTimestamp());

	int64 FileId = DB.InsertFile(FilePath, ModuleId, FileType, ParseResult.SourceLines.Num(), LastModified);
	NewFileIds.Add(FileId);

	// Includes
	for (const FString& IncPath : ParseResult.Includes)
	{
		int32 IncLine = 0;
		for (int32 i = 0; i < ParseResult.SourceLines.Num(); ++i)
		{
			if (ParseResult.SourceLines[i].Contains(IncPath) && ParseResult.SourceLines[i].Contains(TEXT("#include")))
			{
				IncLine = i + 1; // 1-based
				break;
			}
		}
		DB.InsertInclude(FileId, IncPath, IncLine);
	}

	// Symbols
	int32 SymbolCount = 0;
	for (const FParsedSourceSymbol& Sym : ParseResult.Symbols)
	{
		if (Sym.Kind == TEXT("include")) continue;

		FString QualifiedName = Sym.Name;
		if (!Sym.ParentClass.IsEmpty())
		{
			QualifiedName = Sym.ParentClass + TEXT("::") + Sym.Name;
		}

		// Look up parent symbol id
		int64 ParentSymbolId = 0;
		if (!Sym.ParentClass.IsEmpty())
		{
			const int64* ParentId = SymbolNameToId.Find(Sym.ParentClass);
			if (ParentId) ParentSymbolId = *ParentId;
		}

		int64 SymId = DB.InsertSymbol(
			Sym.Name, QualifiedName, Sym.Kind,
			FileId, Sym.LineStart, Sym.LineEnd,
			ParentSymbolId, Sym.Access, Sym.Signature, Sym.Docstring,
			Sym.bIsUEMacro
		);

		// Update symbol maps
		UpdateSymbolMap(Sym.Name, SymId, Sym.LineStart, Sym.LineEnd);
		if (QualifiedName != Sym.Name)
		{
			UpdateSymbolMap(QualifiedName, SymId, Sym.LineStart, Sym.LineEnd);
		}

		// Class/struct tracking
		if (Sym.Kind == TEXT("class") || Sym.Kind == TEXT("struct"))
		{
			UpdateClassMap(Sym.Name, SymId, Sym.LineStart, Sym.LineEnd);

			if (Sym.BaseClasses.Num() > 0)
			{
				PendingBaseClasses.Add(Sym.Name, Sym.BaseClasses);

				FScopeLock Lock(&DiagLock);
				Diagnostics.WithBaseClasses++;
			}

			{
				FScopeLock Lock(&DiagLock);
				if (Sym.LineEnd > Sym.LineStart) Diagnostics.Definitions++;
				else Diagnostics.ForwardDecls++;
			}
		}

		SymbolCount++;
	}

	// --- Deprecation extraction (item 3) ---
	// LOCAL FRegexPattern/FRegexMatcher only — never static/global (ICU init
	// gotcha; the matcher relies on the internationalization system, and a
	// file-scope instance would construct before ICU is ready). The indexer runs
	// after engine init, so constructing locals here is safe.
	//
	// Matches UE_DEPRECATED / UE_DEPRECATED_FORENGINE / UE_DEPRECATED_FORGAME with
	//   (Version, "Message")  — Version may be absent (e.g. some FORGAME forms).
	// Capture groups: 1 = kind suffix (_FORENGINE|_FORGAME|empty), 2 = version,
	//                 3 = message.
	{
		const FRegexPattern DeprPattern(
			TEXT("UE_DEPRECATED(_FORENGINE|_FORGAME)?\\s*\\(\\s*([\\d.]+)?\\s*,?\\s*\"([^\"]*)\""));

		const TArray<FString>& Lines = ParseResult.SourceLines;
		for (int32 i = 0; i < Lines.Num(); ++i)
		{
			FRegexMatcher Matcher(DeprPattern, Lines[i]);
			if (!Matcher.FindNext())
			{
				continue;
			}

			const FString Suffix  = Matcher.GetCaptureGroup(1);
			const FString Version = Matcher.GetCaptureGroup(2);
			const FString Message = Matcher.GetCaptureGroup(3);

			FString Kind = TEXT("UE_DEPRECATED");
			if (Suffix == TEXT("_FORENGINE")) Kind = TEXT("UE_DEPRECATED_FORENGINE");
			else if (Suffix == TEXT("_FORGAME")) Kind = TEXT("UE_DEPRECATED_FORGAME");

			// Parse the symbol NAME from the declaration text following the macro.
			// Class-body methods have no symbols row (Step-0 finding), so we scan
			// forward over intervening specifier/macro lines (UPROPERTY/UFUNCTION/
			// UE_API/comments/blanks) to the first real declaration, then take the
			// identifier immediately before '(' (function) or before ';'/'=' (var).
			FString SymbolName;
			for (int32 j = i; j < Lines.Num() && j < i + 8; ++j)
			{
				FString Decl = Lines[j].TrimStartAndEnd();

				// On the macro line itself, strip the macro invocation up to the
				// LAST ')' (the macro's closing paren; using the last paren tolerates
				// a message string that itself contains "()", e.g. "Use Foo() instead").
				if (j == i)
				{
					int32 CloseIdx = INDEX_NONE;
					if (Decl.FindLastChar(TEXT(')'), CloseIdx))
					{
						Decl = Decl.Mid(CloseIdx + 1).TrimStartAndEnd();
					}
					else
					{
						continue; // macro args spill to next line — skip this one
					}
				}

				if (Decl.IsEmpty()) continue;
				if (Decl.StartsWith(TEXT("//")) || Decl.StartsWith(TEXT("/*")) || Decl.StartsWith(TEXT("*"))) continue;

				// Skip pure specifier/macro lines (UPROPERTY(), UFUNCTION(...), etc.)
				// and lone UE_API-style export macros — keep scanning for the decl.
				if (Decl.StartsWith(TEXT("UPROPERTY")) || Decl.StartsWith(TEXT("UFUNCTION"))
					|| Decl.StartsWith(TEXT("UDELEGATE")) || Decl.StartsWith(TEXT("UE_DEPRECATED")))
				{
					continue;
				}

				// Function form: identifier immediately before the first '('.
				int32 ParenIdx = INDEX_NONE;
				int32 SemiIdx = INDEX_NONE;
				int32 EqIdx = INDEX_NONE;
				Decl.FindChar(TEXT('('), ParenIdx);
				Decl.FindChar(TEXT(';'), SemiIdx);
				Decl.FindChar(TEXT('='), EqIdx);

				int32 EndIdx = INDEX_NONE;
				if (ParenIdx != INDEX_NONE)
				{
					EndIdx = ParenIdx; // function
				}
				else if (SemiIdx != INDEX_NONE || EqIdx != INDEX_NONE)
				{
					EndIdx = (SemiIdx != INDEX_NONE && (EqIdx == INDEX_NONE || SemiIdx < EqIdx)) ? SemiIdx : EqIdx; // variable / property
				}

				if (EndIdx == INDEX_NONE)
				{
					continue; // declaration continues on the next line
				}

				// Walk backwards from EndIdx over the trailing identifier.
				int32 NameEnd = EndIdx;
				while (NameEnd > 0 && FChar::IsWhitespace(Decl[NameEnd - 1])) --NameEnd;
				int32 NameStart = NameEnd;
				while (NameStart > 0)
				{
					const TCHAR Ch = Decl[NameStart - 1];
					if (FChar::IsAlnum(Ch) || Ch == TEXT('_'))
					{
						--NameStart;
					}
					else
					{
						break;
					}
				}
				if (NameEnd > NameStart)
				{
					SymbolName = Decl.Mid(NameStart, NameEnd - NameStart);
				}
				break;
			}

			if (SymbolName.IsEmpty())
			{
				continue; // could not resolve a name — skip rather than store garbage
			}

			// Link to a symbols row when one exists; NULL (0) otherwise.
			int64 LinkedSymId = 0;
			if (const int64* Found = SymbolNameToId.Find(SymbolName))
			{
				LinkedSymId = *Found;
			}

			DB.InsertDeprecation(LinkedSymId, SymbolName, Version, Message, Kind);
		}
	}

	// Source FTS chunks
	DB.InsertSourceChunks(FileId, ParseResult.SourceLines);

	return SymbolCount;
}

int32 FMonolithSourceIndexer::IndexShaderFile(const FString& FilePath, int64 ModuleId, FMonolithSourceDatabase& DB)
{
	FMonolithShaderParser Parser;
	FParsedFileResult ParseResult = Parser.ParseFile(FilePath);

	FString Ext = FPaths::GetExtension(FilePath).ToLower();
	FString FileType = (Ext == TEXT("ush")) ? TEXT("shader_header") : TEXT("shader");

	FDateTime ModTime = IFileManager::Get().GetTimeStamp(*FilePath);
	double LastModified = static_cast<double>(ModTime.ToUnixTimestamp());

	int64 FileId = DB.InsertFile(FilePath, ModuleId, FileType, ParseResult.SourceLines.Num(), LastModified);
	NewFileIds.Add(FileId);

	// Includes
	for (const FString& IncPath : ParseResult.Includes)
	{
		int32 IncLine = 0;
		for (int32 i = 0; i < ParseResult.SourceLines.Num(); ++i)
		{
			if (ParseResult.SourceLines[i].Contains(IncPath) && ParseResult.SourceLines[i].Contains(TEXT("#include")))
			{
				IncLine = i + 1;
				break;
			}
		}
		DB.InsertInclude(FileId, IncPath, IncLine);
	}

	// Symbols — shader symbols do NOT go into SymbolNameToId (prevents false cross-references)
	int32 SymbolCount = 0;
	for (const FParsedSourceSymbol& Sym : ParseResult.Symbols)
	{
		if (Sym.Kind == TEXT("include")) continue;

		FString QualifiedName = Sym.Name;
		if (!Sym.ParentClass.IsEmpty())
		{
			QualifiedName = Sym.ParentClass + TEXT("::") + Sym.Name;
		}

		DB.InsertSymbol(
			Sym.Name, QualifiedName, Sym.Kind,
			FileId, Sym.LineStart, Sym.LineEnd,
			0, Sym.Access, Sym.Signature, Sym.Docstring,
			Sym.bIsUEMacro
		);

		SymbolCount++;
	}

	// Source FTS chunks
	DB.InsertSourceChunks(FileId, ParseResult.SourceLines);

	return SymbolCount;
}

// ============================================================
// Symbol map helpers
// ============================================================

void FMonolithSourceIndexer::UpdateSymbolMap(const FString& Name, int64 SymId, int32 LineStart, int32 LineEnd)
{
	if (Name.StartsWith(TEXT("_bases_"))) return;

	bool bIsDefinition = (LineEnd > LineStart);
	TPair<int32, int32>* ExistingSpan = SymbolSpans.Find(Name);

	if (!ExistingSpan)
	{
		SymbolNameToId.Add(Name, SymId);
		SymbolSpans.Add(Name, TPair<int32, int32>(LineStart, LineEnd));
	}
	else if (bIsDefinition && ExistingSpan->Value <= ExistingSpan->Key)
	{
		// Overwrite forward decl with definition
		SymbolNameToId[Name] = SymId;
		*ExistingSpan = TPair<int32, int32>(LineStart, LineEnd);
	}
}

void FMonolithSourceIndexer::UpdateClassMap(const FString& Name, int64 SymId, int32 LineStart, int32 LineEnd)
{
	if (Name.StartsWith(TEXT("_bases_"))) return;

	bool bIsDefinition = (LineEnd > LineStart);
	TPair<int32, int32>* ExistingSpan = ClassSpans.Find(Name);

	if (!ExistingSpan)
	{
		ClassNameToId.Add(Name, SymId);
		ClassSpans.Add(Name, TPair<int32, int32>(LineStart, LineEnd));
	}
	else if (bIsDefinition && ExistingSpan->Value <= ExistingSpan->Key)
	{
		// Overwrite forward decl with definition
		ClassNameToId[Name] = SymId;
		*ExistingSpan = TPair<int32, int32>(LineStart, LineEnd);
	}
}

// ============================================================
// Finalization — inheritance resolution + reference extraction
// ============================================================

void FMonolithSourceIndexer::Finalize(FMonolithSourceDatabase& DB)
{
	UE_LOG(LogMonolithSource, Log, TEXT("Indexer: Finalizing — resolving inheritance..."));

	// Phase 1: Resolve inheritance
	DB.BeginTransaction();
	for (const auto& Pair : PendingBaseClasses)
	{
		const FString& ChildName = Pair.Key;
		const TArray<FString>& BaseClasses = Pair.Value;

		const int64* ChildId = ClassNameToId.Find(ChildName);
		if (!ChildId)
		{
			FScopeLock Lock(&DiagLock);
			Diagnostics.InheritanceFailed += BaseClasses.Num();
			continue;
		}

		for (const FString& BaseName : BaseClasses)
		{
			const int64* ParentId = ClassNameToId.Find(BaseName);
			if (ParentId)
			{
				DB.InsertInheritance(*ChildId, *ParentId);
				FScopeLock Lock(&DiagLock);
				Diagnostics.InheritanceResolved++;
			}
			else
			{
				FScopeLock Lock(&DiagLock);
				Diagnostics.InheritanceFailed++;
			}
		}
	}
	DB.CommitTransaction();

	// Phase 2: Reference extraction (only new files)
	UE_LOG(LogMonolithSource, Log, TEXT("Indexer: Extracting references from %d new files..."), NewFileIds.Num());

	FMonolithReferenceBuilder RefBuilder(DB, SymbolNameToId);

	DB.BeginTransaction();
	int32 RefCount = 0;
	int32 FilesProcessed = 0;

	for (int64 FileId : NewFileIds)
	{
		if (bShouldStop) break;

		FString Path = DB.GetFilePath(FileId);
		if (Path == TEXT("<unknown>")) continue;

		// Only process C++ files for references (not shaders)
		FString Ext = FPaths::GetExtension(Path).ToLower();
		if (Ext != TEXT("h") && Ext != TEXT("cpp") && Ext != TEXT("inl")) continue;

		int32 Refs = RefBuilder.ExtractReferences(Path, FileId);
		RefCount += Refs;
		FilesProcessed++;

		// Periodic commit every 500 files to keep WAL size manageable
		if (FilesProcessed % 500 == 0)
		{
			DB.CommitTransaction();
			DB.BeginTransaction();
			UE_LOG(LogMonolithSource, Log, TEXT("  References: %d files processed, %d refs found"), FilesProcessed, RefCount);
		}
	}
	DB.CommitTransaction();

	UE_LOG(LogMonolithSource, Log, TEXT("Indexer: Reference extraction complete — %d refs from %d files"), RefCount, FilesProcessed);

	// Set meta
	DB.SetMeta(TEXT("schema_version"), FString::FromInt(1));
	DB.SetMeta(TEXT("index_timestamp"), FString::FromInt(FDateTime::UtcNow().ToUnixTimestamp()));
	DB.SetMeta(TEXT("total_files"), FString::FromInt(TotalFilesProcessed.Load()));
	DB.SetMeta(TEXT("total_symbols"), FString::FromInt(TotalSymbolsExtracted.Load()));
}
