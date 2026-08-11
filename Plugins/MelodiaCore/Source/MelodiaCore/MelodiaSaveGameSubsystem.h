#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaSaveGameSubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaOnSaveCompleted, bool, bSuccess);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaOnLoadCompleted, bool, bSuccess);

/** Lightweight per-slot metadata for the Save/Load UI to display without keeping
 * a fully-restored save around. Fields mirror the headline UMelodiaSaveGame
 * fields the Figma Save/Load panel needs (occupied state, map, active party
 * member, save time). Populated by peeking the slot, not by restoring state. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaSaveSlotSummary
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	int32 SlotIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	bool bOccupied = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	FString CurrentMapName;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	int32 ActivePartyIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	EMelodiaOpeningPhase OpeningPhase = EMelodiaOpeningPhase::NotStarted;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Save")
	FDateTime Timestamp;
};

/** Owns the narrow profile save (opening-flow phase + persistent party stats).
 * Async save/load per project convention (writes at deliberate checkpoints, not
 * every frame/combat beat). Does not own or persist any roguelike run/recipe
 * state - that belongs to the run subsystem's own persistence layer.
 *
 * Slotting: slot 0 keeps the legacy slot name ("MelusinaSlot0") so existing
 * saves stay valid; higher indices append their index ("MelusinaSlot1", ...).
 * The parameterless SaveGame/LoadGame/HasSaveGame forward to slot 0 unchanged. */
// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (second save authority). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API UMelodiaSaveGameSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Number of enumerable save slots surfaced to the UI (design: 3-4 cards). */
	static constexpr int32 NumSaveSlots = 4;

	UFUNCTION(BlueprintPure, Category="Melodia|Save", meta=(WorldContext="WorldContextObject"))
	static UMelodiaSaveGameSubsystem* Get(const UObject* WorldContextObject);

	/** Gathers state from UMelodiaOpeningFlowSubsystem + UMelodiaBattleSession and async-writes it to slot 0. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save")
	void SaveGame();

	/** Async-loads slot 0, then restores state into the two subsystems via their
	 * dedicated Restore* methods. Call after the destination level's BeginPlay pass
	 * has already run (see UMelodiaOpeningFlowSubsystem::RestoreFromSave comment)
	 * to avoid racing AMelodiaSirMelodiousIntroActor::BeginPlay's BeginMorning() call. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save")
	void LoadGame();

	UFUNCTION(BlueprintPure, Category="Melodia|Save")
	bool HasSaveGame() const;

	/** Gathers current state and async-writes it to the given slot index. Slot 0
	 * behaves identically to SaveGame(). Broadcasts OnSaveCompleted when done. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save")
	void SaveToSlot(int32 SlotIndex);

	/** Async-loads the given slot index and restores state (same semantics as
	 * LoadGame()). Broadcasts OnLoadCompleted when done. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save")
	void LoadFromSlot(int32 SlotIndex);

	UFUNCTION(BlueprintPure, Category="Melodia|Save")
	bool HasSaveInSlot(int32 SlotIndex) const;

	/** Deletes the save in the given slot, if any. Returns true when a save was removed. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save")
	bool DeleteSlot(int32 SlotIndex);

	/** Peeks a single slot's headline metadata for the UI. Loads the slot to read
	 * its fields (there is no lighter header), so call on menu open, not per frame.
	 * An empty slot returns a summary with bOccupied=false. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save")
	FMelodiaSaveSlotSummary GetSaveSlotSummary(int32 SlotIndex) const;

	/** Peeks every enumerable slot (0..NumSaveSlots-1) and returns one summary each,
	 * in slot order, so the Save/Load panel can render the full card list at once. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save")
	TArray<FMelodiaSaveSlotSummary> GetAllSaveSlotSummaries() const;

	/** Runtime-readable accessibility/perf motion-amplitude gate that every WBP_Sparkle instance
	 * reads at construct time. Captured into the save on SaveToSlot, restored on load. */
	UFUNCTION(BlueprintPure, Category="Melodia|Save|Settings")
	EMelodiaMotionTier GetMotionTier() const { return CurrentMotionTier; }

	UFUNCTION(BlueprintCallable, Category="Melodia|Save|Settings")
	void SetMotionTier(EMelodiaMotionTier NewTier) { CurrentMotionTier = NewTier; }

	UPROPERTY(BlueprintAssignable, Category="Melodia|Save")
	FMelodiaOnSaveCompleted OnSaveCompleted;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Save")
	FMelodiaOnLoadCompleted OnLoadCompleted;

private:
	void HandleAsyncSaveComplete(const FString& SlotName, int32 InUserIndex, bool bSuccess);
	void HandleAsyncLoadComplete(const FString& SlotName, int32 InUserIndex, class USaveGame* LoadedSave);

	EMelodiaMotionTier CurrentMotionTier = EMelodiaMotionTier::Full;

	/** Slot 0 keeps the legacy name for back-compat; higher indices append the index. */
	static FString SlotNameForIndex(int32 SlotIndex) { return SlotIndex <= 0 ? TEXT("MelusinaSlot0") : FString::Printf(TEXT("MelusinaSlot%d"), SlotIndex); }
	static FString SlotName() { return SlotNameForIndex(0); }
	static int32 UserIndex() { return 0; }
};
