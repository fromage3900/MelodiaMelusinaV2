#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASASCActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 1: ASC Setup
	static FMonolithActionResult HandleAddASCToActor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureASC(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetupASCInit(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetupAbilitySystemInterface(const TSharedPtr<FJsonObject>& Params);

	// Phase 2: Configuration
	static FMonolithActionResult HandleApplyASCTemplate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetDefaultAbilities(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetDefaultEffects(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetDefaultAttributeSets(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetASCReplicationMode(const TSharedPtr<FJsonObject>& Params);
	// Phase 3: Validation
	static FMonolithActionResult HandleValidateASCSetup(const TSharedPtr<FJsonObject>& Params);
	// Phase 4: Runtime
	static FMonolithActionResult HandleGrantAbility(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRevokeAbility(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetASCSnapshot(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAllASCs(const TSharedPtr<FJsonObject>& Params);
};
