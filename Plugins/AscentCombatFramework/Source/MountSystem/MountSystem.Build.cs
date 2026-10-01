// Copyright 1998-2019 Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class MountSystem : ModuleRules
{
	public MountSystem(ReadOnlyTargetRules Target) : base(Target)
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
                "AscentCombatFramework",
				"AIFramework"   ,
				"CharacterController",
				"AscentTeams",
				"AscentCoreInterfaces",
				"ActionsSystem"
			}
			);
			
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"CoreUObject",
				"Engine",
				"Slate",
				"SlateCore",
                "UMG",
               "GameplayTags" ,
               "Networking",
              "OnlineSubsystem",
              "OnlineSubsystemUtils",
              "CinematicCameraManager",
			  "AIModule",
			  "AscentCoreInterfaces",
              "NavigationSystem",
			  "GameplayAbilities"

				// ... add private dependencies that you statically link with here ...	
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
