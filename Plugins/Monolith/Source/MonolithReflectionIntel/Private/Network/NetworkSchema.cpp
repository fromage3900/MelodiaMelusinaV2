// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// NetworkSchema.cpp — CREATE TABLE statements for the Phase 4a network table.
// Same `IF NOT EXISTS` idempotency pattern as DecisionSchema.cpp /
// RiskSchema.cpp / CppReflectSchema.cpp. Statements consumed exclusively from
// FNetworkRepIndexer::EnsureSchema().

#include "Network/NetworkSchema.h"

namespace MonolithNetworkSchema
{
	const TCHAR* GetCreateReplicatedPropertiesTableSQL()
	{
		// One row per UPROPERTY observed in UHT artefacts to carry replication
		// metadata.
		//   owning_class      — C++ class symbol (matches reflect_uclasses.class_name).
		//   property_name     — UPROPERTY field name as it appears in source.
		//   cpp_module        — UE module that owns the class. Partitions same-named
		//                       classes shipped from multiple modules.
		//   rep_kind          — one of:
		//                         "Replicated"        : UPROPERTY(Replicated)
		//                         "ReplicatedUsing"   : UPROPERTY(ReplicatedUsing=OnRep_Foo)
		//                       Stored as a stable string so downstream callers can
		//                       LIKE / equality match without re-decoding integer
		//                       enums. Phase 4b may add push-model variants
		//                       ("PushModel") behind the same column.
		//   rep_notify_func   — when rep_kind = "ReplicatedUsing", the OnRep_ function
		//                       name. Empty when rep_kind = "Replicated".
		//   source_path       — same path semantics as reflect_uproperties.source_path
		//                       (ModuleRelativePath in Phase 4a). 0-line.
		//   source_line       — 0 in Phase 4a (UHT artefacts do not record source line).
		// PK triple (owning_class, property_name, cpp_module) tolerates re-runs and
		// matches the reflect_uproperties shape so audit JOINs are cheap.
		return TEXT(
			"CREATE TABLE IF NOT EXISTS reflect_replicated_properties ("
			"    owning_class     TEXT NOT NULL,"
			"    property_name    TEXT NOT NULL,"
			"    cpp_module       TEXT NOT NULL,"
			"    rep_kind         TEXT NOT NULL,"
			"    rep_notify_func  TEXT,"
			"    source_path      TEXT,"
			"    source_line      INTEGER NOT NULL DEFAULT 0,"
			"    PRIMARY KEY (owning_class, property_name, cpp_module)"
			");"
		);
	}

	const TCHAR* GetCreateReplicatedPropertiesIndexOwningClassSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_reflect_replicated_properties_owning_class "
			"ON reflect_replicated_properties(owning_class);"
		);
	}

	const TCHAR* GetCreateReplicatedPropertiesIndexRepNotifySQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_reflect_replicated_properties_rep_notify "
			"ON reflect_replicated_properties(rep_notify_func);"
		);
	}
}
