// Copyright 1998-2018 Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class AscentCombatFramework : ModuleRules
{
	public AscentCombatFramework(ReadOnlyTargetRules Target) : base(Target)
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
                "AIModule" ,
                "GameplayTags",
                "AdvancedRPGSystem",
				"AscentCoreInterfaces",
				"InventorySystem",
				"CollisionsManager",
				"MotionWarping",
				"NetCore",
				"ActionsSystem",
				"CharacterController",
                "AscentGASRuntime",
                "GameplayAbilities",
                "CinematicCameraManager"
				
				// ... add other public dependencies that you statically link with here ...
			}
			);
			
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"CoreUObject",
				"Engine",
                "GameplayTags",
                "OnlineSubsystem", "OnlineSubsystemUtils", "UMG",
                "Slate", "SlateCore","AIModule", 
                "AscentTargetingSystem", "NavigationSystem",
                "PhysicsCore", "DeveloperSettings", "AscentSaveSystem", "AnimGraphRuntime", "Chooser",
                "GameplayTasks", "AscentTeams", "CommonUI",
                "GeometryCollectionEngine"

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
