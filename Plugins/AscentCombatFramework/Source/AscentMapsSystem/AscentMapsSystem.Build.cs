// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using System.IO;
using UnrealBuildTool;

public class AscentMapsSystem : ModuleRules {
    public AscentMapsSystem(ReadOnlyTargetRules Target)
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
                "Core", "GameplayTags", "UMG",
                "Slate", "SlateCore", "InputCore",
                "CommonUI"
            });

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore",
                "UMG",
                "DeveloperSettings",
                "CommonUI",
                "CommonInput"
            });

        DynamicallyLoadedModuleNames.AddRange(
            new string[] {

            });
    }
}
