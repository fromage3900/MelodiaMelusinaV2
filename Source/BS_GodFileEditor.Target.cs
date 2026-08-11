// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class BS_GodFileEditorTarget : TargetRules
{
	public BS_GodFileEditorTarget( TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V7;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
		ExtraModuleNames.Add("BS_GodFile");

		// Validate GMM manifests before every editor build.
		PreBuildSteps.Add(
			"set PYTHONPATH=$(ProjectDir)\\Content\\Python & "
			+ "python $(ProjectDir)\\Content\\Python\\validate_melodia_manifest.py "
			+ "$(ProjectDir)\\Content\\Python\\gmm\\fixtures\\melodia_project_manifest.fixture.json"
		);
	}
}
