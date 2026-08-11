#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 21: Horror Advanced — Encounter Design Actions (8 actions)
 * High-level horror intelligence composing all existing analysis into
 * encounter design, patrol routing, territory analysis, safe room evaluation,
 * pacing structure, scare sequences, intensity validation, and hospice reports.
 *
 * Dependencies: Phase 6 (horror analysis), Phase 15 (horror design),
 *               Phase 7 (lighting), Phase 8 (acoustics), Phase 9 (accessibility)
 */
class FMonolithMeshEncounterActions
{
public:
	/** Register all 8 encounter/horror-advanced actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	/** Capstone: compose spawn + patrol + sightlines + audio into scored encounter spec */
	static FMonolithActionResult DesignEncounter(const TSharedPtr<FJsonObject>& Params);

	/** Generate navmesh patrol routes per AI archetype (stalker/patrol/ambusher) */
	static FMonolithActionResult SuggestPatrolRoute(const TSharedPtr<FJsonObject>& Params);

	/** Score a region as AI territory: hiding, patrol, ambush, sightline control */
	static FMonolithActionResult AnalyzeAiTerritory(const TSharedPtr<FJsonObject>& Params);

	/** Score a room as a safe room: entrances, lighting, sound isolation, defensibility */
	static FMonolithActionResult EvaluateSafeRoom(const TSharedPtr<FJsonObject>& Params);

	/** Macro-level tension mapping: encounter zones, safe rooms, pacing rhythm */
	static FMonolithActionResult AnalyzeLevelPacingStructure(const TSharedPtr<FJsonObject>& Params);

	/** Procedurally generate scare event sequence with variety, escalation, pacing */
	static FMonolithActionResult GenerateScareSequence(const TSharedPtr<FJsonObject>& Params);

	/** Validate horror intensity caps for hospice mode */
	static FMonolithActionResult ValidateHorrorIntensity(const TSharedPtr<FJsonObject>& Params);

	/** Full hospice accessibility + horror audit: intensity, rest, cognitive load, input demands */
	static FMonolithActionResult GenerateHospiceReport(const TSharedPtr<FJsonObject>& Params);
};
