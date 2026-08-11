// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// FNetworkQueryAdapter — registers the `network` namespace (4 actions) against
// the central FMonolithToolRegistry. Pure read-only handlers; no indexing
// happens here (that's FNetworkRepIndexer + the Phase 3a reflect_ufunctions
// table).
//
// Phase 4a action surface:
//   network_query("list_replicated_classes", {limit?, cursor?})
//   network_query("list_rpc_functions",     {class_name?, rpc_kind?, limit?, cursor?})
//   network_query("list_onrep_handlers",    {class_name?, limit?, cursor?})
//   network_query("audit_unbalanced_onreps", {limit?, cursor?})
//
// Phase 4b (deferred) will replace `list_rpc_functions`'s name-pattern detection
// with specifier-driven matching once Phase 3a's `reflect_ufunctions.specifiers`
// is populated by tree-sitter or a UHT MetaData re-sweep.
//
// v0.17.0 ergonomics adoption (mirrors Phase 1+2+3a pattern):
//   - `class_name` is a bare C++ symbol (NOT path-typed).
//   - Dispatcher annotated readOnlyHint=true + idempotentHint=true.
//   - All list-style actions adopt cursor pagination.

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class MONOLITHREFLECTIONINTEL_API FNetworkQueryAdapter
{
public:
	/** Register all 4 network actions + dispatcher annotations. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Action handlers ---
	static FMonolithActionResult HandleListReplicatedClasses(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListRPCFunctions(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListOnRepHandlers(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAuditUnbalancedOnReps(const TSharedPtr<FJsonObject>& Params);

	/** Shared DB accessor — routes through the module's cached query DB. Triggers
	 *  the network-indexer lazy bootstrap on first call if reflect_replicated_properties
	 *  is missing. */
	static class FSQLiteDatabase* GetRawDB();
};
