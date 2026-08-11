#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * PIE-runtime animation telemetry actions for Monolith.
 *
 * Modeled on FMonolithLogicDriverRuntimeActions — resolves a live PIE actor's
 * USkeletalMeshComponent + UAnimInstance and reports live state (active state
 * machine state, montage, requested anim-instance variables, bone/socket
 * transforms). Read-only sampling; no graph mutation.
 */
class FMonolithAnimationRuntimeActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleSamplePIEAnimInstance(const TSharedPtr<FJsonObject>& Params);
};
