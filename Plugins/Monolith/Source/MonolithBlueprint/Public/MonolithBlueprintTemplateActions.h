#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithBlueprintTemplateActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleApplyTemplate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListTemplates(const TSharedPtr<FJsonObject>& Params);
};
