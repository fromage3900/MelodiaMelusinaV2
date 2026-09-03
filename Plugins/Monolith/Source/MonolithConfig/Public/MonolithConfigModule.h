#pragma once

#include "Modules/ModuleManager.h"

class FMonolithConfigModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
