// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


using UnrealBuildTool;

public class AscentDialogueSystemEditor : ModuleRules
{
    public AscentDialogueSystemEditor(ReadOnlyTargetRules Target) : base(Target)
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
                "AGSGraphEditor",
                "GameplayTags",
                "UnrealEd",
                "PropertyEditor",
                 "EditorSubsystem",
            "ToolMenus",
                 "AssetTools",
                 "EditorScriptingUtilities",
                  "Json",
                 "HTTP",
                 "AudioExtensions",
                 "SignalProcessing",
                 "AudioMixer", 
				// ... add other public dependencies that you statically link with here ...
			}
            );


        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore",
                "AscentDialogueSystem",
                  "UnrealEd",
                  "AGSGraphRuntime",
                  "InputCore",
                  "AssetRegistry",
                  "ContentBrowser"
				// ... add private dependencies that you statically link with here ...	
			}
            );

        // MetaHuman (Animator) only supports Win64/Linux. Pull its modules in
        // conditionally so the editor module still builds on unsupported platforms
        // (e.g. Mac), where facial-animation generation is gracefully disabled.
        if (Target.Platform == UnrealTargetPlatform.Win64 || Target.Platform == UnrealTargetPlatform.Linux)
        {
            PrivateDependencyModuleNames.AddRange(
                new string[]
                {
                    "MetaHumanPerformance",
                    "MetaHumanSpeech2Face"
                }
            );
            PublicDefinitions.Add("WITH_ADS_METAHUMAN=1");
        }
        else
        {
            PublicDefinitions.Add("WITH_ADS_METAHUMAN=0");
        }


        DynamicallyLoadedModuleNames.AddRange(
            new string[]
            {
				// ... add any modules that your module loads dynamically here ...
			}
            );
    }
}
