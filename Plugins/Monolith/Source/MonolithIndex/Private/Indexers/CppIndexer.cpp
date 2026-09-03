#include "Indexers/CppIndexer.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Internationalization/Regex.h"

bool FCppIndexer::IndexAsset(const FAssetData& AssetData, UObject* LoadedAsset, FMonolithIndexDatabase& DB, int64 AssetId)
{
	// Collect .h and .cpp files from both Source/ and Plugins/ directories
	TArray<FString> SourceFiles;
	FString ProjectSourceDir = FPaths::ProjectDir() / TEXT("Source");
	FString ProjectPluginsDir = FPaths::ProjectDir() / TEXT("Plugins");

	// bClearFileNames must be false on subsequent calls to append rather than overwrite
	IFileManager::Get().FindFilesRecursive(SourceFiles, *ProjectSourceDir, TEXT("*.h"), true, false, true);
	IFileManager::Get().FindFilesRecursive(SourceFiles, *ProjectSourceDir, TEXT("*.cpp"), true, false, false);
	IFileManager::Get().FindFilesRecursive(SourceFiles, *ProjectPluginsDir, TEXT("*.h"), true, false, false);
	IFileManager::Get().FindFilesRecursive(SourceFiles, *ProjectPluginsDir, TEXT("*.cpp"), true, false, false);

	UE_LOG(LogMonolithIndex, Log, TEXT("CppIndexer: found %d source files (Source/ + Plugins/)"), SourceFiles.Num());

	int32 TotalSymbols = 0;

	for (const FString& SourceFile : SourceFiles)
	{
		FString RelativePath = SourceFile;
		FPaths::MakePathRelativeTo(RelativePath, *FPaths::ProjectDir());
		TotalSymbols += ParseSourceFile(SourceFile, RelativePath, DB);
	}

	UE_LOG(LogMonolithIndex, Log, TEXT("CppIndexer: indexed %d symbols from %d source files"), TotalSymbols, SourceFiles.Num());
	return true;
}

int32 FCppIndexer::ParseSourceFile(const FString& FilePath, const FString& RelativePath, FMonolithIndexDatabase& DB)
{
	TArray<FString> Lines;
	if (!FFileHelper::LoadFileToStringArray(Lines, *FilePath))
	{
		return 0;
	}

	int32 Inserted = 0;
	FString CurrentClass;

	// Patterns for UE macro-decorated declarations
	// UCLASS/USTRUCT/UENUM: look for the macro, then the type declaration on the next line(s)
	// UFUNCTION/UPROPERTY: look for the macro, then the declaration on the next line(s)

	for (int32 i = 0; i < Lines.Num(); ++i)
	{
		const FString& Line = Lines[i].TrimStartAndEnd();

		// --- UCLASS ---
		if (Line.Contains(TEXT("UCLASS(")))
		{
			// The class declaration is typically on the next non-empty line
			for (int32 j = i + 1; j < FMath::Min(i + 5, Lines.Num()); ++j)
			{
				FString NextLine = Lines[j].TrimStartAndEnd();
				FRegexPattern ClassPattern(TEXT("class\\s+(?:[A-Z_]+\\s+)?([A-Za-z_][A-Za-z0-9_]*)"));
				FRegexMatcher ClassMatcher(ClassPattern, NextLine);
				if (ClassMatcher.FindNext())
				{
					FIndexedCppSymbol Symbol;
					Symbol.FilePath = RelativePath;
					Symbol.SymbolName = ClassMatcher.GetCaptureGroup(1);
					Symbol.SymbolType = TEXT("Class");
					Symbol.Signature = NextLine;
					Symbol.LineNumber = j + 1;
					DB.InsertCppSymbol(Symbol);
					CurrentClass = Symbol.SymbolName;
					Inserted++;
					break;
				}
			}
		}
		// --- USTRUCT ---
		else if (Line.Contains(TEXT("USTRUCT(")))
		{
			for (int32 j = i + 1; j < FMath::Min(i + 5, Lines.Num()); ++j)
			{
				FString NextLine = Lines[j].TrimStartAndEnd();
				FRegexPattern StructPattern(TEXT("struct\\s+(?:[A-Z_]+\\s+)?([A-Za-z_][A-Za-z0-9_]*)"));
				FRegexMatcher StructMatcher(StructPattern, NextLine);
				if (StructMatcher.FindNext())
				{
					FIndexedCppSymbol Symbol;
					Symbol.FilePath = RelativePath;
					Symbol.SymbolName = StructMatcher.GetCaptureGroup(1);
					Symbol.SymbolType = TEXT("Struct");
					Symbol.Signature = NextLine;
					Symbol.LineNumber = j + 1;
					DB.InsertCppSymbol(Symbol);
					CurrentClass = Symbol.SymbolName;
					Inserted++;
					break;
				}
			}
		}
		// --- UENUM ---
		else if (Line.Contains(TEXT("UENUM(")))
		{
			for (int32 j = i + 1; j < FMath::Min(i + 5, Lines.Num()); ++j)
			{
				FString NextLine = Lines[j].TrimStartAndEnd();
				FRegexPattern EnumPattern(TEXT("enum\\s+(?:class\\s+)?([A-Za-z_][A-Za-z0-9_]*)"));
				FRegexMatcher EnumMatcher(EnumPattern, NextLine);
				if (EnumMatcher.FindNext())
				{
					FIndexedCppSymbol Symbol;
					Symbol.FilePath = RelativePath;
					Symbol.SymbolName = EnumMatcher.GetCaptureGroup(1);
					Symbol.SymbolType = TEXT("Enum");
					Symbol.Signature = NextLine;
					Symbol.LineNumber = j + 1;
					DB.InsertCppSymbol(Symbol);
					CurrentClass = Symbol.SymbolName;
					Inserted++;
					break;
				}
			}
		}
		// --- UFUNCTION ---
		else if (Line.Contains(TEXT("UFUNCTION(")))
		{
			// Function signature follows the UFUNCTION macro (may span multiple lines for the macro)
			for (int32 j = i + 1; j < FMath::Min(i + 5, Lines.Num()); ++j)
			{
				FString NextLine = Lines[j].TrimStartAndEnd();
				// Skip empty lines and continued macro lines
				if (NextLine.IsEmpty() || NextLine.StartsWith(TEXT("UFUNCTION")))
				{
					continue;
				}
				// Match return_type FunctionName(
				FRegexPattern FuncPattern(TEXT("(?:virtual\\s+|static\\s+|FORCEINLINE\\s+)*(?:[A-Za-z_][A-Za-z0-9_<>:*&\\s]*?)\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*\\("));
				FRegexMatcher FuncMatcher(FuncPattern, NextLine);
				if (FuncMatcher.FindNext())
				{
					FIndexedCppSymbol Symbol;
					Symbol.FilePath = RelativePath;
					Symbol.SymbolName = FuncMatcher.GetCaptureGroup(1);
					Symbol.SymbolType = TEXT("Function");
					Symbol.Signature = NextLine;
					Symbol.LineNumber = j + 1;
					Symbol.ParentSymbol = CurrentClass;
					DB.InsertCppSymbol(Symbol);
					Inserted++;
					break;
				}
				break; // Don't search too far
			}
		}
		// --- UPROPERTY ---
		else if (Line.Contains(TEXT("UPROPERTY(")))
		{
			// Property declaration follows the macro
			for (int32 j = i + 1; j < FMath::Min(i + 5, Lines.Num()); ++j)
			{
				FString NextLine = Lines[j].TrimStartAndEnd();
				if (NextLine.IsEmpty() || NextLine.StartsWith(TEXT("UPROPERTY")))
				{
					continue;
				}
				// Match type PropertyName; (last identifier before semicolon)
				FRegexPattern PropPattern(TEXT("([A-Za-z_][A-Za-z0-9_]*)\\s*(?:=.*)?;"));
				FRegexMatcher PropMatcher(PropPattern, NextLine);
				if (PropMatcher.FindNext())
				{
					FIndexedCppSymbol Symbol;
					Symbol.FilePath = RelativePath;
					Symbol.SymbolName = PropMatcher.GetCaptureGroup(1);
					Symbol.SymbolType = TEXT("Property");
					Symbol.Signature = NextLine;
					Symbol.LineNumber = j + 1;
					Symbol.ParentSymbol = CurrentClass;
					DB.InsertCppSymbol(Symbol);
					Inserted++;
					break;
				}
				break;
			}
		}
		// --- UDELEGATE / DECLARE_DYNAMIC_MULTICAST_DELEGATE ---
		else if (Line.Contains(TEXT("DECLARE_DYNAMIC_MULTICAST_DELEGATE")) ||
				 Line.Contains(TEXT("DECLARE_DYNAMIC_DELEGATE")) ||
				 Line.Contains(TEXT("DECLARE_MULTICAST_DELEGATE")) ||
				 Line.Contains(TEXT("DECLARE_DELEGATE")))
		{
			// Extract delegate name from macro arguments: DECLARE_..._DELEGATE...(DelegateName, ...)
			FRegexPattern DelegatePattern(TEXT("DECLARE_\\w+DELEGATE\\w*\\(\\s*([A-Za-z_][A-Za-z0-9_]*)"));
			FRegexMatcher DelegateMatcher(DelegatePattern, Line);
			if (DelegateMatcher.FindNext())
			{
				FIndexedCppSymbol Symbol;
				Symbol.FilePath = RelativePath;
				Symbol.SymbolName = DelegateMatcher.GetCaptureGroup(1);
				Symbol.SymbolType = TEXT("Delegate");
				Symbol.Signature = Line;
				Symbol.LineNumber = i + 1;
				Symbol.ParentSymbol = CurrentClass;
				DB.InsertCppSymbol(Symbol);
				Inserted++;
			}
		}
	}

	return Inserted;
}
