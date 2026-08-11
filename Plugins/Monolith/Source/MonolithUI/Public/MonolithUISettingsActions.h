// MonolithUISettingsActions.h
#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUISettingsActions
{
public:
    static void RegisterActions(FMonolithToolRegistry& Registry);

    static FMonolithActionResult HandleScaffoldGameUserSettings(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleScaffoldSaveGame(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleScaffoldSaveSubsystem(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleScaffoldAudioSettings(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleScaffoldInputRemapping(const TSharedPtr<FJsonObject>& Params);

private:
    /** Resolve the Source/<ModuleName>/ directory, creating it if needed. Returns empty string on failure. */
    static FString ResolveSourceDir(const FString& ModuleName, FMonolithActionResult& OutError);

    /** Write a .h and .cpp pair. Returns true on success. */
    static bool WriteSourceFiles(const FString& Dir, const FString& ClassName,
        const FString& HeaderContent, const FString& CppContent,
        TSharedPtr<FJsonObject>& OutResult, FMonolithActionResult& OutError);
};
