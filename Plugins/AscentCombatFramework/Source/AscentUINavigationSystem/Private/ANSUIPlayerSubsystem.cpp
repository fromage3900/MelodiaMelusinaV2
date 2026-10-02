// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ANSUIPlayerSubsystem.h"
#include "ANSNavPageWidget.h"
#include "ANSUITypes.h"
#include "ANSUIWidgetRegistryDataAsset.h"
#include "ANSUINavigationTags.h"
#include "ANSWidgetInteractionComponent.h"
#include "AUTDeveloperSettings.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "CommonActionWidget.h"
#include "CommonActivatableWidget.h"
#include "Engine/DataTable.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "Engine/Texture.h"
#include "Engine/Texture2D.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PawnMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Input/CommonUIInputSettings.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "UITag.h"
#include "Widgets/CommonActivatableWidgetContainer.h"
#include <CommonButtonBase.h>

static const FString LayerMissingError = TEXT("No UI layers registered! Add a CommonActivatableWidgetStack to your HUD and call RegisterLayer(), or call SetWidgetStack() for legacy support.");

void UANSUIPlayerSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	FWorldDelegates::OnWorldBeginTearDown.AddUObject(this, &UANSUIPlayerSubsystem::HandleWorldBeginTearDown);
	FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(this, &UANSUIPlayerSubsystem::HandlePostLoadMapWithWorld);
}

void UANSUIPlayerSubsystem::Deinitialize()
{
	FWorldDelegates::OnWorldBeginTearDown.RemoveAll(this);
	FCoreUObjectDelegates::PostLoadMapWithWorld.RemoveAll(this);

	ResetRuntimeState(GetWorld());

	Super::Deinitialize();
}

UUserWidget* UANSUIPlayerSubsystem::SpawnInGameWidget(TSubclassOf<UUserWidget> widgetClass, bool bPauseGame /*= true*/, bool bLockGameInput, FGameplayTag LayerTag)
{
	APlayerController* playerController = UGameplayStatics::GetPlayerController(this, 0);
	if (!playerController || !widgetClass) {
		return nullptr;
	}

	if (!EnsureLayers())
	{
		UE_LOG(LogTemp, Error, TEXT("%s"), *LayerMissingError);
		if (GEngine) { GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Red, LayerMissingError); }
		return nullptr;
	}

	UCommonActivatableWidgetStack* TargetStack = GetLayerStack(LayerTag);
	if (!TargetStack)
	{
		const FString Msg = FString::Printf(
			TEXT("No UI layer registered for tag '%s'."),
			*LayerTag.ToString());
		UE_LOG(LogTemp, Error, TEXT("%s"), *Msg);
		if (GEngine) { GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Red, Msg); }
		return nullptr;
	}

	if (!widgetClass->IsChildOf(UCommonActivatableWidget::StaticClass()))
	{
		const FString Msg = FString::Printf(
			TEXT("Widget class '%s' must derive from UCommonActivatableWidget to be pushed onto the stack."),
			*widgetClass->GetName());
		UE_LOG(LogTemp, Error, TEXT("%s"), *Msg);
		if (GEngine) { GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Red, Msg); }
		return nullptr;
	}

	SuspendActiveNavPages(TargetStack);

	TSubclassOf<UCommonActivatableWidget> ActivatableClass(*widgetClass);
	UCommonActivatableWidget* Pushed = TargetStack->AddWidget(ActivatableClass);
	if (!Pushed)
	{
		RestoreSuspendedPages();
		return nullptr;
	}

	// OnDisplayedWidgetChanged may run during AddWidget; if it restores suspended pages before the new widget enables nav, suspend again.
	SuspendActiveNavPages(TargetStack);

	currentWidget = Pushed;
	if (bPauseGame)
	{
		AddPauseRequester(Pushed, playerController);
	}

	if (bLockGameInput)
	{
		AddInputLockRequester(Pushed, playerController);
	}
	APawn* pawn = playerController->GetPawn();
	if (pawn && pawn->GetMovementComponent())
	{
		pawn->GetMovementComponent()->StopMovementImmediately();
	}
	return Pushed;
}

void UANSUIPlayerSubsystem::DisplayInGameWidget(UUserWidget* widgetRef, bool bPauseGame /*= true*/, bool bLockGameInput /*= true*/)
{
	APlayerController* playerController = UGameplayStatics::GetPlayerController(this, 0);
	if (!playerController || !widgetRef) {
		return;
	}

	UCommonActivatableWidget* Activatable = Cast<UCommonActivatableWidget>(widgetRef);
	if (!Activatable)
	{
		const FString Msg = FString::Printf(
			TEXT("Widget '%s' must derive from UCommonActivatableWidget."),
			*widgetRef->GetClass()->GetName());
		UE_LOG(LogTemp, Error, TEXT("%s"), *Msg);
		if (GEngine) { GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Red, Msg); }
		return;
	}

	currentWidget = widgetRef;
	Activatable->ActivateWidget();

	if (bPauseGame)
	{
		AddPauseRequester(Activatable, playerController);
	}

	if (bLockGameInput)
	{
		AddInputLockRequester(Activatable, playerController);
	}

	APawn* pawn = playerController->GetPawn();
	if (pawn && pawn->GetMovementComponent())
	{
		pawn->GetMovementComponent()->StopMovementImmediately();
	}
}

void UANSUIPlayerSubsystem::RemoveInGameWidget(UUserWidget* widget, bool bUnlockUIInput, bool bRemovePause)
{
	APlayerController* playerController = UGameplayStatics::GetPlayerController(this, 0);
	if (!widget || !playerController) {
		return;
	}

	UCommonActivatableWidget* Activatable = Cast<UCommonActivatableWidget>(widget);
	if (!Activatable)
	{
		const FString Msg = FString::Printf(
			TEXT("Widget '%s' must derive from UCommonActivatableWidget."),
			*widget->GetClass()->GetName());
		UE_LOG(LogTemp, Error, TEXT("%s"), *Msg);
		if (GEngine) { GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Red, Msg); }
		return;
	}

	Activatable->DeactivateWidget();

	// Drop this widget's pause / input-lock requests. The game state is only flipped
	// when the relevant requester list becomes empty, so chained subwidgets
	// (e.g. Options -> Video) keep the pause until ALL of them are removed.
	if (bRemovePause)
	{
		RemovePauseRequester(Activatable, playerController);
	}

	if (bUnlockUIInput)
	{
		RemoveInputLockRequester(Activatable, playerController);
	}
	else
	{
		// Caller asked to keep the input lock for this widget; just refocus the topmost
		// remaining locking page so gamepad navigation keeps working.
		RefocusTopmostInputLockingPage();
	}
}

void UANSUIPlayerSubsystem::GoToPreviousWidget()
{
	if (!EnsureLayers())
	{
		UE_LOG(LogTemp, Error, TEXT("%s"), *LayerMissingError);
		if (GEngine) { GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::Red, LayerMissingError); }
		return;
	}

	UCommonActivatableWidgetStack* TargetStack = nullptr;

	if (IsValid(currentWidget))
	{
		for (const auto& Pair : Layers)
		{
			UCommonActivatableWidgetStack* Stack = Pair.Value.Get();
			if (IsValid(Stack) && Stack->GetActiveWidget() == currentWidget.Get())
			{
				TargetStack = Stack;
				break;
			}
		}
	}

	if (!TargetStack)
	{
		for (const auto& Pair : Layers)
		{
			UCommonActivatableWidgetStack* Stack = Pair.Value.Get();
			if (IsValid(Stack) && Stack->GetActiveWidget())
			{
				TargetStack = Stack;
				break;
			}
		}
	}

	if (TargetStack)
	{
		if (UCommonActivatableWidget* ActiveWidget = TargetStack->GetActiveWidget())
		{
			APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
			ActiveWidget->DeactivateWidget();
			// Mirror RemoveInGameWidget: drop this widget's pause / input-lock requests
			// so back-navigation cleans up its contribution.
			RemovePauseRequester(ActiveWidget, PC);
			RemoveInputLockRequester(ActiveWidget, PC);
			currentWidget = TargetStack->GetActiveWidget();
		}
	}
}

bool UANSUIPlayerSubsystem::TryGetActionsFromKey(const FKey& key, TArray<FUIActionTag>& outActionsTag)
{
	const UCommonUIInputSettings* inputSett = GetInputSettings();
	const TArray<FUIInputAction> actionsList = inputSett->GetUIInputActions();
	bool bFound = false;
	for (const FUIInputAction& action : actionsList) {
		for (const FUIActionKeyMapping& mapping : action.KeyMappings) {
			if (mapping.Key == key) {
				outActionsTag.Add(action.ActionTag);
				bFound = true;
			}
		}
	}
	return bFound;
}

bool UANSUIPlayerSubsystem::TryGetKeysForAction(const FUIActionTag& UIAction, TArray<FKey>& outKeys)
{
	const UCommonUIInputSettings* inputSett = GetInputSettings();
	const TArray<FUIInputAction> actionsList = inputSett->GetUIInputActions();
	bool bFound = false;
	for (const FUIInputAction& action : actionsList) {

		if (action.ActionTag == UIAction) {
			outKeys.Empty();
			for (const auto& keyMap : action.KeyMappings) {
				outKeys.Add(keyMap.Key);
			}
			bFound = true;
		}
	}
	return bFound;
}

UCommonUIInputSettings* UANSUIPlayerSubsystem::GetInputSettings() const
{
	return GetMutableDefault<UCommonUIInputSettings>();
}

const UAUTDeveloperSettings* UANSUIPlayerSubsystem::GetUISettings() const
{
	return GetDefault<UAUTDeveloperSettings>();
}

UTexture2D* UANSUIPlayerSubsystem::GetIconByTag(FGameplayTag iconTag)
{
	const UAUTDeveloperSettings* UISetting = GetUISettings();

	if (!UISetting) { return nullptr; }

	const UDataTable* IconsByTag = UISetting->GetIconsByTag();
	if (!IconsByTag) {
		UE_LOG(LogTemp, Error, TEXT("Remember to set your UI Icons By Tag in Project Settings > Ascent UI Settings! - UANSUIPlayerSubsystem::GetIconByTag"));
		return nullptr;
	}

	for (const auto& row : IconsByTag->GetRowMap()) {
		FANSIcons* icon = (FANSIcons*)(row.Value);

		if (!icon) {
			UE_LOG(LogTemp, Error, TEXT("Wrong DB Type! - UANSUIPlayerSubsystem::GetIconByTag "));
			return nullptr;
		}
		if (iconTag == icon->IconTag) {
			return icon->Icon;
		}
	}

	return nullptr;
}

bool UANSUIPlayerSubsystem::TryGetActionConfig(FUIActionTag actionName, const ECommonInputType& inputType, FANSActionConfig& outAction)
{
	const UCommonUIInputSettings* inputSettings = GetInputSettings();

	const TArray<FUIInputAction> actionsList = inputSettings->GetUIInputActions();
	const FUIInputAction* action = actionsList.FindByPredicate([actionName](const FUIInputAction& Action) { return Action.ActionTag == actionName; });

	if (!action) {
		UE_LOG(LogTemp, Error, TEXT("Remember to set your UI Actions in Common UI Input Settings"));
		return false;
	}

	outAction.Action = actionName;
	outAction.UIName = action->DefaultDisplayName;

	for (const auto& keymap : action->KeyMappings) {
		if (inputType == ECommonInputType::Gamepad && keymap.Key.IsGamepadKey() || inputType == ECommonInputType::MouseAndKeyboard && !keymap.Key.IsGamepadKey()) {
			outAction.KeyIcon = GetCurrentPlatformIconForKey(keymap.Key);
			return true;
		}
	}

	UE_LOG(LogTemp, Warning, TEXT("Remember to set your Icons! - UANSNavbarComponent::TryGetActionFromKey "));
	return false;
}

class UTexture2D* UANSUIPlayerSubsystem::GetIconForUIAction(FUIActionTag actionName, const ECommonInputType& inputType)
{
	FANSActionConfig outConfig;
	UANSUIPlayerSubsystem::TryGetActionConfig(actionName, inputType, outConfig);
	return outConfig.KeyIcon;
}

class UTexture2D* UANSUIPlayerSubsystem::GetCurrentPlatformIconForKey(const FKey& key)
{
	const FString platform = UGameplayStatics::GetPlatformName();
	return GetIconForKey(key, platform);
}

class UTexture2D* UANSUIPlayerSubsystem::GetIconForKey(const FKey& key, const FString& platform)
{
	const UAUTDeveloperSettings* UISetting = GetUISettings();

	if (!UISetting) {
		UE_LOG(LogTemp, Error, TEXT("Ascent UI Settings unavailable. -UANSUIPlayerSubsystem::GetIconForKey"));
		return nullptr;
	}
	const UDataTable* platformIcons = UISetting->GetKeysConfigForPlatform(platform);
	if (!platformIcons) {
		UE_LOG(LogTemp, Error, TEXT("Remember to set your UI Keys Config for platform '%s' in Project Settings > Ascent UI Settings! -UANSUIPlayerSubsystem::GetIconForKey"), *platform);
		return nullptr;
	}

	for (const auto& row : platformIcons->GetRowMap()) {
		FANSKeysIconConfig* iconConfig = (FANSKeysIconConfig*)(row.Value);
		if (iconConfig && iconConfig->Key == key) {
			return iconConfig->KeyIcon;
		}
	}
	UE_LOG(LogTemp, Warning, TEXT("Remember to set your Keys!! -UANSNavbarComponent::GetIconForKey "));
	return nullptr;
}

UANSWidgetInteractionComponent* UANSUIPlayerSubsystem::GetLocalInteractionComponent() const
{
	if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
	{
		return PC->FindComponentByClass<UANSWidgetInteractionComponent>();
	}
	return nullptr;
}

void UANSUIPlayerSubsystem::SetWidgetStack(UCommonActivatableWidgetStack* InStack)
{
	RegisterLayer(FANSNavigationTag::UI_Layer_Default, InStack);
}

void UANSUIPlayerSubsystem::RegisterLayer(FGameplayTag LayerTag, UCommonActivatableWidgetStack* LayerStack)
{
	if (!LayerTag.IsValid() || !IsValid(LayerStack))
	{
		UE_LOG(LogTemp, Warning, TEXT("RegisterLayer: invalid tag or stack."));
		return;
	}

	PruneInvalidLayers();

	Layers.Add(LayerTag, LayerStack);
	BindStackDelegates(LayerStack);

	if (!DefaultLayerTag.IsValid())
	{
		const UAUTDeveloperSettings* Settings = GetDefault<UAUTDeveloperSettings>();
		if (Settings && Settings->GetDefaultLayerTag().IsValid())
		{
			DefaultLayerTag = Settings->GetDefaultLayerTag();
		}
		else
		{
			DefaultLayerTag = LayerTag;
		}
	}
}

void UANSUIPlayerSubsystem::SetLayerVisibility(FGameplayTag LayerTag, bool bVisible)
{
	EnsureLayers();
	UCommonActivatableWidgetStack* Stack = GetLayerStack(LayerTag);
	if (!IsValid(Stack))
	{
		UE_LOG(LogTemp, Warning, TEXT("SetLayerVisibility: nessun layer per il tag '%s'."), *LayerTag.ToString());
		return;
	}

	const FGameplayTag ResolvedTag = LayerTag.IsValid()
		? LayerTag
		: (DefaultLayerTag.IsValid() ? DefaultLayerTag : FANSNavigationTag::UI_Layer_Default);

	if (bVisible)
	{
		ManuallyHiddenLayers.Remove(ResolvedTag);
	}
	else
	{
		ManuallyHiddenLayers.Add(ResolvedTag);
	}

	UpdateLayerVisibility();
}

bool UANSUIPlayerSubsystem::IsLayerHidden(FGameplayTag LayerTag) const
{
	const FGameplayTag ResolvedTag = LayerTag.IsValid()
		? LayerTag
		: (DefaultLayerTag.IsValid() ? DefaultLayerTag : FANSNavigationTag::UI_Layer_Default);
	return ManuallyHiddenLayers.Contains(ResolvedTag);
}

void UANSUIPlayerSubsystem::HideAllLayers(bool bHide)
{
	EnsureLayers();

	if (bHide)
	{
		for (const auto& Pair : Layers)
		{
			if (Pair.Key.IsValid())
			{
				ManuallyHiddenLayers.Add(Pair.Key);
			}
		}
	}
	else
	{
		ManuallyHiddenLayers.Reset();
	}

	UpdateLayerVisibility();
}

UCommonActivatableWidget* UANSUIPlayerSubsystem::SpawnWidgetByTag(FGameplayTag WidgetTag)
{
	const UANSUIWidgetRegistryDataAsset* Registry = GetWidgetRegistry();
	if (!Registry)
	{
		UE_LOG(LogTemp, Error, TEXT("Widget Registry not set! Configure it in Project Settings > Ascent Navigation Settings. - UANSUIPlayerSubsystem::SpawnWidgetByTag"));
		return nullptr;
	}

	const FANSWidgetConfig* Config = Registry->FindConfigForTag(WidgetTag);
	if (!Config || !Config->WidgetClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("No widget config mapped to tag '%s' in the Widget Registry. - UANSUIPlayerSubsystem::SpawnWidgetByTag"), *WidgetTag.ToString());
		return nullptr;
	}

	return Cast<UCommonActivatableWidget>(SpawnInGameWidget(Config->WidgetClass, Config->bPauseGame, Config->bLockGameInput, Config->LayerTag));
}

UCommonActivatableWidget* UANSUIPlayerSubsystem::SpawnWidgetByTagWithActor(FGameplayTag WidgetTag, AActor* Actor)
{
	UCommonActivatableWidget* Widget = SpawnWidgetByTag(WidgetTag);
	if (UANSNavPageWidget* Page = Cast<UANSNavPageWidget>(Widget))
	{
		Page->SetupWithActor(Actor);
	}
	return Widget;
}

UCommonActivatableWidget* UANSUIPlayerSubsystem::SpawnWidgetByTagWithComponent(FGameplayTag WidgetTag, UActorComponent* Component)
{
	UCommonActivatableWidget* Widget = SpawnWidgetByTag(WidgetTag);
	if (UANSNavPageWidget* Page = Cast<UANSNavPageWidget>(Widget))
	{
		Page->SetupWithComponent(Component);
	}
	return Widget;
}

UCommonActivatableWidget* UANSUIPlayerSubsystem::SpawnWidgetByClassWithActor(TSubclassOf<UUserWidget> WidgetClass, AActor* Actor, bool bPauseGame, bool bLockGameInput, FGameplayTag LayerTag)
{
	UCommonActivatableWidget* Widget = Cast<UCommonActivatableWidget>(SpawnInGameWidget(WidgetClass, bPauseGame, bLockGameInput, LayerTag));
	if (UANSNavPageWidget* Page = Cast<UANSNavPageWidget>(Widget))
	{
		Page->SetupWithActor(Actor);
	}
	return Widget;
}

UCommonActivatableWidget* UANSUIPlayerSubsystem::SpawnWidgetByClassWithComponent(TSubclassOf<UUserWidget> WidgetClass, UActorComponent* Component, bool bPauseGame, bool bLockGameInput, FGameplayTag LayerTag)
{
	UCommonActivatableWidget* Widget = Cast<UCommonActivatableWidget>(SpawnInGameWidget(WidgetClass, bPauseGame, bLockGameInput, LayerTag));
	if (UANSNavPageWidget* Page = Cast<UANSNavPageWidget>(Widget))
	{
		Page->SetupWithComponent(Component);
	}
	return Widget;
}

UANSUIWidgetRegistryDataAsset* UANSUIPlayerSubsystem::GetWidgetRegistry() const
{
	const UAUTDeveloperSettings* Settings = GetDefault<UAUTDeveloperSettings>();
	if (Settings)
	{
		const FSoftObjectPath& Path = Settings->GetWidgetRegistryPath();
		return Cast<UANSUIWidgetRegistryDataAsset>(Path.TryLoad());
	}
	return nullptr;
}

UCommonActivatableWidgetStack* UANSUIPlayerSubsystem::GetLayerStack(const FGameplayTag& LayerTag) const
{
	FGameplayTag ResolvedTag = LayerTag;
	if (!ResolvedTag.IsValid())
	{
		ResolvedTag = DefaultLayerTag.IsValid() ? DefaultLayerTag : FANSNavigationTag::UI_Layer_Default;
	}

	if (const TObjectPtr<UCommonActivatableWidgetStack>* Found = Layers.Find(ResolvedTag))
	{
		UCommonActivatableWidgetStack* Stack = Found->Get();
		const UWorld* CurrentWorld = GetWorld();
		return IsValid(Stack) && (!CurrentWorld || Stack->GetWorld() == CurrentWorld) ? Stack : nullptr;
	}
	return nullptr;
}

bool UANSUIPlayerSubsystem::EnsureLayers()
{
	PruneInvalidLayers();

	if (Layers.Num() > 0)
	{
		return true;
	}

	TArray<UUserWidget*> AllWidgets;
	UWidgetBlueprintLibrary::GetAllWidgetsOfClass(this, AllWidgets, UUserWidget::StaticClass(), false);

	for (UUserWidget* Widget : AllWidgets)
	{
		if (!Widget || !Widget->WidgetTree)
		{
			continue;
		}

		Widget->WidgetTree->ForEachWidget([this](UWidget* Child)
		{
			if (Layers.Num() == 0)
			{
				if (UCommonActivatableWidgetStack* Stack = Cast<UCommonActivatableWidgetStack>(Child))
				{
					RegisterLayer(FANSNavigationTag::UI_Layer_Default, Stack);
				}
			}
		});

		if (Layers.Num() > 0)
		{
			return true;
		}
	}

	return false;
}

void UANSUIPlayerSubsystem::RefocusTopmostInputLockingPage()
{
	// Walk the input-lock requesters from most-recently-added down and refocus
	// the first live NavPage we find.
	for (int32 Index = InputLockRequesters.Num() - 1; Index >= 0; --Index)
	{
		UCommonActivatableWidget* Widget = InputLockRequesters[Index].Get();
		if (!IsValid(Widget))
		{
			continue;
		}
		if (UANSNavPageWidget* NavPage = Cast<UANSNavPageWidget>(Widget))
		{
			NavPage->ResetDefaultFocus();
			return;
		}
	}
}

void UANSUIPlayerSubsystem::AddPauseRequester(UCommonActivatableWidget* Widget, APlayerController* PC)
{
	if (!IsValid(Widget) || !PC)
	{
		return;
	}

	PruneRequesters();
	PauseRequesters.AddUnique(Widget);

	if (!bPausedBySubsystem)
	{
		bPausedBySubsystem = true;
		UGameplayStatics::SetGamePaused(PC, true);
	}
}

void UANSUIPlayerSubsystem::RemovePauseRequester(UCommonActivatableWidget* Widget, APlayerController* PC)
{
	PauseRequesters.RemoveAll([Widget](const TWeakObjectPtr<UCommonActivatableWidget>& W)
	{
		return !W.IsValid() || W.Get() == Widget;
	});

	if (bPausedBySubsystem && !HasAnyValidPauseRequester())
	{
		bPausedBySubsystem = false;
		if (PC)
		{
			UGameplayStatics::SetGamePaused(PC, false);
		}
	}
}

void UANSUIPlayerSubsystem::AddInputLockRequester(UCommonActivatableWidget* Widget, APlayerController* PC)
{
	if (!IsValid(Widget) || !PC)
	{
		return;
	}

	PruneRequesters();
	InputLockRequesters.AddUnique(Widget);
	bGameInputLocked = true;

	// Always re-set the input mode so focus lands on the newly added requester
	// (mirrors the previous per-spawn behaviour).
	FInputModeUIOnly InputMode;
	InputMode.SetWidgetToFocus(Widget->TakeWidget());
	PC->SetInputMode(InputMode);
}

void UANSUIPlayerSubsystem::RemoveInputLockRequester(UCommonActivatableWidget* Widget, APlayerController* PC)
{
	InputLockRequesters.RemoveAll([Widget](const TWeakObjectPtr<UCommonActivatableWidget>& W)
	{
		return !W.IsValid() || W.Get() == Widget;
	});

	if (bGameInputLocked && !HasAnyValidInputLockRequester())
	{
		bGameInputLocked = false;
		if (PC)
		{
			FInputModeGameOnly InputMode;
			PC->SetInputMode(InputMode);
		}
	}
	else
	{
		// Another input-locking widget remains; re-route focus to it.
		RefocusTopmostInputLockingPage();
	}
}

bool UANSUIPlayerSubsystem::HasAnyValidPauseRequester() const
{
	for (const TWeakObjectPtr<UCommonActivatableWidget>& W : PauseRequesters)
	{
		if (W.IsValid())
		{
			return true;
		}
	}
	return false;
}

bool UANSUIPlayerSubsystem::HasAnyValidInputLockRequester() const
{
	for (const TWeakObjectPtr<UCommonActivatableWidget>& W : InputLockRequesters)
	{
		if (W.IsValid())
		{
			return true;
		}
	}
	return false;
}

void UANSUIPlayerSubsystem::PruneRequesters()
{
	PauseRequesters.RemoveAll([](const TWeakObjectPtr<UCommonActivatableWidget>& W)
	{
		return !W.IsValid();
	});
	InputLockRequesters.RemoveAll([](const TWeakObjectPtr<UCommonActivatableWidget>& W)
	{
		return !W.IsValid();
	});
}

void UANSUIPlayerSubsystem::BindStackDelegates(UCommonActivatableWidgetStack* Stack)
{
	if (IsValid(Stack))
	{
		Stack->OnDisplayedWidgetChanged().RemoveAll(this);
		Stack->OnDisplayedWidgetChanged().AddUObject(this, &UANSUIPlayerSubsystem::HandleDisplayedWidgetChanged);
	}
}

void UANSUIPlayerSubsystem::UnbindStackDelegates(UCommonActivatableWidgetStack* Stack)
{
	if (IsValid(Stack))
	{
		Stack->OnDisplayedWidgetChanged().RemoveAll(this);
	}
}

void UANSUIPlayerSubsystem::HandleDisplayedWidgetChanged(UCommonActivatableWidget* Widget)
{
	currentWidget = Widget;

	UpdateLayerVisibility();
	RestoreSuspendedPages();

	// Ensure the now-visible page re-routes Slate focus to its last focused child.
	// NativeOnActivated already does this for same-stack transitions; this is the
	// safety net for any path where the widget becomes visible without going through
	// the full CommonUI activation lifecycle (e.g. layer visibility changes).
	if (UANSNavPageWidget* NavPage = Cast<UANSNavPageWidget>(Widget))
	{
		NavPage->SetNeedsReset();
	}

	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC)
	{
		return;
	}

	// Catch widgets that disappeared without going through RemoveInGameWidget
	// (e.g. CommonUI back navigation or external destroy). Their weak refs go
	// stale here, so pruning + re-checking releases the pause / input lock.
	PruneRequesters();

	if (bPausedBySubsystem && !HasAnyValidPauseRequester())
	{
		bPausedBySubsystem = false;
		UGameplayStatics::SetGamePaused(PC, false);
	}

	if (bGameInputLocked && !HasAnyValidInputLockRequester())
	{
		bGameInputLocked = false;
		FInputModeGameOnly InputMode;
		PC->SetInputMode(InputMode);
	}
}

void UANSUIPlayerSubsystem::HandleWorldBeginTearDown(UWorld* World)
{
	if (!World)
	{
		return;
	}

	bool bOwnsWorldState = (World == GetWorld())
		|| (IsValid(currentWidget) && currentWidget->GetWorld() == World);

	if (!bOwnsWorldState)
	{
		for (const auto& Pair : Layers)
		{
			if (IsValid(Pair.Value) && Pair.Value->GetWorld() == World)
			{
				bOwnsWorldState = true;
				break;
			}
		}
	}

	if (bOwnsWorldState)
	{
		ResetRuntimeState(World);
	}
}

void UANSUIPlayerSubsystem::HandlePostLoadMapWithWorld(UWorld* LoadedWorld)
{
	if (!LoadedWorld || LoadedWorld != GetWorld())
	{
		return;
	}

	if (bRestoreGameInputOnNextWorld)
	{
		if (APlayerController* PC = LoadedWorld->GetFirstPlayerController())
		{
			FInputModeGameOnly InputMode;
			PC->SetInputMode(InputMode);
			bRestoreGameInputOnNextWorld = false;
		}
	}

	PruneRequesters();
	PruneInvalidLayers();

	if (bPausedBySubsystem || bGameInputLocked)
	{
		ResetRuntimeState(LoadedWorld);
	}
}

void UANSUIPlayerSubsystem::ResetRuntimeState(UWorld* World)
{
	APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;

	if (bGameInputLocked)
	{
		if (PC)
		{
			FInputModeGameOnly InputMode;
			PC->SetInputMode(InputMode);
			bRestoreGameInputOnNextWorld = false;
		}
		else
		{
			bRestoreGameInputOnNextWorld = true;
		}
	}

	if (bPausedBySubsystem && PC)
	{
		UGameplayStatics::SetGamePaused(PC, false);
	}

	for (const auto& Pair : Layers)
	{
		UnbindStackDelegates(Pair.Value.Get());
	}

	currentWidget = nullptr;
	Layers.Reset();
	DefaultLayerTag = FGameplayTag();
	PauseRequesters.Reset();
	InputLockRequesters.Reset();
	SuspendedPages.Reset();
	ManuallyHiddenLayers.Reset();
	bPausedBySubsystem = false;
	bGameInputLocked = false;
}

void UANSUIPlayerSubsystem::PruneInvalidLayers()
{
	const UWorld* CurrentWorld = GetWorld();
	for (auto It = Layers.CreateIterator(); It; ++It)
	{
		UCommonActivatableWidgetStack* Stack = It.Value().Get();
		if (!IsValid(Stack) || (CurrentWorld && Stack->GetWorld() != CurrentWorld))
		{
			UnbindStackDelegates(Stack);
			It.RemoveCurrent();
		}
	}

	if (Layers.Num() == 0)
	{
		DefaultLayerTag = FGameplayTag();
	}
}

void UANSUIPlayerSubsystem::SuspendActiveNavPages(const UCommonActivatableWidgetStack* TargetStack)
{
	for (const auto& Pair : Layers)
	{
		UCommonActivatableWidgetStack* Stack = Pair.Value.Get();
		if (!IsValid(Stack))
		{
			continue;
		}
		if (Stack == TargetStack)
		{
			continue;
		}
		if (UCommonActivatableWidget* Active = Stack->GetActiveWidget())
		{
			if (UANSNavPageWidget* NavPage = Cast<UANSNavPageWidget>(Active))
			{
				if (NavPage->GetNavigationEnabled())
				{
					NavPage->SetNavigationEnabled(false);
					NavPage->SetVisibility(ESlateVisibility::HitTestInvisible);
					SuspendedPages.AddUnique(TWeakObjectPtr<UANSNavPageWidget>(NavPage));
				}
			}
		}
	}
}

void UANSUIPlayerSubsystem::RestoreSuspendedPages()
{
	TArray<UANSNavPageWidget*> RestoredPages;
	for (const TWeakObjectPtr<UANSNavPageWidget>& WeakPage : SuspendedPages)
	{
		if (UANSNavPageWidget* Page = WeakPage.Get())
		{
			Page->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
			Page->SetNavigationEnabled(true);
			RestoredPages.Add(Page);
		}
	}
	SuspendedPages.Empty();

	if (RestoredPages.Num() > 0)
	{
		UANSNavPageWidget* PageToFocus = RestoredPages[0];
		if (UWorld* World = PageToFocus->GetWorld())
		{
			TWeakObjectPtr<UANSNavPageWidget> WeakPageToFocus = PageToFocus;
			World->GetTimerManager().SetTimerForNextTick([WeakPageToFocus]()
			{
				if (UANSNavPageWidget* Page = WeakPageToFocus.Get())
				{
					Page->SetNeedsReset();
				}
			});
		}
	}
}

void UANSUIPlayerSubsystem::UpdateLayerVisibility()
{
	const UANSUIWidgetRegistryDataAsset* Registry = GetWidgetRegistry();
	if (!Registry)
	{
		return;
	}

	const TMap<FGameplayTag, FANSUILayerConfig>& Configs = Registry->GetLayerConfigs();

	TSet<FGameplayTag> LayersToHide;
	for (const auto& Pair : Layers)
	{
		if (IsValid(Pair.Value) && Pair.Value->GetActiveWidget())
		{
			if (const FANSUILayerConfig* Cfg = Configs.Find(Pair.Key))
			{
				for (const FGameplayTag& Tag : Cfg->HidesLayers)
				{
					LayersToHide.Add(Tag);
				}
			}
		}
	}

	for (const FGameplayTag& Tag : ManuallyHiddenLayers)
	{
		LayersToHide.Add(Tag);
	}

	for (const auto& Pair : Layers)
	{
		if (IsValid(Pair.Value))
		{
			const ESlateVisibility DesiredVisibility = LayersToHide.Contains(Pair.Key)
				? ESlateVisibility::Collapsed
				: ESlateVisibility::SelfHitTestInvisible;
			Pair.Value->SetVisibility(DesiredVisibility);
		}
	}
}

void UANSUIPlayerSubsystem::BroadcastNotification(const FText& Message, float Duration)
{
	OnNotificationRequested.Broadcast(Message, Duration);
}

void UANSUIPlayerSubsystem::RequestAddNavbarAction(FUIActionTag ActionTag)
{
	OnNavbarActionAddRequested.Broadcast(ActionTag);
}

void UANSUIPlayerSubsystem::RequestRemoveNavbarAction(FUIActionTag ActionTag)
{
	OnNavbarActionRemoveRequested.Broadcast(ActionTag);
}

void UANSUIPlayerSubsystem::RequestSetNavbarActions(const TArray<FUIActionTag>& ActionTags)
{
	OnNavbarActionsSetRequested.Broadcast(ActionTags);
}

void UANSUIPlayerSubsystem::BroadcastNavbarActionTriggered(FUIActionTag ActionTag)
{
	OnNavbarActionTriggered.Broadcast(ActionTag);
}
