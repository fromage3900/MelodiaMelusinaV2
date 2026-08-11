using UnrealBuildTool;
using System.IO;

public class MonolithBABridge : ModuleRules
{
	public MonolithBABridge(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// Probe for Blueprint Assist in multiple locations.
		// BA installs to Engine/Plugins/Marketplace/ with an obfuscated folder name,
		// or can be manually placed in the project's Plugins/ folder.
		//
		// Release builds: set MONOLITH_RELEASE_BUILD=1 to force all optional deps off.
		// This ensures binary releases don't link against plugins the user may not have.
		bool bHasBlueprintAssist = false;
		bool bReleaseBuild = System.Environment.GetEnvironmentVariable("MONOLITH_RELEASE_BUILD") == "1";

		if (!bReleaseBuild)
		{
			// 1. Check project Plugins/ folder (manual install or symlink)
			string ProjectPluginsDir = Path.Combine(
				Target.ProjectFile.Directory.FullName, "Plugins");
			if (Directory.Exists(ProjectPluginsDir))
			{
				bHasBlueprintAssist = Directory.Exists(
					Path.Combine(ProjectPluginsDir, "BlueprintAssist"));

				if (!bHasBlueprintAssist)
				{
					bHasBlueprintAssist = Directory.GetDirectories(
						ProjectPluginsDir, "Blueprin*",
						SearchOption.TopDirectoryOnly).Length > 0;
				}
			}

			// 2. Check Engine Plugins/Marketplace/ folder (Fab/launcher install)
			if (!bHasBlueprintAssist)
			{
				string EngineDir = Path.GetFullPath(Target.RelativeEnginePath);
				string MarketplaceDir = Path.Combine(EngineDir, "Plugins", "Marketplace");
				if (Directory.Exists(MarketplaceDir))
				{
					bHasBlueprintAssist = Directory.GetDirectories(
						MarketplaceDir, "Blueprin*",
						SearchOption.TopDirectoryOnly).Length > 0;
				}

				// 3. Check Engine Plugins/ root (some installs go here)
				if (!bHasBlueprintAssist)
				{
					string EnginePluginsDir = Path.Combine(EngineDir, "Plugins");
					bHasBlueprintAssist = Directory.Exists(
						Path.Combine(EnginePluginsDir, "BlueprintAssist"));
				}
			}
		}

		if (bHasBlueprintAssist)
		{
			// Full implementation -- link against BA
			PrivateDependencyModuleNames.AddRange(new string[]
			{
				"Core", "CoreUObject", "Engine",
				"Slate", "SlateCore",
				"MonolithCore",
				"BlueprintAssist",
				"UnrealEd", "GraphEditor",
				"Json"
			});
			PublicDefinitions.Add("WITH_BLUEPRINT_ASSIST=1");
		}
		else
		{
			// Empty shell -- compiles clean, does nothing at runtime
			PrivateDependencyModuleNames.AddRange(new string[]
			{
				"Core", "CoreUObject", "Engine",
				"MonolithCore"
			});
			PublicDefinitions.Add("WITH_BLUEPRINT_ASSIST=0");
		}
	}
}
