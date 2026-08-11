#pragma once

#include "MonolithAIInternal.h"

class FMonolithAIDiscoveryActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleGetAIOverview(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListAINodeTypes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSearchAIAssets(const TSharedPtr<FJsonObject>& Params);

	// Cross-reference discovery
	static FMonolithActionResult HandleValidateAIDataFlow(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindEQSReferences(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindSOReferences(const TSharedPtr<FJsonObject>& Params);

	// Lint & manifest
	static FMonolithActionResult HandleLintBehaviorTree(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleLintStateTree(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDetectAICircularReferences(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleExportAIManifest(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAIBehaviorSummary(const TSharedPtr<FJsonObject>& Params);
};
