// Copyright 2025 Dmitry Karpukhin. All Rights Reserved.

using UnrealBuildTool;
using System.IO;

public class ScreenSpaceFogScattering : ModuleRules
{
	public ScreenSpaceFogScattering(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		
		PrivateIncludePaths.AddRange(
			new string[] {
				Path.Combine(EngineDirectory, "Source/Runtime/Renderer/Private")
			}
		);
		
		if (Target.Version.MajorVersion == 5 && Target.Version.MinorVersion >= 6)
		{
			PrivateIncludePaths.Add(Path.Combine(EngineDirectory, "Source/Runtime/Renderer/Internal"));
		}
		
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
			}
		);
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"RenderCore",
				"Renderer",
				"RHI",
				"Projects",
			}
		);
	}
}
