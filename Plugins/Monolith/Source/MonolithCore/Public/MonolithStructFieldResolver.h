#pragma once

#include "CoreMinimal.h"

class FProperty;

/**
 * Dotted-path + UserDefinedStruct friendly-name property resolver.
 *
 * Resolves a possibly-dotted member path (e.g. "Movement.Speed") against a live
 * UObject container, descending FStructProperty segments and matching each segment
 * by its authored (friendly) name when the containing struct is a UUserDefinedStruct.
 * UserDefinedStruct fields carry a "_<index>_<32-hex-GUID>" suffix on their internal
 * FName; UUserDefinedStruct::GetAuthoredNameForField strips it so a caller can address
 * a member by the name shown in the editor.
 *
 * Non-dotted names resolve via a flat lookup on the object's class, preserving the
 * original single-segment behavior (back-compat). Array / map indexing is out of scope:
 * dotted traversal descends struct members only.
 *
 * Lives in MonolithCore (Public) so module-internal readers in either MonolithAnimation
 * (anim-instance sampling) or MonolithEditor (PIE object property read + function-arg
 * marshalling) share one resolver. Exported via MONOLITHCORE_API.
 */
namespace MonolithStructField
{
	/** Result of resolving a (possibly dotted) member path. */
	struct FResolved
	{
		/** The leaf property, or null if any segment failed to resolve. */
		const FProperty* Leaf = nullptr;
		/** Pointer to the leaf value, valid only when Leaf is non-null. */
		const void* ValuePtr = nullptr;
		/** The segment that failed to resolve, set only on failure. */
		FString FailedSegment;
	};

	/**
	 * Resolve a member path against a UObject container.
	 *
	 * @param Container  The owning UObject (e.g. a UAnimInstance). Null yields a miss.
	 * @param Path       A member name, optionally dotted to descend nested structs.
	 * @return The leaf FProperty + value pointer, or a miss with FailedSegment set.
	 */
	MONOLITHCORE_API FResolved Resolve(const UObject* Container, const FString& Path);
}
