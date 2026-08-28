// Copyright 2026 BS_GodFile. All Rights Reserved.

#include "MelodiaShader.h"
#include "Misc/Paths.h"
#include "ShaderCore.h"

void FMelodiaShaderModule::StartupModule()
{
	const FString ShaderDirectory = FPaths::Combine(
		FPaths::ProjectDir(), TEXT("Source/MelodiaShader/Shaders"));
	AddShaderSourceDirectoryMapping(TEXT("/Melodia"), ShaderDirectory);
}

IMPLEMENT_MODULE(FMelodiaShaderModule, MelodiaShader)
