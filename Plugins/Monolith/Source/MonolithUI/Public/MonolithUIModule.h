#pragma once

#include "Modules/ModuleManager.h"

class FMonolithUIModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
