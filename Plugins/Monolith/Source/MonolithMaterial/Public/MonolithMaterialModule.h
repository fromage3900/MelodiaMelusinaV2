#pragma once

#include "Modules/ModuleManager.h"

class FMonolithMaterialModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
