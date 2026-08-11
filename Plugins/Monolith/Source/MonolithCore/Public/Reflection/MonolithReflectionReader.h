// SPDX-License-Identifier: MIT
// FMonolithReflectionReader — FProperty -> JSON-value reader.
// Read counterpart to the write-side FMonolithReflectionWalker; deliberately a
// separate file so the read/write split stays legible. Pure reflection over
// CoreUObject + Json; performs NO mutation, opens NO transaction, dirties nothing.

#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

class FProperty;

/**
 * Static helper that serialises a live FProperty value into a JSON value tree.
 *
 * This is the canonical FProperty->JSON reader for Monolith. It is the read
 * counterpart to FMonolithReflectionWalker (which writes JSON->FProperty). It is
 * a strictly read-only walk: it never mutates the container, never opens a
 * transaction, and never marks a package dirty.
 *
 * Handles numeric/byte-enum, bool, enum, string/name/text, soft-object /
 * soft-class / class / object references, FInstancedStruct (unwrapped with a
 * __struct tag), nested structs, arrays, sets, maps, and an ExportTextItem
 * fallback for anything else.
 */
class MONOLITHCORE_API FMonolithReflectionReader
{
public:
	/**
	 * Serialise a single FProperty value pointed to by ValuePtr into a JSON value.
	 *
	 * @param Prop      The property describing the value layout.
	 * @param ValuePtr  Pointer to the live value (e.g. Prop->ContainerPtrToValuePtr<void>(Object)).
	 * @param Owner     Optional owning object, used only as the export root for the
	 *                  ExportTextItem fallback branch (matches the historical CDO copy).
	 * @return A JSON value; FJsonValueNull when Prop or ValuePtr is null.
	 */
	static TSharedPtr<FJsonValue> PropertyToJsonValue(FProperty* Prop, const void* ValuePtr, const UObject* Owner = nullptr);

	/**
	 * Convenience: serialise every reflected (non-transient, non-UObject-base)
	 * property on an object into a flat JSON object keyed by property name.
	 * Mirrors the property-skip rules used by the DataAsset indexer.
	 */
	static TSharedPtr<FJsonObject> PropertiesToJsonObject(UObject* Object);
};
