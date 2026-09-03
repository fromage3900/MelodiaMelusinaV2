// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

namespace PCGExComponentFixups
{
	/** Register built-in post-apply fixups. Called from FPCGExCollectionsModule::StartupModule. */
	PCGEXCOLLECTIONS_API void RegisterBuiltins();

	/** Release built-in fixup handles. Called from FPCGExCollectionsModule::ShutdownModule. */
	PCGEXCOLLECTIONS_API void UnregisterBuiltins();
}
