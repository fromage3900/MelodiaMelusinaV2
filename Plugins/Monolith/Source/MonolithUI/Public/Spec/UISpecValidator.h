// Copyright tumourlove. All Rights Reserved.
// UISpecValidator.h
//
// Pre-mutation validator for the FUISpecDocument schema. The builder calls
// `Validate` before opening the FScopedTransaction; if any Error-severity
// findings are returned, no asset mutation runs. This is the gatekeeper that
// prevents partially-mutated broken Widget Blueprints (surface-map gap §3).
//
// Phase A scope: skeleton only. Implements the missing-root structural check
// so the test harness has a green path. Subsequent phases extend this with
// type-registry lookups, allowlist validation, animation reference checks,
// and the LLM-targeted error formatter.
//
// Phase H additions (2026-04-26): the deeper validation surface — parent-class
// allow check, node-tree depth limit, cycle detection (visited-set keyed by
// FName-id), per-node type-token resolution, animation/style ref existence
// checks. The full builder pipeline calls Validate before opening any
// transaction; failure aborts before any asset mutation. The depth + cycle
// checks live in `FUISpecBuilder` (where they share the dry-walk pass) so the
// validator surface here is the documentary contract.

#pragma once

#include "CoreMinimal.h"
#include "Spec/UISpec.h"

class FJsonObject;

/**
 * Stateless validator. Static methods only — no per-instance state, so
 * concurrent validation passes are safe.
 */
class MONOLITHUI_API FUISpecValidator
{
public:
    /**
     * Validate a parsed FUISpecDocument tree. Returns a populated
     * FUISpecValidationResult; callers should inspect `bIsValid` before
     * continuing into the builder pipeline.
     */
    static FUISpecValidationResult Validate(const FUISpecDocument& Document);

    /**
     * Convenience overload: validate from a raw JSON string. Parse failures
     * are reported as a single Error finding with line/column populated from
     * the JSON deserializer's error context.
     */
    static FUISpecValidationResult ValidateFromJson(const FString& JsonText);

    /**
     * Convenience overload: validate from an already-parsed JSON object.
     * Used by the MCP action handler which deserialises params upstream.
     */
    static FUISpecValidationResult ValidateFromJson(const TSharedPtr<FJsonObject>& JsonObject);
};
