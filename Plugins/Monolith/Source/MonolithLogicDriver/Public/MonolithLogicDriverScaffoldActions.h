#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverScaffoldActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Scaffold presets (Phase 2-4)
	static FMonolithActionResult HandleScaffoldHelloWorldSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldDialogueSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldQuestSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldInteractableSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldWeaponSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldHorrorEncounterSM(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldGameFlowSM(const TSharedPtr<FJsonObject>& Params);
};
