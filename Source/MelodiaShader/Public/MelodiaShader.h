// Copyright 2026 BS_GodFile. All Rights Reserved.
//
// MelodiaShader module registration.
// The shader source lives in Shaders/ and is indexed by Rider as HLSL.
// No C++ types are exported from this module — it is a pure shader source container.

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FMelodiaShaderModule : public IModuleInterface
{
public:
    virtual void StartupModule() override {}
    virtual void ShutdownModule() override {}
};
