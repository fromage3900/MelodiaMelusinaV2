// Copyright 1998-2019 Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class AscentSkillTree : ModuleRules
{
    public AscentSkillTree(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(
            new string[] {
				// ... add public include paths required here ...
			}
        );


        PrivateIncludePaths.AddRange(
            new string[] {
				// ... add other private include paths required here ...
			}
        );


        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core",
                "AGSGraphRuntime",
                "GameplayTags",
                "AdvancedRPGSystem",
                "EnhancedInput",
                "GameplayAbilities",
                "CommonUI",
                "SlateCore",
                "MediaAssets",
                "AscentCoreInterfaces",
                "AscentGASRuntime",
                "NetCore",
                "AscentUINavigationSystem",
            }
        );


        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "CoreUObject",
                "Engine",
                "UMG",
                "Slate",
                "AscentCoreInterfaces",
                "SlateCore",
                "ActionsSystem",
                "AscentUINavigationSystem"
            }
        );


        DynamicallyLoadedModuleNames.AddRange(
            new string[]
            {
				// ... add any modules that your module loads dynamically here ...
			}
        );
    }
}