// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

using System.IO;
using UnrealBuildTool;

public class ActionsSystem : ModuleRules
{
    public ActionsSystem(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(
            new string[]
            {
                Path.Combine(ModuleDirectory, "Public")
            }
            );


        PrivateIncludePaths.AddRange(
            new string[]
            {

            }
            );


        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core",
                "CollisionsManager",
                "AscentCoreInterfaces",
                "AdvancedRPGSystem",
                 "GameplayTags",
                 "MotionWarping",
                    "GameplayAbilities",
                  "GameplayTasks",
                  "EnhancedInput"

            }
            );


        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "Core",
                "CoreUObject",
                "Engine",
                "AIModule",
                "DeveloperSettings",
                "MotionWarping",
                 "GameplayAbilities",
                  "GameplayTasks",
              "AscentGASRuntime",
            }
            );


        DynamicallyLoadedModuleNames.AddRange(
            new string[]
            {

            }
            );
    }
}
