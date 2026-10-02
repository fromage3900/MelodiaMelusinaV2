// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.
#pragma once

#include <AttributeSet.h>

#include "ACFAttributeWrapper.generated.h"

/**
 * Safe gameplay attribute reference.
 *
 * FEasyGasAttribute provides a persistent and safe reference to a gameplay attribute
 * that remains valid even if the original AttributeSet class or property is reloaded,
 * renamed, or temporarily unavailable.
 *
 * It supports resolving references dynamically and handling AttributeSet removal,
 * which makes it suitable for serialized data, Blueprint exposure, or editor tools.
 */

USTRUCT()
struct FACFAttributeWrapper
{
	GENERATED_BODY()
public:
	/// Constructs an attribute reference from a reflected property.
	explicit FACFAttributeWrapper(const FProperty* Property = nullptr);

	/// Constructs from an existing FGameplayAttribute.
	FACFAttributeWrapper(const FGameplayAttribute& Attribute);
	
	/// Constructs from a class path and property name pair.
	FACFAttributeWrapper(const FSoftClassPath& ClassPath, const FName& PropertyName);

	/// Returns true if initialized with a valid attribute reference (fast check, no resolution).
	bool IsValidFast() const;
	
	/// Attempts to resolve the reference; returns true if the attribute is accessible and valid.
	bool IsValidSafe() const;

	/// Implicit conversion operator to FGameplayAttribute.
	operator FGameplayAttribute () const;

	/// Returns the attribute path in the form <AttributeSet>.<PropertyName>.
	FString ToPathString() const;

	/// Returns the AttributeSet class name (or "None" if unresolved).
	FString GetClassName() const;

	/// Returns the attribute property name.
	FString GetAttributeName() const;

	/// Returns the AttributeSet class path.
	FSoftClassPath GetClassPath() const;

private:
	/// Updates cached class and property pointers when resolving the reference.
	void UpdateCache() const;

	/// Path to the AttributeSet class (used for resolving soft references).
	UPROPERTY()
	FSoftClassPath ClassPath;

	/// Name of the attribute property inside the AttributeSet.
	UPROPERTY()
	FName PropertyName;

	/// Cached UClass pointer for faster access.
	UPROPERTY()
	mutable TObjectPtr<UClass> ClassPtr;

	/// Cached property pointer (resolved lazily).
	mutable const FProperty* Property = nullptr;
};
