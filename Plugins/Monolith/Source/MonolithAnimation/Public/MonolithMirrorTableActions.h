#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * MirrorDataTable domain action handlers for Monolith (Motion Matching Pack — Sprint 2).
 * - create_mirror_data_table     : create a UMirrorDataTable, populate find/replace rules, build rows.
 * - set_schema_mirror_data_table : assign a mirror table to a PoseSearchSchema roled-skeleton slot.
 */
class MONOLITHANIMATION_API FMonolithMirrorTableActions
{
public:
	/** Register all mirror-table actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleCreateMirrorDataTable(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetSchemaMirrorDataTable(const TSharedPtr<FJsonObject>& Params);
};
