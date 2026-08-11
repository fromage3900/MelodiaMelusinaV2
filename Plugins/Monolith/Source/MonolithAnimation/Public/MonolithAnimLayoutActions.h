#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Animation Blueprint auto-layout action for Monolith.
 * Uses IMonolithGraphFormatter (Blueprint Assist bridge) to format ABP graphs.
 */
class MONOLITHANIMATION_API FMonolithAnimLayoutActions
{
public:
	/** Register all layout actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleAutoLayout(const TSharedPtr<FJsonObject>& Params);
};
