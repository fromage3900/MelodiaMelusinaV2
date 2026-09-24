// Copyright 2025 Dmitry Karpukhin. All Rights Reserved.

#include "SSFS.h"
#include "Interfaces/IPluginManager.h"
#include "ShaderCore.h"

#define LOCTEXT_NAMESPACE "FScreenSpaceFogScatteringModule"

void FScreenSpaceFogScatteringModule::StartupModule()
{
	FString PluginShaderDir = FPaths::Combine(IPluginManager::Get().FindPlugin(TEXT("ScreenSpaceFogScattering"))->GetBaseDir(), TEXT("Shaders"));
	AddShaderSourceDirectoryMapping(TEXT("/Plugin/ScreenSpaceFogScattering"), PluginShaderDir);
}

void FScreenSpaceFogScatteringModule::ShutdownModule()
{
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FScreenSpaceFogScatteringModule, ScreenSpaceFogScattering)