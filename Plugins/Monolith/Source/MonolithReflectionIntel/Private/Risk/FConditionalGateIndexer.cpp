// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// FConditionalGateIndexer — implementation. Regex sweep + idempotent write.

#include "Risk/FConditionalGateIndexer.h"
#include "Risk/RiskSchema.h"
#include "MonolithReflectionIntelModule.h"
#include "Shared/RIPathUtils.h"

#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "SQLiteDatabase.h"

namespace
{
	// ToProjectRelative hoisted to Private/Shared/RIPathUtils.{h,cpp}
	// (RIToProjectRelative) to avoid unity-build collisions across the three
	// indexers that carried a byte-identical copy. Behaviour unchanged.

	bool HasGateableExtension(const FString& Path)
	{
		const FString Lower = Path.ToLower();
		return Lower.EndsWith(TEXT(".cpp")) ||
			   Lower.EndsWith(TEXT(".h")) ||
			   Lower.EndsWith(TEXT(".hpp")) ||
			   Lower.EndsWith(TEXT(".inl")) ||
			   Lower.EndsWith(TEXT(".build.cs"));
	}

	bool IsBuildCsFile(const FString& Path)
	{
		return Path.EndsWith(TEXT(".Build.cs"), ESearchCase::IgnoreCase);
	}

	void WalkRecursive(const FString& Root, TArray<FString>& OutFiles)
	{
		class FVisitor : public IPlatformFile::FDirectoryVisitor
		{
		public:
			TArray<FString>& Out;
			explicit FVisitor(TArray<FString>& InOut) : Out(InOut) {}
			virtual bool Visit(const TCHAR* FilenameOrDirectory, bool bIsDirectory) override
			{
				if (!bIsDirectory)
				{
					const FString Path(FilenameOrDirectory);
					if (HasGateableExtension(Path))
					{
						Out.Add(Path);
					}
				}
				return true;
			}
		};
		FVisitor Visitor(OutFiles);
		IFileManager::Get().IterateDirectoryRecursively(*Root, Visitor);
	}
}

FConditionalGateIndexer::FConditionalGateIndexer()
	// Phase 2 code-quality item 4 — patterns constructed once per indexer
	// instance. Both are case-sensitive (Build.cs probes are PascalCase, C++
	// macros are SCREAMING_SNAKE_CASE; case-insensitive matching would catch
	// false positives like local-variable names ending in "_with").
	: IfWithPattern(
		TEXT("^\\s*#\\s*(?:if|ifdef|elif)\\s+(?:!\\s*)?(?:defined\\s*\\(\\s*)?(WITH_[A-Z0-9_]+)"))
	, BuildCsProbePattern(
		TEXT("\\b(bHas[A-Z][A-Za-z0-9_]*)\\b"))
{
}

bool FConditionalGateIndexer::Run(
	FSQLiteDatabase& DB, const TArray<FString>& ScanRoots, FString& OutStatus)
{
	ensure(IsInGameThread());

	if (!EnsureSchema(DB))
	{
		OutStatus = TEXT("FConditionalGateIndexer: schema bootstrap failed");
		UE_LOG(LogMonolithReflectionIntel, Error, TEXT("%s"), *OutStatus);
		return false;
	}

	// Wipe-and-rewrite. AUTOINCREMENT id resets — fine, no foreign refs.
	{
		FSQLitePreparedStatement Del;
		Del.Create(DB, TEXT("DELETE FROM reflect_conditional_gates;"));
		Del.Execute();
	}

	const FString ProjectRoot =
		FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());

	TArray<FConditionalGateRow> AllRows;
	int32 FilesScanned = 0;

	for (const FString& RawRoot : ScanRoots)
	{
		FString Root = RawRoot;
		if (FPaths::IsRelative(Root))
		{
			Root = FPaths::ConvertRelativePathToFull(ProjectRoot / Root);
		}
		Root = FPaths::ConvertRelativePathToFull(Root);

		IPlatformFile& Pf = FPlatformFileManager::Get().GetPlatformFile();
		if (!Pf.DirectoryExists(*Root))
		{
			UE_LOG(LogMonolithReflectionIntel, Verbose,
				TEXT("ConditionalGateIndexer: skipping missing root '%s'"), *Root);
			continue;
		}

		TArray<FString> Files;
		WalkRecursive(Root, Files);

		for (const FString& File : Files)
		{
			++FilesScanned;
			ScanFile(File, ProjectRoot, AllRows);
		}
	}

	if (!WriteRows(DB, AllRows))
	{
		OutStatus = FString::Printf(
			TEXT("FConditionalGateIndexer: write failed after %d files"),
			FilesScanned);
		return false;
	}

	OutStatus = FString::Printf(
		TEXT("ConditionalGateIndexer: %d gates from %d files"),
		AllRows.Num(), FilesScanned);
	UE_LOG(LogMonolithReflectionIntel, Log, TEXT("%s"), *OutStatus);
	return true;
}

bool FConditionalGateIndexer::EnsureSchema(FSQLiteDatabase& DB)
{
	auto Exec = [&DB](const TCHAR* Sql) -> bool
	{
		FSQLitePreparedStatement Stmt;
		if (!Stmt.Create(DB, Sql))
		{
			UE_LOG(LogMonolithReflectionIntel, Error,
				TEXT("ConditionalGateIndexer DDL prepare failed: %s"), Sql);
			return false;
		}
		return Stmt.Execute();
	};
	if (!Exec(MonolithRiskSchema::GetCreateConditionalGatesTableSQL())) { return false; }
	Exec(MonolithRiskSchema::GetCreateConditionalGatesIndexMacroSQL());
	return true;
}

void FConditionalGateIndexer::ScanFile(
	const FString& AbsPath, const FString& ProjectRoot,
	TArray<FConditionalGateRow>& OutRows)
{
	FString FileText;
	if (!FFileHelper::LoadFileToString(FileText, *AbsPath)) { return; }

	TArray<FString> Lines;
	FileText.ParseIntoArrayLines(Lines, /*InCullEmpty=*/false);

	const bool bIsBuildCs = IsBuildCsFile(AbsPath);
	const FString RelPath = RIToProjectRelative(AbsPath, ProjectRoot);

	for (int32 i = 0; i < Lines.Num(); ++i)
	{
		const FString& Line = Lines[i];

		// `#if WITH_*` pattern — C++ source.
		if (!bIsBuildCs)
		{
			FRegexMatcher M(IfWithPattern, Line);
			while (M.FindNext())
			{
				const FString Macro = M.GetCaptureGroup(1).TrimStartAndEnd();
				if (Macro.IsEmpty()) { continue; }

				FConditionalGateRow Row;
				Row.SourcePath = RelPath;
				Row.SourceLine = i + 1;
				Row.MacroName = Macro;
				Row.GateKind = TEXT("cpp_if");
				Row.ContextSnippet = Line.TrimStartAndEnd().Left(256);
				OutRows.Add(MoveTemp(Row));
			}
		}

		// `bHas*` Build.cs probe pattern — Build.cs files only.
		if (bIsBuildCs)
		{
			FRegexMatcher M(BuildCsProbePattern, Line);
			while (M.FindNext())
			{
				const FString ProbeId = M.GetCaptureGroup(1).TrimStartAndEnd();
				if (ProbeId.IsEmpty()) { continue; }

				FConditionalGateRow Row;
				Row.SourcePath = RelPath;
				Row.SourceLine = i + 1;
				Row.MacroName = ProbeId;
				Row.GateKind = TEXT("build_cs_probe");
				Row.ContextSnippet = Line.TrimStartAndEnd().Left(256);
				OutRows.Add(MoveTemp(Row));
			}
		}
	}
}

bool FConditionalGateIndexer::WriteRows(
	FSQLiteDatabase& DB, const TArray<FConditionalGateRow>& Rows)
{
	FSQLitePreparedStatement Ins;
	if (!Ins.Create(DB, TEXT(
		"INSERT INTO reflect_conditional_gates "
		"(source_path, source_line, macro_name, gate_kind, context_snippet) "
		"VALUES (?, ?, ?, ?, ?);")))
	{
		UE_LOG(LogMonolithReflectionIntel, Error,
			TEXT("ConditionalGateIndexer: INSERT prepare failed"));
		return false;
	}

	DB.Execute(TEXT("BEGIN TRANSACTION;"));
	int32 OkCount = 0;
	for (const FConditionalGateRow& R : Rows)
	{
		Ins.Reset();
		Ins.ClearBindings();
		Ins.SetBindingValueByIndex(1, R.SourcePath);
		Ins.SetBindingValueByIndex(2, R.SourceLine);
		Ins.SetBindingValueByIndex(3, R.MacroName);
		Ins.SetBindingValueByIndex(4, R.GateKind);
		Ins.SetBindingValueByIndex(5, R.ContextSnippet);
		if (Ins.Execute()) { ++OkCount; }
		else
		{
			UE_LOG(LogMonolithReflectionIntel, Verbose,
				TEXT("ConditionalGateIndexer: INSERT failed for %s:%d (%s)"),
				*R.SourcePath, R.SourceLine, *R.MacroName);
		}
	}
	DB.Execute(TEXT("COMMIT;"));

	UE_LOG(LogMonolithReflectionIntel, Verbose,
		TEXT("ConditionalGateIndexer: wrote %d / %d rows"), OkCount, Rows.Num());
	return OkCount == Rows.Num();
}
