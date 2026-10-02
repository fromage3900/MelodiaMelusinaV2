// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ANSUITypes.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Input/CommonUIInputSettings.h"
#include "InputCoreTypes.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "ANSUINavigationTags.h"
#include "UITag.h"

#include "ANSUIPlayerSubsystem.generated.h"

class UUserWidget;
class UCommonUIInputSettings;
class UCommonActivatableWidget;
class UCommonActivatableWidgetStack;
class UCommonActivatableWidgetContainerBase;
class UAUTDeveloperSettings;
class UANSUIWidgetRegistryDataAsset;
class UANSWidgetInteractionComponent;
class UANSNavPageWidget;
class UWorld;

/**
 * Delegate for notifying when the focused navigation widget changes.
 *
 * @param focusedWidget The new widget that has received focus.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnFocusedWidgetChanged, UANSNavWidget*, focusedWidget);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnNotificationRequested, const FText&, Message, float, Duration);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnNavbarActionRequested, const FUIActionTag&, ActionTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnNavbarActionsRequested, const TArray<FUIActionTag>&, ActionTags);

/**
 * Player UI Subsystem for managing in-game UI widgets and input.
 *
 * This subsystem handles the spawning and removal of widgets on the local viewport,
 * navigation between UI widgets, retrieving input actions and icons, and more.
 */
UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSUIPlayerSubsystem : public UGameInstanceSubsystem {
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Spawns a widget and pushes it onto the specified UI layer stack.
	 *
	 * The widget is created and pushed onto the layer identified by LayerTag.
	 * If LayerTag is empty, the default layer is used. Optionally, the game can
	 * be paused and UI/game input can be locked while the widget is active.
	 *
	 * @param widgetClass The class of the widget to spawn.
	 * @param bPauseGame If true, the game will be paused when the widget is shown. Default is true.
	 * @param bLockGameInput If true, the game input will be locked while the widget is active. Default is true.
	 * @param LayerTag The UI layer to push onto (e.g. UI.Layer.Menu, UI.Layer.Modal). Empty = default layer.
	 * @return A pointer to the spawned UUserWidget instance.
	 */
	UFUNCTION(BlueprintCallable, meta = (DeterminesOutputType = "widgetClass", Categories = "UI.Layer"), Category = ANS)
	UUserWidget* SpawnInGameWidget(TSubclassOf<UUserWidget> widgetClass, bool bPauseGame = true, bool bLockGameInput = true, FGameplayTag LayerTag = FGameplayTag());

	/**
	 * Displays an already spawned widget and adds it to the local viewport.
	 *
	 * @param widgetRef The widget do be displayed, which must be a valid UUserWidget instance.
	 * @param bPauseGame If true, the game will be paused when the widget is shown. Default is true.
	 * @param bLockGameInput If true, the game input will be locked while the widget is active. Default is true.
	 * @return A pointer to the spawned UUserWidget instance.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void DisplayInGameWidget(UUserWidget* widgetRef, bool bPauseGame = true, bool bLockGameInput = true);

	/**
	 * Removes a widget from the local viewport.
	 *
	 * The specified widget is removed from the player's viewport. Optionally, UI input is unlocked
	 * and the game is unpaused.
	 *
	 * @param widget The widget instance to remove.
	 * @param bUnlockUIInput If true, UI/game input will be unlocked. Default is true.
	 * @param bRemovePause If true, the game pause state will be removed. Default is true.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void RemoveInGameWidget(UUserWidget* widget, bool bUnlockUIInput = true, bool bRemovePause = true);

	/**
	 * Navigates back to the previous widget in the widget stack.
	 *
	 * This function switches focus to the previously active widget.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void GoToPreviousWidget();

	/**
	 * Registers a CommonUI widget stack to receive pushed widgets.
	 * Call this from your HUD Blueprint (e.g. on BeginPlay) after adding
	 * a UCommonActivatableWidgetStack to your HUD widget tree.
	 * When set, SpawnInGameWidget and SpawnWidgetByTag will push onto
	 * this stack instead of calling AddToViewport directly.
	 *
	 * @param InStack The widget stack to use for push/pop operations.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS, meta = (DeprecatedFunction, DeprecationMessage = "Use RegisterLayer instead."))
	void SetWidgetStack(UCommonActivatableWidgetStack* InStack);

	/**
	 * Registers a UI layer identified by a GameplayTag.
	 * Call from your HUD Blueprint on Construct for each stack you placed.
	 * The first layer registered becomes the default layer used when no
	 * LayerTag is specified in SpawnInGameWidget.
	 *
	 * @param LayerTag GameplayTag that identifies this layer (e.g. UI.Layer.Menu, UI.Layer.Modal).
	 * @param LayerStack The widget stack for this layer.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS, meta = (Categories = "UI.Layer"))
	void RegisterLayer(FGameplayTag LayerTag, UCommonActivatableWidgetStack* LayerStack);

	/**
	 * Spawns a widget by tag (same as SpawnWidgetByTag) and immediately calls
	 * SetupWithActor on it if the widget is an ANSNavPageWidget.
	 * Use this from gameplay code (AGSAction, abilities, etc.) to open a page
	 * that needs a context actor (vendor, container, NPC…) without the gameplay
	 * layer holding a reference to any specific widget class.
	 *
	 * @param WidgetTag  Tag mapped to a widget config in the registry.
	 * @param Actor      The actor to pass to SetupWithActor on the spawned page.
	 * @return The spawned widget, or nullptr if the tag was not found.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	UCommonActivatableWidget* SpawnWidgetByTagWithActor(UPARAM(meta = (Categories = "UI.Widget")) FGameplayTag WidgetTag, AActor* Actor);

	/**
	 * Spawns a widget by tag (same as SpawnWidgetByTag) and immediately calls
	 * SetupWithComponent on it if the widget is an ANSNavPageWidget.
	 *
	 * @param WidgetTag   Tag mapped to a widget config in the registry.
	 * @param Component   The component to pass to SetupWithComponent on the spawned page.
	 * @return The spawned widget, or nullptr if the tag was not found.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	UCommonActivatableWidget* SpawnWidgetByTagWithComponent(UPARAM(meta = (Categories = "UI.Widget")) FGameplayTag WidgetTag, UActorComponent* Component);

	/**
	 * Spawns a widget by class and immediately calls SetupWithActor on it
	 * if the widget is an ANSNavPageWidget.
	 *
	 * @param WidgetClass    The widget class to spawn.
	 * @param Actor          The actor to pass to SetupWithActor.
	 * @param bPauseGame     Whether to pause the game while the widget is active.
	 * @param bLockGameInput Whether to switch to UI-only input while the widget is active.
	 * @param LayerTag       The UI layer to push onto. Empty = default layer.
	 * @return The spawned widget, or nullptr on failure.
	 */
	UFUNCTION(BlueprintCallable, meta = (DeterminesOutputType = "WidgetClass", Categories = "UI.Layer"), Category = ANS)
	UCommonActivatableWidget* SpawnWidgetByClassWithActor(TSubclassOf<UUserWidget> WidgetClass, AActor* Actor, bool bPauseGame = true, bool bLockGameInput = true, FGameplayTag LayerTag = FGameplayTag());

	/**
	 * Spawns a widget by class and immediately calls SetupWithComponent on it
	 * if the widget is an ANSNavPageWidget.
	 *
	 * @param WidgetClass    The widget class to spawn.
	 * @param Component      The component to pass to SetupWithComponent.
	 * @param bPauseGame     Whether to pause the game while the widget is active.
	 * @param bLockGameInput Whether to switch to UI-only input while the widget is active.
	 * @param LayerTag       The UI layer to push onto. Empty = default layer.
	 * @return The spawned widget, or nullptr on failure.
	 */
	UFUNCTION(BlueprintCallable, meta = (DeterminesOutputType = "WidgetClass", Categories = "UI.Layer"), Category = ANS)
	UCommonActivatableWidget* SpawnWidgetByClassWithComponent(TSubclassOf<UUserWidget> WidgetClass, UActorComponent* Component, bool bPauseGame = true, bool bLockGameInput = true, FGameplayTag LayerTag = FGameplayTag());

	/**
	 * Spawns a widget by looking up the GameplayTag in the Widget Registry
	 * Data Asset (configured in Project Settings > Ascent Navigation Settings).
	 * Layer, pause, and input-lock settings are all read from the registry entry —
	 * configure them per widget in the Data Asset, not at call sites.
	 *
	 * @param WidgetTag The tag mapped to a widget config in the registry.
	 * @return The spawned widget, or nullptr if the tag was not found.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	UCommonActivatableWidget* SpawnWidgetByTag(UPARAM(meta = (Categories = "UI.Widget")) FGameplayTag WidgetTag);

	/**
	 * Retrieves UI action tags associated with a specific key.
	 *
	 * This function queries the input settings and returns a list of UI action tags that are mapped to the provided key.
	 *
	 * @param key The key for which to retrieve action tags.
	 * @param outActionsTag An array that will be filled with the corresponding UI action tags.
	 * @return True if one or more action tags were found for the key; otherwise, false.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	bool TryGetActionsFromKey(const FKey& key, TArray<FUIActionTag>& outActionsTag);

	/**
	 * Retrieves keys mapped to a specific UI action.
	 *
	 * This function queries the input settings to obtain a list of keys associated with the given UI action tag.
	 *
	 * @param UIAction The UI action tag to query.
	 * @param outKeys An array that will be filled with the corresponding keys.
	 * @return True if one or more keys were found for the action; otherwise, false.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	bool TryGetKeysForAction(const FUIActionTag& UIAction, TArray<FKey>& outKeys);

	/**
	 * Retrieves an icon associated with a gameplay tag.
	 *
	 * This function returns the texture representing the icon for the specified gameplay tag.
	 *
	 * @param iconTag The gameplay tag used to identify the icon.
	 * @return A pointer to the UTexture2D representing the icon, or nullptr if not found.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	UTexture2D* GetIconByTag(FGameplayTag iconTag);

	/**
	 * Retrieves the configuration for a specific UI action.
	 *
	 * This function queries the action configuration based on the UI action tag and input type.
	 *
	 * @param actionName The UI action tag.
	 * @param inputType The input type (e.g., keyboard, gamepad).
	 * @param outAction An output parameter that will contain the action configuration if found.
	 * @return True if the action configuration was found; otherwise, false.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	bool TryGetActionConfig(FUIActionTag actionName, const ECommonInputType& inputType, FANSActionConfig& outAction);

	/**
	 * Retrieves an icon for a specific UI action.
	 *
	 * This function returns the icon associated with the given UI action tag and input type.
	 *
	 * @param actionName The UI action tag.
	 * @param inputType The input type (e.g., keyboard, gamepad).
	 * @return A pointer to the UTexture2D representing the icon, or nullptr if not found.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	UTexture2D* GetIconForUIAction(FUIActionTag actionName, const ECommonInputType& inputType);

	/**
	 * Retrieves the icon for a specific key based on the current platform.
	 *
	 * This function returns the appropriate icon for the given key according to the current platform settings.
	 *
	 * @param key The key for which to retrieve the icon.
	 * @return A pointer to the UTexture2D representing the icon, or nullptr if not found.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	UTexture2D* GetCurrentPlatformIconForKey(const FKey& key);

	/**
	 * Retrieves the icon for a specific key for a given platform.
	 *
	 * This function returns the icon associated with the specified key and platform.
	 *
	 * @param key The key for which to retrieve the icon.
	 * @param platform The platform identifier as a string.
	 * @return A pointer to the UTexture2D representing the icon, or nullptr if not found.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	UTexture2D* GetIconForKey(const FKey& key, const FString& platform);

	/**
	* Returns the widget interaction component owned by the local player controller.
	 *
	 * @return The local UANSWidgetInteractionComponent, or nullptr if not found.
	*/
	UFUNCTION(BlueprintPure, Category = ANS)
	UANSWidgetInteractionComponent* GetLocalInteractionComponent() const;

	/**
    * Broadcasts a notification to the UI system.
    * @param Message - The notification text to display.
    * @param Duration - How long the notification should be visible in seconds.
    */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void BroadcastNotification(const FText& Message, float Duration);

	/**
	 * Re-enables navigation on NavPages currently tracked as suspended and clears the list.
	 * Useful when closing overlays/popups that previously suspended background pages.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void RestoreSuspendedPages();

	/**
	 * Mostra o nasconde un intero layer UI (CommonActivatableWidgetStack)
	 * identificato dal suo GameplayTag. Utile per nascondere l'HUD durante
	 * le cinematiche. La scelta persiste agli aggiornamenti automatici dei layer.
	 * @param LayerTag Tag del layer (es. UI.Layer.HUD). Vuoto = layer di default.
	 * @param bVisible true per mostrare, false per nascondere (Collapsed).
	 */
	UFUNCTION(BlueprintCallable, Category = ANS, meta = (Categories = "UI.Layer"))
	void SetLayerVisibility(FGameplayTag LayerTag, bool bVisible);

	UFUNCTION(BlueprintPure, Category = ANS, meta = (Categories = "UI.Layer"))
	bool IsLayerHidden(FGameplayTag LayerTag) const;

	/**
	 * Nasconde o mostra tutti i layer UI attualmente registrati (presi dalla
	 * mappa dei layer). Utile per nascondere completamente la UI durante una
	 * cinematica e ripristinarla alla fine.
	 * @param bHide true per nascondere tutti i layer, false per ripristinarli.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void HideAllLayers(bool bHide);

	/**
	 * Event triggered when the focused navigation widget changes.
	 */
	UPROPERTY(BlueprintAssignable, Category = ANS)
	FOnFocusedWidgetChanged OnFocusChanged;

	/** Broadcast when a UI notification should be displayed. */
	UPROPERTY(BlueprintAssignable, Category = "AUT|Events")
	FOnNotificationRequested OnNotificationRequested;

	// ── Global Navbar Dispatchers ───────────────────────────────────
	// Call the Request* functions from any widget to modify the active
	// navbar without a direct reference. The navbar subscribes to the
	// On* delegates and applies the changes automatically.

	/**
	 * Requests a single action to be added to the active navbar.
	 * Broadcasts OnNavbarActionAddRequested; the navbar handles the rest.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS|Navbar")
	void RequestAddNavbarAction(FUIActionTag ActionTag);

	/**
	 * Requests a single action to be removed from the active navbar.
	 * Broadcasts OnNavbarActionRemoveRequested; the navbar handles the rest.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS|Navbar")
	void RequestRemoveNavbarAction(FUIActionTag ActionTag);

	/**
	 * Replaces the entire set of navbar actions.
	 * Broadcasts OnNavbarActionsSetRequested; the navbar handles the rest.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS|Navbar")
	void RequestSetNavbarActions(const TArray<FUIActionTag>& ActionTags);

	UPROPERTY(BlueprintAssignable, Category = "ANS|Navbar")
	FOnNavbarActionRequested OnNavbarActionAddRequested;

	UPROPERTY(BlueprintAssignable, Category = "ANS|Navbar")
	FOnNavbarActionRequested OnNavbarActionRemoveRequested;

	UPROPERTY(BlueprintAssignable, Category = "ANS|Navbar")
	FOnNavbarActionsRequested OnNavbarActionsSetRequested;

	/**
	 * Broadcasts globally that a navbar action was triggered by user input.
	 * Called automatically by the navbar; can also be invoked manually.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS|Navbar")
	void BroadcastNavbarActionTriggered(FUIActionTag ActionTag);

	/** Fired when any navbar action is triggered by user input (key press or button click). */
	UPROPERTY(BlueprintAssignable, Category = "ANS|Navbar")
	FOnNavbarActionRequested OnNavbarActionTriggered;

private:
	/**
	 * Retrieves the common UI input settings.
	 *
	 * This internal function returns the current UCommonUIInputSettings used by the system.
	 *
	 * @return A pointer to the UCommonUIInputSettings instance.
	 */
	UCommonUIInputSettings* GetInputSettings() const;

	/**
	 * Retrieves the UI developer settings (Project Settings > Ascent UI Settings).
	 * Hosts the icons-by-tag DataTable and per-platform key icon DataTables.
	 *
	 * @return A pointer to the UAUTDeveloperSettings CDO.
	 */
	const UAUTDeveloperSettings* GetUISettings() const;

	/** Loads the widget registry from developer settings. */
	UANSUIWidgetRegistryDataAsset* GetWidgetRegistry() const;

	/**
	 * Returns the stack for the given layer tag, falling back to the default
	 * layer when the tag is empty. Returns nullptr if no matching layer exists.
	 */
	UCommonActivatableWidgetStack* GetLayerStack(const FGameplayTag& LayerTag) const;

	/**
	 * Ensures at least one layer is available.
	 * If none were explicitly registered via RegisterLayer(), auto-discovers
	 * a stack by searching all viewport UUserWidgets' widget trees and
	 * registers it as the default layer.
	 * @return true if at least one layer is available.
	 */
	bool EnsureLayers();

	/** Binds OnDisplayedWidgetChanged on the given stack. */
	void BindStackDelegates(UCommonActivatableWidgetStack* Stack);

	/** Removes this subsystem from a stack's delegates. */
	void UnbindStackDelegates(UCommonActivatableWidgetStack* Stack);

	/** Called when any stack's displayed widget changes; cleans up dead requesters and
	 *  releases pause / input lock if no live requester remains. */
	void HandleDisplayedWidgetChanged(UCommonActivatableWidget* Widget);

	/** Clears per-map UI state when the current world is unloaded. */
	void HandleWorldBeginTearDown(UWorld* World);

	/** Safety net after travel: clears stale input flags before new UI is registered. */
	void HandlePostLoadMapWithWorld(UWorld* LoadedWorld);

	/** Restores gameplay input/pause and forgets all world-owned UI state. */
	void ResetRuntimeState(UWorld* World);

	/** Drops registered layer stacks that are invalid or belong to a previous world. */
	void PruneInvalidLayers();

	/**
	 * Registers a widget as currently requesting the game to be paused.
	 * If this is the first requester the game is paused; subsequent calls just add a ref.
	 */
	void AddPauseRequester(UCommonActivatableWidget* Widget, APlayerController* PC);

	/**
	 * Unregisters a widget that previously requested pause. If no other valid requester
	 * remains the game is unpaused (only when the subsystem owns the pause state).
	 */
	void RemovePauseRequester(UCommonActivatableWidget* Widget, APlayerController* PC);

	/**
	 * Registers a widget as currently requesting UI-only input lock and focuses on it.
	 * If this is the first requester the input mode is switched to UI-only.
	 */
	void AddInputLockRequester(UCommonActivatableWidget* Widget, APlayerController* PC);

	/**
	 * Unregisters a widget that previously requested input lock. If no other valid
	 * requester remains the input mode is switched back to game-only; otherwise focus
	 * is routed to the next remaining input-locking page.
	 */
	void RemoveInputLockRequester(UCommonActivatableWidget* Widget, APlayerController* PC);

	/** Returns true if at least one entry in PauseRequesters still points to a live widget. */
	bool HasAnyValidPauseRequester() const;

	/** Returns true if at least one entry in InputLockRequesters still points to a live widget. */
	bool HasAnyValidInputLockRequester() const;

	/** Drops dead weak refs from both requester arrays. */
	void PruneRequesters();

	/**
	 * After a widget is removed, finds the topmost live input-lock requester and
	 * re-routes Slate focus to its default focusable child. Prevents focus loss on the page
	 * underneath when a pop-up is closed.
	 */
	void RefocusTopmostInputLockingPage();

	/** Reads LayerConfigs from the Widget Registry and hides/shows layers accordingly. */
	void UpdateLayerVisibility();

	/**
	 * Calls SetNavigationEnabled(false) on all active NavPages except those
	 * currently hosted by TargetStack.
	 */
	void SuspendActiveNavPages(const UCommonActivatableWidgetStack* TargetStack);

	/** The currently active widget on the viewport. */
	UPROPERTY()
	TObjectPtr<UUserWidget> currentWidget;

	/** Tag-to-stack map. Populated by RegisterLayer(). */
	UPROPERTY()
	TMap<FGameplayTag, TObjectPtr<UCommonActivatableWidgetStack>> Layers;

	/** The tag of the first layer registered, used as fallback when no LayerTag is specified. */
	FGameplayTag DefaultLayerTag;

	/** True when the subsystem itself paused the game. Used so we don't clobber pause
	 *  state set by external gameplay code. */
	bool bPausedBySubsystem = false;

	/** True when the subsystem switched the input mode to UI-only. */
	bool bGameInputLocked = false;

	/** True when travel destroyed the old PlayerController before we could restore game input. */
	bool bRestoreGameInputOnNextWorld = false;

	/**
	 * Widgets that asked for pause (bPauseGame = true) when spawned/displayed.
	 * Pause stays active as long as at least one valid widget is in this list.
	 * Tracked per-instance so the same widget class opened as standalone vs. as a
	 * subwidget (Options -> Video) keeps its own pause request and back navigation
	 * removes the right one without dropping the pause prematurely.
	 */
	TArray<TWeakObjectPtr<UCommonActivatableWidget>> PauseRequesters;

	/** Widgets that asked for UI-only input lock when spawned/displayed. Same semantics. */
	TArray<TWeakObjectPtr<UCommonActivatableWidget>> InputLockRequesters;

	/** NavPages whose navigation was suspended while a higher layer is active. */
	TArray<TWeakObjectPtr<UANSNavPageWidget>> SuspendedPages;

	/** Layer nascosti esplicitamente via SetLayerVisibility; rispettato da UpdateLayerVisibility. */
	TSet<FGameplayTag> ManuallyHiddenLayers;
};
