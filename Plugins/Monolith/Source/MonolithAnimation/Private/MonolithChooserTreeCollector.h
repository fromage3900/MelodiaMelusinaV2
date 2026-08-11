#pragma once

#include "CoreMinimal.h"

/**
 * Read-only recursive collector for UChooserTable trees.
 *
 * Walks a chooser table's result rows, fallback result, and output-object column
 * cells, classifying each result location by row kind (asset / soft_asset /
 * evaluate_chooser / nested_chooser) and resolving its target asset path. Recurses
 * into embedded child tables (NestedObjects) and reports ParentTable / RootChooser.
 *
 * This is the READ counterpart factored out of the duplicate-tree writer's traversal
 * (HandleDuplicateChooserTree). The writer remaps in place and is NOT routed through
 * this collector (it owns its own per-duplicate cursors); this collector is purely
 * additive read-only structure, shared by inspect_chooser (recursive) and any future
 * readback path that needs to prove a root->child chooser tree.
 *
 * GATING (two gates, governing different things — do NOT collapse to one):
 *   - WITH_CHOOSER       : the chooser struct TYPES (FEvaluateChooser / FNestedChooser
 *                          / FAssetChooser / FOutputObjectColumn) and UChooserTable.
 *   - WITH_EDITORONLY_DATA: the ROW DATA itself (ResultsStructs / ColumnsStructs /
 *                          NestedObjects / ParentTable). RootChooser and FallbackResult
 *                          are NOT editor-only.
 * The collector COMPILES CLEANLY when WITH_CHOOSER=1 but editor-only data is OFF
 * (cooked / release): in that configuration the row-data walk is elided and the
 * collector returns the asset/soft-asset-resolvable structure only (empty rows tree).
 */

#if WITH_CHOOSER

#include "Dom/JsonObject.h"

class UChooserTable;

namespace MonolithChooserTree
{
	/**
	 * Collect the full read-only tree of a chooser table into a JSON object.
	 *
	 * Output shape (fields present depend on build configuration):
	 *   asset_path      : this table's path name
	 *   root_chooser    : RootChooser path (if any)
	 *   parent_table    : ParentTable path (editor-only; if any)
	 *   row_count       : number of result rows (editor-only)
	 *   rows            : [ { row, kind, struct_type, asset, is_null }, ... ] (editor-only)
	 *   fallback        : { kind, struct_type, asset, is_null } (if FallbackResult set)
	 *   output_columns  : [ { column, cells:[...] }, ... ] (editor-only)
	 *   nested_objects  : count of NestedObjects (editor-only)
	 *   child_tables    : [ <nested table sub-tree>, ... ] (recursive; editor-only)
	 *
	 * @param Table          The table to collect. Null yields an empty object.
	 * @param VisitedTables  REQUIRED cycle guard, passed by reference. Tables already
	 *                       present are skipped (the sub-tree is replaced with a
	 *                       { "cycle": <path> } marker). A pure read has no
	 *                       new-object-creation bound, so a cyclic ParentTable /
	 *                       NestedObject reference would otherwise recurse forever.
	 *                       The caller MUST supply this set; it is not optional.
	 * @return A JSON object describing the table sub-tree (never null).
	 */
	TSharedPtr<FJsonObject> CollectTree(UChooserTable* Table, TSet<UChooserTable*>& VisitedTables);
}

#endif // WITH_CHOOSER
