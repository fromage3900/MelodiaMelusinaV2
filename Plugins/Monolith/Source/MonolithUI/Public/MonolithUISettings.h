// Copyright tumourlove. All Rights Reserved.
// MonolithUISettings.h — Phase G
//
// UDeveloperSettings-derived configuration for the MonolithUI module. Drives
// asset paths used by the style service, cache caps, and validator limits.
// Lives in /Script/MonolithUI.MonolithUISettings — surfaces in Project Settings
// under the "Plugins" category.
//
// Module dependency reminder: UDeveloperSettings is in the `DeveloperSettings`
// module, NOT `Engine`. MonolithUI.Build.cs has been updated accordingly.
// Verified: C:\Program Files (x86)\UE_5.7\Engine\Source\Runtime\DeveloperSettings\Public\Engine\DeveloperSettings.h:23
//   `UCLASS(Abstract, MinimalAPI) class UDeveloperSettings : public UObject`
//
// Live-refresh wiring: `UDeveloperSettings::OnSettingChanged()` (header line 47)
// is a multicast delegate fired from PostEditChangeProperty. Subscribing the
// MonolithUI registry subsystem to that delegate lets cache caps and paths
// re-apply mid-session — but the wiring is DEFERRED to a follow-up task to
// avoid touching `MonolithUIRegistrySubsystem.cpp` while Phase E owns it for
// curated-mapping additions. Until that lands, edits in Project Settings
// require an editor restart to take effect.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "MonolithUISettings.generated.h"

/**
 * Project Settings → Plugins → Monolith UI.
 *
 * All values have safe defaults so the module works out of the box; only
 * projects that want to relocate generated assets or change cache discipline
 * need to edit the INI.
 *
 * Stored under `[/Script/MonolithUI.MonolithUISettings]` in `DefaultGame.ini`
 * (the `config` UCLASS specifier keys to the per-game settings file).
 */
UCLASS(config = Game, defaultconfig, meta = (DisplayName = "Monolith UI"))
class MONOLITHUI_API UMonolithUISettings : public UDeveloperSettings
{
    GENERATED_BODY()

public:
    UMonolithUISettings();

    //~ Begin UDeveloperSettings interface
    virtual FName GetCategoryName() const override;
    virtual FName GetSectionName() const override;
#if WITH_EDITOR
    virtual FText GetSectionText() const override;
    virtual FText GetSectionDescription() const override;
#endif
    //~ End UDeveloperSettings interface

    /**
     * Where the style service writes newly-generated style class assets when
     * no explicit `package_path` is supplied. Style assets are Blueprints
     * whose parent is `UCommonButtonStyle` / `UCommonTextStyle` / `UCommonBorderStyle`;
     * the generated class is what `apply_style_to_widget` consumes.
     *
     * Default: `/Game/UI/Styles/`. Trailing slash optional — the service
     * normalises before use.
     */
    UPROPERTY(config, EditAnywhere, Category = "Style",
        meta = (DisplayName = "Generated Styles Path",
                ToolTip = "Folder where the style service places newly-created style class assets."))
    FString GeneratedStylesPath;

    /**
     * Folder scanned for canonical pre-authored style assets. The style service
     * checks this folder by name BEFORE falling back to hash-based dedup, so
     * the project's curated library always wins over auto-generated styles.
     *
     * Default: `/Game/UI/Library/`. Empty disables the canonical-library lookup
     * step entirely (service still does name-cache + hash-cache lookups).
     */
    UPROPERTY(config, EditAnywhere, Category = "Style",
        meta = (DisplayName = "Canonical Library Path",
                ToolTip = "Folder containing pre-authored style assets that win over auto-generated ones."))
    FString CanonicalLibraryPath;

    /**
     * Maximum number of entries the style service keeps in its name + hash
     * caches before LRU-evicting the oldest. Each entry is a TSubclassOf<>
     * weak pointer plus two cheap maps' worth of FString keys; 200 is
     * comfortably under 1 MB of working set even with long names.
     *
     * Set to 0 to disable eviction entirely (cache grows unbounded).
     * Default: 200.
     */
    UPROPERTY(config, EditAnywhere, Category = "Cache",
        meta = (DisplayName = "Style Cache Cap", ClampMin = "0", ClampMax = "100000",
                ToolTip = "Max entries in the style service cache; 0 disables eviction."))
    int32 StyleCacheCap;

    /**
     * Maximum nesting depth allowed in `FUISpecDocument` when it ships in
     * Phase H. The validator rejects specs deeper than this with a `TooDeep`
     * error before any asset mutation. Mirrors the recon doc's max-depth-8
     * advice for reflection walking, applied to the spec tree itself.
     *
     * Default: 32. Cap is generous — real-world UMG trees rarely exceed 6–8.
     * Surfaced now so the validator (Phase H) and the property path cache can
     * read the same source of truth.
     */
    UPROPERTY(config, EditAnywhere, Category = "Spec",
        meta = (DisplayName = "Max Nesting Depth", ClampMin = "1", ClampMax = "256",
                ToolTip = "Maximum tree depth a UISpec can request; deeper specs are rejected by the validator."))
    int32 MaxNestingDepth;

    /**
     * Maximum entries kept in `FUIPropertyPathCache` (Phase C). The cache itself
     * currently hardcodes 256 — TODO: have the cache read this value at
     * construction so projects can tune it. Until then, this field is the
     * intended source of truth and the cache constructor will pick it up in a
     * follow-up patch.
     *
     * Default: 256.
     */
    UPROPERTY(config, EditAnywhere, Category = "Reflection",
        meta = (DisplayName = "Path Cache Cap", ClampMin = "0", ClampMax = "100000",
                ToolTip = "Max entries the property-path cache holds. Currently hardcoded to 256 — wired to this field in a follow-up patch."))
    int32 PathCacheCap;

    /**
     * Convenience accessor — null-safe pointer to the CDO-backed settings
     * instance. Returns the engine's GetDefault<> result; never null in any
     * normal context (UDeveloperSettings is always loaded with the module).
     */
    static const UMonolithUISettings* Get();

    /**
     * Normalise a folder path: trim trailing slash, ensure leading `/Game/`.
     * Used internally by the style service so callers get consistent results
     * regardless of trailing-slash inconsistency in Project Settings entries.
     */
    static FString NormalizeFolderPath(const FString& Path);
};
