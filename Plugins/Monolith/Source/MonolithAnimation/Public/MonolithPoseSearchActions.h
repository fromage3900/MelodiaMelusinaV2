#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * PoseSearch domain action handlers for Monolith.
 * 5 actions: schema inspection, database CRUD, stats.
 */
class MONOLITHANIMATION_API FMonolithPoseSearchActions
{
public:
	/** Register all PoseSearch actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleGetPoseSearchSchema(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetPoseSearchDatabase(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddDatabaseSequence(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveDatabaseSequence(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetDatabaseStats(const TSharedPtr<FJsonObject>& Params);

	// --- Wave 11: PoseSearch Creation (2) ---
	static FMonolithActionResult HandleCreatePoseSearchSchema(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCreatePoseSearchDatabase(const TSharedPtr<FJsonObject>& Params);

	// --- Wave 14: PoseSearch Writes (6) ---
	static FMonolithActionResult HandleSetDatabaseSequenceProperties(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddSchemaChannel(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveSchemaChannel(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetChannelWeight(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRebuildPoseSearchIndex(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetDatabaseSearchMode(const TSharedPtr<FJsonObject>& Params);

	// --- Motion Matching Pack Sprint 1: NormalizationSet + DB entry tags (3 class-member) ---
	static FMonolithActionResult HandleCreateNormalizationSet(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddDatabaseToNormalizationSet(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetDatabaseEntryTags(const TSharedPtr<FJsonObject>& Params);
};
