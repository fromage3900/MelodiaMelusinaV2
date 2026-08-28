// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class BS_GodFile : ModuleRules
{
	public BS_GodFile(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"Water",
			"Niagara",
			"MetasoundEngine",
			"DeveloperSettings",
			"InputCore",
			"EnhancedInput",
			"CommonUI",
			"PCG",
			"ProceduralMeshComponent",
			"Quillscript",
			"MelodiaCore",  // Added for Melodia integration
			"MelodiaShader", // Custom shader source (ink, Nikki, bioluminescence) — Rider-indexed .usf/.ush

			// Harmonix owns authored musical time for the rhythm presentation
			// layer (see Docs/HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md).
			// These ship with the engine and are enabled in BS_GodFile.uproject.
			"Harmonix",          // ECalibratedMusicTimebase, musical time primitives
			"HarmonixMidi",      // UMidiFile
			"HarmonixMetasound"  // UMusicClockComponent
		});

		PrivateDependencyModuleNames.AddRange(new string[] { "UMG", "Slate", "SlateCore", "HTTP", "Json" });

		if (Target.bBuildEditor)
		{
			PrivateIncludePaths.Add(System.IO.Path.Combine(EngineDirectory, "Source/Runtime/Engine/Internal"));
			PrivateDependencyModuleNames.AddRange(new string[] {
				"UnrealEd",
				"AssetTools",
				"NiagaraEditor",
				"PCGEditor",
				"MeshPartition",
				"MeshPartitionEditor",
				"GeometryScriptingCore",
				// UDynamicMesh itself lives in GeometryFramework, not GeometryScriptingCore.
				// PCGScaleWorldEditorLibrary.cpp calls NewObject<UDynamicMesh>, IsEmpty,
				// GetTriangleCount and ExtractMesh, which link only against this module.
				"GeometryFramework"
			});
		}

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });
		
		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
