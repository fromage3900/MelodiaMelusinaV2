// MelodiaCore ΓÇö Turn-based rhythm battle kernel.
// Ported from MelodiaMelusina_PROD (UE 5.7.2) to UE 5.8 plugin.

using UnrealBuildTool;

public class MelodiaCore : ModuleRules
{
	public MelodiaCore(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// This legacy module keeps exported headers at the module root rather than
		// under Public/. Expose that root to dependent modules such as BS_GodFile.
		PublicIncludePaths.Add(ModuleDirectory);

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AudioMixer",
			"UMG",
			"Slate",
			"SlateCore",
			"AIModule",
			"Networking",
			"Sockets",
			"Quillscript"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"ImageWrapper",
			"Json",
			"JsonUtilities",
			"ProceduralDungeon",
			"PCG"
		});

		if (Target.bBuildEditor)
		{
			PrivateDependencyModuleNames.Add("UnrealEd");
		}

		// iOS/mobile platform support
		if (Target.Platform == UnrealTargetPlatform.IOS || Target.Platform == UnrealTargetPlatform.Android)
		{
			PublicDependencyModuleNames.Add("MobileUtils");
			PublicDefinitions.Add("MELODIA_MOBILE=1");
		}

		// iOS specific
		if (Target.Platform == UnrealTargetPlatform.IOS)
		{
			PublicDefinitions.Add("MELODIA_IOS=1");
		}

		// EOS for cloud saves
		if (Target.bBuildEditor == false)
		{
			PublicDependencyModuleNames.Add("OnlineSubsystem");
			PublicDependencyModuleNames.Add("OnlineSubsystemUtils");
		}

		// TODO-OPCODE: add PreBuildStep for GMM manifest validation
		// Validate GMM manifests before every editor build.
		// Set this in BS_GodFileEditor.Target.cs: PreBuildSteps.Add(...)
		// Example:
		//   set PYTHONPATH=$(ProjectDir)Content\Python &
		//   python $(ProjectDir)Content\Python\validate_melodia_manifest.py
		//     $(ProjectDir)Content\Melodia\DataStuctures\DT_Blessings.json
	}
}
