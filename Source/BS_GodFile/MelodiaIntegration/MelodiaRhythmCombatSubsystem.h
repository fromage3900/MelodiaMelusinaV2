#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MelodiaRhythmCombatTypes.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaRhythmCombatSubsystem.generated.h"

class UMelodiaRhythmSkillDefinition;
class UMelodiaTokenWalletSubsystem;

/**
 * Broadcast once per session when FinishSession accepts the aggregate result.
 * Blueprint binds this to drive the stock resolver hookup and to tear the
 * rhythm HUD down; it fires exactly once per session.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FMelodiaRhythmSessionCompleted,
	EMelodiaSkillGrade, Grade, int32, HitCount, int32, MissCount);

/**
 * The universal battle-scoped rhythm combat authority.
 *
 * This is the single place the rhythm layer produces a combat-affecting
 * request. It owns a data-driven skill catalog (UMelodiaRhythmSkillDefinition
 * rows), starts a session per skill, accepts exactly one authoritative result,
 * validates it (rejects duplicate session IDs), converts it into a typed
 * FMelodiaRhythmEffectRequest, and exposes it to the stock resolver.
 *
 * AUTHORITY (Decisions 009/011/012, MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING):
 * this subsystem never applies damage, healing, SP, statuses, speed, turns,
 * victory, defeat, or save mutations. It only produces a request for the stock
 * resolver. It never bypasses the stock resolver.
 *
 * It does own the ORDERING of the stock skill invocation (UseSkillWithRhythm):
 * it already owns the moment a session starts, every path by which one ends, and
 * the damage latch the montage reads, so it is the only class that can sequence
 * the two without mirroring session lifetime somewhere else. Ordering is not
 * application -- the stock UseSkill still applies everything.
 *
 * CLOCK OWNER: this subsystem does NOT own a clock. It reads musical time from
 * UMelodiaMusicClockSubsystem -- the project's single universal metronome /
 * musical influence source (Decision 012/015). Harmonix is preferred, Quartz is
 * the fallback, and the subsystem degrades when no clock is running.
 *
 * WALLET INTEGRATION: rhythm skills may spend mana (TrySpendMana) and grant
 * shards (TryGrantShards) as rewards, following the same OnWalletChanged -> UI
 * pattern as UMelodiaTokenWalletSubsystem. No second wallet is created.
 */
UCLASS()
class BS_GODFILE_API UMelodiaRhythmCombatSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	// --- FTickableGameObject (via UTickableWorldSubsystem) --------------------
	// Ticks only while a session is live: advances the session beat, expires unhit
	// notes, pushes the visible note window to the HUD, and closes the session once
	// SessionBeat passes the skill's authored window.
	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickable() const override { return bSessionActive; }
	virtual TStatId GetStatId() const override
	{
		RETURN_QUICK_DECLARE_CYCLE_STAT(UMelodiaRhythmCombatSubsystem, STATGROUP_Tickables);
	}

	/**
	 * Bind the HUD this subsystem should drive. Held weakly -- the HUD is owned by
	 * the widget tree and may be torn down independently of the session.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	void BindRhythmHUD(UMelodiaRhythmHUDWidget* InHUD);

	/** Project-wide accessor, matching UMelodiaMusicClockSubsystem::Get. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaRhythmCombatSubsystem* Get(const UObject* WorldContextObject);

	/** Register a skill definition into the catalog. Call once per skill at startup. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	void RegisterSkill(UMelodiaRhythmSkillDefinition* InSkill);

	/** Look up a registered skill definition by ID. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	UMelodiaRhythmSkillDefinition* FindSkill(FName SkillId) const;

	/**
	 * Start a new authoritative rhythm session for the given skill.
	 * Returns a unique session ID, or 0 if the skill is not registered.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	int32 StartSession(FName SkillId);

	/**
	 * Submit the single authoritative result for the active session.
	 * Returns true if accepted and converted into a pending effect request.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	bool SubmitResult(const FMelodiaAuthoritativeRhythmResult& InResult);

	/**
	 * Bridge: submit a graded input (from UMelodiaJRPGPresentationRhythmComponent
	 * or any timing grader) for the active session. Builds the authoritative
	 * result from the grade and the active skill, then validates it exactly like
	 * SubmitResult. Returns true if accepted.
	 *
	 * This is the seam that makes the presentation layer feed the authoritative
	 * rhythm combat layer without the presentation layer ever computing damage.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	bool SubmitRatedInput(EMelodiaSkillGrade Grade, int32 HitCount, int32 MissCount);

	/** True when a validated, unconsumed effect request is pending. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	bool HasPendingRequest() const;

	/** Pop the pending effect request for the stock resolver to consume. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	bool ConsumePendingRequest(FMelodiaRhythmEffectRequest& OutRequest);

	/**
	 * Grade one lane press against the music clock and accumulate it into the
	 * active session. Returns the grade for immediate presentation feedback.
	 *
	 * LaneIndex is presentation-only (which lane lit up); it does not affect
	 * grading. Timing comes from UMelodiaMusicClockSubsystem's error-to-nearest-
	 * beat, graded through the same UMelodiaCoreRulesLibrary windows the
	 * presentation component uses -- there is no second grading rule.
	 *
	 * Returns Miss with no accumulation when there is no active session, so a
	 * stray keypress outside a session can never bank a hit.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	EMelodiaSkillGrade RegisterLaneHit(int32 LaneIndex);

	/**
	 * Close the active session: derive the aggregate grade from the accumulated
	 * hits/misses, feed it through the existing SubmitRatedInput validation path,
	 * and broadcast OnRhythmComplete. Returns true if the result was accepted.
	 *
	 * This adds no second authority -- it is a wrapper that computes the grade
	 * and delegates to SubmitRatedInput, which remains the only path that builds
	 * a pending effect request.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	bool FinishSession();

	/** Hits banked so far in the active session. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	int32 GetSessionHitCount() const { return SessionHitCount; }

	/** Misses banked so far in the active session. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	int32 GetSessionMissCount() const { return SessionMissCount; }

	/** Fires once when a session completes. */
	UPROPERTY(BlueprintAssignable, Category = "Melodia|Rhythm Combat")
	FMelodiaRhythmSessionCompleted OnRhythmComplete;

	/**
	 * Invalidate the active session and any pending request.
	 *
	 * Does not touch PendingDamageMultiplier: that is a finished session's output,
	 * and this runs on battle-end / save-recovery / HUD-hide paths where the
	 * damage notify may not have read it yet. StartSession and
	 * ClearPendingDamageMultiplier are the only things that reset it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	void InvalidateSession();

	/** The active session ID, or 0 if none. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	int32 GetActiveSessionId() const { return ActiveSessionId; }

	/**
	 * Effective magnitude the last accepted rhythm result produced
	 * (BaseMagnitude * RhythmScalar), or 1.0 when nothing is pending.
	 *
	 * WHY POLLING: the damage anim-notify is an async callback raised by the
	 * montage on its own call stack. Nothing connects it to the exec chain that
	 * started the skill, so there is no pin to feed the scalar down -- that is
	 * true regardless of which side fires first. A Blueprint reads the value here
	 * at notify time instead: no delegate plumbing, no mirrored Blueprint
	 * variable to drift.
	 *
	 * ORDERING (measured from the montage + skill assets, not assumed): the
	 * notify fires EARLY, not late. All four template attack montages are
	 * 1.2999833s long with their damage notify at 0.500-0.516s, while a Cadence
	 * Strike session runs ~3.05s (TempoBPM 128 -> 0.46875 s/beat; IntroBeats 2 +
	 * ActiveBeats 4 = 6 beats, + 0.5 ExpiryGraceBeats). The notify therefore
	 * lands roughly 2.5s BEFORE FinishSession latches the scalar. So whenever the
	 * montage is fired in parallel with the session, this reads identity and the
	 * hit is unscaled; sequencing UseSkill behind the OnRhythmComplete broadcast
	 * is what makes the latch exist in time to be read. See
	 * Docs/Handoffs/INTEGRATION_POLISH_HANDOFFS_2026-08-06.md, Lane D.
	 *
	 * Returns 1.0 (identity) rather than 0 so an unscaled hit is never zeroed.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	float GetPendingDamageMultiplier() const { return PendingDamageMultiplier; }

	/** Reset to identity once the damage it scaled has been applied. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	void ClearPendingDamageMultiplier() { PendingDamageMultiplier = 1.0f; }

	/** True while a session is live -- lets Blueprint gate on rhythm without polling the id. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	bool IsSessionActive() const { return bSessionActive; }

	/**
	 * Player-facing label for a grade (PERFECT / GREAT / GOOD / MISS).
	 *
	 * Public and static so every surface that shows a grade -- the highway HUD, the
	 * Melodia battle overlay, Blueprint -- reads the same words from one place. A
	 * second copy of this mapping is how two UIs end up disagreeing about the same
	 * result.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	static FText GradeToText(EMelodiaSkillGrade Grade);

	/**
	 * Resolve a stock battle-skill object to its rhythm SkillId via
	 * UMelodiaIntegrationConfig::StockSkillRhythmIds, or NAME_None when the skill
	 * has no rhythm minigame.
	 *
	 * Blueprint feeds the result straight into StartSession, which already returns
	 * 0 for NAME_None -- so an unmapped skill falls through to stock with no branch.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	FName ResolveRhythmSkillId(const UObject* StockSkill) const;

	/**
	 * Single entry point for "use this stock skill, with its rhythm minigame if it
	 * has one". Replaces the StartSession -> Branch -> UseSkill cluster in
	 * BP_BattleController, which fired UseSkill on BOTH branch outputs and so ran
	 * the montage in parallel with the session -- the damage notify lands ~0.51s
	 * in, the session latches at ~3.05s, so every rhythm-scaled hit was landing
	 * unscaled. See GetPendingDamageMultiplier for the measurement.
	 *
	 * Unmapped / unregistered skill (StartSession returns 0): UseSkill is invoked
	 * on this call stack, same frame, no deferral and no added latency -- the
	 * no-rhythm path is unchanged.
	 *
	 * Rhythm skill: the skill object is held and UseSkill is invoked from
	 * FinishSession, immediately after PendingDamageMultiplier is latched and
	 * OnRhythmComplete has been broadcast. The montage therefore starts after the
	 * scalar exists, so the notify reads a real multiplier.
	 *
	 * Returns true when the call was deferred, false when it went straight
	 * through. Callers do not branch on it; it exists for logging and tests.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	bool UseSkillWithRhythm(UObject* StockSkill);

	/** The skill object whose UseSkill is deferred, or null. Read-only for tests. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm Combat")
	UObject* GetDeferredSkill() const { return DeferredSkill; }

	/**
	 * Latch the song chart index a quantum draw chose for this skill.
	 *
	 * The latch is per skill, cleared each battle by ClearSongSelections. The
	 * service draw is async and may land after the first StartSession of a
	 * battle; a session that starts before the draw lands plays the first
	 * authored chart, exactly the classical fallback when the service is down.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	void SetSongSelectionIndex(FName SkillId, int32 SongIndex);

	/** Clear every skill's drawn chart index (battle boundary). */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm Combat")
	void ClearSongSelections();

	/** Read-only access to the skill catalog (draw subsystem, tests). */
	const TMap<FName, TObjectPtr<UMelodiaRhythmSkillDefinition>>& GetSkillCatalog() const { return SkillCatalog; }

private:
	/**
	 * Reflected invocation of the stock BP_BattleSkillBase UseSkill, following the
	 * same FindFunction/ProcessEvent pattern UMelodiaExternalJRPGBridgeSubsystem
	 * uses for the stock StartBattle. UseSkill takes no parameters beyond self, so
	 * a zero-size parameter block is passed; a signature that grew parameters is a
	 * hard error rather than a silently defaulted call.
	 */
	static void InvokeStockUseSkill(UObject* StockSkill);

	/**
	 * The pending deferral. This pointer IS the guard: it is cleared before
	 * dispatch, so a session that both completes and is invalidated can only fire
	 * UseSkill once. A deferral has exactly two exits -- fired by FinishSession,
	 * or dropped by InvalidateSession/Deinitialize. There is no timeout, because
	 * every session that stays active in a live world self-closes: StartSession
	 * always sets SessionEndBeat, IsTickable() follows bSessionActive, and Tick
	 * calls FinishSession once SessionBeat passes it. The only exits that skip
	 * FinishSession are deliberate teardown (save recovery, battle end, HUD hide,
	 * a superseding StartSession, world Deinitialize) where no turn survives to
	 * be stranded.
	 */
	UPROPERTY(Transient)
	TObjectPtr<UObject> DeferredSkill;

	/** Build the typed effect request from a validated result and the skill definition. */
	FMelodiaRhythmEffectRequest BuildEffectRequest(const UMelodiaRhythmSkillDefinition* Skill, const FMelodiaAuthoritativeRhythmResult& InResult) const;

	/** Resolve the effect's magnitude from the skill's grade multipliers. */
	float ResolveMagnitude(const UMelodiaRhythmSkillDefinition* Skill, EMelodiaSkillGrade Grade) const;

	/** Apply any wallet integration (SP cost / shard reward) for the consumed request. */
	void ApplyWalletIntegration(const FMelodiaRhythmEffectRequest& Request);

	/** Clear the per-session lane accumulators and chart state. */
	void ResetSessionAccumulators();

	/**
	 * Resolve the skill's PatternAsset into a session-relative note list.
	 *
	 * Notes are rebased so TargetBeat 0 == the moment the session started, then
	 * clipped to IntroBeats + ActiveBeats. The chart is therefore a per-skill
	 * PATTERN, not a song-position sync: FMelodiaMusicTime::TotalBeats (absolute
	 * song position) is Harmonix-only and reads 0 under the Quartz fallback, so
	 * anything song-locked would silently collapse to beat 0 on the live clock.
	 *
	 * Returns false when the skill has no usable chart -- the caller then falls
	 * back to beat-proximity grading.
	 */
	bool LoadChartForSkill(const UMelodiaRhythmSkillDefinition* Skill);

	/** Push the current visible note window and beat position to the bound HUD. */
	void PushHighwayToHUD(bool bActive);

	/** Timing windows for lane grading -- the same rules the presentation component uses. */
	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm Combat")
	FMelodiaRhythmWindows RhythmWindows;

	/** How far ahead of the hit line notes are drawn. Mirrors the execution component's default. */
	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm Combat")
	float ScrollBeatsAhead = 2.5f;

	/**
	 * A note is expired (auto-Miss) once the session beat passes its TargetBeat by
	 * more than this. Derived from the widest grading window so a note can never
	 * expire while it is still legally hittable.
	 */
	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm Combat")
	float ExpiryGraceBeats = 0.5f;

	UPROPERTY(Transient)
	TWeakObjectPtr<UMelodiaRhythmHUDWidget> BoundHUD;

	/** Session-relative chart. TargetBeat 0 == session start. Empty when uncharted. */
	TArray<FMelodiaHighwayNote> SessionNotes;

	/**
	 * Handoff latch, NOT session-accumulator state: it is an output of a session
	 * that has already finished. Written by FinishSession, cleared by the
	 * consumer (ClearPendingDamageMultiplier, called after DealDamage) or by
	 * StartSession, which resets it directly so a fresh session always begins at
	 * identity. Deliberately not reset by ResetSessionAccumulators -- that would
	 * put it inside InvalidateSession, which fires on battle-end and save-recovery
	 * paths and would wipe a latch the damage notify has not read yet.
	 */
	float PendingDamageMultiplier = 1.0f;

	bool bSessionActive = false;
	bool bSessionCharted = false;
	float SessionBeat = 0.0f;
	float SessionSecondsPerBeat = 0.46875f; // 128 BPM fallback
	float SessionEndBeat = 0.0f;

	int32 SessionHitCount = 0;
	int32 SessionMissCount = 0;

	/** Sum of per-press grade values, used to derive the aggregate grade on finish. */
	int32 SessionGradeTotal = 0;

	UPROPERTY()
	TMap<FName, TObjectPtr<UMelodiaRhythmSkillDefinition>> SkillCatalog;

	/**
	 * Song chart index per skill, latched by the quantum draw subsystem before
	 * the session starts. Empty map = play the first authored chart.
	 */
	UPROPERTY(Transient)
	TMap<FName, int32> SongSelectionIndices;

	FName ActiveSkillId = NAME_None;
	int32 ActiveSessionId = 0;
	int32 NextSessionId = 1;
	bool bResultAccepted = false;
	bool bHasPendingRequest = false;
	FMelodiaRhythmEffectRequest PendingRequest;
};