#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaUIBridgeSubsystem.generated.h"

class UMelodiaNarrativeSubsystem;
class UMelodiaExternalJRPGBridgeSubsystem;
class UMelodiaBattleKeyboardLegendWidget;
class UMelodiaBattleResultsWidget;
class UMelodiaBattleSession;
class UUserWidget;

// Underlying-type enums used by the reflected handlers below; complete
// definitions live in the MelodiaCore plugin (MelodiaBattleTypes.h).
enum class EMelodiaEncounterResult : uint8;
enum class EMelodiaBattlePhase : uint8;

/**
 * Creates and manages Melodia UI widgets on top of the stock JRPG UI.
 *
 * Melodia widgets are created into generic UUserWidget variables so there are
 * NO type compatibility issues with stock BP_BattleUI_C typed variables.
 * The stock UI still renders underneath (invisible if hidden); Melodia UI is
 * the visible overlay.
 *
 * Listens to native C++ events -- no modifications to stock Blueprints needed.
 */
UCLASS()
class BS_GODFILE_API UMelodiaUIBridgeSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UMelodiaUIBridgeSubsystem();

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category = "Melodia|UI|Bridge", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaUIBridgeSubsystem* Get(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge")
	UUserWidget* CreateMelodiaBattleUI(TSubclassOf<UUserWidget> MelodiaWidgetClass);

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge")
	void DestroyMelodiaBattleUI();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge")
	void ShowMelodiaBattleUI();

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge")
	void HideMelodiaBattleUI();

	/**
	 * Forward a completed rhythm verdict to BP_MelodiaBattleUI's ShowRhythmGrade
	 * event, if the widget exists and implements it.
	 *
	 * ShowRhythmGrade is authored in Blueprint, so it is invoked reflectively --
	 * the same idiom UMelodiaExternalJRPGBridgeSubsystem uses to call stock JRPG
	 * template functions. Monolith cannot script a Blueprint delegate bind (it has
	 * no CreateDelegate node type), so driving the widget from C++ is what makes
	 * this reachable at all without hand-authoring the graph.
	 *
	 * Returns false, with a log line naming the expected signature, when the event
	 * is absent or its parameters do not match. It never guesses at a signature --
	 * a silent mismatch here would look wired while displaying nothing, which is
	 * the exact failure this project has been bitten by repeatedly.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge")
	bool ShowRhythmGradeOnBattleUI(const FString& GradeText, int32 HitCount, int32 MissCount);

	/**
	 * Write the stock BP_BattleUI widget's `battleController` reference from C++.
	 *
	 * That property has four readers in BP_BattleUI's EventGraph and ZERO writers
	 * anywhere -- not in the widget, not in its BP_MelodiaBattleUI child, not in
	 * BP_BattleController. So it is permanently null at runtime, every Branch that
	 * reads it takes the wrong leg, and target selection never resolves. That is
	 * the root of the "Accessed None ... property battleController" cascade.
	 *
	 * Doing it here rather than by hand in the graph is the whole point: Monolith
	 * cannot author a cross-object VariableSet (it produces an unbound `Set` node
	 * with no target pin), so the Blueprint fix is manual and therefore easy to
	 * lose to any future re-author. This is a single reflective write against
	 * names the stock template already owns.
	 *
	 * Idempotent, and verifies by reading the value back -- a set that did not
	 * take is reported as a failure rather than assumed. Returns false with a
	 * named log line for every distinguishable cause, including the ordinary one
	 * where the stock widget simply has not been created yet.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge")
	bool EnsureStockBattleUIControllerReference();

	UFUNCTION(BlueprintPure, Category = "Melodia|UI|Bridge")
	bool IsMelodiaUIActive() const { return MelodiaBattleWidget.Get() != nullptr; }

	UFUNCTION(BlueprintPure, Category = "Melodia|UI|Bridge")
	bool IsMelodiaUIVisible() const;

	/** Widget class path for auto-created battle UI. Override in defaults or per-project config. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|UI|Bridge|Config")
	FSoftClassPath MelodiaBattleWidgetPath;

	/** Widget class path for the persistent live-results widget shown even outside battle. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|UI|Bridge|Config")
	FSoftClassPath LiveResultsWidgetPath;

private:
	UFUNCTION()
	void HandleBattleRequested(FName EncounterId);
	UFUNCTION()
	void HandleBattleCompleted(FName EncounterId, EMelodiaBattleResult Result);
	UFUNCTION()
	void HandleBattleAborted(FName EncounterId, FString Reason);
	UFUNCTION()
	void HandleExternalBattleStarted(FName EncounterId);
	UFUNCTION()
	void HandleExternalBattleEnded(uint8 BattleResult);
	void RemoveStockDefeatDialogueWidgets();
	UFUNCTION()
	void HandleNarrativeFlagChanged(FName FlagId, bool bValue);
	UFUNCTION()
	void HandleQuestStateCommitted(FName QuestId, bool bCompleted);
	UFUNCTION()
	void HandleBattleSessionEnded(EMelodiaEncounterResult Result);
	UFUNCTION()
	void HandleBattlePhaseChanged(EMelodiaBattlePhase NewPhase, EMelodiaBattlePhase PreviousPhase);

	void CreateBattleUIInternal();
	void RemoveBattleUIInternal();
	void CreateBattlePresentationOverlaysInternal();
	void RemoveBattlePresentationOverlaysInternal();
	void CreateLiveResultsWidgetInternal();
	void PushLiveGameDataToActiveWidgets();
	void LinkMelodiaWidgetsToBattleController();

public:
	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge")
	void LinkWidgetsToBattleControllerPublic() { LinkMelodiaWidgetsToBattleController(); }

private:
	/** Next-tick trampoline: the stock widget is built during InitBattle, after the battle-started broadcast. */
	void EnsureStockBattleUIControllerReferenceDeferred();

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaNarrativeSubsystem> NarrativeSubsystem;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaBattleSession> BattleSession;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaExternalJRPGBridgeSubsystem> ExternalBridge;

	UPROPERTY(Transient)
	TObjectPtr<UUserWidget> MelodiaBattleWidget;

	/** Persistent results surface fed by battle/narrative events; survives battle teardown. */
	UPROPERTY(Transient)
	TObjectPtr<UMelodiaBattleResultsWidget> LiveResultsWidget;

	/**
	 * All battle-time Melodia widgets are owned by this subsystem. Keeping the
	 * prompt and keyboard legend beside the main battle widget prevents a second
	 * GameInstance subsystem from adding competing viewport widgets on the same
	 * narrative event.
	 */
	UPROPERTY(Transient)
	TObjectPtr<UUserWidget> RhythmPrompt;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaBattleKeyboardLegendWidget> KeyboardLegend;

	FTimerHandle StockDefeatCleanupTimer;
	int32 StockDefeatCleanupTicksRemaining = 0;
};
