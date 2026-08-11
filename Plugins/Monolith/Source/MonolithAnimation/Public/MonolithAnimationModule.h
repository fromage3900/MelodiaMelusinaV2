#pragma once

#include "Modules/ModuleManager.h"

class FMonolithAnimationModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
