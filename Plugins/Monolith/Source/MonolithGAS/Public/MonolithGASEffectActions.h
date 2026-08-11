#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASEffectActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 1: Core CRUD
	static FMonolithActionResult HandleCreateGameplayEffect(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetGameplayEffect(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListGameplayEffects(const TSharedPtr<FJsonObject>& Params);
	// Modifiers
	static FMonolithActionResult HandleAddModifier(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetModifier(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveModifier(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListModifiers(const TSharedPtr<FJsonObject>& Params);
	// Components & Configuration
	static FMonolithActionResult HandleAddGEComponent(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetGEComponent(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetEffectStacking(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetDuration(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetPeriod(const TSharedPtr<FJsonObject>& Params);

	// Phase 2: Productivity
	static FMonolithActionResult HandleCreateEffectFromTemplate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBuildEffectFromSpec(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBatchCreateEffects(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddExecution(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateGameplayEffect(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDeleteGameplayEffect(const TSharedPtr<FJsonObject>& Params);
	// Phase 3: Analysis
	static FMonolithActionResult HandleValidateEffect(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetEffectInteractionMatrix(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveGEComponent(const TSharedPtr<FJsonObject>& Params);
	// Phase 4: Runtime
	static FMonolithActionResult HandleGetActiveEffects(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetEffectModifiersBreakdown(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleApplyEffect(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveEffect(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSimulateEffectStack(const TSharedPtr<FJsonObject>& Params);
};
