#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Control Rig graph read/write action handlers for Monolith.
 * 3 actions: graph reading, node spawning, pin wiring.
 */
class MONOLITHANIMATION_API FMonolithControlRigWriteActions
{
public:
	/** Register all Control Rig graph actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleGetControlRigGraph(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddControlRigNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConnectControlRigPins(const TSharedPtr<FJsonObject>& Params);
};
