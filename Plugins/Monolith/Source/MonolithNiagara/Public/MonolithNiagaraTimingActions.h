#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithNiagaraTimingActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	// System-level (4)
	static FMonolithActionResult HandleGetSystemTiming(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetWarmupProfile(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetFixedTickDelta(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetRequireCurrentFrameData(const TSharedPtr<FJsonObject>& Params);

	// Emitter composite + read aggregator (2)
	static FMonolithActionResult HandleSetEmitterLoopProfile(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetEmitterTimingSummary(const TSharedPtr<FJsonObject>& Params);

	// Sim-stage aliases (2)
	static FMonolithActionResult HandleSetSimStageIterationCount(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetSimStageExecuteBehavior(const TSharedPtr<FJsonObject>& Params);

	// Particle lifetime (1)
	static FMonolithActionResult HandleSetParticleLifetime(const TSharedPtr<FJsonObject>& Params);
};
