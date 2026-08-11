using UnrealBuildTool;

public class MonolithAI : ModuleRules
{
	// Returns true iff `PluginName` is ENABLED for this target (not merely present on disk).
	// Mirrors UnrealBuildTool Plugins.IsPluginEnabledForTarget (UE 5.7
	// Engine/Source/Programs/UnrealBuildTool/System/Plugins.cs:693). Fixes issue #71:
	// engine plugins ship-but-default-off (EnabledByDefault:false), so disk presence != enablement.
	// Design + API citations: Docs/plans/2026-06-15-issue71-plugin-enablement-gating.md.
	// Keep BYTE-IDENTICAL with the copies in MonolithMesh/MonolithIndex/MonolithAudio/MonolithAnimation.
	private static bool IsPluginEnabled(ReadOnlyTargetRules Target, string PluginName)
	{
		if (Target.ProjectFile == null)
		{
			return false;   // engine/program target with no .uproject: every gated engine plugin is EnabledByDefault:false -> treat as OFF
		}

		// 1. Target-level overrides win outright (uncommon but correct: -EnablePlugin=/-DisablePlugin=).
		if (Target.DisablePlugins != null && System.Linq.Enumerable.Contains(Target.DisablePlugins, PluginName)) { return false; }
		if (Target.EnablePlugins  != null && System.Linq.Enumerable.Contains(Target.EnablePlugins,  PluginName)) { return true;  }

		// 2. The .uproject's explicit Plugins[] entry (non-optional) is the deciding signal.
		try
		{
			ProjectDescriptor Project = ProjectDescriptor.FromFile(Target.ProjectFile);
			if (Project.Plugins != null)
			{
				foreach (PluginReferenceDescriptor Ref in Project.Plugins)
				{
					if (string.Equals(Ref.Name, PluginName, System.StringComparison.OrdinalIgnoreCase) && !Ref.bOptional)
					{
						return Ref.bEnabled
							&& Ref.IsEnabledForPlatform(Target.Platform)
							&& Ref.IsEnabledForTargetConfiguration(Target.Configuration)
							&& Ref.IsEnabledForTarget(Target.Type);
					}
				}
			}
		}
		catch (System.Exception)
		{
			return false;   // unreadable .uproject -> fail safe to OFF (never hard-link)
		}

		// 3. No .uproject entry -> falls to the .uplugin EnabledByDefault. ALL gated plugins here are
		//    engine plugins with EnabledByDefault:false, so absence == disabled. Return false.
		//    (If a future gated plugin were EnabledByDefault:true, this branch would need to read its
		//    .uplugin; documented as a known limitation in the plan.)
		return false;
	}

	public MonolithAI(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// Always-available engine AI modules
		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core", "CoreUObject", "Engine",
			"AIModule", "GameplayTasks", "GameplayTags", "NavigationSystem"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"MonolithCore", "MonolithBlueprint", "MonolithIndex",
			"UnrealEd", "BlueprintGraph", "AIGraph",
			"BehaviorTreeEditor", "EnvironmentQueryEditor",
			"Projects",  // IPluginManager (Phase D2)
			"Json", "JsonUtilities",
			"SQLiteCore"
		});

		// --- Conditional optional deps ---
		// MONOLITH_RELEASE_BUILD=1 forces all optional plugin deps OFF so binary
		// release zips never hard-link against plugins the end-user may not have
		// enabled. Mirrors the pattern in MonolithGAS.Build.cs / MonolithUI.Build.cs.
		// Origin: GitHub issue #30 (MonolithMesh.dll hard-linked GeometryScriptingCore).
		bool bReleaseBuild = System.Environment.GetEnvironmentVariable("MONOLITH_RELEASE_BUILD") == "1";

		// --- Conditional: StateTree (engine plugin, EnabledByDefault=false) ---
		// StateTree itself contains StateTreeModule + StateTreeEditorModule (UncookedOnly).
		// GameplayStateTree is a SEPARATE engine plugin that depends on StateTree and
		// supplies StateTreeAIComponent / BT-to-StateTree task bridge.
		// PropertyBindingUtils is also a separate engine plugin required by
		// StateTree's binding/instance-data system. We gate the StateTree family
		// together under bHasStateTree because StateTree's own .uplugin lists
		// PropertyBindingUtils as a required dep and GameplayStateTree.uplugin
		// requires StateTree. Without StateTree the others are dead weight.
		// (Historical: the StructUtils plugin was previously listed here but is
		// deprecated since UE 5.5 — FInstancedStruct relocated into CoreUObject
		// and resolves transparently via the existing CoreUObject Public dep above.)
		//
		// Issue #71: gate on ENABLEMENT (read from the .uproject), not disk presence.
		// StateTree ships under Engine/Plugins/Runtime on every UE 5.7 install but is
		// EnabledByDefault:false; disk presence would false-positive a hard-link on a
		// source builder who hasn't enabled it. GameplayStateTree/PropertyBindingUtils are
		// co-enabled with StateTree (StateTree.uplugin requires them), so checking StateTree
		// alone is sufficient.
		bool bHasStateTree = !bReleaseBuild && IsPluginEnabled(Target, "StateTree");

		if (bHasStateTree)
		{
			PrivateDependencyModuleNames.AddRange(new string[]
			{
				"StateTreeModule", "StateTreeEditorModule",
				"GameplayStateTreeModule",
				"PropertyBindingUtils"
			});
			PublicDefinitions.Add("WITH_STATETREE=1");
		}
		else
		{
			PublicDefinitions.Add("WITH_STATETREE=0");
		}

		// --- Conditional: SmartObjects (engine plugin, EnabledByDefault=false) ---
		// SmartObjects plugin contains SmartObjectsModule + SmartObjectsEditorModule.
		// Both gated together — editor module is always co-installed with runtime.
		// Issue #71: gate on ENABLEMENT, not disk presence (ships-but-off on every install).
		bool bHasSmartObjects = !bReleaseBuild && IsPluginEnabled(Target, "SmartObjects");

		if (bHasSmartObjects)
		{
			PrivateDependencyModuleNames.AddRange(new string[]
			{
				"SmartObjectsModule",
				"SmartObjectsEditorModule"
			});
			PublicDefinitions.Add("WITH_SMARTOBJECTS=1");
		}
		else
		{
			PublicDefinitions.Add("WITH_SMARTOBJECTS=0");
		}

		// --- Conditional: GameplayAbilities (Phase I2: BT-to-GAS task) ---
		// Engine plugin (EnabledByDefault:false) but listed NON-optional in Monolith.uplugin,
		// so it is force-enabled when the user enables Monolith. Issue #71: gate on ENABLEMENT
		// rather than disk presence — correct for the normal case and also handles a user who
		// explicitly disables GameplayAbilities in their .uproject.
		bool bHasGameplayAbilities = !bReleaseBuild && IsPluginEnabled(Target, "GameplayAbilities");

		if (bHasGameplayAbilities)
		{
			PublicDependencyModuleNames.Add("GameplayAbilities");
			PublicDefinitions.Add("WITH_GAMEPLAYABILITIES=1");
		}
		else
		{
			PublicDefinitions.Add("WITH_GAMEPLAYABILITIES=0");
		}

		// --- Conditional: GameplayBehaviors (Experimental) ---
		// Issue #71 PRIMARY FIX: Optional:true in Monolith.uplugin, so NOT transitively
		// enabled when the user enables Monolith. Ships on disk on every install →
		// disk presence false-positived a hard-link → GetLastError=126 for source builders
		// who didn't enable it. Gate on ENABLEMENT read from the .uproject.
		bool bHasGameplayBehaviors = !bReleaseBuild && IsPluginEnabled(Target, "GameplayBehaviors");

		if (bHasGameplayBehaviors)
		{
			PrivateDependencyModuleNames.Add("GameplayBehaviorsModule");
			PublicDefinitions.Add("WITH_GAMEPLAYBEHAVIORS=1");
		}
		else
		{
			PublicDefinitions.Add("WITH_GAMEPLAYBEHAVIORS=0");
		}

		// --- Conditional: Mass (Experimental) ---
		// Issue #71 PRIMARY FIX. This block links MassEntity + MassSpawner + MassGameplayEditor.
		// MassSpawner (MassGameplay.uplugin:36) and MassGameplayEditor (:68) are MassGameplay-plugin
		// modules. The MassEntity *plugin* is DEPRECATED in 5.7 (empty Modules:[], DeprecatedEngineVersion:5.5)
		// — the MassEntity *module* now lives in the engine, not the plugin. So we gate ONLY on the
		// MassGameplay plugin's enablement (the name users put in .uproject), never on MassEntity.
		// MassGameplay is Optional:true in Monolith.uplugin → NOT transitively enabled; disk presence
		// false-positived a hard-link on MassSpawner/MassGameplayEditor → GetLastError=126.
		bool bHasMassEntity = !bReleaseBuild && IsPluginEnabled(Target, "MassGameplay");

		if (bHasMassEntity)
		{
			// MassGameplayEditor lives in Runtime/MassGameplay — assumed co-installed with MassEntity
			PrivateDependencyModuleNames.AddRange(new string[] { "MassEntity", "MassSpawner", "MassGameplayEditor" });
			PublicDefinitions.Add("WITH_MASSENTITY=1");
		}
		else
		{
			PublicDefinitions.Add("WITH_MASSENTITY=0");
		}

		// --- Conditional: ZoneGraph (Experimental) ---
		// Issue #71 PRIMARY FIX: Optional:true in Monolith.uplugin, ships-but-off on every
		// install → disk presence false-positived a hard-link on ZoneGraph → GetLastError=126.
		// Gate on ENABLEMENT read from the .uproject.
		bool bHasZoneGraph = !bReleaseBuild && IsPluginEnabled(Target, "ZoneGraph");

		if (bHasZoneGraph)
		{
			PrivateDependencyModuleNames.Add("ZoneGraph");
			PublicDefinitions.Add("WITH_ZONEGRAPH=1");
		}
		else
		{
			PublicDefinitions.Add("WITH_ZONEGRAPH=0");
		}
	}
}
