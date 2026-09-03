// Copyright tumourlove. All Rights Reserved.
// UIReflectionHelper.h
//
// Allowlist-gated, type-aware property writer used by `set_widget_property`
// and the spec/builder pipeline. Replaces the bare `FProperty::ImportText_Direct`
// path that previously sat directly in the action handler — `ImportText_Direct`
// works but is text-only (no JSON shape), accepts any property name on any
// UClass (no security gate), and re-walks the FProperty link list per call
// (no cache).
//
// What this helper adds on top:
//   * **Allowlist gate** — by default, only paths in
//     `FUIPropertyAllowlist::IsAllowed(WidgetToken, JsonPath)` are permitted.
//     Bypass via `bRawMode = true` for callers that pre-date the gate.
//   * **JSON value parsing** — accepts FJsonValue, dispatching on the target
//     `FProperty` kind. Hand-rolled parsers for FVector2D, FLinearColor,
//     FMargin, FVector4, FSlateColor accept both array-form and object-form
//     JSON.
//   * **Path cache** — nested paths like `Slot.LayoutData.Offsets` resolve
//     through `FUIPropertyPathCache` for amortised constant-time lookup.
//
// Why a result struct instead of a bool: the action handler needs to surface
// the failure reason ("NotInAllowlist" / "PropertyNotFound" / "TypeMismatch"
// / "ParseFailed") so the LLM caller knows whether to fix the path, the
// allowlist, or the value. A flat bool would force the caller to grep logs.
//
// Thread safety: game-thread-only. The cache is a member of
// `UMonolithUIRegistrySubsystem`; nothing in this helper acquires locks.
//
// Clean-room: dispatch-on-FProperty-kind is a generic UE 5.7 reflection idiom.
// Allowlist gate at the FRONT (rather than at the FProperty layer) is OUR
// design choice — it lets us reject writes BEFORE walking the property link
// list, which matters for paths like `InternalEngineFlag` that don't exist
// on the widget at all.

#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonValue.h"
#include "UObject/NameTypes.h"

class FProperty;
class FUIPropertyAllowlist;
class FUIPropertyPathCache;
class UObject;

/**
 * Outcome of an `Apply` call. Always populated; never throws.
 *
 * `bSuccess` is the gate the caller checks. `FailureReason` is non-empty
 * when `bSuccess == false` and is one of the strings documented above.
 * `PropertyPath` echoes the input path so the LLM error report can frame
 * the failure ("X failed at path Y").
 */
struct MONOLITHUI_API FUIReflectionApplyResult
{
    bool bSuccess = false;
    FString FailureReason;
    FString PropertyPath;
    /**
     * Optional human-readable detail. For NotInAllowlist this is the widget
     * token; for PropertyNotFound it's the failed segment; for TypeMismatch
     * it's the expected vs actual type.
     */
    FString Detail;
};

/**
 * Stateless utility — instantiate per-call (cheap; no fields), call `Apply`,
 * inspect the result. Holding an instance across calls is safe but offers
 * no benefit since the cache lives on the subsystem.
 *
 * Why a struct rather than free functions: the per-call constructor injection
 * (`Allowlist*`, `PathCache*`) keeps the caller-side noise low. The action
 * handler builds one helper, points it at the subsystem's cache + allowlist,
 * and invokes Apply for each property in a batch.
 */
class MONOLITHUI_API FUIReflectionHelper
{
public:
    /**
     * Construct a helper bound to the supplied cache + allowlist. Both may
     * be null when `bRawMode = true` is the only intended call mode (e.g.
     * the legacy `set_widget_property` raw branch). With cache=null the
     * helper falls back to direct `FindPropertyByName` walks per call.
     */
    FUIReflectionHelper(FUIPropertyPathCache* InCache, const FUIPropertyAllowlist* InAllowlist);

    /**
     * Apply `Value` to the property at `PropertyPath` on `Root`.
     *
     * Allowlist gate runs first when `bRawMode == false`. On gate-fail the
     * call short-circuits with `FailureReason = "NotInAllowlist"`.
     *
     * Path resolution uses the cache when present. On cache miss the helper
     * walks the property link list directly. When no cache is supplied, every
     * call walks (no measurable cost on flat paths; ~2x cost on deep paths).
     *
     * Value dispatch table (FProperty kind -> JSON shape consumed):
     *   * FBoolProperty           : bool / 0|1 number / "true"|"false" string
     *   * FNumericProperty        : number / numeric string
     *   * FStrProperty            : string
     *   * FNameProperty           : string -> FName
     *   * FByteProperty (enum)    : enum-name string OR number
     *   * FEnumProperty           : enum-name string OR number
     *   * FObjectProperty         : asset path string (StaticLoadObject)
     *   * FStructProperty         : dispatched on `Struct->GetFName()`:
     *       - "Vector2D"     : object{x,y} OR array[x,y] OR "x,y" string
     *       - "LinearColor"  : "#RRGGBBAA" OR object{r,g,b,a} OR array[r,g,b,a]
     *       - "Margin"       : object{left,top,right,bottom} OR array[l,t,r,b] OR scalar
     *       - "Vector4"      : object{x,y,z,w} OR array[x,y,z,w]
     *       - "SlateColor"   : delegated to LinearColor parser
     *       - other          : falls back to ImportText_Direct on the JSON
     *                          value's string serialisation
     *   * FArrayProperty / FMapProperty : not navigated by path; if the leaf
     *     is an array/map, ImportText_Direct fallback is attempted with the
     *     stringified JSON.
     *
     * Returns a populated FUIReflectionApplyResult — never throws, never
     * crashes on bad input. The action handler surfaces the result to MCP.
     */
    FUIReflectionApplyResult Apply(
        UObject* Root,
        const FString& PropertyPath,
        const TSharedPtr<FJsonValue>& Value,
        bool bRawMode = false);

    /**
     * JSON-path-aware overload. Performs the same allowlist gate against the
     * caller-supplied `JsonPath`, then translates `JsonPath` into the
     * engine-side reflection path via the type registry's curated mapping
     * for `WidgetToken`, then calls `Apply(Root, EnginePath, Value, true)`
     * (raw-mode internally because the gate has already passed).
     *
     * Hoisted from the Phase F per-handler helper so the Phase H builder and
     * the per-MCP-call action wrappers share one translation routine. When
     * `WidgetToken` has no registry entry OR the entry has no mapping for
     * the supplied JsonPath, the JsonPath is used verbatim as the engine
     * path (same fallback the per-handler version had).
     *
     * Returns the same FUIReflectionApplyResult shape; the `PropertyPath`
     * field on the result echoes the JSON-side path (LLM-facing) regardless
     * of the engine-side translation.
     *
     * Phase H addition (closes Phase F's local-translation gap).
     */
    FUIReflectionApplyResult ApplyJsonPath(
        UObject* Root,
        const FName& WidgetToken,
        const FString& JsonPath,
        const TSharedPtr<FJsonValue>& Value);

    // Phase J: symmetric counterpart to ApplyJsonPath. Reads the value at the
    // engine-side property path corresponding to the LLM-facing `JsonPath`
    // for `WidgetToken`, and emits a FJsonValue of the appropriate JSON shape
    // (the inverse of the `Apply` value-dispatch table).
    //
    // Allowlist gate runs first -- unreachable JSON paths return a null
    // FJsonValue + bSuccess=false. JSON-path -> engine-path translation uses
    // the same registry mapping table `ApplyJsonPath` consults.
    //
    // Value dispatch (mirror of WriteValueToProperty):
    //   * FBoolProperty           -> JSON boolean
    //   * FNumericProperty        -> JSON number
    //   * FStrProperty            -> JSON string
    //   * FNameProperty           -> JSON string (FName::ToString)
    //   * FByteProperty (enum)    -> JSON string (enum name) or number
    //   * FEnumProperty           -> JSON string (enum name) or number
    //   * FObjectProperty         -> JSON string (asset path or empty)
    //   * FStructProperty:
    //       - "Vector2D"     -> object{x,y}
    //       - "LinearColor"  -> object{r,g,b,a}
    //       - "Margin"       -> object{left,top,right,bottom}
    //       - "Vector4"      -> object{x,y,z,w}
    //       - "SlateColor"   -> object{r,g,b,a}
    //       - other          -> JSON string via ExportText_Direct fallback
    //   * FArrayProperty / FMapProperty: NOT navigated by path (caller reads
    //     the leaf via separate enumeration; see ReadArrayProperty for the
    //     EffectSurface DropShadow / InnerShadow / Stops path).
    //
    // OutValue is populated on success; on failure it is set to a JSON null
    // and FailureReason is one of the same strings ApplyJsonPath emits.
    //
    // Pure read; never mutates the source object.
    FUIReflectionApplyResult ReadJsonPath(
        const UObject* Root,
        const FName& WidgetToken,
        const FString& JsonPath,
        TSharedPtr<FJsonValue>& OutValue) const;

private:
    FUIPropertyPathCache* Cache = nullptr;
    const FUIPropertyAllowlist* Allowlist = nullptr;
};
