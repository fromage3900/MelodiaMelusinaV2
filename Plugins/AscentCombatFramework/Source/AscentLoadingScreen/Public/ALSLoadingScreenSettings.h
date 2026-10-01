// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include <MoviePlayer.h>

#include "ALSLoadingScreenSettings.generated.h"

/**
 *
 */
USTRUCT(BlueprintType)
struct ASCENTLOADINGSCREEN_API FALSLoadingScreenAttributes {
    GENERATED_BODY()

    // The minimum time that a loading screen should be up, -1 means no minimum time. 
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ALS)
    float MinimumLoadingScreenDisplayTime = 5.f;

    // Additional delay in seconds before removing the loading screen after loading is complete. This helps hide asset streaming and level initialization.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ALS, meta = (ClampMin = "0.0", UIMin = "0.0"))
    float LoadingScreenRemovalDelay = 2.f;

    // If true, the loading screen will disappear as soon as loading is done.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ALS)
    bool bAutoCompleteWhenLoadingCompletes = true;

//     UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ALS)
//     bool bMoviesAreSkippable = true;

    /**
     * If true, movie playback continue until RemoveLoadingScreen from the ALSLoadingScreenSubsystem is called
     */
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ALS)
    bool bWaitForManualStop = false;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ALS)
    bool bAllowInEarlyStartup = false;

    /** If true, this will call the engine tick while the game is loading */
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ALS)
    bool bAllowEngineTick = false;

    /** How the playback sghould happen*/
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Movies Settings")
    TEnumAsByte<EMoviePlaybackType> PlaybackType = EMoviePlaybackType::MT_Normal;

    /**
     * All movie files must be in Content/Movies/ director and should be MPEG-4 (mp4). Enter file path/name without the extension.
     */
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ALS)
    TArray<FString> MoviePaths;
};

UCLASS(config = Plugins, Defaultconfig, meta = (DisplayName = "Ascent Loading Screens"))
class ASCENTLOADINGSCREEN_API UALSLoadingScreenSettings : public UDeveloperSettings {
    GENERATED_BODY()

public:
    bool GetIsEnabled() const { return EnableLoadingScreen; }
    FALSLoadingScreenAttributes GetLoadingScreenSettings() const { return LoadingScreenAttributes; }

    TSubclassOf<class UUserWidget> GetLoadingScreen() const { return LoadingWidget; }
    UALSLoadingScreenSettings();


protected:
    UPROPERTY(EditAnywhere, config, Category = "ALS")
    bool EnableLoadingScreen;



    UPROPERTY(EditAnywhere, config, Category = "ALS|LoadingScreens")
    FALSLoadingScreenAttributes LoadingScreenAttributes;

    /** Widget Class for the loading screen */
    UPROPERTY(EditAnywhere, config, Category = "ALS|LoadingScreens")
    TSubclassOf<class UUserWidget> LoadingWidget;
};
