// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// Internal-only schema accessors for the Phase 4a network tables. Mirrors the
// Phase 1 DecisionSchema.h / Phase 2 RiskSchema.h / Phase 3a CppReflectSchema.h
// pattern — private header, no other module needs the raw SQL strings; they
// exist so the network indexer and any future migration script share one
// source of truth.
//
// One table shipped in Phase 4a:
//   reflect_replicated_properties — one row per UPROPERTY observed to be
//     replicated (i.e. Class_MetaDataParams / Prop_<X>_MetaData contained a
//     replication metadata signal: ReplicatedUsing=<RepNotify>, or the
//     property was emitted into the class's `NewProp_<X>_Replication` block).
//     Composed on top of the same UHT-artefact corpus Phase 3a touches.
//
// Phase 4b (deferred) may extend with `reflect_rpc_specifiers` once tree-sitter
// support lands and lets us read `UFUNCTION(Server, Reliable, ...)` specifier
// payloads with full fidelity instead of name-pattern matching on
// reflect_ufunctions.function_name.

#pragma once

#include "CoreMinimal.h"

namespace MonolithNetworkSchema
{
	// One row per UPROPERTY discovered to carry replication metadata.
	const TCHAR* GetCreateReplicatedPropertiesTableSQL();

	// Helper indices (nice-to-have, non-fatal if they fail).
	const TCHAR* GetCreateReplicatedPropertiesIndexOwningClassSQL();
	const TCHAR* GetCreateReplicatedPropertiesIndexRepNotifySQL();
}
