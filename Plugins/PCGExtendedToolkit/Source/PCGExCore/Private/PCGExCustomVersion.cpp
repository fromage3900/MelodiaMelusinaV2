// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExCustomVersion.h"

#include "PCGExVersion.h"
#include "Serialization/CustomVersion.h"

// Unique to PCGExCore. Must differ from every other PCGEx custom version (e.g. FPCGExPropertiesCustomVersion)
// and must never change once shipped. Regenerate only if it has not yet reached any saved asset.
const FGuid FPCGExCustomVersion::GUID(0x7F2C9A41, 0x6E0D4B83, 0xB15A8C72, 0x3D9E0146);

namespace PCGExCustomVersion
{
	// Global registration: announces the version to the engine's custom-version registry at module load
	// so packages record PCGExVersion::Latest and can query it on load. Single source of truth -- bump
	// only PCGExVersion.h. (A package saved on a newer plugin version won't load on an older one; that's
	// fine -- Unreal assets aren't backward-loadable across versions, and the reverse doesn't happen.)
	FCustomVersionRegistration GRegisterPCGExCustomVersion(
		FPCGExCustomVersion::GUID,
		static_cast<int32>(PCGExVersion::Latest),
		TEXT("PCGExCore"));
}
