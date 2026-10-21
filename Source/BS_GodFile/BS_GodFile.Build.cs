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
			"GameplayTags",
			"KawaiiPhysics",
			"Water",
			"Niagara",
			"MetasoundEngine",
			"DeveloperSettings",
			"InputCore",
			"EnhancedInput",
			"CommonUI",
			"MultiWorld",
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

		PrivateDependencyModuleNames.AddRange(new string[] { "UMG", "Slate", "SlateCore", "ApplicationCore", "HTTP", "Json", "NiagaraUIRenderer", "Sockets", "Networking",
			// MelodiaLiveVoiceSubsystem binds UADSGraphNode::OnUnvoicedLine so silent
			// dialogue nodes can be spoken live. ADS never depends on BS_GodFile (no cycle).
			"AscentDialogueSystem" });

		if (Target.bBuildEditor)
		{
			PrivateIncludePaths.Add(System.IO.Path.Combine(EngineDirectory, "Source/Runtime/Engine/Internal"));
			PrivateDependencyModuleNames.AddRange(new string[] {
				"UnrealEd",
				"AssetTools",
				// UK2Node_CallFunction, for the wiring-contract tests that identify
				// Blueprint call sites by their referenced UFunction name. Editor-only;
				// the tests are behind WITH_EDITOR && WITH_DEV_AUTOMATION_TESTS.
				"BlueprintGraph",
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
