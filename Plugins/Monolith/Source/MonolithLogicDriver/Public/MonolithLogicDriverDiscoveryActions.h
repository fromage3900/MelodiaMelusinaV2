#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverDiscoveryActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Discovery/Inspection (Phase 1 partial, rest Phase 2-4)
	static FMonolithActionResult HandleGetSMOverview(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateStateMachine(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindSMReferences(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindNodeClassUsages(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleVisualizeSMAsText(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleExplainStateMachine(const TSharedPtr<FJsonObject>& Params);
};
