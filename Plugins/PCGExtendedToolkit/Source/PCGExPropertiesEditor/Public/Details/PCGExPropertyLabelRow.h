// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Misc/Attribute.h"

class SWidget;

/**
 * Shared "Name | Type" label row used by property entry headers. Name renders in
 * the normal detail font; the "|" separator and Type render in italic + subdued
 * foreground so the type half visually backs off the name.
 */
namespace PCGExPropertyLabelRow
{
	/**
	 * Build the labeled row.
	 * @param NameAttr live name text (e.g. property name)
	 * @param TypeAttr live type text (e.g. FPCGExProperty::GetDisplayTypeName)
	 * @param bShowSeparator emit the "|" between Name and Type. Set false for
	 *        tighter inline contexts where the type sits flush against the name.
	 */
	PCGEXPROPERTIESEDITOR_API TSharedRef<SWidget> Build(
		TAttribute<FText> NameAttr,
		TAttribute<FText> TypeAttr,
		bool bShowSeparator = true);
}
