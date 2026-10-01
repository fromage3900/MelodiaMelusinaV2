// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using System.IO;
using UnrealBuildTool;

public class InventorySystem : ModuleRules
{
    public InventorySystem(ReadOnlyTargetRules Target)
        : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(
            new string[] {
                Path.Combine(ModuleDirectory, "Public")
            });

        PrivateIncludePaths.AddRange(
            new string[] {

            });

        PublicDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                 "AdvancedRPGSystem",
                "CollisionsManager",
                "AscentCoreInterfaces",
                "AscentSaveSystem",
                "GameplayTags",
                "AIModule",
                "AscentGASRuntime",
                "GameplayAbilities"
            });

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "CoreUObject",
                "Engine",
                "NavigationSystem",
                "DeveloperSettings",
                 "ActionsSystem",
                 "NetCore","AscentTeams"
            });

        DynamicallyLoadedModuleNames.AddRange(
            new string[] {

            });
    }
}
