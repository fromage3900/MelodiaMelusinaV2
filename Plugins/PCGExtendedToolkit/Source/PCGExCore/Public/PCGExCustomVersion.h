// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Misc/Guid.h"

/**
 * Package custom version for PCGEx node-settings deprecation.
 *
 * Lives in the package archive header, so -- unlike a delta-serialized UPROPERTY -- it is never
 * omitted when it happens to equal a default. UPCGExSettings::GetUserCustomVersionGuid() returns
 * this GUID; the engine then fills UPCGSettings::UserDataVersion from it on load, which is what
 * drives the PCGEX_IF_VERSION_LOWER deprecation gates (via UPCGExSettings::ResolveDataVersion).
 *
 * The version NUMBER is PCGExVersion::Latest (see PCGExVersion.h) -- this struct only owns the GUID,
 * so PCGExVersion.h stays the single place to bump.
 */
struct PCGEXCORE_API FPCGExCustomVersion
{
	/** The GUID for this custom version. Must never change once shipped. */
	static const FGuid GUID;

	FPCGExCustomVersion() = delete;
};
