#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverTextGraphActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Text graph inspection (Phase 3)
	static FMonolithActionResult HandleGetTextGraphContent(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetDialogueFlow(const TSharedPtr<FJsonObject>& Params);
};
