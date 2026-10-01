// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "ACFSkillsLibrary.generated.h"

/**
 * Editor-only helpers to deploy the Claude skills that ship with the AscentCombatFramework
 * plugin into the current project. Skills are stored under the plugin's Resources/Skills folder
 * and are copied into <ProjectDir>/.claude/skills so they become available to Claude for this project.
 */
UCLASS()
class ASCENTEDITOREXTENSIONS_API UACFSkillsLibrary : public UBlueprintFunctionLibrary {
	GENERATED_BODY()

public:
	/**
	 * Copies every skill folder shipped under the AscentCombatFramework plugin's Resources/Skills
	 * into the current project's .claude/skills directory.
	 *
	 * @param OutCopiedSkills   Number of top-level skill folders successfully copied.
	 * @param bOverwriteExisting If true, existing files in the destination are overwritten.
	 * @return True if at least one skill was copied and no copy failed.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Skills")
	static bool CopyPluginSkillsToClaude(int32& OutCopiedSkills, bool bOverwriteExisting = true);

	/** Absolute path to the plugin's shipped skills folder (Resources/Skills). */
	UFUNCTION(BlueprintPure, Category = "ACF|Skills")
	static FString GetPluginSkillsSourceDir();

	/** Absolute path to the project's Claude skills folder (.claude/skills). */
	UFUNCTION(BlueprintPure, Category = "ACF|Skills")
	static FString GetProjectClaudeSkillsDir();
};
