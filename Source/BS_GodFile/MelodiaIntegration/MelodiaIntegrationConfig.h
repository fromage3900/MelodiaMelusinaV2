#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaIntegrationConfig.generated.h"

UCLASS(BlueprintType)
class BS_GODFILE_API UMelodiaIntegrationConfig : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Allowlist")
	TSet<FName> EncounterIds;

	/** World-challenge identities accepted by the canonical completion adapter. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Allowlist")
	TSet<FName> WorldChallengeIds;

	/** Generic StateAnchor identities accepted by the canonical apply adapter. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Allowlist")
	TSet<FName> StateAnchorIds;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Allowlist")
	TSet<FName> QuestIds;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Allowlist")
	TSet<FName> NarrativeFlagIds;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Allowlist")
	TSet<FName> TravelLevelIds;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Allowlist")
	TSet<FName> DialogueRewardIds;

	/**
	 * Persona-lite social stats a dialogue choice may raise (Decision 018).
	 * Dialogue is the only source; combat, pickups and traversal must not grant
	 * stats. Name these musically -- Harmony, Tempo, Timbre -- and fix the IDs
	 * before content is authored, because they are persisted in the save record.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Allowlist")
	TSet<FName> SocialStatIds;

	/**
	 * Stock battle-skill class name -> rhythm SkillId.
	 *
	 * Key is the generated class FName exactly as it appears at runtime
	 * (e.g. "BP_FocusAttack_C"); value is one of the authored rhythm ids
	 * (cadence_strike, resonant_arc, lullaby_mend, downbeat_break,
	 * dissonant_silence, tempo_shift, crescendo_wave, harmony_shield).
	 *
	 * Explicit map rather than a name transform: the two id spaces are authored
	 * independently, so a string rule would mis-resolve the first time either side
	 * is renamed. A skill with no entry simply has no rhythm minigame -- StartSession
	 * returns 0 and the stock skill resolves normally.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Rhythm")
	TMap<FName, FName> StockSkillRhythmIds;

	/**
	 * Quantum draw service (python service.py): one POST per battle-start per
	 * song asset picks which authored chart plays. 'The library chooses your song.'
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quantum Draw")
	FString QuantumDrawServiceUrl = TEXT("http://127.0.0.1:8008/rank_layouts");

	/** Draw provider: classical-baseline | qsharp-simulator | qiskit-aer | chaos | swarm | pbit | entropy | cellular | commit-reveal | oracle */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quantum Draw")
	FString QuantumDrawProvider = TEXT("qsharp-simulator");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quantum Draw")
	bool bEnableQuantumDraw = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quantum Draw", meta = (ClampMin = "100"))
	int32 QuantumDrawTimeoutMs = 3000;

	/**
	 * If true, MelodiaOllamaValidation failures (unreachable daemon or malformed reply)
	 * will cause the intent to be rejected. If false, validation logs the error
	 * but allows the intent to proceed if it passes the allowlist.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Validation")
	bool bStrictAiValidation = false;

	/**
	 * If true, the subsystem will try to connect to background services (Ollama, VOICEVOX).
	 * If false, it will immediately use fallback/mock behavior without even trying to connect.
	 * This is useful for offline development or when working on unrelated features.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Validation")
	bool bEnableBackgroundServices = true;

	/**
	 * If true, unregistered IDs (Encounter, Quest, etc.) are allowed in non-shipping builds,
	 * but will trigger a warning log. This prevents "Allowlist Hell" during iteration.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Validation")
	bool bRelaxedAllowlistInEditor = true;

	/**
	 * IDs discovered during relaxed validation are added here temporarily (runtime only)
	 * to facilitate bulk-adding to the permanent sets.
	 */
	UPROPERTY(Transient, VisibleAnywhere, Category = "Validation|Debug")
	TSet<FName> DiscoveredUnregisteredIds;

	/**
	 * Additional world state to inject into the AI validation prompt.
	 * e.g., "PlayerLocation", "PartyHealth", "CurrentQuest".
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Validation")
	TMap<FString, FString> AiContextTemplates;
};
