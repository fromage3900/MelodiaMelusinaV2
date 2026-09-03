// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Maintenance — v0.17.0).
//
// FReflectMaintenanceAdapter — registers the `reflect` namespace, a maintenance
// surface for the Reflection Intelligence reflect_* tables. Unlike the
// cppreflect / network query dispatchers (pure read-only), this dispatcher hosts
// a WRITE/maintenance action that mutates the index.
//
// WHY a dedicated namespace (not an action under cppreflect / network):
//   MCP annotation hints are set per-DISPATCHER, not per-action (see
//   FMonolithActionInfo / FMonolithDispatcherAnnotations in MonolithToolRegistry.h).
//   The `cppreflect` and `network` dispatchers are annotated readOnlyHint=true.
//   Adding a write action to either would force the WHOLE dispatcher to drop its
//   read-only/idempotent annotation, mis-advertising 6 (cppreflect) / 4 (network)
//   sibling read actions. A separate `reflect` dispatcher carries the correct
//   write-maintenance annotation in isolation, matching the established pattern
//   where this module fully owns (and wholesale-unregisters) its namespaces.
//
// Action surface:
//   reflect_query("rebuild_reflection_index", {})
//
// The handler delegates to FMonolithReflectionIntelModule::ForceRebuildReflectionTables,
// which force-repopulates the reflect_* tables PROJECT-SCOPED ONLY (engine
// excluded; see that method's contract). It is reusable for any future change to
// the FUHTArtefactReader / FNetworkRepIndexer parsing code that leaves the tables
// stale with no other clean rebuild trigger.

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class MONOLITHREFLECTIONINTEL_API FReflectMaintenanceAdapter
{
public:
	/** Register the single `reflect` maintenance action + dispatcher annotations. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	/** Force-rebuild the RI reflection tables (cppreflect set + network set),
	 *  project-scoped. Write/maintenance handler — mutates the index. */
	static FMonolithActionResult HandleRebuildReflectionIndex(const TSharedPtr<FJsonObject>& Params);
};
