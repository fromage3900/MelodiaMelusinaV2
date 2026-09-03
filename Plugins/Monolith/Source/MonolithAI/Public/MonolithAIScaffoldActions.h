#pragma once

#include "MonolithAIInternal.h"

class FMonolithAIScaffoldActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// 180b. hello_world_ai — ONE-CALL onboarding demo
	static FMonolithActionResult HandleHelloWorldAI(const TSharedPtr<FJsonObject>& Params);

	// 181. scaffold_complete_ai_character — Full AI character stack
	static FMonolithActionResult HandleScaffoldCompleteAICharacter(const TSharedPtr<FJsonObject>& Params);

	// 182. scaffold_perception_to_blackboard — Perception→BB bridge
	static FMonolithActionResult HandleScaffoldPerceptionToBlackboard(const TSharedPtr<FJsonObject>& Params);

	// 184. scaffold_team_system — Team IDs + attitude solver
	static FMonolithActionResult HandleScaffoldTeamSystem(const TSharedPtr<FJsonObject>& Params);

	// 185. scaffold_patrol_investigate_ai — Guard AI
	static FMonolithActionResult HandleScaffoldPatrolInvestigateAI(const TSharedPtr<FJsonObject>& Params);

	// 186. scaffold_enemy_ai — Basic enemy with chase+attack
	static FMonolithActionResult HandleScaffoldEnemyAI(const TSharedPtr<FJsonObject>& Params);

	// 198. scaffold_eqs_move_sequence — RunEQS→MoveTo convenience
	static FMonolithActionResult HandleScaffoldEQSMoveSequence(const TSharedPtr<FJsonObject>& Params);

	// 199. create_bt_from_template — BT templates
	static FMonolithActionResult HandleCreateBTFromTemplate(const TSharedPtr<FJsonObject>& Params);

	// 200. create_st_from_template — ST templates
	static FMonolithActionResult HandleCreateSTFromTemplate(const TSharedPtr<FJsonObject>& Params);

	// 206. batch_validate_ai_assets — Run all validators
	static FMonolithActionResult HandleBatchValidateAIAssets(const TSharedPtr<FJsonObject>& Params);

	// 107. validate_ai_controller — Check controller setup
	static FMonolithActionResult HandleValidateAIController(const TSharedPtr<FJsonObject>& Params);

	// 106. scaffold_ai_controller_blueprint — Full controller setup
	static FMonolithActionResult HandleScaffoldAIControllerBlueprint(const TSharedPtr<FJsonObject>& Params);

	// Genre scaffolds (Task 7)
	static FMonolithActionResult HandleScaffoldCompanionAI(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldBossAI(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldAmbientNPC(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldHorrorStalker(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldHorrorAmbush(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldHorrorPresence(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldHorrorMimic(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldStealthGameAI(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldTurretAI(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldGroupCoordinator(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldFlyingAI(const TSharedPtr<FJsonObject>& Params);

	// ── Internal Helpers ──

	/** Dispatch to a lower-level Monolith action and return the result */
	static FMonolithActionResult Dispatch(const FString& Namespace, const FString& Action, const TSharedPtr<FJsonObject>& Params);

	/** Dispatch and check success, appending error to warnings if it fails */
	static bool DispatchOrWarn(const FString& Namespace, const FString& Action,
		const TSharedPtr<FJsonObject>& Params, TArray<FString>& Warnings, FString StepName);

	/** Build a BT spec JSON for a named template */
	static TSharedPtr<FJsonObject> BuildBTTemplateSpec(const FString& TemplateName, const FString& BBPath);

	/** Build blackboard keys array for a given template */
	static TArray<TSharedPtr<FJsonValue>> BuildBBKeysForTemplate(const FString& TemplateName);
};
