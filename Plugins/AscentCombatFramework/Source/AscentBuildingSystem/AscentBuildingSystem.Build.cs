// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using UnrealBuildTool;

public class AscentBuildingSystem : ModuleRules
{
    public AscentBuildingSystem(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
            {
                "Core",
                "CoreUObject",
                "Engine",
                "InventorySystem",
                "NetCore",
                "AscentSaveSystem",
                "AscentCoreInterfaces"
            });

        PrivateDependencyModuleNames.AddRange(
            new string[]
            {"EnhancedInput",
            "NetCore"   
            });

        DynamicallyLoadedModuleNames.AddRange(
            new string[]
            {

            });
    }
}
