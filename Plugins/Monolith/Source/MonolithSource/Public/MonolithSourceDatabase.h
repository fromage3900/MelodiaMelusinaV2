#pragma once

#include "CoreMinimal.h"

class FSQLiteDatabase;
class FSQLitePreparedStatement;

DECLARE_LOG_CATEGORY_EXTERN(LogMonolithSource, Log, All);

struct FMonolithSourceSymbol
{
	int64 Id = 0;
	FString Name;
	FString QualifiedName;
	FString Kind;
	int64 FileId = 0;
	int32 LineStart = 0;
	int32 LineEnd = 0;
	FString Access;
	FString Signature;
	FString Docstring;
	bool bIsUEMacro = false;
};

struct FMonolithSourceReference
{
	int64 Id = 0;
	int64 FromSymbolId = 0;
	int64 ToSymbolId = 0;
	FString RefKind;
	int64 FileId = 0;
	int32 Line = 0;
	FString FromName;
	FString ToName;
	FString Path;
};

struct FMonolithSourceInheritance
{
	int64 Id = 0;
	FString Name;
	FString QualifiedName;
	FString Kind;
	int64 FileId = 0;
	int32 LineStart = 0;
	int32 LineEnd = 0;
};

struct FMonolithSourceModuleStats
{
	FString Name;
	FString Path;
	FString ModuleType;
	int32 FileCount = 0;
	TMap<FString, int32> SymbolCounts;
};

struct FMonolithSourceChunk
{
	int64 FileId = 0;
	int32 LineNumber = 0;
	FString Text;
};

struct FMonolithSourceFile
{
	int64 Id = 0;
	FString Path;
	int64 ModuleId = 0;
	FString FileType;
	int32 LineCount = 0;
};

/** A single symbol_deprecations row (item 3). Structured so a message containing
 *  '|' cannot corrupt the version/kind fields (parity-safe vs the offline mirrors,
 *  which read columns directly). */
struct FMonolithDeprecationRow
{
	FString Version;
	FString Message;
	FString Kind;
};

/**
 * C++ wrapper around the engine source SQLite DB.
 * Supports both read-only access (Open) and read-write access (OpenForWriting)
 * for use by both query handlers and the C++ source indexer.
 */
class MONOLITHSOURCE_API FMonolithSourceDatabase
{
public:
	FMonolithSourceDatabase();
	~FMonolithSourceDatabase();

	bool Open(const FString& DbPath);
	void Close();
	bool IsOpen() const;

	/**
	 * Borrowable access to the underlying open SQLite handle.
	 *
	 * MonolithReflectionIntel's read-only query adapters (decision / risk /
	 * cppreflect / network — ~25 actions) borrow THIS handle instead of opening
	 * a SECOND handle on the same EngineSource.db file. UE 5.7 builds SQLite with
	 * a custom `unreal-fs` VFS that permits only ONE open of a given file per
	 * process (and grabs a write reservation even on a "ReadOnly" open), so a
	 * second open in the same process is rejected with SQLITE_IOERR
	 * ("disk I/O error"). Routing the read-only SELECTs through the subsystem's
	 * already-open ReadWrite handle sidesteps the single-open VFS entirely — a
	 * read-only SELECT rides a ReadWrite handle perfectly well.
	 *
	 * Returns nullptr when the DB is not open (e.g. before the first index, or
	 * while a reindex has the handle closed). Callers MUST null-check and surface
	 * a clean "not yet indexed — run source.trigger_reindex" state, never crash.
	 *
	 * THREAD SAFETY: the returned raw pointer is NOT self-synchronising. A caller
	 * that prepares/steps statements on it MUST hold this database's lock for the
	 * duration of the borrow — take it via GetLock() / FScopeLock. All of this
	 * class's own query/write methods already lock the same FCriticalSection, so
	 * a borrower that locks correctly is serialised against them.
	 */
	FSQLiteDatabase* GetRawHandle() const;

	/**
	 * Expose the database lock so an external borrower of GetRawHandle() can
	 * serialise its statement use against this class's own locked methods.
	 * Hold an FScopeLock on this for the full borrow (handle fetch through the
	 * last Step()/Destroy() on the prepared statement).
	 */
	FCriticalSection& GetLock() const { return DbLock; }

	// --- Symbol queries ---
	TArray<FMonolithSourceSymbol> SearchSymbolsFTS(const FString& Query, int32 Limit = 20);
	TArray<FMonolithSourceSymbol> GetSymbolsByName(const FString& Name, const FString& Kind = TEXT(""));
	TOptional<FMonolithSourceSymbol> GetSymbolById(int64 Id);

	// --- File queries ---
	FString GetFilePath(int64 FileId);
	TOptional<FMonolithSourceFile> FindFileBySuffix(const FString& Suffix);
	TOptional<FMonolithSourceFile> FindFileByPath(const FString& Path);
	/** Resolve a file's owning module name + (possibly empty) build_cs_path. False if file/module not found. */
	bool GetFileModuleInfo(int64 FileId, FString& OutModuleName, FString& OutBuildCsPath);

	// --- Reference queries ---
	TArray<FMonolithSourceReference> GetReferencesTo(int64 SymbolId, const FString& RefKind = TEXT(""), int32 Limit = 50);
	TArray<FMonolithSourceReference> GetReferencesFrom(int64 SymbolId, const FString& RefKind = TEXT(""), int32 Limit = 50);

	// --- Inheritance queries ---
	TArray<FMonolithSourceInheritance> GetParents(int64 SymbolId);
	TArray<FMonolithSourceInheritance> GetChildren(int64 SymbolId);

	// --- Module queries ---
	TOptional<FMonolithSourceModuleStats> GetModuleStats(const FString& ModuleName);
	TArray<FMonolithSourceSymbol> GetSymbolsInModule(const FString& ModuleName, const FString& Kind = TEXT(""), int32 Limit = 200);

	// --- Source FTS ---
	TArray<FMonolithSourceChunk> SearchSourceFTS(const FString& Query, const FString& Scope = TEXT("all"), int32 Limit = 20);
	TArray<FMonolithSourceChunk> SearchSourceFTSFiltered(const FString& Query, const FString& Scope, const FString& Module, const FString& PathFilter, int32 Limit);
	TArray<FMonolithSourceSymbol> SearchSymbolsFTSFiltered(const FString& Query, const FString& Kind, const FString& Module, const FString& PathFilter, int32 Limit);

	// --- FTS COUNT(*) helpers (Survivor E, plan §3.E) ---
	// Issued ONLY on page 0 of cursor-paginated search_source so subsequent
	// pages can thread the cached total. Each helper issues a single
	// `SELECT COUNT(*) FROM <fts_table> WHERE <fts_table> MATCH ?` plus the
	// same JOIN/WHERE filters used by SearchSymbolsFTSFiltered /
	// SearchSourceFTSFiltered respectively. Dominant cost is ~50-200ms cold
	// cache per audit; warm cache is sub-ms.
	int32 CountSymbolsFTSFiltered(const FString& Query, const FString& Kind, const FString& Module, const FString& PathFilter);
	int32 CountSourceFTSFiltered(const FString& Query, const FString& Scope, const FString& Module, const FString& PathFilter);

	// --- FTS helper ---
	static FString EscapeFTS(const FString& Query);

	// --- Write methods (for C++ indexer) ---
	bool OpenForWriting(const FString& DbPath);
	bool CreateTablesIfNeeded();
	bool ResetDatabase();

	bool BeginTransaction();
	bool CommitTransaction();
	bool RollbackTransaction();

	int64 InsertModule(const FString& Name, const FString& Path, const FString& ModuleType, const FString& BuildCsPath = TEXT(""));
	int64 InsertFile(const FString& FilePath, int64 ModuleId, const FString& FileType, int32 LineCount, double LastModified);
	int64 InsertSymbol(const FString& Name, const FString& QualifiedName, const FString& Kind, int64 FileId, int32 LineStart, int32 LineEnd, int64 ParentSymbolId, const FString& Access, const FString& Signature, const FString& Docstring, bool bIsUEMacro);
	void InsertInheritance(int64 ChildId, int64 ParentId);
	void InsertReference(int64 FromSymbolId, int64 ToSymbolId, const FString& RefKind, int64 FileId, int32 Line);
	void InsertInclude(int64 FileId, const FString& IncludedPath, int32 Line);
	void InsertSourceChunks(int64 FileId, const TArray<FString>& Lines);

	void SetMeta(const FString& Key, const FString& Value);
	FString GetMeta(const FString& Key);

	// --- Deprecation queries (item 3) ---
	// symbol_id is NULLABLE: pass 0 to store NULL (class-body methods have no
	// symbols row — Step-0 finding). Lookups key on symbol_name.
	void InsertDeprecation(int64 SymbolId, const FString& SymbolName, const FString& Version, const FString& Message, const FString& Kind);
	/** Returns the deprecation row for the first matching symbol, or unset when not deprecated. */
	TOptional<FMonolithDeprecationRow> GetDeprecation(const FString& SymbolName);
	/** Batch lookup: maps each input symbol name that IS deprecated to its row. Absent keys = not deprecated. */
	TMap<FString, FMonolithDeprecationRow> GetDeprecationsBatch(const TArray<FString>& SymbolNames);
	/** Total rows in symbol_deprecations (used to detect the "index empty" state — Decision 3). */
	int32 GetDeprecationCount();

	// --- Incremental indexing support ---
	int32 LoadExistingSymbols(TMap<FString, int64>& OutSymbolNameToId, TMap<FString, int64>& OutClassNameToId,
		TMap<FString, TPair<int32,int32>>& OutSymbolSpans, TMap<FString, TPair<int32,int32>>& OutClassSpans);

private:
	FMonolithSourceSymbol ReadSymbolFromStatement(FSQLitePreparedStatement& Stmt);
	FMonolithSourceReference ReadReferenceFromStatement(FSQLitePreparedStatement& Stmt, bool bIsRefTo);

	FSQLiteDatabase* Database = nullptr;
	FString CachedDbPath;
	mutable FCriticalSection DbLock;
};
