// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using UnrealBuildTool;

public class AscentGASRuntime : ModuleRules
{
	public AscentGASRuntime(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] 
			{ 
				"Core",
				"CoreUObject",
				"Engine",
				"GameplayAbilities",
				"UMG"
			});
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
                "GameplayAbilities",
                 "GameplayTags",
                 "DeveloperSettings"
            });
		
		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				
			});
	}
}
