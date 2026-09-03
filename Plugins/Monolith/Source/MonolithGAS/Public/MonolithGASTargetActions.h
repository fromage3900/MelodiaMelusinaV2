#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASTargetActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 3: Targeting
	static FMonolithActionResult HandleCreateTargetActor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureTargetActor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddTargetingToAbility(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldFPSTargeting(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateTargeting(const TSharedPtr<FJsonObject>& Params);
};
