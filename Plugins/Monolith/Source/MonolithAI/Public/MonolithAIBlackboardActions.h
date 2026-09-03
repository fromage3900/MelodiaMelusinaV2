#pragma once

#include "MonolithAIInternal.h"

class FMonolithAIBlackboardActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Blackboard CRUD
	static FMonolithActionResult HandleCreateBlackboard(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetBlackboard(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListBlackboards(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDeleteBlackboard(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateBlackboard(const TSharedPtr<FJsonObject>& Params);

	// Key management
	static FMonolithActionResult HandleAddBBKey(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveBBKey(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRenameBBKey(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetBBKeyDetails(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBatchAddBBKeys(const TSharedPtr<FJsonObject>& Params);

	// Parent / comparison
	static FMonolithActionResult HandleSetBBParent(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCompareBlackboards(const TSharedPtr<FJsonObject>& Params);
};
