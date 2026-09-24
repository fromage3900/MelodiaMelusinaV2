// Copyright UNAmedia. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

//class FUNAAuthManager;



DECLARE_LOG_CATEGORY_EXTERN(LogMultiWorld, Warning, All)

/**
 * Defines the MultiWorld module
 */
class FMultiWorldModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;

    /** IModuleInterface implementation */
	virtual void ShutdownModule() override;

//#if WITH_EDITOR
//private:
//	TSharedPtr<FUNAAuthManager> Authorizer;
//#endif // WITH_EDITOR
};
