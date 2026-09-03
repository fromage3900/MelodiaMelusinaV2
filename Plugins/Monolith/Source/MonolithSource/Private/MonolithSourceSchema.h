#pragma once

/**
 * DDL constants for the Monolith engine source SQLite database.
 * Must produce the EXACT same schema as Scripts/source_indexer/db/schema.py.
 *
 * Each DDL_* constant may contain multiple semicolon-separated statements.
 * Use ExecuteMulti() in MonolithSourceDatabase.cpp — FSQLiteDatabase::Execute() only
 * runs the first statement of a multi-statement string.
 * Constants are split into logical groups so callers can execute them independently.
 */
namespace MonolithSourceSchema
{
	static const int32 SchemaVersion = 2;

	// ----------------------------------------------------------------
	// Core tables + indexes
	// ----------------------------------------------------------------
	static const TCHAR* DDL_Tables =
		TEXT("CREATE TABLE IF NOT EXISTS modules (")
		TEXT("    id          INTEGER PRIMARY KEY AUTOINCREMENT,")
		TEXT("    name        TEXT NOT NULL,")
		TEXT("    path        TEXT NOT NULL,")
		TEXT("    module_type TEXT NOT NULL,")
		TEXT("    build_cs_path TEXT,")
		TEXT("    UNIQUE(name, path)")
		TEXT(");")

		TEXT("CREATE TABLE IF NOT EXISTS files (")
		TEXT("    id            INTEGER PRIMARY KEY AUTOINCREMENT,")
		TEXT("    path          TEXT NOT NULL UNIQUE,")
		TEXT("    module_id     INTEGER REFERENCES modules(id),")
		TEXT("    file_type     TEXT NOT NULL,")
		TEXT("    line_count    INTEGER NOT NULL DEFAULT 0,")
		TEXT("    last_modified REAL NOT NULL DEFAULT 0.0")
		TEXT(");")

		TEXT("CREATE TABLE IF NOT EXISTS symbols (")
		TEXT("    id               INTEGER PRIMARY KEY AUTOINCREMENT,")
		TEXT("    name             TEXT NOT NULL,")
		TEXT("    qualified_name   TEXT NOT NULL,")
		TEXT("    kind             TEXT NOT NULL,")
		TEXT("    file_id          INTEGER REFERENCES files(id),")
		TEXT("    line_start       INTEGER,")
		TEXT("    line_end         INTEGER,")
		TEXT("    parent_symbol_id INTEGER REFERENCES symbols(id),")
		TEXT("    access           TEXT,")
		TEXT("    signature        TEXT,")
		TEXT("    docstring        TEXT,")
		TEXT("    is_ue_macro      INTEGER NOT NULL DEFAULT 0")
		TEXT(");")

		TEXT("CREATE INDEX IF NOT EXISTS idx_symbols_name           ON symbols(name);")
		TEXT("CREATE INDEX IF NOT EXISTS idx_symbols_qualified_name ON symbols(qualified_name);")
		TEXT("CREATE INDEX IF NOT EXISTS idx_symbols_kind           ON symbols(kind);")
		TEXT("CREATE INDEX IF NOT EXISTS idx_symbols_file_id        ON symbols(file_id);")
		TEXT("CREATE INDEX IF NOT EXISTS idx_symbols_parent         ON symbols(parent_symbol_id);")

		TEXT("CREATE TABLE IF NOT EXISTS inheritance (")
		TEXT("    id        INTEGER PRIMARY KEY AUTOINCREMENT,")
		TEXT("    child_id  INTEGER NOT NULL REFERENCES symbols(id),")
		TEXT("    parent_id INTEGER NOT NULL REFERENCES symbols(id),")
		TEXT("    UNIQUE(child_id, parent_id)")
		TEXT(");")

		TEXT("CREATE TABLE IF NOT EXISTS \"references\" (")
		TEXT("    id             INTEGER PRIMARY KEY AUTOINCREMENT,")
		TEXT("    from_symbol_id INTEGER NOT NULL REFERENCES symbols(id),")
		TEXT("    to_symbol_id   INTEGER NOT NULL REFERENCES symbols(id),")
		TEXT("    ref_kind       TEXT NOT NULL,")
		TEXT("    file_id        INTEGER REFERENCES files(id),")
		TEXT("    line           INTEGER")
		TEXT(");")

		TEXT("CREATE INDEX IF NOT EXISTS idx_refs_from ON \"references\"(from_symbol_id);")
		TEXT("CREATE INDEX IF NOT EXISTS idx_refs_to   ON \"references\"(to_symbol_id);")
		TEXT("CREATE INDEX IF NOT EXISTS idx_refs_kind ON \"references\"(ref_kind);")

		TEXT("CREATE TABLE IF NOT EXISTS includes (")
		TEXT("    id            INTEGER PRIMARY KEY AUTOINCREMENT,")
		TEXT("    file_id       INTEGER NOT NULL REFERENCES files(id),")
		TEXT("    included_path TEXT NOT NULL,")
		TEXT("    line          INTEGER")
		TEXT(");")

		// Schema v2 (item 3): UE_DEPRECATED extraction. symbol_id is NULLABLE —
		// class-body method declarations are NOT indexed as `symbols` rows
		// (Step-0 finding), so the extractor parses the symbol NAME from the
		// declaration text after the macro and stores symbol_id = NULL when it
		// cannot resolve a symbols row. Lookups (check_deprecations) key on
		// symbol_name, so a NULL symbol_id does not break the read path.
		TEXT("CREATE TABLE IF NOT EXISTS symbol_deprecations (")
		TEXT("    id          INTEGER PRIMARY KEY AUTOINCREMENT,")
		TEXT("    symbol_id   INTEGER REFERENCES symbols(id),")
		TEXT("    symbol_name TEXT NOT NULL,")
		TEXT("    version     TEXT,")
		TEXT("    message     TEXT,")
		TEXT("    kind        TEXT NOT NULL")
		TEXT(");")

		TEXT("CREATE INDEX IF NOT EXISTS idx_deprecations_name ON symbol_deprecations(symbol_name);")

		TEXT("CREATE TABLE IF NOT EXISTS meta (")
		TEXT("    key   TEXT PRIMARY KEY,")
		TEXT("    value TEXT")
		TEXT(");");

	// ----------------------------------------------------------------
	// FTS5 virtual tables
	// ----------------------------------------------------------------
	static const TCHAR* DDL_FTS =
		TEXT("CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(")
		TEXT("    name, qualified_name, docstring,")
		TEXT("    content=symbols, content_rowid=id")
		TEXT(");")

		TEXT("CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(")
		TEXT("    file_id UNINDEXED, line_number UNINDEXED, text")
		TEXT(");");

	// ----------------------------------------------------------------
	// Triggers to keep symbols_fts in sync with symbols
	// ----------------------------------------------------------------
	static const TCHAR* DDL_Triggers =
		TEXT("CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN")
		TEXT("    INSERT INTO symbols_fts(rowid, name, qualified_name, docstring)")
		TEXT("    VALUES (new.id, new.name, new.qualified_name, new.docstring);")
		TEXT("END;")

		TEXT("CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN")
		TEXT("    INSERT INTO symbols_fts(symbols_fts, rowid, name, qualified_name, docstring)")
		TEXT("    VALUES ('delete', old.id, old.name, old.qualified_name, old.docstring);")
		TEXT("END;");

	// ----------------------------------------------------------------
	// DROP statements for ResetDatabase()
	// ----------------------------------------------------------------
	static const TCHAR* DDL_Drop =
		TEXT("DROP TRIGGER IF EXISTS symbols_ad;")
		TEXT("DROP TRIGGER IF EXISTS symbols_ai;")
		TEXT("DROP TABLE IF EXISTS symbols_fts;")
		TEXT("DROP TABLE IF EXISTS source_fts;")
		TEXT("DROP TABLE IF EXISTS symbol_deprecations;")
		TEXT("DROP TABLE IF EXISTS includes;")
		TEXT("DROP TABLE IF EXISTS \"references\";")
		TEXT("DROP TABLE IF EXISTS inheritance;")
		TEXT("DROP TABLE IF EXISTS symbols;")
		TEXT("DROP TABLE IF EXISTS files;")
		TEXT("DROP TABLE IF EXISTS modules;")
		TEXT("DROP TABLE IF EXISTS meta;");

} // namespace MonolithSourceSchema
