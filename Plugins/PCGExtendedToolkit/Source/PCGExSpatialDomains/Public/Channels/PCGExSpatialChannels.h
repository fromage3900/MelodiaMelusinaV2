// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

/**
 * Channel-key constants for the spatial-domain framework.
 *
 * Channels are named buckets that organize how shapes interact with each
 * other in placement queries. The full registered list is authored in
 * UPCGExSpatialDomainsSettings::SpatialChannels; this namespace just
 * provides the always-present "Default" constant that code references
 * directly. New channel names live in the settings asset, not here.
 */
namespace PCGExSpatialChannels
{
	/**
	 * The default channel -- always present, always at bit index 0 of the
	 * runtime channel mask. Footprints with a missing or unrecognized
	 * ChannelKey fall back to this at runtime.
	 */
	PCGEXSPATIALDOMAINS_API extern const FName Default;
}
