#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverNodeActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Node configuration (Phase 2-3)
	static FMonolithActionResult HandleConfigureState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureTransition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureConduit(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetTransitionCondition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetExposedProperties(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetExposedProperty(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureStateMachineNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetStateTags(const TSharedPtr<FJsonObject>& Params);
};
