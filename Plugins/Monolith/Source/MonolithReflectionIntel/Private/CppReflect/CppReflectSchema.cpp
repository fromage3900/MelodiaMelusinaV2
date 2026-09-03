// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 3a — v0.17.0).
//
// CppReflectSchema.cpp — CREATE TABLE statements for the six Phase 3a tables.
// Same `IF NOT EXISTS` idempotency pattern as DecisionSchema.cpp / RiskSchema.cpp.
// Statements consumed exclusively from FUHTArtefactReader / FAssetGraphJoiner
// EnsureSchema() entry points. See SPEC_MonolithReflectionIntel.md (Phase 3a
// Schema section) for per-column documentation.

#include "CppReflect/CppReflectSchema.h"

namespace MonolithCppReflectSchema
{
	const TCHAR* GetCreateUClassesTableSQL()
	{
		// One row per UCLASS observed in UHT artefacts. `class_name` is the
		// C++ symbol (e.g. "ALeviathanCharacterBase" — with leading A/U/F/I
		// prefix as it appears in source). `module_name` is the UE module that
		// owns the class (e.g. "Leviathan", "InventorySystemX"). `parent_class`
		// is the immediate Super observed in the UHT `DependentSingletons[]`
		// list — bare C++ name without prefix-stripping (`ACharacter`,
		// `UObject`, ...). `source_path` is the UHT ModuleRelativePath when UHT
		// supplies one (e.g. "Public/Characters/LeviathanCharacterBase.h"), but is
		// frequently empty at write time. `source_line` is 0 at write time — UHT
		// artefacts do not carry the declaration line. The cppreflect query
		// adapter (FCppReflectQueryAdapter) now best-effort joins BOTH the line
		// AND the file path from the source-symbol index (the same EngineSource.db
		// `symbols`/`files` tables that power source_query) when the stored value
		// is missing, so `get_uclass` / `list_ufunctions` responses surface real
		// lines and an absolute file path without forcing a separate
		// `source_query` call. The joined path is ABSOLUTE (e.g.
		// "D:/Unreal Projects/.../Foo.h") because the symbol index stores full
		// paths; engine files outside the project dir don't relativise cleanly.
		// The join is name-only, so for two classes sharing a name it may surface
		// the wrong file/line. Empty path / 0 line still means "unknown". The
		// tree-sitter Phase 3b pass will fill the columns itself.
		// `flags` is a colon-joined metadata-key list (UHT Class_MetaDataParams
		// keys, e.g. "IsBlueprintBase:BlueprintType") — NOT C++ specifiers. UHT
		// rewrites some specifiers into metadata keys (UCLASS(Blueprintable) is
		// stored as "IsBlueprintBase"), passes a few through 1:1 ("BlueprintType",
		// "Abstract"), and drops others entirely ("MinimalAPI", "NotBlueprintable").
		// Query via cppreflect_query("list_class_specifiers") to discover the
		// real stored token universe.
		// PK pair (class_name, module_name) tolerates same-named classes in
		// different modules without uniqueness conflicts.
		return TEXT(
			"CREATE TABLE IF NOT EXISTS reflect_uclasses ("
			"    class_name    TEXT NOT NULL,"
			"    module_name   TEXT NOT NULL,"
			"    parent_class  TEXT,"
			"    source_path   TEXT NOT NULL,"
			"    source_line   INTEGER NOT NULL DEFAULT 0,"
			"    flags         TEXT,"
			"    PRIMARY KEY (class_name, module_name)"
			");"
		);
	}

	const TCHAR* GetCreateUPropertiesTableSQL()
	{
		// One row per UPROPERTY observed in UHT artefacts. `owning_class` is the
		// containing C++ class name (matches reflect_uclasses.class_name).
		// `property_name` is the field name as the UPROPERTY appears (e.g.
		// "WalkSpeeds", "bWantsToSprint"). `property_type` is the UHT-emitted
		// type tag (e.g. "Struct", "Bool", "Enum", "Object", "SoftObject",
		// "Float", "Double") — Phase 3a does NOT reconstruct the full template
		// signature; that is a Phase 3b refinement.
		// `cpp_module` partitions properties by their owning UE module so we
		// can distinguish two classes with the same name shipped from different
		// modules. `blueprint_visibility` is one of "BlueprintReadOnly",
		// "BlueprintReadWrite", "EditAnywhere", "VisibleAnywhere", "" (none).
		// `specifiers` is a colon-delimited specifier list. `source_line` is 0
		// in Phase 3a (UHT artefact carries ModuleRelativePath, not the line).
		return TEXT(
			"CREATE TABLE IF NOT EXISTS reflect_uproperties ("
			"    owning_class          TEXT NOT NULL,"
			"    property_name         TEXT NOT NULL,"
			"    property_type         TEXT NOT NULL,"
			"    cpp_module            TEXT NOT NULL,"
			"    blueprint_visibility  TEXT,"
			"    specifiers            TEXT,"
			"    source_line           INTEGER NOT NULL DEFAULT 0,"
			"    PRIMARY KEY (owning_class, property_name, cpp_module)"
			");"
		);
	}

	const TCHAR* GetCreateUFunctionsTableSQL()
	{
		// One row per UFUNCTION observed in UHT artefacts. `owning_class` is the
		// declaring C++ class (matches reflect_uclasses.class_name).
		// `function_name` is the C++ symbol without `exec` prefix.
		// `return_type` is best-effort from the FuncParams struct (Phase 3a's
		// regex grabs the C++ return-type token off the parm-struct declaration
		// when present — empty when only `P_NATIVE_BEGIN` is visible without a
		// return).
		// `blueprint_callable` is 1 iff the function appears in the static
		// `Funcs[]` (`UE::CodeGen::FClassNativeFunction`) registration array —
		// i.e. UHT wired BP-callable plumbing for it. UFUNCTIONs that are
		// pure-native (Server/Client without BlueprintCallable) still get a
		// Funcs[] entry — the flag is "exposed-to-BP-VM", not BlueprintCallable
		// strictly.
		// `cpp_module` partitions by module. `specifiers` colon-delimited.
		return TEXT(
			"CREATE TABLE IF NOT EXISTS reflect_ufunctions ("
			"    owning_class         TEXT NOT NULL,"
			"    function_name        TEXT NOT NULL,"
			"    return_type          TEXT,"
			"    blueprint_callable   INTEGER NOT NULL DEFAULT 0,"
			"    cpp_module           TEXT NOT NULL,"
			"    specifiers           TEXT,"
			"    source_line          INTEGER NOT NULL DEFAULT 0,"
			"    PRIMARY KEY (owning_class, function_name, cpp_module)"
			");"
		);
	}

	const TCHAR* GetCreateUInterfacesTableSQL()
	{
		// One row per UINTERFACE. `interface_name` is the U-prefixed C++ symbol
		// as it appears in UHT (e.g. "UISXWeaponFireBridgeInterface"). UE's
		// UINTERFACE pattern generates BOTH a U-prefixed UClass (the
		// reflection-visible side) AND an I-prefixed pure-C++ interface (the
		// implementer-side ABI). reflect_uinterfaces stores ONLY the U-prefixed
		// name; reflect_uinterface_impls references the same.
		// PK is `interface_name` — interfaces are globally unique by C++ name
		// in UE (the linker would not tolerate duplicates).
		return TEXT(
			"CREATE TABLE IF NOT EXISTS reflect_uinterfaces ("
			"    interface_name  TEXT PRIMARY KEY,"
			"    module_name     TEXT NOT NULL,"
			"    source_path     TEXT NOT NULL,"
			"    source_line     INTEGER NOT NULL DEFAULT 0"
			");"
		);
	}

	const TCHAR* GetCreateUInterfaceImplsTableSQL()
	{
		// Edge table: `implementing_class` (a UCLASS) declares it implements
		// `interface_name`. Detected by scanning the implementor's UHT
		// `FImplementedInterfaceParams InterfaceParams[]` array. PK pair allows
		// the same class to declare multiple interfaces without ambiguity but
		// blocks duplicate edges from a re-run.
		return TEXT(
			"CREATE TABLE IF NOT EXISTS reflect_uinterface_impls ("
			"    implementing_class  TEXT NOT NULL,"
			"    interface_name      TEXT NOT NULL,"
			"    cpp_module          TEXT NOT NULL,"
			"    PRIMARY KEY (implementing_class, interface_name)"
			");"
		);
	}

	const TCHAR* GetCreateCppAssetEdgesTableSQL()
	{
		// Edge between a UCLASS (C++ side) and an asset path on disk (UE side).
		// `cpp_class` is the C++ symbol (matches reflect_uclasses.class_name).
		// `asset_path` is /Game/... or /<Plugin>/... form.
		// `edge_kind` is one of:
		//   "instance_of"      — the asset's class chain INCLUDES this UCLASS
		//                        (i.e. the asset is an instance / derived BP
		//                        of this UCLASS).
		//   "references_class" — (Phase 3b — not currently emitted by Phase 3a
		//                        indexer.) Reserved for a future pass that
		//                        cross-references the asset's hard-dependency
		//                        graph against the per-package class set, so
		//                        the cpp_class column carries the REFERENCED
		//                        class rather than the asset's own class.
		// The column + index are created so the Phase 3b rewrite is purely
		// additive (no schema migration). PK triple tolerates the same
		// class+asset participating in BOTH edge kinds.
		return TEXT(
			"CREATE TABLE IF NOT EXISTS cpp_asset_edges ("
			"    cpp_class    TEXT NOT NULL,"
			"    asset_path   TEXT NOT NULL,"
			"    edge_kind    TEXT NOT NULL,"
			"    PRIMARY KEY (cpp_class, asset_path, edge_kind)"
			");"
		);
	}

	const TCHAR* GetCreateUPropertiesIndexOwningClassSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_reflect_uproperties_owning_class "
			"ON reflect_uproperties(owning_class);"
		);
	}

	const TCHAR* GetCreateUFunctionsIndexOwningClassSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_reflect_ufunctions_owning_class "
			"ON reflect_ufunctions(owning_class);"
		);
	}

	const TCHAR* GetCreateUFunctionsIndexBlueprintCallableSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_reflect_ufunctions_blueprint_callable "
			"ON reflect_ufunctions(blueprint_callable);"
		);
	}

	const TCHAR* GetCreateCppAssetEdgesIndexClassSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_cpp_asset_edges_class "
			"ON cpp_asset_edges(cpp_class);"
		);
	}

	const TCHAR* GetCreateCppAssetEdgesIndexKindSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_cpp_asset_edges_kind "
			"ON cpp_asset_edges(edge_kind);"
		);
	}
}
