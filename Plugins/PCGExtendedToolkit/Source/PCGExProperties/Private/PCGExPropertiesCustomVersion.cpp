// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExPropertiesCustomVersion.h"

#include "Serialization/CustomVersion.h"

const FGuid FPCGExPropertiesCustomVersion::GUID(0xE3D7A914, 0x52C84B0F, 0x8A6FD1C2, 0x094B7E65);

namespace PCGExPropertiesCustomVersion
{
	// Global registration object: announces the version to the engine's custom-version registry
	// at module load so packages can record and query it.
	FCustomVersionRegistration GRegisterPCGExPropertiesCustomVersion(
		FPCGExPropertiesCustomVersion::GUID,
		FPCGExPropertiesCustomVersion::LatestVersion,
		TEXT("PCGExProperties"));
}
