// Copyright tumourlove. All Rights Reserved.
// MonolithUISettings.cpp — Phase G

#include "MonolithUISettings.h"

#define LOCTEXT_NAMESPACE "MonolithUISettings"

UMonolithUISettings::UMonolithUISettings()
    : GeneratedStylesPath(TEXT("/Game/UI/Styles/"))
    , CanonicalLibraryPath(TEXT("/Game/UI/Library/"))
    , StyleCacheCap(200)
    , MaxNestingDepth(32)
    , PathCacheCap(256)
{
    // CategoryName is exposed via GetCategoryName() override below — we keep
    // the protected `CategoryName` member untouched so the override is the
    // single source of truth for the section grouping.
}

FName UMonolithUISettings::GetCategoryName() const
{
    // Surfaces under "Plugins" in Project Settings, alongside other
    // Monolith-family settings classes. Matches the long-standing convention
    // used by `UMonolithSettings` (MonolithCore).
    return FName(TEXT("Plugins"));
}

FName UMonolithUISettings::GetSectionName() const
{
    // Section short-name; the editor uses GetSectionText() for the display
    // string. Stable across versions because INI sections key off this name.
    return FName(TEXT("Monolith UI"));
}

#if WITH_EDITOR
FText UMonolithUISettings::GetSectionText() const
{
    return LOCTEXT("MonolithUISettingsSection", "Monolith UI");
}

FText UMonolithUISettings::GetSectionDescription() const
{
    return LOCTEXT(
        "MonolithUISettingsDescription",
        "Configuration for the MonolithUI module: generated-asset paths, cache caps, and validator limits.");
}
#endif

const UMonolithUISettings* UMonolithUISettings::Get()
{
    // GetDefault<> on a UDeveloperSettings is always non-null after the module
    // initialises (the CDO is registered on first access). Returning the
    // const* matches the read-only nature of settings access from the style
    // service hot path.
    return GetDefault<UMonolithUISettings>();
}

FString UMonolithUISettings::NormalizeFolderPath(const FString& Path)
{
    if (Path.IsEmpty())
    {
        return Path;
    }

    FString Out = Path;

    // Strip a trailing slash so callers can always Printf("%s/%s", ...) without
    // worrying about doubling.
    while (Out.Len() > 1 && (Out.EndsWith(TEXT("/")) || Out.EndsWith(TEXT("\\"))))
    {
        Out = Out.LeftChop(1);
    }

    // Ensure a leading slash. Project paths in UE always begin with `/Game/`
    // or `/<Plugin>/`; users sometimes elide the slash in INI entries.
    if (!Out.StartsWith(TEXT("/")))
    {
        Out = FString(TEXT("/")) + Out;
    }

    return Out;
}

#undef LOCTEXT_NAMESPACE
