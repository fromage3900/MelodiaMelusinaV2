using UnrealBuildTool;
using System.IO;

public class MonolithLogicDriver : ModuleRules
{
	public MonolithLogicDriver(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// Release builds: set MONOLITH_RELEASE_BUILD=1 to force all optional deps off.
		bool bHasLogicDriver = false;
		bool bReleaseBuild = System.Environment.GetEnvironmentVariable("MONOLITH_RELEASE_BUILD") == "1";

		if (!bReleaseBuild)
		{
			// 1. Check project Plugins/ folder
			string ProjectPluginsDir = Path.Combine(
				Target.ProjectFile.Directory.FullName, "Plugins");
			if (Directory.Exists(ProjectPluginsDir))
			{
				bHasLogicDriver = Directory.Exists(
					Path.Combine(ProjectPluginsDir, "SMSystem"))
					|| Directory.GetDirectories(
						ProjectPluginsDir, "LogicDri*",
						SearchOption.TopDirectoryOnly).Length > 0;
			}

			// 2. Check Engine Plugins/Marketplace/ folder (Fab install)
			if (!bHasLogicDriver)
			{
				string EngineDir = Path.GetFullPath(Target.RelativeEnginePath);
				string MarketplaceDir = Path.Combine(EngineDir, "Plugins", "Marketplace");
				if (Directory.Exists(MarketplaceDir))
				{
					bHasLogicDriver = Directory.GetDirectories(
						MarketplaceDir, "LogicDri*",
						SearchOption.TopDirectoryOnly).Length > 0;
				}

				// 3. Check Engine Plugins/ root
				if (!bHasLogicDriver)
				{
					string EnginePluginsDir = Path.Combine(EngineDir, "Plugins");
					bHasLogicDriver = Directory.Exists(
						Path.Combine(EnginePluginsDir, "SMSystem"));
				}
			}
		}

		if (bHasLogicDriver)
		{
			PrivateDependencyModuleNames.AddRange(new string[]
			{
				"Core", "CoreUObject", "Engine",
				"MonolithCore", "MonolithIndex",
				"UnrealEd",
				"BlueprintGraph",
				"EditorScriptingUtilities",
				"SMSystem", "SMSystemEditor",
				"GameplayTags",
				"Json", "JsonUtilities"
			});
			PublicDefinitions.Add("WITH_LOGICDRIVER=1");
		}
		else
		{
			PrivateDependencyModuleNames.AddRange(new string[]
			{
				"Core", "CoreUObject", "Engine",
				"MonolithCore"
			});
			PublicDefinitions.Add("WITH_LOGICDRIVER=0");
		}
	}
}
