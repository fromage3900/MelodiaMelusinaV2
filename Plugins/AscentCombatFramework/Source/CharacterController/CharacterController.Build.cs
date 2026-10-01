// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

using System.IO;
using UnrealBuildTool;

public class CharacterController : ModuleRules
{
	public CharacterController(ReadOnlyTargetRules Target) : base(Target)
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
				"AscentCoreInterfaces",
				"DeveloperSettings",
				"AdvancedRPGSystem",
				"ActionsSystem",
				"Niagara",
                 "AnimationCore",
                 "AscentGASRuntime",
                 "GameplayAbilities",
                 "EnhancedInput",
                 "GameplayTags"
            }
			);
			
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"GameplayTags",
				"AnimGraphRuntime",
				"AIModule",
				"AscentTargetingSystem",
				"MotionWarping",
				"InventorySystem"
			}
			);
		
		
		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				
			}
			);
	}
}
