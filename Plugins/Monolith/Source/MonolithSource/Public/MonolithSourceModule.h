#pragma once

#include "Modules/ModuleManager.h"

class FMonolithSourceModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
