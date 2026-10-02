// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include <MoviePlayer.h>
#include "Subsystems/WorldSubsystem.h"



#include "ALSLoadingScreensSubsystem.generated.h"


struct FLoadingScreenAttributes;
    /**
 *
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnMapLoaded);

UCLASS(BlueprintType)
class ASCENTLOADINGSCREEN_API UALSLoadingScreensSubsystem : public UGameInstanceSubsystem {
    GENERATED_BODY()

public:
//     UFUNCTION(BlueprintCallable, Category = ALS)
//     void StartLoadingScreen(TSubclassOf<UUserWidget> loadingScreen);

//     UFUNCTION(BlueprintCallable, Category = ALS)
//     void OpenLevelWithLoadingScreen(const TSoftObjectPtr<UWorld> Level, TSubclassOf<UUserWidget> loadingScreen);

     UFUNCTION(BlueprintCallable, Category = ALS)
     void RemoveLoadingScreen();

    UFUNCTION(BlueprintCallable, Category = ALS)
    void RemoveLoadingScreenImmediate();

    UFUNCTION(BlueprintCallable, Category = ALS)
    void SetLoadingScreensEnabled(const bool bIsEnabled)
    {
        bIsSubsystemActive = bIsEnabled;
    }

    UFUNCTION(BlueprintPure, Category = ALS)
    bool IsEnabled() const
    {
        return bIsSubsystemActive;
    }

    UPROPERTY(BlueprintAssignable, Category = ALS)
    FOnMapLoaded OnMapLoaded;

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

/*    virtual void Tick(float DeltaTime) override;*/

private:

   void SetupMoviePlayer();

    UFUNCTION()
	virtual void BeginLoadingScreen(const FString& MapName);
	UFUNCTION()
	virtual void EndLoadingScreen(UWorld* InLoadedWorld);

    bool bStartUpLoadingScreen = true;
    bool bIsSubsystemActive = false;

    FLoadingScreenAttributes loadingScreen;
    
    FTimerHandle RemovalDelayTimerHandle;
};
