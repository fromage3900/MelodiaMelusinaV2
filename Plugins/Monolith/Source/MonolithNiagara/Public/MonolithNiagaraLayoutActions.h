#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithNiagaraLayoutActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleAutoLayout(const TSharedPtr<FJsonObject>& Params);
};
