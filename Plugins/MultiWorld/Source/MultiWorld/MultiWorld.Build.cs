// Copyright 1998-2019 Epic Games, Inc. All Rights Reserved.

using System.IO;
using UnrealBuildTool;
using UnrealBuildTool.Rules;

public class MultiWorld : ModuleRules
{
	public MultiWorld(ReadOnlyTargetRules Target) : base(Target)
	{
		// Below line is needed by "BuildBinaryRedist.ps1" script.
		bUsePrecompiled=bUsePrecompiled;
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		
		PublicIncludePaths.AddRange(
			new string[] {
				// ... add public include paths required here ...
			}
			);
				
		
		PrivateIncludePaths.AddRange(
			new string[] {
				// ... add other private include paths required here ...
				System.IO.Path.Combine(EngineDirectory, "Source", "Runtime", "Renderer", "Private"),
				System.IO.Path.Combine(EngineDirectory, "Source", "Runtime", "Renderer", "Internal")
			}
			);
			
		
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				// ... add other public dependencies that you statically link with here ...
			}
			);
			
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"CoreUObject",
				"Engine",
				"Slate",
				"SlateCore",
				"EngineSettings",
				"UMG",
				"InputCore",
				"EnhancedInput",
				"RenderCore"
				// ... add private dependencies that you statically link with here ...	
			}
			);

		if(Target.Type == TargetType.Editor)
		{
            PrivateIncludePaths.AddRange(
            new string[] {
                Path.GetFullPath(Path.Combine(EngineDirectory, "Source/Editor/PluginWarden/Private"))
            });

            PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"UnrealEd",
				"OpenSSL",
				"PluginWarden",
				"PortalServices",
				"LauncherPlatform",
				"Kismet"
            }
			);
		}
		
		
		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				// ... add any modules that your module loads dynamically here ...
			}
			);
	}
}
