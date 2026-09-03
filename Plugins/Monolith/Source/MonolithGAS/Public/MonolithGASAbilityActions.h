#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASAbilityActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 1: Core CRUD
	static FMonolithActionResult HandleCreateAbility(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAbilityInfo(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListAbilities(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCompileAbility(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAbilityTags(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAbilityTags(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAbilityPolicy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAbilityCost(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAbilityCooldown(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAbilityTriggers(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAbilityFlags(const TSharedPtr<FJsonObject>& Params);

	// Phase 2: Graph Building + Templates
	static FMonolithActionResult HandleAddAbilityTaskNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddCommitAndEndFlow(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddEffectApplication(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddGameplayCueNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCreateAbilityFromTemplate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBuildAbilityFromSpec(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBatchCreateAbilities(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateAbility(const TSharedPtr<FJsonObject>& Params);
	// Phase 2: Ability Tasks
	static FMonolithActionResult HandleListAbilityTasks(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAbilityTaskPins(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleWireAbilityTaskDelegate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAbilityGraphFlow(const TSharedPtr<FJsonObject>& Params);
	// Phase 3: Analysis
	static FMonolithActionResult HandleValidateAbility(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindAbilitiesByTag(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAbilityTagMatrix(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateAbilityBlueprint(const TSharedPtr<FJsonObject>& Params);
	// Phase 4: Advanced
	static FMonolithActionResult HandleScaffoldCustomAbilityTask(const TSharedPtr<FJsonObject>& Params);
};
