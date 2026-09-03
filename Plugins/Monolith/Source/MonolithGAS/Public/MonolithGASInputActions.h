#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASInputActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 1: Input Binding
	static FMonolithActionResult HandleSetupAbilityInputBinding(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBindAbilityToInput(const TSharedPtr<FJsonObject>& Params);

	// Phase 2: Input Binding Productivity
	static FMonolithActionResult HandleBatchBindAbilities(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAbilityInputBindings(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldInputBindingComponent(const TSharedPtr<FJsonObject>& Params);
};
