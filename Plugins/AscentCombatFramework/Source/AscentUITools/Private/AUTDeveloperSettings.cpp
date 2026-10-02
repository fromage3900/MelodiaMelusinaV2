// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "AUTDeveloperSettings.h"
#include "AUTThemeDataAsset.h"

 UAUTThemeDataAsset* UAUTDeveloperSettings::GetTheme() const
{
 	return Cast<UAUTThemeDataAsset>(ThemesAsset.TryLoad());
}

TSoftObjectPtr<UWorld> UAUTDeveloperSettings::GetDefaultMenuMapRef() const
{
    TSoftObjectPtr<UWorld> newWorld;
    newWorld = DefaultMenuMap;
    return newWorld;
}

TSoftObjectPtr<UWorld> UAUTDeveloperSettings::GetDefaultNewGameMapRef() const
{
    TSoftObjectPtr<UWorld> newWorld;
    newWorld = DefaultNewGameMap;
    return newWorld;
}

UDataTable* UAUTDeveloperSettings::GetKeysConfigForPlatform(const FString& Platform) const
{
    const TSoftObjectPtr<UDataTable>* Found = KeysConfigByPlatform.Find(Platform);
    if (!Found)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("UAUTDeveloperSettings::GetKeysConfigForPlatform - Platform '%s' not configured. Add it under Project Settings > Ascent UI Settings > UI Keys."),
            *Platform);
        return nullptr;
    }

    UDataTable* Loaded = Found->LoadSynchronous();
    if (!Loaded)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("UAUTDeveloperSettings::GetKeysConfigForPlatform - Failed to load DataTable for platform '%s'. Asset path may be invalid."),
            *Platform);
    }
    return Loaded;
}
