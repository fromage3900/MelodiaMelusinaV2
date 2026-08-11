#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Atomic T3D node injection.
 *
 * copy_nodes (MonolithBlueprintGraphExportActions) already round-trips T3D between two
 * live graphs, but there was no way to hand Monolith T3D text that does not yet exist in
 * any graph. That gap forced authoring through per-node add_node/connect_nodes calls: many
 * round trips, a partially-wired graph on every failure, and no dry run.
 *
 * inject_nodes_t3d closes it. One call: resolve placeholders, validate against the
 * reflection system, then FEdGraphUtilities::ImportNodesFromText inside a single
 * transaction. Either the whole payload lands or nothing does.
 */
class FMonolithBlueprintT3DActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleInjectNodesT3D(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateNodesT3D(const TSharedPtr<FJsonObject>& Params);
};
