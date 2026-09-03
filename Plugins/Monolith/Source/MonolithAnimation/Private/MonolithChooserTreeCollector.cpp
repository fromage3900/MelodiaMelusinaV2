#include "MonolithChooserTreeCollector.h"

#if WITH_CHOOSER

#include "Dom/JsonValue.h"

// Chooser runtime headers — same set HandleDuplicateChooserTree relies on. Chooser.Build.cs
// places its Internal/ dir on PublicIncludePaths, so the Internal table/result headers are
// reachable for any module taking the "Chooser" dependency.
#include "Chooser.h"                  // UChooserTable, FEvaluateChooser, FNestedChooser
#include "ObjectChooser_Asset.h"      // FAssetChooser / FSoftAssetChooser
#include "OutputObjectColumn.h"        // FOutputObjectColumn / FChooserOutputObjectRowData

#include "StructUtils/InstancedStruct.h"
#include "UObject/SoftObjectPtr.h"
#include "UObject/SoftObjectPath.h"

namespace MonolithChooserTree
{
	namespace
	{
		/**
		 * Classify ONE result FInstancedStruct (a result row, a table's FallbackResult, or an
		 * FOutputObjectColumn cell) into a { kind, struct_type, asset, is_null } JSON object.
		 *
		 * This is the read-only superset of GetRowAssetPath in MonolithChooserActions.cpp: that
		 * helper only resolves FAssetChooser / FSoftAssetChooser; here we ALSO classify
		 * FEvaluateChooser (reads Eval->Chooser — a separate chooser asset) and FNestedChooser
		 * (reads Nested->Chooser — an embedded child table). Mirrors the dispatch in the donor
		 * RemapResultStruct lambda, read side only.
		 *
		 * `kind` is one of: asset / soft_asset / evaluate_chooser / nested_chooser / other.
		 * `is_null` is true when the struct IS a recognized result kind but its reference is unset.
		 */
		TSharedPtr<FJsonObject> DescribeResultStruct(const FInstancedStruct& S)
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();

			const UScriptStruct* SS = S.GetScriptStruct();
			Obj->SetStringField(TEXT("struct_type"), SS ? SS->GetName() : TEXT("<null>"));
			Obj->SetStringField(TEXT("asset"), FString());
			Obj->SetBoolField(TEXT("is_null"), false);

			if (const FAssetChooser* Hard = S.GetPtr<FAssetChooser>())
			{
				Obj->SetStringField(TEXT("kind"), TEXT("asset"));
				if (Hard->Asset)
				{
					Obj->SetStringField(TEXT("asset"), Hard->Asset->GetPathName());
				}
				else
				{
					Obj->SetBoolField(TEXT("is_null"), true);
				}
			}
			else if (const FSoftAssetChooser* Soft = S.GetPtr<FSoftAssetChooser>())
			{
				Obj->SetStringField(TEXT("kind"), TEXT("soft_asset"));
				const FSoftObjectPath SoftPath = Soft->Asset.ToSoftObjectPath();
				if (SoftPath.IsValid())
				{
					Obj->SetStringField(TEXT("asset"), SoftPath.ToString());
				}
				else
				{
					Obj->SetBoolField(TEXT("is_null"), true);
				}
			}
			else if (const FEvaluateChooser* Eval = S.GetPtr<FEvaluateChooser>())
			{
				// FEvaluateChooser points at a SEPARATE chooser asset.
				Obj->SetStringField(TEXT("kind"), TEXT("evaluate_chooser"));
				if (Eval->Chooser)
				{
					Obj->SetStringField(TEXT("asset"), Eval->Chooser->GetPathName());
				}
				else
				{
					Obj->SetBoolField(TEXT("is_null"), true);
				}
			}
			else if (const FNestedChooser* Nested = S.GetPtr<FNestedChooser>())
			{
				// FNestedChooser points at a chooser table EMBEDDED in this asset.
				Obj->SetStringField(TEXT("kind"), TEXT("nested_chooser"));
				if (Nested->Chooser)
				{
					Obj->SetStringField(TEXT("asset"), Nested->Chooser->GetPathName());
				}
				else
				{
					Obj->SetBoolField(TEXT("is_null"), true);
				}
			}
			else
			{
				Obj->SetStringField(TEXT("kind"), TEXT("other"));
			}

			return Obj;
		}
	}

	TSharedPtr<FJsonObject> CollectTree(UChooserTable* Table, TSet<UChooserTable*>& VisitedTables)
	{
		TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
		if (!Table)
		{
			return Root;
		}

		Root->SetStringField(TEXT("asset_path"), Table->GetPathName());

		// CYCLE GUARD. A pure read has no new-object-creation bound (unlike the duplicate path),
		// so a cyclic ParentTable / NestedObject reference would recurse forever without this.
		// The visited set is a REQUIRED entry-point parameter precisely so reuse (Phase 3) cannot
		// re-introduce unbounded recursion.
		if (VisitedTables.Contains(Table))
		{
			Root->SetStringField(TEXT("cycle"), Table->GetPathName());
			return Root;
		}
		VisitedTables.Add(Table);

		// RootChooser + FallbackResult are NOT editor-only (Chooser.h:141/145) — always available.
		if (Table->RootChooser)
		{
			Root->SetStringField(TEXT("root_chooser"), Table->RootChooser->GetPathName());
		}
		if (Table->FallbackResult.IsValid())
		{
			Root->SetObjectField(TEXT("fallback"), DescribeResultStruct(Table->FallbackResult));
		}

		// Result rows, output-object column cells, NestedObjects, and ParentTable are all
		// WITH_EDITORONLY_DATA on UChooserTable (Chooser.h:150-181). In a cooked / release build
		// (WITH_CHOOSER=1, editor-only data OFF) this entire block is elided and the collector
		// returns the asset_path / root_chooser / fallback structure only.
#if WITH_EDITORONLY_DATA
		Root->SetNumberField(TEXT("row_count"), Table->ResultsStructs.Num());

		{
			TArray<TSharedPtr<FJsonValue>> Rows;
			for (int32 RowIdx = 0; RowIdx < Table->ResultsStructs.Num(); ++RowIdx)
			{
				TSharedPtr<FJsonObject> RowObj = DescribeResultStruct(Table->ResultsStructs[RowIdx]);
				RowObj->SetNumberField(TEXT("row"), RowIdx);
				Rows.Add(MakeShared<FJsonValueObject>(RowObj));
			}
			Root->SetArrayField(TEXT("rows"), Rows);
		}

		// FOutputObjectColumn cell values (per-row RowValues[].Value, plus FallbackValue.Value
		// and DefaultRowValue.Value). Mirrors WalkTableReferences' column branch, read side.
		{
			TArray<TSharedPtr<FJsonValue>> Columns;
			for (int32 ColIdx = 0; ColIdx < Table->ColumnsStructs.Num(); ++ColIdx)
			{
				const FInstancedStruct& ColumnData = Table->ColumnsStructs[ColIdx];
				const FOutputObjectColumn* OutCol = ColumnData.GetPtr<FOutputObjectColumn>();
				if (!OutCol)
				{
					continue;
				}

				TSharedPtr<FJsonObject> ColObj = MakeShared<FJsonObject>();
				ColObj->SetNumberField(TEXT("column"), ColIdx);

				TArray<TSharedPtr<FJsonValue>> Cells;
				for (int32 CellIdx = 0; CellIdx < OutCol->RowValues.Num(); ++CellIdx)
				{
					if (OutCol->RowValues[CellIdx].Value.IsValid())
					{
						TSharedPtr<FJsonObject> CellObj = DescribeResultStruct(OutCol->RowValues[CellIdx].Value);
						CellObj->SetNumberField(TEXT("row"), CellIdx);
						CellObj->SetStringField(TEXT("site"), TEXT("row"));
						Cells.Add(MakeShared<FJsonValueObject>(CellObj));
					}
				}
				if (OutCol->FallbackValue.Value.IsValid())
				{
					TSharedPtr<FJsonObject> CellObj = DescribeResultStruct(OutCol->FallbackValue.Value);
					CellObj->SetStringField(TEXT("site"), TEXT("fallback"));
					Cells.Add(MakeShared<FJsonValueObject>(CellObj));
				}
				if (OutCol->DefaultRowValue.Value.IsValid())
				{
					TSharedPtr<FJsonObject> CellObj = DescribeResultStruct(OutCol->DefaultRowValue.Value);
					CellObj->SetStringField(TEXT("site"), TEXT("default"));
					Cells.Add(MakeShared<FJsonValueObject>(CellObj));
				}

				ColObj->SetArrayField(TEXT("cells"), Cells);
				Columns.Add(MakeShared<FJsonValueObject>(ColObj));
			}
			Root->SetArrayField(TEXT("output_columns"), Columns);
		}

		// ParentTable (deprecated in favor of RootChooser, but still read for completeness).
		if (Table->ParentTable)
		{
			Root->SetStringField(TEXT("parent_table"), Table->ParentTable->GetPathName());
		}

		// Recurse into embedded child choosers. The engine's ReplaceReferences
		// (SNestedChooserTree.cpp ~104-121) iterates RootTable->NestedObjects, casts each to
		// UChooserTable, and walks every embedded child. The same set holds the embedded child
		// tables whose FNestedChooser / FEvaluateChooser rows form the nested tree.
		Root->SetNumberField(TEXT("nested_objects"), Table->NestedObjects.Num());
		{
			TArray<TSharedPtr<FJsonValue>> ChildTables;
			for (int32 NestedIdx = 0; NestedIdx < Table->NestedObjects.Num(); ++NestedIdx)
			{
				if (UChooserTable* NestedChild = Cast<UChooserTable>(Table->NestedObjects[NestedIdx]))
				{
					// Recurse with the SAME visited set — the cycle guard spans the whole walk.
					TSharedPtr<FJsonObject> ChildTree = CollectTree(NestedChild, VisitedTables);
					ChildTree->SetNumberField(TEXT("nested_index"), NestedIdx);
					ChildTables.Add(MakeShared<FJsonValueObject>(ChildTree));
				}
			}
			Root->SetArrayField(TEXT("child_tables"), ChildTables);
		}
#endif // WITH_EDITORONLY_DATA

		return Root;
	}
}

#endif // WITH_CHOOSER
