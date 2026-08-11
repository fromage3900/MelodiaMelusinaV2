#pragma once

#include "MonolithAIInternal.h"

class USCS_Node;

class FMonolithAIPerceptionActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	// Public helpers (used by anonymous-namespace helper in .cpp)

	/** Find the UAIPerceptionComponent SCS node on a Blueprint */
	static USCS_Node* FindPerceptionNode(UBlueprint* BP);

	/** Find a UAIPerceptionStimuliSourceComponent SCS node */
	static USCS_Node* FindStimuliSourceNode(UBlueprint* BP);

	/** Get the perception component template from an SCS node */
	static class UAIPerceptionComponent* GetPerceptionTemplate(USCS_Node* Node);

private:
	// 109. add_perception_component
	static FMonolithActionResult HandleAddPerceptionComponent(const TSharedPtr<FJsonObject>& Params);

	// 110. get_perception_config
	static FMonolithActionResult HandleGetPerceptionConfig(const TSharedPtr<FJsonObject>& Params);

	// 111. configure_sight_sense
	static FMonolithActionResult HandleConfigureSightSense(const TSharedPtr<FJsonObject>& Params);

	// 112. configure_hearing_sense
	static FMonolithActionResult HandleConfigureHearingSense(const TSharedPtr<FJsonObject>& Params);

	// 113. configure_damage_sense
	static FMonolithActionResult HandleConfigureDamageSense(const TSharedPtr<FJsonObject>& Params);

	// 114. configure_touch_sense
	static FMonolithActionResult HandleConfigureTouchSense(const TSharedPtr<FJsonObject>& Params);

	// 117. remove_sense
	static FMonolithActionResult HandleRemoveSense(const TSharedPtr<FJsonObject>& Params);

	// 118. add_stimuli_source_component
	static FMonolithActionResult HandleAddStimuliSourceComponent(const TSharedPtr<FJsonObject>& Params);

	// 119. configure_stimuli_source
	static FMonolithActionResult HandleConfigureStimuliSource(const TSharedPtr<FJsonObject>& Params);

	// 126. validate_perception_setup
	static FMonolithActionResult HandleValidatePerceptionSetup(const TSharedPtr<FJsonObject>& Params);

	// 218. get_ai_system_config
	static FMonolithActionResult HandleGetAISystemConfig(const TSharedPtr<FJsonObject>& Params);

	// ── Helpers ──

	/** Parse affiliation from JSON (object with enemies/neutrals/friendlies bools, or comma-separated string) */
	static void ParseAffiliation(const TSharedPtr<FJsonObject>& Params, const FString& FieldName,
		bool& bEnemies, bool& bNeutrals, bool& bFriendlies);

	/** Serialize affiliation filter to JSON */
	static TSharedPtr<FJsonObject> AffiliationToJson(const struct FAISenseAffiliationFilter& Filter);

	/** Find or create a sense config of the given class on a perception component template */
	template<typename TSenseConfig>
	static TSenseConfig* FindOrCreateSenseConfig(class UAIPerceptionComponent* PerceptionComp);

	/** Find a sense config of the given class */
	template<typename TSenseConfig>
	static TSenseConfig* FindSenseConfig(class UAIPerceptionComponent* PerceptionComp);

	/** Resolve sense type string to UAISenseConfig subclass */
	static UClass* ResolveSenseConfigClass(const FString& SenseType);

	/** Serialize a single sense config to JSON */
	static TSharedPtr<FJsonObject> SenseConfigToJson(class UAISenseConfig* SenseConfig);
};
