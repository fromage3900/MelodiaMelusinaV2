// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlend.h"
#include "ShaderCore.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"

#define LOCTEXT_NAMESPACE "FMeshBlendModule"

const FString PluginName = FString(TEXT("MeshBlend"));

void FMeshBlendModule::StartupModule()
{
	FString PluginBaseDirectory = IPluginManager::Get().FindPlugin(PluginName)->GetBaseDir();
	const FString ShaderDirectory = FPaths::Combine(PluginBaseDirectory, TEXT("Shaders"));
	const FString VirtualShaderDirectory = FString::Printf(TEXT("/Plugin/%s"), *PluginName);
	AddShaderSourceDirectoryMapping(VirtualShaderDirectory, ShaderDirectory);
}

void FMeshBlendModule::ShutdownModule()
{
	ResetAllShaderSourceDirectoryMappings();
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMeshBlendModule, MeshBlend)
