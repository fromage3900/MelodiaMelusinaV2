// Copyright tumourlove. All Rights Reserved.
// MonolithUICommon.h
//
// Shared, exported helpers for MonolithUI and any consumer that needs the
// same color / widget-blueprint / alignment parsing logic. The historical
// home for this code was the private header `MonolithUIInternal.h` which is
// unreachable from sibling plugins; this header replaces the duplicated
// copies, and the inline namespace `MonolithUIInternal` versions are now
// thin wrappers that forward into the exported symbols declared here.
//
// Color parsing comes in two flavours that intentionally differ in their
// FColor -> FLinearColor conversion path:
//   * `ParseColor` (legacy) — uses `FLinearColor(FColor)` which applies the
//     sRGB->linear degamma table. Matches the long-standing internal helper.
//     Use for engine widget properties expecting a degamma'd linear color.
//   * `TryParseColor` (sRGB pass-through) — divides each byte component by
//     255 directly, skipping the degamma. Use when feeding MD_UI material
//     parameters where the Slate shader applies its own gamma correction.
//
// Anchor preset names, halign/valign tokens, and widget class shortnames
// stay identical to the inline-namespace versions to preserve action-surface
// behaviour during the hoist.
#pragma once

#include "CoreMinimal.h"
#include "Components/CanvasPanelSlot.h"   // FAnchors (required by GetAnchorPreset's by-value return)
#include "Math/Color.h"
#include "Types/SlateEnums.h"

class UClass;
class UWidget;
class UWidgetBlueprint;
struct FMonolithActionResult;

/**
 * Filterable log category for the UISpec / build_ui_from_spec stack.
 * Kept distinct from `LogMonolith` (MonolithCore) so spec-builder iteration
 * noise can be filtered independently of the broader Monolith log surface.
 */
MONOLITHUI_API DECLARE_LOG_CATEGORY_EXTERN(LogMonolithUISpec, Log, All);

namespace MonolithUI
{
    /**
     * Parse a color string into FLinearColor with sRGB degamma applied.
     *
     * Accepted forms:
     *   "#RRGGBB"      — 6-digit hex, alpha defaults to 1.0
     *   "#RRGGBBAA"    — 8-digit hex with explicit alpha byte
     *   "#RGB"         — 3-digit hex (FColor::FromHex expands)
     *   "R,G,B"        — comma-delimited 0..1 floats, alpha defaults to 1.0
     *   "R,G,B,A"      — comma-delimited 0..1 floats with explicit alpha
     *
     * Returns FLinearColor::White on any unrecognised form. This is the legacy
     * MonolithUIInternal behaviour — callers wanting failure signalling should
     * use `TryParseColor` instead.
     */
    MONOLITHUI_API FLinearColor ParseColor(const FString& ColorStr);

    /**
     * Parse a color string into FLinearColor without sRGB degamma.
     *
     * Accepted forms identical to `ParseColor`, with two differences:
     *   1. Hex bytes are converted via direct R/255 division — no
     *      `FLinearColor(FColor)` ctor, no degamma. This keeps sRGB hex codes
     *      visually faithful when the consuming material/shader handles its
     *      own gamma correction (e.g. Slate UI materials).
     *   2. Returns false on unrecognised input rather than silently defaulting,
     *      so callers can fail fast with a useful error message.
     *
     * Hex length validation: only 3 / 6 / 8 hex digits accepted (FColor::FromHex
     * silently zeros out shorter or longer inputs).
     */
    MONOLITHUI_API bool TryParseColor(const FString& InStr, FLinearColor& OutColor);

    /**
     * Load a UWidgetBlueprint asset by path. Tries the path verbatim first,
     * then prepends `/Game/` if the supplied path is not already absolute.
     * On failure, populates `OutError` and returns nullptr.
     */
    MONOLITHUI_API UWidgetBlueprint* LoadWidgetBlueprint(
        const FString& AssetPath,
        FMonolithActionResult& OutError);

    /**
     * Map a short widget-class token (e.g. "VerticalBox", "TextBlock") or a
     * fully qualified class path to a UClass*. Falls back to FindFirstObject
     * when the short name is not in the curated table. Returns nullptr if the
     * class cannot be resolved.
     */
    MONOLITHUI_API UClass* WidgetClassFromName(const FString& ClassName);

    /**
     * Look up a named anchor preset (e.g. "top_left", "center", "stretch_fill")
     * and return the corresponding FAnchors. Unknown names default to the
     * top-left preset.
     */
    MONOLITHUI_API FAnchors GetAnchorPreset(const FString& PresetName);

    /**
     * Parse a horizontal alignment token. Accepted: "Left", "Center", "Right".
     * Anything else maps to HAlign_Fill.
     */
    MONOLITHUI_API EHorizontalAlignment ParseHAlign(const FString& S);

    /**
     * Parse a vertical alignment token. Accepted: "Top", "Center", "Bottom".
     * Anything else maps to VAlign_Fill.
     */
    MONOLITHUI_API EVerticalAlignment ParseVAlign(const FString& S);

    /**
     * Strip the engine `U` prefix from a UClass display name to derive the
     * public-facing registry token. `UVerticalBox` -> `VerticalBox`.
     * Mirrors the rule used by `UMonolithUIRegistrySubsystem::PopulateFromReflectionWalk`
     * so callers (e.g. `set_widget_property`) can map a widget instance to its
     * registry token without reaching into the subsystem's internals or
     * round-tripping through `FUITypeRegistry::FindByClass` (O(N) scan).
     *
     * Returns NAME_None if Class is null. Returns the input class name verbatim
     * (as an FName) if it does not begin with an uppercase `U` followed by
     * another uppercase letter — keeps non-conforming class names (third-party
     * plugins) round-trip-able.
     *
     * Clean-room: rule is OURS — derived from CLAUDE.md naming convention
     * ("U UObject, F struct, E enum"). Phase C hoist (2026-04-26).
     */
    MONOLITHUI_API FName MakeTokenFromClassName(const UClass* Class);

    /**
     * Register a variable name on a UWidgetBlueprint so the editor sees the
     * widget as a named variable (otherwise it lives as an anonymous tree
     * node and cannot be wired to graph pins).
     */
    MONOLITHUI_API void RegisterVariableName(UWidgetBlueprint* WBP, const FName& VariableName);

    /** Convenience: register the supplied widget's FName as a variable. */
    MONOLITHUI_API void RegisterCreatedWidget(UWidgetBlueprint* WBP, UWidget* Widget);

    /**
     * Walk the WBP's source widget tree and register every widget as a named
     * variable. Used after bulk widget construction to ensure the variable map
     * mirrors the tree state.
     */
    MONOLITHUI_API void ReconcileWidgetVariableGuids(UWidgetBlueprint* WBP);

    // -------------------------------------------------------------------------
    // Optional EffectSurface provider probe API (R3b / section 5.5 contract)
    // -------------------------------------------------------------------------
    //
    // Single source of truth for "is an optional EffectSurface UClass available
    // right now?". Action handlers, serializer, tests, and builder-side checks
    // reach the class through these two functions.
    //
    // The probe scans loaded UClasses by public class token instead of naming a
    // provider module. This keeps public Monolith source free of private
    // provider names while still preserving the runtime contract: if the
    // provider is loaded and the class is registered, Monolith can use it.
    //
    // Cache lifecycle:
    //   - Backing store is a function-static `TWeakObjectPtr<UClass>` shared
    //     across both functions.
    //   - First call resolves; subsequent calls return the cached weak-ptr's
    //     `Get()` result.
    //   - The cache is reset from `FCoreUObjectDelegates::ReloadCompleteDelegate`
    //     so Live Coding reloads re-scan the optional provider class.

    /**
     * Returns the optional EffectSurface UClass if a provider is loaded and its
     * UClass has been registered, nullptr otherwise. Caches the result on first
     * lookup; the cache is invalidated on reload so provider patches re-resolve
     * cleanly.
     */
    MONOLITHUI_API UClass* GetEffectSurfaceClass();

    /** Convenience: returns true iff an optional EffectSurface provider is loaded. */
    MONOLITHUI_API bool IsEffectSurfaceAvailable();
}
