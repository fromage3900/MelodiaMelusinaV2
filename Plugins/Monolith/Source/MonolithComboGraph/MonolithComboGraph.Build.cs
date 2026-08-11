using UnrealBuildTool;
using System.IO;

public class MonolithComboGraph : ModuleRules
{
	public MonolithComboGraph(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// Release builds: set MONOLITH_RELEASE_BUILD=1 to force all optional deps off.
		bool bHasComboGraph = false;
		bool bReleaseBuild = System.Environment.GetEnvironmentVariable("MONOLITH_RELEASE_BUILD") == "1";

		if (!bReleaseBuild)
		{
			// 1. Check project Plugins/ folder
			string ProjectPluginsDir = Path.Combine(
				Target.ProjectFile.Directory.FullName, "Plugins");
			if (Directory.Exists(ProjectPluginsDir))
			{
				bHasComboGraph = Directory.Exists(
					Path.Combine(ProjectPluginsDir, "ComboGraph"))
					|| Directory.GetDirectories(
						ProjectPluginsDir, "ComboGra*",
						SearchOption.TopDirectoryOnly).Length > 0;
			}

			// 2. Check Engine Plugins/Marketplace/ folder (Fab install)
			if (!bHasComboGraph)
			{
				string EngineDir = Path.GetFullPath(Target.RelativeEnginePath);
				string MarketplaceDir = Path.Combine(EngineDir, "Plugins", "Marketplace");
				if (Directory.Exists(MarketplaceDir))
				{
					bHasComboGraph = Directory.GetDirectories(
						MarketplaceDir, "ComboGra*",
						SearchOption.TopDirectoryOnly).Length > 0;
				}

				// 3. Check Engine Plugins/ root
				if (!bHasComboGraph)
				{
					string EnginePluginsDir = Path.Combine(EngineDir, "Plugins");
					bHasComboGraph = Directory.Exists(
						Path.Combine(EnginePluginsDir, "ComboGraph"));
				}
			}
		}

		if (bHasComboGraph)
		{
			PrivateDependencyModuleNames.AddRange(new string[]
			{
				"Core", "CoreUObject", "Engine",
				"MonolithCore",
				"UnrealEd",
				"GameplayAbilities", "GameplayTags",
				"GameplayAbilitiesEditor", "GameplayTasksEditor",
				"BlueprintGraph",
				"EditorScriptingUtilities",
				"ComboGraph", "ComboGraphEditor",
				"Json", "JsonUtilities"
			});
			PublicDefinitions.Add("WITH_COMBOGRAPH=1");
		}
		else
		{
			PrivateDependencyModuleNames.AddRange(new string[]
			{
				"Core", "CoreUObject", "Engine",
				"MonolithCore"
			});
			PublicDefinitions.Add("WITH_COMBOGRAPH=0");
		}
	}
}
