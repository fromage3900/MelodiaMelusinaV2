// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using UnrealBuildTool;

public class AscentMapsEditor : ModuleRules {
    public AscentMapsEditor(ReadOnlyTargetRules Target)
        : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] {
            "Core",
            "CoreUObject",
            "Engine",
            "UMGEditor",
            "Blutility",
            "EditorSubsystem"
        });

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "InputCore",
                "EditorFramework",
                "UnrealEd",
                "ToolMenus",
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore",
                "BlueprintGraph",
                "Projects"
            });

        DynamicallyLoadedModuleNames.AddRange(
            new string[] {

            });
    }
}
