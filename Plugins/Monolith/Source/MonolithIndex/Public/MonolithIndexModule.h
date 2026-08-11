#pragma once

#include "Modules/ModuleManager.h"

class FMonolithIndexModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
