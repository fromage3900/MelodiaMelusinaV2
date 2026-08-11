// MonolithCommonUIActions.h
// Public aggregator for the CommonUI action pack. Compiles to empty header when CommonUI absent.
#pragma once

#if WITH_COMMONUI

#include "CoreMinimal.h"

class FMonolithToolRegistry;

class MONOLITHUI_API FMonolithCommonUIActions
{
public:
	/** Register every CommonUI action across all 9 categories with the registry. */
	static void RegisterAll(FMonolithToolRegistry& Registry);
};

#endif // WITH_COMMONUI
