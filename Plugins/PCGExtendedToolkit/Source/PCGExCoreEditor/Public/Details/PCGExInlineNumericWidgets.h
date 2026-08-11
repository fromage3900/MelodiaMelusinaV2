// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Widgets/Input/NumericTypeInterface.h"

class IPropertyHandle;
class SWidget;

/**
 * Compact single-row numeric editors for FVector / FVector2D / FRotator property handles.
 *
 * Replaces UE's expandable struct editors with a horizontal row of SNumericEntryBox<double>
 * components that carry:
 *  - UE-standard XYZ colored narrow labels (matches Transform / Vector native style)
 *  - Unbounded slider range (drag freely, no 0-100 clamp)
 *  - LinearDeltaSensitivity-based drag behavior
 *  - For Rotator components: trailing degree symbol on display (`°`), stripped on parse
 *
 * Intended to be called from PropertyTypeCustomization code paths that want an inline
 * (non-expanding) editor for a struct-valued property handle.
 */
namespace PCGExInlineNumericWidgets
{
	// UE-standard axis label background colors used in native Transform / Vector inline editors.
	PCGEXCOREEDITOR_API extern const FLinearColor AxisColorX;
	PCGEXCOREEDITOR_API extern const FLinearColor AxisColorY;
	PCGEXCOREEDITOR_API extern const FLinearColor AxisColorZ;

	/**
	 * Numeric type interface that displays values with a trailing degree symbol (e.g. 90.0 -> "90.0°")
	 * and tolerates the symbol on input parsing. Used by the Rotator editor to match FTransform's UX.
	 */
	struct PCGEXCOREEDITOR_API FDegreesNumericTypeInterface : TDefaultNumericTypeInterface<double>
	{
		virtual FString ToString(const double& Value) const override;
		virtual TOptional<double> FromString(const FString& InString, const double& ExistingValue) override;
	};

	/**
	 * Build a single labeled SNumericEntryBox<double> bound to the given property handle.
	 * Returns SNullWidget::NullWidget if the handle is invalid.
	 * Optional TypeInterface controls display formatting (e.g. degrees).
	 */
	PCGEXCOREEDITOR_API TSharedRef<SWidget> MakeAxisEntry(
		TSharedPtr<IPropertyHandle> AxisHandle,
		const FLinearColor& LabelColor,
		TSharedPtr<INumericTypeInterface<double>> TypeInterface = nullptr);

	/** Compact inline editor for an FVector property handle (three X/Y/Z numeric entries). */
	PCGEXCOREEDITOR_API TSharedRef<SWidget> MakeVectorWidget(const TSharedRef<IPropertyHandle>& ValueHandle);

	/** Compact inline editor for an FVector2D property handle (two X/Y numeric entries). */
	PCGEXCOREEDITOR_API TSharedRef<SWidget> MakeVector2Widget(const TSharedRef<IPropertyHandle>& ValueHandle);

	/** Compact inline editor for an FRotator property handle (Roll/Pitch/Yaw numeric entries with degree display). */
	PCGEXCOREEDITOR_API TSharedRef<SWidget> MakeRotatorWidget(const TSharedRef<IPropertyHandle>& ValueHandle);
}
