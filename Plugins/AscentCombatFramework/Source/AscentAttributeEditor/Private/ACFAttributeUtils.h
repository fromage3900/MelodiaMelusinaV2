// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Containers/UnrealString.h"

class UAttributeSet;
struct FGameplayAttribute;

/**
 * Utility functions for working with FGameplayAttribute.
 *
 * Provides helper methods for validation, serialization, and type checking
 * of gameplay attributes.
 */
namespace ACFAttributeUtils
{
    /// Safe checks whether the given FGameplayAttribute is valid, even if UAttributeSet was removed.
	bool IsValid(const FGameplayAttribute& InAttribute);

	/// Converts the FGameplayAttribute to a string representation.
	FString ExportToString(const FGameplayAttribute& InAttribute);

	/// Converts a string representation back to an FGameplayAttribute.
	FGameplayAttribute ImportFromString(const FString& InStr);

	/// Checks whether the given FProperty is a valid attribute type.
	bool IsAttributeType(const FProperty* InProperty);
}
