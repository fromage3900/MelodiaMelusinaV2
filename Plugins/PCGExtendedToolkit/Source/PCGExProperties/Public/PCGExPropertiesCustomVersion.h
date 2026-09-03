// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Misc/Guid.h"

/**
 * Custom serialization version for packages containing PCGExProperties data.
 * Append new entries before VersionPlusOne; never reorder or remove existing ones.
 */
struct PCGEXPROPERTIES_API FPCGExPropertiesCustomVersion
{
	enum Type
	{
		/** Versions before this custom version system existed. */
		BeforeCustomVersionWasAdded = 0,

		/**
		 * UPCGExPropertyCollectionComponent::EnabledOverrides is serialized unconditionally in
		 * UPCGExPropertyCollectionComponent::Serialize. Per-instance override toggles no longer
		 * participate in archetype delta serialization -- in-parity instances used to silently
		 * inherit the template's CURRENT toggle state on every package load, so a CDO toggle
		 * change bled into every instance that had never authored its own toggle.
		 */
		InstanceOwnedOverrideToggles,

		// -- add new versions above this line --
		VersionPlusOne,
		LatestVersion = VersionPlusOne - 1
	};

	/** The GUID for this custom version. Must never change once shipped. */
	static const FGuid GUID;

	FPCGExPropertiesCustomVersion() = delete;
};
