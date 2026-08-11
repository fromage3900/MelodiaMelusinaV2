#pragma once

#include "MonolithAIInternal.h"

class FMonolithAIControllerActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleCreateAIController(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAIController(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListAIControllers(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAIControllerBT(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetPawnAIControllerClass(const TSharedPtr<FJsonObject>& Params);

	// 97. set_ai_controller_flags
	static FMonolithActionResult HandleSetAIControllerFlags(const TSharedPtr<FJsonObject>& Params);

	// 98. set_ai_team
	static FMonolithActionResult HandleSetAITeam(const TSharedPtr<FJsonObject>& Params);

	// 99. get_ai_team
	static FMonolithActionResult HandleGetAITeam(const TSharedPtr<FJsonObject>& Params);

	// 103. spawn_ai_actor
	static FMonolithActionResult HandleSpawnAIActor(const TSharedPtr<FJsonObject>& Params);

	// 104. get_ai_actors
	static FMonolithActionResult HandleGetAIActors(const TSharedPtr<FJsonObject>& Params);
};
