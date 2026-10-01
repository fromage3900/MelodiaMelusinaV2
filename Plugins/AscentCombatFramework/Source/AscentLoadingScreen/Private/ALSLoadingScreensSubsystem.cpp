// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ALSLoadingScreensSubsystem.h"
#include "ALSLoadingScreenSettings.h"
#include <Blueprint/UserWidget.h>
#include <Kismet/GameplayStatics.h>
#include <MoviePlayer.h>
#include <TimerManager.h>
#include <Engine/World.h>

void UALSLoadingScreensSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{

	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	if (!IsRunningDedicatedServer()) {
		bStartUpLoadingScreen = true;
		FCoreUObjectDelegates::PreLoadMap.AddUObject(this, &UALSLoadingScreensSubsystem::BeginLoadingScreen);
		FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(this, &UALSLoadingScreensSubsystem::EndLoadingScreen);
	}
}

void UALSLoadingScreensSubsystem::Deinitialize()
{
	if (!IsRunningDedicatedServer()) 
	{
		FCoreUObjectDelegates::PreLoadMap.RemoveAll(this);
		FCoreUObjectDelegates::PostLoadMapWithWorld.RemoveAll(this);
		
		// Clear any pending removal timer
		if (RemovalDelayTimerHandle.IsValid())
		{
			UWorld* World = GetWorld();
			if (World)
			{
				World->GetTimerManager().ClearTimer(RemovalDelayTimerHandle);
			}
			RemovalDelayTimerHandle.Invalidate();
		}
	}
}

void UALSLoadingScreensSubsystem::BeginLoadingScreen(const FString& MapName)
{
	const UALSLoadingScreenSettings* Settings = GetDefault<UALSLoadingScreenSettings>();
	TSubclassOf<class UUserWidget> loadingScreenClass = Settings->GetLoadingScreen();
	UGameInstance* pc = UGameplayStatics::GetGameInstance(this);

	if (Settings->GetIsEnabled() && loadingScreenClass && pc) {

		FLoadingScreenAttributes LoadingScreen;
		if (!bStartUpLoadingScreen) {

			FALSLoadingScreenAttributes config = Settings->GetLoadingScreenSettings();

			const auto LoadingWidget = CreateWidget<UUserWidget>(pc, loadingScreenClass, TEXT("LoadingScreen"));
			LoadingScreen.WidgetLoadingScreen = LoadingWidget->TakeWidget();
			LoadingScreen.bAllowInEarlyStartup = config.bAllowInEarlyStartup;
			LoadingScreen.PlaybackType = config.PlaybackType;
			LoadingScreen.bAllowEngineTick = config.bAllowEngineTick;
			LoadingScreen.bWaitForManualStop = config.bWaitForManualStop;
			LoadingScreen.bAutoCompleteWhenLoadingCompletes = config.bAutoCompleteWhenLoadingCompletes;
			LoadingScreen.MinimumLoadingScreenDisplayTime = config.MinimumLoadingScreenDisplayTime;
			LoadingScreen.bMoviesAreSkippable = false;
			GetMoviePlayer()->SetupLoadingScreen(LoadingScreen);
		}


	}
	else {
		UE_LOG(LogTemp, Warning, TEXT("Missing Default Item Class! - UACFFunctionLibrary "));
	}
}

void UALSLoadingScreensSubsystem::EndLoadingScreen(UWorld* InLoadedWorld)
{
	OnMapLoaded.Broadcast();
	bStartUpLoadingScreen = false;
	
	// Apply configurable delay before removing loading screen
	const UALSLoadingScreenSettings* Settings = GetDefault<UALSLoadingScreenSettings>();
	if (Settings && Settings->GetIsEnabled())
	{
		const FALSLoadingScreenAttributes config = Settings->GetLoadingScreenSettings();
		
		if (config.LoadingScreenRemovalDelay > 0.f)
		{
			// Clear any existing timer
			if (InLoadedWorld && RemovalDelayTimerHandle.IsValid())
			{
				InLoadedWorld->GetTimerManager().ClearTimer(RemovalDelayTimerHandle);
			}
			
			// Set timer to remove loading screen after delay
			if (InLoadedWorld)
			{
				InLoadedWorld->GetTimerManager().SetTimer(
					RemovalDelayTimerHandle,
					this,
					&UALSLoadingScreensSubsystem::RemoveLoadingScreenImmediate,
					config.LoadingScreenRemovalDelay,
					false
				);
			}
		}
		else
		{
			// No delay, remove immediately
			RemoveLoadingScreenImmediate();
		}
	}
}

// void UALSLoadingScreensSubsystem::Tick(float DeltaTime)
// {
//     Super::Tick(DeltaTime);
//     if (bPendingRemove) {
//         RemoveLoadingScreen();
//     }
// }

// void UALSLoadingScreensSubsystem::StartLoadingScreen(TSubclassOf<UUserWidget> loadingScreenClass)
// {
// }
//
// void UALSLoadingScreensSubsystem::SetupMoviePlayer()
// {
//     const UALSLoadingScreenSettings* Settings = GetDefault<UALSLoadingScreenSettings>();
//
//     FALSLoadingScreenAttributes LoadingScreenSettings = Settings->GetLoadingScreenSettings();
//     FLoadingScreenAttributes LoadingScreen;
//     LoadingScreen.MinimumLoadingScreenDisplayTime = LoadingScreenSettings.MinimumLoadingScreenDisplayTime;
//     LoadingScreen.bAutoCompleteWhenLoadingCompletes = LoadingScreenSettings.bAutoCompleteWhenLoadingCompletes;
//     LoadingScreen.bMoviesAreSkippable = LoadingScreenSettings.bMoviesAreSkippable;
//     LoadingScreen.bWaitForManualStop = LoadingScreenSettings.bWaitForManualStop;
//     LoadingScreen.bAllowInEarlyStartup = LoadingScreenSettings.bAllowInEarlyStartup;
//     LoadingScreen.bAllowEngineTick = LoadingScreenSettings.bAllowEngineTick;
//     LoadingScreen.MoviePaths = LoadingScreen.MoviePaths;
//     LoadingScreen.PlaybackType = LoadingScreenSettings.PlaybackType;
//
//     APlayerController* pc = UGameplayStatics::GetPlayerController(this, 0);
//     TSubclassOf<class UUserWidget> loadingScreenClass = Settings->GetLoadingScreen();
//     if (pc && loadingScreenClass) {
//         loadingWidget = CreateWidget<UUserWidget>(pc, loadingScreenClass);
//         if (loadingWidget) {
//             LoadingScreen.WidgetLoadingScreen = loadingWidget->TakeWidget();
//         }
//     }
//
//     GetMoviePlayer()->SetupLoadingScreen(LoadingScreen);
// }

// void UALSLoadingScreensSubsystem::OpenLevelWithLoadingScreen(const TSoftObjectPtr<UWorld> Level, TSubclassOf<UUserWidget> loadingScreen)
// {
//     StartLoadingScreen(loadingScreen);
//     bPendingRemove = true;
//     UGameplayStatics::OpenLevelBySoftObjectPtr(this, Level, true);
// }

void UALSLoadingScreensSubsystem::RemoveLoadingScreen()
{
	// This function now applies the configured delay
	const UALSLoadingScreenSettings* Settings = GetDefault<UALSLoadingScreenSettings>();
	if (Settings && Settings->GetIsEnabled())
	{
		const FALSLoadingScreenAttributes config = Settings->GetLoadingScreenSettings();
		
		if (config.LoadingScreenRemovalDelay > 0.f)
		{
			UWorld* World = GetWorld();
			if (World && RemovalDelayTimerHandle.IsValid())
			{
				World->GetTimerManager().ClearTimer(RemovalDelayTimerHandle);
			}
			
			if (World)
			{
				World->GetTimerManager().SetTimer(
					RemovalDelayTimerHandle,
					this,
					&UALSLoadingScreensSubsystem::RemoveLoadingScreenImmediate,
					config.LoadingScreenRemovalDelay,
					false
				);
			}
		}
		else
		{
			RemoveLoadingScreenImmediate();
		}
	}
	else
	{
		RemoveLoadingScreenImmediate();
	}
}

void UALSLoadingScreensSubsystem::RemoveLoadingScreenImmediate()
{
	if (GetMoviePlayer() && GetMoviePlayer()->IsLoadingFinished()) 
	{
		GetMoviePlayer()->StopMovie();
		bIsSubsystemActive = false;
	}
	
	// Clear timer handle
	if (RemovalDelayTimerHandle.IsValid())
	{
		UWorld* World = GetWorld();
		if (World)
		{
			World->GetTimerManager().ClearTimer(RemovalDelayTimerHandle);
		}
		RemovalDelayTimerHandle.Invalidate();
	}
}
